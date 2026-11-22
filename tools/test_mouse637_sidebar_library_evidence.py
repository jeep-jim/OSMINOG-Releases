#!/usr/bin/env python3
"""Synthetic contract mutations; the published gate still requires native bytes."""
import base64
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import runpy
import struct
import unittest
import zlib

ROOT = Path(__file__).parent
F = runpy.run_path(str(ROOT / 'mouse637-features-evidence.py'))
L = runpy.run_path(str(ROOT / 'mouse637-library-actions-evidence.py'))
S = runpy.run_path(str(ROOT / 'mouse637-sidebar-focus-evidence.py'))
H = runpy.run_path(str(ROOT / 'test_mouse637_ai_preview_evidence.py'))
ORIGIN, SIDEBAR = 'http://127.0.0.1:12002', 'http://127.0.0.1:12003'


def png(color, width=160, height=96):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress((b'\0' + bytes(color + [255]) * width) * height)) + chunk(b'IEND', b''))


def owner(index, ticks=1):
    return H['identity'](index, 'main-' + str(index), ORIGIN, ticks)


def native(own, x=20, y=80):
    return H['native'](own, {'x': x, 'y': y, 'width': 400, 'height': 600})


def click(selector, tab_id=None):
    return H['click'](selector, tab_id)


def gesture_fixture(event, file, index=0, platform='linux'):
    start, end = event['from'], event['to']
    points = [copy.deepcopy(start), {'x': start['x'] - 14, 'y': start['y'] + 8}]
    points += [{key: L['N']['jsround'](start[key] + (end[key] - start[key]) * step / 10) for key in ('x', 'y')}
               for step in range(1, 11)]
    points.append(copy.deepcopy(end))
    # Synthetic contract fixture: exercise non-identity Windows conversion,
    # without presenting these generated coordinates as native evidence.
    physical = [{key: point[key] * 2 + 20 for key in ('x', 'y')} if platform == 'win32' else copy.deepcopy(point) for point in points]
    nonce = '10000000-0000-4000-8000-' + str(index + 1).zfill(12)
    return {'schema': 1, 'method': 'independent-native-input-process', 'platform': platform, 'source': L['N']['source'](platform),
            'parentPid': 11, 'childPid': 100 + index, 'nonce': nonce, 'budgetMs': 10000,
            'driverCallLimitMs': None if platform == 'darwin' else 7000, 'lifecycleLimitMs': 53000, 'terminationRequested': False,
            'forkedAt': 900, 'startedAt': 1000, 'completedAt': 2500, 'exitAt': 2600, 'deadlineAt': 10900,
            'elapsedMs': 1500, 'exitCode': 0, 'released': True, 'ok': True,
            'coordinates': {'source': 'Electron screen.dipToScreenPoint' if platform == 'win32' else 'native screen coordinates',
                            'samples': [{'logical': point, 'physical': target} for point, target in zip(points, physical)]},
            'events': [{**point, 'phase': 0 if i == 0 else 2 if i == 12 else 1, 'at': 1100 + i * 100, 'accepted': True} for i, point in enumerate(physical)],
            'handshake': {'schema': 1, 'nonce': nonce, 'parentPid': 11, 'childPid': 100 + index, 'at': 1200, 'observedAt': 1250,
                          'nativeFile': {'name': file['dragName'], 'size': file['size'], 'sha256': file['sha256'], 'hasIcon': True, 'keys': ['file', 'icon']}}}


class FakeFrames:
    """Frame decoding is covered by the immutable primitive tests, not mocked as CI."""
    def __init__(self, raw):
        self.raw = raw
        self.menu_changed = True

    def read(self, name):
        return self.raw[name]

    def screen(self, row):
        value = 255 if row['filename'] == 'mouse-637-library-context.png' and self.menu_changed else 0
        return {'width': 50, 'height': 30, 'channels': 4, 'pixels': bytes([value, value, value, 255]) * 1500}


