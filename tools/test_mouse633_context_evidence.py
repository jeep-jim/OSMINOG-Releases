#!/usr/bin/env python3
"""Synthetic unit witnesses for the actual native-context validator.

These generated PNGs and JSON are deliberately not native publication evidence.
No checker, native-state assertion or image decoder is mocked in these tests.
"""
import copy
import json
from pathlib import Path
import runpy
import struct
import unittest
import zlib

E = runpy.run_path(str(Path(__file__).with_name('mouse633-context-evidence.py')))


def encode_png(width, height, pixels):
    def chunk(kind, data):
        return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data)&0xffffffff)
    raw = b''.join(b'\0'+pixels[y*width*4:(y+1)*width*4] for y in range(height))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))+chunk(b'IDAT', zlib.compress(raw))+chunk(b'IEND', b'')


def display_png(opened=False, dark=False):
    color = (40, 40, 40, 255) if dark else (238, 238, 238, 255)
    data = bytearray(bytes(color)*800*600)
    if opened:
        for y in range(220, 420):
            data[(y*800+300)*4:(y*800+500)*4] = bytes((100, 100, 100, 255))*200
    return encode_png(800, 600, data)


def icon_png(index):
    data = bytearray(32*32*4)
    for y in range(4, 28):
        for x in range(4, 28):
            alpha = 128 if x in (4, 27) or y in (4, 27) else 255
            at = (y*32+x)*4
            data[at:at+4] = bytes((128, 128, 128, alpha))
    # Distinct synthetic shapes exercise evidence binding; these are not artwork.
    data[((8+index)*32+8)*4+3] = 0
    return encode_png(32, 32, data)


def preset(count):
    columns, rows = (1, 2) if count == 2 else (2, 2) if count == 4 else (4, 3)
    index = 0

    def vertical(left):
        nonlocal index
        index += 1
        node = {'id': 'p'+str(index)}
        return node if left == 1 else {'axis': 'y', 'ratio': 1/left, 'a': node, 'b': vertical(left-1)}

    def horizontal(left):
        node = vertical(rows)
        return node if left == 1 else {'axis': 'x', 'ratio': 1/left, 'a': node, 'b': horizontal(left-1)}

    return horizontal(columns)


