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
W = module('mouse642-flexible-workspace-evidence')

def identity(name='a', desk='desk-1'):
    return {'id': name, 'index': 1, 'desk': desk, 'webContentsId': 71, 'url': 'http://127.0.0.1:4100/page/1/', 'navigationEpoch': 2, 'identity': 'owned-token', 'timeOrigin': 17000, 'field': 'owned text', 'scrollX': 0, 'scrollY': 131, 'cookie': 'owned=value', 'ticks': 10}

def receipt(selector='#button', action='click'):
    return {'selector': selector, 'source': 'XTest', 'pid': 101, 'action': action, 'at': 1000, 'point': {'x': 40, 'y': 50}, 'from': {'x': 40, 'y': 50}, 'to': {'x': 120, 'y': 80}, 'released': True, 'events': [{'type': 'pointerdown' if action == 'drag' else 'click', 'trusted': True, 'matches': True}]}

def url_input_fixture():
    selector, value = '#settings-adblock-exception-url', 'https://LOCALHOST:443/owned?path=one'
    click = receipt(selector)
    before = {'exists': True, 'focused': True, 'sameTarget': True,
              'activeElement': {'id': selector[1:], 'tagName': 'INPUT', 'type': 'text'},
              'value': '', 'selectionStart': 0, 'selectionEnd': 0, 'events': copy.deepcopy(click['events'])}
    after = {**copy.deepcopy(before), 'value': value, 'selectionStart': len(value), 'selectionEnd': len(value)}
    after['events'].append({'type': 'input', 'trusted': True, 'matches': True})
    row = {'selector': selector, 'value': value, 'source': 'native focus and webContents.insertText',
           'preparation': 'already-empty', 'stage': 'complete', 'input': click, 'before': before,
           'prepared': copy.deepcopy(before), 'after': after, 'events': copy.deepcopy(after['events'])}
    return row, [click], [row]


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

