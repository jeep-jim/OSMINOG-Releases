#!/usr/bin/env python3
"""Synthetic contract mutations only; these fixtures are NEVER native acceptance.

All JSON, executable bytes and PNGs below are made in memory for unit tests.
No browser is launched and no installed package, user device or release is
verified here. Each ordinary mutation reserializes the report and rebinds the
owner's report hash, so a stale outer hash cannot hide an untested inner gate.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import runpy
import struct
import unittest
import zlib


C = runpy.run_path(str(Path(__file__).with_name('mouse637-agent-removal-evidence.py')))
REPORT = 'mouse-637-agent-removal.json'
OWNER = 'mouse-636-owner-feedback.json'
PLATFORMS = [('darwin', 'arm64', 'CGEvent', 2), ('win32', 'x64', 'User32', 1.25),
             ('linux', 'x64', 'XTest', 1)]
CODE = [('mouse-main.cjs', 'mouse-637-agent-code-main.cjs'),
        ('mouse-preload.cjs', 'mouse-637-agent-code-preload.cjs'),
        ('page-pointer-preload.cjs', 'mouse-637-agent-code-page-pointer-preload.cjs')]
# This schema is copied from the reviewed producer contract, independently of
# the validator's constants. In particular, the source-only page preload is
# not a fourth installed ASAR executable.
RETIRED_PATHS = ['mouse-agent', 'mouse/agent-ui.js', 'mouse/agent-chat.css',
                 'mouse/agent-onboarding.js', 'mouse/agent-onboarding.css',
                 'mouse/agent-brand.js', 'mouse/agent-brand.css',
                 'mouse/local-workspace.js', 'mouse/local-workspace.css',
                 'mouse/agent-vendor', 'mouse/vendor/xterm', 'mouse/vendor/xterm.js',
                 'mouse/vendor/xterm.css'] + [
                 'mouse/agent-mouse-' + color + '.svg'
                 for color in ('orange', 'cyan', 'green', 'violet', 'coral')]
SELECTORS = ['#agent-panel', '#agent-settings-page', '#agent-local-workspace',
             '.home-agent-open', '[data-action="assistant"]', '[data-agent-settings]',
             '[data-mode="agents"]', '[data-ai-url="mouse://agent"]',
             '#ai-select option[value="mouse://agent"]', '.localhost-start']
AI_SITES = ['https://chatgpt.com/', 'https://claude.ai/',
            'https://gemini.google.com/', 'https://chat.deepseek.com/']
SETTINGS = ['appearance', 'workspace', 'imports', 'privacy', 'capture',
            'downloads', 'documents', 'updates', 'about']
CAPTURES = ['mouse-637-agent-removed-light.png', 'mouse-637-agent-removed-dark.png']
ORIGIN = 'http://127.0.0.1:34127'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    # The producer and UI contract retain selector insertion order.
    return (json.dumps(value, ensure_ascii=False) + '\n').encode('utf-8')


def png(width, height, pixels, channels=3):
    """A real, small PNG container holding explicitly synthetic test pixels."""
    assert len(pixels) == width * height * channels

    def chunk(kind, raw):
        return (struct.pack('>I', len(raw)) + kind + raw +
                struct.pack('>I', zlib.crc32(kind + raw) & 0xffffffff))

    stride = width * channels
    rows = b''.join(b'\0' + pixels[y * stride:(y + 1) * stride] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8,
                                       2 if channels == 3 else 6, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


def synthetic_capture(name, scale, shade):
    width, height = 40, 30
    pixels = bytes(channel for y in range(height) for x in range(width)
                   for channel in ((x * 17 + y * 13 + shade) % 256,
                                   (x * 11 + y * 19 + shade) % 256,
                                   (x * 7 + y * 23 + shade) % 256))
    # A fractional content origin exercises both floor/ceil and DPI mapping.
    crop = {'x': 4, 'y': 6, 'width': 25, 'height': 17}
    cropped = b''.join(pixels[((y + crop['y']) * width + crop['x']) * 3:
                             ((y + crop['y']) * width + crop['x'] + crop['width']) * 3]
                       for y in range(crop['height']))
    raw, full = png(crop['width'], crop['height'], cropped), png(width, height, pixels)
    display_name = name[:-4] + '-display.png'
    record = {'filename': name, 'displayFilename': display_name,
              'source': 'globalCapture.acquire(display)', 'backend': 'synthetic-unit-frame-only',
              'bytes': len(raw), 'sha256': sha(raw), 'displaySha256': sha(full),
              'pixelSize': {'width': crop['width'], 'height': crop['height']},
              'screenPixelSize': {'width': width, 'height': height},
              'display': {'bounds': {'x': 100, 'y': 200, 'width': width / scale, 'height': height / scale}},
              'contentBounds': {'x': 100 + 4.25 / scale, 'y': 200 + 6.5 / scale,
                                'width': 24 / scale, 'height': 16 / scale},
              'cropPixels': crop,
              'mapping': {'scaleX': scale, 'scaleY': scale, 'originX': .25, 'originY': .5}}
    return record, {name: raw, display_name: full}


def page(index):
    identity = 'synthetic-document-' + str(index)
    return {'id': 'synthetic-tab-' + str(index), 'index': index, 'desk': 'synthetic-desk',
            'webContentsId': index + 300, 'url': ORIGIN + '/page/' + str(index) + '/',
            'navigationEpoch': 1, 'identity': identity, 'timeOrigin': 10000 + index,
            'field': 'preserved-' + str(index) + '-данные', 'scrollX': 0, 'scrollY': 130,
            'cookie': 'mouse631_' + str(index) + '=' + identity, 'ticks': 10}


def native(owner, offset):
    bounds = {'x': offset, 'y': 0, 'width': 6, 'height': 8}
    return {'tabId': owner['id'], 'webContentsId': owner['webContentsId'],
            'index': owner['index'], 'desk': owner['desk'], 'visible': True,
            'parentVisible': True, 'cachedVisible': True, 'attached': True,
            'bounds': bounds, 'actualBounds': dict(bounds), 'viewBounds': dict(bounds),
            'parentBounds': None}


def fixture(platform='linux', arch='x64', source='XTest', scale=1):
    raw, captures = {}, []
    before = [page(201), page(202)]
    code = []
    for index, (name, evidence) in enumerate(CODE):
        body = ('// SYNTHETIC UNIT FIXTURE ONLY; not an installed executable.\n'
                '"use strict";\nmodule.exports = {fixtureIndex: %d};\n' % index).encode()
        raw[evidence] = body
        code.append({'path': name, 'evidenceFile': evidence, 'bytes': len(body),
                     'sha256': sha(body), 'forbidden': []})
    facts = {'schema': 1, 'contract': 'mouse637-agent-removal-v1', 'version': '6.0.37',
             'platform': platform, 'arch': arch, 'pid': 8071, 'packaged': True,
             'source': 'Installed package paths and executable bytes, actual shell/preload readbacks and retained owned native pages',
             'syntheticFixtureOnly': True, 'physicalUserDeviceVerified': False,
             'ok': True, 'restored': True, 'elapsedMs': 4200,
             'runtime': {'contextHasAgentHost': False, 'contextAgentHostType': 'undefined'},
             'package': {'appPath': '/synthetic-unit-fixture/resources/app.asar',
                         'resourcesPath': '/synthetic-unit-fixture/resources',
                         'paths': [{'root': 'app', 'path': name, 'exists': False}
                                   for name in RETIRED_PATHS] +
                                  [{'root': 'resources', 'path': 'mouse-agent-node_modules', 'exists': False}],
                         'code': code},
             'fixtureOrigin': ORIGIN, 'pages': {'before': before,
                                               'after': [{**copy.deepcopy(p), 'ticks': 20} for p in before]},
             'pageAPIs': [{'tabId': p['id'], 'mouseAgentType': 'undefined',
                           'progressType': 'function'} for p in before],
             'themes': [], 'captures': list(CAPTURES)}
    for theme, name, shade in zip(('light', 'dark'), CAPTURES, (0, 53)):
        capture, images = synthetic_capture(name, scale, shade)
        captures.append(capture); raw.update(images)
        facts['themes'].append({'theme': theme, 'selectors': dict.fromkeys(SELECTORS, 0),
                                'preloadKeys': [], 'globals': [], 'modelKeys': [],
                                'modes': ['trader', 'support', 'design', 'content'],
                                'presetKeys': ['support'], 'aiOptions': list(AI_SITES) + ['custom'],
                                'settingsSections': list(SETTINGS),
                                'native': [native(p, i * 6) for i, p in enumerate(before)],
                                'capture': name})
    # The actual producer's shell click ledger has no per-row pid. Its owning
    # process is the report/owner envelope; do not invent a stronger receipt.
    clicks = [{'selector': selector, 'source': source, 'point': {'x': 4, 'y': 5},
               'at': 100 + index, 'navigates': False,
               'events': [{'type': 'click', 'trusted': True, 'matches': True}]}
              for index, selector in enumerate(['#settings-button',
                  '#settings-dialog [data-close-dialog]'] * 2)]
    owner = {'version': '6.0.37', 'platform': platform, 'arch': arch, 'pid': 8071,
             'packaged': True, 'profileIsolated': True, 'budgetMs': 240000,
             'syntheticFixtureOnly': True, 'nativeInputs': clicks, 'captures': captures}
    return {'facts': facts, 'owner': owner, 'raw': raw}


def packed(value):
    """Rebind report bytes after every inner mutation, exactly as requested."""
    raw = dict(value['raw'])
    raw[REPORT] = encode(value['facts'])
    owner = copy.deepcopy(value['owner'])
    owner['agentRemoval'] = {**json.loads(raw[REPORT]), 'reportFile': REPORT,
                             'reportSha256': sha(raw[REPORT])}
    raw[OWNER] = encode(owner)
    return raw, owner


def read_from(raw):
    def read(name):
        if name not in raw:
            raise FileNotFoundError(name)
        return raw[name]
    return read


def set_at(value, path, replacement):
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement


class AgentRemovalEvidenceContract(unittest.TestCase):
    def check(self, value, *, serialized_owner=False):
        raw, owner = packed(value)
        return C['verify'](read_from(raw), **({} if serialized_owner else {'owner': owner}))

    def reject_fields(self, cases, message):
        for path, replacement in cases:
            with self.subTest(path=path, replacement=replacement):
                value = fixture(); set_at(value, path, replacement)
                with self.assertRaisesRegex(ValueError, message):
                    self.check(value)

    def test_three_actual_executables_and_all_platform_contracts(self):
        self.assertEqual(C['CODE_PATHS'], [p for p, _ in CODE])
        self.assertEqual(C['CODE_EVIDENCE'], [p for _, p in CODE])
        for platform, arch, source, scale in PLATFORMS:
            with self.subTest(platform=platform):
                data = fixture(platform, arch, source, scale)
                self.assertTrue(data['facts']['syntheticFixtureOnly'])
                result = self.check(data)
                self.assertTrue(result['ok'])
                self.assertEqual((result['platform'], result['arch'], result['pid']), (platform, arch, 8071))
                self.assertIs(result['physicalUserDeviceVerified'], False)
                self.assertEqual(result['nativeCaptures'], CAPTURES)
                raw, _ = packed(data)
                expected = [REPORT] + [p for _, p in CODE] + [
                    p for name in CAPTURES for p in (name, name[:-4] + '-display.png')]
                self.assertEqual(result['inputs'], {name: sha(raw[name]) for name in expected})
                self.assertEqual(self.check(data, serialized_owner=True), result)

    def test_owner_must_bind_the_exact_report_bytes_and_fields(self):
        for mutation in (lambda raw, owner: owner['agentRemoval'].update(reportSha256='f' * 64),
                         lambda raw, owner: owner['agentRemoval'].update(reportFile='foreign.json'),
                         lambda raw, owner: owner['agentRemoval'].update(restored=False),
                         lambda raw, owner: raw.update({REPORT: raw[REPORT] + b' '})):
            raw, owner = packed(fixture()); mutation(raw, owner)
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'owner/report bytes differ'):
                C['verify'](read_from(raw), owner=owner)
        raw, owner = packed(fixture()); del raw[REPORT]
        with self.assertRaisesRegex(FileNotFoundError, REPORT): C['verify'](read_from(raw), owner=owner)
        raw, _ = packed(fixture()); del raw[OWNER]
        with self.assertRaisesRegex(FileNotFoundError, OWNER): C['verify'](read_from(raw))

    def test_report_process_architecture_version_and_positive_pid_are_bound(self):
        self.reject_fields([
            (['owner', key], bad) for key, bad in
            [('pid', 8072), ('version', '6.0.36'), ('platform', 'win32'), ('arch', 'arm64')]
        ] + [(['facts', key], bad) for key, bad in
             [('pid', 8072), ('schema', 2), ('contract', 'retired-contract'), ('source', 'mock'),
              ('version', '6.0.36'), ('platform', 'unsupported'), ('arch', 'arm64')]],
            'installed process/contract differs')
        for pid in (0, -1, True, 1.5, None):
            value = fixture(); value['facts']['pid'] = value['owner']['pid'] = pid
            with self.subTest(pid=pid), self.assertRaisesRegex(ValueError, 'installed process/contract differs'):
                self.check(value)

    def test_success_scope_isolation_cleanup_and_budget_cannot_be_claimed(self):
        self.reject_fields([(['facts', key], False) for key in ('ok', 'restored', 'packaged')],
                           'did not finish and restore')
        self.reject_fields([(['owner', 'packaged'], False), (['owner', 'profileIsolated'], False),
                            (['owner', 'budgetMs'], 240001), (['facts', 'elapsedMs'], 0),
                            (['facts', 'elapsedMs'], -1), (['facts', 'elapsedMs'], 240001),
                            (['facts', 'elapsedMs'], True), (['facts', 'elapsedMs'], math.inf),
                            (['facts', 'physicalUserDeviceVerified'], True),
                            (['facts', 'error'], {'message': 'original failure'}),
                            (['facts', 'cleanupError'], 'restore failed')], 'scope/budget')
        self.reject_fields([(['facts', 'runtime'], {}),
                            (['facts', 'runtime', 'contextHasAgentHost'], True),
                            (['facts', 'runtime', 'contextAgentHostType'], 'object')], 'creates an Agent host')

    def test_every_packaged_path_is_absent_and_the_ledger_is_exact(self):
        for index in range(len(RETIRED_PATHS) + 1):
            value = fixture(); value['facts']['package']['paths'][index]['exists'] = True
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, 'application/resources'):
                self.check(value)
        self.reject_fields([(['facts', 'package', 'appPath'], '/synthetic-unit-fixture/unpacked'),
                            (['facts', 'package', 'resourcesPath'], '')], 'ASAR/resources paths missing')
        for mutation in (lambda p: p.pop(), lambda p: p.reverse(),
                         lambda p: p.append(copy.deepcopy(p[0])),
                         lambda p: p[0].update(root='resources'),
                         lambda p: p[0].update(path='foreign'),
                         lambda p: p[0].update(exists=0)):
            value = fixture(); mutation(value['facts']['package']['paths'])
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'application/resources'):
                self.check(value)

    def test_executable_ledger_requires_the_three_real_installed_paths(self):
        for mutation in (lambda c: c.pop(), lambda c: c.reverse(),
                         lambda c: c.append(copy.deepcopy(c[0])),
                         lambda c: c[2].update(path='mouse-page-preload.cjs'),
                         lambda c: c[2].update(evidenceFile='mouse-637-agent-code-page-preload.cjs')):
            value = fixture(); mutation(value['facts']['package']['code'])
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, 'executable evidence ledger differs'):
                self.check(value)

    def test_actual_executable_bytes_size_hash_and_missing_files_are_checked(self):
        for index, (_, filename) in enumerate(CODE):
            for key, bad in [('bytes', 1), ('sha256', 'f' * 64), ('forbidden', ['mouse:agent'])]:
                value = fixture(); value['facts']['package']['code'][index][key] = bad
                with self.subTest(index=index, key=key), self.assertRaisesRegex(ValueError, 'executable bytes/hash differ'):
                    self.check(value)
            value = fixture(); value['raw'][filename] += b'// changed bytes\n'
            with self.assertRaisesRegex(ValueError, 'executable bytes/hash differ'): self.check(value)
            value = fixture(); del value['raw'][filename]
            with self.assertRaisesRegex(FileNotFoundError, filename): self.check(value)
        for raw in (b'', b'x' * (2 * 1024**2 + 1)):
            value = fixture(); name = CODE[0][1]; value['raw'][name] = raw
            value['facts']['package']['code'][0].update(bytes=len(raw), sha256=sha(raw))
            with self.assertRaisesRegex(ValueError, 'executable bytes/hash differ'): self.check(value)

    def test_rehashed_raw_code_cannot_hide_retired_dependencies_behind_an_empty_claim(self):
        for index, (_, filename) in enumerate(CODE):
            for token in ('mouse-agent/', 'mouse:agent', 'MouseAgent', 'node-pty',
                          '@modelcontextprotocol/sdk', '@xterm/'):
                value = fixture(); value['raw'][filename] += ('\n// ' + token).encode()
                value['facts']['package']['code'][index].update(
                    bytes=len(value['raw'][filename]), sha256=sha(value['raw'][filename]), forbidden=[])
                with self.subTest(file=filename, token=token), self.assertRaisesRegex(ValueError, 'still contains an Agent'):
                    self.check(value)

    def test_both_themes_must_reject_every_retired_control_and_runtime_surface(self):
        for theme in range(2):
            for selector in SELECTORS:
                value = fixture(); value['facts']['themes'][theme]['selectors'][selector] = 1
                with self.subTest(theme=theme, selector=selector), self.assertRaisesRegex(ValueError, 'UI control remains'):
                    self.check(value)
            for field, name in [('preloadKeys', 'agent'), ('globals', 'MouseAgent'), ('modelKeys', 'agentOpen')]:
                value = fixture(); value['facts']['themes'][theme][field] = [name]
                with self.subTest(theme=theme, field=field), self.assertRaisesRegex(ValueError, 'API, renderer or active model'):
                    self.check(value)
        for mutation in (lambda s: s.pop(SELECTORS[0]), lambda s: s.update({'#foreign': 0}),
                         lambda s: s.update({SELECTORS[0]: False})):
            value = fixture(); mutation(value['facts']['themes'][0]['selectors'])
            with self.assertRaisesRegex(ValueError, 'UI control remains'): self.check(value)

    def test_mode_cache_and_settings_removal_preserve_the_browser_controls(self):
        cases = [(['facts', 'themes', i, key], replacement) for i in range(2)
                 for key, replacement in [('modes', ['trader', 'support', 'design', 'content', 'agents']),
                                          ('modes', ['trader', 'support', 'design']),
                                          ('presetKeys', ['agents']), ('presetKeys', ['support', 'support']),
                                          ('presetKeys', ['unknown'])]]
        self.reject_fields(cases, 'mode/preset remains')
        self.reject_fields([(['facts', 'themes', i, 'settingsSections'], replacement) for i in range(2)
                            for replacement in [SETTINGS + ['agent'], SETTINGS[:-1], list(reversed(SETTINGS))]],
                           'settings sections differ')

    def test_ordinary_ai_websites_and_page_progress_bridge_are_required(self):
        self.reject_fields([(['facts', 'themes', i, 'aiOptions'], replacement) for i in range(2)
                            for replacement in [AI_SITES[1:] + ['custom'], list(reversed(AI_SITES)) + ['custom'],
                                                AI_SITES + ['mouse://agent', 'custom'], AI_SITES + ['file:///tmp/private', 'custom'],
                                                AI_SITES + ['javascript:alert(1)', 'custom']]], 'AI website chooser')
        value = fixture()
        for scene in value['facts']['themes']: scene['aiOptions'].insert(-1, 'https://synthetic-custom.example/chat')
        self.assertTrue(self.check(value)['ok'], 'Ordinary user-added web AI remains supported')
        self.reject_fields([(['facts', 'pageAPIs', i, key], bad) for i in range(2)
                            for key, bad in [('mouseAgentType', 'object'), ('progressType', 'undefined'),
                                             ('tabId', 'foreign-tab')]], 'page bridge')
        value = fixture(); value['facts']['pageAPIs'].pop()
        with self.assertRaisesRegex(ValueError, 'page bridge'): self.check(value)

    def test_custom_chooser_action_is_retained_in_raw_report_exactly_once(self):
        value = fixture(); result = self.check(value); raw, owner = packed(value)
        for scene in json.loads(raw[REPORT])['themes']:
            self.assertEqual(scene['aiOptions'], AI_SITES + ['custom'])
        self.assertEqual(owner['agentRemoval']['themes'], value['facts']['themes'])
        self.assertEqual(result['reportSha256'], sha(raw[REPORT]))
        self.reject_fields([(['facts', 'themes', i, 'aiOptions'], choices) for i in range(2)
                            for choices in [AI_SITES, AI_SITES + ['custom', 'custom']]], 'AI website chooser')

    def test_page_urls_use_the_actual_fixture_cookie_scope(self):
        self.assertTrue(self.check(fixture())['ok'])
        for index in range(2):
            value = fixture()
            for when in ('before', 'after'):
                page = value['facts']['pages'][when][index]
                page['url'] = ORIGIN + '/' + str(page['index'])
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, 'another origin'):
                self.check(value)

    def test_retained_page_identity_state_scroll_cookie_and_clock_cannot_change(self):
        identity_changes = {'id': 'replacement', 'index': 999, 'desk': 'other-desk',
                            'webContentsId': 9000, 'url': 'http://127.0.0.1:9/201',
                            'navigationEpoch': 2, 'identity': 'new-document', 'timeOrigin': 50000,
                            'field': 'lost', 'scrollX': 4, 'scrollY': 0, 'cookie': ''}
        self.reject_fields([(['facts', 'pages', 'after', i, key], bad) for i in range(2)
                            for key, bad in identity_changes.items()], 'identity, state or scroll changed')
        self.reject_fields([(['facts', 'pages', 'after', i, 'ticks'], 9) for i in range(2)], 'clock restarted')
        for key, bad, message in [('field', 'lost', 'owned fixture state missing'),
                                  ('cookie', '', 'owned fixture state missing'),
                                  ('webContentsId', 0, 'native page identity absent'),
                                  ('timeOrigin', 0, 'native page identity absent')]:
            value = fixture()
            for when in ('before', 'after'): value['facts']['pages'][when][0][key] = bad
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, message): self.check(value)
        value = fixture()
        for when in ('before', 'after'): value['facts']['pages'][when][0]['url'] = 'http://127.0.0.1:9/201'
        with self.assertRaisesRegex(ValueError, 'another origin'): self.check(value)
        value = fixture(); value['facts']['pages']['after'].pop()
        with self.assertRaisesRegex(ValueError, 'retained page pair missing'): self.check(value)

    def test_native_view_ownership_visibility_attachment_and_parent_geometry_are_checked(self):
        self.reject_fields([(['facts', 'themes', theme, 'native', i, key], bad)
                            for theme in range(2) for i in range(2)
                            for key, bad in [('tabId', 'foreign'), ('webContentsId', 9999),
                                             ('index', 0), ('desk', 'foreign')]], 'another page')
        self.reject_fields([(['facts', 'themes', 0, 'native', 0, key], False)
                            for key in ('visible', 'parentVisible', 'cachedVisible', 'attached')], 'hidden or detached')
        self.reject_fields([(['facts', 'themes', 0, 'native', 0, 'actualBounds', 'width'], 5)], 'actual native bounds')
        self.reject_fields([(['facts', 'themes', 0, 'native', 0, 'viewBounds', 'x'], 1)], 'parent/child hierarchy')
        value = fixture(); value['facts']['themes'][0]['native'].pop()
        with self.assertRaisesRegex(ValueError, 'native pages missing'): self.check(value)
        value = fixture(); row = value['facts']['themes'][0]['native'][1]
        row['parentBounds'] = {'x': 6, 'y': 0, 'width': 6, 'height': 8}; row['viewBounds']['x'] = 0
        self.assertTrue(self.check(value)['ok'], 'An equivalent actual clip-parent hierarchy is valid')

    def test_coherent_duplicate_page_ids_cannot_be_two_retained_pages(self):
        value = fixture(); facts = value['facts']; identifier = facts['pages']['before'][0]['id']
        for when in ('before', 'after'): facts['pages'][when][1]['id'] = identifier
        facts['pageAPIs'][1]['tabId'] = identifier
        for scene in facts['themes']: scene['native'][1]['tabId'] = identifier
        with self.assertRaisesRegex(ValueError, 'distinct native pages'): self.check(value)

    def test_coherent_duplicate_webcontents_cannot_be_two_retained_pages(self):
        value = fixture(); facts = value['facts']; identifier = facts['pages']['before'][0]['webContentsId']
        for when in ('before', 'after'): facts['pages'][when][1]['webContentsId'] = identifier
        for scene in facts['themes']: scene['native'][1]['webContentsId'] = identifier
        with self.assertRaisesRegex(ValueError, 'distinct native pages'): self.check(value)

    def test_http_scheme_alone_is_not_an_absolute_ai_website(self):
        for url in ('https:synthetic-invalid', 'https://', 'http:///synthetic-path',
                    'https://example.test:bad/', 'https://example.test:70000/', 'https://bad host.test/'):
            value = fixture(); value['facts']['themes'][0]['aiOptions'].append(url)
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, 'AI website chooser'):
                self.check(value)

    def test_settings_round_trips_require_platform_native_trusted_target_receipts(self):
        for platform, arch, source, scale in PLATFORMS:
            for key, bad in [('source', 'synthetic-input'), ('navigates', True), ('at', None)]:
                value = fixture(platform, arch, source, scale); value['owner']['nativeInputs'][0][key] = bad
                with self.subTest(platform=platform, key=key), self.assertRaisesRegex(ValueError, 'native'):
                    self.check(value)
            for key, bad in [('type', 'pointerdown'), ('trusted', False), ('matches', False)]:
                value = fixture(platform, arch, source, scale); value['owner']['nativeInputs'][0]['events'][0][key] = bad
                with self.subTest(platform=platform, event=key), self.assertRaisesRegex(ValueError, 'native shell click'):
                    self.check(value)
        for selector in ('#settings-button', '#settings-dialog [data-close-dialog]'):
            value = fixture(); value['owner']['nativeInputs'] = [
                row for row in value['owner']['nativeInputs'] if row['selector'] != selector]
            with self.assertRaisesRegex(ValueError, 'round trips missing'): self.check(value)
        value = fixture(); value['owner']['nativeInputs'][0]['point']['x'] = None
        with self.assertRaisesRegex(ValueError, 'input point absent'): self.check(value)

    def test_capture_scenes_cannot_be_omitted_relabelled_or_taken_outside_native_display(self):
        self.reject_fields([(['facts', 'captures'], CAPTURES[:1]),
                            (['facts', 'themes', 1, 'theme'], 'light'),
                            (['facts', 'themes', 0, 'capture'], CAPTURES[1])], 'both-theme removal scenes missing')
        value = fixture(); value['owner']['captures'].pop()
        with self.assertRaisesRegex(ValueError, 'owner capture ledger'): self.check(value)
        self.reject_fields([(['owner', 'captures', 0, 'source'], 'webContents.capturePage'),
                            (['owner', 'captures', 0, 'backend'], '')], 'not a native display frame')
        self.reject_fields([(['owner', 'captures', 0, 'displayFilename'], 'foreign.png')], 'full native display missing')
        self.reject_fields([(['owner', 'captures', 0, 'pixelSize', 'width'], 24)], 'PNG dimensions differ')
        self.reject_fields([(['owner', 'captures', 0, 'screenPixelSize', 'width'], 41)], 'display dimensions differ')
        self.reject_fields([(['owner', 'captures', 0, 'cropPixels', 'x'], 5)], 'window crop differs')
        self.reject_fields([(['owner', 'captures', 0, 'mapping', 'originX'], .5)], 'DPI mapping differs')
        value = fixture(); capture = value['owner']['captures'][0]
        capture['contentBounds']['x'] -= 5; capture['cropPixels']['x'] -= 5
        with self.assertRaisesRegex(ValueError, 'window lies outside native display'): self.check(value)

    def test_png_and_full_display_raw_bytes_and_hashes_cannot_be_substituted(self):
        for index, name in enumerate(CAPTURES):
            display = name[:-4] + '-display.png'
            for field in ('sha256', 'displaySha256'):
                value = fixture(); value['owner']['captures'][index][field] = 'f' * 64
                with self.subTest(name=name, field=field), self.assertRaisesRegex(ValueError, 'hash differs'):
                    self.check(value)
            value = fixture(); value['owner']['captures'][index]['bytes'] += 1
            with self.assertRaisesRegex(ValueError, 'size/hash differs'): self.check(value)
            for filename in (name, display):
                value = fixture(); del value['raw'][filename]
                with self.subTest(missing=filename), self.assertRaisesRegex(FileNotFoundError, filename):
                    self.check(value)
        # Both the changed crop and its owner hash are coherent. Only the
        # independent full-display-to-crop byte comparison can reject this.
        value = fixture(); name = CAPTURES[0]; raw = png(25, 17, bytes([1, 2, 3]) * (25 * 17))
        value['raw'][name] = raw; value['owner']['captures'][0].update(bytes=len(raw), sha256=sha(raw))
        with self.assertRaisesRegex(ValueError, 'pixels differ from the full native display'): self.check(value)
        value = fixture(); name = CAPTURES[0][:-4] + '-display.png'; raw = png(40, 30, bytes([1, 2, 3]) * (40 * 30))
        value['raw'][name] = raw; value['owner']['captures'][0]['displaySha256'] = sha(raw)
        with self.assertRaisesRegex(ValueError, 'pixels differ from the full native display'): self.check(value)


if __name__ == '__main__':
    unittest.main()
