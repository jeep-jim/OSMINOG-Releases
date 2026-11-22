#!/usr/bin/env python3
"""Synthetic negative contracts for UI fixtures; never native acceptance."""
import copy
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).parent
F = runpy.run_path(str(ROOT / 'mouse637-features-evidence.py'))
U = runpy.run_path(str(ROOT / 'mouse637-update-ui-evidence.py'))
H = runpy.run_path(str(ROOT / 'test_mouse637_ai_preview_evidence.py'))
ORIGIN = 'http://127.0.0.1:12002'


def state(phase, theme):
    ink = 'rgb(160, 160, 160)' if theme == 'dark' else 'rgb(36, 40, 49)'
    expected = set(U['CONTROLS'][3:] + (U['CONTROLS'][:1] if phase == 'available' else U['CONTROLS'][1:3] if phase == 'ready' else []))
    placements = [(560, 500, 80, 32), (430, 350, 80, 32), (690, 350, 80, 32),
                  (560, 182, 80, 32), (440, 250, 32, 32), (728, 250, 32, 32)]
    controls = []
    for selector, (x, y, width, height) in zip(U['CONTROLS'], placements):
        visible = selector in expected
        disabled = selector == '#update-check' and phase in ('downloading', 'installing')
        controls.append({'selector': selector, 'visible': visible, 'hidden': not visible,
                         'disabled': disabled, 'label': selector, 'radius': '50%', 'color': ink,
                         'bounds': {'x': x, 'y': y, 'width': width, 'height': height},
                         'hit': {'ready': visible and not disabled, 'x': x + width / 2, 'y': y + height / 2}})
    percent = 46 if phase == 'downloading' else 100 if phase in ('ready', 'installing') else 0
    return {'open': True, 'modal': True, 'phase': phase, 'theme': theme,
            'appearance': {'paneMode': 'square', 'whiteTone': 0},
            'bounds': {'x': 400, 'y': 150, 'width': 400, 'height': 400}, 'viewport': {'width': 1200, 'height': 800},
            'radius': '50%', 'overflow': {'clientWidth': 398, 'scrollWidth': 398, 'clientHeight': 398, 'scrollHeight': 398},
            'backdrop': {'backgroundColor': 'rgba(0, 0, 0, 0.82)', 'opacity': '1'},
            'surfaces': {name: 'rgb(%d, %d, %d)' % tuple(color) for name, color in zip(('ring', 'core'), U['PALETTE'][theme])},
            'logo': {'visible': True, 'complete': True, 'naturalWidth': 400, 'naturalHeight': 400, 'src': 'mouse-update.svg',
                     'bounds': {'x': 520, 'y': 270, 'width': 160, 'height': 160}},
            'status': {'text': 'Owned visual state ' + phase, 'color': ink, 'bounds': {'x': 530, 'y': 440, 'width': 140, 'height': 32}},
            'progress': {'hidden': phase != 'downloading', 'value': percent},
            'meter': {'pathLength': '100', 'dasharray': str(percent) + ' 100', 'progressVisible': str(percent > 0).lower(), 'opacity': '1' if percent else '0'},
            'controls': controls}


def fixture():
    def owners(ticks):
        return [H['identity'](index, 'main-' + str(index), ORIGIN, ticks) for index in range(2)]

    def block(ticks):
        pair = owners(ticks)
        return {'identities': pair, 'native': [H['native'](owner, {'x': 400 * index, 'y': 80, 'width': 400, 'height': 600}) for index, owner in enumerate(pair)]}

    report = {'schema': 1, 'version': '6.0.37', 'source': U['SOURCE'], 'visualStateFixture': True,
              'transportExercised': False, 'installationExercised': False, 'samples': [], 'restored': True, 'ok': True}
    inputs = []
    for index, theme in enumerate(('light', 'dark')):
        opened = H['click']('#version-button'); opened['at'] += index * 2
        closed = H['click'](U['CONTROLS'][-1] if theme == 'light' else '#update-minimize'); closed['at'] += index * 2 + 1
        inputs.extend([opened, closed])
        report['samples'].append({'theme': theme, 'appearance': 'square', 'before': block(20 + index * 20),
                                  'openInput': opened, 'states': [state(phase, theme) for phase in U['PHASES']],
                                  'capture': {'filename': 'mouse-637-update-burrow-' + theme + '.png', 'phase': 'available' if theme == 'light' else 'ready'},
                                  'dismissAction': 'close' if theme == 'light' else 'minimize', 'dismissInput': closed,
                                  'after': {**block(30 + index * 20), 'dialogOpen': False}})
    return report, owners(10), inputs


