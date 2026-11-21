#!/usr/bin/env python3
"""Retain byte-frozen634 algorithms with explicit635 identities."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name("mouse635-reuse.py")))
_reuse["load"]('test_mouse634_feedback_evidence.py',namespace=globals())


# Synthetic635 positions model the newly requested toolbar/footer contract.
_fixtures_before_toolbar = fixtures


def fixtures():
    files, facts = _fixtures_before_toolbar()
    for row in facts[CHECK.JSON_NAMES[2]]['cases']:
        controls = row['controls']
        row['count'] = 7
        row['actions'] = ['tile-search', 'emoji', 'zoom', 'history', 'bookmarks', 'downloads', 'screenshot']
        row['label'] = 'Поиск, эмодзи, масштаб, история, закладки, загрузки и скриншот'
        controls['left'] = ['website']
        controls['right'].insert(len(controls['right']) - 1, 'theme-button')
        controls['themeBeforeSettings'] = True
        controls['privacy'] = {
            'parent': 'toolbar', 'hit': True, 'single': True, 'appRegion': 'no-drag',
            'bounds': {'x': 84, 'y': 8, 'width': 28, 'height': 28, 'right': 112},
            'icon': {'x': 86, 'y': 15, 'width': 24, 'height': 14, 'right': 110},
            'toolbar': {'x': 0, 'y': 0, 'width': row['width'], 'height': 46, 'right': row['width']},
            'traffic': {'x': 0, 'y': 0, 'width': 80, 'height': 46, 'right': 80},
        }
    return files, facts


def toolbar_privacy_and_theme_placement(self):
    for mutate in (
        lambda c: c.update(left=['website', 'theme', 'privacy', 'screenshot']),
        lambda c: c.update(themeBeforeSettings=False),
        lambda c: c['privacy'].update(parent='footer'),
        lambda c: c['privacy'].update(hit=False),
        lambda c: c['privacy'].update(single=False),
        lambda c: c['privacy']['bounds'].update(x=130, right=158),
        lambda c: c['privacy']['icon'].update(width=15),
    ):
        self.setUp()
        mutate(self.footer['cases'][0]['controls'])
        self.reject('footer order|privacy toolbar')


FeedbackContract.test_toolbar_privacy_and_theme_placement = toolbar_privacy_and_theme_placement

if __name__=="__main__":
 import unittest
 unittest.main()
