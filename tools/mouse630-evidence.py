#!/usr/bin/env python3
"""Independent bounded evidence for Mouse 6.0.30.

Retains the reviewed 628 geometry/motion contracts and the accepted 629 Nora
wheel tutorial plus UI/scrollbar proof. Adds the independently checked header
pills, native downloads/capture feedback, closed-page wheel ownership and Nora
foreground/root/fractional/freshness proofs from the frozen 629 candidate.
No historical file or archived evidence is rewritten to satisfy this checker.
Local/progress, accepted tutorial/UI, and new 630 fixtures emit runtime 6.0.30;
borderless, motion and accepted desktop transitions keep schema version 6.0.28.
"""
import hashlib
import json
import math
import pathlib
import re
import runpy
import sys

REVIEWED_PATH = pathlib.Path(__file__).with_name('mouse628-evidence.py')
REVIEWED_SHA256 = 'd5c0f1a6275f54d4529ea5856f6240fb92f4d8d9b5fc69111adc7c3affb7fd46'
if hashlib.sha256(REVIEWED_PATH.read_bytes()).hexdigest() != REVIEWED_SHA256:
    raise ValueError('Reviewed Mouse628 evidence checker changed')
reviewed = runpy.run_path(str(REVIEWED_PATH), run_name='reviewed_mouse628_evidence')
image, display_crop = reviewed['image'], reviewed['display_crop']
decode_png, png_pixel = reviewed['decode_png'], reviewed['png_pixel']
ui_reviewed = runpy.run_path(str(pathlib.Path(__file__).with_name('mouse630-ui-evidence.py')),
                            run_name='retained_mouse630_ui_evidence')
TUTORIAL_JSON_NAME = 'mouse-629-swipe-tutorial.json'
UI_JSON_NAME = 'mouse-629-ui-regressions.json'
RETAINED_JSON_NAMES = tuple(TUTORIAL_JSON_NAME if name == 'mouse-628-swipe-tutorial.json'
                           else name for name in reviewed['JSON_NAMES'])
FEEDBACK_JSON_NAME = 'mouse-630-feedback-evidence.json'
WHEEL_JSON_NAME = 'mouse-630-wheel-pages.json'
NORA_JSON_NAME = 'mouse-630-nora-foreground.json'
JSON_NAMES = RETAINED_JSON_NAMES + (UI_JSON_NAME, FEEDBACK_JSON_NAME, WHEEL_JSON_NAME, NORA_JSON_NAME)
SUPERSEDED_MARKERS = {'MOUSE_628_THREE_FINGER_TUTORIAL_WRITE_PASS',
                      'MOUSE_628_THREE_FINGER_TUTORIAL_NATIVE_PASS'}
require_marker_set = set(reviewed['NATIVE_MARKERS'])
if not SUPERSEDED_MARKERS.issubset(require_marker_set):
    raise ValueError('Reviewed three-finger marker contract changed')
NATIVE_MARKERS = tuple(marker for marker in reviewed['NATIVE_MARKERS']
                       if marker not in SUPERSEDED_MARKERS) + (
    'MOUSE_630_DOWNLOAD_ACTIVITY_PASS', 'MOUSE_630_PRIVATE_DOWNLOAD_SCOPE_PASS',
    'MOUSE_630_CAPTURE_FEEDBACK_PASS', 'MOUSE_629_TWO_FINGER_WHEEL_TUTORIAL_WRITE_PASS',
    'MOUSE_629_TWO_FINGER_WHEEL_TUTORIAL_NATIVE_PASS',
    'MOUSE_630_NATIVE_WHEEL_DESKTOPS_PASS', 'MOUSE_630_PAGE_SCROLL_PRESERVED_PASS',
    'MOUSE_630_NORA_NATIVE_FOREGROUND_PASS', 'MOUSE_629_UI_REGRESSIONS_NATIVE_PASS')
EXPECTED_VERSIONS = {name: ('6.0.30' if name in ('mouse-628-local.json',
    'mouse-628-progress.json', TUTORIAL_JSON_NAME)
    else '6.0.28') for name in RETAINED_JSON_NAMES
    if name != 'mouse-628-motion-trace.json'}
WHEEL_SOURCE = 'webContents.sendInputEvent mouseWheel via Chromium trusted wheel event'
WHEEL_RECOGNIZER = 'horizontal-wheel-and-desktop-controls'
WHEEL_PACKET_ORIGIN = 'webContents.sendInputEvent mouseWheel through the real Chromium wheel listener'


def require(condition, message):
    if not condition:
        raise ValueError('Mouse630 evidence: ' + message)


def verify_retained(read):
    docs = {}
    for name in RETAINED_JSON_NAMES:
        raw = read(name)
        limit = 72 * 1024**2 if name.endswith('trace.json') else 16 * 1024**2
        require(0 < len(raw) <= limit, 'missing or oversized JSON ' + name)
        docs[name] = json.loads(raw)
    local, progress, border, motion, slides, swipe, trace = (docs[n] for n in RETAINED_JSON_NAMES)
    for name, doc in docs.items():
        if name != 'mouse-628-motion-trace.json':
            require(doc.get('version') == EXPECTED_VERSIONS[name], 'version mismatch: ' + name)

    require(local.get('status') == 'pass' and local.get('completed') is True and
            local.get('restored') is True and local.get('fixture') is True and
            local.get('physicalExternalModelVerified') is False, 'Local completion or scope')
    require(local.get('tools') == ['read_file', 'write_file', 'list_directory', 'search_files'] and
            local.get('protocol', {}).get('transport') == 'stdio' and
            local['protocol'].get('sdk') == '1.32.2' and
            local['protocol'].get('sandboxed') is False, 'packaged Local MCP protocol')
    require(len(local.get('denials', [])) >= 10 and len(local.get('fdRaces', [])) == 2 and
            local.get('outside', {}).get('beforeSha256') == local.get('outside', {}).get('afterSha256') and
            local.get('dev', {}).get('previousDead') is True and
            local['dev'].get('commandUnchanged') is True and local['dev'].get('stopped') is True and
            local.get('privacy', {}).get('serverDead') is True and
            local['privacy'].get('accessDenied') is True, 'Local bounds, revocation or dev lifecycle')
    captures = local.get('captures', [])
    require(len(captures) == 4 and
            {(v['theme'], v['view']) for v in captures} ==
            {(theme, view) for theme in ('light', 'dark') for view in ('overview', 'preview')},
            'Local theme/view capture matrix')
    for item in captures:
        require(item.get('source') == 'globalCapture.acquire(display)' and
                item.get('kind') == 'screen' and item.get('backend') and
                item['ui'].get('theme') == item['theme'] and
                item['ui']['preview'].get('readOnly') is True and
                item['readiness']['attempts'][-1].get('accepted') is True and
                all(not row['reasons'] for row in item['readiness']['attempts'] if row.get('accepted')),
                'Local capture provenance, visibility or current theme')
        display_crop(read, {'capture':item['filename'], 'screenCapture':item['screenCapture'],
                            'pixelSize':item['pixelSize'], 'screenPixelSize':item['screenPixelSize'],
                            'cropPixels':item['cropPixels']})
        image(read, item['readiness']['reference']['filename'], item['readiness']['reference']['pixelSize'])

    rows = progress.get('rows', [])
    require(progress.get('restored') is True and len(rows) == 4 and
            {(v['viewport'], v['theme']) for v in rows} ==
            {(viewport, theme) for viewport in ('large', 'small') for theme in ('light', 'dark')},
            'per-panel progress matrix/restoration')
    for row in rows:
        require(row['known'].get('globalRail') is False and
                [p['pill']['value'] for p in row['known']['panes']] == ['37%', '64%'] and
                [p['pill']['value'] for p in row['unknown']['panes']] == ['37%', '…'] and
                row['unknownTask'].get('percent') is None and
                row['capture'].get('source') == 'globalCapture.acquire(display)',
                'progress owner, known or unknown state')
        capture = row['capture']
        display_crop(read, {'capture':capture['filename'], 'screenCapture':capture['screenCapture'],
                            'pixelSize':capture['pixelSize'], 'screenPixelSize':capture['screenPixelSize'],
                            'cropPixels':capture['cropPixels']})
    require(progress.get('privacy', {}).get('privateState') is not None and
            progress.get('noraHold', {}).get('during') is not None and
            progress.get('ownershipSwap', {}).get('capture') is not None,
            'progress privacy, Nora hold or owner transfer')

    require(border.get('restored') is True and border.get('footerSeamAbsent') is True and
            border.get('decorativeOutlinesAbsent') is True and
            border.get('roundedBackgroundCorners') is True and len(border.get('rows', [])) == 24 and
            len(border.get('tinyBurrow', [])) == 2 and len(border.get('corners', [])) == 2,
            'borderless matrix/seam/corners')
    for row in border['rows']:
        sample = row['measurements']['sample']
        require(sample.get('fits') is True and sample.get('line') == 0 and
                row['measurements']['content'].get('scrollTop') == 0 and
                row['measurements']['panel'].get('scrollTop') == 0,
                'Nora content fit, footer seam or inner scrolling')
        image(read, row['capture'])
    for tiny in border['tinyBurrow']:
        require(tiny['pseudo'].get('display') == 'none' and tiny['button'].get('borderWidths') == [0]*4,
                'small Nora has a separate rim')
        image(read, tiny['capture'], tiny['pixelSize'])
    for corner in border['corners']:
        require(corner['theme'] == corner['actualTheme'] and len(corner.get('rows', [])) >= 1,
                'native corner theme/probes')
        for phase in ('before', 'open'):
            display_crop(read, corner['nativeCapture'][phase])

    flags = ('contentFit', 'noInnerScroll', 'translationOnly', 'strokeFreeContour',
             'openClosePainted', 'interruptionPreserved', 'reducedMotion',
             'backgroundStable', 'footerStable', 'stateRestored')
    require(motion.get('themes') == ['light', 'dark'] and all(motion.get(k) is True for k in flags),
            'Nora motion/shape facts')
    for theme in ('light', 'dark'):
        for phase in ('opening', 'closing'):
            painted = motion['captureStates'][theme][phase]['painted']
            require(painted.get('source') == 'beginFrameSubscription' and
                    painted['metadata'].get('strokeFree') is True,
                    'actual intermediate Nora presentation')
            frame = image(read, motion['captures'][theme][phase], painted['pixelSize'])
            metadata = painted['metadata']
            sy = frame['height']/metadata['geometry']['viewport']['height']
            near, far = max(2, round(2*sy)), max(6, round(6*sy))
            for probe in metadata['probes']:
                for key, dy in (('above',-near), ('edge',0), ('inside',near), ('lower',far)):
                    require(png_pixel(frame, probe['x'], probe['y']+dy) == probe[key],
                            'Nora recorded edge differs from archived presentation')
        image(read, motion['captures'][theme]['open'])
    require(slides.get('restored') is True and slides.get('noraStayedOpen') is True and
            slides.get('borrowedHold') is True and len(slides.get('transitions', [])) == 4,
            'open Nora desktop slide')
    for row in slides['transitions']:
        require(row.get('nativeLayoutCalls', 999) <= 8 and len(row.get('frames', [])) >= 3,
                'native desktop slide/layout budget')
        image(read, row['paintedFrame']['filename']) if row.get('paintedFrame') else None
    ui_reviewed['verify_gesture'](swipe, read)
    meta = trace.get('mouseMotionTrace', {})
    require(meta.get('complete') is True and meta.get('dataLossOccurred') is False and
            meta.get('limitedEvents') == 0 and meta.get('errors') == [] and
            meta.get('eventCount') == len(trace.get('traceEvents', [])),
            'lossless complete compositor trace')
    return {'version':'6.0.28', 'localCaptures':4, 'progressRows':4,
            'borderlessRows':24, 'desktopSlides':4, 'traceEvents':meta['eventCount']}


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def rectangle(value, label, viewport=None, edges=True):
    require(isinstance(value, dict) and all(finite(value.get(key)) for key in
            ('x', 'y', 'width', 'height')), label + ' has nonfinite geometry')
    require(0 < value['width'] <= 8192 and 0 < value['height'] <= 8192,
            label + ' has empty or oversized geometry')
    if edges:
        require(all(finite(value.get(key)) for key in ('right', 'bottom')) and
                abs(value['right']-value['x']-value['width']) <= .01 and
                abs(value['bottom']-value['y']-value['height']) <= .01,
                label + ' has inconsistent edges')
    if viewport is not None:
        require(value['x'] >= 0 and value['y'] >= 0 and
                value['x']+value['width'] <= viewport['width']+.01 and
                value['y']+value['height'] <= viewport['height']+.01,
                label + ' lies outside its viewport')
    return value


