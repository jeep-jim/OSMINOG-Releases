"""Causal synthetic reader rejection tests; these are not native acceptance."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('mouse643_polish', Path(__file__).with_name('mouse643-polish-evidence.py'))
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


def page(index=0):
    return {'id': 'page-' + str(index), 'index': index, 'desk': 'desk-1', 'webContentsId': 101 + index,
            'url': 'http://127.0.0.1:9000/page/' + str(index) + '/', 'navigationEpoch': 1,
            'identity': 'document-' + str(index), 'timeOrigin': 1000 + index, 'field': 'preserved',
            'scrollX': 0, 'scrollY': 130, 'cookie': 'owned=1', 'ticks': 10}


def click(selector='.control'):
    return {'pid': 1010, 'selector': selector, 'source': 'CGEvent', 'point': {'x': 21, 'y': 37}, 'at': 100,
            'events': [{'type': 'pointerdown', 'trusted': True, 'matches': True},
                       {'type': 'click', 'trusted': True, 'matches': True}]}


def chrome(theme='light', mode='square'):
    color = '#EACB92' if theme == 'light' else '#1D4B5C'
    tabs = [{'id': str(i), 'active': i == 0, 'text': 'Complete page title ' + str(i), 'title': 'Complete page title ' + str(i),
             'tooltip': 'Complete page title ' + str(i), 'background': 'rgb(255, 255, 255)',
             'radii': ['0px'] * 4, 'buttons': [{'radii': ['0px'] * 4}]} for i in range(2)]
    return {'platform': 'darwin', 'theme': theme, 'mode': mode, 'flowCount': 0, 'rootPanel': '#FFFFFF',
            'appearance': {'paneMode': mode, 'surfaces': {theme: {'top': {'mode': 'solid', 'color': color,
                'endColor': color, 'opacity': 100, 'angle': 0}}}}, 'tabs': tabs,
            'traffic': [{'action': action, 'bounds': {'x': i * 21, 'y': 12, 'width': 13, 'height': 13},
                         'radii': ['50%'] * 4} for i, action in enumerate(('quit', 'minimize', 'zoom'))],
            'dividers': [{'axis': 'x', 'bounds': {'x': 410, 'y': 60, 'width': 1, 'height': 500},
                          'guide': {'width': '1px', 'left': '0px', 'transform': 'none'}}]}


def search():
    grid = {'tree': {'axis': 'x', 'ratio': .5, 'a': {'id': 'p1'}, 'b': {'id': 'p2'}},
            'slots': {'p1': 'page-0', 'p2': 'page-1'}, 'active': 'p1'}
    url = 'https://www.google.com/search?q=mouse+browser+tips'
    actual = 'http://127.0.0.1:9000/page/3/'
    pages = [page(0), page(1)]
    return {'theme': 'light', 'query': 'mouse browser', 'suggestion': 'mouse browser tips', 'externalProviderVerified': False,
            'provider': {'engine': 'google', 'label': 'Google', 'inside': True, 'first': True, 'icon': True,
                         'button': {'x': 100, 'y': 50, 'width': 32, 'height': 32}, 'query': {'x': 134, 'y': 50, 'width': 300, 'height': 32}},
            'options': ['mouse browser tips', 'mouse browser tabs'], 'typed': [{'trusted': True, 'value': 'mouse browser'}],
            'transport': [{'url': 'https://suggestqueries.google.com/complete/search?client=firefox&q=mouse+browser', 'query': 'mouse browser'}],
            'requestedURL': url, 'actualURL': actual, 'loads': [{'requestedURL': url, 'actualURL': actual}],
            'tabId': 'home-1', 'home': {'id': 'home-1', 'internal': True, 'hadNativePage': False},
            'homeMark': {'src': 'mouse-head.svg', 'filter': 'none'}, 'savedGrid': grid, 'afterGrid': copy.deepcopy(grid),
            'after': {'id': 'home-1', 'webContentsId': 999, 'url': actual, 'sameHomeTab': True, 'newNativePage': True},
            'otherBefore': pages, 'otherAfter': copy.deepcopy(pages), 'input': click('.home-query'), 'submit': click('.home-search-suggestion')}


class PolishReaderTests(unittest.TestCase):
    def test_same_document_survives_ticks_but_rejects_reload_or_migration(self):
        before = page(); after = {**before, 'ticks': 15}; R.same_page(before, after)
        for key in R.IDENTITY:
            value = dict(after); value[key] = None
            with self.subTest(key=key), self.assertRaises(ValueError): R.same_page(before, value)

    def test_native_click_requires_cgevent_actual_child_and_trusted_matched_event(self):
        R.native_input(click(), 1010)
        for change in ({'source': 'sendInputEvent'}, {'pid': 1011}, {'events': [{'type': 'click', 'trusted': False, 'matches': True}]},
                       {'events': [{'type': 'click', 'trusted': True, 'matches': False}]}, {'point': {'x': None, 'y': 2}}):
            with self.subTest(change=change), self.assertRaises(ValueError): R.native_input({**click(), **change}, 1010)

    def test_square_chrome_accepts_actual_box_and_rejects_radius_and_wide_guide(self):
        R.chrome(chrome(), 'light', 'square')
        mutations = [lambda v: v['tabs'][0]['radii'].__setitem__(0, '9px'),
                     lambda v: v['tabs'][0]['buttons'][0]['radii'].__setitem__(0, '4px'),
                     lambda v: v['dividers'][0]['guide'].__setitem__('width', '3px'),
                     lambda v: v['dividers'][0]['guide'].__setitem__('transform', 'matrix(1, 0, 0, 1, -1, 0)'),
                     lambda v: v.__setitem__('flowCount', 1)]
        for mutate in mutations:
            value = chrome(); mutate(value)
            with self.subTest(value=value), self.assertRaises(ValueError): R.chrome(value, 'light', 'square')

    def test_custom_header_cannot_override_active_tab_or_control_shape(self):
        for mutate in (lambda v: v['tabs'][0].__setitem__('background', 'rgb(234, 203, 146)'),
                       lambda v: v['traffic'][0].__setitem__('radii', ['0px'] * 4),
                       lambda v: v['traffic'][1]['bounds'].__setitem__('width', 24)):
            value = chrome(); mutate(value)
            with self.assertRaises(ValueError): R.chrome(value, 'light', 'square')

    def test_full_title_tooltip_cannot_silently_be_url(self):
        value = chrome(); value['tabs'][0]['tooltip'] = 'https://example.invalid/'
        with self.assertRaises(ValueError): R.chrome(value, 'light', 'square')

    def test_real_theme_requires_media_css_and_first_script(self):
        value = {'dark': True, 'light': False, 'initial': True, 'background': 'rgb(27, 41, 55)', 'identity': 'doc', 'timeOrigin': 100}
        R.media(value, 'dark', initial=True)
        for change in ({'dark': False}, {'light': True}, {'initial': False}, {'background': 'rgb(241, 244, 249)'}):
            with self.subTest(change=change), self.assertRaises(ValueError): R.media({**value, **change}, 'dark', initial=True)

    def test_native_search_creates_first_guest_in_same_home_id_and_preserves_grid(self):
        R.search(search(), 'light', 1010)
        mutations = [lambda v: v['after'].__setitem__('id', 'new-tab'), lambda v: v['after'].__setitem__('newNativePage', False),
                     lambda v: v['home'].__setitem__('hadNativePage', True), lambda v: v['loads'].append(dict(v['loads'][0])),
                     lambda v: v['afterGrid']['slots'].__setitem__('p1', 'home-1'), lambda v: v['otherAfter'][0].__setitem__('timeOrigin', 2000),
                     lambda v: v['homeMark'].__setitem__('filter', 'invert(1)')]
        for mutate in mutations:
            value = search(); mutate(value)
            with self.subTest(value=value), self.assertRaises(ValueError): R.search(value, 'light', 1010)

    def test_remote_provider_claim_or_untrusted_typing_or_wrong_query_is_rejected(self):
        for mutate in (lambda v: v.__setitem__('externalProviderVerified', True),
                       lambda v: v['typed'][0].__setitem__('trusted', False),
                       lambda v: v['transport'][0].__setitem__('query', 'other query'),
                       lambda v: v['provider'].__setitem__('first', False),
                       lambda v: v.__setitem__('requestedURL', 'https://www.google.com/search?q=other')):
            value = search(); mutate(value)
            with self.assertRaises(ValueError): R.search(value, 'light', 1010)

    def test_native_drag_requires_all_event_phases_and_unchanged_documents(self):
        before = [page(0), page(1)]
        value = {'pid': 1010, 'source': 'CGEvent', 'completed': True, 'from': {'x': 20, 'y': 30}, 'to': {'x': 80, 'y': 90},
                 'before': before, 'after': copy.deepcopy(before),
                 'events': [{'type': t, 'trusted': True, 'matches': True} for t in ('pointerdown', 'pointermove', 'pointerup')]}
        R.native_drag(value, 1010)
        for key in ('pointerdown', 'pointermove', 'pointerup'):
            changed = copy.deepcopy(value); changed['events'] = [e for e in value['events'] if e['type'] != key]
            with self.assertRaises(ValueError): R.native_drag(changed, 1010)
        value['after'][1]['identity'] = 'reloaded'
        with self.assertRaises(ValueError): R.native_drag(value, 1010)


if __name__ == '__main__': unittest.main()
