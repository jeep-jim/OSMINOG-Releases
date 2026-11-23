#!/usr/bin/env python3
"""Independent reader of installed 6.0.38 rendering and Web Store evidence.

No Electron process or success marker supplies the pixel verdict: PNGs, crop
geometry, input receipts, persistent identities and two process logs are read
again here. ``verify(read)`` also accepts an archive's bounded bytes reader.
"""
import argparse
import importlib.util
import io
import json
import math
import re
import subprocess
import urllib.parse
import zipfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location('mouse631_pixels', Path(__file__).with_name('mouse638-task-evidence.py'))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)
VERSION = '6.0.38'


def need(condition, message):
    if not condition:
        raise ValueError('Mouse638: ' + message)


def rgb(value):
    if isinstance(value, str) and re.fullmatch(r'#[0-9a-f]{6}', value, re.I):
        return [int(value[i:i + 2], 16) for i in (1, 3, 5)]
    match = re.match(r'^rgba?\((\d+),\s*(\d+),\s*(\d+)', value or '')
    need(match, 'missing actual computed RGB value')
    return [int(part) for part in match.groups()]


def image(read, name, sha, dimensions):
    need(isinstance(name, str) and re.fullmatch(r'mouse-638-[a-z0-9-]+\.png', name), 'unsafe image filename')
    blob = read(name)
    need(P.digest(blob) == sha, name + ' hash differs')
    result = P.decode_png(blob, name)
    P.size(dimensions, name)
    need(all(result[key] == dimensions[key] for key in ('width', 'height')), name + ' dimensions differ')
    return result


def close(a, b, tolerance=3):
    return len(a) == len(b) == 4 and a[3] == b[3] == 255 and all(abs(a[i] - b[i]) <= tolerance for i in range(3))


def point(mapping, value):
    need(isinstance(value, dict) and all(P.finite(value.get(k)) for k in ('x', 'y')), 'invalid CSS point')
    return tuple(math.floor(mapping['origin' + axis] + value[key] * mapping['scale' + axis]) for key, axis in (('x', 'X'), ('y', 'Y')))


