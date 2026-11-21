#!/usr/bin/env python3
"""Run byte-frozen633 algorithms against634 facts; never rewrite evidence."""
import runpy
from pathlib import Path
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse634-reuse.py')))
_retained = _reuse['load']('test_mouse633_feedback_evidence.py', namespace=globals())
globals().update({key: value for key, value in _retained.items() if not key.startswith('__')})

_fixtures_before_search = fixtures


def fixtures():
    files, facts = _fixtures_before_search()
    for row in facts[CHECK.JSON_NAMES[2]]['cases']:
        row['count'] = 6
        row['actions'] = ['tile-search', 'emoji', 'zoom', 'history', 'bookmarks', 'downloads']
        row['label'] = 'Поиск, эмодзи, история, закладки и загрузки'
    return files, facts


def search_footer_order(self):
    expected = ['tile-search', 'emoji', 'zoom', 'history', 'bookmarks', 'downloads']
    for actions, count in [(expected[1:], 5), (expected[1:], 6),
                           (['emoji', 'tile-search', *expected[2:]], 6),
                           ([*expected, 'tile-search'], 7), (expected, 5)]:
        self.setUp()
        self.footer['cases'][0].update(actions=actions, count=count)
        self.reject('overflow/order')


FeedbackContract.test_search_is_required_immediately_before_smile = search_footer_order


def search_footer_accessible_label(self):
    for label in (None, '', 'Эмодзи, история, закладки и загрузки', True):
        self.setUp()
        if label is None:
            self.footer['cases'][0].pop('label')
        else:
            self.footer['cases'][0]['label'] = label
        self.reject('accessible label')


FeedbackContract.test_search_is_named_in_the_actual_accessible_group_label = search_footer_accessible_label

if __name__ == '__main__':
    unittest.main()
