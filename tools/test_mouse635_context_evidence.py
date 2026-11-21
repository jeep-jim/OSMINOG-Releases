#!/usr/bin/env python3
"""Retain byte-frozen634 algorithms with explicit635 identities."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name("mouse635-reuse.py")))
_reuse["load"]('test_mouse634_context_evidence.py',namespace=globals())


_fixture_before_pin = fixture


def fixture(*args, **kwargs):
    files, facts = _fixture_before_pin(*args, **kwargs)
    raw = icon_png(13)
    checksum = E['sha'](raw)
    name = 'mouse-633-context-icon-' + checksum[:20] + '.png'
    files[name] = raw
    icon = {'filename': name, 'sha256': checksum, 'logicalSize': {'width': 16, 'height': 16},
            'pixelSize': {'width': 32, 'height': 32}, 'scales': [2], 'template': facts['platform'] == 'darwin'}
    facts['icons'].append(icon)
    for row in facts['scenarios']:
        row['menu']['items'].insert(2, {'id': E['PREFIX'] + 'pin', 'label': 'Pin pane', 'type': 'normal',
                                      'enabled': True, 'visible': True, 'role': '', 'icon': icon})
        if 'favorite' not in row['name']:
            row['input']['keys'].insert(1, {'key': 'DOWN', 'source': row['input']['source']})
            for index, event in enumerate(row['input']['keys']):
                event['at'] = 1100 + index * 40
    return files, facts


def pin_menu_labels_grid_and_icons(self):
    self.facts['scenarios'][0]['menu']['items'][2]['label'] = 'Other action'; self.reject('label')
    self.setUp(); self.facts['scenarios'][0]['menu']['items'][5]['submenu'].pop(); self.reject('grid choices')
    self.setUp(); items = self.facts['scenarios'][0]['menu']['items']; items[4]['icon'] = items[3]['icon']; self.reject('distinct native shapes')
    self.setUp(); items = self.facts['scenarios'][0]['menu']['items']; items[2]['icon'] = items[3]['icon']; self.reject('distinct native shapes')


NativeContextEvidence.test_exact_menu_labels_grid_choices_and_native_icons_are_required = pin_menu_labels_grid_and_icons

if __name__=="__main__":
 import unittest
 unittest.main()