def library_fixture():
    owners = [owner(index, 100) for index in range(2)]
    before = [owner(index) for index in range(2)]
    inputs, raw, captures, files = [], {}, {}, []
    for i, (key, kind, mime, title, artifact, color) in enumerate(L['SPECS']):
        ident = '00000000-0000-4000-8000-' + str(i + 1).zfill(12)
        if kind == 'downloads':
            ident = 'mouse637-' + ident
        suffix = '.txt' if mime == 'text/plain' else '.png'
        data = png(color) if color else L['TEXT'].encode()
        file = {'key': key, 'kind': kind, 'id': ident, 'type': mime, 'title': title, 'artifact': artifact,
                'filename': ident + suffix if kind == 'captures' else title, 'at': 1700000000000,
                'dragName': title + suffix if kind == 'captures' else title,
                'size': len(data), 'sha256': L['sha'](data), 'archiveType': 'text' if mime == 'text/plain' else 'image'}
        if color:
            file['rgb'] = color
        files.append(file); raw[artifact] = data

    def state(kind='captures', view='grid', theme='dark'):
        rows = []
        for index, file in enumerate(file for file in files if file['kind'] == kind):
            y = 210 + index * 150
            row = {'id': file['id'], 'tag': 'BUTTON', 'title': file['title'], 'aria': file['title'], 'draggable': True, 'controls': 0,
                   'content': L['TEXT'] if file['type'] == 'text/plain' else 'PNG' if kind == 'downloads' else '',
                   'open': {'x': 900, 'y': y, 'width': 160, 'height': 96},
                   'checkbox': {'bounds': {'x': 1070, 'y': y, 'width': 16, 'height': 16}, 'checked': kind == 'captures' and file['type'] == 'image/png'}}
            if file['type'] == 'image/png':
                row['image'] = {'bounds': copy.deepcopy(row['open']), 'loaded': True, 'width': 160, 'height': 96,
                                'src': 'data:image/png;base64,' + base64.b64encode(raw[file['artifact']]).decode()}
            rows.append(row)
        return {'open': True, 'kind': kind, 'view': view, 'theme': theme, 'query': L['QUERY'], 'rows': rows}

    report = {'schema': 1, 'source': 'Owned local files, native context menu and OS file drops into live panes', 'query': L['QUERY'],
              'ok': True, 'files': files, 'pages': {'before': before, 'after': [owner(i, 50) for i in range(2)], 'identityPreserved': True},
              'samples': [], 'menus': [], 'transfers': [], 'restored': {'archiveEntries': True, 'downloads': True, 'collectorUnchanged': True}}
    pair = [native(before[0]), native(before[1], 430)]
    for theme, view in [('light', 'list'), ('light', 'grid'), ('dark', 'list'), ('dark', 'grid')]:
        name = 'mouse-637-library-captures-' + view + '-' + theme + '.png'
        captures[name] = {'filename': name}
        report['samples'].append({'theme': theme, 'view': view, 'state': state(view=view, theme=theme), 'native': copy.deepcopy(pair), 'capture': name})
    content = {'x': 10, 'y': 20, 'width': 1200, 'height': 800}
    for file in (files[0], files[2]):
        target = '.library-row[data-id=' + json.dumps(file['id']) + '] .library-file-open'
        event = {'selector': target, 'action': 'context-menu', 'pid': 11, 'source': 'XTest', 'point': {'x': 990, 'y': 278}, 'at': 100,
                 'events': [{'type': 'contextmenu', 'trusted': True, 'matches': True}]}
        inputs.append(event)
        typ = 'PNG · Image' if file['kind'] == 'captures' else 'PNG'
        labels = [file['title'], 'Type: ' + typ, 'Created: Nov 14, 2023, 22:13:20']
        actions = ['preview', 'copy', 'remove'] if file['kind'] == 'captures' else ['open', 'show', 'remove']
        items = [{'id': 'mouse-library-info-' + str(i), 'label': label, 'type': 'normal', 'enabled': False, 'visible': True} for i, label in enumerate(labels)]
        items.append({'id': '', 'label': '', 'type': 'separator', 'enabled': True, 'visible': True})
        items.extend({'id': 'mouse-library-' + action, 'label': action, 'type': 'normal', 'enabled': True, 'visible': True} for action in actions)
        menu = {'id': file['id'], 'kind': file['kind'], 'locale': 'en', 'shownAt': 100, 'closedAt': 200, 'input': event, 'state': state(kind=file['kind']), 'contentBounds': content,
                'items': items, 'popup': {'windowId': 1, 'x': 980, 'y': 258}, 'keys': [{'key': key, 'source': 'XTest', 'at': 150} for key in (['HOME', 'ENTER'] if file['kind'] == 'captures' else ['ESC'])],
                'metadata': {'name': file['title'], 'type': typ, 'createdAt': '2023-11-14T22:13:20.000Z', 'labels': labels}, 'previewSelected': file['kind'] == 'captures'}
        if file['kind'] == 'captures':
            name = 'mouse-637-library-context.png'; captures[name] = {'filename': name}
            menu.update(capture=name, native=copy.deepcopy(pair), preview={'title': file['title'], 'src': state()['rows'][0]['image']['src']})
        report['menus'].append(menu)
    event = click('.library-row[data-id=' + json.dumps(files[1]['id']) + '] .library-file-open'); inputs.append(event)
    report['textPreview'] = {'input': event, 'state': {'title': files[1]['title'], 'text': L['TEXT'], 'nested': 0}}
    report['downloadState'] = state('downloads')
    for file, index in [(files[0], 0), (files[1], 1), (files[2], 0)]:
        source_state = state(file['kind'], 'list')
        opened = next(row for row in source_state['rows'] if row['id'] == file['id'])['open']
        event = {'selector': '.library-row[data-id=' + json.dumps(file['id']) + '] .library-file-open', 'action': 'file-drag', 'pid': 11, 'source': 'XTest',
                 'from': {'x': content['x'] + opened['x'] + 80, 'y': content['y'] + opened['y'] + 48},
                 'to': {'x': content['x'] + pair[index]['bounds']['x'] + 98, 'y': content['y'] + pair[index]['bounds']['y'] + 198},
                 'events': [{'type': typ, 'trusted': True, 'matches': True} for typ in ('pointerdown', 'dragstart')]}
        inputs.append(event)
        report['transfers'].append({'fileKey': file['key'], 'targetTabId': before[index]['id'], 'pane': 'p' + str(index + 1),
                                   'before': owner(index, 5), 'after': owner(index, 6), 'nativeBefore': copy.deepcopy(pair[index]), 'nativeAfter': copy.deepcopy(pair[index]),
                                   'input': event, 'gesture': gesture_fixture(event, file, files.index(file)), 'sourceState': source_state, 'contentBounds': content,
                                   'received': {'trusted': True, 'types': ['Files'], 'files': [{'name': file['dragName'], 'type': file['type'], 'size': file['size'], 'bytes': list(raw[file['artifact']])}]},
                                   'over': [{'trusted': True, 'at': 100}], 'nativeFile': {'name': file['dragName'], 'size': file['size'], 'sha256': file['sha256'], 'hasIcon': True, 'keys': ['file', 'icon']},
                                   'clipboardBefore': 'a' * 64, 'clipboardAfter': 'a' * 64, 'libraryStillOpen': True})
    return report, owners, inputs, FakeFrames(raw), captures