def capture(read, value):
    need(value.get('source') == 'globalCapture.acquire(display)' and value.get('kind') == 'screen'
         and isinstance(value.get('backend'), str) and value['backend'], 'not an actual OS display capture')
    name = value.get('filename')
    result = image(read, name, value.get('sha256'), value.get('pixelSize'))
    need(value.get('displayFilename') == name[:-4] + '-display.png', 'wrong full display identity')
    full = image(read, value['displayFilename'], value.get('displaySha256'), value.get('screenPixelSize'))
    display = P.rectangle(value.get('display', {}).get('bounds'), 'native display')
    bounds = P.rectangle(value.get('contentBounds'), 'native window content')
    sx, sy = full['width'] / display['width'], full['height'] / display['height']
    left, top = (bounds['x'] - display['x']) * sx, (bounds['y'] - display['y']) * sy
    crop = {'x': math.floor(left), 'y': math.floor(top),
            'width': math.ceil(left + bounds['width'] * sx) - math.floor(left),
            'height': math.ceil(top + bounds['height'] * sy) - math.floor(top)}
    need(value.get('cropPixels') == crop and result['width'] == crop['width'] and result['height'] == crop['height'], 'incorrect native crop')
    mapping = {'scaleX': sx, 'scaleY': sy, 'originX': left - crop['x'], 'originY': top - crop['y']}
    need(all(P.finite(value.get('mapping', {}).get(k)) and abs(value['mapping'][k] - v) < 1e-8 for k, v in mapping.items()), 'incorrect native DPI mapping')
    need(crop['x'] >= 0 and crop['y'] >= 0 and crop['x'] + crop['width'] <= full['width'] and crop['y'] + crop['height'] <= full['height'], 'window lies outside captured display')
    # Verify pixels throughout the actual crop, independent of reported probes.
    for x in range(0, result['width'], max(1, result['width'] // 37)):
        for y in range(0, result['height'], max(1, result['height'] // 31)):
            need(P.pixel(result, x, y) == P.pixel(full, x + crop['x'], y + crop['y']), 'cropped PNG is not the actual full display region')
    return result, mapping


def verify_probe(image_value, mapping, actual, expected):
    for key in ('kind', 'point', 'expectedRGB'):
        need(actual.get(key) == expected[key], 'probe changes independent expected ' + key)
    x, y = point(mapping, expected['point'])
    need(actual.get('x') == x and actual.get('y') == y and actual.get('tolerance') == 3, 'probe changes DPI coordinate or tolerance')
    value = P.pixel(image_value, x, y)
    need(value == actual.get('actualRGBA'), 'claimed pixel differs from archived native PNG')
    need(close(value, expected['expectedRGB'] + [255]), 'native pixels fail ' + expected['kind'] + ' witness')


def native_geometry(value, content):
    need(all(value.get(k) is True for k in ('visible', 'parentVisible', 'cachedVisible', 'attached')), 'native content hidden or detached')
    bounds, view = P.rectangle(value.get('bounds'), 'native page'), P.rectangle(value.get('viewBounds'), 'native view')
    parent = value.get('parentBounds')
    if parent is not None:
        P.rectangle(parent, 'native clip parent')
    actual = {'x': view['x'] + (parent['x'] if parent else 0), 'y': view['y'] + (parent['y'] if parent else 0),
              'width': view['width'], 'height': view['height']}
    need(actual == bounds == value.get('actualBounds'), 'native hierarchy differs from recorded page bounds')
    need(bounds['x'] >= 0 and bounds['y'] >= 0 and bounds['x'] + bounds['width'] <= content['width']
         and bounds['y'] + bounds['height'] <= content['height'], 'native pane extends outside content')
    return bounds


def verify_grid(read, receipt, captures, identities):
    state = receipt.get('state', {})
    mode, theme = state.get('appearance', {}).get('paneMode'), state.get('theme')
    need(mode in ('square', 'rounded') and theme in ('dark', 'light'), 'unknown grid state')
    seam, gap, radius = ([53, 67, 87] if theme == 'dark' else [199, 207, 223]), (1 if mode == 'square' else 6), (0 if mode == 'square' else 12)
    need(state.get('gap') == gap and state.get('radius') == radius and rgb(state.get('seam')) == seam, 'wrong grid seam or radius')
    panes, dividers, native = state.get('panes', []), state.get('dividers', []), receipt.get('native', [])
    need(len(panes) == len(native) == 8 and len(dividers) == 7, 'eight real native panes and seven separators are required')
    need({n.get('tabId') for n in native} == set(identities), 'native pane owners changed')
    need({p.get('tabId') for p in panes} == set(identities), 'DOM pane owners changed')
    need(len({p.get('id') for p in panes}) == 8 and len({d.get('path') for d in dividers}) == 7, 'duplicate grid entries')
    screenshot = captures[receipt['capture']]
    pixels, mapping = capture(read, screenshot)
    expected = []
    for own in native:
        identity = identities[own['tabId']]
        need(all(own.get(k) == identity[k] for k in ('index', 'desk', 'webContentsId')), 'native identity changed')
        bounds = native_geometry(own, screenshot['contentBounds'])
        pane = next(p for p in panes if p['tabId'] == own['tabId'])
        pb = P.rectangle(pane.get('bounds'), 'DOM pane')
        need(all(float(v).is_integer() for v in pb.values()) and pane.get('radius') == radius, 'fractional DOM pane or wrong rounded edge')
        need(bounds == pane.get('slot'), 'native view and DOM slot have different edges')
        page_probes = [p for p in screenshot.get('probes', []) if p.get('kind') == 'page' and p.get('tabId') == own['tabId']]
        need(len(page_probes) == 2 and {p.get('part') for p in page_probes} == {0, 1}, 'each real page requires both owned content patches')
        for probe in sorted(page_probes, key=lambda p: p['part']):
            local = P.rectangle(probe.get('localBounds'), 'owned DOM colour region')
            need(local['y'] == 78 and local['height'] == 34 and abs(local['width'] / bounds['width'] - .36) < .002, 'page region is not the unchanged owned fixture')
            need(abs(local['x'] / bounds['width'] - (.08 if probe['part'] == 0 else .56)) < .002, 'page region position changed')
            expected.append({'kind': 'page', 'point': {'x': bounds['x'] + local['x'] + local['width'] / 2, 'y': bounds['y'] + local['y'] + local['height'] / 2}, 'expectedRGB': P.color(identity['index'], probe['part'])})
        for side in ('left', 'right'):
            expected.append({'kind': 'corner', 'point': {'x': pb['x'] + (1.5 if side == 'left' else pb['width'] - 1.5), 'y': pb['y'] + pb['height'] - 1.5}, 'expectedRGB': seam if mode == 'rounded' else [243, 240, 232]})
        if mode == 'rounded':
            for side in ('left', 'right'):
                points = ({'x': pb['x'] + (-.5 if side == 'left' else pb['width'] + .5), 'y': pb['y'] + pb['height'] - 1.5},
                          {'x': pb['x'] + (1.5 if side == 'left' else pb['width'] - 1.5), 'y': pb['y'] + pb['height'] + .5})
                for q in points:
                    if 0 <= q['x'] < screenshot['contentBounds']['width'] and 0 <= q['y'] < screenshot['contentBounds']['height']:
                        expected.append({'kind': 'corner-neighbor', 'point': q, 'expectedRGB': seam})
    for divider in dividers:
        b = P.rectangle(divider.get('bounds'), 'divider')
        axis = divider.get('axis')
        need(axis in ('x', 'y') and b['width' if axis == 'x' else 'height'] == gap, 'separator is not exactly the required CSS pixel width')
        for fraction in (.08, .3, .7, .92):
            expected.append({'kind': 'seam', 'point': {'x': b['x'] + b['width'] * (.5 if axis == 'x' else fraction), 'y': b['y'] + b['height'] * (.5 if axis == 'y' else fraction)}, 'expectedRGB': seam})
    probes = screenshot.get('probes', [])
    need(len(probes) == len(expected) and len(expected) >= (80 if mode == 'rounded' else 60), 'missing native grid/corner/separator/neighbour probes')
    for actual, wanted in zip(probes, expected):
        verify_probe(pixels, mapping, actual, wanted)
    need(len(receipt.get('identities', [])) == 8, 'grid identity samples missing')
    for after in receipt['identities']:
        P.verify_identity(identities[after['id']], after)
    return {'name': receipt['name'], 'pages': 8, 'nativePixelProbes': len(expected)}


def css_region(image_value, mapping, bounds):
    P.rectangle(bounds, 'visible glyph region')
    x0, y0 = point(mapping, {'x': bounds['x'], 'y': bounds['y']})
    x1, y1 = point(mapping, {'x': bounds['x'] + bounds['width'], 'y': bounds['y'] + bounds['height']})
    need(0 <= x0 < x1 <= image_value['width'] and 0 <= y0 < y1 <= image_value['height'], 'required text or image is clipped outside the actual screenshot')
    return [(x, y, P.pixel(image_value, x, y)) for y in range(y0, y1) for x in range(x0, x1)]


def verify_newtab(read, receipt, captures):
    state = receipt.get('state', {})
    need(state.get('background') == 'aurora' and 'gradient' in state.get('backgroundImage', ''), 'production aurora background missing')
    need(state.get('zoom') in (.8, 1, 1.25), 'unverified new-tab zoom')
    bounds = P.rectangle(state.get('bounds'), 'new tab')
    value = captures[receipt['capture']]
    pixels, mapping = capture(read, value)
    reference = value.get('reference', {})
    ref = image(read, reference.get('filename'), reference.get('sha256'), reference.get('pixelSize'))
    refmap = {'originX': 0, 'originY': 0, 'scaleX': ref['width'] / value['contentBounds']['width'], 'scaleY': ref['height'] / value['contentBounds']['height']}
    # The two outer columns span the whole start page. The reported corruption
    # painted an opaque dark rectangle over most of this area; these samples
    # must contain the real continuous production gradient on the OS display.
    background_count = 0
    for fx in (.04, .96):
        for fy in (.04, .18, .35, .5, .65, .82, .96):
            q = {'x': bounds['x'] + bounds['width'] * fx, 'y': bounds['y'] + bounds['height'] * fy}
            actual = P.pixel(pixels, *point(mapping, q))
            expected = P.pixel(ref, *point(refmap, q))
            need(min(expected[:3]) >= 35 and close(actual, expected, 12), 'new tab has a missing/opaque background region')
            background_count += 1
    regions = state.get('regions', [])
    text_regions = [r for r in regions if r.get('kind') == 'text']
    icons = [r for r in regions if r.get('kind') == 'icon']
    need(len(text_regions) >= 3 and len(icons) >= 1 and any('home-welcome' in r.get('className', '') for r in text_regions)
         and any('home-favorites-title' in r.get('className', '') for r in text_regions), 'new-tab headings, labels or icons missing')
    checked = []
    for region in regions:
        samples = css_region(ref, refmap, region['bounds'])
        levels = sorted(sum(v[:3]) / 3 for _, _, v in samples)
        need(levels and levels[-1] - levels[0] >= 20, 'compositor reference itself has a blank label or icon')
        if region['kind'] == 'text':
            need(region.get('text') and rgb(region.get('color')) == [255, 255, 255], 'unexpected new-tab label colour or content')
            foreground = [(x, y, v) for x, y, v in samples if min(v[:3]) >= 200 and sum(v[:3]) / 3 >= levels[len(levels) // 10] + 20]
        else:
            foreground = [(x, y, v) for x, y, v in samples if max(v[:3]) < 150]
        need(len(foreground) >= 3, 'reference has no readable foreground glyphs')
        matched = 0
        for x, y, expected in foreground:
            q = {'x': (x + .5) / refmap['scaleX'], 'y': (y + .5) / refmap['scaleY']}
            actual = P.pixel(pixels, *point(mapping, q))
            matched += close(actual, expected, 40)
        need(matched / len(foreground) >= .78, 'actual OS display loses the new-tab text or icon foreground')
        checked.append({'className': region['className'], 'kind': region['kind'], 'foregroundPixels': len(foreground), 'matchedPixels': matched})
    return {'name': receipt['name'], 'zoom': state['zoom'], 'backgroundSamples': background_count, 'regions': checked}


def verify_tone(read, receipt, captures):
    channel, name = receipt.get('channel'), receipt.get('name')
    need(channel in (160, 255), 'tone endpoint missing')
    appearance = receipt.get('appearance', {})
    need(appearance.get('theme') in ('dark', 'light') and appearance.get('whiteTone') in (0, 100), 'tone was not selected at an endpoint')
    wanted = 255 if appearance['theme'] == 'light' else 160 + round(95 * appearance['whiteTone'] / 100)
    need(channel == wanted, 'text tone does not follow the browser setting')
    state = receipt.get('pageTone', {})
    need(state.get('theme') == appearance['theme'] and state.get('whiteTone') == appearance['whiteTone']
         and rgb(state.get('color')) == [160 + round(95 * appearance['whiteTone'] / 100)] * 3, 'main reading preference differs')
    value = captures[receipt['capture']]
    pixels, mapping = capture(read, value)
    native = native_geometry(receipt.get('native', {}), value['contentBounds'])
    elements = {e['id']: e for e in receipt.get('dom', {}).get('elements', [])}
    expected = {'neutral-light': [channel] * 3, 'colored-link': [45, 145, 235], 'light-panel': [190] * 3, 'inherit-light': [255] * 3, 'inherit-blue': [255] * 3}
    if name in ('dynamic', 'maximum', 'light-theme-unchanged'):
        expected['dynamic-neutral'] = [channel] * 3
    results = []
    for ident, color in expected.items():
        element = elements.get(ident, {})
        need(rgb(element.get('color')) == color and rgb(element.get('fill')) == color, 'website colour or text-fill changed incorrectly: ' + ident)
        if ident in ('colored-link', 'light-panel', 'inherit-light', 'inherit-blue'):
            need(element.get('tag') != 'text', 'coloured text or light surface was selected for toning')
        elif appearance['theme'] == 'dark':
            need(element.get('tag') == 'text', 'eligible live website text was not marked')
        local = P.rectangle(element.get('bounds'), ident)
        region = {**local, 'x': native['x'] + local['x'], 'y': native['y'] + local['y']}
        samples = css_region(pixels, mapping, region)
        visible = sum(close(value, color + [255], 8) for _, _, value in samples)
        need(visible >= 12, 'actual OS display does not contain the required text glyph colour: ' + ident)
        results.append({'id': ident, 'nativeGlyphPixels': visible, 'rgb': color})
    media = P.rectangle(elements.get('media', {}).get('bounds'), 'excluded SVG')
    expected_probe = {'kind': 'media', 'point': {'x': native['x'] + media['x'] + media['width'] / 2, 'y': native['y'] + media['y'] + media['height'] / 2}, 'expectedRGB': [235, 40, 155]}
    need(len(value.get('probes', [])) == 2, 'media or inherited SVG exclusion witness missing')
    verify_probe(pixels, mapping, value['probes'][0], expected_probe)
    svg = elements.get('inherit-svg', {})
    sb = P.rectangle(svg.get('bounds'), 'currentColor SVG')
    need(rgb(svg.get('color')) == rgb(svg.get('fill')) == rgb(svg.get('svgFill')) == [255] * 3, 'currentColor SVG inherited the text tone')
    svg_probe = {'kind': 'currentColor-svg', 'point': {'x': native['x'] + sb['x'] + sb['width'] / 2, 'y': native['y'] + sb['y'] + sb['height'] / 2}, 'expectedRGB': [255] * 3}
    verify_probe(pixels, mapping, value['probes'][1], svg_probe)
    return {'name': name, 'glyphs': results, 'mediaUnchanged': True}


def verify_input(value, platform, pid):
    source = 'Cocoa' if platform == 'darwin' and value.get('action') == 'dialog-click' else {'darwin': 'CGEvent', 'win32': 'User32', 'linux': 'XTest'}[platform]
    need(value.get('pid') == pid and value.get('source') == source, 'input did not come from the real native process')
    events = value.get('events', [])
    if value.get('action') == 'click':
        need(any(e.get('type') == 'click' and e.get('trusted') is True and e.get('matches') is True for e in events), 'native click lacks a trusted matching DOM receipt')
    elif value.get('action') == 'drag':
        need(any(e.get('type') == 'pointerdown' and e.get('trusted') is True and e.get('matches') is True for e in events), 'drag did not begin with trusted native input')
        need(all(any(e.get('type') == kind and e.get('trusted') is True for e in events) for kind in ('pointermove', 'pointerup')), 'drag lacks native movement or release')
        need(value.get('from') != value.get('to'), 'drag never moved')
        before, after = value.get('before', []), value.get('after', [])
        need(len(before) == len(after) == 8, 'drag lost live native identities')
        for a, b in zip(before, after):
            P.verify_identity(a, b)
    elif value.get('action') == 'dialog-click':
        native = value.get('native', {})
        need(platform in ('darwin', 'win32') and native.get('pid') == pid and native.get('source') == source
             and native.get('title') == 'Установить расширение' and native.get('enabled') is not False, 'native permission button is not owned and enabled')
        bounds = P.rectangle(native.get('bounds'), 'native permission button')
        expected = {k: math.floor(bounds[k] + bounds['width' if k == 'x' else 'height'] / 2 + .5) for k in ('x', 'y')}
        need(value.get('point') == expected, 'permission input did not use actual native button bounds')
    elif value.get('action') == 'dialog-keys':
        native = value.get('native', {})
        need(platform == 'linux' and native.get('pid') == pid and native.get('source') == 'XTest'
             and native.get('nativeType') == '_NET_WM_WINDOW_TYPE_DIALOG' and native.get('transient') is True
             and isinstance(native.get('window'), str) and native['window'].isdigit() and native.get('title')
             and value.get('keys') == ['Tab', 'Return'], 'native Linux consent did not target the active owned transient dialog')
    else:
        raise ValueError('Mouse638: unknown native input action')


def processes(read, facts):
    value = json.loads(read('mouse-638-feedback-processes.json'))
    need(value.get('version') == VERSION and value.get('reportSha256') == P.digest(read('mouse-638-feedback.json')), 'native process receipt does not bind final evidence')
    write = json.loads(read('mouse-638-feedback-write.json'))
    need(write.get('writeComplete') is True and write.get('awaitingRestart') is True and write.get('ok') is False, 'write process was not awaiting an actual restart')
    for phase, marker in (('write', 'MOUSE_638_FEEDBACK_WRITE_PASS'), ('read', 'MOUSE_638_FEEDBACK_NATIVE_PASS')):
        item = value.get(phase, {})
        pid = facts['pid'] if phase == 'write' else facts['restart']['pid']
        need(item.get('pid') == pid and P.integer(pid, 1) and item.get('exitCode') == 0, 'native process identity or exit differs')
        need(P.finite(item.get('elapsedMs')) and 0 < item['elapsedMs'] <= (390000 if phase == 'write' else 210000), 'native phase budget exceeded')
        name = 'mouse-638-feedback-' + phase + '.log'
        log = read(name)
        need(item.get('log') == name and item.get('logSha256') == P.digest(log), 'native process log hash differs')
        lines = log.decode('utf-8', 'replace').splitlines()
        need(marker in lines and not any('MOUSE_638_FEEDBACK_FAIL' in line or 'MOUSE_NATIVE_PROCESS_TIMEOUT' in line for line in lines), 'native process did not complete the required phase')
        need(any(line.startswith(f'MOUSE_638_PROCESS_RETURN pid={pid} code=0 ') for line in lines), 'native runner did not observe the exact child exit')
        report = 'mouse-638-feedback-write.json' if phase == 'write' else 'mouse-638-feedback.json'
        need(item.get('report') == report and item.get('reportSha256') == P.digest(read(report)), 'native phase report bytes differ')
    need(facts['pid'] != facts['restart']['pid'] and write.get('pid') == facts['pid'], 'two distinct actual installed processes are required')
    for field in ('grid', 'newTabs', 'gridInitial', 'gridAfter', 'initial', 'profile', 'writePid'):
        need(facts.get(field) == write.get(field), 'read process rewrote write evidence: ' + field)
    return value


def verify_webstore_runtime(read, runtime, captures, ident, version):
    need(runtime.get('ownedResponse') == {'background': [250, 250, 250], 'color': [20, 20, 20], 'scripts': 0}, 'extension runtime page is not the unmodified script-free owned fixture')
    result = []
    for name, enabled in (('enabled', True), ('disabled', False), ('reenabled', True)):
        item = runtime.get(name, {})
        state = item.get('state', {})
        need(item.get('enabled') is enabled and state.get('url') == runtime.get('url')
             and state.get('originalBackground') == 'rgb(250, 250, 250)'
             and state.get('text') == 'Owned white page — Chrome extension runtime 638', 'runtime page identity changed')
        color = rgb(state.get('background'))
        if enabled:
            need(state.get('mode') == 'dynamic' and state.get('scheme') == 'dark'
                 and any(P.integer(style.get('bytes'), 1) for style in state.get('styles', []))
                 and all(c < 100 for c in color) and all(c > 100 for c in rgb(state.get('color'))), 'live Store content script did not execute')
        else:
            need(state.get('mode') is None and state.get('styles') == [] and color == [250, 250, 250], 'disabled Store extension still modifies the owned page')
        shot = captures[item['capture']]
        pixels, mapping = capture(read, shot)
        bounds = native_geometry(item.get('native', {}), shot['contentBounds'])
        local = P.rectangle(item.get('rect'), 'actual runtime content region')
        expected = {'kind': 'webstore-runtime', 'point': {'x': bounds['x'] + local['x'] + 24, 'y': bounds['y'] + local['y'] + local['height'] - 24}, 'expectedRGB': color}
        need(len(shot.get('probes', [])) == 1, 'native runtime witness missing')
        verify_probe(pixels, mapping, shot['probes'][0], expected)
        result.append({'phase': name, 'rgb': color, 'capture': item['capture']})
    action = runtime.get('action', {})
    need(action.get('id') == ident and action.get('version') == version and action.get('url', '').startswith('chrome-extension://' + ident + '/')
         and P.integer(action.get('buttons'), 1) and len(action.get('text', '')) > 40, 'the signed extension toolbar popup did not execute')
    shot = captures[action['capture']]
    capture(read, shot)
    full = image(read, shot['displayFilename'], shot['displaySha256'], shot['screenPixelSize'])
    display = shot['display']['bounds']
    bounds = P.rectangle(action.get('bounds'), 'actual extension popup')
    smap = {'originX': -display['x'] * full['width'] / display['width'], 'originY': -display['y'] * full['height'] / display['height'],
            'scaleX': full['width'] / display['width'], 'scaleY': full['height'] / display['height']}
    # Read a regular grid across the actual native popup. A blank/hidden popup
    # cannot be passed by a successful chrome.runtime JavaScript readback.
    levels = []
    for fx in (.1, .25, .5, .75, .9):
        for fy in (.1, .25, .5, .75, .9):
            levels.append(sum(P.pixel(full, *point(smap, {'x': bounds['x'] + bounds['width'] * fx, 'y': bounds['y'] + bounds['height'] * fy}))[:3]))
    need(max(levels) - min(levels) >= 45, 'actual native extension popup is blank')
    return result


def verify_webstore_install_control(read, installed, facts, captures, ident):
    # Google's page may deliberately hide/disable its Chrome-only button.
    # Require Mouse's real shell control and bind it to the owned Store guest;
    # diagnostics from Google's button/API do not authorize an installation.
    need(installed.get('installPath') == 'browser-control', 'Store installation did not use the production Mouse control')
    url = installed.get('storeURL', '')
    source = urllib.parse.urlsplit(url)
    need(source.scheme == 'https' and source.netloc == 'chromewebstore.google.com'
         and re.fullmatch(r'/detail/(?:[^/]+/)?' + re.escape(ident) + r'/?', source.path), 'installation did not originate in the real Store detail page')
    need(installed.get('storePage', {}).get('url') == url, 'real Store document differs from the installation source')
    owner = installed.get('storeOwner', {})
    need(isinstance(owner.get('tabId'), str) and owner['tabId'] and P.integer(owner.get('webContentsId'), 1)
         and owner.get('url') == url, 'owned Store page identity missing')
    native = owner.get('native', {})
    need(native.get('tabId') == owner['tabId'] and native.get('webContentsId') == owner['webContentsId'], 'Store guest differs from its owned native page')
    detail = captures[installed['storeCapture']]
    need(detail.get('pid') == facts['pid'] and installed.get('pid') == facts['pid'], 'Store detail belongs to another process')
    capture(read, detail)
    native_geometry(native, detail['contentBounds'])
    shell_id = installed.get('shellWebContentsId')
    need(P.integer(shell_id, 1) and shell_id != owner['webContentsId'], 'Mouse install control is not separate from the Store guest')
    control = installed.get('installControl', {})
    selector = '#mouse-extensions-install-page'
    need(control.get('selector') == selector and control.get('tabId') == owner['tabId']
         and control.get('managerOpen') is True and control.get('visible') is True and control.get('disabled') is False,
         'production Mouse install control was unavailable or targeted another page')
    bounds = P.rectangle(control.get('bounds'), 'Mouse installation control')
    shot = captures[control['capture']]
    need(shot.get('pid') == facts['pid'], 'Mouse install control belongs to another process')
    capture(read, shot)
    content = shot['contentBounds']
    need(bounds['x'] >= 0 and bounds['y'] >= 0 and bounds['x'] + bounds['width'] <= content['width']
         and bounds['y'] + bounds['height'] <= content['height'], 'Mouse installation control lies outside the native window')
    click = installed.get('installInput', {})
    need(click in facts.get('nativeInputs', []) and click.get('action') == 'click' and click.get('selector') == selector
         and 'tabId' in click and click['tabId'] is None, 'Mouse installation lacks a bound native shell click')
    verify_input(click, facts['platform'], facts['pid'])
    point_value = click.get('point', {})
    need(all(P.finite(point_value.get(k)) for k in ('x', 'y')), 'Mouse install native point missing')
    local = {k: point_value[k] - content[k] for k in ('x', 'y')}
    need(all(bounds[k] <= local[k] < bounds[k] + bounds['width' if k == 'x' else 'height'] for k in ('x', 'y')),
         'native install point misses the observed Mouse control')
    need(any(event.get('type') == 'click' and event.get('trusted') is True and event.get('matches') is True
             and event.get('selector') == selector
             and all(P.finite(event.get(k)) and abs(event[k] - local[k]) <= 1 for k in ('x', 'y'))
             for event in click.get('events', [])), 'trusted Mouse install event differs from the actual native point')
    bridge = installed.get('bridge', {})
    need(bridge.get('requestSource') == bridge.get('completionSource') == 'browser-control'
         and bridge.get('tabId') == owner['tabId'] and bridge.get('webContentsId') == owner['webContentsId']
         and bridge.get('nativeGestureWebContentsId') == shell_id, 'production installation did not bind the Mouse shell gesture to its Store guest')
    need(bridge.get('extensionId') == ident and bridge.get('url') == url and bridge.get('result') == 'success'
         and bridge.get('nativeGestureType') == 'mouseDown', 'production Store bridge did not complete the actual install request')
    for key in ('nativeGestureAt', 'beginAt', 'installedAt', 'completeAt'):
        need(P.integer(bridge.get(key), 1), 'Store bridge timestamp missing')
    need(P.integer(click.get('at'), 1) and bridge['nativeGestureAt'] <= bridge['beginAt'] <= bridge['installedAt'] <= bridge['completeAt']
         and abs(bridge['nativeGestureAt'] - click['at']) <= 2000, 'Store bridge was not initiated by the observed native user input')
    return bridge


def verify_webstore(read, facts):
    # Kept separate from owned unpacked-extension fixtures. The live helper's
    # receipt must identify Google's signed bytes and the real install UI.
    store = facts.get('webStore', {})
    installed, restored = store.get('write', {}), store.get('restart', {})
    need(installed.get('liveStore') is True and installed.get('installed') is True, 'live Chrome Web Store installation missing')
    need(restored.get('restored') is True and restored.get('removed') is True, 'live Store extension did not survive restart and clean up')
    signed = installed.get('evidence', {})
    ident = signed.get('id')
    need(isinstance(ident, str) and re.fullmatch(r'[a-p]{32}', ident), 'invalid Store extension identity')
    need(signed.get('developerVerified') is True and signed.get('publisherVerified') is True and signed.get('installedFilesVerified') is True, 'CRX3 or installed extension verification missing')
    need(isinstance(signed.get('sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', signed['sha256'])
         and P.integer(signed.get('bytes'), 1) and isinstance(signed.get('version'), str) and signed['version'], 'signed Store package identity is incomplete')
    need(signed.get('source') == 'chrome-web-store', 'extension came from an unpacked fixture')
    request, download = urllib.parse.urlsplit(signed.get('requestedURL', '')), urllib.parse.urlsplit(signed.get('downloadURL', ''))
    need(request.scheme == 'https' and request.netloc == 'clients2.google.com' and request.path == '/service/update2/crx'
         and download.scheme == 'https' and download.netloc in ('clients2.google.com', 'clients2.googleusercontent.com', 'clients.google.com', 'clients.googleusercontent.com'), 'live Store download origin missing')
    query = urllib.parse.parse_qs(request.query)
    need(query.get('acceptformat') == ['crx3'] and urllib.parse.parse_qs(query.get('x', [''])[0]).get('id') == [ident], 'Store request identifies another extension or unsigned format')
    need(installed.get('nativeInstallClick') is True and installed.get('nativeConsent') is True, 'live Store install and permission confirmation were not native input')
    need(installed.get('runtimeVerified') is True and restored.get('runtimeVerified') is True, 'extension did not execute in a real renderer before and after restart')
    need(restored.get('id') == ident and restored.get('sha256') == signed['sha256'], 'restored Store extension is not the verified installed package')
    artifact = signed.get('artifact', {})
    need(artifact.get('filename') == 'mouse-638-webstore.crx' and artifact.get('sha256') == signed['sha256'] and artifact.get('bytes') == signed['bytes'], 'original signed Store package was not archived')
    raw = read('mouse-638-webstore.crx')
    need(isinstance(raw, bytes) and len(raw) == signed['bytes'] and len(raw) <= 64 * 1024**2 and P.digest(raw) == signed['sha256'], 'archived Store package bytes differ')
    checked = subprocess.run(['node', str(Path(__file__).with_name('mouse-638-crx-proof.cjs')), '--id', ident],
                             input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, check=False)
    need(checked.returncode == 0, 'independent CRX3 cryptographic verification failed: ' + checked.stderr.decode('utf-8', 'replace')[-500:])
    proof = json.loads(checked.stdout)
    need(proof.get('id') == ident and proof.get('sha256') == signed['sha256'] and proof.get('bytes') == signed['bytes']
         and proof.get('developerVerified') is True and proof.get('publisherVerified') is True, 'independent CRX3 identity differs')
    with zipfile.ZipFile(io.BytesIO(raw[proof['archiveOffset']:])) as archive:
        manifest_info = archive.getinfo('manifest.json')
        need(manifest_info.file_size <= 256 * 1024, 'unbounded archived Store manifest')
        manifest = json.loads(archive.read(manifest_info))
        need(manifest.get('version') == signed['version'], 'installed Store version differs from the signed manifest')
    captures = {value['filename']: value for value in facts.get('captures', [])}
    bridge = verify_webstore_install_control(read, installed, facts, captures, ident)
    consent = installed.get('consent', {})
    need(consent.get('originalNativeDialog') is True and consent.get('response') == 1 and consent.get('buttons') == ['Отмена', 'Установить расширение']
         and consent.get('defaultId') == consent.get('cancelId') == 0 and consent.get('title') == 'Установить расширение из Chrome Web Store?'
         and consent.get('message') == 'Dark Reader ' + signed['version'], 'native permission dialog was replaced or did not consent')
    need(consent.get('input') in facts['nativeInputs'] and consent['input'].get('native') == consent.get('native'), 'native permission input is not bound to observed OS dialog')
    verify_input(consent['input'], facts['platform'], facts['pid'])
    need(consent.get('at', 0) <= consent['input'].get('at', 0) <= consent.get('resolvedAt', 0) <= bridge['installedAt'], 'permission confirmation order differs')
    capture(read, captures[consent['capture']])
    runtime = {'write': verify_webstore_runtime(read, installed.get('runtime', {}), captures, ident, signed['version']),
               'restart': verify_webstore_runtime(read, restored.get('runtime', {}), captures, ident, signed['version'])}
    need(restored.get('removeInput') in facts['nativeInputs'], 'restored live extension was not removed through its actual manager control')
    return {'id': ident, 'version': signed['version'], 'sha256': signed['sha256'], 'bytes': signed['bytes'], 'liveStore': True, 'restored': True, 'installPath': 'browser-control', 'independentCRX3': proof, 'runtime': runtime}


def verify(read, *, expected_platform=None, expected_arch=None):
    facts = json.loads(read('mouse-638-feedback.json'))
    need(facts.get('schema') == 1 and facts.get('version') == VERSION and facts.get('ok') is True and facts.get('restored') is True, 'native final report did not finish')
    need(facts.get('packaged') is True and facts.get('profileIsolated') is True and facts.get('physicalUserDeviceVerified') is False, 'installed/profile/verification scope differs')
    platform, arch = facts.get('platform'), facts.get('arch')
    need((platform, arch) in (('darwin', 'arm64'), ('win32', 'x64'), ('linux', 'x64')), 'unsupported native platform')
    need(expected_platform in (None, platform) and expected_arch in (None, arch), 'evidence came from the wrong native platform')
    processes(read, facts)
    initial, after = facts.get('gridInitial', []), facts.get('gridAfter', [])
    need(len(initial) == len(after) == 8 and len({v.get('id') for v in initial}) == 8, 'eight original live renderers missing')
    identities = {item['id']: item for item in initial}
    for before, current in zip(initial, after):
        P.verify_identity(before, current)
    values = facts.get('captures', [])
    captures = {value['filename']: value for value in values}
    need(len(captures) == len(values), 'duplicate capture identity')
    for value in values:
        need(value.get('pid') in (facts['pid'], facts['restart']['pid']), 'capture process was not observed')
    grid = facts.get('grid', [])
    names = {item.get('name') for item in grid}
    need(names == {'rounded-dark', 'rounded-light', 'square-light', 'square-dark', 'square-after-resize', 'square-after-swap', 'rounded-after-resize', 'rounded-after-swap'}, 'both themes, both shapes and actual drags must be captured')
    grids = [verify_grid(read, item, captures, identities) for item in grid]
    newtabs = facts.get('newTabs', [])
    need({item.get('name') for item in newtabs} == {'full-dark-first', 'full-dark-repeat', 'full-light', 'full-light-125', 'grid-light', 'grid-dark'}, 'new-tab full, tiled, repeated and zoomed paints are incomplete')
    starts = [verify_newtab(read, item, captures) for item in newtabs]
    need({item['zoom'] for item in starts} == {.8, 1, 1.25}, '80/100/125 percent new-tab coverage missing')
    tones = facts.get('tone', [])
    need({item.get('name') for item in tones} == {'minimum', 'dynamic', 'maximum', 'light-theme-unchanged', 'navigation', 'history-back', 'restored'}, 'live, dynamic, navigation, history or restart website-tone evidence missing')
    reading = [verify_tone(read, item, captures) for item in tones]
    by_name = {item['name']: item for item in tones}
    need(by_name['minimum']['dom']['identity'] == by_name['maximum']['dom']['identity'], 'changing white tone reloaded the site')
    need(by_name['navigation']['dom']['identity'] != by_name['minimum']['dom']['identity'], 'reload case did not navigate')
    need(facts.get('restart', {}).get('appearance') == {'theme': 'dark', 'appearance': {'paneMode': 'square', 'whiteTone': 0}, 'stored': {'paneMode': 'square', 'whiteTone': 0}}, 'appearance preference did not persist')
    inputs = facts.get('nativeInputs', [])
    need(inputs and all(item.get('pid') in (facts['pid'], facts['restart']['pid']) for item in inputs), 'native input receipts missing')
    for item in inputs:
        verify_input(item, platform, item['pid'])
    need({item.get('kind') for item in facts.get('drags', [])} == {'resize-square', 'swap-square', 'resize-rounded', 'swap-rounded'}, 'actual resize and pane movement not verified in both modes')
    need(sum(item.get('selector') == '#new-tab' for item in inputs) == len(newtabs), 'new tabs were not opened with native user input')
    webstore = verify_webstore(read, facts)
    need(facts.get('cleanup', {}).get('restored') is True, 'isolated native fixture cleanup failed')
    return {'ok': True, 'version': VERSION, 'platform': platform, 'arch': arch, 'grid': grids, 'newTabs': starts, 'readingTone': reading, 'webStore': webstore}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--platform', choices=('darwin', 'win32', 'linux'), required=True)
    parser.add_argument('--arch', choices=('arm64', 'x64'), required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    def read(name):
        need(isinstance(name, str) and Path(name).name == name, 'unsafe artifact name')
        return (directory / name).read_bytes()
    result = verify(read, expected_platform=args.platform, expected_arch=args.arch)
    (directory / 'mouse-638-acceptance.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('MOUSE_638_INDEPENDENT_NATIVE_ACCEPTANCE_PASS')


if __name__ == '__main__':
    main()
