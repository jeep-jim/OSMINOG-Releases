#!/usr/bin/env python3
"""Synthetic current635 layout contracts; not native acceptance evidence."""
import copy
from pathlib import Path
import runpy
import unittest

HERE = Path(__file__).parent
C = runpy.run_path(str(HERE / 'mouse635-pane-layout-evidence.py'))
L = runpy.run_path(str(HERE / 'test_mouse635_library_evidence.py'))


def fixture(platform='linux', arch='x64'):
    library = L['fixture'](); template = library['facts']['captures'][0]
    raw, captures = {}, []
    for name in C['CAPTURES']:
        frame = copy.deepcopy(template)
        frame.update(filename=name, displayFilename=name[:-4] + '-display.png')
        raw[name] = library['raw'][template['filename']]
        raw[frame['displayFilename']] = library['raw'][template['displayFilename']]
        captures.append(frame)
    facts = {'schema': 1, 'source': C['SOURCE'], 'captures': C['CAPTURES'],
             **dict.fromkeys(('nativeLayoutMenu', 'actualPresetChecked', 'preservesTabOrder', 'pin',
                              'freeSiblingEditable', 'persisted', 'desktopIsolation', 'privateIsolation',
                              'explicitUnpin', 'livePagePreserved'), True), 'guards': dict.fromkeys(C['GUARDS'], True)}
    pages = [{'id': 'page-' + str(i), 'index': i, 'desk': 'desk-0', 'webContentsId': 200 + i,
              'url': 'http://127.0.0.1:31337/page/' + str(i) + '/', 'navigationEpoch': 1,
              'identity': 'owned-' + str(i), 'timeOrigin': 10000 + i, 'field': 'preserved-' + str(i) + '-данные',
              'scrollX': 0, 'scrollY': 130, 'cookie': 'mouse631_' + str(i) + '=owned-' + str(i), 'ticks': 10} for i in (101, 102)]
    initial = {'desktopId': 'desk-0', 'tree': {'axis': 'x', 'ratio': .5, 'a': {'id': 'p1'}, 'b': {'id': 'p2'}},
               'slots': {'p1': pages[0]['id'], 'p2': pages[1]['id']}, 'active': 'p1', 'pinnedPanes': {}}
    pinned = copy.deepcopy(initial); pinned.update(active='p2', pinnedPanes={'p2': pages[1]['id']}); pinned['tree']['ratio'] = .53
    split = copy.deepcopy(pinned); split.update(active='p3'); split['slots']['p3'] = 'owned-start'
    split['tree']['a'] = {'axis': 'y', 'ratio': .5, 'a': {'id': 'p1'}, 'b': {'id': 'p3'}}
    bounds = {'x': 430, 'y': 80, 'width': 370, 'height': 500}
    state = {'tabId': pages[1]['id'], 'index': 102, 'desk': 'desk-0', 'webContentsId': pages[1]['webContentsId'],
             'bounds': bounds, 'viewBounds': dict(bounds), 'parentBounds': None, 'actualBounds': dict(bounds),
             'visible': True, 'parentVisible': True, 'cachedVisible': True, 'attached': True}
    facts.update(elapsedMs=6000, pagesBefore=pages, pagesAfter=copy.deepcopy(pages), layoutBefore=initial, pinned=pinned,
                 afterFreeSplit=split, afterFreeSplitRenderer=copy.deepcopy(split), pinnedBoundsBefore=state, pinnedBoundsAfter=copy.deepcopy(state),
                 persistence={'key': 'mouseDesktopsV1', 'desktopId': 'desk-0', 'pinnedPanes': {'p2': pages[1]['id']},
                              'rehydrated': True, 'tree': copy.deepcopy(split['tree']), 'slots': dict(split['slots'])},
                 private={'before': {'desktopId': 'desk-0', 'tree': {'id': 'p1'}, 'slots': {}, 'active': 'p1', 'pinnedPanes': {}}, 'pinnedPanes': {'p1': ''}},
                 guardResults=[{'action': action, 'rejected': True, 'message': 'Сначала открепите окно'}
                               for action in ('close', 'replace', 'split', 'preset', 'transfer')], menuSnapshots=[])
    for index in range(5):
        target = {'desk': 'desk-0', 'pane': 'p1' if index in (1, 2) else 'p2',
                  'id': pages[0 if index in (1, 2) else 1]['id'], 'source': 'shell' if index < 3 else 'guest'}
        if index < 3:
            target['kind'] = 'layout'
            items = [{'id': identifier, 'label': identifier, 'type': 'checkbox', 'hasIcon': True, 'enabled': True,
                      'checked': index == 0 and identifier == C['GRID'][1] or index == 1 and identifier == C['GRID'][2]} for identifier in C['GRID']]
        else:
            items = [{'id': 'mouse-context-pin', 'label': 'Закрепить окно' if index == 3 else 'Открепить окно',
                      'type': 'normal', 'hasIcon': True, 'enabled': True}]
            items.extend({'id': 'mouse-context-split-' + axis, 'label': axis, 'type': 'normal', 'hasIcon': True,
                          'enabled': index == 3} for axis in ('x', 'y'))
        facts['menuSnapshots'].append({'target': target, 'items': items, 'openedAt': 1000 + index * 200,
                                       'closedAt': 1100 + index * 200})
    native = [{'selector': '#layout-menu-button', 'source': {'linux': 'XTest', 'win32': 'User32', 'darwin': 'CGEvent'}[platform],
               'point': {'x': 50, 'y': 650}, 'at': 1234, 'navigates': False,
               'events': [{'type': 'click', 'trusted': True, 'matches': True}]}]
    raw['mouse-635-owner-feedback.log'] = (C['MARKER'] + '\n').encode()
    return {'raw': raw, 'owner': {'pid': 80, 'platform': platform, 'arch': arch, 'budgetMs': 240000,
                                'panes': facts, 'nativeInputs': native, 'captures': captures}}


