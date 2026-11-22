#!/usr/bin/env python3
"""Independent sidebar dim, pointer passthrough and native/shell OS witnesses."""
from pathlib import Path
import re
import runpy

N = runpy.run_path(str(Path(__file__).with_name('mouse637-native-evidence.py')))
need, rect, finite = (N[k] for k in ('need', 'rect', 'finite'))
ORIGINAL = [37, 143, 191]
DIMMED = [round(value * .86) for value in ORIGINAL]
SOURCE = 'Owned native and browser-owned panes, real OS capture and trusted native clicks'


def state(value, *, enabled, kind, theme, owners, start, author):
    shell, guest, native = (value.get(key, {}) for key in ('readback', 'guest', 'native'))
    need(shell.get('theme') == theme and shell.get('dimmed') is enabled and shell.get('settingsOpen') is (kind == 'settings')
         and shell.get('libraryOpen') is (kind == 'library'), 'sidebar shell visibility/focus state differs')
    shell_mask = shell.get('mask', {})
    if enabled:
        need(shell_mask.get('pointerEvents') == 'none' and shell_mask.get('backgroundColor') == 'rgba(0, 0, 0, 0.14)'
             and shell_mask.get('content') not in (None, 'none'), 'browser-owned panes do not have the input-transparent requested dim')
    else:
        need(shell_mask.get('content') == 'none', 'browser-owned pane remains dimmed after closing')
    if theme == 'dark' and kind:
        toolbar = shell.get('toolbar', {})
        need(shell.get(kind) == toolbar and isinstance(toolbar.get('backgroundColor'), str)
             and isinstance(toolbar.get('backgroundImage'), str), 'dark sidebar does not share the actual toolbar surface')
        channels = re.fullmatch(r'rgba?\((\d+), (\d+), (\d+)(?:, [01](?:\.\d+)?)?\)', toolbar['backgroundColor'])
        need(channels and max(map(int, channels.groups())) < 100, 'dark sidebar background is unexpectedly bright')
    owned_start = shell.get('start', {})
    need(owned_start.get('id') == start and owned_start.get('internal') is True and owned_start.get('visible') is True, 'real browser-owned start page missing')
    slot = rect(owned_start.get('slotBounds'))
    shell_point = {'x': slot['x'] + 60, 'y': slot['y'] + 190}
    need(slot['width'] > 96 and slot['height'] > 206 and shell.get('witness') == {'point': shell_point, 'color': 'rgb(37, 143, 191)'}, 'browser-owned dim witness was moved or recolored')
    need(guest.get('buttonReceivesPoint') is True and guest.get('author') == author
         and guest.get('witness') == {'point': {'x': 60, 'y': 190}, 'color': 'rgb(37, 143, 191)'}, 'native dim changed author CSS or intercepted the real target')
    need(isinstance(native, list) and len(native) == 2, 'sidebar live native pair absent')
    for row, owner in zip(native, owners):
        N['native'](row, owner)
        need(row.get('dim') == {'requested': enabled, 'applied': enabled, 'pending': False, 'error': ''}, 'native page dim has not actually settled')
    viewport = guest.get('viewport', {})
    need(viewport.get('width') == native[0]['bounds']['width'] and viewport.get('height') == native[0]['bounds']['height'], 'native dim viewport differs from the attached page')
    if enabled:
        mask = guest.get('mask', {})
        need(mask.get('count') == 1 and mask.get('ariaHidden') == 'true' and mask.get('inert') is True
             and mask.get('closedShadow') is True and mask.get('pointerEvents') == mask.get('backdropPointerEvents') == 'none'
             and mask.get('popoverOpen') is True, 'native dim is not one hidden, input-transparent top layer')
        bounds = rect(mask.get('bounds'))
        for key, expected in {'x': 0, 'y': 0, 'width': viewport['width'], 'height': viewport['height']}.items():
            N['near'](bounds[key], expected, 'native dim must cover the exact viewport ' + key, 1.1)
    else:
        need(guest.get('mask') is None, 'native page keeps a stale dim layer')
    clicks = guest.get('clicks', [])
    need(isinstance(clicks, list) and all(row.get('trusted') is True and finite(row.get('at')) for row in clicks), 'native dim guest click log is untrusted')
    color = DIMMED if enabled else ORIGINAL
    return [
        {'name': 'owned native sidebar witness', 'tabId': owners[0]['id'], 'webContentsId': owners[0]['webContentsId'],
         'point': {'x': native[0]['bounds']['x'] + 60, 'y': native[0]['bounds']['y'] + 190}, 'expectedRGB': color},
        {'name': 'owned browser start witness', 'tabId': start, 'point': shell_point, 'expectedRGB': color},
    ]


