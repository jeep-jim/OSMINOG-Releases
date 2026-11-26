#!/usr/bin/env python3
"""Reject old flat Settings and excess input in the actual current readers."""
import ast
from pathlib import Path
import runpy
import unittest

TOOLS = Path(__file__).resolve().parent
OWNER = runpy.run_path(str(TOOLS / 'mouse641-633-owner-evidence.py'))
REUSE = runpy.run_path(str(TOOLS / 'mouse641-reuse.py'))
OLD_FIXTURE = runpy.run_path(str(TOOLS / 'test_mouse633_owner_feedback_evidence.py'))
PAGES = ['overview', 'appearance', 'surfaces', 'workspace', 'privacy', 'imports', 'capture', 'downloads', 'documents', 'about']


def settings_fixture():
    _, facts = OLD_FIXTURE['fixture']()
    value = facts['settings']
    sections = [{'name': name, 'hidden': name not in ('privacy', 'overview-links'), 'title': name}
                for name in OWNER['SECTIONS']]
    value['sections'] = list(OWNER['SECTIONS'])
    value['initial'].update(sections=sections, selectedPage='overview', navigation=PAGES[:])
    keys = OWNER['SETTINGS']
    value['toggles'] = [{'key': key, 'before': False, 'changed': True, 'afterReload': True, 'restored': False}
                        for key in keys]
    value['persisted'] = dict.fromkeys(keys, True)
    value['afterReload']['toggles'] = [{'key': key, 'checked': True} for key in keys]
    value['search']['readback']['sections'] = [{**row, 'hidden': row['name'] != 'downloads'} for row in sections]
    value['categoryInputs'] = []
    for page in ('appearance', 'workspace', 'downloads', 'imports'):
        event = {'selector': '#settings-dialog .settings-nav-item[data-settings-page="' + page + '"]',
                 'events': [{'type': 'click', 'trusted': True, 'matches': True}]}
        facts['nativeInputs'].append(event)
        value['categoryInputs'].append({'page': page, 'input': event})
    return facts


class RetainedSettings(unittest.TestCase):
    def verify(self, facts):
        return OWNER['settings_contract'](facts, facts['settings']['livePages']['before'], facts['fixtureOrigin'])

    def test_categorized_overview_preserves_actual_native_pages_and_persisted_controls(self):
        result = self.verify(settings_fixture())
        self.assertEqual(result['sections'], OWNER['SECTIONS'])
        self.assertTrue(result['nonmodal'])

    def test_flat_hidden_or_wrong_category_overview_fails(self):
        for defect in ('flat', 'hidden-adblock', 'wrong-page', 'missing-navigation'):
            facts = settings_fixture()
            initial = facts['settings']['initial']
            if defect == 'flat':
                for row in initial['sections']: row['hidden'] = False
            elif defect == 'hidden-adblock': initial['sections'][0]['hidden'] = True
            elif defect == 'wrong-page': initial['selectedPage'] = 'appearance'
            else: initial['navigation'].pop()
            with self.subTest(defect=defect), self.assertRaisesRegex(ValueError, 'Settings sections'):
                self.verify(facts)

    def test_missing_or_untrusted_category_receipt_fails(self):
        for defect in ('missing', 'unbound', 'untrusted'):
            facts = settings_fixture()
            rows = facts['settings']['categoryInputs']
            if defect == 'missing': rows.pop()
            elif defect == 'unbound': facts['nativeInputs'].remove(rows[0]['input'])
            else: rows[0]['input']['events'][0]['trusted'] = False
            with self.subTest(defect=defect), self.assertRaisesRegex(ValueError, 'Settings category'):
                self.verify(facts)

    def test_live_page_state_and_toggle_persistence_still_reject_mutations(self):
        for defect in ('page-state', 'persisted-toggle'):
            facts = settings_fixture()
            if defect == 'page-state': facts['settings']['livePages']['after'][0]['field'] = 'lost'
            else: facts['settings']['toggles'][0]['afterReload'] = False
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                self.verify(facts)

    def test_actual_native_ledger_guard_allows_only_old_budget_plus_thirty_settings_clicks(self):
        tree = REUSE['adapted_tree']('mouse637-features-evidence.py')
        verify = next(row for row in tree.body if isinstance(row, ast.FunctionDef) and row.name == 'verify')
        guards = [row for row in verify.body if isinstance(row, ast.Expr) and isinstance(row.value, ast.Call)
                  and any(isinstance(arg, ast.Constant) and arg.value == '637 actual input ledger missing'
                          for arg in row.value.args)]
        self.assertEqual(len(guards), 1)
        code = compile(ast.Module(body=guards, type_ignores=[]), '<actual-current-native-ledger-guard>', 'exec')
        def need(ok, message):
            if not ok: raise ValueError(message)
        for count in (50, 200, 215, 230): exec(code, {'native': [None] * count, 'need': need})
        for invalid in ([None] * 49, [None] * 231, tuple([None] * 215)):
            with self.assertRaisesRegex(ValueError, 'actual input ledger'):
                exec(code, {'native': invalid, 'need': need})


if __name__ == '__main__':
    unittest.main()
