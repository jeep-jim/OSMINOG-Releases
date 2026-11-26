"""Synthetic unit receipts only; these are never native acceptance evidence."""
import copy
import datetime
import importlib.util
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


A = load_module('mouse639_acceptance_test_subject', 'mouse641-adblock-evidence.py')
R = load_module('mouse639_runner_test_fixture', 'fixtures/mouse641-adblock-seed.py')


def encode_png(width, height, rows):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b''.join(b'\0' + row for row in rows))) + chunk(b'IEND', b'')


def fixture():
    """Return (raw files, report, refresh bindings) for mutation tests.

    All PIDs, click receipts and bitmaps below are explicitly synthetic unit
    data. Only the separate installed runner can create actual release proof.
    """
    files = {}
    generated = datetime.datetime(2026, 11, 25, 12, 0, tzinfo=datetime.timezone.utc)
    start = int(generated.timestamp() * 1000) + 100
    with tempfile.TemporaryDirectory() as root:
        output, profile = Path(root) / 'out', Path(root) / 'profile'
        output.mkdir()
        profile.mkdir()
        seed = R.seed_cache(output, profile, now=generated)
        for name in output.iterdir():
            files[name.name] = name.read_bytes()
    profile = seed['profile']
    records = []
    for row in seed['records']:
        record = json.loads(files[row['file']])
        records.append({'source': row['source'], 'sha256': row['sha256'], 'textSha256': record['sha256'], 'updatedAt': record['updatedAt']})
    template = b"<!doctype html><title>Owned local AdBlock fixture</title><script>for(const kind of ['allowed','advertising']){mouse639.attempted[kind]++;script.onload=load;script.onerror=error;document.head.append(script);}</script>"
    files['mouse-639-adblock-fixture.html'] = template
    facts = {'schema': 1, 'version': A.VERSION, 'platform': 'linux', 'arch': 'x64', 'packaged': True, 'pid': 101,
             'profile': profile, 'profileIsolated': True, 'physicalUserDeviceVerified': False,
             'fixture': 'synthetic-cache-and-loopback-http', 'ok': True, 'restored': True, 'writeComplete': True,
             'awaitingRestart': False, 'cleanup': {'restored': True}}
    processes = {'version': A.VERSION, 'platform': 'linux', 'arch': 'x64', 'profile': profile,
                 'executable': '/synthetic/unit-only/Mouse', 'executableSha256': 'f' * 64,
                 'cacheSeedSha256': A.digest(files['mouse-639-adblock-cache.json'])}
    images = {}
    counter = 0
    def ticket():
        nonlocal counter
        counter += 1
        return '00000000-0000-4000-8000-' + str(counter).zfill(12)
    def setting(enabled, private=False, include_private=False):
        result = {**A.BASE_SETTINGS, 'blockAds': enabled}
        if include_private:
            result['privateMode'] = private
        return result
    def state(enabled, prepared=True):
        return {'enabled': enabled, 'phase': 'ready' if enabled else 'off', 'lists': 2 if prepared else 0,
                'rules': 124 if prepared else 3, 'updatedAt': seed['generatedAt'] if prepared else None}
    def image_pair(blocked, ui):
        key = (blocked, ui)
        if key in images:
            return images[key]
        width, height = 700, 520
        pixels = bytearray(bytes([243, 240, 232]) * width * height)
        def paint(x, y, w, h, color):
            for row in range(y, y + h):
                at = (row * width + x) * 3
                pixels[at:at + w * 3] = bytes(color) * w
        if ui:
            paint(560, 220, 20, 20, [30, 30, 30])
            paint(570, 220, 10, 20, [235, 235, 235])
        else:
            paint(20 + 20 + 24, 20 + 40 + 80, 200, 42, A.COLORS['allowed'])
            paint(20 + 20 + 24, 20 + 40 + 144, 200, 42, A.COLORS['blocked' if blocked else 'advertising'])
        full = encode_png(width, height, [bytes(pixels[y * width * 3:(y + 1) * width * 3]) for y in range(height)])
        crop = encode_png(640, 480, [bytes(pixels[((y + 20) * width + 20) * 3:((y + 20) * width + 660) * 3]) for y in range(480)])
        images[key] = crop, full
        return images[key]
    def capture(part, phase, name, blocked=False, ui=None):
        filename = 'mouse-639-adblock-' + phase + '-' + name + '.png'
        crop, full = image_pair(blocked, ui is not None)
        files[filename], files[filename[:-4] + '-display.png'] = crop, full
        value = {'filename': filename, 'displayFilename': filename[:-4] + '-display.png', 'pid': part['pid'],
                 'source': 'globalCapture.acquire(display)', 'kind': 'screen', 'backend': 'synthetic-unit-fixture',
                 'sha256': A.digest(crop), 'displaySha256': A.digest(full), 'screenPixelSize': {'width': 700, 'height': 520},
                 'pixelSize': {'width': 640, 'height': 480}, 'display': {'bounds': {'x': 0, 'y': 0, 'width': 700, 'height': 520}},
                 'contentBounds': {'x': 20, 'y': 20, 'width': 640, 'height': 480}, 'cropPixels': {'x': 20, 'y': 20, 'width': 640, 'height': 480},
                 'mapping': {'scaleX': 1, 'scaleY': 1, 'originX': 0, 'originY': 0}, 'ui': ui, 'probes': []}
        part['captures'].append(value)
        return value
    def native_click(part, selector):
        ident = ticket()
        value = {'ticket': ident, 'selector': selector, 'action': 'click', 'pid': part['pid'], 'source': 'XTest',
                 'point': {'x': 30, 'y': 50}, 'at': part['startedAt'] + 300,
                 'events': [{'ticket': ident, 'selector': selector, 'type': 'click', 'trusted': True, 'matches': True, 'at': part['startedAt'] + 301}]}
        part['inputs'].append(value)
        return ident
    def ui_shot(part, phase, name, enabled, private=False, theme='light'):
        value = {'open': True, 'checked': enabled, 'disabled': private, 'theme': theme, 'privateMode': private,
                 'stored': enabled, 'status': 'Local filter lists are ready' if enabled else 'Ad blocking is off', 'label': 'Block ads',
                 'bounds': {'x': 540, 'y': 200, 'width': 20, 'height': 20}}
        shot = capture(part, phase, name, ui=copy.deepcopy(value))
        part['ui'].append({'name': name, **value, 'capture': shot['filename']})
        return value
    for phase, key, pid in [('write', 'write', 101), ('read', 'restart', 202)]:
        at = start if phase == 'write' else start + 5000
        enabled = phase == 'read'
        part = {'pid': pid, 'startedAt': at, 'completedAt': at + 2000, 'elapsedMs': 2000,
                'budgetMs': 180000 if phase == 'write' else 60000, 'origin': 'http://127.0.0.1:' + ('12345' if phase == 'write' else '12346'),
                'fixtureSha256': A.digest(template), 'inputs': [], 'captures': [], 'cases': [], 'changes': [], 'ui': []}
        facts[key] = part
        cache = {'seedSha256': A.digest(files['mouse-639-adblock-cache.json']), 'records': records, 'state': state(enabled, enabled)}
        part['initial'] = {'settings': setting(enabled, include_private=True), 'state': state(enabled, enabled), 'cache': copy.deepcopy(cache)}
        part['cache'] = copy.deepcopy(cache)
        part['cache']['state'] = state(not enabled)
        part['finalSettings'] = setting(not enabled)
        hits = []
        def hit(kind, token):
            body = template if kind == 'page' else A.SCRIPT[kind].encode('utf-8')
            hits.append({'sequence': len(hits) + 1, 'at': at + 500, 'method': 'GET', 'path': A.PREFIX + ('page' if kind == 'page' else kind + '-script.js'),
                         'token': token, 'kind': kind, 'status': 200, 'bodySha256': A.digest(body), 'bytes': len(body),
                         'contentType': 'text/html; charset=utf-8' if kind == 'page' else 'application/javascript; charset=utf-8'})
        names = A.WRITE_CASES if phase == 'write' else ('restart-enabled',)
        for index, name in enumerate(names):
            blocked, private = name not in ('default-off', 'disabled-again'), name == 'enabled-private'
            token = ticket()
            tab = 'tab-first' if name in ('default-off', 'enabled-first', 'disabled-again') else 'tab-' + name
            wc = 11 if tab == 'tab-first' else 20 + index
            desk = 'desk-private' if private else 'desk-other' if name == 'enabled-other-desktop' else 'desk-home'
            bounds = {'x': 20, 'y': 40, 'width': 600, 'height': 350}
            value = {'name': name, 'token': token, 'pid': pid, 'url': part['origin'] + A.PREFIX + 'page?token=' + token,
                     'blocked': blocked, 'privateMode': private, 'sessionPersistent': not private,
                     'native': {'tabId': tab, 'desk': desk, 'webContentsId': wc, 'bounds': bounds, 'viewBounds': bounds,
                                'parentBounds': None, 'actualBounds': bounds, 'visible': True, 'parentVisible': True, 'cachedVisible': True, 'attached': True, 'zoom': 1},
                     'counts': {'page': 1, 'allowed': 1, 'advertising': 0 if blocked else 1}, 'state': state(blocked, name != 'default-off'),
                     'settings': setting(blocked, private, True)}
            value['dom'] = {'url': value['url'], 'title': 'Mouse639 owned AdBlock fixture', 'timeOrigin': at + 50 + index, 'token': token,
                            'attempted': {'allowed': 1, 'advertising': 1}, 'executed': {'allowed': 1, 'advertising': 0 if blocked else 1},
                            'settled': {'allowed': 'load', 'advertising': 'error' if blocked else 'load'}, 'regions': []}
            shot = capture(part, phase, name, blocked)
            for kind, top in [('allowed', 80), ('advertising', 144)]:
                region = {'x': 24, 'y': top, 'width': 200, 'height': 42}
                color = A.COLORS['blocked' if blocked and kind == 'advertising' else kind]
                value['dom']['regions'].append({'kind': kind, 'bounds': region, 'color': 'rgb(' + ', '.join(map(str, color)) + ')'})
                for offset in (-5, 0, 5):
                    point = {'x': 20 + 24 + 100 + offset, 'y': 40 + top + 21}
                    shot['probes'].append({'kind': kind, 'localBounds': region, 'offset': offset, 'point': point, 'expectedRGB': color,
                                           'x': point['x'], 'y': point['y'], 'actualRGBA': color + [255]})
            value['capture'] = shot['filename']
            part['cases'].append(value)
            hit('page', token)
            hit('allowed', token)
            if not blocked:
                hit('advertising', token)
        changes = [('enable-dark', True), ('disable-again', False), ('persist-enabled', True)] if phase == 'write' else [('restore-initial-off', False)]
        for name, on in changes:
            after = ui_shot(part, phase, name, on, theme='dark' if name == 'enable-dark' else 'light')
            before = {**after, 'checked': not on, 'stored': not on}
            part['changes'].append({'name': name, 'enabled': on, 'before': before, 'after': after,
                                    'input': native_click(part, '[data-setting="blockAds"]'), 'saved': setting(on), 'state': state(on)})
        if phase == 'write':
            ui_shot(part, phase, 'initial-off', False)
            ui_shot(part, phase, 'enabled-light', True)
            private_ui = ui_shot(part, phase, 'private-enabled', True, private=True)
            part['private'] = {'partition': 'mouse-private-unit-only', 'persistent': False, 'distinctSession': True,
                               'enterInput': native_click(part, '#private-button'), 'leaveInput': native_click(part, '#private-button'),
                               'ui': private_ui, 'writeError': 'Постоянные настройки меняются в обычном режиме'}
            part['deskSwitch'] = {'from': 'desk-home', 'to': 'desk-other',
                                  'input': native_click(part, '.desktop-card[data-desk="desk-other"] .desk-open'),
                                  'returnInput': native_click(part, '.desktop-card[data-desk="desk-home"] .desk-open')}
            identity = {'token': part['cases'][1]['token'], 'timeOrigin': part['cases'][1]['dom']['timeOrigin']}
            part['retained'] = {'before': identity, 'after': dict(identity), 'webContentsId': 11}
            token = ticket()
            hit('advertising', token)
            part['mainFrame'] = {'token': token, 'enabled': True, 'hits': 1, 'url': part['origin'] + A.PREFIX + 'advertising-script.js?token=' + token,
                                 'body': A.SCRIPT['advertising'], 'webContentsId': 49}
        else:
            ui_shot(part, phase, 'restored-enabled', True)
        filename = 'mouse-639-adblock-http-' + phase + '.json'
        files[filename] = (json.dumps({'schema': 1, 'synthetic': True, 'version': A.VERSION, 'pid': pid, 'origin': part['origin'], 'hits': hits}) + '\n').encode()
        part['http'] = {'file': filename, 'sha256': A.digest(files[filename])}
        marker = 'MOUSE_639_ADBLOCK_WRITE_PASS' if phase == 'write' else 'MOUSE_639_ADBLOCK_NATIVE_PASS'
        log = 'mouse-639-adblock-' + phase + '.log'
        files[log] = (marker + '\nMOUSE_639_PROCESS_RETURN pid=' + str(pid) + ' code=0 elapsedMs=2000\n').encode()
        processes[phase] = {'pid': pid, 'exitCode': 0, 'elapsedMs': 2000, 'log': log, 'logSha256': A.digest(files[log]), 'requiredMarkers': [marker],
                            'report': 'mouse-639-adblock-write.json' if phase == 'write' else 'mouse-639-adblock.json'}
    def refresh():
        written = copy.deepcopy(facts)
        written.pop('restart', None)
        written.update(ok=False, restored=False, awaitingRestart=True)
        files['mouse-639-adblock-write.json'] = (json.dumps(written) + '\n').encode()
        files['mouse-639-adblock.json'] = (json.dumps(facts) + '\n').encode()
        for phase in ('write', 'read'):
            processes[phase]['reportSha256'] = A.digest(files[processes[phase]['report']])
            processes[phase]['logSha256'] = A.digest(files[processes[phase]['log']])
        processes['reportSha256'] = A.digest(files['mouse-639-adblock.json'])
        files['mouse-639-adblock-processes.json'] = (json.dumps(processes) + '\n').encode()
    refresh.processes = processes
    refresh()
    return files, facts, refresh