def verify_library(fixture):
    report, owners, inputs, evidence, captures = fixture
    return L['verify'](report, owners, evidence=evidence, pid=11, platform='linux', inputs=inputs, input_check=F['input_event'], origin=ORIGIN, captures=captures)


class LibraryAcceptance(unittest.TestCase):
    def test_actual_file_bytes_and_full_menu_content_contract_accept(self):
        result = verify_library(library_fixture())
        self.assertEqual(len(result['witnesses']), 5)
        self.assertEqual(len(result['inputs']), 3)
        self.assertTrue(result['summary']['nativeFilesToBothPanes'])

    def test_independent_native_file_gesture_preserves_platform_coordinate_conversion(self):
        report, *_rest = library_fixture()
        event, file = report['transfers'][0]['input'], report['files'][0]
        for platform in ('darwin', 'linux', 'win32'):
            receipt = gesture_fixture(event, file, platform=platform)
            with self.subTest(platform=platform):
                self.assertEqual(L['native_gesture'](receipt, event, file, 11, platform), receipt['nonce'])

    def test_native_file_gesture_requires_actual_child_and_owned_nonce_handshake(self):
        mutations = [lambda g: g.update(childPid=11), lambda g: g.update(parentPid=12),
                     lambda g: g.update(exitCode=1), lambda g: g.update(released=False),
                     lambda g: g.update(budgetMs=10001), lambda g: g.update(deadlineAt=2499),
                     lambda g: g.update(terminationRequested=True), lambda g: g.update(lifecycleLimitMs=54000),
                     lambda g: g['handshake'].update(childPid=9), lambda g: g['handshake'].update(nonce='a' * 36),
                     lambda g: g['handshake']['nativeFile'].update(sha256='a' * 64),
                     lambda g: g['handshake'].update(observedAt=2400)]
        for mutate in mutations:
            fixture = library_fixture(); mutate(fixture[0]['transfers'][0]['gesture'])
            with self.assertRaises(ValueError): verify_library(fixture)
        fixture = library_fixture(); del fixture[0]['transfers'][0]['gesture']
        with self.assertRaises(ValueError): verify_library(fixture)
        fixture = library_fixture(); first, second = fixture[0]['transfers'][:2]
        second['gesture']['nonce'] = second['gesture']['handshake']['nonce'] = first['gesture']['nonce']
        with self.assertRaises(ValueError): verify_library(fixture)

    def test_native_file_gesture_requires_complete_ordered_pointer_trace(self):
        for mutate in [lambda g: g['events'].pop(), lambda g: g['events'][12].update(phase=1),
                       lambda g: g['events'][2].update(accepted=False), lambda g: g['events'][2].update(at=1000),
                       lambda g: g['events'][2].update(x=0), lambda g: g['coordinates']['samples'][2]['logical'].update(x=0),
                       lambda g: g['coordinates']['samples'][2]['physical'].update(x=0)]:
            fixture = library_fixture(); mutate(fixture[0]['transfers'][0]['gesture'])
            with self.assertRaises(ValueError): verify_library(fixture)

    def test_native_file_data_mime_names_clipboard_and_target_forgery_rejected(self):
        for mutate in [lambda r: r['transfers'][0]['received'].update(trusted=False),
                       lambda r: r['transfers'][0]['received'].update(types=['text/plain']),
                       lambda r: r['transfers'][0]['received']['files'][0]['bytes'].__setitem__(0, 0),
                       lambda r: r['transfers'][1]['received']['files'][0].update(type='image/png'),
                       lambda r: r['transfers'][0]['nativeFile'].update(keys=['text']),
                       lambda r: r['transfers'][0].update(clipboardAfter='b' * 64),
                       lambda r: r['transfers'][1]['input']['to'].update(x=0),
                       lambda r: r['transfers'][2]['nativeAfter'].update(attached=False)]:
            fixture = library_fixture(); mutate(fixture[0])
            with self.assertRaises(ValueError):
                verify_library(fixture)

    def test_clutter_inaccessible_controls_and_wrong_thumbnail_bytes_rejected(self):
        for mutate in [lambda r: r['samples'][0]['state']['rows'][0].update(controls=2),
                       lambda r: r['samples'][0]['state']['rows'][0].update(aria=''),
                       lambda r: r['samples'][0]['state']['rows'][0].update(content='Screenshot'),
                       lambda r: r['samples'][0]['state']['rows'][0]['checkbox'].update(checked=False),
                       lambda r: r['samples'][0]['state']['rows'][0]['image'].update(src='data:image/png;base64,' + base64.b64encode(png([1, 2, 3])).decode())]:
            fixture = library_fixture(); mutate(fixture[0])
            with self.assertRaises(ValueError):
                verify_library(fixture)

    def test_native_menu_metadata_actions_and_pixel_evidence_are_mandatory(self):
        for mutate in [lambda r: r['menus'][0]['metadata'].update(createdAt='2026-01-01T00:00:00.000Z'),
                       lambda r: r['menus'][0]['items'][5].update(enabled=False),
                       lambda r: r['menus'][0]['input']['events'][0].update(trusted=False),
                       lambda r: r['menus'][0].update(keys=[]),
                       lambda r: r['menus'][0]['popup'].update(x=0)]:
            fixture = library_fixture(); mutate(fixture[0])
            with self.assertRaises(ValueError):
                verify_library(fixture)
        fixture = library_fixture(); fixture[3].menu_changed = False
        with self.assertRaises(ValueError):
            verify_library(fixture)


