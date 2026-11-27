#!/usr/bin/env python3
"""Retained native-context mutation tests plus641 checkbox state contracts.

The PNGs and JSON here are explicitly synthetic unit fixtures, never native
acceptance. The complete independent reader and its image decoder remain real.
"""
import copy
from pathlib import Path
import runpy
import unittest

TOOLS = Path(__file__).resolve().parent
E = runpy.run_path(str(TOOLS / 'mouse642-context-evidence.py'))
F = runpy.run_path(str(TOOLS / 'test_mouse635_context_evidence.py'))
_old_fixture = F['fixture']
_old_globals = _old_fixture.__globals__
_old_globals['E'] = E


def fixture(*args, **kwargs):
    files, facts = _old_fixture(*args, **kwargs)
    facts['version'] = E['VERSION']
    for row in facts['scenarios']:
        private = row['scope'] == 'private'
        row['controls'] = {'muted': False, 'adBlock': {'host': '127.0.0.1', 'eligible': True,
                           'excluded': False, 'globalEnabled': True, 'enabled': True,
                           'privateMode': private, 'canChange': not private}}
        row['menu']['items'][1:1] = [
            {'id': E['PREFIX'] + 'mute', 'type': 'checkbox', 'label': 'Mute tab',
             'visible': True, 'enabled': True, 'checked': False},
            {'id': E['PREFIX'] + 'adblock', 'type': 'checkbox', 'label': 'Block ads on this site',
             'visible': True, 'enabled': not private, 'checked': True}]
        refresh_keys(row)
    return files, facts


def refresh_keys(row):
    name, prefix = row['name'], E['PREFIX']
    action = prefix + 'bookmark' if 'favorite' in name else prefix + name if name.startswith('split-') else prefix + 'grid'
    choices = [item for item in row['menu']['items'] if item.get('visible') and item.get('enabled') and item.get('type') != 'separator']
    keys = ['HOME'] + ['DOWN'] * next(index for index, item in enumerate(choices) if item['id'] == action)
    if action == prefix + 'grid':
        keys += ['RIGHT', 'HOME'] + ['DOWN'] * E['GRID'].index(prefix + 'layout-' + name[5:])
    row['input']['keys'] = [{'key': key, 'at': 1100 + index * 40, 'source': row['input']['source']}
                           for index, key in enumerate(keys + ['ENTER'])]


# Reuse every retained635 mutation test against the complete641 reader. The
# changed menu positions below preserve all four icon/label/grid mutations.
_old_globals['fixture'] = fixture
NativeContextEvidence = F['NativeContextEvidence']
assert NativeContextEvidence.setUpClass.__func__.__globals__ is _old_globals


def exact_menu_labels_grid_and_icons(self):
    self.facts['scenarios'][0]['menu']['items'][4]['label'] = 'Other action'; self.reject('label')
    self.setUp(); self.facts['scenarios'][0]['menu']['items'][7]['submenu'].pop(); self.reject('grid choices')
    self.setUp(); items = self.facts['scenarios'][0]['menu']['items']; items[6]['icon'] = items[5]['icon']; self.reject('distinct native shapes')
    self.setUp(); items = self.facts['scenarios'][0]['menu']['items']; items[4]['icon'] = items[5]['icon']; self.reject('distinct native shapes')


def live_checkbox_states(self):
    icons = {row['filename']: row for row in self.facts['icons']}
    for muted, excluded, globally_enabled in ((False, False, True), (True, False, True), (False, True, True), (True, False, False)):
        row = copy.deepcopy(self.facts['scenarios'][1])
        row['controls']['muted'] = row['menu']['items'][1]['checked'] = muted
        state = row['controls']['adBlock']; state.update(excluded=excluded, globalEnabled=globally_enabled, enabled=globally_enabled and not excluded)
        row['menu']['items'][2].update(checked=state['enabled'], enabled=globally_enabled)
        refresh_keys(row)
        E['menu_contract'](row, icons, row['input']['source'])
    private = self.facts['scenarios'][-1]
    self.assertTrue(private['controls']['adBlock']['privateMode'])
    self.assertFalse(private['menu']['items'][2]['enabled'])
    E['menu_contract'](private, icons, private['input']['source'])


def incorrect_checkbox_states(self):
    mutations = [lambda r: r['menu']['items'][1].update(type='normal'),
                 lambda r: r['menu']['items'][1].update(checked=True),
                 lambda r: r['menu']['items'][2].update(checked=False),
                 lambda r: r['menu']['items'][2].update(enabled=False),
                 lambda r: r['controls']['adBlock'].update(host='different.test'),
                 lambda r: r['controls']['adBlock'].update(privateMode=True),
                 lambda r: r['controls']['adBlock'].update(enabled=False),
                 lambda r: r['controls']['adBlock'].update(canChange=False),
                 lambda r: r['controls'].update(muted='false'),
                 lambda r: r.pop('controls'),
                 lambda r: r['menu']['items'].__delitem__(1)]
    for mutate in mutations:
        self.setUp(); mutate(self.facts['scenarios'][0]); self.reject()
    self.setUp(); self.facts['scenarios'][-1]['menu']['items'][2]['enabled'] = True; self.reject('live policy')


def checkbox_keyboard_positions(self):
    # The original menu keyboard assertions must count both new enabled items.
    self.facts['scenarios'][1]['input']['keys'].pop(1)
    self.reject('native menu keys')


NativeContextEvidence.test_exact_menu_labels_grid_choices_and_native_icons_are_required = exact_menu_labels_grid_and_icons
NativeContextEvidence.test_live_mute_exclusion_global_and_private_states_are_bound = live_checkbox_states
NativeContextEvidence.test_missing_or_inconsistent_checkbox_states_are_rejected = incorrect_checkbox_states
NativeContextEvidence.test_checkbox_positions_are_counted_by_the_real_keyboard_route = checkbox_keyboard_positions


if __name__ == '__main__':
    unittest.main()
