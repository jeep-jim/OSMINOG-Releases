#!/usr/bin/env python3
"""Synthetic637 preset contract mutations, never native acceptance evidence."""
import ast
import copy
import hashlib
from pathlib import Path
import runpy
import struct
import tempfile
import unittest
from urllib.parse import quote
import zlib

P = runpy.run_path(str(Path(__file__).with_name('mouse637-presets-evidence.py')))
ORIGIN = 'http://127.0.0.1:12345'


def leaf(n): return {'id': 'p' + str(n)}
def split(axis, ratio, a, b): return {'axis': axis, 'ratio': ratio, 'a': a, 'b': b}
def column(*ids): return leaf(ids[0]) if len(ids) == 1 else split('y', 1 / len(ids), leaf(ids[0]), column(*ids[1:]))
def columns(*trees): return trees[0] if len(trees) == 1 else split('x', 1 / len(trees), trees[0], columns(*trees[1:]))


def trees():
    return {'trader': split('x', .66, leaf(1), column(2, 3, 4)),
            'support': split('x', .64, split('x', .5, column(1, 2), column(3, 4)), leaf(5)),
            'design': split('x', .64, split('y', .66, leaf(1), split('x', .5, leaf(2), leaf(3))), column(4, 5)),
            'content': columns(*(column(i, i + 1) for i in range(1, 13, 2))), 'agents': leaf(1)}


def png(rgb, width=1000, height=800):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress((b'\0' + bytes(rgb) * width) * height)) + chunk(b'IEND', b''))


