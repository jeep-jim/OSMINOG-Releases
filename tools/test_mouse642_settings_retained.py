#!/usr/bin/env python3
"""Reject old flat Settings and excess input in the actual current readers."""
import ast
from pathlib import Path
import runpy
import unittest

TOOLS = Path(__file__).resolve().parent
OWNER = runpy.run_path(str(TOOLS / 'mouse642-633-owner-evidence.py'))
REUSE = runpy.run_path(str(TOOLS / 'mouse642-reuse.py'))
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
    value['initial']['toggles'] = [{'key': key, 'checked': False, 'disabled': False} for key in keys]
    for phase in ('initial', 'afterReload'):
        value[phase]['branding'] = {'controlCount': 0, 'footerText': '', 'footerIcon': True,
                                    'settingsHeading': 'Настройки', 'versionLabel': 'v6.0.42'}
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
        self.assertEqual(result['toggles'], ['showFavicons', 'desktopGestures', 'downloadBounce', 'downloadBadge'])
        self.assertTrue(result['nonmodal'])

    def test_removed_brand_controls_captions_and_missing_icon_or_version_are_rejected(self):
        for phase in ('initial', 'afterReload'):
            for defect in ('missing-proof', 'control', 'false-count', 'footer-text', 'footer-icon',
                           'heading', 'missing-heading', 'empty-heading', 'blank-heading',
                           'version', 'brand-version', 'toggle'):
                facts = settings_fixture()
                state = facts['settings'][phase]
                branding = state['branding']
                if defect == 'missing-proof': del state['branding']
                elif defect == 'control': branding['controlCount'] = 1
                elif defect == 'false-count': branding['controlCount'] = False
                elif defect == 'footer-text': branding['footerText'] = 'Mouse Browser'
                elif defect == 'footer-icon': branding['footerIcon'] = False
                elif defect == 'heading': branding['settingsHeading'] = 'Настройки Mouse Browser'
                elif defect == 'missing-heading': del branding['settingsHeading']
                elif defect == 'empty-heading': branding['settingsHeading'] = ''
                elif defect == 'blank-heading': branding['settingsHeading'] = ' \t '
                elif defect == 'version': branding['versionLabel'] = 'v6.0.41'
                elif defect == 'brand-version': branding['versionLabel'] = 'v6.0.42 Mouse Browser'
                else: state['toggles'].append({'key': 'showBrandName', 'checked': True})
                with self.subTest(phase=phase, defect=defect), self.assertRaisesRegex(ValueError, 'brand'):
                    self.verify(facts)

    def test_version_is_an_exact_token_and_preserves_current_action_suffixes(self):
        for phase in ('initial', 'afterReload'):
            for label in ('', ' \t ', 'v6.0.420', 'v6.0.42beta', 'v6.0.42.1', 'v6.0.42·Обновить'):
                facts = settings_fixture()
                facts['settings'][phase]['branding']['versionLabel'] = label
                with self.subTest(phase=phase, label=label), self.assertRaisesRegex(ValueError, 'brand'):
                    self.verify(facts)
            for label in ('v6.0.42', 'v6.0.42 · Обновить', 'v6.0.42 · Проверить обновления'):
                facts = settings_fixture()
                facts['settings'][phase]['branding']['versionLabel'] = label
                with self.subTest(phase=phase, label=label):
                    self.assertTrue(self.verify(facts)['nonmodal'])

    def test_each_remaining_setting_must_toggle_persist_reload_and_restore(self):
        for key in OWNER['SETTINGS']:
            for defect in ('missing', 'unchanged', 'not-persisted', 'not-reloaded', 'not-restored'):
                facts = settings_fixture()
                value = facts['settings']
                row = next(item for item in value['toggles'] if item['key'] == key)
                if defect == 'missing': value['toggles'].remove(row)
                elif defect == 'unchanged': row['changed'] = row['before']
                elif defect == 'not-persisted': value['persisted'][key] = False
                elif defect == 'not-reloaded':
                    next(item for item in value['afterReload']['toggles'] if item['key'] == key)['checked'] = False
                else: row['restored'] = row['changed']
                with self.subTest(key=key, defect=defect), self.assertRaises(ValueError):
                    self.verify(facts)

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