def sidebar_fixture():
    owners = [owner(i, 100) for i in range(2)]
    primary = H['identity'](5, 'strict-csp', SIDEBAR, 1)
    pair = [primary, owner(1)]
    report = {'schema': 1, 'ok': True, 'opacity': .14, 'source': S['SOURCE'], 'origin': SIDEBAR, 'csp': "style-src 'self'",
              'owners': {'primary': primary['id'], 'adjacent': pair[1]['id'], 'start': 'real-start'}, 'samples': []}
    inputs, total_clicks = [], []
    author = {'filter': 'contrast(1)', 'transform': 'matrix(1, 0, 0, 1, 0, 0)', 'before': '"owned decoration"'}

    def block(theme, kind=None):
        enabled = kind is not None
        pages = [native(pair[0]), native(pair[1], 430)]
        for page in pages:
            page['dim'] = {'requested': enabled, 'applied': enabled, 'pending': False, 'error': ''}
        shell = {'theme': theme, 'dimmed': enabled, 'settingsOpen': kind == 'settings', 'libraryOpen': kind == 'library',
                 'mask': {'content': '""' if enabled else 'none', 'pointerEvents': 'none', 'backgroundColor': 'rgba(0, 0, 0, 0.14)'},
                 'start': {'id': 'real-start', 'internal': True, 'visible': True, 'slotBounds': {'x': 500, 'y': 400, 'width': 350, 'height': 270}},
                 'witness': {'point': {'x': 560, 'y': 590}, 'color': 'rgb(37, 143, 191)'}}
        for field in ['toolbar', 'settings', 'library']:
            shell[field] = {'backgroundColor': 'rgb(15, 20, 28)', 'backgroundImage': 'none'}
        guest = {'buttonReceivesPoint': True, 'author': copy.deepcopy(author), 'witness': {'point': {'x': 60, 'y': 190}, 'color': 'rgb(37, 143, 191)'},
                 'viewport': {'width': 400, 'height': 600}, 'clicks': copy.deepcopy(total_clicks), 'mask': None}
        if enabled:
            guest['mask'] = {'count': 1, 'ariaHidden': 'true', 'inert': True, 'closedShadow': True, 'pointerEvents': 'none', 'backdropPointerEvents': 'none',
                             'popoverOpen': True, 'bounds': {'x': 0, 'y': 0, 'width': 400, 'height': 600}}
        return {'readback': shell, 'guest': guest, 'native': pages}

    for i, theme in enumerate(['light', 'dark']):
        initial = [{**pair[0], 'ticks': i * 10 + 1}, {**pair[1], 'ticks': i * 10 + 1}]
        sample = {'theme': theme, 'before': {**block(theme), 'identities': initial}, 'captures': {}}
        for kind in ['settings', 'library']:
            total_clicks.append({'trusted': True, 'at': len(total_clicks) + 1})
            value = block(theme, kind)
            for key, selector, tab_id in [('openInput', '#settings-button' if kind == 'settings' else '#history-button', None),
                                         ('clickInput', '#dim-click', primary['id']),
                                         ('closeInput', '#settings-dialog [data-close-dialog]' if kind == 'settings' else '#library-close', None)]:
                value[key] = click(selector, tab_id); inputs.append(value[key])
            value['clicks'] = copy.deepcopy(total_clicks); sample[kind] = value
        sample['after'] = {**block(theme), 'identities': [{**p, 'ticks': i * 10 + 5} for p in pair]}
        sample['captures'] = {phase: 'mouse-637-sidebar-' + phase + '-' + theme + '.png' for phase in ['before', 'settings', 'library', 'restored']}
        report['samples'].append(sample)
    return report, owners, inputs