def fixture(platform='win32', pages=None, pid=123):
    arch = 'arm64' if platform == 'darwin' else 'x64'
    source = {'darwin': 'CGEvent', 'win32': 'User32', 'linux': 'XTest'}[platform]
    if pages is None:
        pages = [{'id': 'page-'+str(i), 'index': i, 'desk': 'd0', 'webContentsId': 100+i,
                  'url': 'http://127.0.0.1:31337/page/'+str(i)+'/', 'navigationEpoch': 1,
                  'identity': 'owned-'+str(i), 'timeOrigin': 10000+i,
                  'field': 'preserved-'+str(i)+'-данные', 'cookie': 'mouse631_'+str(i)+'=owned-'+str(i), 'ticks': 10}
                 for i in (0, 1)]
    pages = copy.deepcopy(pages)
    files = {}
    normal_layout = {'tree': {'axis': 'x', 'ratio': .5, 'a': {'id': 'p1'}, 'b': {'id': 'p2'}},
                     'slots': {'p1': pages[0]['id'], 'p2': pages[1]['id']}, 'active': 'p1'}
    facts = {'schema': 1, 'version': '6.0.33', 'platform': platform, 'arch': arch, 'pid': pid,
             'budgetMs': 60000, 'elapsedMs': 15000, 'source': E['SOURCE'], 'ok': True, 'restored': True,
             'physicalUserDeviceVerified': False, 'normal': {'beforePages': pages, 'afterPages': copy.deepcopy(pages),
                 'bookmarksBeforeSHA256': 'a'*64, 'bookmarksAfterSHA256': 'a'*64},
             'private': {'normalBeforeSHA256': 'b'*64, 'normalAfterSHA256': 'b'*64,
                 'privateBookmarksBefore': [], 'privateBookmarksAfter': [], 'privateTabId': 'private-page',
                 'privateWebContentsId': 900, 'closed': True, 'normalUnchanged': True, 'noPrivateProfileMarker': True},
             'scenarios': [], 'icons': [], 'captures': []}
    icons = {}
    for i, kind in enumerate(['star', 'star-filled', 'split-x', 'split-y', *E['GRID']]):
        raw = icon_png(i)
        checksum = E['sha'](raw)
        name = 'mouse-633-context-icon-'+checksum[:20]+'.png'
        files[name] = raw
        row = {'filename': name, 'sha256': checksum, 'logicalSize': {'width': 16, 'height': 16},
               'pixelSize': {'width': 32, 'height': 32}, 'scales': [2], 'template': platform == 'darwin'}
        facts['icons'].append(row)
        icons[kind] = row

    def item(id, label, image, enabled=True, submenu=None):
        value = {'id': id, 'label': label, 'type': 'submenu' if submenu else 'normal', 'enabled': enabled,
                 'visible': True, 'role': '', 'icon': image}
        if submenu:
            value['submenu'] = submenu
        return value

    def menu(first):
        grid = []
        for suffix in ('1', '2-x', '2-y', '3', '4', '6', '8', '9', '12'):
            label = ('2 panes · side by side' if suffix == '2-x' else '2 panes · stacked') if suffix.startswith('2-') else suffix+' '+('pane' if suffix == '1' else 'panes')
            name = E['PREFIX']+'layout-'+suffix
            grid.append(item(name, label, icons[name]))
        return [item(E['PREFIX']+'bookmark', 'Add to favorites' if first else 'Already in favorites', icons['star' if first else 'star-filled'], first),
                {'id': '', 'label': '', 'type': 'separator', 'enabled': True, 'visible': True, 'role': ''},
                item(E['PREFIX']+'split-x', 'Split to the right', icons['split-x']),
                item(E['PREFIX']+'split-y', 'Split below', icons['split-y']),
                item(E['PREFIX']+'grid', 'Pane layout', icons[E['PREFIX']+'layout-4'], submenu=grid)]

    for name in E['SCENARIOS']:
        private = name.startswith('private-')
        first = 'favorite' in name
        scope = 'private' if private else 'normal'
        target = {'id': 'private-page', 'webContentsId': 900, 'url': 'http://127.0.0.1:31338/mouse633-private-context-owned'} if private else pages[1]
        before = {'tree': {'id': 'p1'}, 'slots': {'p1': target['id']}, 'active': 'p1'} if private else copy.deepcopy(normal_layout)
        after = copy.deepcopy(before)
        pane = 'p1' if private else 'p2'
        title = 'Owned private context fixture' if private else 'Owned second page'
        if first:
            bookmark = {'id': 'private-bookmark' if private else 'normal-bookmark', 'url': target['url'], 'title': title}
            effect = {'action': 'bookmark', 'url': target['url'], 'title': title, 'bookmark': bookmark, 'library': scope}
            after['active'] = pane  # Native focus may activate the clicked page.
            if private:
                facts['private']['privateBookmarksAfter'] = [bookmark]
        elif name.startswith('split-'):
            axis = name[-1]
            after['tree'] = E['changed_tree'](before['tree'], pane, axis, 'p3')
            after['slots']['p3'] = 'new-start'
            after['active'] = 'p3'
            effect = {'action': 'split', 'axis': axis, 'targetPane': pane, 'beforeCount': 2, 'afterCount': 3}
        else:
            count = int(name.split('-')[1])
            after = {'tree': preset(count), 'slots': {'p1': pages[1]['id'], 'p2': pages[0]['id']}, 'active': 'p1'}
            effect = {'action': 'layout', 'count': count, 'axis': 'y' if count == 2 else None,
                      'firstPane': 'p1', 'firstTabId': target['id'], 'paneIds': ['p'+str(i) for i in range(1, count+1)]}
        items = menu(first)
        selected = E['PREFIX']+'bookmark' if first else E['PREFIX']+name if name.startswith('split-') else E['PREFIX']+'grid'
        choices = [row for row in items if row['enabled'] and row['type'] != 'separator']
        keys = ['HOME']+['DOWN']*next(i for i, value in enumerate(choices) if value['id'] == selected)
        if selected == E['PREFIX']+'grid':
            keys += ['RIGHT', 'HOME']+['DOWN']*E['GRID'].index(E['PREFIX']+'layout-'+name[5:])
        keys += ['ENTER']
        row = {'name': name, 'scope': scope, 'beforeLayout': before, 'afterLayout': after,
               'target': {'id': target['id'], 'webContentsId': target['webContentsId'], 'pane': pane, 'desk': 'private-desk' if private else target['desk'], 'source': 'guest'},
               'pagesBefore': [] if private else copy.deepcopy(pages), 'pagesAfter': [] if private else copy.deepcopy(pages),
               'effect': effect, 'menu': {'shownAt': 1000, 'closedAt': 2000, 'items': items, 'popup': {'windowId': 1, 'x': None, 'y': None}},
               'input': {'source': source, 'rightClick': {'x': 300, 'y': 220},
                    'contextEvent': {'isTrusted': True, 'timeStamp': 15, 'x': 80, 'y': 160, 'url': target['url']},
                    'keys': [{'key': key, 'at': 1100+i*40, 'source': source} for i, key in enumerate(keys)]}}
        if not private:
            native = []
            for i, page in enumerate(pages):
                bounds = {'x': i*220, 'y': 100, 'width': 200, 'height': 300}
                native.append({'tabId': page['id'], 'index': page['index'], 'desk': page['desk'], 'webContentsId': page['webContentsId'],
                               'bounds': bounds.copy(), 'viewBounds': bounds.copy(), 'parentBounds': None, 'actualBounds': bounds.copy(),
                               'visible': True, 'parentVisible': True, 'cachedVisible': True, 'attached': True})
            row['nativePages'] = native
        if name in ('favorite-light', 'split-x', 'private-favorite-dark'):
            theme = 'light' if name == 'favorite-light' else 'dark'
            capture = {'difference': {'algorithm': E['DIFFERENCE'], 'region': {'x': 0, 'y': 0, 'width': 800, 'height': 600},
                                     'changedPixels': 40000, 'tolerance': 8, 'bounds': {'x': 300, 'y': 220, 'width': 200, 'height': 200}},
                       'anchorPixel': {'x': 300, 'y': 220}, 'mapping': {'scaleX': 1, 'scaleY': 1, 'originX': 0, 'originY': 0}}
            for phase in ('before', 'open'):
                filename = 'mouse-633-context-'+name+'-'+phase+'.png'
                raw = display_png(phase == 'open', theme == 'dark')
                files[filename] = raw
                value = {'filename': filename, 'sha256': E['sha'](raw), 'pixelSize': {'width': 800, 'height': 600},
                         'display': {'id': 1, 'bounds': {'x': 0, 'y': 0, 'width': 800, 'height': 600}, 'scaleFactor': 1},
                         'contentBounds': {'x': 0, 'y': 0, 'width': 800, 'height': 600}, 'source': 'globalCapture.acquire(display)',
                         'backend': 'synthetic unit fixture', 'theme': theme, 'scope': scope, 'phase': phase}
                capture[phase] = value
                facts['captures'].append(value)
            row['capture'] = capture
        facts['scenarios'].append(row)
    files['mouse-633-owner-feedback.log'] = (E['MARKER']+'\nMOUSE_633_OWNER_FEEDBACK_PASS\n').encode()
    return files, facts


class NativeContextEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files_original, cls.facts_original = fixture()

    def setUp(self):
        self.files = dict(self.files_original)
        self.facts = copy.deepcopy(self.facts_original)

    def verify(self, platform='win32', **kwargs):
        raw = json.dumps(self.facts, allow_nan=False).encode()
        self.files[E['NAME']] = raw
        return E['verify'](self.files.__getitem__, expected_platform=platform,
                           expected_arch='arm64' if platform == 'darwin' else 'x64', **kwargs)

    def reject(self, message=None):
        with self.assertRaisesRegex(ValueError, message) if message else self.assertRaises(ValueError):
            self.verify()

    def test_actual_checker_accepts_all_three_platform_fixture_branches(self):
        for platform in ('darwin', 'win32', 'linux'):
            with self.subTest(platform=platform):
                self.files, self.facts = fixture(platform)
                result = self.verify(platform)
                self.assertEqual(len(result['nativeScenarios']), 7)
                self.assertEqual(len(result['captures']), 6)

    def test_wrong_runtime_process_physical_scope_or_cleanup_fails(self):
        for key, value in [('version', '6.0.32'), ('pid', 0), ('ok', False), ('restored', False),
                           ('physicalUserDeviceVerified', True), ('elapsedMs', 60001), ('error', {'message': 'failed'})]:
            self.setUp(); self.facts[key] = value; self.reject()
        self.setUp()
        with self.assertRaisesRegex(ValueError, 'process/runtime'):
            self.verify(expected_pid=124)

    def test_owner_raw_hash_pid_and_original_page_binding_are_independent(self):
        raw = json.dumps(self.facts, allow_nan=False).encode()
        binding = {'report': E['NAME'], 'sha256': E['sha'](raw), 'marker': E['MARKER']}
        self.assertTrue(self.verify(expected_pid=123, expected_pages=self.facts['normal']['beforePages'], binding=binding)['ok'])
        binding['sha256'] = 'f'*64
        with self.assertRaisesRegex(ValueError, 'raw report binding'):
            self.verify(binding=binding)
        pages = copy.deepcopy(self.facts['normal']['beforePages']); pages[1]['webContentsId'] += 1
        with self.assertRaisesRegex(ValueError, 'owner process'):
            self.verify(expected_pages=pages)

    def test_missing_scenario_native_observation_or_success_marker_fails(self):
        self.facts['scenarios'].pop(); self.reject('coverage')
        self.setUp(); self.facts['scenarios'][0]['menu']['shownAt'] = None; self.reject('popup/close')
        self.setUp(); self.files['mouse-633-owner-feedback.log'] = b'MOUSE_633_OWNER_FEEDBACK_PASS\n'; self.reject('success marker')

    def test_real_guest_rightclick_and_exact_native_keyboard_route_are_required(self):
        self.facts['scenarios'][0]['input']['contextEvent']['isTrusted'] = False; self.reject('trusted guest')
        self.setUp(); self.facts['scenarios'][3]['input']['keys'][0]['source'] = 'DOM'; self.reject('native menu keys')
        self.setUp(); self.facts['scenarios'][3]['input']['keys'] = self.facts['scenarios'][3]['input']['keys'][:-1]; self.reject('native menu keys')

    def test_enter_timestamp_can_follow_synchronous_menu_close(self):
        for row in self.facts['scenarios']:
            row['menu']['closedAt'] = row['input']['keys'][-1]['at']-1
        self.assertTrue(self.verify()['ok'])

    def test_exact_menu_labels_grid_choices_and_native_icons_are_required(self):
        self.facts['scenarios'][0]['menu']['items'][2]['label'] = 'Other action'; self.reject('label')
        self.setUp(); self.facts['scenarios'][0]['menu']['items'][4]['submenu'].pop(); self.reject('grid choices')
        self.setUp(); item = self.facts['scenarios'][0]['menu']['items']; item[3]['icon'] = item[2]['icon']; self.reject('distinct native shapes')

    def test_real_icon_png_transparency_antialias_and_native_scale_are_checked(self):
        self.facts['icons'][0]['logicalSize']['width'] = 32; self.reject('2x native image')
        self.setUp(); self.facts['icons'][0]['scales'] = [1]; self.reject('scale/template')
        self.setUp(); icon = self.facts['icons'][0]; raw = encode_png(32, 32, bytes((128, 128, 128, 255))*32*32)
        icon['sha256'] = E['sha'](raw); icon['filename'] = 'mouse-633-context-icon-'+icon['sha256'][:20]+'.png'
        self.files[icon['filename']] = raw; self.reject('clipped or lacks smooth')

    def test_template_hint_is_platform_specific_and_does_not_invent_an_api(self):
        for row in self.facts['icons']: row['template'] = None
        self.assertTrue(self.verify()['ok'])
        self.files, self.facts = fixture('darwin'); self.facts['icons'][0]['template'] = None
        with self.assertRaisesRegex(ValueError, 'scale/template'): self.verify('darwin')

    def test_rehashed_changed_os_pixels_cannot_preserve_an_old_difference_claim(self):
        row = self.facts['scenarios'][0]['capture']['open']
        raw = display_png(False, False); self.files[row['filename']] = raw; row['sha256'] = E['sha'](raw)
        self.reject('pixel differences')

    def test_native_popup_display_mapping_and_anchor_must_match_actual_pixels(self):
        self.facts['scenarios'][0]['capture']['mapping']['scaleX'] = 2; self.reject('DPI mapping')
        self.setUp(); self.facts['scenarios'][0]['capture']['anchorPixel']['x'] += 1; self.reject('anchor')
        self.setUp(); self.facts['scenarios'][0]['capture']['difference']['tolerance'] = 255; self.reject('pixel differences')

    def test_bookmark_uses_clicked_nonactive_page_and_does_not_change_pane_slots(self):
        self.facts['scenarios'][0]['target']['id'] = self.facts['normal']['beforePages'][0]['id']; self.reject('different native page')
        self.setUp(); self.facts['scenarios'][0]['beforeLayout']['active'] = 'p2'; self.reject('active page')
        self.setUp(); self.facts['scenarios'][0]['afterLayout']['slots']['p2'] = 'other'; self.reject()

    def test_split_changes_only_the_clicked_branch_in_the_requested_direction(self):
        self.facts['scenarios'][1]['afterLayout']['tree']['b']['axis'] = 'y'; self.reject('wrong pane or direction')
        self.setUp(); self.facts['scenarios'][1]['afterLayout']['slots']['p1'] = 'other'; self.reject()

    def test_grid_keeps_both_original_pages_and_exact_selected_geometry(self):
        self.facts['scenarios'][5]['afterLayout']['tree']['ratio'] = .5; self.reject('cell geometry')
        self.setUp(); self.facts['scenarios'][3]['afterLayout']['tree']['axis'] = 'x'; self.reject('count/axis')
        self.setUp(); self.facts['scenarios'][4]['afterLayout']['slots']['p1'] = 'other'; self.reject()

    def test_native_page_identity_and_visibility_survive_every_action(self):
        self.facts['scenarios'][2]['pagesAfter'][0]['timeOrigin'] += 1; self.reject('page reloaded')
        self.setUp(); self.facts['scenarios'][4]['nativePages'][0]['visible'] = False; self.reject('visibility')
        self.setUp(); self.facts['normal']['afterPages'][1]['cookie'] = ''; self.reject('page reloaded')

    def test_private_favorite_is_ephemeral_and_normal_library_remains_unchanged(self):
        for key, value in [('normalAfterSHA256', 'c'*64), ('closed', False), ('noPrivateProfileMarker', False),
                           ('privateWebContentsId', 100), ('privateTabId', 'page-1')]:
            self.setUp(); self.facts['private'][key] = value; self.reject('private favorite')
        self.setUp(); self.facts['normal']['bookmarksAfterSHA256'] = 'b'*64; self.reject('not restored')

    def test_all_three_publication_contracts_run_this_native_menu_validator_suite(self):
        root = Path(__file__).resolve().parents[1]
        for name in ('publish-mouse633.yml', 'publish-mouse633-windows.yml', 'publish-mouse633-linux.yml'):
            with self.subTest(workflow=name):
                text = (root/'.github/workflows'/name).read_text()
                self.assertIn('run: python3 tools/test_mouse633_context_evidence.py -v', text)


if __name__ == '__main__':
    unittest.main()