def viewport_size(value, label):
    require(isinstance(value, dict) and all(finite(value.get(key)) and
            0 < value[key] <= 8192 for key in ('width', 'height')),
            label + ' has invalid dimensions')
    return value


def exact_pane_map(ui, label):
    viewport_size(ui.get('viewport'), label + ' viewport')
    panes = ui.get('panes')
    require(isinstance(panes, list) and len(panes) == 2, label + ' must contain two panes')
    require(all(isinstance(p, dict) and isinstance(p.get('tabId'), str) and
                p['tabId'] and isinstance(p.get('pane'), str) and p['pane'] for p in panes),
            label + ' has invalid pane owners')
    require(len({p['tabId'] for p in panes}) == 2 and
            len({p['pane'] for p in panes}) == 2, label + ' repeats an owner')
    return {p['tabId']:p for p in panes}


def header_panes(ui, label, modal_hold=False):
    panes = exact_pane_map(ui, label)
    require(ui.get('globalRail') is False and ui.get('privateMode') is False,
            label + ' has a global progress rail or wrong session')
    for p in panes.values():
        bounds = rectangle(p['bounds'], label + ' pane', ui['viewport'])
        header = rectangle(p['header'], label + ' address row', ui['viewport'])
        slot = rectangle(p['slot'], label + ' page', ui['viewport'])
        dock = p.get('dock')
        require(isinstance(dock, dict) and dock.get('hidden') is False and
                dock.get('parentPane') == p['pane'], label + ' progress has the wrong parent')
        strip = rectangle(dock['bounds'], label + ' progress strip', ui['viewport'])
        pill = p.get('pill')
        require(isinstance(pill, dict) and pill.get('tabId') == p['tabId'] and
                pill.get('desk') == ui.get('desk') and pill.get('id'),
                label + ' progress does not belong to the visible native page')
        shape = rectangle(pill['bounds'], label + ' pill', ui['viewport'])
        dismiss = pill.get('dismiss', {})
        if modal_hold:
            require(dismiss.get('ready') is False and dismiss.get('reason') == 'covered or clipped' and
                    dismiss.get('lastHit') == 'dialog' and
                    all(finite(dismiss.get(k)) and dismiss[k] > 0 for k in ('width','height')),
                    label + ' modal Nora does not block background progress controls')
            clip, fragments = dismiss.get('clip', {}), dismiss.get('fragments')
            require(all(finite(clip.get(k)) and abs(clip[k]-shape[key]) <= 1 for k,key in
                    (('left','x'),('top','y'),('right','right'),('bottom','bottom'))) and
                    isinstance(fragments,list) and 1 <= len(fragments) <= 16 and
                    all(all(finite(fragment.get(k)) for k in ('left','top','width','height')) and
                        fragment['width'] > 0 and fragment['height'] > 0 and
                        fragment['left'] < clip['right'] and fragment['left']+fragment['width'] > clip['left'] and
                        fragment['top'] < clip['bottom'] and fragment['top']+fragment['height'] > clip['top']
                        for fragment in fragments), label + ' blocked dismiss lost its actual hit/clip geometry')
        else:
            require(dismiss.get('ready') is True, label + ' progress dismiss is not clickable')
        require(abs(header['y']-bounds['y']) <= 1 and
                abs(header['x']-bounds['x']) <= 1 and
                abs(header['width']-bounds['width']) <= 1 and header['height'] <= 96,
                label + ' address row is not at the top of its pane')
        require(abs(header['bottom']-strip['y']) <= 1 and
                abs(strip['bottom']-slot['y']) <= 1 and
                abs(strip['height']-28) <= 1 and abs(shape['height']-24) <= 1,
                label + ' pill is not immediately below its address row')
        require(abs(strip['x']-bounds['x']) <= 1 and
                abs(strip['width']-bounds['width']) <= 1 and
                abs(slot['x']-bounds['x']) <= 1 and
                abs(slot['width']-bounds['width']) <= 1 and
                abs(slot['bottom']-bounds['bottom']) <= 1,
                label + ' page no longer occupies its remaining pane')
        require(shape['x'] >= strip['x']+7 and shape['right'] <= strip['right']-7 and
                shape['y'] >= strip['y']+1 and shape['bottom'] <= strip['bottom']-1,
                label + ' pill lacks its compact side/vertical inset')
        require(finite(pill.get('radius')) and pill['radius'] >= shape['height']/2 and
                pill.get('borderWidth') == '0px' and pill.get('shadow') == 'none',
                label + ' pill is not rounded and borderless')
        require(finite(p.get('roundBottom')) and 0 <= p['roundBottom'] <= 24,
                label + ' has an invalid bottom radius')
    return panes


def static_native_pixels(read, capture, ui, regions, label):
    """Recompute shell/display agreement over the actual header pill pixels."""
    view = viewport_size(ui['viewport'], label + ' viewport')
    require(capture.get('source') == 'globalCapture.acquire(display)' and
            capture.get('kind') == 'screen' and isinstance(capture.get('backend'), str) and
            0 < len(capture['backend']) <= 80, label + ' has no native display provenance')
    content = rectangle(capture['contentBounds'], label + ' content bounds', edges=False)
    display_box = rectangle(capture['display']['bounds'], label + ' display bounds', edges=False)
    require(abs(content['width']-view['width']) <= .01 and
            abs(content['height']-view['height']) <= .01, label + ' content size differs')
    crop = image(read, capture['filename'], capture['pixelSize'])
    display = image(read, capture['screenCapture'], capture['screenPixelSize'])
    crop_box, mapping = capture['cropPixels'], capture['mapping']
    sx, sy = display['width']/display_box['width'], display['height']/display_box['height']
    left, top = (content['x']-display_box['x'])*sx, (content['y']-display_box['y'])*sy
    expected = {'x':math.floor(left), 'y':math.floor(top),
                'width':math.ceil(left+content['width']*sx)-math.floor(left),
                'height':math.ceil(top+content['height']*sy)-math.floor(top)}
    require(crop_box == expected and crop['width'] == expected['width'] and
            crop['height'] == expected['height'] and expected['x'] >= 0 and
            expected['y'] >= 0 and expected['x']+crop['width'] <= display['width'] and
            expected['y']+crop['height'] <= display['height'], label + ' native crop is inconsistent')
    expected_mapping = {'scaleX':sx, 'scaleY':sy, 'originX':left-expected['x'],
                        'originY':top-expected['y']}
    require(all(finite(mapping.get(k)) and abs(mapping[k]-v) <= .000001
                for k, v in expected_mapping.items()), label + ' has an invented pixel mapping')
    ready = capture.get('readiness', {})
    attempts = ready.get('attempts', [])
    require(ready.get('source') == 'current static shell readback matched to native display pixels' and
            isinstance(attempts, list) and 1 <= len(attempts) <= 20 and
            attempts[-1].get('accepted') is True and attempts[-1].get('reasons') == [] and
            all(a.get('sequence') == i+1 for i, a in enumerate(attempts)),
            label + ' has no bounded accepted native readback')
    ref = ready.get('reference', {})
    require(ref.get('source') == 'webContents.capturePage static shell UI only',
            label + ' reference source is not the current shell')
    reference = image(read, ref['filename'], ref['pixelSize'])
    rx, ry = reference['width']/view['width'], reference['height']/view['height']
    require(0 < sx <= 8 and 0 < sy <= 8 and 0 < rx <= 8 and 0 < ry <= 8,
            label + ' unsupported physical scale')
    compared = 0
    for bounds in regions:
        rectangle(bounds, label + ' native pill region', view)
        trim = min(1, bounds['width']/4, bounds['height']/4)
        x0, x1 = math.ceil((bounds['x']+trim)*rx), math.floor((bounds['right']-trim)*rx)
        y0, y1 = math.ceil((bounds['y']+trim)*ry), math.floor((bounds['bottom']-trim)*ry)
        require(0 < (x1-x0)*(y1-y0) <= 2_000_000, label + ' empty or oversized pixel region')
        colors = set()
        for y in range(y0, y1):
            for x in range(x0, x1):
                cx = math.floor(mapping['originX']+(x+.5)/rx*sx)
                cy = math.floor(mapping['originY']+(y+.5)/ry*sy)
                shell, actual = png_pixel(reference, x, y), png_pixel(crop, cx, cy)
                require(actual == png_pixel(display, cx+expected['x'], cy+expected['y']),
                        label + ' pill crop differs from its archived display')
                require(shell[3] == actual[3] == 255 and
                        all(abs(a-b) <= 2 for a, b in zip(shell[:3], actual[:3])),
                        label + ' native header pixels differ from the shell')
                if len(colors) < 3:
                    colors.add(tuple(actual))
                compared += 1
        require(len(colors) >= 3, label + ' header pill is not painted')
    return compared


def verify_headers(read, progress):
    rows = progress['rows']
    require(len(rows) == 4, 'missing progress size/theme matrix')
    pixel_count = 0
    for i, row in enumerate(rows):
        label = 'progress row ' + str(i)
        before = exact_pane_map(row['before'], label + ' before')
        for phase in ('known', 'unknown'):
            ui = row[phase]
            panes = header_panes(ui, label + ' ' + phase)
            require(set(panes) == set(before) and ui['theme'] == row['theme'] and
                    ui['footer'] == row['before']['footer'] and
                    ui['bodyRows'] == row['before']['bodyRows'],
                    label + ' changed owners, theme or the application footer')
            for tab_id, p in panes.items():
                old = before[tab_id]
                require(p['bounds'] == old['bounds'] and p['header'] == old['header'] and
                        p['roundBottom'] == old['roundBottom'],
                        label + ' changed panel/header bounds or erased bottom rounding')
                rectangle(old['slot'], label + ' empty page', row['before']['viewport'])
                require(abs(p['slot']['height']+p['dock']['bounds']['height']-old['slot']['height']) <= 1,
                        label + ' did not reserve exactly the header strip height')
        pixel_count += static_native_pixels(read, row['capture'], row['known'],
            [p['pill']['bounds'] for p in row['known']['panes']], label)
    hold = progress['noraHold']
    original = header_panes(hold['before'], 'Nora before')
    snapshots = hold.get('snapshots')
    require(isinstance(snapshots, list) and len(snapshots) == 2 and
            {s.get('tabId') for s in snapshots} == set(original), 'Nora snapshot owners differ')
    for phase in ('held', 'during', 'after'):
        current = header_panes(hold[phase], 'Nora ' + phase, modal_hold=phase in ('held','during'))
        require(set(current) == set(original), 'Nora changed progress owners')
        for tab_id, p in current.items():
            old = original[tab_id]
            require(p['slot'] == old['slot'] and p['dock']['bounds'] == old['dock']['bounds'] and
                    p['roundBottom'] == old['roundBottom'], 'Nora changed header progress geometry')
    for snapshot in snapshots:
        p = original[snapshot['tabId']]
        require(str(snapshot.get('roundBottom')) == str(p['roundBottom']),
                'Nora lost rounded page corners below the header pill')
        for key in ('width', 'height'):
            value = snapshot.get(key)
            require(isinstance(value, str) and re.fullmatch(r'\d+(?:\.\d+)?px', value) and
                    abs(float(value[:-2])-p['slot'][key]) <= .01,
                    'Nora snapshot size differs from the real page slot')
    swap = progress['ownershipSwap']
    before_swap, after_swap = header_panes(swap['before'], 'before swap'), header_panes(swap['after'], 'after swap')
    require(set(before_swap) == set(after_swap), 'swapping panes lost a task owner')
    for tab_id, p in after_swap.items():
        require(p['pane'] != before_swap[tab_id]['pane'] and
                p['pill']['id'] == before_swap[tab_id]['pill']['id'],
                'progress did not follow its original native tab through the swap')
    pixel_count += static_native_pixels(read, swap['capture'], swap['after'],
        [p['pill']['bounds'] for p in swap['after']['panes']], 'swapped header progress')
    return {'rows':4, 'nativePillPixels':pixel_count, 'noraPaneCornersChecked':2, 'ownerSwap':2}