def verify_sidebar(fixture):
    value, owners, inputs = fixture
    return S['verify'](value, owners, pid=11, platform='linux', inputs=inputs, input_check=F['input_event'], origin=ORIGIN)


class SidebarAcceptance(unittest.TestCase):
    def test_both_surface_types_themes_and_real_clickthrough_contract_accept(self):
        result = verify_sidebar(sidebar_fixture())
        self.assertEqual(len(result['witnesses']), 8)
        self.assertEqual(result['witnesses']['mouse-637-sidebar-library-dark.png'][0]['expectedRGB'], [32, 123, 164])

    def test_bad_masks_author_styles_and_unsettled_views_fail(self):
        for mutate in [lambda r: r['samples'][0]['settings']['guest']['mask'].update(pointerEvents='auto'),
                       lambda r: r['samples'][0]['settings']['guest']['mask'].update(closedShadow=False),
                       lambda r: r['samples'][0]['settings']['native'][0]['dim'].update(applied=False),
                       lambda r: r['samples'][0]['settings']['native'][1].update(attached=False),
                       lambda r: r['samples'][0]['settings']['guest']['author'].update(filter='brightness(0.86)'),
                       lambda r: r['samples'][0]['after']['guest'].update(mask={}),
                       lambda r: r['samples'][1]['library']['readback']['library'].update(backgroundColor='rgb(255, 255, 255)')]:
            fixture = sidebar_fixture(); mutate(fixture[0])
            with self.assertRaises(ValueError):
                verify_sidebar(fixture)

    def test_native_input_page_identity_and_fixed_probe_positions_are_bound(self):
        for mutate in [lambda r: r['samples'][0]['settings']['clickInput'].update(tabId='another-page'),
                       lambda r: r['samples'][0]['library']['guest'].update(buttonReceivesPoint=False),
                       lambda r: r['samples'][0]['settings']['clicks'].clear(),
                       lambda r: r['samples'][1]['after']['identities'][0].update(identity='reloaded'),
                       lambda r: r['samples'][0]['library']['readback']['witness']['point'].update(x=500),
                       lambda r: r['samples'][0]['library']['guest']['witness']['point'].update(y=191)]:
            fixture = sidebar_fixture(); mutate(fixture[0])
            with self.assertRaises(ValueError):
                verify_sidebar(fixture)


if __name__ == '__main__':
    unittest.main()
