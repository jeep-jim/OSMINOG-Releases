#!/usr/bin/env python3
"""Independently read 6.0.39 native AdBlock evidence, HTTP hits and OS PNGs.

The two cache records are labelled synthetic fixtures. This verifies production
request interception and persistence, not coverage of live advertising lists.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import re
import urllib.parse
from pathlib import Path

_spec = importlib.util.spec_from_file_location('mouse639_pixels', Path(__file__).with_name('mouse639-task-evidence.py'))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)
VERSION = '6.0.39'
PREFIX = '/mouse-adblock-fixture/'
SCRIPT = {'allowed': '/* Mouse639 owned allowed script */ globalThis.mouse639.executed.allowed++;',
          'advertising': '/* Mouse639 owned advertising script */ globalThis.mouse639.executed.advertising++;'}
COLORS = {'allowed': [42, 178, 93], 'advertising': [235, 158, 43], 'blocked': [200, 65, 85]}
WRITE_CASES = ('default-off', 'enabled-first', 'enabled-second-tab', 'enabled-other-desktop', 'enabled-private', 'disabled-again')
BASE_SETTINGS = {key: True for key in ('showBrandName', 'showFavicons', 'desktopGestures', 'downloadBounce', 'downloadBadge')}


def need(condition, message):
    if not condition:
        raise ValueError('Mouse639: ' + message)


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def stamp(value):
    need(isinstance(value, str), 'missing ISO cache date')
    try:
        parsed = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
        need(parsed.tzinfo is not None, 'cache date has no timezone')
        return parsed.timestamp() * 1000
    except (ValueError, OverflowError) as error:
        raise ValueError('Mouse639: invalid ISO cache date') from error


def settings(value, enabled, *, private=False, state=False):
    expected = {**BASE_SETTINGS, 'blockAds': enabled}
    if state:
        expected['privateMode'] = private
    need(value == expected, 'settings defaults, opt-in value or private state differ')


def state(value, enabled, *, prepared=True):
    need(isinstance(value, dict) and set(value) == {'enabled', 'phase', 'lists', 'rules', 'updatedAt'}, 'unexpected public blocker state')
    need(value['enabled'] is enabled and value['phase'] == ('ready' if enabled else 'off'), 'blocker is not in the required settled state')
    need(value['lists'] == (2 if prepared else 0) and P.integer(value['rules'], 10 if prepared else 1), 'synthetic filter lists were not loaded')
    if prepared:
        stamp(value['updatedAt'])
    else:
        need(value['updatedAt'] is None, 'default-off profile parsed filter cache')


def image_capture(read, value):
    need(value.get('source') == 'globalCapture.acquire(display)' and value.get('kind') == 'screen'
         and isinstance(value.get('backend'), str) and value['backend'], 'capture is not an actual OS screen')
    images = []
    name = value.get('filename')
    need(isinstance(name, str) and re.fullmatch(r'mouse-639-adblock-[a-z0-9-]+\.png', name), 'unsafe PNG filename')
    need(value.get('displayFilename') == name[:-4] + '-display.png', 'full display filename differs')
    for filename, checksum, dimensions in ((name, value.get('sha256'), value.get('pixelSize')),
                                           (value['displayFilename'], value.get('displaySha256'), value.get('screenPixelSize'))):
        blob = read(filename)
        need(digest(blob) == checksum, 'PNG bytes differ: ' + filename)
        decoded = P.decode_png(blob, filename)
        P.size(dimensions, filename)
        need(all(decoded[key] == dimensions[key] for key in ('width', 'height')), 'PNG dimensions differ')
        images.append(decoded)
    image, full = images
    display, content = P.rectangle(value.get('display', {}).get('bounds'), 'display'), P.rectangle(value.get('contentBounds'), 'content')
    sx, sy = full['width'] / display['width'], full['height'] / display['height']
    left, top = (content['x'] - display['x']) * sx, (content['y'] - display['y']) * sy
    crop = {'x': math.floor(left), 'y': math.floor(top), 'width': math.ceil(left + content['width'] * sx) - math.floor(left),
            'height': math.ceil(top + content['height'] * sy) - math.floor(top)}
    mapping = {'scaleX': sx, 'scaleY': sy, 'originX': left - crop['x'], 'originY': top - crop['y']}
    need(value.get('cropPixels') == crop and all(image[k] == crop[k] for k in ('width', 'height')), 'incorrect screen crop')
    need(crop['x'] >= 0 and crop['y'] >= 0 and crop['x'] + crop['width'] <= full['width'] and crop['y'] + crop['height'] <= full['height'], 'window is outside captured display')
    need(all(P.finite(value.get('mapping', {}).get(k)) and abs(value['mapping'][k] - v) < 1e-8 for k, v in mapping.items()), 'incorrect native DPI mapping')
    for x in range(0, image['width'], max(1, image['width'] // 29)):
        for y in range(0, image['height'], max(1, image['height'] // 23)):
            need(P.pixel(image, x, y) == P.pixel(full, x + crop['x'], y + crop['y']), 'crop is not the recorded display')
    return image, mapping


def pixel_at(image, mapping, point):
    need(isinstance(point, dict) and all(P.finite(point.get(k)) for k in ('x', 'y')), 'invalid CSS pixel point')
    x, y = (math.floor(mapping['origin' + axis] + point[key] * mapping['scale' + axis]) for key, axis in (('x', 'X'), ('y', 'Y')))
    return x, y, P.pixel(image, x, y)


def input_receipts(part, platform):
    values = part.get('inputs', [])
    need(values, 'native input receipts are missing')
    by_ticket = {}
    for value in values:
        ticket = value.get('ticket')
        need(isinstance(ticket, str) and re.fullmatch(r'[a-f0-9-]{36}', ticket) and ticket not in by_ticket, 'invalid or duplicate native input ticket')
        need(value.get('pid') == part['pid'] and value.get('action') == 'click'
             and value.get('source') == {'darwin': 'CGEvent', 'linux': 'XTest', 'win32': 'User32'}[platform], 'input did not use the installed native driver')
        need(all(P.finite(value.get('point', {}).get(key)) for key in ('x', 'y')), 'native input point missing')
        need(P.finite(value.get('at')) and part['startedAt'] <= value['at'] <= part['completedAt'], 'input is outside the installed phase')
        need(any(event.get('ticket') == ticket and event.get('selector') == value.get('selector') and event.get('type') == 'click'
                 and event.get('trusted') is True and event.get('matches') is True and value['at'] <= event.get('at', 0) <= part['completedAt']
                 for event in value.get('events', [])), 'native click has no matching trusted DOM receipt')
        by_ticket[ticket] = value
    return by_ticket


def verify_case(value, part, hits, captures, decoded, blocked, private):
    name, token = value.get('name'), value.get('token')
    need(isinstance(token, str) and re.fullmatch(r'[a-f0-9-]{36}', token), 'invalid HTTP request token')
    need(value.get('pid') == part['pid'] and value.get('blocked') is blocked and value.get('privateMode') is private
         and value.get('sessionPersistent') is (not private), 'wrong native process, expectation or Session')
    url = part['origin'] + PREFIX + 'page?token=' + token
    need(value.get('url') == url, 'case did not load the owned local HTTP page')
    dom = value.get('dom', {})
    need(dom.get('url') == url and dom.get('token') == token and dom.get('title') == 'Mouse639 owned AdBlock fixture', 'actual page identity differs')
    need(dom.get('attempted') == {'allowed': 1, 'advertising': 1}, 'page did not attempt both real script requests')
    need(dom.get('executed') == {'allowed': 1, 'advertising': 0 if blocked else 1}
         and dom.get('settled') == {'allowed': 'load', 'advertising': 'error' if blocked else 'load'}, 'actual script execution or completion differs')
    own_hits = [hit for hit in hits if hit['token'] == token]
    counts = {kind: sum(hit['kind'] == kind for hit in own_hits) for kind in ('page', 'allowed', 'advertising')}
    need(counts == value.get('counts') == {'page': 1, 'allowed': 1, 'advertising': 0 if blocked else 1}, 'server actually received an unexpected request')
    settings(value.get('settings'), blocked, private=private, state=True)
    state(value.get('state'), blocked, prepared=name != 'default-off')
    native = value.get('native', {})
    need(all(native.get(key) is True for key in ('visible', 'parentVisible', 'cachedVisible', 'attached')) and native.get('zoom') == 1, 'fixture is not a visible native view at actual scale')
    need(isinstance(native.get('tabId'), str) and native['tabId'] and isinstance(native.get('desk'), str) and native['desk'] and P.integer(native.get('webContentsId'), 1), 'native page owner missing')
    bounds, view = P.rectangle(native.get('bounds'), 'page bounds'), P.rectangle(native.get('viewBounds'), 'native view')
    parent = native.get('parentBounds')
    if parent is not None:
        P.rectangle(parent, 'native parent')
    actual = {'x': view['x'] + (parent['x'] if parent else 0), 'y': view['y'] + (parent['y'] if parent else 0), 'width': view['width'], 'height': view['height']}
    need(actual == bounds == native.get('actualBounds'), 'native page hierarchy differs')
    shot = captures.get(value.get('capture'))
    need(shot and shot.get('ui') is None and shot['pid'] == part['pid'], 'page screenshot is missing or belongs to another process')
    need(bounds['x'] >= 0 and bounds['y'] >= 0 and bounds['x'] + bounds['width'] <= shot['contentBounds']['width'] and bounds['y'] + bounds['height'] <= shot['contentBounds']['height'], 'page lies outside window')
    image, mapping = decoded[shot['filename']]
    regions, probes = dom.get('regions', []), shot.get('probes', [])
    need(len(regions) == 2 and [r.get('kind') for r in regions] == ['allowed', 'advertising'] and len(probes) == 6, 'owned native pixel witnesses missing')
    for index, region in enumerate(regions):
        kind = region['kind']
        wanted = {'x': 24, 'y': 80 if kind == 'allowed' else 144, 'width': 200, 'height': 42}
        color = COLORS['blocked' if blocked and kind == 'advertising' else kind]
        need(region.get('bounds') == wanted and region.get('color') == 'rgb(' + ', '.join(map(str, color)) + ')', 'fixture result patch changed')
        for probe, offset in zip(probes[index * 3:index * 3 + 3], (-5, 0, 5)):
            point = {'x': bounds['x'] + wanted['x'] + 100 + offset, 'y': bounds['y'] + wanted['y'] + 21}
            need(probe.get('kind') == kind and probe.get('localBounds') == wanted and probe.get('offset') == offset
                 and probe.get('point') == point and probe.get('expectedRGB') == color, 'pixel expectation was changed')
            x, y, pixel = pixel_at(image, mapping, point)
            need(probe.get('x') == x and probe.get('y') == y and probe.get('actualRGBA') == pixel, 'pixel receipt differs from archived OS frame')
            need(pixel[3] == 255 and all(abs(pixel[i] - color[i]) <= 3 for i in range(3)), 'OS pixels do not show the actual request outcome')
    return {'name': name, 'blocked': blocked, 'private': private, 'tabId': native['tabId'], 'desk': native['desk'], 'webContentsId': native['webContentsId']}


def verify(read, *, expected_platform=None, expected_arch=None):
    artifacts = {}
    source_read = read
    def raw(name):
        need(isinstance(name, str) and re.fullmatch(r'mouse-639-[a-z0-9.-]+', name) and '..' not in name, 'unsafe native artifact name')
        data = source_read(name)
        need(isinstance(data, bytes) and 0 < len(data) <= 16 * 1024**2, 'unbounded or empty native artifact')
        artifacts[name] = {'file': name, 'sha256': digest(data), 'bytes': len(data)}
        return data
    def load(name):
        value = json.loads(raw(name))
        need(isinstance(value, dict), 'native evidence must be an object')
        return value
    facts, written, processes = (load(name) for name in ('mouse-639-adblock.json', 'mouse-639-adblock-write.json', 'mouse-639-adblock-processes.json'))
    need(facts.get('schema') == 1 and facts.get('version') == VERSION and facts.get('ok') is True and facts.get('restored') is True and facts.get('awaitingRestart') is False, 'native acceptance did not finish both processes')
    need(facts.get('packaged') is True and facts.get('profileIsolated') is True and facts.get('physicalUserDeviceVerified') is False
         and facts.get('fixture') == 'synthetic-cache-and-loopback-http', 'installed profile or fixture scope differs')
    platform, arch = facts.get('platform'), facts.get('arch')
    need((platform, arch) in (('darwin', 'arm64'), ('linux', 'x64'), ('win32', 'x64')) and expected_platform in (None, platform) and expected_arch in (None, arch), 'wrong native platform')
    need(all(processes.get(key) == facts.get(key) for key in ('version', 'platform', 'arch', 'profile')), 'process profile identity differs')
    need(processes.get('reportSha256') == digest(raw('mouse-639-adblock.json')) and re.fullmatch(r'[a-f0-9]{64}', processes.get('executableSha256', '')), 'installed executable or final report binding missing')
    need(written.get('ok') is False and written.get('writeComplete') is True and written.get('awaitingRestart') is True and 'restart' not in written, 'first process was not awaiting a real restart')
    for key in ('schema', 'version', 'platform', 'arch', 'packaged', 'pid', 'profile', 'profileIsolated', 'physicalUserDeviceVerified', 'fixture', 'write'):
        need(written.get(key) == facts.get(key), 'read process rewrote first-process evidence: ' + key)
    need(P.integer(facts.get('pid'), 1) and P.integer(facts.get('restart', {}).get('pid'), 1) and facts['pid'] != facts['restart']['pid'], 'two distinct native PIDs are required')
    seed = load('mouse-639-adblock-cache.json')
    need(seed.get('schema') == 1 and seed.get('version') == VERSION and seed.get('synthetic') is True and seed.get('purpose') == 'isolated-installed-adblock-smoke'
         and seed.get('profile') == facts['profile'] and processes.get('cacheSeedSha256') == digest(raw('mouse-639-adblock-cache.json')), 'synthetic cache provenance differs')
    rows = seed.get('records', [])
    need(len(rows) == 2 and {row.get('source') for row in rows} == {'easylist', 'ruadlist'}, 'two labelled synthetic records are required')
    cache_records = []
    for row in rows:
        ident, url = row['source'], 'https://easylist-downloads.adblockplus.org/' + row['source'] + '.txt'
        filename = 'mouse-639-adblock-cache-' + ident + '.json'
        need(row.get('url') == url and row.get('file') == filename and row.get('profileRelative') == 'mouse-adblock/' + ident + '.json', 'cache source identity differs')
        data = raw(filename)
        need(digest(data) == row.get('sha256'), 'archived cache bytes differ')
        record = json.loads(data)
        expected_lines = ['[Adblock Plus 2.0]', '! MOUSE639 SYNTHETIC CI FIXTURE — not the actual subscription contents', '! Only for an isolated installed-process acceptance profile.', PREFIX + 'advertising-script.js']
        expected_lines += ['||mouse639-' + ident + '-' + str(index).zfill(2) + '.test^' for index in range(60)]
        expected_text = '\n'.join(expected_lines) + '\n'
        need(record.get('schema') == 1 and record.get('source') == ident and record.get('url') == url and record.get('synthetic') is True
             and record.get('text') == expected_text and record.get('sha256') == row.get('textSha256') == digest(expected_text.encode('utf-8'))
             and row.get('lines') == 64 and row.get('supportedBlockRules') == 61 and record.get('updatedAt') == seed.get('generatedAt'), 'synthetic rule contents or real cache schema differ')
        cache_records.append({'source': ident, 'sha256': digest(data), 'textSha256': record['sha256'], 'updatedAt': record['updatedAt']})
    template = raw('mouse-639-adblock-fixture.html')
    need(b'Owned local AdBlock fixture' in template and b"for(const kind of ['allowed','advertising'])" in template
         and b'mouse639.attempted[kind]++' in template and b'script.onload' in template and b'script.onerror' in template and b'document.head.append(script)' in template,
         'owned page did not contain both unconditional real script requests')
    accepted_cases = []
    for phase, key, marker, budget in (('write', 'write', 'MOUSE_639_ADBLOCK_WRITE_PASS', 210000), ('read', 'restart', 'MOUSE_639_ADBLOCK_NATIVE_PASS', 90000)):
        part, receipt = facts.get(key, {}), processes.get(phase, {})
        pid = facts['pid'] if phase == 'write' else facts['restart']['pid']
        need(part.get('pid') == receipt.get('pid') == pid and receipt.get('exitCode') == 0 and P.finite(receipt.get('elapsedMs')) and 0 < receipt['elapsedMs'] <= budget, 'installed child identity, exit or time budget differs')
        need(part.get('budgetMs') == (180000 if phase == 'write' else 60000) and P.finite(part.get('startedAt')) and P.finite(part.get('completedAt'))
             and part.get('elapsedMs') == part['completedAt'] - part['startedAt'] and 0 < part['elapsedMs'] <= part['budgetMs'], 'native bounded phase did not complete')
        report_name = 'mouse-639-adblock-write.json' if phase == 'write' else 'mouse-639-adblock.json'
        need(receipt.get('report') == report_name and receipt.get('reportSha256') == digest(raw(report_name)), 'phase report binding differs')
        log_name = 'mouse-639-adblock-' + phase + '.log'
        log = raw(log_name)
        need(receipt.get('log') == log_name and receipt.get('logSha256') == digest(log) and receipt.get('requiredMarkers') == [marker], 'phase log binding differs')
        lines = log.decode('utf-8', 'replace').splitlines()
        need(marker in lines and not any('MOUSE_639_ADBLOCK_FAIL' in line or 'MOUSE_NATIVE_PROCESS_TIMEOUT' in line for line in lines)
             and any(line.startswith(f'MOUSE_639_PROCESS_RETURN pid={pid} code=0 ') for line in lines), 'installed child did not produce the required exit receipt')
        need(-300000 <= part['startedAt'] - stamp(seed['generatedAt']) < 3600000, 'cached fixture lists were not fresh for this process')
        for cache in (part.get('initial', {}).get('cache', {}), part.get('cache', {})):
            need(cache.get('seedSha256') == digest(raw('mouse-639-adblock-cache.json')) and cache.get('records') == cache_records, 'installed process did not read the exact seeded cache')
        enabled = phase == 'read'
        settings(part.get('initial', {}).get('settings'), enabled, state=True)
        state(part.get('initial', {}).get('state'), enabled, prepared=enabled)
        settings(part.get('finalSettings'), not enabled)
        need(part.get('fixtureSha256') == digest(template), 'served fixture template differs')
        origin = urllib.parse.urlparse(part.get('origin', ''))
        need(origin.scheme == 'http' and origin.hostname == '127.0.0.1' and origin.port and origin.path == '' and not origin.query and not origin.fragment, 'fixture was not loopback HTTP')
        http_name = 'mouse-639-adblock-http-' + phase + '.json'
        http_raw = raw(http_name)
        need(part.get('http') == {'file': http_name, 'sha256': digest(http_raw)}, 'raw server log hash differs')
        server = json.loads(http_raw)
        need(server.get('schema') == 1 and server.get('synthetic') is True and server.get('version') == VERSION and server.get('pid') == pid and server.get('origin') == part['origin'], 'server log came from another fixture process')
        hits = server.get('hits', [])
        need(isinstance(hits, list) and hits, 'server saw no actual HTTP requests')
        for sequence, hit in enumerate(hits, 1):
            kind = hit.get('kind')
            need(kind in ('page', 'allowed', 'advertising'), 'unexpected owned HTTP route')
            body = template if kind == 'page' else SCRIPT[kind].encode('utf-8')
            need(hit.get('sequence') == sequence and hit.get('method') == 'GET' and hit.get('status') == 200 and hit.get('path') == PREFIX + ('page' if kind == 'page' else kind + '-script.js')
                 and hit.get('bodySha256') == digest(body) and hit.get('bytes') == len(body), 'server request or delivered fixture bytes differ')
            need(P.finite(hit.get('at')) and part['startedAt'] <= hit['at'] <= part['completedAt'], 'HTTP request occurred outside native phase')
        inputs = input_receipts(part, platform)
        capture_rows = part.get('captures', [])
        captures = {value['filename']: value for value in capture_rows}
        need(len(captures) == len(capture_rows) and captures and all(value.get('pid') == pid for value in capture_rows), 'native capture identity differs')
        decoded = {name: image_capture(raw, value) for name, value in captures.items()}
        cases = part.get('cases', [])
        need(tuple(value.get('name') for value in cases) == (WRITE_CASES if phase == 'write' else ('restart-enabled',)), 'required native cases were omitted or reordered')
        need(len({value.get('token') for value in cases}) == len(cases), 'HTTP request tokens were reused')
        for value in cases:
            blocked = value['name'] not in ('default-off', 'disabled-again')
            accepted_cases.append(verify_case(value, part, hits, captures, decoded, blocked, value['name'] == 'enabled-private'))
        ui = {value['name']: value for value in part.get('ui', [])}
        for value in ui.values():
            shot = captures.get(value.get('capture'))
            need(shot and value.get('open') is True and shot.get('ui') == {k: v for k, v in value.items() if k not in ('name', 'capture')}, 'settings screenshot does not bind the actual checkbox readback')
            rect = P.rectangle(value.get('bounds'), 'checkbox')
            image, mapping = decoded[shot['filename']]
            shades = [sum(pixel_at(image, mapping, {'x': rect['x'] + rect['width'] * x, 'y': rect['y'] + rect['height'] * y})[2][:3]) for x in (.2, .4, .6, .8) for y in (.2, .4, .6, .8)]
            need(max(shades) - min(shades) >= 20, 'checkbox OS pixels are blank')
        expected_changes = [('enable-dark', True), ('disable-again', False), ('persist-enabled', True)] if phase == 'write' else [('restore-initial-off', False)]
        changes = part.get('changes', [])
        need([(change.get('name'), change.get('enabled')) for change in changes] == expected_changes, 'native preference transitions differ')
        for change in changes:
            on = change['enabled']
            need(inputs.get(change.get('input'), {}).get('selector') == '[data-setting="blockAds"]', 'setting was not changed with its native checkbox')
            need(change.get('before', {}).get('checked') is (not on) and change['before'].get('disabled') is False and change.get('after', {}).get('checked') is on
                 and change['after'].get('stored') is on and change['after'].get('disabled') is False, 'checkbox does not reflect committed preference')
            need(change['name'] in ui and all(ui[change['name']].get(k) == v for k, v in change['after'].items()), 'transition has no bound UI capture')
            settings(change.get('saved'), on)
            state(change.get('state'), on)
        if phase == 'write':
            need(ui.get('initial-off', {}).get('checked') is False and ui.get('enable-dark', {}).get('theme') == 'dark'
                 and ui.get('enabled-light', {}).get('theme') == 'light' and ui['enabled-light'].get('checked') is True, 'new toggle was not observed in both themes')
            first, second, other = cases[1], cases[2], cases[3]
            need(first['native']['webContentsId'] != second['native']['webContentsId'] and first['native']['desk'] == second['native']['desk']
                 and other['native']['desk'] != first['native']['desk'], 'second tab or second desktop was not real')
            switch = part.get('deskSwitch', {})
            need(switch.get('from') == first['native']['desk'] and switch.get('to') == other['native']['desk'], 'desktop transition identity differs')
            for field, target in (('input', switch['to']), ('returnInput', switch['from'])):
                need(inputs.get(switch.get(field), {}).get('selector') == '.desktop-card[data-desk="' + target + '"] .desk-open', 'desktop was not selected with native UI')
            privacy = part.get('private', {})
            need(privacy.get('persistent') is False and privacy.get('distinctSession') is True and str(privacy.get('partition', '')).startswith('mouse-private-'), 'private requests reused a persistent normal Session')
            need(all(inputs.get(privacy.get(key), {}).get('selector') == '#private-button' for key in ('enterInput', 'leaveInput')), 'incognito transition did not use native UI')
            private_ui = privacy.get('ui', {})
            need(private_ui.get('checked') is True and private_ui.get('disabled') is True and private_ui.get('privateMode') is True and 'обычном режиме' in str(privacy.get('writeError', '')), 'private profile could change the persistent preference')
            need(all(ui.get('private-enabled', {}).get(k) == v for k, v in private_ui.items()), 'private disabled checkbox capture missing')
            retained = part.get('retained', {})
            need(retained.get('before') == retained.get('after') == {'token': first['token'], 'timeOrigin': first['dom']['timeOrigin']}
                 and retained.get('webContentsId') == first['native']['webContentsId'], 'normal page was replaced by a desktop or private transition')
            main = part.get('mainFrame', {})
            main_hits = [hit for hit in hits if hit['token'] == main.get('token')]
            need(main.get('enabled') is True and main.get('hits') == len(main_hits) == 1 and main_hits[0]['kind'] == 'advertising'
                 and main.get('url') == part['origin'] + PREFIX + 'advertising-script.js?token=' + main['token'] and SCRIPT['advertising'] in str(main.get('body', '')), 'top-level navigation was incorrectly blocked')
            tokens = {case['token'] for case in cases} | {main['token']}
        else:
            need(ui.get('restored-enabled', {}).get('checked') is True and ui['restored-enabled'].get('stored') is True, 'enabled setting did not return in the restarted UI')
            tokens = {case['token'] for case in cases}
        need(all(hit['token'] in tokens for hit in hits), 'server log contains an unbound probe request')
    need(facts.get('cleanup', {}).get('restored') is True, 'owned profile fixture cleanup failed')
    return {'ok': True, 'version': VERSION, 'platform': platform, 'arch': arch, 'scope': 'synthetic cached filters, real HTTP requests and installed native UI',
            'syntheticFilters': True, 'cases': accepted_cases, 'processes': {'writePid': facts['pid'], 'readPid': facts['restart']['pid']},
            'cache': {'lists': 2, 'records': cache_records}, 'artifacts': [artifacts[name] for name in sorted(artifacts)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--platform', choices=('darwin', 'win32', 'linux'), required=True)
    parser.add_argument('--arch', choices=('arm64', 'x64'), required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    def read(name):
        need(isinstance(name, str) and Path(name).name == name, 'unsafe evidence filename')
        return (directory / name).read_bytes()
    result = verify(read, expected_platform=args.platform, expected_arch=args.arch)
    (directory / 'mouse-639-acceptance.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('MOUSE_639_INDEPENDENT_NATIVE_ACCEPTANCE_PASS')


if __name__ == '__main__':
    main()