class AdBlockReader(unittest.TestCase):
    def test_complete_synthetic_shape_passes_and_binds_all_raw_artifacts(self):
        files, facts, refresh = fixture()
        result = A.verify(files.__getitem__, expected_platform='linux', expected_arch='x64')
        self.assertTrue(result['syntheticFilters'])
        self.assertEqual([case['name'] for case in result['cases']], list(A.WRITE_CASES) + ['restart-enabled'])
        self.assertEqual(result['processes'], {'writePid': 101, 'readPid': 202})
        self.assertEqual({value['file'] for value in result['artifacts']}, set(files))

    def test_native_network_and_privacy_mutations_are_rejected_even_with_fresh_report_hashes(self):
        changes = [lambda f: f['write']['cases'][1]['counts'].__setitem__('advertising', 1),
                   lambda f: f['write']['cases'][1]['dom']['attempted'].__setitem__('advertising', 0),
                   lambda f: f['write']['cases'][1]['dom']['executed'].__setitem__('allowed', 0),
                   lambda f: f['write']['cases'][2]['native'].__setitem__('webContentsId', 11),
                   lambda f: f['write']['cases'][3]['native'].__setitem__('desk', 'desk-home'),
                   lambda f: f['write']['private'].__setitem__('persistent', True),
                   lambda f: f['write']['private'].__setitem__('writeError', ''),
                   lambda f: f['restart']['initial']['settings'].__setitem__('blockAds', False),
                   lambda f: f['restart']['initial']['state'].__setitem__('lists', 0),
                   lambda f: f['write']['inputs'][0]['events'][0].__setitem__('trusted', False)]
        for change in changes:
            with self.subTest(change=change):
                files, facts, refresh = fixture()
                change(facts)
                refresh()
                with self.assertRaises(ValueError):
                    A.verify(files.__getitem__)

    def test_raw_server_advertising_hit_cannot_be_hidden_by_claiming_zero(self):
        files, facts, refresh = fixture()
        name = 'mouse-639-adblock-http-write.json'
        server = json.loads(files[name])
        hit = copy.deepcopy(next(value for value in server['hits'] if value['kind'] == 'advertising'))
        hit.update(sequence=len(server['hits']) + 1, token=facts['write']['cases'][1]['token'])
        server['hits'].append(hit)
        files[name] = json.dumps(server).encode()
        facts['write']['http']['sha256'] = A.digest(files[name])
        refresh()
        with self.assertRaisesRegex(ValueError, 'server actually received'):
            A.verify(files.__getitem__)

    def test_native_png_bytes_are_redecoded_after_a_valid_hash_rebind(self):
        files, facts, refresh = fixture()
        shot = facts['write']['captures'][1]
        blank_crop = encode_png(640, 480, [bytes([243, 240, 232]) * 640] * 480)
        blank_full = encode_png(700, 520, [bytes([243, 240, 232]) * 700] * 520)
        files[shot['filename']], files[shot['displayFilename']] = blank_crop, blank_full
        shot['sha256'], shot['displaySha256'] = A.digest(blank_crop), A.digest(blank_full)
        refresh()
        with self.assertRaisesRegex(ValueError, 'pixel receipt|OS pixels'):
            A.verify(files.__getitem__)

    def test_real_restart_cache_freshness_and_platform_are_required(self):
        for change in [lambda f: f['restart'].__setitem__('pid', f['pid']),
                       lambda f: f['restart'].__setitem__('startedAt', f['restart']['startedAt'] + 3600000),
                       lambda f: f['restart']['initial']['cache']['records'][0].__setitem__('sha256', '0' * 64)]:
            files, facts, refresh = fixture()
            change(facts)
            refresh()
            with self.assertRaises(ValueError):
                A.verify(files.__getitem__)
        files, _, _ = fixture()
        with self.assertRaisesRegex(ValueError, 'wrong native platform'):
            A.verify(files.__getitem__, expected_platform='darwin')


if __name__ == '__main__':
    unittest.main()