def sha256_value(value, label):
    require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value),
            label + ' is not a SHA-256')
    return value


def recorded_image(read, item, label):
    require(item.get('source') == 'BrowserWindow.capturePage',
            label + ' must identify its real shell/editor capture source')
    require(hashlib.sha256(read(item['file'])).hexdigest() ==
            sha256_value(item.get('sha256'), label + ' hash'), label + ' bytes differ from their hash')
    return image(read, item['file'], item['pixelSize'])


def nonnegative_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 2**53-1


def download_geometry(ui, native, label):
    view = viewport_size(ui.get('viewport'), label + ' viewport')
    pill = ui.get('pill')
    require(isinstance(pill, dict) and pill.get('hidden') is False and
            pill.get('tabId') == native.get('tabId'), label + ' download is hidden or owned by another page')
    shape = rectangle(pill['bounds'], label + ' pill', view, edges=False)
    head = rectangle(ui['head'], label + ' address row', view, edges=False)
    slot = rectangle(ui['slot'], label + ' page slot', view, edges=False)
    actual = rectangle(native['bounds'], label + ' native page', view, edges=False)
    require(abs(shape['height']-24) <= 1 and
            1 <= shape['y']-head['y']-head['height'] <= 3 and
            abs(slot['y']-head['y']-head['height']-28) <= 1 and
            shape['x'] >= head['x']+7 and
            shape['x']+shape['width'] <= head['x']+head['width']-7,
            label + ' download pill is not compactly inset below its address row')
    require(all(abs(actual[key]-slot[key]) <= 1.5 for key in ('x', 'y', 'width', 'height')) and
            actual['y'] >= shape['y']+shape['height']-1,
            label + ' native page overlaps or fails to follow the progress strip')
    rectangle(ui['footer']['bounds'], label + ' download control', view, edges=False)
    return shape


def painted_region(frame, bounds, view, label):
    sx, sy = frame['width']/view['width'], frame['height']/view['height']
    require(0 < sx <= 8 and 0 < sy <= 8, label + ' invalid bitmap scale')
    x0, y0 = math.ceil((bounds['x']+1)*sx), math.ceil((bounds['y']+1)*sy)
    x1 = math.floor((bounds['x']+bounds['width']-1)*sx)
    y1 = math.floor((bounds['y']+bounds['height']-1)*sy)
    require(0 <= x0 < x1 <= frame['width'] and 0 <= y0 < y1 <= frame['height'] and
            (x1-x0)*(y1-y0) <= 2_000_000, label + ' invalid pixel region')
    colors = set()
    for y in range(y0, y1):
        for x in range(x0, x1):
            value = png_pixel(frame, x, y)
            require(value[3] == 255, label + ' is not opaque rendered UI')
            colors.add(tuple(value))
            if len(colors) >= 3:
                return
    require(False, label + ' has no rendered detail')


def motion_media(value, label):
    require(isinstance(value,dict) and isinstance(value.get('before'),bool) and
            value.get('normal') is False and isinstance(value.get('restored'),bool) and
            value['restored'] is value['before'],
            label + ' normal-motion fixture did not restore the measured initial media preference')


def feedback_state(value, state, label, reduced=False):
    require(isinstance(value,dict) and value.get('reducedMotion') is reduced,
            label + ' recorded the wrong actual media preference')
    require(isinstance(value, dict) and value.get('state') == state and
            value.get('hidden') is (state is None), label + ' has the wrong confirmation state')
    if state is None:
        return
    rectangle(value['badgeBounds'], label + ' badge', edges=False)
    require(value.get('animationName') == ('none' if reduced else 'mouse-capture-confirm'),
            label + ' has the wrong motion mode')
    require(value.get('bladeDisplay') == 'none' if reduced else
            value.get('bladeDisplay') not in (None, 'none'), label + ' shutter visibility differs')
    if not reduced:
        require(value.get('bladeAnimationName') == 'mouse-capture-shutter' and
                isinstance(value.get('bladeTransform'),str) and len(value['bladeTransform']) <= 512 and
                value['bladeTransform'].startswith(('matrix(', 'matrix3d(')),
                label + ' has no actual shutter animation/translation')


def copy_plateau_sample(value, label):
    """Observe one live CSS animation without accepting a replayed cue."""
    feedback_state(value, 'copy', label)
    view = viewport_size(value.get('viewport'), label + ' viewport')
    rectangle(value.get('badgeBounds'), label + ' badge', view, edges=False)
    require(finite(value.get('sampledAt')) and value['sampledAt'] >= 0 and
            finite(value.get('timeOrigin')) and value['timeOrigin'] > 0,
            label + ' lacks its actual renderer clock')
    opacity = value.get('badgeOpacity')
    require(isinstance(opacity, str) and re.fullmatch(r'\d+(?:\.\d+)?', opacity) and
            .99 <= float(opacity) <= 1, label + ' is not fully visible')
    animations = value.get('badgeAnimations')
    require(isinstance(animations, list) and 1 <= len(animations) <= 16 and
            all(isinstance(animation, dict) for animation in animations),
            label + ' lacks bounded actual animation observations')
    matching = [animation for animation in animations
                if animation.get('animationName') == 'mouse-capture-confirm']
    require(len(matching) == 1, label + ' does not identify one confirmation animation')
    animation = matching[0]
    require(finite(animation.get('startTime')) and animation['startTime'] >= 0 and
            finite(animation.get('currentTime')) and 224 <= animation['currentTime'] <= 1064 and
            animation.get('playState') == 'running' and
            animation.get('timing', {}).get('duration') == 1400,
            label + ' is outside the unchanged 1400ms animation visibility plateau')
    return animation


def verify_copy_attempt(capture, frame):
    attempt, copied = capture.get('copyAttempt'), capture['copied']
    require(isinstance(attempt, dict) and attempt.get('source') ==
            'one actual copy export and one BrowserWindow.capturePage during the natural CSS visibility plateau',
            'copy confirmation lacks its single native readback observation')
    barrier = attempt.get('barrier')
    require(isinstance(barrier, dict) and barrier.get('reason') == 'plateau',
            'copy confirmation did not reach its natural visibility plateau')
    before, after = barrier.get('before'), attempt.get('after')
    first = copy_plateau_sample(before, 'copy before readback')
    last = copy_plateau_sample(after, 'copy after readback')
    require(after['timeOrigin'] == before['timeOrigin'] and
            after['sampledAt'] >= before['sampledAt'] and
            last['startTime'] == first['startTime'] and last['currentTime'] >= first['currentTime'] and
            after['viewport'] == before['viewport'],
            'copy readback crossed a different renderer, restarted animation or reversed clock')
    samples = barrier.get('samples')
    require(isinstance(samples, list) and 1 <= len(samples) <= 128 and all(
            isinstance(sample, dict) and sample.get('timeOrigin') == before['timeOrigin'] and
            finite(sample.get('sampledAt')) and 0 <= sample['sampledAt'] <= before['sampledAt']
            for sample in samples) and all(a['sampledAt'] <= b['sampledAt']
            for a, b in zip(samples, samples[1:])) and
            (samples[-1] == before or len(samples) == 128),
            'copy plateau barrier lacks its bounded chronological renderer samples')
    keys = ('copyStartedAt', 'copyResolvedAt', 'requestedAt', 'receivedAt', 'afterSampledAt', 'encodedAt')
    require(finite(attempt.get('mainTimeOrigin')) and attempt['mainTimeOrigin'] > 0 and
            all(finite(attempt.get(key)) and attempt[key] >= 0 for key in keys) and
            all(attempt[a] <= attempt[b] for a, b in zip(keys, keys[1:])),
            'copy native readback, renderer observation or PNG encoding ran out of order')
    require(attempt.get('result') == copied['result'] and copied['feedback'] == before and
            attempt.get('frame') == copied['frame'] and
            all(copied['frame'].get(key) == attempt[key]
                for key in ('mainTimeOrigin', 'requestedAt', 'receivedAt', 'encodedAt')) and
            all(attempt.get(key) == copied.get(key) for key in
                ('changedRegion', 'changedPixels', 'changedRegionUnits', 'changedTolerance', 'changedAlgorithm')),
            'copy plateau observation is not bound to the same export, PNG, clocks and pixel comparison')
    bounds, view = before['badgeBounds'], before['viewport']
    sx, sy = frame['width']/view['width'], frame['height']/view['height']
    require(0 < sx <= 8 and 0 < sy <= 8, 'copy confirmation bitmap has an invalid scale')
    expected = {'x':max(0, math.floor(bounds['x']*sx)),
                'y':max(0, math.floor(bounds['y']*sy)),
                'width':min(frame['width']-math.floor(bounds['x']*sx), math.ceil(bounds['width']*sx)),
                'height':min(frame['height']-math.floor(bounds['y']*sy), math.ceil(bounds['height']*sy))}
    require(copied.get('changedRegion') == expected,
            'copy PNG comparison does not cover the actually observed confirmation badge')


def verify_retry_lifecycle(downloads, native_by_id, events):
    """A native restart can reset counters; prior delivery and done stay required."""
    failures = [event for event in events if event['case'] == 'retry' and event['state'] == 'error']
    completions = [event for event in events if event['case'] == 'retry' and event['state'] == 'completed']
    require(len(failures) == len(completions) == 1, 'retry must expose one actual error and one fresh completion')
    failed, completed = failures[0], completions[0]
    require(failed['activity']['id'] != completed['activity']['id'] and
            all(finite(row.get('at')) and row['at'] > 0 for row in (failed,completed)),
            'retry did not retain two distinct native lifecycle samples')
    failed_group = native_by_id[failed['activity']['id']]
    completed_group = native_by_id[completed['activity']['id']]
    terminal = failed_group[-1]
    require(terminal.get('event') == 'done' and terminal.get('nativeState') == 'interrupted' and
            terminal['received'] == failed['activity']['received'] and
            max(0,terminal['total']) == failed['activity']['total'] and
            terminal['activity'].get('state') == 'error', 'retry error counters do not match the actual terminal DownloadItem')
    partial = [event for event in failed_group[:-1] if event['event'] == 'updated' and
               event.get('nativeState') == 'progressing' and event['total'] == 1048576 and
               0 < event['received'] <= 65536]
    require(failed_group[0]['total'] == 1048576 and partial,
            'retry error has no earlier actual native partial delivery of the known file')
    requests = downloads.get('httpRequests')
    require(isinstance(requests,list) and 3 <= len(requests) <= 2048 and all(
            isinstance(row,dict) and row.get('case') in ('known','unknown','retry','normal-unknown','private-unknown') and
            finite(row.get('at')) and row['at'] > 0 and row.get('status') in (200,404) and
            nonnegative_integer(row.get('sentBytes')) and row['sentBytes'] <= 1048576 and
            isinstance(row.get('aborted'),bool) and (row.get('range') is None or
                isinstance(row['range'],str) and 0 < len(row['range']) <= 256)
            for row in requests), 'retry has no bounded actual HTTP request record')
    retry_requests = [row for row in requests if row['case'] == 'retry']
    require(3 <= len(retry_requests) <= 128 and all(a['at'] <= b['at']
            for a,b in zip(retry_requests,retry_requests[1:])), 'retry HTTP lifecycle order differs')
    first, last = retry_requests[0], retry_requests[-1]
    rejected = retry_requests[1:-1]
    require(first['status'] == 200 and first['aborted'] is True and first['sentBytes'] == 65536 and
            all(row['status'] == 404 and row['aborted'] is False and row['sentBytes'] == 0 for row in rejected) and
            last['status'] == 200 and last['aborted'] is False and last['sentBytes'] == 1048576,
            'retry HTTP proof lacks the truncated 200, real 404 and explicit full 200')
    require(first['at'] <= failed_group[0]['at'] <= partial[0]['at'] <= terminal['at'] and
            rejected[-1]['at'] <= terminal['at'] <= failed['at'] <= last['at'] <= completed_group[0]['at'] and
            completed_group[-1]['at'] <= completed['at'],
            'explicit retry HTTP request did not follow the observed native error')