def fixture(platform='linux'):
    all_trees = trees()
    automatic = {'enabled': False, 'running': False, 'port': 0, 'autonomous': True, 'terminal': False,
                 'connectionUrl': '', 'writeAllowed': False, 'commandsAllowed': False, 'devEnabled': False,
                 'devRunning': False, 'workerRunning': False, 'modelRequests': 0}
    report = {'schema': 1, 'version': '6.0.37', 'platform': platform, 'arch': 'arm64' if platform == 'darwin' else 'x64',
              'pid': 71, 'packaged': True, 'ok': True, 'source': P['SOURCE'], 'fixtureOrigin': ORIGIN,
              'catalog': [{'id': mode, 'sites': sites[:], 'tree': copy.deepcopy(all_trees[mode])} for mode, sites in P['CATALOG'].items()],
              'applications': [], 'selectedRequests': []}
    inputs, files, pages, cached, next_id = [], {}, {}, {}, 0

    def input_click(selector):
        entry = {'selector': selector, 'source': P['N']['source'](platform), 'point': {'x': 45, 'y': 67},
                 'at': 10000 + len(inputs), 'trusted': True, 'pid': 71,
                 'events': [{'type': 'click', 'matches': True, 'trusted': True, 'at': 10000 + len(inputs)}]}
        inputs.append(entry)
        return copy.deepcopy(entry)

    def add(url, internal=False):
        nonlocal next_id
        next_id += 1
        identifier = 'owned-' + str(next_id)
        value = {'id': identifier, 'internal': internal, 'url': url, 'webContentsId': None, 'identity': None}
        if not internal:
            value.update(webContentsId=100 + next_id, identity=next_id / 1000, timeOrigin=12345678.25 + next_id,
                         navigationEpoch=0, field='preserved-preset-' + identifier, scrollX=0, scrollY=0)
        pages[identifier] = value
        return value

    def snapshot(): return copy.deepcopy(list(pages.values()))

    original = None
    for index, mode in enumerate(P['SEQUENCE']):
        if index == 6:
            pages, cached = {}, {}
            ai_only = add(ORIGIN + '/ai-only')
            only_before = snapshot()
        before, offset, selected = snapshot(), len(report['selectedRequests']), []
        for number, canonical in enumerate(P['CATALOG'][mode], 1):
            if canonical not in cached:
                internal = canonical == 'mouse://start'
                observed = canonical if internal else ORIGIN + '/suggested/' + quote(canonical, safe="~()*!.'-_")
                row = add(observed, internal)
                cached[canonical] = row['id']
                if not internal: report['selectedRequests'].append(canonical)
            row = pages[cached[canonical]]
            selected.append({'pane': 'p' + str(number), 'url': canonical, 'id': row['id'], 'webContentsId': row['webContentsId'],
                             'observedURL': row['url'], 'identity': row['identity'], 'internal': row['internal']})
        application = {'mode': mode, 'desk': 'desk-4' if index == 6 else 'desk-2', 'tree': copy.deepcopy(all_trees[mode]),
                       'slots': {row['pane']: row['id'] for row in selected}, 'selected': selected,
                       'beforePages': before, 'afterPages': copy.deepcopy(before), 'requestBefore': offset,
                       'requestAfter': len(report['selectedRequests']), 'requestDelta': len(report['selectedRequests']) - offset,
                       'input': input_click('#desk-modes [data-mode="' + mode + '"]'),
                       'automaticBefore': copy.deepcopy(automatic), 'automaticAfter': copy.deepcopy(automatic)}
        report['applications'].append(application)
        if index == 0:
            add(ORIGIN + '/owned-ai')
            original = snapshot()
        if mode == 'agents':
            identifier = selected[0]['id']
            initial, before_ids = copy.deepcopy(pages[identifier]), sorted(pages)
            navigation = {'id': identifier, 'internal': False, 'url': ORIGIN + '/', 'webContentsId': 600,
                          'identity': .9, 'timeOrigin': 12345698.25, 'navigationEpoch': 1,
                          'field': 'preserved-preset-' + identifier, 'scrollX': 0, 'scrollY': 0}
            pages[identifier] = navigation
            themes = []
            for theme, color in [('light', [246, 247, 249]), ('dark', [17, 23, 31])]:
                raw = png(color)
                name = 'mouse-637-localhost-' + theme + '.png'
                files[name] = files[name[:-4] + '-display.png'] = raw
                bounds = {'x': 0, 'y': 0, 'width': 1000, 'height': 800}
                capture = {'filename': name, 'displayFilename': name[:-4] + '-display.png', 'source': 'globalCapture.acquire(display)',
                           'backend': 'synthetic-unit-fixture', 'kind': 'screen', 'pid': 71, 'sha256': hashlib.sha256(raw).hexdigest(),
                           'displaySha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw),
                           'screenPixelSize': {'width': 1000, 'height': 800}, 'pixelSize': {'width': 1000, 'height': 800},
                           'contentBounds': bounds, 'display': {'bounds': bounds, 'scaleFactor': 1}, 'cropPixels': bounds,
                           'mapping': {'scaleX': 1, 'scaleY': 1, 'originX': 0, 'originY': 0}}
                background = 'rgb(%d, %d, %d)' % tuple(color)
                themes.append({'theme': theme, 'id': identifier, 'slot': identifier,
                               'pane': {'x': 0, 'y': 0, 'width': 600, 'height': 700},
                               'agent': {'x': 606, 'y': 0, 'width': 394, 'height': 700}, 'agentHidden': False,
                               'background': background, 'resolvedBackground': background, 'color': 'rgb(212, 212, 212)',
                               'readOnly': False, 'disabled': False, 'value': 'http://127.0.0.1:3000/', 'capture': capture})
            report['agentLanding'] = {'id': identifier, 'initial': initial, 'themes': themes,
                                      'input': input_click('.localhost-start-open'), 'navigation': copy.deepcopy(navigation),
                                      'restored': copy.deepcopy(navigation), 'beforeIds': before_ids, 'afterIds': before_ids[:],
                                      'automaticBefore': copy.deepcopy(automatic), 'automaticAfter': copy.deepcopy(automatic)}
        if index == 5:
            repeat = snapshot()
            report['repeat'] = {'mode': 'support', 'beforePages': repeat, 'afterPages': copy.deepcopy(repeat),
                                'requestBefore': 22, 'requestAfter': 22, 'newRequests': 0}
            report['preservation'] = {'beforePages': original, 'afterPages': copy.deepcopy(original)}
        if index == 6:
            report['aiOnly'] = {'id': ai_only['id'], 'beforePages': only_before, 'afterPages': copy.deepcopy(only_before),
                                'application': copy.deepcopy(application), 'requestBefore': 22, 'requestAfter': 27}
    return report, inputs, files