def verify(value, owners, *, pid, platform, inputs, input_check, origin):
    need(value.get('schema') == 1 and value.get('ok') is True and value.get('opacity') == .14 and value.get('source') == SOURCE
         and value.get('csp') == "style-src 'self'", 'strict-CSP native sidebar focus proof absent')
    owned_origin = value.get('origin')
    need(isinstance(owned_origin, str) and re.fullmatch(r'http://127\.0\.0\.1:\d+', owned_origin), 'sidebar site is not an owned loopback fixture')
    samples = value.get('samples', [])
    need([sample.get('theme') for sample in samples] == ['light', 'dark'], 'sidebar both themes required')
    first = samples[0].get('before', {}).get('identities', [])
    need(len(first) == 2 and first[0].get('index') == 5 and first[1].get('index') == 1, 'sidebar strict-CSP and adjacent owned page identities missing')
    ownership = value.get('owners', {})
    need(ownership.get('primary') == first[0]['id'] and ownership.get('adjacent') == first[1]['id'] == owners[1]['id']
         and isinstance(ownership.get('start'), str) and ownership['start'] not in {row['id'] for row in owners + first}, 'sidebar page/start ownership differs')
    N['identity'](first[0], first[0], owned_origin); N['identity'](first[1], owners[1], origin)
    author = samples[0].get('before', {}).get('guest', {}).get('author')
    need(isinstance(author, dict) and author.get('filter') == 'contrast(1)' and author.get('before') == '"owned decoration"'
         and author.get('transform') in ('matrix(1, 0, 0, 1, 0, 0)', 'matrix3d(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)'), 'owned author CSS control is absent')
    witnesses, click_count, previous = {}, 0, first
    for sample in samples:
        before = sample.get('before', {}).get('identities', [])
        after = sample.get('after', {}).get('identities', [])
        need(len(before) == len(after) == 2, 'sidebar before/after document identities absent')
        for old, new, final, source in zip(previous, before, after, (owned_origin, origin)):
            N['identity'](old, new, source); N['identity'](new, final, source)
        previous = after
        need(len(sample['before'].get('guest', {}).get('clicks', [])) == click_count, 'sidebar fixture click counter reset')
        capture_names = sample.get('captures', {})
        for phase, kind, enabled in [('before', None, False), ('settings', 'settings', True), ('library', 'library', True), ('restored', None, False)]:
            block = sample['after' if phase == 'restored' else phase]
            name = 'mouse-637-sidebar-' + phase + '-' + sample['theme'] + '.png'
            need(capture_names.get(phase) == name, 'sidebar exact native capture missing')
            witnesses[name] = state(block, enabled=enabled, kind=kind, theme=sample['theme'], owners=before, start=ownership['start'], author=author)
            if not kind:
                continue
            for key, selector, tab_id in [('openInput', '#settings-button' if kind == 'settings' else '#history-button', None),
                                          ('clickInput', '#dim-click', first[0]['id']),
                                          ('closeInput', '#settings-dialog [data-close-dialog]' if kind == 'settings' else '#library-close', None)]:
                event = block.get(key, {})
                need(event in inputs and event.get('selector') == selector and event.get('tabId') == tab_id, 'sidebar native action belongs to another target')
                input_check(event, platform, {pid})
            click_count += 1
            need(block.get('clicks') == block.get('guest', {}).get('clicks') and len(block['clicks']) == click_count, 'native guest did not receive exactly one click through the dim layer')
        need(len(sample['after']['guest']['clicks']) == click_count, 'closing the sidebar changed its live guest click state')
    need(click_count == 4, 'all four sidebar native click-through cases required')
    return {'witnesses': witnesses, 'summary': {'bothThemes': True, 'nativeAndBrowserOwnedDim': True, 'nativePointerPassThrough': True, 'darkToolbarSurface': True, 'authorStylesPreserved': True}}