def verify_feedback(read, facts):
    require(facts.get('version') == '6.0.30' and facts.get('platform') == 'darwin' and
            facts.get('arch') == 'arm64' and facts.get('source') ==
            'actual Electron DownloadItem events and capture/export IPC' and
            facts.get('restored') is True and not facts.get('error') and not facts.get('cleanupError') and
            not facts.get('motionCleanupError'),
            'feedback evidence lacks the restored installed arm64 run')
    downloads = facts['downloads']
    native_events, events = downloads.get('nativeEvents'), downloads.get('events')
    require(isinstance(native_events, list) and 6 <= len(native_events) <= 2048 and
            isinstance(events, list) and 9 <= len(events) <= 64, 'download event bounds')
    native_by_id = {}
    cases = {'known', 'unknown', 'retry', 'normal-unknown', 'private-unknown'}
    for event in native_events:
        activity = event.get('activity', {})
        require(event.get('case') in cases and event.get('scope') ==
                ('private' if event['case'] == 'private-unknown' else 'normal') and
                event.get('event') in ('will-download', 'updated', 'done') and
                finite(event.get('at')) and nonnegative_integer(event.get('received')) and
                (nonnegative_integer(event.get('total')) or event.get('total') == -1 and
                 ('unknown' in event['case'] or event['case'] == 'retry' and event.get('nativeState') == 'interrupted')),
                'native DownloadItem event has invalid provenance or bytes')
        require(isinstance(activity.get('id'), str) and activity['id'] and activity.get('tabId') and
                activity.get('desk') and activity.get('received') == event['received'] and
                activity.get('total') == max(0, event['total']), 'native activity differs from its DownloadItem')
        native_by_id.setdefault(activity['id'], []).append(event)
    for group in native_by_id.values():
        require(group[0]['event'] == 'will-download' and
                len({event['case'] for event in group}) == 1 and
                len({(event['activity']['tabId'], event['activity']['desk']) for event in group}) == 1 and
                all(a['at'] <= b['at'] for a, b in zip(group, group[1:])),
                'native download lifecycle changed identity, ownership or event order')
    observed = set()
    for event in events:
        case, state, activity, task = event['case'], event['state'], event['activity'], event['task']
        require(case in cases and state in ('paused', 'downloading', 'completed', 'cancelled', 'error') and
                state == activity.get('state') == task.get('downloadState'), 'download state chain differs')
        observed.add((case, state))
        require(activity.get('id') in native_by_id and
                native_by_id[activity['id']][0]['case'] == case and
                task.get('source') == 'download' and task.get('kind') == 'download' and
                task.get('id') == 'download:'+activity['id'] and task.get('taskId') == activity['id'] and
                task.get('privateMode') is (case == 'private-unknown') and task.get('estimated') is False and
                task.get('tabId') == activity['tabId'] == event['native'].get('tabId') and
                task.get('desk') == activity['desk'], 'download task ownership or session differs')
        require(all(nonnegative_integer(activity.get(k)) for k in ('received', 'total')),
                'download task bytes are not exact nonnegative integers')
        if case in ('known', 'retry') and not (case == 'retry' and state == 'error'):
            require(activity['total'] == 1048576 and 0 < activity['received'] <= activity['total'],
                    'known-size fixture lost its Content-Length or transferred byte count')
        if state == 'completed':
            require(activity['received'] == activity['total'] == 1048576,
                    'completion was reported before the full known payload arrived')
        expected = 100 if state == 'completed' else min(100, activity['received']/activity['total']*100) if activity['total'] else None
        require((task.get('percent') is None if expected is None else
                 finite(task.get('percent')) and abs(task['percent']-expected) <= .0000001),
                'download percentage does not derive from actual byte counts')
        phase = {'completed':'completed', 'cancelled':'stopped', 'error':'error'}.get(state, 'running')
        require(task.get('phase') == phase, 'download terminal state was reported as success')
        pill = event.get('ui', {}).get('pill', {})
        require(pill.get('state') == phase and pill.get('tabId') == activity['tabId'],
                'rendered download phase or owner differs from the actual task')
        if expected is not None:
            require(isinstance(pill.get('ariaNow'), str) and
                    re.fullmatch(r'\d+(?:\.\d+)?', pill['ariaNow']) and
                    abs(float(pill['ariaNow'])-expected) <= .0000001 and
                    pill.get('value') == str(math.floor(expected+.5))+'%',
                    'rendered known download percentage differs from native bytes')
        else:
            require(pill.get('ariaNow') is None and pill.get('value') == '…',
                    'unknown native total invented a rendered percentage')
        group = native_by_id[activity['id']]
        require(any(e['activity']['received'] == activity['received'] and
                    e['activity']['total'] == activity['total'] for e in group),
                'renderer download bytes never occurred on the native DownloadItem')
        if state in ('completed', 'cancelled', 'error'):
            native_state = {'completed':'completed', 'cancelled':'cancelled', 'error':'interrupted'}[state]
            require(any(e['event'] == 'done' and e['nativeState'] == native_state and
                        e['received'] == activity['received'] and e['activity']['total'] == activity['total'] and
                        e['activity'].get('state') == state for e in group),
                    'download terminal task/counters lack the corresponding actual done event')
        if 'unknown' in case:
            require(activity['total'] == 0 and expected is None and
                    event['ui']['pill']['ariaNow'] is None and event['ui']['pill']['value'] == '…',
                    'unknown download invented a total, percentage or completion')
        if state == 'downloading':
            require(activity['received'] > 0 and event['ui']['footer']['count'] >= 1,
                    'download activity has no transferred bytes or visible activity count')
            download_geometry(event['ui'], event['native'], case + ' running')
    require({('known','paused'), ('known','downloading'), ('known','completed'),
             ('unknown','downloading'), ('unknown','cancelled'), ('retry','error'),
             ('retry','completed'), ('private-unknown','downloading'),
             ('private-unknown','cancelled')}.issubset(observed), 'download lifecycle cases are incomplete')
    retry_ids = {e['activity']['id'] for e in events if e['case'] == 'retry'}
    require(len(retry_ids) == 2, 'retry reused the interrupted native download identity')
    verify_retry_lifecycle(downloads,native_by_id,events)
    files = downloads.get('files')
    expected_sha = hashlib.sha256(bytes([71])*1048576).hexdigest()
    require(isinstance(files, list) and len(files) == 2 and {f.get('case') for f in files} == {'known', 'retry'},
            'completed download file proofs are missing')
    for result in files:
        require(result.get('bytes') == result.get('expectedBytes') == 1048576 and
                result.get('sha256') == result.get('expectedSha256') == expected_sha,
                'downloaded file bytes differ from the actual served fixture')
    screenshots = downloads.get('screenshots')
    require(isinstance(screenshots, list) and len(screenshots) == 2 and
            {s.get('theme') for s in screenshots} == {'light', 'dark'}, 'download screenshot theme matrix')
    for shot in screenshots:
        require(shot.get('case') == 'known', 'download screenshot has no known transfer')
        frame = recorded_image(read, shot, 'download '+shot['theme'])
        shape = download_geometry(shot['ui'], shot['native'], 'download '+shot['theme'])
        painted_region(frame, shape, shot['ui']['viewport'], 'download '+shot['theme'])
    privacy = facts['privacy']
    before, during, after, disposed = (privacy[k] for k in ('before', 'privateDuring', 'normalAfter', 'privateDisposed'))
    normal_ids = {item['id'] for item in before['items']}
    private_ids = {item['id'] for item in during['items']}
    require(normal_ids and private_ids and normal_ids.isdisjoint(private_ids) and
            set(privacy['normalIds']) == normal_ids and before.get('privateMode') is False and
            during.get('privateMode') is True and after.get('privateMode') is False and
            disposed.get('privateMode') is True and disposed.get('items') == [] and
            private_ids.isdisjoint(item['id'] for item in after['items']), 'normal/private download stores are not isolated')
    private_tasks = privacy.get('privateTasks')
    require(isinstance(private_tasks, list) and private_tasks and
            all(t.get('privateMode') is True and t.get('source') == 'download' and
                t.get('taskId') in private_ids for t in private_tasks), 'private renderer exposes a foreign download')
    normal_live = {e['activity']['id'] for e in native_events if e['case'] == 'normal-unknown'}
    require(normal_live and normal_live.issubset(normal_ids) and
            normal_live.issubset({item['id'] for item in after['items']}), 'normal live download was lost across private mode')
    capture = facts['capture']
    motion_media(capture.get('motionMedia'),'capture editor')
    feedback_state(capture['acquired'], 'capture', 'capture acquisition')
    before_image = recorded_image(read, capture['before'], 'editor before confirmation')
    copied, saved = capture['copied'], capture['saved']
    require(copied.get('result', {}).get('ok') is True and saved.get('result', {}).get('ok') is True,
            'capture confirmation preceded a successful actual export')
    feedback_state(copied['feedback'], 'copy', 'clipboard confirmation')
    feedback_state(saved['feedback'], 'save', 'file confirmation')
    after_image = recorded_image(read, copied['frame'], 'editor confirmation')
    verify_copy_attempt(capture, after_image)
    require((before_image['width'], before_image['height']) == (after_image['width'], after_image['height']),
            'editor confirmation changed the viewport size')
    region = copied.get('changedRegion', {})
    require(copied.get('changedRegionUnits') == 'pixels' and copied.get('changedTolerance') == 0 and
            copied.get('changedAlgorithm') == 'any RGB channel differs' and
            all(nonnegative_integer(region.get(k)) for k in ('x','y','width','height')) and
            0 < region['width']*region['height'] <= 1_000_000 and
            region['x']+region['width'] <= after_image['width'] and
            region['y']+region['height'] <= after_image['height'], 'invalid confirmation pixel comparison')
    changed = sum(png_pixel(before_image, x, y)[:3] != png_pixel(after_image, x, y)[:3]
                  for y in range(region['y'], region['y']+region['height'])
                  for x in range(region['x'], region['x']+region['width']))
    require(changed > 20 and copied.get('changedPixels') == changed,
            'confirmation pixel change does not match the archived editor PNGs')
    canvas_raw, clipboard_raw, saved_raw = (read(name) for name in
        (copied['canvasFile'], copied['clipboardFile'], saved['savedFile']))
    canvas_sha, clipboard_sha = hashlib.sha256(canvas_raw).hexdigest(), hashlib.sha256(clipboard_raw).hexdigest()
    require(canvas_sha == copied.get('canvasSha256') == saved.get('canvasSha256') == saved.get('fileSha256') and
            clipboard_sha == copied.get('clipboardSha256') and canvas_raw == saved_raw,
            'exported PNG acquired shutter pixels or differs from the saved bytes')
    canvas_image, clipboard_image = image(read, copied['canvasFile']), image(read, copied['clipboardFile'])
    require((canvas_image['width'], canvas_image['height']) == (clipboard_image['width'], clipboard_image['height']) and
            sha256_value(copied.get('canvasBitmapSha256'), 'canvas bitmap') ==
            sha256_value(copied.get('clipboardBitmapSha256'), 'clipboard bitmap'), 'clipboard bitmap identity differs')
    if canvas_image['channels'] == clipboard_image['channels']:
        require(canvas_image['pixels'] == clipboard_image['pixels'], 'clipboard decoded pixels differ from the exported canvas')
    else:
        require(all(png_pixel(canvas_image, x, y) == png_pixel(clipboard_image, x, y)
                    for y in range(canvas_image['height']) for x in range(canvas_image['width'])),
                'clipboard decoded pixels differ from the exported canvas')
    require(capture['cancelled'].get('result', {}).get('canceled') is True and
            'deliberate export failure' in capture['failed'].get('result', {}).get('error', ''),
            'cancelled/failed exports were not exercised')
    feedback_state(capture['cancelled']['feedback'], None, 'cancelled export')
    feedback_state(capture['failed']['feedback'], None, 'failed export')
    require(capture['reducedMotion'].get('matches') is True, 'reduced motion was not active')
    feedback_state(capture['reducedMotion'], 'copy', 'reduced motion confirmation', reduced=True)
    global_capture = capture['global']
    require(global_capture.get('source') == 'synthetic input frame, real native editor and export IPC',
            'global editor fixture must not claim a physical external capture')
    motion_media(global_capture.get('motionMedia'),'global capture editor')
    feedback_state(global_capture['initialFeedback'], 'capture', 'global editor acquisition')
    feedback_state(global_capture['saveFeedback'], 'save', 'global editor save')
    require(global_capture.get('reducedMotion',{}).get('matches') is True,
            'global editor reduced motion was not active')
    feedback_state(global_capture['reducedMotion'],'copy','global editor reduced motion',reduced=True)
    return {'nativeDownloadItems':len(native_by_id), 'downloadEvents':len(native_events),
            'downloadFiles':2, 'downloadThemes':2, 'confirmationChangedPixels':changed,
            'exportBytesUnchanged':True, 'privateStoresIsolated':True}