def windows_layout_fixture():
    """Synthetic child receipts, with the real 641 plan and clock semantics."""
    value, ledger = layout_fixture()
    for row in ledger: row['source'] = 'User32'
    for action, kind in (('blankDrag', 'blank'), ('edgeCarry', 'edge')):
        row = value[action]['input']; row['tabId'] = value[action]['before']['id']
        start, finish = row['from'], row['to']; threshold = {'x': start['x'] + 12, 'y': start['y'] + 7}
        target = {'x': 900, 'y': 80} if kind == 'edge' else finish
        logical = [start.copy(), threshold]
        for a, b, count in [(threshold, target, 12)] + ([(target, finish, 1)] if kind == 'edge' else []):
            logical += [{axis: math.floor(a[axis] + (b[axis] - a[axis]) * step / count + .5)
                         for axis in ('x', 'y')} for step in range(1, count + 1)]
        logical.append(finish.copy())
        samples = [{'logical': point, 'physical': {axis: point[axis] * 2 for axis in ('x', 'y')}} for point in logical]
        start_at = 200000 if kind == 'edge' else 100000; hold, settle = (800, 5000) if kind == 'edge' else (400, 200)
        elapsed = 0; events, event_ns = [], []
        for index, sample in enumerate(samples):
            phase = 0 if index == 0 else 2 if index == len(samples) - 1 else 1
            if phase == 2: elapsed += settle
            events.append({**sample['physical'], 'phase': phase, 'at': start_at + elapsed, 'accepted': True})
            event_ns.append(str(elapsed * 1000000))
            if index == 13:
                hold_start = elapsed; elapsed += hold; hold_end = elapsed
            elif phase != 2: elapsed += 60 if index == 0 else 100 if index == 1 else 22
        row['nativeDrag'] = {'schema': 1, 'method': 'independent-native-html-input-process', 'platform': 'win32', 'source': 'User32',
            'parentPid': 101, 'childPid': 203 if kind == 'edge' else 202,
            'nonce': '12345678-1234-1234-1234-12345678900' + ('2' if kind == 'edge' else '1'), 'kind': kind,
            'budgetMs': 15000, 'driverCallLimitMs': 7000, 'holdMs': hold, 'settleMs': settle,
            'deadlineAt': start_at - 3 + 15000, 'startedAt': start_at, 'completedAt': start_at + elapsed,
            'elapsedMs': elapsed, 'forkedAt': start_at - 2, 'exitAt': start_at + elapsed + 2,
            'exitCode': 0, 'exitSignal': None, 'lifecycleLimitMs': 30000, 'terminationRequested': False,
            'coordinates': {'source': 'Electron screen.dipToScreenPoint', 'samples': samples},
            'events': events, 'released': True, 'ok': True,
            'timing': {'source': 'process.hrtime.bigint', 'scope': 'per-process elapsed',
                'child': {'eventNs': event_ns, 'holdStartNs': str(hold_start * 1000000),
                          'holdEndNs': str(hold_end * 1000000), 'elapsedNs': str(elapsed * 1000000)},
                'parent': {'preparationNs': '1000000', 'elapsedNs': str((elapsed + 4) * 1000000)}}}
        if kind == 'edge':
            value[action]['direction'] = 1
            value[action]['whileHeld'].update(active=True, sourceMembership='desk-1', sourceMembershipAfterCapture='desk-1',
                originDesk='desk-1', sourceTabId='a', observerPid=101, observedAt=start_at + 1300,
                captureFinishedAt=start_at + 1800, mouseDownAfterCapture=True,
                observedElapsedNs='1303000000', captureElapsedNs='1803000000',
                edgeObservation={'schema': 1, 'clock': 'renderer performance.now', 'edgeId': 'mouse-drag-edge-right',
                    'destination': 'desk-2', 'originDesktop': 'desk-1', 'armedAtMs': 100, 'hoverAtMs': 500,
                    'switchedAtMs': 1150, 'elapsedMs': 650, 'ok': True})
    return value, ledger


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
    def test_empty_url_insertion_and_legacy_input_receipts_remain_distinct_valid_routes(self):
        row, inputs, texts = url_input_fixture()
        W.verify_settings_url_input(row, 'linux', 101, inputs, texts)
        legacy = {'value': row['value'], 'source': 'native focus, webContents.sendInputEvent and insertText',
                  'input': row['input'], 'events': [{'type': 'input', 'trusted': True}]}
        W.verify_settings_url_input(legacy, 'linux', 101, inputs)
        row['source'] = legacy['source']
        with self.assertRaisesRegex(ValueError, 'legacy key route'):
            W.verify_settings_url_input(row, 'linux', 101, inputs, texts)

    def test_empty_url_insertion_requires_stored_before_prepared_and_after_snapshots(self):
        for key in ('before', 'prepared', 'after'):
            row, inputs, texts = url_input_fixture(); row.pop(key)
            with self.assertRaisesRegex(ValueError, 'snapshot'):
                W.verify_settings_url_input(row, 'linux', 101, inputs, texts)
        for field, replacement in [('stage', 'select-all'), ('preparation', 'assumed-empty'),
                                   ('selector', '#another-field'), ('value', 'https://other.example/'), ('error', {'message': 'failed'})]:
            row, inputs, texts = url_input_fixture(); row[field] = replacement
            with self.assertRaises(ValueError): W.verify_settings_url_input(row, 'linux', 101, inputs, texts)
        row, inputs, texts = url_input_fixture()
        with self.assertRaisesRegex(ValueError, 'stored text ledger'):
            W.verify_settings_url_input(row, 'linux', 101, inputs, [])
        changed = copy.deepcopy(texts); changed[0]['prepared']['focused'] = False
        with self.assertRaisesRegex(ValueError, 'stored text ledger'):
            W.verify_settings_url_input(row, 'linux', 101, inputs, changed)

    def test_empty_url_insertion_cannot_clear_a_nonempty_field_or_switch_its_target(self):
        for key in ('before', 'prepared', 'after'):
            changes = [('exists', False), ('focused', False), ('sameTarget', False),
                       ('activeElement', {'id': 'another', 'tagName': 'INPUT', 'type': 'text'}),
                       ('activeElement', {'id': 'settings-adblock-exception-url', 'tagName': 'INPUT', 'type': 'password'}),
                       ('value', 'unexpected value')]
            if key != 'after': changes += [('selectionStart', 1), ('selectionEnd', None), ('selectionStart', False)]
            for field, replacement in changes:
                row, inputs, texts = url_input_fixture(); row[key][field] = replacement
                with self.subTest(snapshot=key, field=field, replacement=replacement):
                    with self.assertRaises(ValueError): W.verify_settings_url_input(row, 'linux', 101, inputs, texts)

    def test_empty_url_insertion_requires_native_click_and_new_trusted_input_on_the_same_target(self):
        row, inputs, texts = url_input_fixture()
        with self.assertRaisesRegex(ValueError, 'native process ledger'):
            W.verify_settings_url_input(row, 'linux', 101, [], texts)
        for field, replacement in [('source', 'script'), ('pid', 999), ('selector', '#another-field')]:
            row, inputs, texts = url_input_fixture(); row['input'][field] = replacement
            with self.assertRaises(ValueError): W.verify_settings_url_input(row, 'linux', 101, inputs, texts)
        for field in ('trusted', 'matches'):
            row, inputs, texts = url_input_fixture(); row['after']['events'][-1][field] = False
            row['events'] = copy.deepcopy(row['after']['events'])
            with self.assertRaises(ValueError): W.verify_settings_url_input(row, 'linux', 101, inputs, texts)
        row, inputs, texts = url_input_fixture(); row['prepared']['events'] = copy.deepcopy(row['after']['events'])
        with self.assertRaisesRegex(ValueError, 'new trusted input'):
            W.verify_settings_url_input(row, 'linux', 101, inputs, texts)
        row, inputs, texts = url_input_fixture(); row['before']['events'][0]['trusted'] = False
        with self.assertRaisesRegex(ValueError, 'event history'):
            W.verify_settings_url_input(row, 'linux', 101, inputs, texts)

    def test_windows_html_drags_bind_separate_child_input_path_clocks_and_held_ownership(self):
        value, ledger = windows_layout_fixture()
        W.verify_layout(value, 'win32', 101, ledger)
        self.assertEqual([len(value[kind]['input']['nativeDrag']['events']) for kind in ('blankDrag', 'edgeCarry')], [15, 16])
        for kind in ('blankDrag', 'edgeCarry'):
            row = value[kind]['input']; child = row['nativeDrag']
            self.assertEqual(child['coordinates']['samples'][0]['logical'], row['from'])
            self.assertEqual(child['coordinates']['samples'][-1]['logical'], row['to'])
            self.assertEqual(child['events'][-1]['phase'], 2)

    def test_windows_html_drag_rejects_changed_child_receipts_even_in_the_same_ledger(self):
        value, ledger = windows_layout_fixture()
        mutations = [(['nativeDrag'], None), (['nativeDrag', 'schema'], 2), (['nativeDrag', 'method'], 'parent-script'),
            (['nativeDrag', 'platform'], 'linux'), (['nativeDrag', 'source'], 'XTest'), (['nativeDrag', 'parentPid'], 999),
            (['nativeDrag', 'childPid'], 101), (['nativeDrag', 'childPid'], 0), (['nativeDrag', 'nonce'], 'missing'),
            (['nativeDrag', 'kind'], 'other'), (['nativeDrag', 'ok'], False), (['nativeDrag', 'released'], False),
            (['nativeDrag', 'exitCode'], 1), (['nativeDrag', 'exitSignal'], 'SIGTERM'),
            (['nativeDrag', 'terminationRequested'], True), (['nativeDrag', 'failureCleanup'], {'accepted': True}),
            (['nativeDrag', 'error'], 'deadline'), (['nativeDrag', 'releaseError'], 'UP failed'),
            (['nativeDrag', 'budgetMs'], 15001), (['nativeDrag', 'budgetMs'], 0),
            (['nativeDrag', 'driverCallLimitMs'], 14000), (['nativeDrag', 'lifecycleLimitMs'], 60000),
            (['nativeDrag', 'holdMs'], 1), (['nativeDrag', 'settleMs'], 0), (['nativeDrag', 'elapsedMs'], -1),
            (['nativeDrag', 'coordinates', 'source'], 'script coordinates'), (['nativeDrag', 'coordinates', 'samples'], []),
            (['nativeDrag', 'events'], []), (['nativeDrag', 'events', 0, 'phase'], 1),
            (['nativeDrag', 'events', 3, 'phase'], 2), (['nativeDrag', 'events', -1, 'phase'], 1),
            (['nativeDrag', 'events', 1, 'accepted'], False), (['nativeDrag', 'events', 2, 'x'], 999),
            (['nativeDrag', 'coordinates', 'samples', 1, 'logical', 'x'], 999),
            (['nativeDrag', 'coordinates', 'samples', 2, 'logical', 'y'], 999), (['from', 'x'], 999), (['to', 'x'], 999),
            (['nativeDrag', 'timing', 'source'], 'Date.now'), (['nativeDrag', 'timing', 'scope'], 'shared wall clock'),
            (['nativeDrag', 'timing', 'child', 'eventNs'], []), (['nativeDrag', 'timing', 'child', 'eventNs', 0], '15000000001'),
            (['nativeDrag', 'timing', 'child', 'eventNs', 2], '0'),
            (['nativeDrag', 'timing', 'child', 'elapsedNs'], '15000000001'),
            (['nativeDrag', 'timing', 'child', 'holdStartNs'], '0'),
            (['nativeDrag', 'timing', 'child', 'holdEndNs'], '402000000'),
            (['nativeDrag', 'timing', 'parent', 'preparationNs'], '15000000000'),
            (['nativeDrag', 'timing', 'parent', 'elapsedNs'], '15000000001'),
            (['nativeDrag', 'timing', 'parent', 'elapsedNs'], '-1'), (['observationError'], 'late callback'), (['tabId'], 'other')]
        for kind in ('blankDrag', 'edgeCarry'):
            for path, replacement in mutations:
                with self.subTest(kind=kind, path=path, replacement=replacement):
                    wrong, same_ledger = copy.deepcopy((value, ledger)); target = wrong[kind]['input']
                    for key in path[:-1]: target = target[key]
                    target[path[-1]] = replacement
                    self.assertIn(wrong[kind]['input'], same_ledger)
                    with self.assertRaisesRegex(ValueError, 'Windows'):
                        W.verify_layout(wrong, 'win32', 101, same_ledger)
            wrong, same_ledger = copy.deepcopy((value, ledger)); timing = wrong[kind]['input']['nativeDrag']['timing']['child']
            settle = wrong[kind]['input']['nativeDrag']['settleMs']
            timing['eventNs'][-1] = str(max(int(timing['eventNs'][-2]), int(timing['holdEndNs'])) + settle * 1000000 - 1)
            with self.assertRaisesRegex(ValueError, 'Windows'):
                W.verify_layout(wrong, 'win32', 101, same_ledger)

    def test_windows_held_proof_rejects_late_native_samples_or_changed_source_ownership(self):
        value, ledger = windows_layout_fixture(); child = value['edgeCarry']['input']['nativeDrag']
        mutations = [('observerPid', 202), ('active', False), ('sourceTabId', 'other'), ('originDesk', 'desk-2'),
            ('sourceMembership', 'desk-2'), ('sourceMembershipAfterCapture', 'desk-2'),
            ('mouseDownAfterCapture', False), ('observedAt', child['events'][0]['at'] - 1),
            ('observedAt', child['events'][-1]['at'] + 1), ('captureFinishedAt', child['events'][-1]['at'] + 1),
            ('captureFinishedAt', child['events'][0]['at']), ('observedElapsedNs', '15000000001'),
            ('captureElapsedNs', '0'), ('captureElapsedNs', '15000000001'), ('observedElapsedNs', 'invalid')]
        for key, replacement in mutations:
            with self.subTest(key=key, replacement=replacement):
                wrong, same_ledger = copy.deepcopy((value, ledger)); wrong['edgeCarry']['whileHeld'][key] = replacement
                with self.assertRaisesRegex(ValueError, 'Windows'):
                    W.verify_layout(wrong, 'win32', 101, same_ledger)

    def test_windows_edge_dwell_requires_its_own_renderer_observation(self):
        value, ledger = windows_layout_fixture()
        mutations = [('schema', 2), ('clock', 'child wait'), ('ok', False), ('error', 'timed out'),
            ('edgeId', 'mouse-drag-edge-left'), ('originDesktop', 'desk-2'), ('destination', 'desk-1'),
            ('armedAtMs', 600), ('hoverAtMs', None), ('switchedAtMs', 499), ('elapsedMs', 649)]
        for key, replacement in mutations:
            with self.subTest(key=key, replacement=replacement):
                wrong, same_ledger = copy.deepcopy((value, ledger)); wrong['edgeCarry']['whileHeld']['edgeObservation'][key] = replacement
                with self.assertRaisesRegex(ValueError, 'Windows'):
                    W.verify_layout(wrong, 'win32', 101, same_ledger)
        wrong, same_ledger = copy.deepcopy((value, ledger)); wrong['edgeCarry']['whileHeld']['edgeObservation'] = None
        with self.assertRaisesRegex(ValueError, 'Windows'):
            W.verify_layout(wrong, 'win32', 101, same_ledger)


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

    def test_intercepted_link_pointerdown_exception_is_narrow_and_url_bound(self):
        value = receipt('#ordinary-link'); value.update(interceptedLink=True, linkURL='http://localhost:4100/page/3/')
        value['events'][0]['type'] = 'pointerdown'; W.input_receipt(value, 'linux', 101)
        for field, replacement in [('selector', '#settings-button'), ('linkURL', 'https://unrelated.example/')]:
            wrong = {**value, field: replacement}
            with self.assertRaises(ValueError): W.input_receipt(wrong, 'linux', 101)

    def test_classic_corner_minus_and_return_button_require_native_input_and_preserved_pages(self):
        grid = {'tree': {'axis': 'x', 'first': 'p1', 'second': 'p2'}, 'slots': {'p1': 'a', 'p2': 'b'},
                'pinnedPanes': {'p2': 'b'}, 'desktopId': 'desk-1', 'mode': 'grid', 'classicTabId': ''}
        initial = [identity('a'), {**identity('b'), 'webContentsId': 72}]
        for kind in ['link', 'blank-link', 'window-open', 'new-tab', 'top-tab']:
            selector = '[data-window="minimize"]' if kind == 'link' else '#return-to-grid'
            click, back = receipt('#ordinary-link'), receipt(selector)
            row = {'kind': kind, 'before': grid, 'active': 'c',
                   'state': {**copy.deepcopy(grid), 'mode': 'classic', 'classicTabId': 'c', 'returnVisible': True,
                             'panes': [{'id': 'p0', 'view': 'classic'}]},
                   'returned': copy.deepcopy(grid), 'returnedWindow': {'visible': True, 'minimized': False},
                   'input': click, 'returnInput': back, 'identities': copy.deepcopy(initial)}
            ledger = [click, back]
            W.verify_classic_return(row, initial, 'linux', 101, ledger)
            mutations = [lambda v: v['returnInput'].update(selector='#return-to-grid' if kind == 'link' else '[data-window="minimize"]'),
                         lambda v: v['returnInput'].update(source='script'), lambda v: v['returnInput'].update(pid=999),
                         lambda v: v['returnInput']['events'][0].update(trusted=False),
                         lambda v: v['returned'].update(mode='classic'), lambda v: v['returned'].update(classicTabId='c'),
                         lambda v: v['returned']['slots'].update(p1='c'), lambda v: v['returned'].update(pinnedPanes={}),
                         lambda v: v['returned'].update(desktopId='desk-2'), lambda v: v['returned'].update(tree={'id': 'p0'}),
                         lambda v: v['returnedWindow'].update(visible=False), lambda v: v['returnedWindow'].update(minimized=True),
                         lambda v: v['identities'][0].update(webContentsId=999), lambda v: v['identities'][0].update(timeOrigin=999),
                         lambda v: v['identities'].pop()]
            for index, change in enumerate(mutations):
                with self.subTest(kind=kind, mutation=index):
                    wrong, same_ledger = copy.deepcopy((row, ledger)); change(wrong)
                    with self.assertRaises(ValueError): W.verify_classic_return(wrong, initial, 'linux', 101, same_ledger)
            with self.assertRaises(ValueError): W.verify_classic_return(row, initial, 'linux', 101, [click])

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