class PaneLayoutEvidence(unittest.TestCase):
    def verify(self, value):
        return C['verify'](value['raw'].__getitem__, owner=value['owner'])

    def test_supported_platform_input_shapes(self):
        for platform, arch in [('linux', 'x64'), ('win32', 'x64'), ('darwin', 'arm64')]:
            result = self.verify(fixture(platform, arch)); self.assertTrue(result['ok'])
            self.assertEqual(len(result['nativeCaptures']), 2)

    def test_each_pin_guard_and_explicit_scope_is_mandatory(self):
        for guard in C['GUARDS']:
            value = fixture(); value['owner']['panes']['guards'][guard] = False
            with self.assertRaises(ValueError): self.verify(value)
        for key in ('nativeLayoutMenu', 'actualPresetChecked', 'preservesTabOrder', 'persisted',
                    'desktopIsolation', 'privateIsolation', 'explicitUnpin', 'livePagePreserved'):
            value = fixture(); value['owner']['panes'][key] = False
            with self.assertRaises(ValueError): self.verify(value)

    def test_native_input_marker_and_frame_binding(self):
        value = fixture(); value['owner']['nativeInputs'][0]['events'][0]['trusted'] = False
        with self.assertRaises(ValueError): self.verify(value)
        value = fixture(); value['owner']['captures'][0]['displaySha256'] = 'f' * 64
        with self.assertRaises(ValueError): self.verify(value)
        value = fixture(); value['raw']['mouse-635-owner-feedback.log'] = b'not a native pane pass\n'
        with self.assertRaises(ValueError): self.verify(value)

    def test_raw_layout_identity_geometry_and_menu_readbacks_are_required(self):
        for mutate in [lambda p: p['pagesAfter'][1].update(timeOrigin=999),
                       lambda p: p['persistence']['tree'].update(ratio=.5),
                       lambda p: p['pinnedBoundsAfter']['bounds'].update(width=350),
                       lambda p: p['afterFreeSplit']['tree'].update(ratio=.5),
                       lambda p: p['afterFreeSplitRenderer']['tree'].update(ratio=.5),
                       lambda p: p['private']['pinnedPanes'].update(p1='normal-tab'),
                       lambda p: p['menuSnapshots'][0]['items'][1].update(checked=False),
                       lambda p: p['menuSnapshots'][4]['items'][1].update(enabled=True),
                       lambda p: p['guardResults'][0].update(rejected=False)]:
            value = fixture(); mutate(value['owner']['panes'])
            with self.assertRaises(ValueError): self.verify(value)


if __name__ == '__main__':
    unittest.main()
