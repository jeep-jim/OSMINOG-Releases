#!/usr/bin/env python3
"""Independent Mac643 native input, page ownership, theme and display reader."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit, parse_qs

_spec = importlib.util.spec_from_file_location('mouse643_native_pixels', Path(__file__).with_name('mouse643-task-evidence.py'))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)
VERSION = '6.0.43'
TOKENS = ('native643-mac-chrome-and-tab-shapes', 'native643-search-suggestions-and-address-tools',
          'native643-real-page-theme-and-restart')
CAPTURES = tuple('mouse-643-' + value + '.png' for value in (
    'chrome-rounded-light', 'chrome-rounded-dark', 'chrome-square-light', 'traffic-light',
    'chrome-square-dark', 'traffic-dark', 'address-pages', 'search-light', 'search-dark', 'restored'))
IDENTITY = ('id', 'index', 'desk', 'webContentsId', 'url', 'navigationEpoch', 'identity', 'timeOrigin',
            'field', 'scrollX', 'scrollY', 'cookie')


def need(value, message):
    if not value:
        raise ValueError('Mouse643 polish: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def same_page(before, after):
    need(isinstance(before, dict) and isinstance(after, dict), 'missing real page identities')
    need(all(key in before and after.get(key) == before[key] for key in IDENTITY), 'live page/document/profile state changed')
    need(type(before.get('webContentsId')) is int and before['webContentsId'] > 0
         and isinstance(before.get('identity'), str) and before['identity']
         and P.finite(after.get('ticks')) and after['ticks'] >= before.get('ticks', 0), 'actual live document ownership/timer is missing')


def native_input(value, pid):
    need(isinstance(value, dict) and value.get('pid') == pid and value.get('source') == 'CGEvent'
         and isinstance(value.get('selector'), str) and value['selector'] and P.finite(value.get('at'))
         and all(P.finite(value.get('point', {}).get(axis)) for axis in ('x', 'y')), 'missing actual Mac input delivery')
    events = value.get('events', [])
    need(isinstance(events, list) and 0 < len(events) <= 300
         and any(e.get('type') == 'click' and e.get('trusted') is True and e.get('matches') is True for e in events),
         'trusted native click did not reach its original control')


def native_drag(value, pid):
    need(value.get('pid') == pid and value.get('source') == 'CGEvent' and value.get('completed') is True,
         'native drag did not complete')
    for point in ('from', 'to'):
        need(all(P.finite(value.get(point, {}).get(axis)) for axis in ('x', 'y')), 'native drag coordinates missing')
    need(value['from'] != value['to'], 'native drag did not move')
    events = value.get('events', [])
    for kind in ('pointerdown', 'pointermove', 'pointerup'):
        need(any(e.get('type') == kind and e.get('trusted') is True and (kind != 'pointerdown' or e.get('matches') is True)
                 for e in events), 'native drag lacks trusted ' + kind)
    before, after = value.get('before', []), value.get('after', [])
    need(len(before) == len(after) == 2, 'drag must preserve two actual native pages')
    for a, b in zip(before, after): same_page(a, b)


def rgb(value):
    if isinstance(value, str) and re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
        return tuple(int(value[n:n+2], 16) for n in (1, 3, 5))
    match = re.fullmatch(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', value or '')
    need(match is not None, 'expected an opaque computed color')
    return tuple(map(int, match.groups()))


def chrome(value, theme, mode):
    need(value.get('platform') == 'darwin' and value.get('theme') == theme and value.get('mode') == mode
         and value.get('appearance', {}).get('paneMode') == mode and value.get('flowCount') == 0,
         'Mac theme/shape or retired SVG flow differs')
    custom = value.get('appearance', {}).get('surfaces', {}).get(theme, {}).get('top', {})
    need(custom == {'mode': 'solid', 'color': '#EACB92' if theme == 'light' else '#1D4B5C',
                    'endColor': '#EACB92' if theme == 'light' else '#1D4B5C', 'opacity': 100, 'angle': 0},
         'custom top surface fixture was not applied')
    tabs = value.get('tabs', [])
    need(len(tabs) >= 2 and len({t.get('id') for t in tabs}) == len(tabs), 'actual top tabs missing')
    active = [t for t in tabs if t.get('active') is True]
    need(len(active) == 1 and rgb(active[0].get('background')) == rgb(value.get('rootPanel')),
         'active Mac tab does not use the root page paint')
    for tab in tabs:
        need(isinstance(tab.get('text'), str) and tab['text'] and tab.get('title') == tab['text']
             and tab.get('tooltip') == tab['text'], 'full actual tab title/hover text is missing')
        if mode == 'square':
            for element in [tab, *tab.get('buttons', [])]:
                need(len(element.get('radii', [])) == 4 and all(re.fullmatch(r'0(?:px|%)?', str(v)) for v in element['radii']),
                     'square top tab or a child button still has rounded corners')
    traffic = value.get('traffic', [])
    need([t.get('action') for t in traffic] == ['quit', 'minimize', 'zoom'], 'actual three Mac traffic controls missing')
    for control in traffic:
        box = P.rectangle(control.get('bounds'), 'traffic control')
        need(box['width'] == box['height'] == 13 and len(control.get('radii', [])) == 4
             and all(v in ('50%', '6.5px') for v in control['radii']), 'custom top color changed the Mac traffic control shape')
    if mode == 'square':
        dividers = value.get('dividers', [])
        need(dividers, 'square native split divider missing')
        for divider in dividers:
            box, guide = P.rectangle(divider.get('bounds'), 'square divider'), divider.get('guide', {})
            key = 'width' if divider.get('axis') == 'x' else 'height'
            offset = 'left' if key == 'width' else 'top'
            need(box[key] == 1 and guide.get(key) == '1px' and guide.get(offset) == '0px'
                 and guide.get('transform') == 'none', 'square separator or hover guide exceeds its one-pixel seam')


def media(value, theme, *, initial=False):
    dark = theme == 'dark'
    need(value.get('dark') is dark and value.get('light') is (not dark)
         and value.get('background') == ('rgb(27, 41, 55)' if dark else 'rgb(241, 244, 249)')
         and isinstance(value.get('identity'), str) and value['identity'] and P.finite(value.get('timeOrigin')),
         'real page matchMedia and its CSS do not match the chosen theme')
    if initial: need(value.get('initial') is dark, 'new page received the wrong native theme at its first script')


def search(value, theme, pid):
    need(value.get('theme') == theme and value.get('query') == 'mouse browser'
         and value.get('suggestion') == 'mouse browser tips' and value.get('externalProviderVerified') is False,
         'owned suggestion fixture must not claim external-provider verification')
    provider = value.get('provider', {})
    need(provider.get('inside') is True and provider.get('first') is True and provider.get('icon') is True
         and provider.get('engine') == 'google' and 'google' in provider.get('label', '').lower(),
         'current provider icon is not the first real search-field control')
    button, query = P.rectangle(provider.get('button'), 'provider'), P.rectangle(provider.get('query'), 'query')
    need(button['x'] + button['width'] <= query['x'] + 1, 'provider icon overlaps query text')
    need(value.get('options') == ['mouse browser tips', 'mouse browser tabs']
         and any(e.get('trusted') is True and e.get('value') == 'mouse browser' for e in value.get('typed', [])),
         'actual typed query or parsed provider suggestions differ')
    requests = value.get('transport', [])
    need(len(requests) == 1 and requests[0].get('query') == 'mouse browser', 'unexpected suggestion requests')
    suggestion_url = urlsplit(requests[0].get('url', ''))
    need(suggestion_url.scheme == 'https' and suggestion_url.hostname in ('suggestqueries.google.com', 'www.google.com')
         and parse_qs(suggestion_url.query).get('q') == ['mouse browser'], 'real service did not construct the selected provider request')
    requested = urlsplit(value.get('requestedURL', ''))
    need(requested.scheme == 'https' and requested.hostname == 'www.google.com' and requested.path == '/search'
         and parse_qs(requested.query) == {'q': ['mouse browser tips']}, 'submitted row did not produce its exact ordinary search URL')
    loads = value.get('loads', [])
    need(len(loads) == 1 and loads[0].get('requestedURL') == value['requestedURL']
         and loads[0].get('actualURL') == value.get('actualURL'), 'native suggestion did not produce exactly one actual page load')
    home, after = value.get('home', {}), value.get('after', {})
    need(value.get('homeMark') == {'src': 'mouse-head.svg', 'filter': 'none'},
         'ordinary new tab does not preserve the black Mouse favicon in both themes')
    grid = value.get('savedGrid', {})
    need(set(grid) == {'tree', 'slots', 'active'} and grid == value.get('afterGrid')
         and isinstance(grid['slots'], dict) and len(grid['slots']) == 2 and grid['active'] in grid['slots'],
         'native new-tab search changed the saved grid')
    need(home == {'id': value.get('tabId'), 'internal': True, 'hadNativePage': False}
         and after.get('id') == home['id'] and after.get('sameHomeTab') is True and after.get('newNativePage') is True
         and type(after.get('webContentsId')) is int and after['webContentsId'] > 0 and after.get('url') == value.get('actualURL'),
         'local new tab did not keep its ID while creating its first real guest')
    before, current = value.get('otherBefore', []), value.get('otherAfter', [])
    need(len(before) == len(current) == 2, 'other live pages are unbound')
    for a, b in zip(before, current): same_page(a, b)
    native_input(value.get('input'), pid); native_input(value.get('submit'), pid)


def image(read, name, claimed_digest, dimensions):
    need(isinstance(name, str) and re.fullmatch(r'mouse-643-[a-z0-9-]+\.png', name), 'unsafe native screenshot name')
    raw = read(name)
    need(sha(raw) == claimed_digest, 'actual PNG hash differs')
    result = P.decode_png(raw, name)
    need(dimensions == {key: result[key] for key in ('width', 'height')}, 'actual PNG dimensions differ')
    return result


# This private imported reader retains all original native-page and pixel gates;
# only this new suite's explicit PNG filename boundary differs from631.
P.read_png = image


def shell_capture(read, value, expected_name, label):
    need(value.get('filename') == expected_name and value.get('shellOnly') is True
         and value.get('source') == 'globalCapture.acquire(display)' and value.get('kind') == 'screen'
         and isinstance(value.get('backend'), str) and value['backend'], 'missing real OS shell capture')
    actual = image(read, expected_name, value.get('sha256'), value.get('pixelSize'))
    need(value.get('displayFilename') == expected_name[:-4] + '-display.png', 'wrong full OS display')
    full = image(read, value['displayFilename'], value.get('displaySha256'), value.get('screenPixelSize'))
    display, bounds = P.rectangle(value.get('display', {}).get('bounds'), 'display'), P.rectangle(value.get('contentBounds'), 'window')
    sx, sy = full['width'] / display['width'], full['height'] / display['height']
    left, top = (bounds['x'] - display['x']) * sx, (bounds['y'] - display['y']) * sy
    crop = {'x': math.floor(left), 'y': math.floor(top), 'width': math.ceil(left + bounds['width'] * sx) - math.floor(left),
            'height': math.ceil(top + bounds['height'] * sy) - math.floor(top)}
    need(value.get('cropPixels') == crop and actual['width'] == crop['width'] and actual['height'] == crop['height']
         and crop['x'] >= 0 and crop['y'] >= 0 and crop['x'] + crop['width'] <= full['width']
         and crop['y'] + crop['height'] <= full['height'], 'actual window crop differs')
    mapping = {'scaleX': sx, 'scaleY': sy, 'originX': left - crop['x'], 'originY': top - crop['y']}
    need(all(P.finite(value.get('mapping', {}).get(k)) and abs(value['mapping'][k] - v) < 1e-8 for k, v in mapping.items()), 'native DPI mapping differs')
    for x in range(0, actual['width'], max(1, actual['width'] // 37)):
        for y in range(0, actual['height'], max(1, actual['height'] // 31)):
            need(P.pixel(actual, x, y) == P.pixel(full, x + crop['x'], y + crop['y']), 'window is not the archived display crop')
    regions = value.get('shell', {}).get('regions', [])
    need(len(regions) == 1 and regions[0].get('label') == label, 'wrong actual feature surface')
    box = P.rectangle(regions[0].get('bounds'), 'feature surface')
    need(box['width'] >= 65 and box['height'] >= 25 and box['x'] >= 0 and box['y'] >= 0
         and box['x'] + box['width'] <= bounds['width'] and box['y'] + box['height'] <= bounds['height'], 'feature surface is a trivial/outside patch')
    P.verify_shell(read, value, actual, expected_count=1)
    need(value.get('attempts') and 1 <= len(value['attempts']) <= 6 and value['attempts'][-1].get('accepted') is True,
         'bounded OS surface capture never passed')
    need(all(value.get(key) == [] for key in ('native', 'content', 'probes')), 'shell overlay wrongly claims native page pixel proof')


def verify(read, expected_platform=None, expected_arch=None):
    artifacts = {}
    def bound(name):
        need(isinstance(name, str) and re.fullmatch(r'mouse-643-[a-z0-9.-]+', name) and '..' not in name, 'unsafe artifact name')
        raw = read(name)
        need(isinstance(raw, bytes) and 0 < len(raw) <= 96 * 1024**2, 'empty/oversized artifact')
        artifacts[name] = {'file': name, 'bytes': len(raw), 'sha256': sha(raw)}
        return raw
    names = ('mouse-643-polish.json', 'mouse-643-polish-write.json', 'mouse-643-polish-processes.json')
    facts, written, processes = [json.loads(bound(name)) for name in names]
    pid, write, restart = facts.get('pid'), facts.get('write', {}), facts.get('restart', {})
    need((facts.get('platform'), facts.get('arch')) == ('darwin', 'arm64')
         and expected_platform in (None, 'darwin') and expected_arch in (None, 'arm64'), '643 is Mac arm64 only')
    need(facts.get('schema') == 1 and facts.get('version') == VERSION and facts.get('packaged') is True
         and facts.get('physicalUserDeviceVerified') is False and facts.get('phase') == 'read' and facts.get('ok') is True
         and facts.get('writeComplete') is True and facts.get('awaitingRestart') is False and type(pid) is int and pid > 0
         and facts.get('writePid') == pid and PurePosixPath(facts.get('profile', '')).is_absolute(), 'not completed installed643 evidence')
    need(written.get('ok') is False and written.get('phase') == 'write' and written.get('writeComplete') is True
         and written.get('awaitingRestart') is True and written.get('write') == write, 'original native write receipt was replaced')
    for key in ('schema', 'version', 'platform', 'arch', 'packaged', 'physicalUserDeviceVerified', 'profile', 'pid', 'writePid'):
        need(written.get(key) == facts.get(key), 'original native process identity changed')
    for row in (facts, written):
        need(not any(row.get(key) for key in ('error', 'restoreError', 'cleanupError'))
             and row.get('cleanup', {}).get('restored') is True and row['cleanup'].get('desktopStateRestored') is True, 'native fixture cleanup failed')
    need(processes.get('schema') == 1 and processes.get('version') == VERSION and processes.get('platform') == 'darwin'
         and processes.get('arch') == 'arm64' and processes.get('profile') == facts['profile']
         and PurePosixPath(processes.get('executable', '')).is_absolute()
         and re.fullmatch('[a-f0-9]{64}', processes.get('executableSha256', ''))
         and processes.get('reportSha256') == sha(bound(names[0])), 'installed executable/profile/report binding differs')
    for phase, part, report, limit, native_limit, marker in (
            ('write', write, names[1], 300000, 270000, 'MOUSE_643_POLISH_WRITE_PASS'),
            ('read', restart, names[0], 120000, 90000, 'MOUSE_643_POLISH_NATIVE_PASS')):
        receipt = processes.get(phase, {}); child = part.get('pid'); log_name = 'mouse-643-polish-' + phase + '.log'
        need(type(child) is int and child > 0 and child == receipt.get('pid') and (child == pid if phase == 'write' else child != pid)
             and receipt.get('exitCode') == 0 and P.finite(receipt.get('elapsedMs')) and 0 < receipt['elapsedMs'] <= limit,
             'distinct actual process/native exit/budget missing')
        need(P.finite(part.get('startedAt')) and P.finite(part.get('completedAt'))
             and 0 < part['completedAt'] - part['startedAt'] <= native_limit, 'native phase time budget differs')
        raw = bound(log_name); lines = raw.decode('utf-8', 'strict').splitlines()
        need(receipt.get('report') == report and receipt.get('reportSha256') == sha(bound(report))
             and receipt.get('log') == log_name and receipt.get('logSha256') == sha(raw)
             and receipt.get('requiredMarkers') == [marker] and marker in lines
             and any(re.fullmatch(r'MOUSE_643_PROCESS_RETURN pid=' + str(child) + r' code=0 elapsedMs=\d+', line) for line in lines),
             'native process logs and actual phase reports differ')
    need(write.get('fixtureOnly') is True and write.get('externalSearchProviderVerified') is False and write.get('persistedTheme') == 'light', 'fixture provenance/persisted test state differs')
    origin = write.get('fixtureOrigin', '')
    need(re.fullmatch(r'http://127\.0\.0\.1:\d+', origin) and written.get('fixtureOrigin') == facts.get('fixtureOrigin') == origin,
         'original owned HTTP fixture identity changed')
    inputs, original_inputs = facts.get('nativeInputs', []), written.get('nativeInputs', [])
    need(inputs == original_inputs and len(inputs) >= 20, 'native input ledger changed across restart')
    for value in inputs: native_input(value, pid)
    rows = write.get('chrome', [])
    need([(r.get('mode'), r.get('theme')) for r in rows] == [('rounded', 'light'), ('rounded', 'dark'), ('square', 'light'), ('square', 'dark')], 'both real Mac shapes/themes are required')
    captures = facts.get('captures', [])
    need([c.get('filename') for c in captures] == list(CAPTURES) and written.get('captures') == captures[:-1], 'native frame ledger differs')
    by_name = {c['filename']: c for c in captures}
    for row in rows:
        chrome(row.get('state', {}), row['theme'], row['mode']); media(row.get('media', {}), row['theme'])
        need(row.get('native') == {'source': row['theme'], 'dark': row['theme'] == 'dark'}, 'actual native theme differs')
        name = 'mouse-643-chrome-' + row['mode'] + '-' + row['theme'] + '.png'
        need(row.get('capture') == name, 'chrome is not bound to its actual frame')
        P.verify_capture(bound, by_name[name], name, row.get('pages', []), shell=True, shell_count=1)
        if row['mode'] == 'square':
            hover = row.get('hover', {}); delivery = hover.get('delivery', {})
            need(delivery.get('warpResult') == 0 and delivery.get('postAccess') is True
                 and all(P.finite(hover.get('actual', {}).get(k)) and abs(hover['actual'][k] - hover.get('point', {}).get(k, -999)) <= 1 for k in ('x', 'y')),
                 'actual native pointer never reached traffic controls')
            controls = hover.get('state', {}).get('traffic', [])
            need(len(controls) == 3, 'hover traffic controls missing')
            for c, expected in zip(controls, ((255,98,90), (255,192,66), (48,206,85))):
                need(rgb(c.get('background')) == expected and rgb(c.get('color')) == (48,40,41), 'custom theme obscures native traffic feedback')
            name = 'mouse-643-traffic-' + row['theme'] + '.png'; need(hover.get('capture') == name, 'traffic native frame missing')
            shell_capture(bound, by_name[name], name, '.traffic-space')
    drags = facts.get('drags', [])
    need(len(drags) == 3 and written.get('drags') == drags, 'native resize/title/favicon drags missing')
    for value in drags: native_drag(value, pid)
    divider = write.get('divider', {})
    need(divider.get('drag') == drags[0] and drags[0].get('selector') == '.divider[data-path=""]'
         and abs(divider.get('before', {}).get('tree', {}).get('ratio', 0) - divider.get('after', {}).get('tree', {}).get('ratio', 0)) > .005, 'native square divider did not resize')
    for index, key in ((1, 'tabDrag'), (2, 'faviconDrag')):
        row = write.get(key, {})
        need(row.get('drag') == drags[index] and row.get('after', {}).get('slots', {}).get(row.get('targetPane')) == row.get('sourceTab'), 'native drag did not route its actual tab')
    need('.tab-title' in drags[1].get('selector', '') and '.pane-icon' in drags[2].get('selector', ''), 'title or favicon drag hotspot was bypassed')
    address = write.get('address', {})
    same_page(address.get('before'), address.get('afterCopy')); same_page(address.get('otherBefore'), address.get('otherAfter'))
    need(address['before'].get('url') == origin + '/page/0/' and address['otherBefore'].get('url') == origin + '/page/2/',
         'address actions do not belong to the owned HTTP pages')
    need(address.get('copied') == address['before']['url'] and address.get('clipboardRestored') is True
         and address.get('activeDesk') == address['otherBefore']['desk'] and address['activeDesk'] != address['before']['desk'], 'native clipboard/cross-desktop activation differs')
    selected = [r for r in address.get('rows', []) if r.get('id') == address['otherBefore']['id']]
    need(len(selected) == 1 and selected[0].get('kind') == 'open' and selected[0].get('desk') == address['activeDesk']
         and selected[0].get('title') == address['otherBefore']['url'] and selected[0].get('icon', '').startswith('data:image/'), 'other-desktop real favicon entry missing')
    for key in ('copy', 'open', 'choose'): need(address.get(key) in inputs, 'native address user action missing')
    need(address.get('capture') == CAPTURES[6], 'address menu native frame missing'); shell_capture(bound, by_name[CAPTURES[6]], CAPTURES[6], '#mouse-address-page-list')
    searches = write.get('search', [])
    need(len(searches) == 2, 'both native search themes required')
    for index, theme in enumerate(('light', 'dark')):
        row = searches[index]; search(row, theme, pid)
        need(row.get('actualURL') == origin + '/page/3/', 'search fixture committed outside its owned HTTP origin')
        need(row.get('input') in inputs and row.get('submit') in inputs and row.get('capture') == CAPTURES[7+index], 'native suggestion action/frame not in ledger')
        shell_capture(bound, by_name[CAPTURES[7+index]], CAPTURES[7+index], '.pane.active .home-search-suggestions')
    need(len([h for h in write.get('httpHits', []) if h.get('path') == '/suggest' and h.get('query') == 'mouse browser']) == 2, 'actual loopback provider requests missing')
    schemes = write.get('scheme', [])
    need([s.get('theme') for s in schemes] == ['dark', 'light'], 'actual existing/future page theme sequence missing')
    for row in schemes:
        media(row.get('existing', {}), row['theme']); media(row.get('future', {}), row['theme'], initial=True)
        same_page(row.get('before'), row.get('after'))
        need(row.get('native') == {'source': row['theme'], 'dark': row['theme'] == 'dark'}, 'page theme differs from nativeTheme')
    private = write.get('privateScheme', {}); media(private.get('private', {}), 'dark', initial=True)
    media(private.get('normalMedia', {}), 'light'); same_page(private.get('normalBefore'), private.get('normalAfter'))
    need(private.get('native') == {'source': 'light', 'dark': False}, 'leaving private mode did not restore the actual normal theme')
    need(restart.get('initialNative') == {'source': 'light', 'dark': False}
         and restart.get('initialRenderer') == {'theme': 'light', 'dark': False}, 'startup did not apply saved theme before pages')
    media(restart.get('media', {}), 'light', initial=True)
    need(restart.get('capture') == CAPTURES[-1], 'restart native frame missing')
    # The restarted owned pair is bound directly to its native capture metadata.
    final = by_name[CAPTURES[-1]]
    expected = [{'id': n['tabId'], 'index': n['index'], 'desk': n['desk'], 'webContentsId': n['webContentsId'],
                 'identity': next(c['identity'] for c in final['content'] if c['tabId'] == n['tabId'])} for n in final.get('native', [])]
    need(len(expected) == 2 and {p['index'] for p in expected} == {0, 1}
         and expected[0]['identity'] == restart['media']['identity']
         and re.fullmatch(r'http://127\.0\.0\.1:\d+', restart.get('fixtureOrigin', ''))
         and restart['media'].get('url') == restart['fixtureOrigin'] + '/page/0/', 'restart real page identity differs')
    P.verify_capture(bound, final, CAPTURES[-1], expected, shell=True, shell_count=1)
    for index, value in enumerate(captures): need(value.get('pid') == (restart['pid'] if index == len(captures)-1 else pid), 'native capture belongs to another process')
    return {'schema': 1, 'version': VERSION, 'ok': True, 'platform': 'darwin', 'arch': 'arm64',
            'processes': {'writePid': pid, 'readPid': restart['pid']}, 'nativeCaptures': list(CAPTURES),
            'checks': list(TOKENS), 'externalSearchProviderVerified': False, 'physicalUserDeviceVerified': False,
            'artifacts': sorted(artifacts.values(), key=lambda item: item['file'])}


def run(directory, *, platform='darwin', arch='arm64'):
    directory = Path(directory).resolve()
    result = verify(lambda name: (directory / name).read_bytes(), expected_platform=platform, expected_arch=arch)
    (directory / 'mouse-643-polish-acceptance.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--platform', choices=('darwin',), required=True)
    parser.add_argument('--arch', choices=('arm64',), required=True)
    args = parser.parse_args(); run(args.directory, platform=args.platform, arch=args.arch)
    print('MOUSE_643_POLISH_ACCEPTANCE_PASS')


if __name__ == '__main__': main()
