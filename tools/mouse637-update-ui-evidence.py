#!/usr/bin/env python3
"""Independent circular updater presentation contract and real OS witnesses.

The six states are UI-owned fixtures. They do not prove update transport or
installation, which remain mandatory in the separate installed update gate.
"""
import math
from pathlib import Path
import re
import runpy

N = runpy.run_path(str(Path(__file__).with_name('mouse637-native-evidence.py')))
need, rect, finite = (N[key] for key in ('need', 'rect', 'finite'))
SOURCE = 'UI-owned state fixtures with real installed controls, trusted native open/close and OS screenshots'
PHASES = ['current', 'available', 'downloading', 'ready', 'installing', 'error']
CONTROLS = ['#update-download', '#update-install', '#update-open', '#update-check',
            '#update-minimize', '#update-dialog [data-close-dialog]']
PALETTE = {'light': [[230, 232, 236], [250, 250, 250]], 'dark': [[34, 40, 50], [21, 26, 34]]}


def radius(value, diameter, label):
    match = re.fullmatch(r'(\d+(?:\.\d+)?)(%|px)', value if isinstance(value, str) else '')
    need(match is not None, label + ' computed radius is absent')
    amount = float(match[1])
    need(amount >= (49.9 if match[2] == '%' else diameter / 2 - 1.1), label + ' is not circular')


def numeric_css(value, label):
    need(isinstance(value, str) and re.fullmatch(r'(?:0|1|0?\.\d+)', value), label + ' is not a computed opacity')
    result = float(value)
    need(0 <= result <= 1, label + ' is out of range')
    return result


def presentation(value, phase, theme):
    need(value.get('open') is True and value.get('modal') is True and value.get('phase') == phase
         and value.get('theme') == theme and value.get('appearance') == {'paneMode': 'square', 'whiteTone': 0},
         'update presentation state, theme or square workspace differs')
    bounds = rect(value.get('bounds'))
    need(bounds['width'] >= 360 and bounds['height'] >= 360, 'update circle is too small')
    N['near'](bounds['width'], bounds['height'], 'update window is not a circle in square mode', 1.1)
    radius(value.get('radius'), bounds['width'], 'update window')
    viewport = value.get('viewport', {})
    need(all(finite(viewport.get(axis)) and viewport[axis] > 0 for axis in ('width', 'height'))
         and bounds['x'] >= 0 and bounds['y'] >= 0
         and N['right'](bounds) <= viewport['width'] + 1 and N['bottom'](bounds) <= viewport['height'] + 1,
         'complete update circle is outside the viewport')
    overflow = value.get('overflow', {})
    for axis in ('Width', 'Height'):
        client, scroll = overflow.get('client' + axis), overflow.get('scroll' + axis)
        need(finite(client) and finite(scroll) and client > 0 and 0 <= scroll <= client + 1,
             'update circle has scroll overflow or missing geometry')
    backdrop = value.get('backdrop', {})
    channels = re.fullmatch(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*(0|1|0?\.\d+))?\)', backdrop.get('backgroundColor', ''))
    need(channels is not None, 'update backdrop computed color is absent')
    alpha = float(channels[4]) if channels[4] is not None else 1
    need(all(0 <= int(channels[i]) <= 20 for i in (1, 2, 3)) and 0 <= alpha <= 1
         and alpha * numeric_css(backdrop.get('opacity'), 'update backdrop') >= .75,
         'update backdrop is not strongly darkened')
    logo = value.get('logo', {})
    need(logo.get('visible') is True and logo.get('complete') is True and logo.get('src') == 'mouse-update.svg'
         and all(finite(logo.get(key)) and logo[key] > 0 for key in ('naturalWidth', 'naturalHeight')),
         'existing Mouse update logo is absent or not decoded')
    logo_bounds = rect(logo.get('bounds'))
    need(logo_bounds['width'] >= 150 and logo_bounds['height'] >= 150, 'existing Mouse logo is too small')
    for axis, size in (('x', 'width'), ('y', 'height')):
        N['near'](logo_bounds[axis] + logo_bounds[size] / 2, bounds[axis] + bounds[size] / 2,
                  'existing Mouse logo is not centered on ' + axis, 1.1)
    status = value.get('status', {})
    need(isinstance(status.get('text'), str) and status['text'].strip(), 'update status text is absent')
    ink = 'rgb(160, 160, 160)' if theme == 'dark' else 'rgb(36, 40, 49)'
    need(status.get('color') == ink, 'update status ignores the selected primary text tone')
    rect(status.get('bounds'))
    progress = value.get('progress', {})
    need(progress.get('hidden') is (phase != 'downloading')
         and (phase != 'downloading' or progress.get('value') == 46), 'update progress state differs')
    percent = 46 if phase == 'downloading' else 100 if phase in ('ready', 'installing') else 0
    meter = value.get('meter', {})
    need(meter.get('pathLength') == '100' and meter.get('dasharray') == str(percent) + ' 100'
         and meter.get('progressVisible') == ('true' if percent else 'false'), 'circular update progress meter differs')
    numeric_css(meter.get('opacity'), 'update progress meter')
    surfaces = value.get('surfaces', {})
    for name, color in zip(('ring', 'core'), PALETTE[theme]):
        need(surfaces.get(name) == 'rgb(%d, %d, %d)' % tuple(color), 'update circle surface is not the required theme')
    controls = value.get('controls', [])
    need(isinstance(controls, list) and [control.get('selector') for control in controls] == CONTROLS,
         'update presentation controls are missing, duplicated or reordered')
    expected = set(CONTROLS[3:] + (CONTROLS[:1] if phase == 'available' else CONTROLS[1:3] if phase == 'ready' else []))
    center_x, center_y = bounds['x'] + bounds['width'] / 2, bounds['y'] + bounds['height'] / 2
    for control in controls:
        selector = control['selector']
        if selector == '#update-check':
            need(control.get('color') == ink, 'update secondary action ignores the selected primary text tone')
        need(control.get('visible') is (selector in expected), 'update control visibility differs: ' + selector)
        if not control['visible']:
            continue
        need(control.get('hidden') is False and isinstance(control.get('label'), str) and control['label'].strip(),
             'visible update control lacks its accessible label')
        disabled = selector == '#update-check' and phase in ('downloading', 'installing')
        need(control.get('disabled') is disabled, 'update control disabled state differs')
        control_bounds = rect(control.get('bounds'))
        need(control_bounds['x'] >= bounds['x'] - 1.1 and control_bounds['y'] >= bounds['y'] - 1.1
             and N['right'](control_bounds) <= N['right'](bounds) + 1.1
             and N['bottom'](control_bounds) <= N['bottom'](bounds) + 1.1,
             'visible update control is outside the circle bounds')
        if selector in CONTROLS[4:]:
            N['near'](control_bounds['width'], control_bounds['height'], 'update close/minimize button is not square', 1.1)
            radius(control.get('radius'), control_bounds['width'], 'update close/minimize button')
        if not disabled:
            hit = control.get('hit', {})
            need(hit.get('ready') is True and finite(hit.get('x')) and finite(hit.get('y'))
                 and math.hypot(hit['x'] - center_x, hit['y'] - center_y) <= bounds['width'] / 2 + 1.1,
                 'enabled update control is not exposed to native input within the circle')
        if selector in CONTROLS[:4]:
            need(math.hypot(control_bounds['x'] + control_bounds['width'] / 2 - center_x,
                            control_bounds['y'] + control_bounds['height'] / 2 - center_y) >= bounds['width'] * .29,
                 'update action is not placed on the circular rim')
    return [
        {'name': 'update circle ring', 'point': {'x': bounds['x'] + bounds['width'] * .5,
                                               'y': bounds['y'] + bounds['height'] * .055}, 'expectedRGB': PALETTE[theme][0]},
        {'name': 'update circle core', 'point': {'x': bounds['x'] + bounds['width'] * .25,
                                               'y': bounds['y'] + bounds['height'] * .5}, 'expectedRGB': PALETTE[theme][1]},
    ]