def wheel_observations(events, label, axis, trusted=True):
    require(isinstance(events,list) and 1 <= len(events) <= 500,
            label + ' has no bounded observed Chromium wheel events')
    other = 'deltaY' if axis == 'x' else 'deltaX'
    component = 'deltaX' if axis == 'x' else 'deltaY'
    for event in events:
        require(isinstance(event,dict) and event.get('isTrusted') is trusted and
                event.get('deltaMode') == 0 and all(finite(event.get(k)) and
                abs(event[k]) <= 32768 for k in ('deltaX','deltaY')) and
                event[other] == 0 and event[component] != 0,
                label + ' is not the recorded trusted pixel wheel route')
    meaningful = [event[component] for event in events if abs(event[component]) >= 4]
    require(meaningful and all(value*meaningful[0] > 0 for value in meaningful),
            label + ' has no consistent observed gesture after calibration')
    return meaningful


def wheel_inputs(events, label, axis, count, precise):
    require(isinstance(events,list) and count <= len(events) <= count+1,
            label + ' has missing or excess native input, including calibration')
    component, other = ('deltaX','deltaY') if axis == 'x' else ('deltaY','deltaX')
    for event in events:
        require(event.get('type') == 'mouseWheel' and event.get('canScroll') is True and
                event.get('hasPreciseScrollingDeltas') is precise and
                all(nonnegative_integer(event.get(k)) and event[k] <= 8192 for k in ('x','y')) and
                finite(event.get('at')) and event['at'] > 0 and
                all(finite(event.get(k)) and abs(event[k]) <= 1024 for k in ('deltaX','deltaY')) and
                event[other] == 0 and event[component] != 0,
                label + ' lacks actual bounded native mouseWheel input')
    require(all(a['at'] <= b['at'] for a,b in zip(events,events[1:])),
            label + ' native input timestamps go backwards')
    meaningful = [event for event in events if abs(event[component]) >= 4]
    calibration = [event for event in events if abs(event[component]) < 4]
    require(len(meaningful) == count and (not calibration or
            len(calibration) == 1 and calibration[0] is events[0] and abs(calibration[0][component]) == 2),
            label + ' native burst/calibration does not match its recorded fixture')
    require(all(event[component]*meaningful[0][component] > 0 for event in meaningful),
            label + ' native gesture input changes direction')
    return meaningful


def wheel_packet(dispatch, label, surface, before, after, observed, origin=False):
    require(isinstance(dispatch,dict) and dispatch.get('channel') == 'mouse:desktop-swipe' and
            finite(dispatch.get('at')) and dispatch['at'] > 0 and
            (not origin or dispatch.get('origin') == WHEEL_PACKET_ORIGIN),
            label + ' lacks the real native gesture dispatch')
    packet = dispatch.get('packet', {})
    require(packet.get('source') == 'trusted-wheel' and packet.get('surface') == surface and
            isinstance(packet.get('id'),str) and 0 < len(packet['id']) <= 128 and
            isinstance(packet.get('from'),str) and packet['from'] == before and
            isinstance(packet.get('to'),str) and packet['to'] == after and before != after and
            packet.get('direction') in ('left','right'), label + ' gesture owner/direction/source differs')
    require(isinstance(packet.get('tabId'),str) and (0 < len(packet['tabId']) <= 128
            if surface == 'page' else packet['tabId'] == ''), label + ' page/shell ownership differs')
    gesture = packet.get('gesture', {})
    axis = gesture.get('axis')
    require(axis in ('x','y') and (axis == 'x' or surface in ('control','nora')) and
            gesture.get('direction') == packet['direction'] and
            nonnegative_integer(gesture.get('count')) and (2 if axis == 'x' else 1) <= gesture['count'] <= 256 and
            finite(gesture.get('distance')) and (112 if axis == 'x' else 64) <= gesture['distance'] <= 1024*gesture['count'] and
            finite(gesture.get('startedAt')) and gesture['startedAt'] > 0,
            label + ' has no thresholded accumulated wheel gesture')
    values = wheel_observations(observed,label+' observed',axis)
    sign = 1 if packet['direction'] == 'left' else -1
    require(all(value*sign > 0 for value in values) and gesture['count'] <= len(values) and
            abs(sum(min(1024,abs(value)) for value in values[:gesture['count']])-gesture['distance']) <= .001,
            label + ' accumulated distance/count differs from actual Chromium deltas')
    return packet


def verify_nora_transitions(slides, tutorial):
    # The accepted Nora route records nora-wheel on each dispatch. Its retained
    # transition document deliberately has schema version 628, not app version.
    require(slides.get('version') == '6.0.28' and
            tutorial.get('source') == 'nora-wheel' and
            tutorial.get('recognizer') == 'two-finger-or-wheel' and
            all(slides.get(key) is True for key in ('simultaneous','pngSurfaces','compositorOnly',
                'nativeIdentityPreserved','viewportAndScrollPreserved','slowAckBounded','noraStayedOpen')),
            'retained desktop transition did not exercise the accepted Nora wheel route')
    successes = [row for row in tutorial['records'] if row['kind'] == 'successful-native-switch']
    require(len(slides.get('transitions', [])) == len(successes) == 4,
            'accepted Nora tutorial and desktop transitions differ in count')
    for transition, record in zip(slides['transitions'],successes):
        require(record.get('dispatch', {}).get('packet', {}).get('source') == 'nora-wheel' and
                all(transition.get(key) == record.get(key) for key in ('theme','direction','before','after')) and
                transition.get('pageBefore') == transition.get('pageAfter') and
                isinstance(transition.get('pageBefore'),list) and len(transition['pageBefore']) == 2 and
                all(page.get('scrollX') == 0 and page.get('scrollY') == 137 for page in transition['pageBefore']),
                'accepted Nora tutorial does not match retained native desktop identity/scroll proof')


def verify_wheel_pages(read, facts):
    require(facts.get('version') == '6.0.30' and facts.get('source') == WHEEL_SOURCE and
            facts.get('recognizer') == WHEEL_RECOGNIZER and facts.get('physicalTwoFingerDeviceVerified') is False and
            facts.get('restored') is True and not facts.get('error') and not facts.get('cleanupError') and
            isinstance(facts.get('electronVersion'),str) and re.fullmatch(r'\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?',facts['electronVersion']) and
            facts.get('limits') == {'horizontalThreshold':112,'controlThreshold':64,'quietMs':280,'cooldownMs':420},
            'wheel input provenance, physical verification claim, limits or restoration differs')
    case_names = ('verticalPage','horizontalScroller','pageHandledWheel','contentEditable','closedPage',
                  'shellControl','boundary','privateClosedPage')
    cases, packets, inputs, observed = (facts.get(key) for key in ('cases','packets','inputs','observed'))
    require(isinstance(cases,dict) and set(cases) == set(case_names)|{'forgedDOM','duplicateBurst'} and
            isinstance(packets,list) and len(packets) == 3 and
            isinstance(inputs,list) and 33 <= len(inputs) <= 41 and
            isinstance(observed,list) and len(observed) == len(case_names) and
            [item.get('case') for item in observed] == list(case_names) and
            all(item.get('case') in case_names for item in inputs), 'wheel input/case/dispatch inventory differs')
    normal_id = cases['verticalPage']['before']['desktopId']
    switched_id = cases['closedPage']['after']['desktopId']
    require(isinstance(normal_id,str) and isinstance(switched_id,str) and normal_id != switched_id,
            'closed Nora wheel did not reach an adjacent desktop')
    expected_range = dict(zip(case_names,((0,0),(0,0),(0,0),(0,0),(0,1),(1,2),(2,2),(2,3))))
    wc_ids, packet_ids = {}, []
    for name, observed_row in zip(case_names,observed):
        case = cases[name]
        before, after = case.get('before',{}), case.get('after',{})
        require(all(isinstance(state.get('desktopId'),str) and state['desktopId'] and
                state.get('noraOpen') is False and state.get('switching') is False and
                state.get('gesture',{}).get('supported') is True and state['gesture'].get('running') is False
                for state in (before,after)), name + ' altered Nora state or did not settle')
        start,end = expected_range[name]
        require(case.get('packetIndex') == start and case.get('packetEndIndex') == end and
                case.get('packetCount') == end-start, name + ' emitted an extra or missing desktop dispatch')
        axis = 'y' if name in ('verticalPage','shellControl') else 'x'
        native_count = 8 if name == 'closedPage' else 1 if name == 'shellControl' else 4
        precise = axis == 'x'
        sent = [event for event in inputs if event['case'] == name]
        real_sent = wheel_inputs(sent,name,axis,native_count,precise)
        expected_amount = 50 if name == 'verticalPage' else 55 if name in (
            'horizontalScroller','pageHandledWheel','contentEditable') else 80 if name == 'shellControl' else 32
        component = 'deltaX' if axis == 'x' else 'deltaY'
        require(all(abs(event[component]) == expected_amount for event in real_sent), name + ' native deltas differ')
        wc = observed_row.get('webContentsId')
        require(nonnegative_integer(wc) and wc > 0 and all(event.get('webContentsId') == wc for event in sent) and
                observed_row.get('events') == case.get('observed'), name + ' observed a different native WebContents')
        wc_ids[name] = wc
        values = wheel_observations(case.get('observed'),name,axis)
        direction = -1 if name in ('boundary','shellControl') else 1
        require(all(value*direction > 0 for value in values), name + ' Chromium direction differs')
        if end == start:
            require(before['desktopId'] == after['desktopId'] == normal_id,
                    name + ' changed desktop while page input should remain local')
        else:
            packet = wheel_packet(packets[start],name,'control' if name == 'shellControl' else 'page',
                                  before['desktopId'],after['desktopId'],case['observed'])
            packet_ids.append(packet['id'])
            result = after['gesture'].get('lastResult',{})
            require(after['gesture'].get('learned') is True and
                    result == {'id':packet['id'],'from':packet['from'],'to':packet['to'],'completed':True},
                    name + ' did not finish its native dispatch')
    require(len(set(packet_ids)) == 3 and len({wc_ids[name] for name in (
            'verticalPage','horizontalScroller','pageHandledWheel','contentEditable','closedPage','boundary')}) == 1 and
            len({wc_ids['closedPage'],wc_ids['shellControl'],wc_ids['privateClosedPage']}) == 3 and
            packets[0]['packet']['tabId'] != packets[2]['packet']['tabId'],
            'normal, shell or private native input owners are mixed')
    require(cases['closedPage']['before']['desktopId'] == normal_id and
            cases['shellControl']['before']['desktopId'] == switched_id and
            cases['shellControl']['after']['desktopId'] == normal_id,
            'closed-page and shell-control gestures do not switch to opposite adjacent desktops')
    for name,before_key,after_key in (('verticalPage','beforeScrollY','afterScrollY'),
                                    ('horizontalScroller','beforeScrollLeft','afterScrollLeft')):
        require(finite(cases[name].get(before_key)) and finite(cases[name].get(after_key)) and
                0 <= cases[name][before_key] < cases[name][after_key] <= 3200,
                name + ' failed to preserve actual content scrolling')
    require(any(event.get('defaultPrevented') is True for event in cases['pageHandledWheel']['observed']),
            'page-owned preventDefault was not exercised')
    forged = cases['forgedDOM']
    require(forged.get('before') == forged.get('after') and forged['before']['desktopId'] == normal_id and
            forged.get('packetIndex') == forged.get('packetEndIndex') == forged.get('packetCount') == 0 and
            len(forged.get('observed',[])) == 6,
            'forged DOM wheel changed native gesture state or dispatched')
    wheel_observations(forged['observed'],'forged DOM','x',trusted=False)
    duplicate = cases['duplicateBurst']
    require(duplicate.get('packetCount') == 1 and duplicate.get('inputCount') == 8 and
            duplicate.get('before') == cases['closedPage']['before'] and
            duplicate.get('after') == cases['closedPage']['after'], 'duplicate native burst switched more than once')
    private, privacy = cases['privateClosedPage'], facts.get('privacy',{})
    require(private['before']['gesture'].get('learned') is False and
            private.get('normalPersisted') == {'completed':True} and private.get('privatePersisted') is None and
            privacy.get('normalBefore') == privacy.get('normalAfter') == {'completed':True} and
            privacy.get('privateDisposed') == {'storeDestroyed':True,'tabCount':0,'webContentsDestroyed':True},
            'private wheel learning leaked to storage or retained its native session')
    require(facts.get('capture',{}).get('file') == 'mouse-630-wheel-desktops.png' and
            facts['capture'].get('source') == 'BrowserWindow.capturePage', 'wheel shell capture provenance differs')
    image(read,facts['capture']['file'])
    return {'cases':10,'nativeDispatches':3,'pageScrollRoutes':4,'privateSessionDisposed':True,
            'physicalTwoFingerDeviceVerified':False}