class PresetAcceptance(unittest.TestCase):
    def check(self, value, inputs, files):
        return P['verify'](value, P['N']['Evidence'](files.__getitem__), value['platform'], 71, inputs)

    def test_all_platforms_require_real_counts_and_both_theme_pixels(self):
        for platform in ('darwin', 'win32', 'linux'):
            proof = self.check(*fixture(platform))
            self.assertEqual(set(proof), {'mouse-637-localhost-light.png', 'mouse-637-localhost-dark.png'})

    def test_wrong_web_app_catalog_order_and_layout_fail(self):
        mutations = [lambda r: r['catalog'][1]['sites'].__setitem__(1, 'https://faq.whatsapp.com/'),
                     lambda r: r['applications'][3]['tree'].update(ratio=.5),
                     lambda r: r['applications'][0]['slots'].update(p1='absent'),
                     lambda r: r['applications'][0]['selected'][0].update(url='https://telegram.org/'),
                     lambda r: r['catalog'].reverse()]
        self.reject(mutations)

    def reject(self, mutations):
        for mutation in mutations:
            report, inputs, files = fixture()
            mutation(report)
            with self.assertRaises((ValueError, KeyError)): self.check(report, inputs, files)

    def test_fake_counts_duplicate_requests_and_replaced_documents_fail(self):
        self.reject([lambda r: r['selectedRequests'].pop(),
                     lambda r: r['applications'][1].update(requestDelta=0),
                     lambda r: r['applications'][5]['selected'][0].update(webContentsId=999),
                     lambda r: r['preservation']['afterPages'][0].update(field='lost draft'),
                     lambda r: r['repeat']['afterPages'][0].update(timeOrigin=123),
                     lambda r: r['applications'][-1].update(desk='desk-2')])

    def test_permissions_worker_or_listener_cannot_start_with_presets(self):
        self.reject([lambda r: r['applications'][0]['automaticAfter'].update(enabled=True),
                     lambda r: r['applications'][2]['automaticAfter'].update(writeAllowed=True),
                     lambda r: r['agentLanding']['automaticAfter'].update(modelRequests=1),
                     lambda r: r['agentLanding']['automaticAfter'].update(terminal=True)])

    def test_localhost_placement_theme_navigation_and_retention_are_mandatory(self):
        self.reject([lambda r: r['agentLanding']['themes'][1].update(background='rgb(255, 255, 255)', resolvedBackground='rgb(255, 255, 255)'),
                     lambda r: r['agentLanding']['themes'][0].update(readOnly=True),
                     lambda r: r['agentLanding']['themes'][0]['agent'].update(x=300),
                     lambda r: r['agentLanding']['restored'].update(webContentsId=998),
                     lambda r: r['agentLanding']['afterIds'].pop()])

    def test_native_input_requires_real_ledger_and_trusted_event(self):
        report, inputs, files = fixture()
        inputs.pop(0)
        with self.assertRaises(ValueError): self.check(report, inputs, files)
        report, inputs, files = fixture()
        report['applications'][2]['input']['trusted'] = False
        with self.assertRaises(ValueError): self.check(report, inputs, files)

    def test_raw_os_png_hash_pixel_and_crop_must_match(self):
        report, inputs, files = fixture()
        files['mouse-637-localhost-dark.png'] = png([255, 255, 255])
        with self.assertRaises(ValueError): self.check(report, inputs, files)
        report, inputs, files = fixture()
        capture = report['agentLanding']['themes'][1]['capture']
        raw = png([255, 255, 255])
        files[capture['filename']] = files[capture['displayFilename']] = raw
        capture.update(sha256=hashlib.sha256(raw).hexdigest(), displaySha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
        with self.assertRaises(ValueError): self.check(report, inputs, files)

    def test_legacy_adaptation_is_exact_and_frozen_files_are_unchanged(self):
        reuse = runpy.run_path(str(Path(__file__).with_name('mouse637-reuse.py')))
        for name in reuse['FROZEN']: reuse['checked'](name)
        tree = reuse['adapted_tree']('mouse632-release.py')
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id == '_mouse637_verify_mode_requests']
        self.assertEqual(len(calls), 1)
        constants = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant)]
        self.assertIn('five-mode-populated-presets-preserve-live-pages', constants)
        self.assertNotIn('five-mode-layouts-empty-only-suggestions', constants)
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaises(ValueError): P['verify_legacy_facts']({'suggestedRequests': 7}, output)

    def test_legacy_actual_count_and_pngs_require_the_complete_new_contract(self):
        report, _, files = fixture('darwin')
        landing = report['agentLanding']
        local = {**landing['navigation'], 'id': 'settings-local', 'webContentsId': 900, 'field': 'preserved-preset-settings-local'}
        identifiers = sorted(landing['beforeIds'] + [local['id']])
        landing['settingsLaunch'] = {'before': local, 'after': copy.deepcopy(local), 'previousId': landing['id'],
                                    'previousRetained': True, 'beforeIds': identifiers, 'afterIds': identifiers[:]}
        with tempfile.TemporaryDirectory() as output:
            for row in landing['themes']:
                raw = files[row['capture']['filename']]
                rgb = P['rgb'](row['background'])
                name = 'mouse-622-localhost-' + row['theme'] + '.png'
                row['capture'] = {'filename': name, 'source': 'win.capturePage()', 'sha256': hashlib.sha256(raw).hexdigest(),
                                  'bytes': len(raw), 'pixelSize': {'width': 1000, 'height': 800},
                                  'contentBounds': {'x': 0, 'y': 0, 'width': 1000, 'height': 800},
                                  'point': {'x': 12, 'y': 12}, 'x': 12, 'y': 12, 'expectedRGB': rgb, 'actualRGBA': rgb + [255]}
                (Path(output) / name).write_bytes(raw)
            facts = {'suggestedRequests': 27, 'preservedTabs': 24, 'presetEvidence': report}
            self.assertTrue(P['verify_legacy_facts'](facts, output))
            (Path(output) / 'mouse-622-localhost-dark.png').write_bytes(png([255, 255, 255]))
            with self.assertRaises(ValueError): P['verify_legacy_facts'](facts, output)


if __name__ == '__main__': unittest.main()