def verify(value, owners, *, pid, platform, inputs, input_check, origin):
    need(value.get('schema') == 1 and value.get('version') == '6.0.37' and value.get('source') == SOURCE
         and value.get('visualStateFixture') is True and value.get('transportExercised') is False
         and value.get('installationExercised') is False and value.get('restored') is True and value.get('ok') is True,
         'update UI fixture identity/scope/restoration differs')
    samples = value.get('samples', [])
    need(isinstance(samples, list) and [sample.get('theme') for sample in samples] == ['light', 'dark'],
         'both update circle themes are required')
    need(isinstance(owners, list) and len(owners) == 2, 'update fixture owned native pair is absent')
    previous, witnesses = owners, {}
    for sample in samples:
        theme = sample['theme']
        need(sample.get('appearance') == 'square', 'update circle was not tested in square workspace mode')
        before, after = sample.get('before', {}), sample.get('after', {})
        need(all(isinstance(block.get('identities'), list) and len(block['identities']) == 2
                 and isinstance(block.get('native'), list) and len(block['native']) == 2 for block in (before, after)),
             'update before/after live native evidence is absent')
        for old, new, final, native_before, native_after in zip(previous, before['identities'], after['identities'], before['native'], after['native']):
            N['identity'](old, new, origin); N['identity'](new, final, origin)
            N['native'](native_before, new); N['native'](native_after, final)
        previous = after['identities']
        need(after.get('dialogOpen') is False, 'update modal did not close')
        dismiss = 'close' if theme == 'light' else 'minimize'
        need(sample.get('dismissAction') == dismiss, 'both native update dismiss controls are required')
        for field, selector in [('openInput', '#version-button'), ('dismissInput', CONTROLS[-1] if theme == 'light' else '#update-minimize')]:
            event = sample.get(field, {})
            need(event in inputs and event.get('selector') == selector and event.get('tabId') is None
                 and event.get('action') is None, 'native update action is absent from its process ledger or targets another control')
            input_check(event, platform, {pid})
        states = sample.get('states', [])
        need(isinstance(states, list) and [state.get('phase') for state in states] == PHASES,
             'all six update presentation phases are required in order')
        capture_phase = 'available' if theme == 'light' else 'ready'
        name = 'mouse-637-update-burrow-' + theme + '.png'
        need(sample.get('capture') == {'filename': name, 'phase': capture_phase}, 'update OS capture is bound to another state')
        for state in states:
            probes = presentation(state, state['phase'], theme)
            if state['phase'] == capture_phase:
                witnesses[name] = probes
    return {'witnesses': witnesses, 'summary': {'visualStateFixture': True, 'transportExercised': False,
            'installationExercised': False, 'bothThemes': True, 'sixPresentationPhases': True,
            'circleInSquareWorkspace': True, 'originalCenteredLogo': True, 'ringControls': True,
            'roundCloseAndMinimize': True, 'strongBackdropReadback': True, 'actualSurfacePixels': True,
            'trustedNativeOpenCloseMinimize': True, 'livePagesPreserved': True, 'stateRestored': True}}
