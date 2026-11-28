"""Synthetic causal rejection tests; no fixture here claims native acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import unittest
import zlib

spec = importlib.util.spec_from_file_location('sync644', Path(__file__).with_name('mouse644-sync-evidence.py'))
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def serialized(value):
    return (json.dumps(value, sort_keys=True) + '\n').encode()


def native_input(selector='#theme-button'):
    return {'pid': 101, 'selector': selector, 'source': 'CGEvent', 'point': {'x': 20, 'y': 30}, 'at': 1000,
            'events': [{'type': 'click', 'trusted': True, 'matches': True}]}


def envelope():
    captures = [{'filename': name, 'pid': 202 if name in S.CAPTURES[-2:] else 101} for name in S.CAPTURES]
    facts = {'schema': 1, 'version': S.VERSION, 'platform': 'darwin', 'arch': 'arm64', 'packaged': True,
             'physicalUserDeviceVerified': False, 'profile': '/owned/profile', 'pid': 101, 'writePid': 101,
             'phase': 'read', 'ok': True, 'writeComplete': True, 'awaitingRestart': False,
             'cleanup': {'restored': True, 'desktopStateRestored': True}, 'captures': captures,
             'nativeInputs': [native_input()],
             'write': {'pid': 101, 'startedAt': 1000, 'completedAt': 1500, 'fixtureOnly': True, 'liveGitHubVerified': False},
             'restart': {'pid': 202, 'startedAt': 2000, 'completedAt': 2500}}
    written = {**copy.deepcopy(facts), 'phase': 'write', 'ok': False, 'awaitingRestart': True, 'captures': captures[:-2]}
    written.pop('restart')
    raw = {'mouse-644-sync.json': serialized(facts), 'mouse-644-sync-write.json': serialized(written)}
    processes = {'schema': 1, 'version': S.VERSION, 'platform': 'darwin', 'arch': 'arm64',
                 'profile': facts['profile'], 'executable': '/owned/Mouse Browser', 'executableSha256': 'a' * 64,
                 'reportSha256': S.sha(raw['mouse-644-sync.json'])}
    for phase, pid, marker, report in (('write', 101, 'MOUSE_644_SYNC_WRITE_PASS', 'mouse-644-sync-write.json'),
                                     ('read', 202, 'MOUSE_644_SYNC_NATIVE_PASS', 'mouse-644-sync.json')):
        name = 'mouse-644-sync-' + phase + '.log'
        raw[name] = (marker + '\nMOUSE_644_PROCESS_RETURN pid=' + str(pid) + ' code=0 elapsedMs=700\n').encode()
        processes[phase] = {'pid': pid, 'exitCode': 0, 'elapsedMs': 700, 'log': name, 'logSha256': S.sha(raw[name]),
                            'requiredMarkers': [marker], 'report': report, 'reportSha256': S.sha(raw[report])}
    raw['mouse-644-sync-processes.json'] = serialized(processes)
    return raw


def original():
    return {'attributes': {'data-color-mode': 'dark', 'data-light-theme': 'dark', 'data-dark-theme': 'dark_dimmed'},
            'cookie': 'mouse631_0=doc; mouse644_normal=normal-only', 'storage': 'site-authored-value'}


def github(theme='light'):
    color = 'rgb(' + ', '.join(map(str, S.COLORS['github'][theme])) + ')'
    return {'url': 'https://github.com/page/0/', 'colorMode': theme, 'lightTheme': 'light', 'darkTheme': 'dark_dimmed',
            'dark': theme == 'dark', 'background': color, 'color': color, 'normalOnly': 'owned-normal-state',
            'cookie': original()['cookie'], 'storage': original()['storage']}


def png(width, height, pixel):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    rows = b''.join(b'\0' + bytes(v for x in range(width) for v in pixel(x, y)) for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


def theme_capture(theme='light', stale=False, generic=False):
    # Synthetic solid swatches validate independent OS-PNG decoding only.
    # Full native-page identity/crop checks remain in the real verifier.
    kinds = ('attribute', 'class') if generic else ('github', 'standard')
    indices = (2, 3) if generic else (0, 1)
    def pixel(x, y):
        for index, kind in enumerate(kinds):
            if index * 400 + 32 <= x < index * 400 + 152 and 180 <= y < 212:
                return (*S.COLORS[kind]['dark' if stale else theme], 255)
        return 80, 80, 80, 255
    data = png(800, 260, pixel)
    name = 'mouse-644-' + ('generic-' if generic else 'theme-') + theme + '.png'
    capture = {'filename': name, 'displayFilename': name[:-4] + '-display.png', 'sha256': S.sha(data),
               'displaySha256': S.sha(data), 'pixelSize': {'width': 800, 'height': 260},
               'screenPixelSize': {'width': 800, 'height': 260}, 'theme': theme,
               'cropPixels': {'x': 0, 'y': 0, 'width': 800, 'height': 260},
               'mapping': {'originX': 0, 'originY': 0, 'scaleX': 1, 'scaleY': 1},
               'native': [{'index': indices[i], 'tabId': 'page-' + str(indices[i]), 'bounds': {'x': i * 400, 'y': 0, 'width': 400, 'height': 260}} for i in range(2)],
               'themeProbes': [{'index': indices[i], 'tabId': 'page-' + str(indices[i]), 'bounds': {'x': 32, 'y': 180, 'width': 120, 'height': 32},
                                'color': 'rgb(' + ', '.join(map(str, S.COLORS[kind][theme])) + ')'}
                               for i, kind in enumerate(kinds)]}
    return {name: data, capture['displayFilename']: data}, capture


def filters():
    def stamp(second):
        return '2026-11-28T10:00:' + str(second).zfill(2) + '.000Z'

    def row(id_, checked=0):
        return {'id': id_, 'name': id_, 'url': S.SOURCES[id_], 'builtin': True, 'enabled': True, 'phase': 'ready',
                'origin': 'cache', 'ruleCount': 61, 'updatedAt': stamp(0), 'checkedAt': stamp(checked),
                'sha256': S.sha(S.fixture_text(id_).encode()), 'lastError': None, 'nextRetryAt': None,
                'authors': 'Fixture authors', 'license': 'https://fixture.invalid/license'}

    def state(checked=0):
        return {'enabled': True, 'privateMode': False, 'phase': 'ready', 'updateIntervalHours': 12,
                'maxSubscriptions': 8, 'revision': checked + 1, 'lists': 2, 'rules': 121,
                'subscriptions': [row(id_, checked) for id_ in S.SOURCES]}
    initial = {'enabled': False, 'phase': 'off'}
    offline = state()
    offline.update(phase='fallback')
    for item in offline['subscriptions']:
        item.update(origin='bundled', sha256=S.BUNDLED[item['id']], updatedAt='2026-11-28T01:52:00.000Z', checkedAt=None,
                    ruleCount=5000, phase='stale', lastError='MOUSE_ADBLOCK_LIST_UNAVAILABLE')
    after200, after304, failed, persisted = state(), state(1), state(1), state(3)
    for item in failed['subscriptions']:
        item.update(phase='stale', lastError='MOUSE_ADBLOCK_LIST_UNAVAILABLE', nextRetryAt='2026-11-28T10:05:02.000Z')
    custom = {'id': 'custom-owned', 'name': 'Owned custom list', 'url': S.CUSTOM_URL, 'builtin': False, 'enabled': True,
              'phase': 'ready', 'origin': 'cache', 'ruleCount': 61, 'updatedAt': stamp(4), 'checkedAt': stamp(4),
              'sha256': S.sha(S.fixture_text('custom').encode()), 'lastError': None, 'nextRetryAt': None}
    added = state(3); added['subscriptions'].append(copy.deepcopy(custom)); added.update(rules=182, lists=3)
    disabled = copy.deepcopy(added); disabled['subscriptions'][-1].update(enabled=False, phase='disabled'); disabled.update(rules=121, lists=2)
    off = copy.deepcopy(persisted); off.update(enabled=False, phase='off')
    for item in off['subscriptions']:
        item['phase'] = 'off'
    allow, block = {'ok': True, 'status': 200}, {'ok': False, 'error': 'TypeError'}
    value = {'initial': initial, 'offline': offline, 'after200': after200, 'after304': after304, 'afterFailure': failed,
             'customAdded': added, 'customDisabled': disabled, 'customRemoved': copy.deepcopy(persisted),
             'off': off, 'persisted': persisted,
             **{key: copy.deepcopy(allow) for key in ('beforeEnabled', 'customAllowed', 'allowed')},
             **{key: copy.deepcopy(block) for key in ('blocked', 'stillBlocked', 'customBlocked')}}
    requests = []
    for id_ in (*S.SOURCES, 'custom'):
        for index, status in enumerate([200] if id_ == 'custom' else [503, 200, 304, 503, 304]):
            etag = '"mouse644-' + id_ + '-v1"'
            requests.append({'path': '/lists/' + id_, 'method': 'GET', 'status': status,
                             'ifNoneMatch': None if id_ == 'custom' or index < 2 else etag,
                             'cookie': None, 'authorization': None, 'etag': etag,
                             'bodySha256': S.sha(S.fixture_text(id_).encode()) if status == 200 else None, 'at': 10000 + index * 1000})
    requests += [{'path': '/mouse-644-ad/resource'}] * 2 + [{'path': '/mouse-644-custom/resource'}]
    inputs = [native_input(selector) for selector in ('[data-setting="blockAds"]', '#settings-filter-refresh', '#settings-filter-url',
              '#settings-filter-add', '[data-filter-toggle="custom-owned"]', '[data-filter-remove="custom-owned"]')]
    return {'filters': value, 'requests': requests}, {'subscriptions': copy.deepcopy(persisted), 'blocked': block}, inputs


class SyncReaderTests(unittest.TestCase):
    def test_envelope_binds_two_actual_processes_immutable_write_and_archived_logs(self):
        raw = envelope()
        facts, *_ = S.read_envelope(raw.__getitem__, 'darwin', 'arm64')
        self.assertNotEqual(facts['pid'], facts['restart']['pid'])
        for key, value in [('pid', 202), ('version', '6.0.43'), ('physicalUserDeviceVerified', True), ('awaitingRestart', True)]:
            changed = dict(raw); report = json.loads(changed['mouse-644-sync.json']); report[key] = value
            changed['mouse-644-sync.json'] = serialized(report)
            with self.subTest(key=key), self.assertRaises(ValueError):
                S.read_envelope(changed.__getitem__)

    def test_current_receipt_cannot_hide_a_changed_original_write_or_wrong_native_log(self):
        for file in ('mouse-644-sync-write.json', 'mouse-644-sync-write.log', 'mouse-644-sync-read.log'):
            raw = envelope(); raw[file] += b' '
            with self.subTest(file=file), self.assertRaises(ValueError):
                S.read_envelope(raw.__getitem__)
        raw = envelope(); processes = json.loads(raw['mouse-644-sync-processes.json']); processes['read']['pid'] = 101
        raw['mouse-644-sync-processes.json'] = serialized(processes)
        with self.assertRaises(ValueError): S.read_envelope(raw.__getitem__)

    def test_original_site_attributes_restore_exactly_without_cookie_or_storage_mutation(self):
        for theme in ('light', 'dark'):
            S.github(github(theme), theme, original())
        off = github('dark'); off.update(lightTheme='dark', dark=False)
        S.github(off, 'light', original(), synced=False)
        for change in ({'darkTheme': 'dark'}, {'storage': None}, {'normalOnly': None}, {'cookie': ''}, {'colorMode': 'auto'}, {'background': 'rgb(0, 0, 0)'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                S.github({**github(), **change}, 'light', original())
        off['lightTheme'] = 'light'
        with self.assertRaises(ValueError): S.github(off, 'light', original(), synced=False)

    def test_adapter_fixture_cannot_be_substituted_with_an_unrelated_lookalike_origin(self):
        for url in ('http://github.com/page/0/', 'https://github.com.attacker.invalid/page/0/', 'https://example.org/page/0/'):
            with self.subTest(url=url), self.assertRaises(ValueError): S.github({**github(), 'url': url}, 'light', original())

    def test_png_reader_rejects_stale_theme_even_when_all_report_hashes_are_recomputed(self):
        raw, capture = theme_capture(); S.theme_pixels(raw.__getitem__, capture, 'light')
        raw, stale = theme_capture(stale=True)
        with self.assertRaisesRegex(ValueError, 'stale or wrong'): S.theme_pixels(raw.__getitem__, stale, 'light')

    def test_theme_pixel_probes_cannot_move_to_another_patch_or_owner(self):
        raw, capture = theme_capture()
        for mutate in (lambda v: v['themeProbes'][0].update(tabId='page-1'),
                       lambda v: v['themeProbes'][0]['bounds'].update(y=10),
                       lambda v: v['themeProbes'][0]['bounds'].update(width=1),
                       lambda v: v['mapping'].update(scaleX=2)):
            changed = copy.deepcopy(capture); mutate(changed)
            with self.assertRaises(ValueError): S.theme_pixels(raw.__getitem__, changed, 'light')

    def test_generic_native_pixels_reject_stale_images_and_wrong_page_owners(self):
        kinds = {2: 'attribute', 3: 'class'}
        raw, capture = theme_capture(generic=True)
        S.theme_pixels(raw.__getitem__, capture, 'light', kinds)
        raw, stale = theme_capture(stale=True, generic=True)
        with self.assertRaisesRegex(ValueError, 'stale or wrong'):
            S.theme_pixels(raw.__getitem__, stale, 'light', kinds)
        with self.assertRaises(ValueError):
            S.theme_pixels(raw.__getitem__, stale, 'light')

    def test_generic_contracts_validate_exact_state_and_private_isolation(self):
        origin = 'http://127.0.0.1:1234'
        for kind, index in (('attribute', 2), ('class', 3)):
            color = 'rgb(' + ', '.join(map(str, S.COLORS[kind]['light'])) + ')'
            view = {'url': origin + '/page/' + str(index) + '/', 'dark': False, 'storage': 'site-authored-value',
                    'background': color, 'color': color, 'dataTheme': 'light' if kind == 'attribute' else None,
                    'rootClass': 'app-shell' if kind == 'attribute' else 'app-shell light',
                    'genericNormalOnly': 'owned-generic-normal-state', 'cookie': 'mouse644_generic_normal=normal-only'}
            S.generic_page(view, kind, 'light', origin)
            for change in ({'dataTheme': 'dark'}, {'rootClass': 'dark'}, {'storage': None}, {'dark': True}, {'cookie': ''}, {'url': 'https://example.org/page/2/'}):
                with self.subTest(kind=kind, change=change), self.assertRaises(ValueError):
                    S.generic_page({**view, **change}, kind, 'light', origin)
            if kind == 'attribute':
                private = {**view, 'url': origin + '/page/7/', 'genericNormalOnly': None, 'cookie': '', 'visibility': 'visible'}
                S.generic_page(private, kind, 'light', origin, private=True)
                for change in ({'genericNormalOnly': 'owned-generic-normal-state'}, {'cookie': 'mouse644_generic_normal=normal-only'}, {'visibility': 'hidden'}):
                    with self.assertRaises(ValueError): S.generic_page({**private, **change}, kind, 'light', origin, private=True)

    def test_filter_fixture_checks_offline_cache_refresh_control_and_restart(self):
        write, restart, inputs = filters()
        accepted = S.verify_filters(write, restart, inputs)
        self.assertEqual(set(accepted), set(S.SOURCES))

    def test_offline_fallback_must_use_the_pinned_bundled_digest_and_origin(self):
        # Source tests hash the bundled files themselves. The publisher also
        # requires this reader to equal the accepted source checker byte-for-byte.
        for field, wrong in [('origin', 'none'), ('sha256', '0' * 64)]:
            write, restart, inputs = filters()
            write['filters']['offline']['subscriptions'][0][field] = wrong
            with self.subTest(field=field), self.assertRaises(ValueError):
                S.verify_filters(write, restart, inputs)

    def test_conditional_refresh_rejects_changed_last_good_body_or_timestamp(self):
        for stage, field, value in [('after304', 'sha256', 'a' * 64), ('after304', 'updatedAt', '2026-11-28T10:00:01.000Z'),
                                    ('afterFailure', 'checkedAt', '2026-11-28T10:00:02.000Z'), ('afterFailure', 'lastError', None)]:
            write, restart, inputs = filters(); write['filters'][stage]['subscriptions'][0][field] = value
            with self.subTest(stage=stage, field=field), self.assertRaises(ValueError): S.verify_filters(write, restart, inputs)

    def test_conditional_http_requires_exact_validator_credential_omission_and_real_response(self):
        for field, value in [('ifNoneMatch', None), ('status', 200), ('cookie', 'session=secret'),
                             ('authorization', 'Bearer secret'), ('bodySha256', 'a' * 64)]:
            write, restart, inputs = filters(); write['requests'][2][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): S.verify_filters(write, restart, inputs)

    def test_custom_disable_and_global_off_must_affect_real_requests_and_survive_restart(self):
        mutations = [lambda w, r, i: w['filters'].__setitem__('customAllowed', {'ok': False, 'error': 'TypeError'}),
                     lambda w, r, i: w['filters']['customDisabled'].update(rules=182),
                     lambda w, r, i: w['requests'].append({'path': '/mouse-644-ad/resource'}),
                     lambda w, r, i: r['subscriptions']['subscriptions'][0].update(enabled=False),
                     lambda w, r, i: i.pop()]
        for mutate in mutations:
            write, restart, inputs = filters(); mutate(write, restart, inputs)
            with self.assertRaises(ValueError): S.verify_filters(write, restart, inputs)


if __name__ == '__main__':
    unittest.main()
