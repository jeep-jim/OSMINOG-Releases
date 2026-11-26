"""Synthetic reader-unit fixtures. These never constitute native acceptance."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

def module(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), Path(__file__).with_name(name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value
W = module('mouse641-flexible-workspace-evidence')

def identity(name='a', desk='desk-1'):
    return {'id': name, 'index': 1, 'desk': desk, 'webContentsId': 71, 'url': 'http://127.0.0.1:4100/page/1/', 'navigationEpoch': 2, 'identity': 'owned-token', 'timeOrigin': 17000, 'field': 'owned text', 'scrollX': 0, 'scrollY': 131, 'cookie': 'owned=value', 'ticks': 10}

def receipt(selector='#button', action='click'):
    return {'selector': selector, 'source': 'XTest', 'pid': 101, 'action': action, 'at': 1000, 'point': {'x': 40, 'y': 50}, 'from': {'x': 40, 'y': 50}, 'to': {'x': 120, 'y': 80}, 'released': True, 'events': [{'type': 'pointerdown' if action == 'drag' else 'click', 'trusted': True, 'matches': True}]}

def layout_fixture():
    home = {'visible': True, 'search': True, 'favorites': True, 'tabs': [{'id': 'c', 'visible': True}]}
    empty = {'input': receipt('#footer-left [data-action="split-x"]'), 'paneId': 'p3', 'after': {'slots': {'p3': ''}}, 'home': home}
    choice = {'input': receipt('.pane[data-pane="p3"] [data-home-tab="c"]'), 'paneId': 'p3', 'selectedId': 'c', 'after': {'slots': {'p3': 'c'}}, 'identity': identity('c')}
    insertion = {'input': receipt('.tab-item[data-tab="c"] .tab-title', 'drag'), 'insertedId': 'c', 'beforeOrder': ['a', 'b'], 'afterOrder': ['a', 'c', 'b'], 'affordance': {'visible': True, 'axis': 'x', 'edge': 'left', 'target': 'p2', 'neighbor': 'p1', 'svg': True, 'text': 'Insert between panes'}, 'whileHeld': {'active': True, 'ghost': True, 'bodyDragging': True}}
    blank = {'input': receipt('#blank-drag', 'drag'), 'before': identity(), 'after': identity(), 'beforePane': 'p1', 'afterPane': 'p2'}
    carry = {'input': receipt('#blank-drag', 'drag'), 'before': identity(), 'after': identity(desk='desk-2'), 'whileHeld': {'mouseDown': True, 'desktopId': 'desk-2'}, 'hoverMs': 650}
    headers = []
    for theme in ('light', 'dark'):
        for stage in ('tiny', 'resized'):
            width, height = (140, 100) if stage == 'tiny' else (210, 140)
            headers.append({'theme': theme, 'stage': stage, 'inputs': [receipt('.divider[data-path=""]', 'drag'), receipt('.divider[data-path="b"]', 'drag')], 'pane': {'bounds': {'x': 10, 'y': 20, 'width': width, 'height': height}, 'header': {'bounds': {'x': 10, 'y': 20, 'width': width, 'height': 28}, 'visible': True, 'display': 'flex', 'opacity': 1, 'visibility': 'visible'}}})
    value = {'schema': 1, 'ok': True, 'fixture': {'third': identity('c')}, 'empty': empty, 'chooser': choice, 'insertion': insertion, 'blankDrag': blank, 'edgeCarry': carry, 'headers': headers}
    ledger = [value[name]['input'] for name in ('empty', 'chooser', 'insertion', 'blankDrag', 'edgeCarry')] + [event for row in headers for event in row['inputs']]
    return (value, ledger)

def corners_fixture(theme='light'):
    surface = {'mode': 'gradient', 'color': '#F3E6CA' if theme == 'light' else '#594B30', 'endColor': '#F2DCC8' if theme == 'light' else '#403C3D', 'angle': 135, 'opacity': 100}
    appearance = {'surfaces': {theme: {'workspace': surface}}}
    rows, captures = ([], {})
    for stage, width in [('before', 400), ('resized', 360)]:
        workspace = {'x': 0, 'y': 0, 'width': width, 'height': 180}
        grad = W.gradient(surface, theme, workspace)
        image = {'width': width, 'height': 180, 'channels': 4, 'pixels': bytearray(width * 180 * 4)}
        for y in range(180):
            for x in range(width):
                image['pixels'][(y * width + x) * 4:(y * width + x) * 4 + 4] = bytes(W.gradient_pixel(grad, x + 0.5, y + 0.5) + [255])
        native, masks, probes = ([], [], [])
        for index, x in enumerate((8, width / 2 + 4)):
            bounds = {'x': x, 'y': 20, 'width': width / 2 - 16, 'height': 150}
            tab = 'page-' + str(index)
            native.append({'id': tab, 'webContentsId': index + 31, 'visible': True, 'attached': True, 'bounds': bounds, 'viewBounds': bounds, 'parentBounds': None, 'actualBounds': bounds, 'parentVisible': True, 'panel': {'roundBottom': 12, 'roundGradient': copy.deepcopy(grad)}})
            masks.append({**bounds, 'gradient': copy.deepcopy(grad)})
            for side in ('left', 'right'):
                probes.append({'tabId': tab, 'webContentsId': index + 31, 'side': side, 'point': {'x': x + (1 if side == 'left' else bounds['width'] - 1), 'y': 169}})
        name = 'synthetic-corners-' + stage
        captures[name] = ({'mapping': {'originX': 0, 'originY': 0, 'scaleX': 1, 'scaleY': 1}, 'contentBounds': workspace}, image)
        rows.append({'stage': stage, 'theme': theme, 'shell': {'theme': theme, 'appearance': appearance, 'settingsOpen': False, 'libraryOpen': False, 'gradient': 'linear-gradient(synthetic)', 'workspace': workspace}, 'native': native, 'masks': masks, 'probes': probes, 'capture': name, 'windowBounds': workspace, 'contentBounds': workspace})
    return (rows, appearance, captures)

def absent():
    return {'widgetCount': 0, 'scripts': [], 'styles': [], 'mediaPlayerAPI': 'undefined', 'onMediaPlayerAPI': 'undefined'}

class Workspace641ReaderTests(unittest.TestCase):

    def test_split_choice_gap_drag_carry_and_both_tiny_headers_form_one_required_flow(self):
        value, ledger = layout_fixture()
        W.verify_layout(value, 'linux', 101, ledger)
        mutations = [lambda v: v['empty']['home'].update(search=False), lambda v: v['empty']['home'].update(favorites=False), lambda v: v['chooser']['after']['slots'].update(p3='wrong'), lambda v: v['insertion'].update(afterOrder=['c', 'a', 'b']), lambda v: v['insertion']['affordance'].update(visible=False), lambda v: v['insertion']['affordance'].update(neighbor=''), lambda v: v['blankDrag'].update(afterPane='p1'), lambda v: v['blankDrag']['after'].update(timeOrigin=123), lambda v: v['edgeCarry']['whileHeld'].update(mouseDown=False), lambda v: v['edgeCarry'].update(hoverMs=10), lambda v: v['edgeCarry']['after'].update(webContentsId=99), lambda v: v['headers'].pop(), lambda v: v['headers'][0]['pane']['header']['bounds'].update(height=5), lambda v: v['headers'][0]['pane']['header'].update(opacity=0), lambda v: v['headers'][0]['pane']['header']['bounds'].update(y=200), lambda v: v['headers'][0]['pane']['bounds'].update(width=500)]
        for change in mutations:
            wrong = copy.deepcopy(value)
            change(wrong)
            with self.assertRaises(ValueError):
                W.verify_layout(wrong, 'linux', 101, ledger)

    def test_native_input_requires_exact_process_driver_target_and_trust(self):
        value = receipt()
        W.input_receipt(value, 'linux', 101, [value])
        for field, replacement in [('source', 'script'), ('pid', 123), ('action', 'invoke')]:
            wrong = {**value, field: replacement}
            with self.assertRaises(ValueError):
                W.input_receipt(wrong, 'linux', 101, [wrong])
        wrong = copy.deepcopy(value)
        wrong['events'][0]['trusted'] = False
        with self.assertRaises(ValueError):
            W.input_receipt(wrong, 'linux', 101, [wrong])
        with self.assertRaises(ValueError):
            W.input_receipt(value, 'linux', 101, [])

    def test_intercepted_link_pointerdown_exception_is_narrow_and_url_bound(self):
        value = receipt('#ordinary-link')
        value.update(interceptedLink=True, linkURL='http://127.0.0.1:4100/page/3/')
        value['events'][0]['type'] = 'pointerdown'
        W.input_receipt(value, 'linux', 101)
        for field, replacement in [('selector', '#settings-button'), ('linkURL', 'https://unrelated.example/')]:
            wrong = {**value, field: replacement}
            with self.assertRaises(ValueError):
                W.input_receipt(wrong, 'linux', 101)

    def test_classic_view_preserves_saved_tree_slots_pins_and_desktop(self):
        grid = {'tree': {'id': 'fixture'}, 'slots': {'p1': 'a', 'p2': 'b'}, 'pinnedPanes': {'p2': 'b'}, 'desktopId': 'desk-1'}
        state = {**copy.deepcopy(grid), 'mode': 'classic', 'classicTabId': 'c', 'returnVisible': True, 'panes': [{'id': 'p0', 'view': 'classic'}]}
        W.same_grid(grid, state)
        W.classic(state, 'c')
        for field, replacement in [('slots', {'p1': 'c'}), ('tree', {'id': 'p0'}), ('pinnedPanes', {}), ('desktopId', 'desk-2')]:
            with self.assertRaises(ValueError):
                W.same_grid(grid, {**state, field: replacement})
        with self.assertRaises(ValueError):
            W.classic({**state, 'panes': [{'id': 'p1', 'view': 'grid'}]}, 'c')

    def test_ai_link_requires_exact_native_anchor_and_restores_the_untouched_grid(self):
        url = 'http://127.0.0.1:4100/page/3/'
        grid = {'view': 'grid', 'classicTabId': '', 'tree': {'axis': 'x'}, 'slots': {'p1': 'a', 'p2': 'b'}, 'aiId': 'chat', 'previewId': '', 'returnVisible': False, 'panes': [{'id': 'p1', 'view': 'grid'}, {'id': 'p2', 'view': 'grid'}]}
        click = receipt('#ai-preview-link', 'intercepted-link')
        click.update(tabId='chat', webContentsId=71, evidence='Trusted pointerdown on the exact anchor before isolated click interception')
        click['events'] = [{'type': 'pointerdown', 'trusted': True, 'isTrusted': True, 'matches': True, 'id': 'ai-preview-link', 'href': url, 'button': 0, 'pointerType': 'mouse', 'at': 1001}]
        back = receipt('#return-to-grid')
        value = {'selector': '#ai-preview-link', 'url': url, 'beforeGrid': grid, 'returnedGrid': copy.deepcopy(grid), 'state': {**copy.deepcopy(grid), 'view': 'classic', 'classicTabId': 'new', 'returnVisible': True, 'panes': [{'id': 'p0', 'view': 'classic'}]}, 'tab': {'id': 'new', 'webContentsId': 72, 'lane': 'main', 'previewOf': '', 'url': url}, 'chatBefore': identity('chat'), 'chatAfter': identity('chat'), 'input': click, 'returnInput': back}
        W.verify_ai_link_routes([value], platform='linux', pid=101, inputs=[click, back], selectors=['#ai-preview-link'])
        changes = [lambda v: v['input']['events'][0].update(href='https://other.example/'), lambda v: v['input']['events'][0].update(button=2), lambda v: v['input']['events'][0].update(pointerType='touch'), lambda v: v['input']['events'][0].update(isTrusted=False), lambda v: v['input'].update(webContentsId=999), lambda v: v['input'].update(action=None), lambda v: v['state']['slots'].update(p1='new'), lambda v: v['returnedGrid'].update(view='classic'), lambda v: v['chatAfter'].update(navigationEpoch=3), lambda v: v['tab'].update(lane='side', previewOf='chat')]
        for change in changes:
            wrong = copy.deepcopy(value)
            change(wrong)
            with self.assertRaises(ValueError):
                W.verify_ai_link_routes([wrong], platform='linux', pid=101)

    def test_real_corner_pixels_are_recomputed_for_both_themes_before_and_after_resize(self):
        for theme in ('light', 'dark'):
            rows, appearance, captures = corners_fixture(theme)
            W.verify_corners(rows, theme, appearance, captures)
            for change in [lambda r: r[1]['masks'][0]['gradient'].update(x1=5), lambda r: r[0]['masks'][0]['gradient'].update(start='#000000'), lambda r: r[0]['probes'].pop(), lambda r: r[0]['native'][0].update(attached=False), lambda r: r[0]['shell'].update(settingsOpen=True)]:
                wrong = copy.deepcopy(rows)
                change(wrong)
                with self.assertRaises(ValueError):
                    W.verify_corners(wrong, theme, appearance, captures)
            wrong = copy.deepcopy(captures)
            name = rows[1]['capture']
            wrong[name][1]['pixels'][:] = bytes([0, 0, 0, 255]) * (wrong[name][1]['width'] * wrong[name][1]['height'])
            with self.assertRaisesRegex(ValueError, 'pixel'):
                W.verify_corners(rows, theme, appearance, wrong)

    def test_stationary_audio_absence_requires_two_old_poll_intervals_and_no_widget_or_bridge(self):
        value = {'schema': 1, 'ok': True, 'pollWorld': 1294, 'polls': [], 'audioPlaying': True, 'elapsedMs': 2400, 'startedAt': 1000, 'finishedAt': 3400, 'initial': absent(), 'final': absent()}
        W.verify_stationary_removal(value)
        for change in [lambda v: v.update(polls=[{'world': 1294}]), lambda v: v.update(audioPlaying=False), lambda v: v.update(elapsedMs=100), lambda v: v['initial'].update(widgetCount=1), lambda v: v['final'].update(onMediaPlayerAPI='function'), lambda v: v['final'].update(styles=['media-widget.css'])]:
            wrong = copy.deepcopy(value)
            change(wrong)
            with self.assertRaises(ValueError):
                W.verify_stationary_removal(wrong)
    def test_corners_bind_parent_and_child_coordinates_to_the_actual_window_bounds(self):
        rows, appearance, captures = corners_fixture()
        for row in rows:
            for page in row['native']:
                page['parentBounds'] = copy.deepcopy(page['bounds'])
                page['viewBounds'] = {**page['bounds'], 'x': 0, 'y': 0}
        W.verify_corners(rows, 'light', appearance, captures)
        for change in (lambda p: p['viewBounds'].update(x=1), lambda p: p['parentBounds'].update(y=0),
                       lambda p: p.update(parentVisible=False), lambda p: p.update(actualBounds=p['viewBounds']),
                       lambda p: p['parentBounds'].update(width=5)):
            wrong = copy.deepcopy(rows); change(wrong[0]['native'][0])
            with self.assertRaisesRegex(ValueError, 'actual visible page bounds'):
                W.verify_corners(wrong, 'light', appearance, captures)


if __name__ == '__main__':
    unittest.main()