def native_display_images(read, metadata, viewport, label):
    """Decode the archived OS plane and verify its exact lossless window crop."""
    view = viewport_size(viewport, label + ' viewport')
    display_box = rectangle(metadata['display']['bounds'], label + ' display', edges=False)
    content = rectangle(metadata['contentBounds'], label + ' content', edges=False)
    require(content['width'] == view['width'] and content['height'] == view['height'] and
            isinstance(metadata.get('backend'), str) and 0 < len(metadata['backend']) <= 80,
            label + ' native source dimensions/backend are missing')
    display = image(read, metadata['source'], metadata['pixelSize'])
    box = metadata['cropPixels']
    require(all(nonnegative_integer(box.get(k)) for k in ('x','y','width','height')),
            label + ' crop is not in physical integer pixels')
    crop = image(read, metadata['capture'], {'width':box['width'], 'height':box['height']})
    sx, sy = display['width']/display_box['width'], display['height']/display_box['height']
    left, top = (content['x']-display_box['x'])*sx, (content['y']-display_box['y'])*sy
    expected = {'x':math.floor(left), 'y':math.floor(top),
                'width':math.ceil(left+content['width']*sx)-math.floor(left),
                'height':math.ceil(top+content['height']*sy)-math.floor(top)}
    require(box == expected and 0 < sx <= 8 and 0 < sy <= 8 and
            box['x']+box['width'] <= display['width'] and box['y']+box['height'] <= display['height'],
            label + ' crop does not come from the measured display/content geometry')
    mapping = metadata['mapping']
    require(all(finite(mapping.get(k)) and abs(mapping[k]-v) <= .000001 for k,v in
            {'scaleX':sx,'scaleY':sy,'originX':left-box['x'],'originY':top-box['y']}.items()),
            label + ' native pixel mapping differs')
    for y in sorted({0,crop['height']//4,crop['height']//2,crop['height']*3//4,crop['height']-1}):
        for x in sorted({0,crop['width']//4,crop['width']//2,crop['width']*3//4,crop['width']-1}):
            require(png_pixel(crop,x,y) == png_pixel(display,x+box['x'],y+box['y']),
                    label + ' PNG crop differs from its archived native display')
    return crop, display


def opaque_css_rgb(value, label):
    require(isinstance(value, str) and len(value) <= 96, label + ' has no opaque CSS fill')
    value = value.strip()
    if re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        return [int(value[i:i+2],16) for i in (1,3,5)]
    match = re.fullmatch(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*(1(?:\.0+)?))?\s*\)', value)
    require(match is not None, label + ' does not describe an opaque RGB fill')
    rgb = [int(match[i]) for i in (1,2,3)]
    require(all(0 <= channel <= 255 for channel in rgb), label + ' RGB fill is outside byte range')
    return rgb


def native_views(rows, label, pinned_ids, hidden=True, root_order=None):
    require(isinstance(rows, list) and 2 <= len(rows) <= 256 and
            all(isinstance(row, dict) and isinstance(row.get('id'), str) and row['id'] for row in rows),
            label + ' native view inventory is missing or unbounded')
    mapped = {row['id']:row for row in rows}
    require(len(mapped) == len(rows) and pinned_ids.issubset(mapped), label + ' has missing/duplicate retained pages')
    require(len({row.get('webContentsId') for row in rows}) == len(rows) and
            len({row.get('rootId') for row in rows}) == len(rows), label + ' reused a native page/root identity')
    for row in rows:
        require(nonnegative_integer(row.get('webContentsId')) and row['webContentsId'] > 0 and
                nonnegative_integer(row.get('rootId')) and row['rootId'] > 0 and
                nonnegative_integer(row.get('rootsCount')) and 0 < row['rootsCount'] <= 512 and
                isinstance(row.get('rootIndex'), int) and not isinstance(row['rootIndex'], bool) and
                -1 <= row['rootIndex'] < row['rootsCount'] and
                row.get('attached') is (row['rootIndex'] >= 0) and
                isinstance(row.get('cached'),bool) and isinstance(row.get('view'),bool) and
                (row.get('clip') is None or isinstance(row['clip'],bool)), label + ' native root metadata differs')
        if row['id'] in pinned_ids:
            require(row['attached'] is True, label + ' detached a retained native page root')
        if hidden:
            require(row.get('cached') is False and row.get('view') is False and
                    (row.get('clip') is False or row.get('clip') is None), label + ' leaves an actual native view visible')
        if root_order is not None:
            require(row['rootsCount'] == len(root_order) and
                    (not row['attached'] or root_order[row['rootIndex']] == row['rootId']),
                    label + ' native root index does not match the archived actual order')
    return mapped


def nora_static_pixels(reference, display, row, label):
    """Recompute freshness observations from both archived pixel planes."""
    geometry, metadata = row['geometry'], row['capture']
    view, mapping, crop = geometry['viewport'], metadata['mapping'], metadata['cropPixels']
    sx, sy = reference['width']/view['width'], reference['height']/view['height']
    require(1 <= sx <= 4 and 1 <= sy <= 4 and abs(sx-sy) <= .01,
            label + ' shell readback density differs from its viewport')
    close = lambda a,b: a[3] == b[3] == 255 and all(abs(x-y) <= 2 for x,y in zip(a[:3],b[:3]))

    def scan(bounds, inset=0):
        trim = min(inset,bounds['width']/4,bounds['height']/4)
        left, top = math.ceil((bounds['x']+trim)*sx), math.ceil((bounds['y']+trim)*sy)
        right = math.floor((bounds['x']+bounds['width']-trim)*sx)
        bottom = math.floor((bounds['y']+bounds['height']-trim)*sy)
        require(0 < (right-left)*(bottom-top) <= 1024**2 and right > left and bottom > top,
                label + ' has an empty or oversized static pixel region')
        for y in range(top,bottom):
            for x in range(left,right):
                css = {'x':(x+.5)/sx,'y':(y+.5)/sy}
                actual = {axis:math.floor(mapping['origin'+axis.upper()]+css[axis]*mapping['scale'+axis.upper()])
                          for axis in ('x','y')}
                require(0 <= actual['x'] < crop['width'] and 0 <= actual['y'] < crop['height'],
                        label + ' static probe lies outside its native crop')
                a = png_pixel(reference,x,y)
                b = png_pixel(display,actual['x']+crop['x'],actual['y']+crop['y'])
                yield a,b,{'reference':{'x':x,'y':y},'actual':actual,'css':css}

    rgb, area = row['expected'], 0
    theme = {'bounds':geometry['opaque'],'css':geometry['fill'],'rgb':rgb,
             'referencePixels':0,'mismatched':0,'minimum':0}
    for a,b,_ in scan(geometry['opaque']):
        area += 1
        if close(a,rgb+[255]):
            theme['referencePixels'] += 1
            theme['mismatched'] += not close(b,rgb+[255])
    theme['minimum'] = max(16,math.ceil(area/4))
    observations = []
    for region in geometry['regions']:
        colors_a, colors_b = set(), set()
        item = {'label':region['label'],'bounds':region['bounds'],'compared':0,'mismatched':0,
                'referenceColors':0,'nativeColors':0}
        for a,b,point in scan(region['bounds'],1):
            item['compared'] += 1
            if len(colors_a) < 3: colors_a.add(tuple(a))
            if len(colors_b) < 3: colors_b.add(tuple(b))
            if not close(a,b):
                item['mismatched'] += 1
                if 'firstMismatch' not in item:
                    item['firstMismatch'] = {**point,'referenceRGBA':a,'nativeRGBA':b}
        item['referenceColors'], item['nativeColors'] = len(colors_a), len(colors_b)
        observations.append(item)
    reasons = []
    if theme['referencePixels'] < theme['minimum']: reasons.append('shell readback has not painted the current theme')
    if theme['mismatched']: reasons.append('native display does not match the current theme')
    for item in observations:
        if item['referenceColors'] < 3: reasons.append(item['label']+': shell UI is not painted')
        if item['nativeColors'] < 3: reasons.append(item['label']+': native UI is not painted')
        if item['mismatched']: reasons.append(item['label']+': native pixels differ from the current static shell readback')
    samples = []
    for final in row['samples']:
        sample = {key:value for key,value in final.items() if key != 'rgba'}
        sample['rgba'] = png_pixel(display,sample['x']+crop['x'],sample['y']+crop['y'])
        samples.append(sample)
    foreground = all(close(sample['rgba'],rgb+[255]) for sample in samples)
    if not foreground: reasons.append('native display has not reached the current Nora foreground')
    return {'theme':theme,'regions':observations,'reasons':reasons,'tolerance':2,
            'foregroundSamples':samples,'foregroundReady':foreground,'accepted':not reasons}


def verify_nora_readiness(read, row, label):
    proof, geometry, metadata = row.get('readiness'), row['geometry'], row['capture']
    require(isinstance(proof,dict) and proof.get('source') ==
            'current static shell readback matched to native display pixels' and
            proof.get('clock') == 'node performance.now() milliseconds' and
            proof.get('timeoutMs') == 4000 and proof.get('maxFrames') == 20,
            label + ' has no bounded current native frame acquisition')
    attempts, stages = proof.get('attempts'), proof.get('stability')
    require(isinstance(attempts,list) and 1 <= len(attempts) <= 20 and
            proof.get('attemptCount') == len(attempts) and isinstance(stages,list) and len(stages) == 3*len(attempts),
            label + ' did not archive every bounded attempt and native stability observation')
    require(all(finite(proof.get(k)) and proof[k] >= 0 for k in ('startedAt','completedAt','elapsedMs')) and
            0 < proof['elapsedMs'] < 4000 and proof['startedAt'] < proof['completedAt'],
            label + ' native acquisition clock or duration is invalid')
    regions, panel = geometry.get('regions'), geometry['panel']
    require(isinstance(regions,list) and len(regions) == 2 and
            [(r.get('label'),r.get('selector')) for r in regions] ==
            [('Nora title','.desk-title'),('Nora actions','.desk-actions')] and proof.get('regions') == regions,
            label + ' static readback must compare the actual Nora title and actions')
    for region in regions:
        bounds = rectangle(region.get('bounds'),label+' static chrome',geometry['viewport'],edges=False)
        require(bounds['x'] >= panel['x'] and bounds['y'] >= panel['y'] and
                bounds['x']+bounds['width'] <= panel['x']+panel['width']+.01 and
                bounds['y']+bounds['height'] <= panel['y']+panel['height']+.01,
                label + ' static chrome lies outside Nora')
    opaque = {'x':panel['x']+panel['width']/2-10,'y':panel['y']+6,'width':20,'height':8}
    require(geometry.get('opaque') == opaque and proof.get('background') ==
            {'bounds':opaque,'css':geometry['fill'],'rgb':row['expected']},
            label + ' opaque fill probe moved away from the current panel')
    rectangle(opaque,label+' opaque chrome',geometry['viewport'],edges=False)
    owners = row.get('underlyingPages') or [row['underlyingPage']]
    require(isinstance(proof.get('desk'),str) and proof['desk'] and
            all(owner['desk'] == proof['desk'] for owner in owners) and
            sha256_value(proof.get('holdId'),label+' native hold') != hashlib.sha256(b'').hexdigest(),
            label + ' freshness checks lost their owning desktop or native hold')
    roots = proof.get('rootOrder')
    require(isinstance(roots,list) and 2 <= len(roots) <= 512 and len(set(roots)) == len(roots) and
            all(nonnegative_integer(value) and value > 0 for value in roots),
            label + ' freshness checks lost the actual native root order')
    native_views(row['native'],label+' freshness',set(owner['id'] for owner in owners),root_order=roots)
    prefix = 'mouse-630-nora-'+row['theme']+'-'+row['phase']
    previous_time, previous_elapsed = proof['startedAt'], 0
    for index, attempt in enumerate(attempts,1):
        require(attempt.get('sequence') == index and all(finite(attempt.get(k)) and attempt[k] >= 0 for k in
                ('readbackStartedAt','readbackCompletedAt','captureStartedAt','captureCompletedAt','completedAt','elapsedMs')),
                label + ' attempt sequence or timestamps are incomplete')
        group = stages[(index-1)*3:index*3]
        for stage, expected_stage in zip(group,('before-readback','before-display','after-display')):
            require(stage.get('sequence') == index and stage.get('stage') == expected_stage and
                    finite(stage.get('at')) and stage['at'] >= 0 and stage.get('blocked') is True and
                    all(stage.get(key) == proof[key] for key in ('desk','holdId','rootOrder')) and
                    stage.get('native') == row['native'] and stage.get('geometry') == geometry and
                    stage.get('contentBounds') == metadata['contentBounds'],
                    label + ' native owner, hold, roots or geometry changed during acquisition')
        times = [previous_time,group[0]['at'],attempt['readbackStartedAt'],attempt['readbackCompletedAt'],
                 group[1]['at'],attempt['captureStartedAt'],attempt['captureCompletedAt'],group[2]['at'],attempt['completedAt']]
        require(all(a <= b for a,b in zip(times,times[1:])) and
                previous_elapsed < attempt['elapsedMs'] <= proof['elapsedMs'] and
                attempt['captureCompletedAt']-attempt['readbackStartedAt'] <= attempt['elapsedMs'] and
                attempt['completedAt'] <= proof['completedAt'], label + ' readback/display chronology is invalid')
        decoded = {}
        for kind in ('shell','display'):
            item = attempt.get(kind,{})
            expected_name = prefix+'-attempt-'+str(index).zfill(2)+'-'+kind+'.png'
            require(item.get('file') == expected_name and isinstance(item.get('pixelSize'),dict),
                    label + ' lost or relabelled an acquisition attempt PNG')
            raw = read(expected_name)
            require(hashlib.sha256(raw).hexdigest() == sha256_value(item.get('sha256'),label+' '+kind),
                    label + ' archived acquisition bytes differ from their measured SHA256')
            decoded[kind] = image(read,expected_name,item['pixelSize'])
        require(attempt.get('backend') == metadata['backend'] and
                attempt['display']['pixelSize'] == metadata['pixelSize'],
                label + ' changed native display geometry or backend between attempts')
        observed = nora_static_pixels(decoded['shell'],decoded['display'],row,label)
        require(all(attempt.get(key) == value for key,value in observed.items()),
                label + ' freshness metadata does not match the archived shell/display pixels')
        require(attempt.get('accepted') is (index == len(attempts)),
                label + ' accepted a stale frame or kept acquiring after acceptance')
        previous_time, previous_elapsed = attempt['completedAt'], attempt['elapsedMs']
    require(previous_time-stages[0]['at'] < 4000 and
            read(attempts[-1]['display']['file']) == read(metadata['source']) and
            attempts[-1]['foregroundSamples'] == row['samples'],
            label + ' final native evidence differs from the bounded accepted acquisition')
    return len(attempts)


def verify_nora_foreground(read, facts):
    require(facts.get('version') == '6.0.30' and facts.get('platform') == 'darwin' and
            facts.get('arch') == 'arm64' and facts.get('source') ==
            'actual Electron native views and globalCapture.acquire(display)' and
            facts.get('physicalInput') is False and facts.get('restored') is True and
            not facts.get('error') and not facts.get('cleanupError') and not facts.get('mediaCleanupError') and
            nonnegative_integer(facts.get('nativeSamples')) and 0 < facts['nativeSamples'] <= 100000 and
            facts.get('visibilityViolations') == [], 'Nora native visibility/provenance/restoration failed')
    motion_media(facts.get('motionMedia'),'Nora')
    before = facts.get('pagesBefore')
    require(isinstance(before,list) and len(before) == 2 and facts.get('pagesAfter') == before,
            'Nora did not preserve its native documents, viewport, scroll and identity')
    pinned = {}
    for page in before:
        require(isinstance(page.get('id'),str) and page['id'] and
                nonnegative_integer(page.get('webContentsId')) and page['webContentsId'] > 0 and
                isinstance(page.get('url'),str) and
                re.fullmatch(r'http://127\.0\.0\.1:[1-9]\d{0,4}/(?:left|right)',page['url']) and
                nonnegative_integer(page.get('epoch')) and finite(page.get('timeOrigin')) and page['timeOrigin'] > 0 and
                finite(page.get('marker')) and 0 <= page['marker'] < 1 and
                page.get('scrollX') == 0 and page.get('scrollY') == 137,
                'Nora native fixture identity/scroll is incomplete')
        viewport_size(page,'Nora native page')
        pinned[page['id']] = page
    require(len(pinned) == 2 and len({p['webContentsId'] for p in before}) == 2 and
            {p['url'].rsplit('/',1)[-1] for p in before} == {'left','right'},
            'Nora foreground proof does not contain two distinct native pages')
    pinned_ids, rows = set(pinned), facts.get('rows')
    phases = {(theme,phase) for theme in ('light','dark') for phase in
              ('cached-native-divergence','open','close-reopen','reversed','desk-switch')}
    phases.add(('dark','after-resize'))
    require(isinstance(rows,list) and len(rows) == len(phases) and
            {(row.get('theme'),row.get('phase')) for row in rows} == phases,
            'Nora foreground theme/reversal/switch/resize matrix is incomplete')
    checked_pixels = 0
    for row in rows:
        label = 'Nora '+row['theme']+' '+row['phase']
        if row['phase'] == 'cached-native-divergence':
            order = row.get('rootOrderBefore')
            require(row.get('faultInjected') is True and isinstance(order,list) and 2 <= len(order) <= 512 and
                    all(nonnegative_integer(value) and value > 0 for value in order) and
                    len(set(order)) == len(order) and row.get('rootOrderAfter') == order,
                    label + ' did not preserve actual native root parents/order during repair')
            divergent = native_views(row['divergent'],label+' divergent',pinned_ids,hidden=False,root_order=order)
            repaired = native_views(row['repaired'],label+' repaired',pinned_ids,root_order=order)
            require(set(divergent) == set(repaired) and any(divergent[i].get('cached') is False and
                    divergent[i].get('view') is True for i in pinned_ids),
                    label + ' did not exercise the cached/native visibility divergence')
            for identity, original in divergent.items():
                require(all(repaired[identity][key] == original[key] for key in
                        ('webContentsId','rootId','rootIndex','rootsCount','attached')),
                        label + ' recreated or reparented a native view instead of hiding it')
            continue
        if row['phase'] == 'close-reopen':
            frames = row.get('frames')
            require(isinstance(frames,list) and 3 <= len(frames) <= 256 and all(
                    frame.get('phase') == 'closing' and frame.get('open') is True and
                    frame.get('hidden') is False and frame.get('duration') == 300 and
                    finite(frame.get('at')) and finite(frame.get('y')) and frame['y'] > 0
                    for frame in frames) and all(a['at'] < b['at'] and a['y']+1 < b['y']
                    for a,b in zip(frames,frames[1:])), label + ' lacks genuine distinct closing/reversal frames')
            continue
        geometry = row.get('geometry', {})
        view = viewport_size(geometry.get('viewport'),label+' viewport')
        panel = rectangle(geometry['panel'],label+' panel',view,edges=False)
        require(geometry.get('open') is True and geometry.get('modal') is True and
                geometry.get('hidden') is False and geometry.get('phase') == 'open',
                label + ' is not an open foreground modal')
        expected = opaque_css_rgb(geometry.get('fill'),label)
        require(row.get('expected') == expected, label + ' recorded fill does not match its computed CSS')
        native = native_views(row['native'],label,pinned_ids)
        require(all(native[identity]['webContentsId'] == pinned[identity]['webContentsId']
                    for identity in pinned_ids), label + ' replaced its retained WebContents')
        underlying = row.get('underlyingPage', {})
        require(underlying.get('id') in pinned and nonnegative_integer(underlying.get('index')) and
                underlying['index'] in (0,1) and isinstance(underlying.get('desk'),str) and underlying['desk'] and
                underlying.get('rgb') == ([227,31,173] if underlying['index'] == 0 else [23,171,213]) and
                pinned[underlying['id']]['url'].endswith('/left' if underlying['index'] == 0 else '/right') and
                any(abs(a-b) > 32 for a,b in zip(expected,underlying['rgb'])),
                label + ' has no distinct underlying native page colour/identity')
        page_box = rectangle(underlying['bounds'],label+' underlying page',view,edges=False)
        points, samples = geometry.get('points'), row.get('samples')
        require(isinstance(points,list) and len(points) == 3 and isinstance(samples,list) and len(samples) == 3,
                label + ' requires three native foreground probes')
        name = 'mouse-630-nora-'+row['theme']+'-'+row['phase']
        require(row['capture'].get('source') == name+'-display.png' and
                row['capture'].get('capture') == name+'.png', label + ' native image identity differs')
        crop, display = native_display_images(read,row['capture'],view,label)
        verify_nora_readiness(read,row,label)
        mapping, crop_box = row['capture']['mapping'], row['capture']['cropPixels']
        for fraction, point, sample in zip((.25,.5,.75),points,samples):
            require(all(finite(point.get(k)) for k in ('x','y')) and
                    abs(point['x']-panel['x']-panel['width']*fraction) <= .01 and
                    abs(point['y']-panel['y']-10) <= .01 and
                    page_box['x'] < point['x'] < page_box['x']+page_box['width'] and
                    page_box['y'] < point['y'] < page_box['y']+page_box['height'] and
                    sample.get('point') == point, label + ' probe does not overlap its real native page')
            x = math.floor(mapping['originX']+point['x']*mapping['scaleX'])
            y = math.floor(mapping['originY']+point['y']*mapping['scaleY'])
            require(sample.get('x') == x and sample.get('y') == y,
                    label + ' recorded probe differs from the physical mapping')
            rgba = png_pixel(crop,x,y)
            require(sample.get('rgba') == rgba and rgba == png_pixel(display,x+crop_box['x'],y+crop_box['y']) and
                    rgba[3] == 255 and all(abs(a-b) <= 2 for a,b in zip(expected,rgba[:3])),
                    label + ' actual display does not paint Nora above its native page')
            checked_pixels += 1
    require(facts.get('resize', {}).get('closedAfterInvalidation') is True,
            'Nora did not close after native resize invalidation')
    native_views(facts['resize']['native'],'Nora resize release',pinned_ids,hidden=False)
    return {'themes':2,'displayCaptures':7,'nativeForegroundPixels':checked_pixels,
            'visibilitySamples':facts['nativeSamples'],'retainedNativePages':2,'nativeRootRepairs':2}


def native_endpoints(slot):
    # BrowserWorkspace uses JavaScript Math.round at each shared endpoint.
    # Python round uses ties-to-even and must not be used for this contract.
    snap = lambda value: math.floor(value+.5)
    return {'x':snap(slot['x']),'y':snap(slot['y']),
            'width':snap(slot['x']+slot['width'])-snap(slot['x']),
            'height':snap(slot['y']+slot['height'])-snap(slot['y'])}


def verify_fractional_layouts(read, facts):
    require(facts.get('version') == '6.0.30' and facts.get('restored') is True and
            not facts.get('error') and not facts.get('cleanupError') and
            facts.get('fractionalPending') is None,
            'seven-pane native regression did not complete and restore')
    rows = facts.get('fractionalLayouts')
    require(isinstance(rows,list) and len(rows) == 1 and rows[0].get('theme') == 'light' and
            rows[0].get('phase') == 'fractional-seven', 'missing exact seven-pane native regression')
    row = rows[0]
    before, during, after = (row.get(key) for key in ('before','during','after'))
    require(isinstance(before,dict) and before == during == after,
            'seven-pane hold or close changed native identity, viewport, scroll, geometry or parents')
    geometry = row.get('geometry',{})
    view = viewport_size(geometry.get('viewport'),'seven-pane viewport')
    require(view['width'] == 971 and geometry.get('open') is True and geometry.get('modal') is True and
            geometry.get('hidden') is False and geometry.get('phase') == 'open',
            'seven-pane proof did not open Nora over its exact fractional viewport')
    pages, slots, roots = (before.get(key) for key in ('pages','slots','rootOrder'))
    require(isinstance(pages,list) and len(pages) == 7 and isinstance(slots,list) and len(slots) == 7 and
            isinstance(roots,list) and 7 <= len(roots) <= 512 and len(set(roots)) == len(roots) and
            all(nonnegative_integer(root) and root > 0 for root in roots),
            'seven-pane native inventory or root order is incomplete')
    require(all(isinstance(page.get('id'),str) and page['id'] for page in pages) and
            all(isinstance(slot.get('id'),str) and slot['id'] for slot in slots), 'seven-pane owners are invalid')
    page_map, slot_map = ({item['id']:item for item in items} for items in (pages,slots))
    require(len(page_map) == len(slot_map) == 7 and set(page_map) == set(slot_map) and
            len({page.get('webContentsId') for page in pages}) == 7,
            'seven-pane owners or WebContents are duplicated or lost')
    expected_paths = {'left'}|{'fractional-'+str(index) for index in range(6)}
    actual_paths, origins, differences = set(), set(), 0
    for identity, page in page_map.items():
        slot = rectangle(slot_map[identity],'seven-pane DOM slot',view,edges=False)
        expected = native_endpoints(slot)
        actual = rectangle(page['bounds'],'seven-pane actual native root',view,edges=False)
        require(actual == expected and page.get('cachedBounds') == expected and
                all(nonnegative_integer(actual[k]) for k in ('x','y','width','height')) and
                page.get('width') == expected['width'] and page.get('height') == expected['height'],
                'seven-pane actual native bounds do not use the rounded shared endpoints')
        clip, child = page.get('clipBounds'), page.get('viewBounds')
        expected_child = {'x':0,'y':0,'width':actual['width'],'height':actual['height']} if clip is not None else actual
        require((clip is None or clip == actual) and child == expected_child,
                'seven-pane native clip/child geometry differs from its actual root')
        differences += math.floor(slot['width']+.5) != expected['width'] or math.floor(slot['height']+.5) != expected['height']
        require(nonnegative_integer(page.get('webContentsId')) and page['webContentsId'] > 0 and
                nonnegative_integer(page.get('epoch')) and finite(page.get('timeOrigin')) and page['timeOrigin'] > 0 and
                finite(page.get('marker')) and 0 <= page['marker'] < 1 and
                page.get('scrollX') == 0 and page.get('scrollY') == 137 and isinstance(page.get('url'),str),
                'seven-pane retained document, viewport or scroll identity is incomplete')
        match = re.fullmatch(r'(http://127\.0\.0\.1:[1-9]\d{0,4})/(left|fractional-[0-5])',page['url'])
        require(match is not None,'seven-pane fixture has a foreign page URL')
        origins.add(match[1]);actual_paths.add(match[2])
    require(actual_paths == expected_paths and len(origins) == 1 and differences >= 1,
            'seven-pane fixture did not reproduce independent-span versus endpoint rounding')
    retained_left = next(page for page in pages if page['url'].endswith('/left'))
    require(any(all(page.get(key) == retained_left[key] for key in
                ('id','webContentsId','url','epoch','timeOrigin','marker','scrollX','scrollY'))
                for page in facts.get('pagesBefore',[])),
            'seven-pane layout replaced the retained page before the regular Nora proof')
    for index, page in enumerate(pages):
        a = page['bounds']
        for other in pages[index+1:]:
            b = other['bounds']
            require(a['x']+a['width'] <= b['x'] or b['x']+b['width'] <= a['x'] or
                    a['y']+a['height'] <= b['y'] or b['y']+b['height'] <= a['y'],
                    'seven independent native panes overlap')
    native = native_views(row.get('native'),'seven-pane open Nora',set(page_map),root_order=roots)
    require(all(native[identity]['webContentsId'] == page['webContentsId'] for identity,page in page_map.items()),
            'seven-pane hold replaced a native WebContents')
    snapshots = row.get('snapshots')
    require(isinstance(snapshots,list) and len(snapshots) == 7 and
            {item.get('id') for item in snapshots} == set(page_map), 'seven-pane hold lost or duplicated a frozen image')
    prefix = 'mouse-630-nora-light-fractional-seven'
    fixture_rgb, snapshot_pixels = [227,31,173], 0
    for index, snapshot in enumerate(snapshots):
        require(snapshot.get('bounds') == page_map[snapshot['id']]['bounds'] and snapshot.get('complete') is True and
                snapshot.get('file') == prefix+'-page-'+str(index)+'.png' and
                all(nonnegative_integer(snapshot.get(k)) and snapshot[k] > 0 for k in ('naturalWidth','naturalHeight')),
                'seven-pane frozen native image has the wrong owner, size, position or completion')
        raw = read(snapshot['file'])
        require(hashlib.sha256(raw).hexdigest() == sha256_value(snapshot.get('sha256'),'seven-pane frozen PNG'),
                'seven-pane frozen PNG bytes differ from the actual native capture')
        frame = image(read,snapshot['file'],{'width':snapshot['naturalWidth'],'height':snapshot['naturalHeight']})
        sx, sy = frame['width']/snapshot['bounds']['width'], frame['height']/snapshot['bounds']['height']
        require(1 <= sx <= 4 and 1 <= sy <= 4 and abs(sx-sy) <= .01,
                'seven-pane frozen bitmap density differs from the native viewport')
        for fraction in (.25,.5,.75):
            rgba = png_pixel(frame,math.floor(frame['width']*fraction),frame['height']//2)
            require(rgba[3] == 255 and all(abs(a-b) <= 2 for a,b in zip(rgba[:3],fixture_rgb)),
                    'seven-pane frozen PNG does not contain its actual retained page pixels')
            snapshot_pixels += 1
    underlying = row.get('underlyingPages')
    require(isinstance(underlying,list) and len(underlying) == 7 and
            {page.get('id') for page in underlying} == set(page_map) and
            all(page.get('index') == 0 and page.get('rgb') == fixture_rgb and
                isinstance(page.get('desk'),str) and page['desk'] and
                page.get('bounds') == page_map[page['id']]['bounds'] for page in underlying) and
            len({page['desk'] for page in underlying}) == 1, 'seven-pane underlying native page identity differs')
    under_map = {page['id']:page for page in underlying}
    panel = rectangle(geometry['panel'],'seven-pane Nora panel',view,edges=False)
    expected = opaque_css_rgb(geometry.get('fill'),'seven-pane Nora fill')
    require(row.get('expected') == expected and any(abs(a-b) > 32 for a,b in zip(expected,fixture_rgb)),
            'seven-pane Nora fill is not distinct from the native pages')
    points, samples = geometry.get('points'), row.get('samples')
    require(isinstance(points,list) and len(points) == 3 and isinstance(samples,list) and len(samples) == 3 and
            row['capture'].get('source') == prefix+'-display.png' and row['capture'].get('capture') == prefix+'.png',
            'seven-pane actual display probes or capture identity are missing')
    crop, display = native_display_images(read,row['capture'],view,'seven-pane Nora')
    verify_nora_readiness(read,row,'seven-pane Nora')
    mapping, crop_box = row['capture']['mapping'], row['capture']['cropPixels']
    for fraction, point, sample in zip((.25,.5,.75),points,samples):
        require(sample.get('pageId') in under_map and sample.get('point') == point and
                all(finite(point.get(k)) for k in ('x','y')) and
                abs(point['x']-panel['x']-panel['width']*fraction) <= .01 and
                abs(point['y']-panel['y']-10) <= .01, 'seven-pane display probe owner/position differs')
        page_box = under_map[sample['pageId']]['bounds']
        require(page_box['x'] < point['x'] < page_box['x']+page_box['width'] and
                page_box['y'] < point['y'] < page_box['y']+page_box['height'],
                'seven-pane Nora display probe misses the actual native page')
        x,y = (math.floor(mapping['origin'+axis.upper()]+point[axis]*mapping['scale'+axis.upper()]) for axis in ('x','y'))
        rgba = png_pixel(crop,x,y)
        require(sample.get('x') == x and sample.get('y') == y and sample.get('rgba') == rgba and
                rgba == png_pixel(display,x+crop_box['x'],y+crop_box['y']) and rgba[3] == 255 and
                all(abs(a-b) <= 2 for a,b in zip(expected,rgba[:3])),
                'seven-pane actual display does not paint Nora over its native pages')
    return {'layouts':1,'nativePanes':7,'endpointRoundingDifferences':differences,
            'frozenNativePngs':7,'frozenNativePixels':snapshot_pixels,'nativeForegroundPixels':3}


def bounded_reader(read):
    cache, total = {}, 0
    def archived(name):
        nonlocal total
        require(isinstance(name, str) and re.fullmatch(r'mouse-[A-Za-z0-9_.-]{1,180}\.(?:json|png)', name),
                'invalid archived evidence filename')
        if name not in cache:
            require(len(cache) < 256, 'too many archived evidence files')
            raw = read(name)
            limit = 72*1024**2 if name == 'mouse-628-motion-trace.json' else 16*1024**2
            require(isinstance(raw, bytes) and 0 < len(raw) <= limit, 'missing or oversized bytes: '+name)
            total += len(raw)
            require(total <= 512*1024**2, 'archived evidence byte budget exceeded')
            cache[name] = raw
        return cache[name]
    return archived


def verify(read):
    archived = bounded_reader(read)
    retained = verify_retained(archived)
    progress = json.loads(archived('mouse-628-progress.json'))
    feedback = json.loads(archived(FEEDBACK_JSON_NAME))
    tutorial = json.loads(archived(TUTORIAL_JSON_NAME))
    ui_facts = json.loads(archived(UI_JSON_NAME))
    gestures = json.loads(archived(WHEEL_JSON_NAME))
    nora = json.loads(archived(NORA_JSON_NAME))
    header_report = verify_headers(archived, progress)
    feedback_report = verify_feedback(archived, feedback)
    verify_nora_transitions(json.loads(archived('mouse-628-desktop-transition.json')),tutorial)
    gesture_report = ui_reviewed['verify_gesture'](tutorial, archived)
    ui_report = ui_reviewed['verify_ui_regressions'](ui_facts, archived)
    wheel_report = verify_wheel_pages(archived,gestures)
    nora_report = verify_nora_foreground(archived,nora)
    fractional_report = verify_fractional_layouts(archived,nora)
    return {'version':'6.0.30', 'retainedContractVersion':'6.0.28',
            'acceptedTutorialContract':'Nora two-finger/wheel route retained from 6.0.29',
            'retained':retained, 'headerProgress':header_report, 'feedback':feedback_report,
            'noraGesture':gesture_report, 'acceptedUi':ui_report,
            'wheelPages':wheel_report, 'noraForeground':nora_report,
            'fractionalNativePanes':fractional_report}


if __name__ == '__main__':
    import zipfile
    with zipfile.ZipFile(sys.argv[1]) as archive:
        print(json.dumps(verify(archive.read), indent=2, allow_nan=False))
