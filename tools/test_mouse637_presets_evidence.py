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
            'content': columns(*(column(i, i + 1) for i in range(1, 13, 2)))}


def png(rgb, width=1000, height=800):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress((b'\0' + bytes(rgb) * width) * height)) + chunk(b'IEND', b''))


def fixture(platform='linux'):
    all_trees = trees()
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
        if index == len(P['SEQUENCE']) - 1:
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
        application = {'mode': mode, 'desk': 'desk-4' if index == len(P['SEQUENCE']) - 1 else 'desk-2', 'tree': copy.deepcopy(all_trees[mode]),
                       'slots': {row['pane']: row['id'] for row in selected}, 'selected': selected,
                       'beforePages': before, 'afterPages': copy.deepcopy(before), 'requestBefore': offset,
                       'requestAfter': len(report['selectedRequests']), 'requestDelta': len(report['selectedRequests']) - offset,
                       'input': input_click('#desk-modes [data-mode="' + mode + '"]')}
        report['applications'].append(application)
        if index == 0:
            add(ORIGIN + '/owned-ai')
            original = snapshot()
        if index == len(P['SEQUENCE']) - 2:
            repeat = snapshot()
            report['repeat'] = {'mode': 'support', 'beforePages': repeat, 'afterPages': copy.deepcopy(repeat),
                                'requestBefore': 22, 'requestAfter': 22, 'newRequests': 0}
            report['preservation'] = {'beforePages': original, 'afterPages': copy.deepcopy(original)}
        if index == len(P['SEQUENCE']) - 1:
            report['aiOnly'] = {'id': ai_only['id'], 'beforePages': only_before, 'afterPages': copy.deepcopy(only_before),
                                'application': copy.deepcopy(application), 'requestBefore': 22, 'requestAfter': 27}
    return report, inputs, files


class PresetAcceptance(unittest.TestCase):
    def check(self, value, inputs, files):
        return P['verify'](value, P['N']['Evidence'](files.__getitem__), value['platform'], 71, inputs)

    def test_all_platforms_require_four_presets_and_real_counts(self):
        for platform in ('darwin', 'win32', 'linux'):
            proof = self.check(*fixture(platform))
            self.assertEqual(proof, {})
            report = fixture(platform)[0]
            self.assertEqual(len(report['catalog']), 4)
            self.assertEqual(len(report['selectedRequests']), 27)

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
                     lambda r: r['applications'][4]['selected'][0].update(webContentsId=999),
                     lambda r: r['preservation']['afterPages'][0].update(field='lost draft'),
                     lambda r: r['repeat']['afterPages'][0].update(timeOrigin=123),
                     lambda r: r['applications'][-1].update(desk='desk-2')])

    def test_retired_agent_preset_and_landing_are_rejected(self):
        self.reject([lambda r: r['catalog'].append({'id': 'agents', 'sites': ['mouse://start'], 'tree': leaf(1)}),
                     lambda r: r.update(agentLanding={}),
                     lambda r: r['applications'][0].update(mode='agents')])

    def test_native_input_requires_real_ledger_and_trusted_event(self):
        report, inputs, files = fixture()
        inputs.pop(0)
        with self.assertRaises(ValueError): self.check(report, inputs, files)
        report, inputs, files = fixture()
        report['applications'][2]['input']['trusted'] = False
        with self.assertRaises(ValueError): self.check(report, inputs, files)

    def test_legacy_adaptation_is_exact_and_frozen_files_are_unchanged(self):
        reuse = runpy.run_path(str(Path(__file__).with_name('mouse637-reuse.py')))
        for name in reuse['FROZEN']: reuse['checked'](name)
        tree = reuse['adapted_tree']('mouse632-release.py')
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                 and node.func.id == '_mouse637_verify_mode_requests']
        self.assertEqual(len(calls), 1)
        constants = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant)]
        self.assertIn('four-mode-populated-presets-preserve-live-pages', constants)
        self.assertNotIn('five-mode-populated-presets-preserve-live-pages', constants)
        self.assertNotIn('five-mode-layouts-empty-only-suggestions', constants)
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaises(ValueError): P['verify_legacy_facts']({'suggestedRequests': 7}, output)

    def test_legacy_actual_count_and_preservation_require_the_complete_current_contract(self):
        report, _, _ = fixture('darwin')
        facts = {'suggestedRequests': 27, 'preservedTabs': 23, 'presetEvidence': report}
        with tempfile.TemporaryDirectory() as output:
            self.assertTrue(P['verify_legacy_facts'](facts, output))
            for key, bad in [('suggestedRequests', 7), ('preservedTabs', 24)]:
                changed = copy.deepcopy(facts); changed[key] = bad
                with self.assertRaises(ValueError): P['verify_legacy_facts'](changed, output)
            changed = copy.deepcopy(facts)
            changed['presetEvidence']['repeat']['afterPages'][0]['field'] = 'lost draft'
            with self.assertRaises(ValueError): P['verify_legacy_facts'](changed, output)


if __name__ == '__main__': unittest.main()