def verify(data):
    report, owners, inputs = data
    return U['verify'](report, owners, pid=11, platform='linux', inputs=inputs, input_check=F['input_event'], origin=ORIGIN)


class UpdatePresentationEvidence(unittest.TestCase):
    def reject(self, mutations):
        for mutation in mutations:
            data = fixture(); mutation(data[0])
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                verify(data)

    def test_two_themes_six_states_have_independently_derived_os_surface_probes(self):
        result = verify(fixture())
        self.assertEqual(list(result['witnesses']), ['mouse-637-update-burrow-light.png', 'mouse-637-update-burrow-dark.png'])
        for theme in ('light', 'dark'):
            probes = result['witnesses']['mouse-637-update-burrow-' + theme + '.png']
            self.assertEqual(probes, [
                {'name': 'update circle ring', 'point': {'x': 600, 'y': 172}, 'expectedRGB': U['PALETTE'][theme][0]},
                {'name': 'update circle core', 'point': {'x': 500, 'y': 350}, 'expectedRGB': U['PALETTE'][theme][1]},
            ])
        self.assertIs(result['summary']['transportExercised'], False)
        self.assertIs(result['summary']['installationExercised'], False)
        self.assertEqual(F['CAPTURES'][-4:], ['mouse-637-update-burrow-light.png', 'mouse-637-update-burrow-dark.png',
                                           'mouse-637-appearance-restored.png', 'mouse-637-extensions-restore-error.png'])

    def test_scope_source_and_restoration_claims_cannot_be_substituted(self):
        self.reject([lambda r: r.update(version='6.0.36'), lambda r: r.update(source='mock'),
                     lambda r: r.update(visualStateFixture=False), lambda r: r.update(transportExercised=True),
                     lambda r: r.update(installationExercised=True), lambda r: r.update(restored=False),
                     lambda r: r['samples'].pop(), lambda r: r['samples'][1].update(theme='light'),
                     lambda r: r['samples'][0]['states'].pop(),
                     lambda r: r['samples'][0]['capture'].update(phase='current')])

    def test_circle_viewport_overflow_and_strong_backdrop_are_required(self):
        self.reject([lambda r: r['samples'][0]['states'][0].update(modal=False),
                     lambda r: r['samples'][0]['states'][0]['appearance'].update(paneMode='rounded'),
                     lambda r: r['samples'][0]['states'][0]['bounds'].update(height=396),
                     lambda r: r['samples'][0]['states'][0].update(radius='0px'),
                     lambda r: r['samples'][0]['states'][0]['viewport'].update(width=798),
                     lambda r: r['samples'][0]['states'][0]['overflow'].update(scrollHeight=400),
                     lambda r: r['samples'][0]['states'][0]['backdrop'].update(backgroundColor='rgba(0, 0, 0, 0.14)'),
                     lambda r: r['samples'][0]['states'][0]['backdrop'].update(backgroundColor='rgba(250, 250, 250, 0.82)'),
                     lambda r: r['samples'][0]['states'][0]['backdrop'].update(opacity='0.5')])

    def test_original_centered_logo_status_progress_and_exact_theme_surfaces(self):
        self.reject([lambda r: r['samples'][0]['states'][0]['logo'].update(src='replacement.svg'),
                     lambda r: r['samples'][0]['states'][0]['logo'].update(complete=False),
                     lambda r: r['samples'][0]['states'][0]['logo']['bounds'].update(x=523),
                     lambda r: r['samples'][0]['states'][0]['logo']['bounds'].update(width=149),
                     lambda r: r['samples'][0]['states'][0]['status'].update(text=' '),
                     lambda r: r['samples'][0]['states'][2]['progress'].update(value=0),
                     lambda r: r['samples'][0]['states'][2]['progress'].update(hidden=True),
                     lambda r: r['samples'][0]['states'][2]['meter'].update(dasharray='0 100'),
                     lambda r: r['samples'][0]['states'][3]['meter'].update(progressVisible='false'),
                     lambda r: r['samples'][1]['states'][3]['surfaces'].update(core='rgb(250, 250, 250)')])

    def test_control_visibility_circle_shape_rim_and_native_hit_exposure(self):
        self.reject([lambda r: r['samples'][0]['states'][1]['controls'].pop(),
                     lambda r: r['samples'][0]['states'][1]['controls'][0].update(selector='#update-check'),
                     lambda r: r['samples'][0]['states'][1]['controls'][0].update(visible=False),
                     lambda r: r['samples'][0]['states'][1]['controls'][0].update(label=' '),
                     lambda r: r['samples'][0]['states'][1]['controls'][0]['bounds'].update(x=560, y=335),
                     lambda r: r['samples'][0]['states'][1]['controls'][0]['hit'].update(ready=False),
                     lambda r: r['samples'][0]['states'][1]['controls'][0]['hit'].update(x=900),
                     lambda r: r['samples'][0]['states'][2]['controls'][3].update(disabled=False),
                     lambda r: r['samples'][0]['states'][0]['controls'][4].update(radius='0px'),
                     lambda r: r['samples'][0]['states'][0]['controls'][5]['bounds'].update(height=40)])

    def test_primary_text_tone_rejects_fixed_white_and_missing_computed_colors(self):
        self.reject([lambda r: r['samples'][1]['states'][0]['status'].update(color='rgb(227, 230, 235)'),
                     lambda r: r['samples'][1]['states'][0]['controls'][3].update(color='rgb(227, 230, 235)'),
                     lambda r: r['samples'][1]['states'][0]['status'].pop('color'),
                     lambda r: r['samples'][1]['states'][0]['controls'][3].pop('color'),
                     lambda r: r['samples'][0]['states'][0]['status'].update(color='rgb(160, 160, 160)'),
                     lambda r: r['samples'][0]['states'][0]['controls'][3].update(color='rgb(160, 160, 160)')])

    def test_native_input_must_match_process_platform_ledger_and_real_controls(self):
        self.reject([lambda r: r['samples'][0]['openInput'].update(selector='#theme-button'),
                     lambda r: r['samples'][0]['openInput'].update(pid=12),
                     lambda r: r['samples'][0]['openInput'].update(source='CGEvent'),
                     lambda r: r['samples'][0]['openInput'].update(tabId='foreign-page'),
                     lambda r: r['samples'][0]['openInput']['events'][0].update(trusted=False),
                     lambda r: r['samples'][1].update(dismissAction='close'),
                     lambda r: r['samples'][1]['dismissInput'].update(selector='#update-dialog [data-close-dialog]')])
        data = fixture(); data[0]['samples'][0]['openInput'] = copy.deepcopy(data[0]['samples'][0]['openInput'])
        data[0]['samples'][0]['openInput']['at'] += 100
        with self.assertRaises(ValueError):
            verify(data)

    def test_live_native_pages_survive_both_dismiss_actions(self):
        self.reject([lambda r: r['samples'][0]['after'].update(dialogOpen=True),
                     lambda r: r['samples'][0]['after']['identities'][0].update(webContentsId=900),
                     lambda r: r['samples'][0]['after']['identities'][0].update(field='lost'),
                     lambda r: r['samples'][1]['before']['identities'][0].update(ticks=1),
                     lambda r: r['samples'][0]['after']['native'][0].update(visible=False),
                     lambda r: r['samples'][0]['after']['native'][0].update(attached=False),
                     lambda r: r['samples'][0]['after']['native'][0]['actualBounds'].update(width=399)])


if __name__ == '__main__':
    unittest.main()
