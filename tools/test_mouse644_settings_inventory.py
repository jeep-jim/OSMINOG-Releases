"""Synthetic retained-inventory mutations; never native acceptance evidence."""
import ast
import copy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parent
REUSE = runpy.run_path(str(TOOLS / 'mouse644-reuse.py'))
OWNER = runpy.run_path(str(TOOLS / 'mouse644-633-owner-evidence.py'))
AGENT = runpy.run_path(str(TOOLS / 'mouse644-agent-removal-evidence.py'))
SETTINGS = runpy.run_path(str(TOOLS / 'mouse644-settings-evidence.py'))
OLD = runpy.run_path(str(TOOLS / 'test_mouse641_settings_retained.py'))
EXPECTED_TOGGLES = ['showFavicons', 'syncWebsiteTheme', 'desktopGestures', 'downloadBounce', 'downloadBadge']


def fixture():
    with patch.dict(OLD['settings_fixture'].__globals__, {'OWNER': OWNER}):
        facts = OLD['settings_fixture']()
    for phase in ('initial', 'afterReload'):
        facts['settings'][phase]['branding']['versionLabel'] = 'v6.0.44'
    return facts


def verify(facts):
    return OWNER['settings_contract'](facts, facts['settings']['livePages']['before'], facts['fixtureOrigin'])


class RetainedCurrentSettings(unittest.TestCase):
    def test_owner_agent_and_native_settings_readers_require_the_same_current_inventory(self):
        self.assertEqual(list(OWNER['SETTINGS']), EXPECTED_TOGGLES)
        sections = REUSE['SETTINGS_SECTIONS']
        self.assertEqual(len(sections), 20)
        self.assertEqual(sections[12:14], ['adblock-subscriptions', 'adblock-exclusions'])
        self.assertEqual(OWNER['SECTIONS'], sections)
        self.assertEqual(AGENT['SECTIONS'], sections)
        self.assertEqual(SETTINGS['SECTIONS'], sections)
        schema = json.loads((TOOLS.parent / 'staging/mouse/6.0.44-arm64/evidence.schema.json').read_text())
        self.assertEqual(schema['x-currentOwnerGate']['settingsSections'], len(sections))
        self.assertEqual(schema['x-currentOwnerGate']['settingsToggles'], len(EXPECTED_TOGGLES))
        self.assertEqual(verify(fixture())['toggles'], EXPECTED_TOGGLES)

    def test_every_control_including_website_theme_must_toggle_persist_reload_and_restore(self):
        for key in EXPECTED_TOGGLES:
            for defect in ('missing', 'unchanged', 'not-persisted', 'not-reloaded', 'not-restored'):
                facts = fixture(); value = facts['settings']
                row = next(item for item in value['toggles'] if item['key'] == key)
                if defect == 'missing': value['toggles'].remove(row)
                elif defect == 'unchanged': row['changed'] = row['before']
                elif defect == 'not-persisted': value['persisted'][key] = False
                elif defect == 'not-reloaded':
                    next(item for item in value['afterReload']['toggles'] if item['key'] == key)['checked'] = False
                else: row['restored'] = row['changed']
                with self.subTest(key=key, defect=defect), self.assertRaises(ValueError): verify(facts)

    def test_missing_subscription_section_or_extra_control_cannot_pass_owner_contract(self):
        for target in ('sections', 'initial', 'toggles'):
            facts = fixture(); value = facts['settings']
            if target == 'sections': value['sections'].remove('adblock-subscriptions')
            elif target == 'initial':
                value['initial']['sections'] = [row for row in value['initial']['sections'] if row['name'] != 'adblock-subscriptions']
            else:
                value['toggles'].append({**value['toggles'][0], 'key': 'unknownSetting'})
            with self.subTest(target=target), self.assertRaises(ValueError): verify(facts)

    def test_agent_absence_reader_preserves_strict_settings_section_inventory(self):
        value = {'selectors': dict.fromkeys(AGENT['SELECTORS'], 0), 'preloadKeys': [], 'globals': [], 'modelKeys': [],
                 'modes': list(AGENT['MODES']), 'presetKeys': ['support'], 'aiOptions': [*AGENT['AI_CATALOG'], 'custom'],
                 'settingsSections': list(AGENT['SECTIONS'])}
        AGENT['ui'](value)
        for replacement in ([name for name in AGENT['SECTIONS'] if name != 'adblock-subscriptions'],
                            [*AGENT['SECTIONS'], 'agent'], [*AGENT['SECTIONS'], 'unknown-section']):
            with self.assertRaises(ValueError): AGENT['ui']({**value, 'settingsSections': replacement})

    def test_adaptation_rejects_drift_missing_or_duplicate_frozen_assignments(self):
        prior = REUSE['legacy']()
        for name, target in (('mouse633-owner-feedback-evidence.py', 'SETTINGS'),
                             ('mouse633-owner-feedback-evidence.py', 'SECTIONS'),
                             ('mouse637-agent-removal-evidence.py', 'SECTIONS')):
            original = prior['adapted_tree'](name)
            for defect in ('drift', 'missing', 'duplicate'):
                tree = copy.deepcopy(original)
                assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                                  and any(isinstance(item, ast.Name) and item.id == target for item in node.targets))
                if defect == 'drift': assignment.value = ast.parse("['unknown-setting']", mode='eval').body
                elif defect == 'missing': tree.body.remove(assignment)
                else: tree.body.append(copy.deepcopy(assignment))
                legacy = lambda: {'adapted_tree': lambda *_a, **_k: tree}
                with patch.dict(REUSE['adapted_tree'].__globals__, {'legacy': legacy}), self.subTest(name=name, target=target, defect=defect), self.assertRaises(ValueError):
                    REUSE['adapted_tree'](name)


if __name__ == '__main__': unittest.main()
