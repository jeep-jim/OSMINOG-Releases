#!/usr/bin/env python3
"""Independently verify installed Mac644 subscriptions and page-theme evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit

_spec = importlib.util.spec_from_file_location('mouse644_retained_pixels', Path(__file__).with_name('mouse644-polish-evidence.py'))
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)
P = R.P
VERSION = '6.0.44'
TOKENS = ('native644-filter-subscriptions-and-conditional-refresh',
          'native644-page-theme-sync-and-restoration', 'native644-private-isolation-and-restart')
CAPTURES = tuple('mouse-644-' + name + '.png' for name in (
    'theme-light', 'theme-dark', 'generic-light', 'generic-dark', 'filters-light', 'filters-dark', 'generic-restored', 'restored'))
COLORS = {'github': {'light': (255, 255, 255), 'dark': (13, 17, 23)},
          'standard': {'light': (241, 244, 249), 'dark': (27, 41, 55)},
          'attribute': {'light': (248, 240, 220), 'dark': (42, 28, 12)},
          'class': {'light': (223, 248, 235), 'dark': (10, 42, 29)}}
SOURCES = {'easylist': 'https://easylist-downloads.adblockplus.org/easylist.txt',
           'ruadlist': 'https://easylist-downloads.adblockplus.org/ruadlist.txt'}
CUSTOM_URL = 'https://filters.example.org/mouse-644.txt'
BUNDLED = {'easylist': 'bca770b29edb08af4f6680431cc20823bdf13446e8f43b4c24b2c9bb381e6c25',
           'ruadlist': '7e23435e9380b15159e4a165ce5b4c472090919187f7a8b1b307979c10c9bddb'}


def need(value, message):
    if not value:
        raise ValueError('Mouse644 sync: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def image(read, name, claimed_digest, dimensions):
    need(isinstance(name, str) and re.fullmatch(r'mouse-644-[a-z0-9-]+\.png', name), 'unsafe native screenshot name')
    raw = read(name)
    need(sha(raw) == claimed_digest, 'actual PNG hash differs')
    result = P.decode_png(raw, name)
    need(dimensions == {key: result[key] for key in ('width', 'height')}, 'actual PNG dimensions differ')
    return result


# Import a private copy of the retained reader. Keep its original OS-display,
# native-page, current-shell and pixel checks; only644's PNG boundary differs.
R.image = image
P.read_png = image


def read_envelope(bound, expected_platform=None, expected_arch=None):
    names = ('mouse-644-sync.json', 'mouse-644-sync-write.json', 'mouse-644-sync-processes.json')
    facts, written, processes = [json.loads(bound(name)) for name in names]
    pid, write, restart = facts.get('pid'), facts.get('write', {}), facts.get('restart', {})
    need((facts.get('platform'), facts.get('arch')) == ('darwin', 'arm64')
         and expected_platform in (None, 'darwin') and expected_arch in (None, 'arm64'), '644 is Mac arm64 only')
    need(facts.get('schema') == 1 and facts.get('version') == VERSION and facts.get('packaged') is True
         and facts.get('physicalUserDeviceVerified') is False and facts.get('phase') == 'read' and facts.get('ok') is True
         and facts.get('writeComplete') is True and facts.get('awaitingRestart') is False and type(pid) is int and pid > 0
         and facts.get('writePid') == pid and PurePosixPath(facts.get('profile', '')).is_absolute(), 'not completed installed644 evidence')
    need(written.get('ok') is False and written.get('phase') == 'write' and written.get('writeComplete') is True
         and written.get('awaitingRestart') is True and written.get('write') == write, 'original native write receipt was replaced')
    for key in ('schema', 'version', 'platform', 'arch', 'packaged', 'physicalUserDeviceVerified', 'profile', 'pid', 'writePid'):
        need(written.get(key) == facts.get(key), 'original native process identity changed')
    for row in (facts, written):
        need(not any(row.get(key) for key in ('error', 'restoreError', 'cleanupError'))
             and row.get('cleanup', {}).get('restored') is True and row['cleanup'].get('desktopStateRestored') is True,
             'native fixture cleanup failed')
    need(processes.get('schema') == 1 and processes.get('version') == VERSION and processes.get('platform') == 'darwin'
         and processes.get('arch') == 'arm64' and processes.get('profile') == facts['profile']
         and PurePosixPath(processes.get('executable', '')).is_absolute()
         and re.fullmatch('[a-f0-9]{64}', processes.get('executableSha256', ''))
         and processes.get('reportSha256') == sha(bound(names[0])), 'installed executable/profile/report binding differs')
    for phase, part, report, limit, native_limit, marker in (
            ('write', write, names[1], 300000, 270000, 'MOUSE_644_SYNC_WRITE_PASS'),
            ('read', restart, names[0], 120000, 90000, 'MOUSE_644_SYNC_NATIVE_PASS')):
        receipt = processes.get(phase, {}); child = part.get('pid'); log_name = 'mouse-644-sync-' + phase + '.log'
        need(type(child) is int and child > 0 and child == receipt.get('pid') and (child == pid if phase == 'write' else child != pid)
             and receipt.get('exitCode') == 0 and P.finite(receipt.get('elapsedMs')) and 0 < receipt['elapsedMs'] <= limit,
             'distinct actual process/native exit/budget missing')
        need(P.finite(part.get('startedAt')) and P.finite(part.get('completedAt'))
             and 0 < part['completedAt'] - part['startedAt'] <= native_limit, 'native phase time budget differs')
        raw = bound(log_name); lines = raw.decode('utf-8', 'strict').splitlines()
        need(receipt.get('report') == report and receipt.get('reportSha256') == sha(bound(report))
             and receipt.get('log') == log_name and receipt.get('logSha256') == sha(raw)
             and receipt.get('requiredMarkers') == [marker] and marker in lines
             and any(re.fullmatch(r'MOUSE_644_PROCESS_RETURN pid=' + str(child) + r' code=0 elapsedMs=\d+', line) for line in lines),
             'native process logs and actual phase reports differ')
    need(write.get('fixtureOnly') is True and write.get('liveGitHubVerified') is False,
         'owned fixture cannot claim a live GitHub session')
    inputs = facts.get('nativeInputs', [])
    need(inputs == written.get('nativeInputs') and isinstance(inputs, list) and inputs, 'native input ledger changed across restart')
    for value in inputs:
        R.native_input(value, pid)
    captures = facts.get('captures', [])
    need([c.get('filename') for c in captures] == list(CAPTURES) and written.get('captures') == captures[:-2],
         'native frame ledger differs')
    for index, value in enumerate(captures):
        need(value.get('pid') == (restart['pid'] if index >= len(captures) - 2 else pid), 'native capture belongs to another process')
    return facts, written, write, restart, {c['filename']: c for c in captures}


def github(value, theme, original, *, synced=True, same_document=True):
    url = urlsplit(value.get('url', ''))
    need(url.scheme == 'https' and url.hostname == 'github.com', 'theme fixture did not exercise the real adapter origin')
    need(value.get('storage') == original.get('storage') == 'site-authored-value'
         and value.get('normalOnly') == 'owned-normal-state'
         and 'mouse644_normal=normal-only' in [v.strip() for v in value.get('cookie', '').split(';')],
         'normal page lost its own cookie or localStorage')
    if same_document:
        need(value.get('cookie') == original.get('cookie'), 'page theme changed its current document cookies')
    if synced:
        need(value.get('colorMode') == theme and value.get('lightTheme') == 'light'
             and value.get('darkTheme') == original.get('attributes', {}).get('data-dark-theme')
             and value.get('dark') is (theme == 'dark'), 'actual GitHub attributes or native color preference differ')
    else:
        need({'data-' + name: value.get(key) for name, key in (('color-mode', 'colorMode'), ('light-theme', 'lightTheme'), ('dark-theme', 'darkTheme'))} == original.get('attributes'),
             'disabling synchronization did not restore the exact original attributes')
    actual_theme = theme if synced else original['attributes']['data-color-mode']
    need(R.rgb(value.get('background')) == COLORS['github'][actual_theme], 'GitHub fixture rendered another theme')
    need(R.rgb(value.get('color')) == COLORS['github'][actual_theme], 'GitHub swatch disagrees with its document theme')


def standard(value, theme):
    need(value.get('dark') is (theme == 'dark') and R.rgb(value.get('background')) == COLORS['standard'][theme]
         and R.rgb(value.get('color')) == COLORS['standard'][theme],
         'standard page media preference or rendered theme differs')


def theme_pixels(bound, capture, theme, kinds=None):
    """Decode swatches at coordinates derived from the actual native page tree."""
    need(capture.get('theme') == theme, 'native theme frame identity differs')
    kinds = {0: 'github', 1: 'standard'} if kinds is None else kinds
    probes, native = capture.get('themeProbes', []), capture.get('native', [])
    need(len(probes) == len(native) == 2 and {v.get('index') for v in probes} == set(kinds),
         'both actual pages require independent theme pixel probes')
    actual = image(bound, capture['filename'], capture.get('sha256'), capture.get('pixelSize'))
    full = image(bound, capture['displayFilename'], capture.get('displaySha256'), capture.get('screenPixelSize'))
    mapping, crop = capture['mapping'], capture['cropPixels']
    for probe in probes:
        owners = [v for v in native if v.get('tabId') == probe.get('tabId') and v.get('index') == probe['index']]
        need(len(owners) == 1, 'theme swatch belongs to another native page')
        page = P.rectangle(owners[0].get('bounds'), 'native page')
        box = P.rectangle(probe.get('bounds'), 'page theme swatch')
        need(box['width'] == 120 and box['height'] == 32 and box['y'] == 180
             and abs(box['x'] - page['width'] * .08) <= .5
             and box['x'] >= 0 and box['y'] + box['height'] <= page['height']
             and box['x'] + box['width'] <= page['width'], 'theme swatch geometry differs from its fixed fixture')
        expected = COLORS[kinds[probe['index']]][theme]
        need(R.rgb(probe.get('color')) == expected, 'claimed theme swatch color differs')
        for fx, fy in ((.2, .25), (.5, .25), (.8, .25), (.3, .75), (.7, .75)):
            x = math.floor(mapping['originX'] + (page['x'] + box['x'] + box['width'] * fx) * mapping['scaleX'])
            y = math.floor(mapping['originY'] + (page['y'] + box['y'] + box['height'] * fy) * mapping['scaleY'])
            measured = P.pixel(actual, x, y)
            need(measured == P.pixel(full, x + crop['x'], y + crop['y']) and measured[3] == 255
                 and all(abs(measured[i] - expected[i]) <= 2 for i in range(3)), 'decoded OS frame has stale or wrong page-theme pixels')


def fixture_text(id_):
    return ('[Adblock Plus 2.0]\n! Owned Mouse644 HTTP fixture, never a public subscription snapshot\n'
            + '\n'.join('||fixture-' + id_ + '-' + str(i) + '.invalid^' for i in range(60))
            + '\n*/mouse-644-' + ('custom' if id_ == 'custom' else 'ad') + '/*$xmlhttprequest\n')


def milliseconds(value):
    need(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z', value),
         'missing exact UTC filter timestamp')
    return round(datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc).timestamp() * 1000)


def subscriptions(value, *, enabled=True, custom=None):
    need(isinstance(value, dict) and value.get('enabled') is enabled and value.get('privateMode') is False
         and value.get('phase') == ('ready' if enabled else 'off') and value.get('updateIntervalHours') == 12
         and value.get('maxSubscriptions') == 8 and type(value.get('revision')) is int and value['revision'] >= 0,
         'filter service state/explicit control policy differs')
    rows = value.get('subscriptions', [])
    need(isinstance(rows, list) and len(rows) == (3 if custom is not None else 2)
         and len({r.get('id') for r in rows}) == len(rows), 'subscription inventory differs')
    builtins = {r.get('id'): r for r in rows if r.get('builtin') is True}
    need(set(builtins) == set(SOURCES), 'built-in subscription identity differs')
    for id_, row in builtins.items():
        need(row.get('url') == SOURCES[id_] and row.get('enabled') is True
             and isinstance(row.get('name'), str) and row['name'] and row.get('authors') and row.get('license'),
             'built-in list source, enablement or attribution differs')
    if custom is not None:
        selected = [r for r in rows if r.get('builtin') is False]
        need(len(selected) == 1 and selected[0].get('url') == CUSTOM_URL and selected[0].get('enabled') is custom,
             'custom list identity/enablement differs')
    for row in rows:
        kind = row['id'] if row['builtin'] else 'custom'
        need(row.get('origin') == 'cache' and row.get('sha256') == sha(fixture_text(kind).encode())
             and row.get('ruleCount') == 61 and milliseconds(row.get('checkedAt')) >= milliseconds(row.get('updatedAt')),
             'cached list bytes, supported rules or timestamps differ from the actual HTTP fixture')
    need(value.get('lists') == (3 if custom is True else 2)
         and value.get('rules') == (182 if custom is True else 121), 'effective matcher does not reflect the enabled subscriptions')
    return {r['id']: r for r in rows}


def verify_filters(write, restart, inputs):
    row = write.get('filters', {})
    initial = row.get('initial', {})
    need(initial.get('enabled') is False and initial.get('phase') == 'off', 'new profile did not start with filtering off')
    offline = row.get('offline', {})
    need(offline.get('enabled') is True and offline.get('phase') == 'fallback' and offline.get('lists') == 2
         and isinstance(offline.get('subscriptions'), list) and len(offline['subscriptions']) == 2,
         'offline first use did not retain both shipped filter lists')
    bundled = {value.get('id'): value for value in offline['subscriptions']}
    need(set(bundled) == set(BUNDLED), 'offline bundled inventory differs')
    for id_, value in bundled.items():
        need(value.get('url') == SOURCES[id_] and value.get('builtin') is True and value.get('enabled') is True
             and value.get('origin') == 'bundled' and value.get('sha256') == BUNDLED[id_]
             and type(value.get('ruleCount')) is int and value['ruleCount'] > 10
             and value.get('checkedAt') is None and value.get('updatedAt') == '2026-11-28T01:52:00.000Z'
             and value.get('phase') == 'stale' and value.get('lastError') == 'MOUSE_ADBLOCK_LIST_UNAVAILABLE',
             'offline fallback used a seed or unrelated bytes instead of the actual shipped list')
    updated = subscriptions(row.get('after200'))
    checked = subscriptions(row.get('after304'))
    failed = subscriptions(row.get('afterFailure'))
    for id_ in SOURCES:
        first, next_, stale = updated[id_], checked[id_], failed[id_]
        need(first['phase'] == next_['phase'] == 'ready' and first.get('lastError') is None and next_.get('lastError') is None
             and first['updatedAt'] == first['checkedAt']
             and next_['updatedAt'] == first['updatedAt'] and milliseconds(next_['checkedAt']) > milliseconds(first['checkedAt']),
             'conditional refresh redownloaded the body or did not advance its check time')
        need(stale['phase'] == 'stale' and stale['lastError'] == 'MOUSE_ADBLOCK_LIST_UNAVAILABLE'
             and stale['updatedAt'] == next_['updatedAt'] and stale['checkedAt'] == next_['checkedAt']
             and milliseconds(stale.get('nextRetryAt')) > milliseconds(stale['checkedAt']),
             'server failure did not retain the last valid body/check timestamp with bounded retry')
    added = subscriptions(row.get('customAdded'), custom=True)
    custom = next(v for v in added.values() if v['builtin'] is False)
    disabled = subscriptions(row.get('customDisabled'), custom=False)
    need(disabled[custom['id']]['phase'] == 'disabled' and disabled[custom['id']]['updatedAt'] == custom['updatedAt']
         and disabled[custom['id']]['checkedAt'] == custom['checkedAt'], 'disabling a subscription changed or reloaded its cached body')
    removed = subscriptions(row.get('customRemoved'))
    off = subscriptions(row.get('off'), enabled=False)
    persisted = subscriptions(row.get('persisted'))
    restored = subscriptions(restart.get('subscriptions'))
    need(custom['id'] not in removed and custom['id'] not in restored, 'removed custom subscription returned after restart')
    for id_ in SOURCES:
        need(off[id_]['phase'] == 'off' and persisted[id_]['phase'] == restored[id_]['phase'] == 'ready'
             and all(restored[id_][key] == persisted[id_][key] for key in ('url', 'enabled', 'sha256', 'ruleCount', 'updatedAt', 'checkedAt')),
             'filter cache or subscription preferences changed on actual restart')
    for name in ('blocked', 'stillBlocked', 'customBlocked'):
        need(row.get(name) == {'ok': False, 'error': 'TypeError'}, 'native webRequest did not block ' + name)
    need(restart.get('blocked') == {'ok': False, 'error': 'TypeError'}, 'restored native matcher did not block the fixture')
    for name in ('beforeEnabled', 'customAllowed', 'allowed'):
        need(row.get(name) == {'ok': True, 'status': 200}, 'explicit user control did not allow ' + name)
    ledger = write.get('requests', [])
    need(isinstance(ledger, list) and ledger, 'actual HTTP request ledger missing')
    for id_ in (*SOURCES, 'custom'):
        requests = [r for r in ledger if r.get('path') == '/lists/' + id_]
        expected = [200] if id_ == 'custom' else [503, 200, 304, 503, 304]
        need([r.get('status') for r in requests] == expected, 'actual conditional HTTP response sequence differs')
        previous_at = -1
        for index, request in enumerate(requests):
            need(request.get('method') == 'GET' and request.get('cookie') is None and request.get('authorization') is None
                 and request.get('etag') == '"mouse644-' + id_ + '-v1"'
                 and request.get('ifNoneMatch') == (None if (id_ == 'custom' or index < 2) else request['etag'])
                 and request.get('bodySha256') == (sha(fixture_text(id_).encode()) if request['status'] == 200 else None)
                 and P.finite(request.get('at')) and request['at'] >= previous_at,
                 'HTTP refresh sent credentials or lost its actual validator/body identity')
            previous_at = request['at']
    need(len([r for r in ledger if r.get('path') == '/mouse-644-ad/resource']) == 2
         and len([r for r in ledger if r.get('path') == '/mouse-644-custom/resource']) == 1,
         'blocked requests reached the actual fixture server')
    selectors = [value.get('selector') for value in inputs]
    for selector in ('[data-setting="blockAds"]', '#settings-filter-refresh', '#settings-filter-url', '#settings-filter-add',
                     '[data-filter-toggle="' + custom['id'] + '"]', '[data-filter-remove="' + custom['id'] + '"]'):
        need(selector in selectors, 'filter change lacked its actual trusted native control: ' + selector)
    return persisted


def filter_ui(value, theme, expected):
    need(value.get('open') is True and value.get('privateMode') is False and value.get('theme') == theme
         and value.get('refresh', {}).get('disabled') is False and value.get('urlDisabled') is False
         and value.get('urlValue') == '' and value.get('addDisabled') is True,
         'normal filter controls are not usable in both themes')
    P.rectangle(value.get('bounds'), 'settings dialog')
    P.rectangle(value.get('refresh', {}).get('bounds'), 'refresh control')
    rows = value.get('rows', [])
    need(len(rows) == 2 and {r.get('id') for r in rows} == set(SOURCES), 'actual settings list did not reflect the restored subscription inventory')
    for row in rows:
        source = expected[row['id']]
        need(row.get('enabled') is True and row.get('disabled') is False and row.get('name') == source['name']
             and isinstance(row.get('text'), str) and source['name'] in row['text'], 'actual filter row differs from its service state')
        P.rectangle(row.get('bounds'), 'subscription row')


def verify_themes(bound, facts, write, restart, captures):
    original = write.get('originalGithub', {})
    need(original.get('attributes') == {'data-color-mode': 'dark', 'data-light-theme': 'dark', 'data-dark-theme': 'dark_dimmed'}
         and original.get('storage') == 'site-authored-value'
         and 'mouse644_normal=normal-only' in [v.strip() for v in original.get('cookie', '').split(';')],
         'site-authored original attributes, cookie and storage were not recorded')
    need(write.get('githubFixtureOrigin') == 'https://github.com'
         and re.fullmatch(r'http://127\.0\.0\.1:\d+', write.get('fixtureOrigin', '')),
         'owned adapter and HTTP fixture origins differ')
    themes = write.get('themes', [])
    need([row.get('theme') for row in themes] == ['light', 'dark'], 'both native page themes are required')
    for row in themes:
        theme = row['theme']
        need(row.get('native') == {'source': theme, 'dark': theme == 'dark'}, 'nativeTheme did not receive the selected application theme')
        before, after = row.get('before', []), row.get('after', [])
        need(len(before) == len(after) == 2 and [v.get('index') for v in before] == [0, 1], 'both original live pages are missing')
        for first, next_ in zip(before, after):
            R.same_page(first, next_)
        need(before[0]['url'] == 'https://github.com/page/0/' and before[1]['url'] == write['fixtureOrigin'] + '/page/1/',
             'theme switch changed an unrelated document')
        github(row.get('github', {}), theme, original)
        standard(row.get('standard', {}), theme)
        for index, key in enumerate(('github', 'standard')):
            need(row[key].get('identity') == after[index]['identity'] and row[key].get('timeOrigin') == after[index]['timeOrigin'],
                 'theme readback belongs to another actual document')
        name = 'mouse-644-theme-' + theme + '.png'
        need(row.get('capture') == name, 'theme readback is not bound to its native frame')
        P.verify_capture(bound, captures[name], name, after, shell=True, shell_count=1)
        theme_pixels(bound, captures[name], theme)
    reapplied = write.get('reapplied', {})
    R.same_page(reapplied.get('before'), reapplied.get('after'))
    github(reapplied.get('snapshot', {}), 'light', original)
    need(reapplied['snapshot'].get('identity') == reapplied['after']['identity'], 'site reapplication belongs to another document')
    github(write.get('disabled', {}), 'light', original, synced=False)
    need(write['disabled'].get('dark') is False and write['disabled'].get('identity') == reapplied['after']['identity'],
         'turning the site adapter off reloaded the document or changed the native preference')
    reload_ = write.get('reload', {})
    github(reload_, 'light', original, same_document=False)
    need(P.finite(reload_.get('timeOrigin')) and reload_['timeOrigin'] > reapplied['after']['timeOrigin']
         and reload_.get('identity') != reapplied['after']['identity'] and reload_.get('initialDark') is False,
         'future document did not receive its current native theme on real reload')
    selectors = [value.get('selector') for value in facts['nativeInputs']]
    need('#theme-button' in selectors and selectors.count('[data-setting="syncWebsiteTheme"]') >= 2,
         'theme/off/on changes bypassed the exposed native controls')
    private = write.get('private', {})
    need(private.get('enabled') is True and private.get('theme') == 'dark' and private.get('normalCookieAbsent') is True,
         'private browser did not retain its separate theme service')
    view = private.get('snapshot', {})
    need(view.get('url') == 'https://github.com/page/6/' and view.get('colorMode') == 'dark'
         and view.get('lightTheme') == 'light' and view.get('darkTheme') == 'dark_dimmed' and view.get('dark') is True
         and view.get('initialDark') is True and R.rgb(view.get('background')) == COLORS['github']['dark']
         and R.rgb(view.get('color')) == COLORS['github']['dark'] and view.get('storage') == 'site-authored-value'
         and view.get('normalOnly') is None and 'mouse644_normal=' not in view.get('cookie', ''),
         'private page leaked normal root-path cookies/storage or rendered another theme')
    R.same_page(private.get('normalBefore'), private.get('normalAfter'))
    need('mouse644_normal=normal-only' in [v.strip() for v in private['normalBefore']['cookie'].split(';')],
         'normal root-path cookie was absent before private isolation was tested')
    ui = private.get('ui', {})
    need(ui.get('open') is True and ui.get('privateMode') is True and ui.get('theme') == 'dark'
         and ui.get('refresh', {}).get('disabled') is True and ui.get('urlDisabled') is True and ui.get('addDisabled') is True
         and len(ui.get('rows', [])) == 2 and all(v.get('disabled') is True for v in ui['rows'])
         and isinstance(private.get('mutationError'), str) and 'обычном' in private['mutationError'],
         'private filter controls or their actual IPC write guard were writable')
    need(restart.get('initialNative') == {'source': 'light', 'dark': False}, 'saved theme was not applied before restarted documents')
    for state in (write.get('settings', {}), restart.get('settings', {})):
        need(state.get('syncWebsiteTheme') is True and state.get('blockAds') is True and state.get('privateMode') is False,
             'explicit filtering/theme settings did not survive actual restart')
    github(restart.get('github', {}), 'light', original, same_document=False)
    standard(restart.get('standard', {}), 'light')
    need(restart['github'].get('initialDark') is False and restart['standard'].get('initialDark') is False,
         'restarted documents received a stale first-script color preference')
    name = CAPTURES[-1]
    need(restart.get('capture') == name, 'restart readback is not bound to its OS frame')
    final = captures[name]
    expected = [{'id': n['tabId'], 'index': n['index'], 'desk': n['desk'], 'webContentsId': n['webContentsId'],
                 'identity': next(c['identity'] for c in final.get('content', []) if c['tabId'] == n['tabId'])}
                for n in final.get('native', [])]
    need(len(expected) == 2 and [v.get('index') for v in expected] == [0, 1]
         and expected[0]['identity'] == restart['github'].get('identity')
         and expected[1]['identity'] == restart['standard'].get('identity'), 'restarted native pages belong to another document')
    P.verify_capture(bound, final, name, expected, shell=True, shell_count=1)
    theme_pixels(bound, final, 'light')



def generic_page(value, kind, theme, origin, *, synced=True, private=False):
    index = 7 if private else 2 if kind == 'attribute' else 3
    need(value.get('url') == origin + '/page/' + str(index) + '/', 'generic theme fixture origin/page differs')
    displayed = theme if synced else 'dark'
    need(value.get('dark') is (theme == 'dark') and value.get('storage') == 'site-authored-value',
         'generic page lost its native preference or persistent site value')
    if kind == 'attribute':
        need(value.get('dataTheme') == displayed and value.get('rootClass') == 'app-shell', 'generic attribute contract differs')
    else:
        need(value.get('dataTheme') is None and value.get('rootClass') == 'app-shell ' + displayed, 'generic class contract differs')
    need(R.rgb(value.get('background')) == COLORS[kind][displayed]
         and R.rgb(value.get('color')) == COLORS[kind][displayed], 'generic page rendered another theme')
    if private:
        need(value.get('visibility') == 'visible', 'private generic transition was not visible to the user')
        need(value.get('genericNormalOnly') is None and 'mouse644_generic_normal=' not in value.get('cookie', ''),
             'private generic document leaked normal cookie/storage')
    else:
        need(value.get('genericNormalOnly') == 'owned-generic-normal-state'
             and 'mouse644_generic_normal=normal-only' in [v.strip() for v in value.get('cookie', '').split(';')],
             'generic document lost its normal cookie/storage')


def verify_generic_themes(bound, write, restart, captures):
    generic, origin = write.get('generic', {}), write.get('fixtureOrigin')
    need(generic.get('origin') == origin, 'generic themes used another fixture origin')
    themes = generic.get('themes', [])
    need([row.get('theme') for row in themes] == ['light', 'dark'], 'both generic page themes are required')
    for row in themes:
        theme, before, after, views = row['theme'], row.get('before', []), row.get('after', []), row.get('views', [])
        need(row.get('native') == {'source': theme, 'dark': theme == 'dark'}
             and len(before) == len(after) == len(views) == 2 and [v.get('index') for v in before] == [2, 3],
             'both original generic documents and their native preference are required')
        for i, kind in enumerate(('attribute', 'class')):
            R.same_page(before[i], after[i])
            generic_page(views[i], kind, theme, origin)
            need(before[i].get('url') == origin + '/page/' + str(i + 2) + '/'
                 and views[i].get('identity') == after[i]['identity'] and views[i].get('timeOrigin') == after[i]['timeOrigin'],
                 'generic readback belongs to another live document')
        name = 'mouse-644-generic-' + theme + '.png'
        need(row.get('capture') == name, 'generic document readback lacks its native frame')
        P.verify_capture(bound, captures[name], name, after, shell=True, shell_count=1)
        theme_pixels(bound, captures[name], theme, {2: 'attribute', 3: 'class'})
    for key, synced in (('disabled', False), ('reenabled', True)):
        values = generic.get(key, [])
        need(len(values) == 2, 'both generic contracts need off/on restoration')
        for i, kind in enumerate(('attribute', 'class')):
            generic_page(values[i], kind, 'light', origin, synced=synced)
            need(values[i].get('identity') == themes[-1]['after'][i]['identity']
                 and values[i].get('timeOrigin') == themes[-1]['after'][i]['timeOrigin']
                 and values[i].get('cookie') == themes[-1]['views'][i]['cookie'],
                 'generic off/on changed the current document or cookies')
    private = write.get('private', {}).get('generic', {})
    need(len(private.get('views', [])) == 2, 'generic private theme transitions are absent')
    for theme, view in zip(('light', 'dark'), private['views']):
        generic_page(view, 'attribute', theme, origin, private=True)
    need(private['views'][0].get('identity') == private['views'][1].get('identity')
         and private['views'][0].get('timeOrigin') == private['views'][1].get('timeOrigin'),
         'private generic theme switch reloaded the document')
    R.same_page(private.get('normalBefore'), private.get('normalAfter'))
    need('mouse644_generic_normal=normal-only' in private['normalBefore'].get('cookie', ''),
         'generic normal cookie was missing before private isolation')
    restored = restart.get('generic', {})
    views = restored.get('views', [])
    need(len(views) == 2 and restored.get('capture') == 'mouse-644-generic-restored.png',
         'generic restart needs both documents and its OS frame')
    need(re.fullmatch(r'http://127\.0\.0\.1:\d+', restored.get('origin', '')), 'generic restarted fixture origin differs')
    for kind, view in zip(('attribute', 'class'), views):
        generic_page(view, kind, 'light', restored['origin'])
        need(view.get('initialDark') is False, 'generic first-script preference was stale after restart')
    capture = captures['mouse-644-generic-restored.png']
    expected = [{'id': n['tabId'], 'index': n['index'], 'desk': n['desk'], 'webContentsId': n['webContentsId'],
                 'identity': next(c['identity'] for c in capture.get('content', []) if c['tabId'] == n['tabId'])}
                for n in capture.get('native', [])]
    need(len(expected) == 2 and [v.get('index') for v in expected] == [2, 3]
         and all(expected[i]['identity'] == views[i].get('identity') for i in range(2)),
         'restarted generic native pages belong to another document')
    P.verify_capture(bound, capture, capture['filename'], expected, shell=True, shell_count=1)
    theme_pixels(bound, capture, 'light', {2: 'attribute', 3: 'class'})


def verify(read, expected_platform=None, expected_arch=None):
    artifacts = {}

    def bound(name):
        need(isinstance(name, str) and re.fullmatch(r'mouse-644-[a-z0-9.-]+', name) and '..' not in name, 'unsafe artifact name')
        raw = read(name)
        need(isinstance(raw, bytes) and 0 < len(raw) <= 96 * 1024**2, 'empty/oversized artifact')
        artifacts[name] = {'file': name, 'bytes': len(raw), 'sha256': sha(raw)}
        return raw

    facts, written, write, restart, captures = read_envelope(bound, expected_platform, expected_arch)
    verify_themes(bound, facts, write, restart, captures)
    verify_generic_themes(bound, write, restart, captures)
    persisted = verify_filters(write, restart, facts['nativeInputs'])
    for theme in ('light', 'dark'):
        name = 'mouse-644-filters-' + theme + '.png'
        filter_ui(captures[name].get('ui', {}), theme, persisted)
        R.shell_capture(bound, captures[name], name, '#settings-dialog')
    return {'schema': 1, 'version': VERSION, 'ok': True, 'platform': 'darwin', 'arch': 'arm64',
            'processes': {'writePid': facts['pid'], 'readPid': restart['pid']}, 'nativeCaptures': list(CAPTURES),
            'checks': list(TOKENS), 'liveGitHubVerified': False, 'physicalUserDeviceVerified': False,
            'artifacts': sorted(artifacts.values(), key=lambda item: item['file'])}


def run(directory, *, platform='darwin', arch='arm64'):
    directory = Path(directory).resolve()

    def read(name):
        target = directory / name
        need(not target.is_symlink() and target.resolve().parent == directory and target.is_file(), 'evidence path escaped its directory')
        return target.read_bytes()

    result = verify(read, expected_platform=platform, expected_arch=arch)
    (directory / 'mouse-644-sync-acceptance.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--platform', choices=('darwin',), required=True)
    parser.add_argument('--arch', choices=('arm64',), required=True)
    args = parser.parse_args()
    run(args.directory, platform=args.platform, arch=args.arch)
    print('MOUSE_644_SYNC_ACCEPTANCE_PASS')


if __name__ == '__main__':
    main()
