#!/usr/bin/env python3
"""Mouse 6.0.29 evidence: retain reviewed 628 geometry, replace its rejected gesture.

Legacy evidence and motion validators are immutable. Their decoded-image and
native display-crop helpers are imported from the exact reviewed 628 module;
the retained feature checks below are kept explicit so no successful gesture
record is manufactured or relabelled to satisfy the old three-finger contract.
"""
import hashlib
import importlib.util
import json
import math
import pathlib
import re

BASE = pathlib.Path(__file__).with_name('mouse628-evidence.py')
if hashlib.sha256(BASE.read_bytes()).hexdigest() != 'd5c0f1a6275f54d4529ea5856f6240fb92f4d8d9b5fc69111adc7c3affb7fd46':
    raise ValueError('Reviewed 628 evidence validator changed')
spec = importlib.util.spec_from_file_location('retained_mouse628_evidence', BASE)
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
image, display_crop, png_pixel = legacy.image, legacy.display_crop, legacy.png_pixel

RETAINED_JSON_NAMES = tuple(name for name in legacy.JSON_NAMES
                            if name != 'mouse-628-swipe-tutorial.json')
JSON_NAMES = RETAINED_JSON_NAMES + ('mouse-629-swipe-tutorial.json',
                                   'mouse-629-ui-regressions.json')
NATIVE_MARKERS = tuple(marker for marker in legacy.NATIVE_MARKERS
                       if 'THREE_FINGER_TUTORIAL' not in marker) + (
    'MOUSE_629_TWO_FINGER_WHEEL_TUTORIAL_WRITE_PASS',
    'MOUSE_629_TWO_FINGER_WHEEL_TUTORIAL_NATIVE_PASS',
    'MOUSE_629_UI_REGRESSIONS_NATIVE_PASS',
)


def require(condition, message):
    if not condition:
        raise ValueError('Mouse629 evidence: ' + message)


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def native_wheel(row):
    event = row.get('nativeInput', {})
    require(event.get('type') == 'mouseWheel' and
            all(number(event.get(k)) for k in ('x', 'y', 'deltaX', 'deltaY')) and
            event['x'] >= 0 and event['y'] >= 0 and
            (abs(event['deltaX']) > 0 or abs(event['deltaY']) > 0),
            'missing delivered native mouseWheel witness')
    return event


def observed_wheel(row, direction=None, duplicate=False):
    delivered = native_wheel(row)
    observed = row.get('duplicateInput' if duplicate else 'observedInput', {})
    require(isinstance(observed, dict) and observed.get('isTrusted') is True and
            observed.get('inPicker') is True and observed.get('deltaMode') == 0 and
            all(number(observed.get(k)) for k in ('x', 'y', 'deltaX', 'deltaY', 'at')) and
            abs(observed['x']-delivered['x']) <= 1 and abs(observed['y']-delivered['y']) <= 1,
            'native mouseWheel was not observed as a trusted event inside the Nora picker')
    axis = 'x' if abs(delivered['deltaX']) > abs(delivered['deltaY'])*1.2 else 'y'
    main, cross = ('deltaX', 'deltaY') if axis == 'x' else ('deltaY', 'deltaX')
    require(abs(delivered[main]) > abs(delivered[cross])*1.2 and
            abs(observed[main]) >= 48 and abs(observed[main]) > abs(observed[cross])*1.2,
            'native/observed wheel axis does not cross the switching threshold')
    if direction is not None:
        require((1 if observed[main] > 0 else -1) == direction,
                'observed native wheel direction differs from the requested adjacent desktop')
    if duplicate:
        require(observed['at'] >= row['observedInput']['at'], 'duplicate wheel precedes the original event')
    return axis


def rgb(value):
    """Accept a recorded opaque CSS colour or an exact RGB triplet."""
    if isinstance(value, list):
        require(len(value) == 3 and all(type(c) is int and 0 <= c <= 255 for c in value),
                'invalid RGB triplet')
        return value
    require(isinstance(value, str), 'missing CSS colour')
    value = value.strip().lower()
    if re.fullmatch(r'#[0-9a-f]{6}', value):
        return [int(value[i:i+2], 16) for i in (1, 3, 5)]
    match = re.fullmatch(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*(1(?:\.0*)?))?\s*\)', value)
    require(match is not None, 'unsupported or non-opaque CSS colour: ' + value)
    return rgb([int(match[i]) for i in (1, 2, 3)])


def rectangle(value):
    require(isinstance(value, dict) and
            all(number(value.get(k)) for k in ('x', 'y', 'width', 'height')) and
            value['width'] > 0 and value['height'] > 0,
            'invalid native rectangle')
    return value


def native_capture(read, item):
    """Decode the original display and derive the crop mapping independently."""
    require(isinstance(item, dict) and item.get('source') == 'globalCapture.acquire(display)' and
            item.get('kind') == 'screen' and isinstance(item.get('backend'), str) and item['backend'],
            'UI capture is not a native display capture')
    display_bounds = rectangle(item.get('display', {}).get('bounds'))
    content_bounds = rectangle(item.get('contentBounds'))
    crop = image(read, item['capture'], item['pixelSize'])
    display = image(read, item['screenCapture'], item['screenPixelSize'])
    scale_x, scale_y = display['width']/display_bounds['width'], display['height']/display_bounds['height']
    left = (content_bounds['x']-display_bounds['x'])*scale_x
    top = (content_bounds['y']-display_bounds['y'])*scale_y
    right, bottom = left+content_bounds['width']*scale_x, top+content_bounds['height']*scale_y
    expected_rect = {'x':math.floor(left), 'y':math.floor(top),
                     'width':math.ceil(right)-math.floor(left),
                     'height':math.ceil(bottom)-math.floor(top)}
    rect = item.get('cropPixels', {})
    require(rect == expected_rect and all(type(v) is int for v in rect.values()) and
            rect['width'] == crop['width'] and rect['height'] == crop['height'] and
            0 <= rect['x'] < display['width'] and 0 <= rect['y'] < display['height'] and
            rect['x']+rect['width'] <= display['width'] and rect['y']+rect['height'] <= display['height'],
            'native crop does not match display and content bounds')
    mapping = {'scaleX':scale_x, 'scaleY':scale_y,
               'originX':left-rect['x'], 'originY':top-rect['y']}
    actual_mapping = item.get('mapping', {})
    require(all(number(actual_mapping.get(k)) and abs(actual_mapping[k]-v) <= 1e-6
                for k, v in mapping.items()), 'native pixel mapping differs from source display')
    for x in sorted({0, crop['width']//4, crop['width']//2, crop['width']*3//4, crop['width']-1}):
        for y in sorted({0, crop['height']//4, crop['height']//2, crop['height']*3//4, crop['height']-1}):
            require(png_pixel(crop, x, y) == png_pixel(display, x+rect['x'], y+rect['y']),
                    'UI crop differs from the original display')
    return {'crop':crop, 'display':display, 'rect':rect, 'mapping':mapping,
            'contentBounds':content_bounds}


def pixel_probe(captured, probe, expected):
    require(isinstance(probe, dict) and type(probe.get('x')) is int and type(probe.get('y')) is int and
            0 <= probe['x'] < captured['crop']['width'] and
            0 <= probe['y'] < captured['crop']['height'], 'UI pixel probe is outside the native capture')
    x, y = probe['x'], probe['y']
    actual = png_pixel(captured['crop'], x, y)
    require(actual == probe.get('rgba') and
            actual == png_pixel(captured['display'], x+captured['rect']['x'], y+captured['rect']['y']),
            'UI pixel probe differs from archived display pixels')
    expected = rgb(expected)
    require(actual[3] == 255 and all(abs(actual[i]-expected[i]) <= 3 for i in range(3)),
            'UI native pixel does not match its expected colour')
    point, mapping = probe.get('point', {}), captured['mapping']
    require(all(number(point.get(k)) for k in ('x', 'y')) and
            math.floor(mapping['originX']+point['x']*mapping['scaleX']) == x and
            math.floor(mapping['originY']+point['y']*mapping['scaleY']) == y,
            'UI probe does not map to its measured CSS position')
    return point['x'], point['y']


def contains(bounds, point):
    bounds = rectangle(bounds)
    return (bounds['x'] <= point[0] < bounds['x']+bounds['width'] and
            bounds['y'] <= point[1] < bounds['y']+bounds['height'])


def verify_gesture(swipe, read):
    require(swipe.get('version') == '6.0.29' and
            swipe.get('recognizer') == 'two-finger-or-wheel' and
            swipe.get('source') == 'nora-wheel' and
            swipe.get('syntheticNativeEvent') is True and
            swipe.get('physicalTrackpadVerified') is False,
            'gesture version/source or physical verification claim')
    require(all(swipe.get(k) is True for k in ('firstUseShown', 'nonSwitchRetained',
                'successHidden', 'reopenHidden', 'restartHidden', 'privateIsolated', 'restored')),
            'gesture first-use lifecycle incomplete')
    records = swipe.get('records', [])
    require(isinstance(records, list) and all(isinstance(row, dict) for row in records),
            'gesture records missing')
    first = [row for row in records if row.get('kind') == 'first-use']
    require(len(first) == 1 and first[0].get('nora', {}).get('open') is True and
            first[0].get('gesture', {}).get('hintVisible') is True and
            first[0]['gesture'].get('learned') is False,
            'first-use hint was not visible in open Nora')
    ordinary = [row for row in records if row.get('kind') == 'ordinary-controls-and-animation']
    require(len(ordinary) == 1 and ordinary[0].get('gesture', {}).get('hintVisible') is True and
            ordinary[0]['gesture'].get('learned') is False,
            'ordinary controls trained the gesture hint')
    rejected = [row for row in records if row.get('kind') == 'failed-native-switch']
    require(len(rejected) == 1 and rejected[0].get('gesture', {}).get('hintVisible') is True and
            rejected[0]['gesture'].get('learned') is False and
            rejected[0].get('desktopId') == first[0].get('desktopId') and
            rejected[0].get('packetDelta') == 0,
            'busy wheel was dispatched, switched a desktop or trained the hint')
    blocked = rejected[0].get('blockedInputs', [])
    require(type(rejected[0].get('packetsBefore')) is int and rejected[0]['packetsBefore'] >= 0 and
            rejected[0].get('packetsAfter') == rejected[0]['packetsBefore'] and len(blocked) == 2 and
            all(row.get('before') == rejected[0]['packetsBefore'] for row in blocked) and
            {observed_wheel(row) for row in blocked} == {'x', 'y'},
            'busy Nora must reject both observed native wheel axes without dispatch')
    success = [row for row in records if row.get('kind') == 'successful-native-switch']
    require(len(success) == 4 and {(row.get('theme'), row.get('direction')) for row in success} ==
            {(theme, direction) for theme in ('light', 'dark') for direction in (-1, 1)},
            'wheel switch direction/theme matrix incomplete')
    axes = set()
    for row in success:
        axis = observed_wheel(row, row['direction'])
        require(observed_wheel(row, row['direction'], duplicate=True) == axis,
                'duplicate momentum must reach the same trusted native wheel route')
        axes.add(axis)
        before, after = row.get('before', {}), row.get('after', {})
        packet = row.get('dispatch', {}).get('packet', {})
        require(packet.get('source') == 'nora-wheel' and
                packet.get('direction') == ('left' if row['direction'] == 1 else 'right') and
                before.get('desktopId') and after.get('desktopId') and
                before['desktopId'] != after['desktopId'] and
                after.get('gesture', {}).get('lastResult', {}).get('completed') is True and
                after['gesture'].get('hintVisible') is False and
                after['gesture'].get('learned') is True and
                after.get('nora', {}).get('open') is True and
                row.get('duplicateSuppressed') is True and
                row.get('persisted') == {'completed': True},
                'wheel switch, completion or duplicate suppression evidence')
    require(axes == {'x', 'y'}, 'horizontal trackpad and vertical mouse-wheel routes both required')
    reopened = [row for row in records if row.get('kind') == 'reopened']
    require(len(reopened) == 1 and reopened[0].get('gesture', {}).get('learned') is True and
            reopened[0]['gesture'].get('hintVisible') is False,
            'completed hint returned on reopen')
    private = [row for row in records if row.get('kind') == 'private-session']
    fresh = [row for row in records if row.get('kind') == 'fresh-private-session']
    require(len(private) == 1 and len(fresh) == 1 and
            private[0].get('first', {}).get('gesture', {}).get('learned') is False and
            private[0]['first']['gesture'].get('hintVisible') is True and
            private[0].get('after', {}).get('gesture', {}).get('learned') is True and
            private[0]['after']['gesture'].get('hintVisible') is False and
            private[0].get('normalValue') == {'completed': True} and
            fresh[0].get('gesture', {}).get('learned') is False and
            fresh[0]['gesture'].get('hintVisible') is True,
            'private gesture learning leaks between sessions')
    observed_wheel(private[0], 1)
    require(private[0].get('dispatch', {}).get('packet', {}).get('source') == 'nora-wheel' and
            private[0]['first'].get('desktopId') and private[0]['after'].get('desktopId') and
            private[0]['first']['desktopId'] != private[0]['after']['desktopId'],
            'private completion lacks an actual native desktop switch')
    restart = swipe.get('restart', {})
    require(type(swipe.get('writePid')) is int and swipe['writePid'] > 0 and
            type(restart.get('pid')) is int and restart['pid'] > 0 and
            restart['pid'] != swipe['writePid'] and restart.get('version') == '6.0.29' and
            number(swipe.get('writeMainTimeOrigin')) and number(restart.get('mainTimeOrigin')) and
            restart['mainTimeOrigin'] != swipe['writeMainTimeOrigin'] and
            number(swipe.get('writeRendererTimeOrigin')) and number(restart.get('timeOrigin')) and
            restart['timeOrigin'] != swipe['writeRendererTimeOrigin'] and
            restart.get('persisted') == {'completed': True} and
            restart.get('gesture', {}).get('learned') is True and
            restart.get('hintHidden') is True and restart.get('noraOpen') is True,
            'learning was not verified in a new native application process')
    image(read, 'mouse-629-swipe-first-use.png')
    image(read, 'mouse-629-swipe-restart.png')
    return {'recognizer':'two-finger-or-wheel', 'source':'nora-wheel',
            'nativeWheelSwitches':len(success), 'physicalTrackpadVerified':False,
            'restartPid':restart['pid']}


def verify_retained_versions(docs):
    # Local/progress helpers record app.getVersion(), not an evidence schema
    # version. Their historical filenames remain unchanged in a 629 install.
    # Geometry/motion helpers explicitly keep their reviewed 628 schema version.
    for name in RETAINED_JSON_NAMES:
        if name != 'mouse-628-motion-trace.json':
            expected = ('6.0.29' if name in ('mouse-628-local.json', 'mouse-628-progress.json')
                        else '6.0.28')
            require(docs[name].get('version') == expected, 'retained version mismatch: ' + name)


def verify_retained(read, docs):
    local, progress, border, motion, slides, trace = (docs[n] for n in RETAINED_JSON_NAMES)
    verify_retained_versions(docs)
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
    meta = trace.get('mouseMotionTrace', {})
    require(meta.get('complete') is True and meta.get('dataLossOccurred') is False and
            meta.get('limitedEvents') == 0 and meta.get('errors') == [] and
            meta.get('eventCount') == len(trace.get('traceEvents', [])),
            'lossless complete compositor trace')
    return {'localCaptures':4, 'progressRows':4, 'borderlessRows':24,
            'desktopSlides':4, 'traceEvents':meta['eventCount']}


VEINS_627 = {'light':('#c7cfdf', [199, 207, 223]), 'dark':('#43536b', [67, 83, 107])}
NORA_FILL = {'light':[255, 255, 255], 'dark':[25, 33, 46]}
PAGE_COLORS = [[171, 43, 158], [24, 117, 150], [158, 75, 32], [75, 89, 158],
               [35, 130, 77], [143, 52, 86], [83, 100, 41]]


def verify_separators(rows, read):
    require(isinstance(rows, list) and len(rows) == 4 and
            {(row.get('theme'), row.get('variant')) for row in rows} ==
            {(theme, variant) for theme in ('light', 'dark') for variant in ('initial', 'resized')},
            'separator theme/resize matrix incomplete')
    captures, pane_sets, resized_panels = {}, [], {}
    total = 0
    for row in rows:
        theme, variant = row['theme'], row['variant']
        expected_hex, expected_rgb = VEINS_627[theme]
        require(row.get('paneCount') == 7 and row.get('expectedHex') == expected_hex and
                row.get('expectedRGB') == expected_rgb and row.get('actualToken') == expected_hex and
                rgb(row.get('stageColor')) == expected_rgb and
                isinstance(row.get('dividerColors'), list) and len(row['dividerColors']) >= 6 and
                all(rgb(color) == expected_rgb for color in row['dividerColors']),
                'separator colours differ from the exact 6.0.27 palette')
        panes = row.get('nativePanels', [])
        require(len(panes) == 7 and all(isinstance(p.get('id'), str) and p['id'] for p in panes) and
                len({p['id'] for p in panes}) == 7, 'seven distinct native panels are required')
        bounds = {p['id']:rectangle(p.get('bounds')) for p in panes}
        colors = {p['id']:PAGE_COLORS[i] for i, p in enumerate(panes)}
        pane_sets.append(set(bounds))
        if variant == 'resized':
            resized_panels[theme] = bounds
        captured = native_capture(read, row.get('nativeCapture'))
        require(row.get('viewport') == {k:captured['contentBounds'][k] for k in ('width', 'height')},
                'separator viewport differs from captured native content bounds')
        captures[(theme, variant)] = captured
        probes = row.get('probes', [])
        kinds = {kind:[p for p in probes if p.get('kind') == kind]
                 for kind in ('divider', 'corner-cutout', 'page-interior')}
        require(len(kinds['divider']) >= 18 and len(kinds['corner-cutout']) >= 20 and
                len(kinds['page-interior']) >= 2 and len(probes) == sum(map(len, kinds.values())),
                'dense native divider, cutout and page pixel probes are incomplete')
        for probe in probes:
            if probe['kind'] == 'divider':
                require(probe.get('expected') == expected_rgb, 'divider expected colour was relabelled')
                pixel_probe(captured, probe, expected_rgb)
                continue
            require(probe.get('id') in bounds and probe.get('guestBounds') == bounds[probe['id']] and
                    probe.get('side') in ('left', 'right'), 'corner probe does not belong to a native pane')
            expected = expected_rgb if probe['kind'] == 'corner-cutout' else colors[probe['id']]
            require(probe.get('expected') == expected, 'corner/page expected colour was relabelled')
            point = pixel_probe(captured, probe, expected)
            rect = bounds[probe['id']]
            require(contains(rect, point), 'native corner/page probe is outside its guest viewport')
            horizontal = point[0]-rect['x'] if probe['side'] == 'left' else rect['x']+rect['width']-point[0]
            vertical = rect['y']+rect['height']-point[1]
            if probe['kind'] == 'corner-cutout':
                require(0 < horizontal <= 3.01 and 0 < vertical <= 3.01 and
                        math.hypot(12-horizontal, 12-vertical) > 13.5,
                        'native cutout probe does not test the square outside the rounded corner')
            else:
                require(abs(horizontal-20) <= 1e-6 and abs(vertical-3) <= 1e-6,
                        'native page-colour witness is not beside the corner cutout')
        require(len({(p['x'], p['y']) for p in probes}) == len(probes),
                'duplicate pixel probes cannot establish dense junction coverage')
        total += len(probes)
    require(all(ids == pane_sets[0] for ids in pane_sets), 'dense pane identities changed across theme/resize scenes')
    for theme in ('light', 'dark'):
        before, after = (captures[(theme, variant)]['contentBounds'] for variant in ('initial', 'resized'))
        require(before['width']-after['width'] == 37 and before['height']-after['height'] == 23,
                'native corner masks were not checked after the required fractional-layout resize')
    return {'scenes':4, 'nativePanels':7, 'decodedPixelProbes':total}, {'ids':pane_sets[0], 'bounds':resized_panels}


def verify_nora(rows, read, panes):
    pane_ids = panes['ids']
    require(isinstance(rows, list) and len(rows) == 2 and
            {row.get('theme') for row in rows} == {'light', 'dark'}, 'Nora native layering theme matrix incomplete')
    total = 0
    for row in rows:
        require(all(row.get(flag) is True for flag in ('holdActive', 'overlayBlocked',
                    'identityPreserved', 'boundsPreserved')), 'Nora guest hold or restored page identity incomplete')
        hidden = row.get('nativeHidden', [])
        require(len(hidden) == 7 and {p.get('id') for p in hidden} == pane_ids and
                all(p.get('view') is False and 'clip' in p and
                    (p['clip'] is None or p['clip'] is False) for p in hidden),
                'a native guest remains visible above Nora')
        snapshots = row.get('snapshots', [])
        require(len(snapshots) == 7 and {p.get('id') for p in snapshots} == pane_ids and
                all(p.get('complete') is True and type(p.get('width')) is int and p['width'] > 0 and
                    type(p.get('height')) is int and p['height'] > 0 for p in snapshots),
                'Nora does not retain seven complete native page snapshots')
        fill = NORA_FILL[row['theme']]
        require(row.get('panelFill') == fill, 'Nora fill differs from the existing theme panel colour')
        captured = native_capture(read, row.get('nativeCapture'))
        panel_bounds = rectangle(row.get('panelBounds'))
        probes = row.get('probes', [])
        require(len(probes) >= 3 and len({(p.get('x'), p.get('y')) for p in probes}) == len(probes),
                'Nora needs three distinct visible fill/guest overlap probes')
        for probe in probes:
            require(probe.get('kind') == 'nora-fill' and probe.get('expected') == fill and
                    probe.get('overlapGuestId') in pane_ids and
                    probe.get('guestBounds') == panes['bounds'][row['theme']][probe['overlapGuestId']],
                    'Nora overlap probe lacks an owned native guest')
            point = pixel_probe(captured, probe, fill)
            require(contains(panel_bounds, point) and contains(probe.get('guestBounds'), point),
                    'Nora fill sample does not overlap the native guest viewport')
        total += len(probes)
    return {'themes':2, 'hiddenNativePanels':7, 'decodedOverlapProbes':total}


def verify_scrollbars(facts, read):
    require(isinstance(facts, dict) and facts.get('version') == '6.0.29' and
            facts.get('source') == 'installed guest WebContents + bundled preload' and
            facts.get('physicalTrackpadVerified') is False and facts.get('restored') is True and
            'error' not in facts and 'cleanupError' not in facts,
            'scrollbar fixture source, physical scope or restoration incomplete')
    fixture = facts.get('fixture', {})
    require(isinstance(fixture.get('tabId'), str) and fixture['tabId'] and
            type(fixture.get('webContentsId')) is int and fixture['webContentsId'] > 0 and
            isinstance(fixture.get('desktop'), str) and fixture['desktop'] and
            isinstance(fixture.get('url'), str) and
            re.fullmatch(r'http://127\.0\.0\.1:\d+/mouse629-scrollbars', fixture['url']) and
            fixture.get('authorScrollbar') == {'width':'auto', 'rootThumb':'#aaaaaa',
                'nestedThumb':'#cccccc', 'track':'white', 'priority':'important'},
            'scrollbar evidence lacks the hostile ordinary website fixture')
    rows = facts.get('themes', [])
    require(isinstance(rows, list) and len(rows) == 2 and
            {row.get('theme') for row in rows} == {'light', 'dark'},
            'scrollbar theme matrix incomplete')
    site = time_origin = previous = None
    completed_wheels = []
    for row in rows:
        theme = row['theme']
        thumb, track = ([104]*3, [23]*3) if theme == 'dark' else ([139]*3, [245]*3)
        expected_color = 'rgb('+', '.join(map(str, thumb))+') rgb('+', '.join(map(str, track))+')'
        before, measured, after = (row.get(key, {}) for key in ('beforeTheme', 'measured', 'afterWheels'))
        require(number(measured.get('timeOrigin')) and measured['timeOrigin'] > 0 and
                measured.get('timeOrigin') == before.get('timeOrigin') == after.get('timeOrigin') and
                measured.get('site') == before.get('site') == after.get('site'),
                'scrollbar theme or wheel interaction reloaded or restyled the website')
        if site is None:
            site, time_origin = measured['site'], measured['timeOrigin']
        require(measured['site'] == site and measured['timeOrigin'] == time_origin and
                site.get('background') == 'rgb(22, 22, 22)' and site.get('color') == 'rgb(237, 237, 237)' and
                site.get('rootScheme') == 'light' and site.get('input', {}).get('scheme') == 'light',
                'browser scrollbar theme changed site content or native form colours')
        viewport = measured.get('viewport', {})
        require(all(number(viewport.get(k)) and viewport[k] > 0 for k in ('width', 'height', 'devicePixelRatio')) and
                viewport['width'] >= 500 and viewport['height'] >= 450 and
                viewport == before.get('viewport') == after.get('viewport'),
                'scrollbar fixture viewport is missing or changed')
        for state in (measured, after):
            require(state.get('media') == {'dark':theme == 'dark', 'forcedColors':False},
                    'scrollbar evidence used the wrong browser theme or forced colours')
            require(number(state.get('at')) and state['at'] >= 0 and
                    state.get('scrollEndSupported') == {'root':True, 'nested':True} and
                    isinstance(state.get('scrollEndEvents'), list),
                    'scrollbar native scrollend observation is unavailable')
            for key in ('root', 'nested'):
                value = state.get(key, {})
                require(value.get('width') == 'thin' and value.get('color') == expected_color and
                        rgb(value.get('corner')) == track and value.get('scheme') == 'light' and
                        value.get('overflowX') == 'scroll' and value.get('overflowY') == 'scroll' and
                        all(number(value.get(k)) and value[k] >= 0 for k in ('clientWidth', 'clientHeight',
                            'offsetWidth', 'offsetHeight', 'scrollWidth', 'scrollHeight', 'scrollTop', 'scrollLeft')) and
                        value['clientWidth'] > 0 and value['clientHeight'] > 0 and
                        value['scrollWidth'] > value['clientWidth'] and value['scrollHeight'] > value['clientHeight'],
                        'root/nested scrollbar did not override the author white style')
        for key in ('root', 'nested'):
            require(all(measured[key][field] == before.get(key, {}).get(field)
                        for field in ('clientWidth', 'clientHeight', 'scrollTop', 'scrollLeft')),
                    'changing scrollbar theme altered viewport geometry or page scroll')
        if previous is not None:
            require(all(before[key][field] == previous[key][field] for key in ('root', 'nested')
                        for field in ('clientWidth', 'clientHeight', 'scrollTop', 'scrollLeft')),
                    'scrollbar themes do not belong to the same uninterrupted native page')
        wheels = row.get('wheels', {})
        running = {key:measured[key]['scrollTop'] for key in ('root', 'nested')}
        for target in ('root', 'nested'):
            wheel = wheels.get(target, {})
            delivered, point, event = wheel.get('input', {}), wheel.get('point', {}), wheel.get('event', {})
            native_wheel({'nativeInput':delivered})
            require(delivered['deltaX'] == 0 and delivered['deltaY'] == -160 and
                    point.get('inside') is True and point.get('nested') is (target == 'nested') and
                    point.get('x') == delivered['x'] and point.get('y') == delivered['y'] and
                    0 < delivered['x'] < viewport['width'] and 0 < delivered['y'] < viewport['height'] and
                    event.get('isTrusted') is True and event.get('nested') is (target == 'nested') and
                    event.get('deltaMode') == 0 and all(number(event.get(k)) for k in ('x', 'y', 'deltaX', 'deltaY', 'at')) and
                    event['deltaX'] == 0 and event['deltaY'] != 0 and
                    abs(event['x']-delivered['x']) <= 1 and abs(event['y']-delivered['y']) <= 1 and
                    event in after.get('wheelEvents', []),
                    'scrollbar wheel input was not observed by the intended native scroll container')
            other = 'nested' if target == 'root' else 'root'
            result = wheel.get('after', {})
            require(wheel.get('before') == running and
                    all(number(result.get(key)) and result[key] >= 0 for key in ('root', 'nested')) and
                    result[target] != running[target] and result[other] == running[other] and
                    wheel.get('desktopBefore') == wheel.get('desktopAfter') ==
                    {'bank':fixture['desktop'], 'shell':fixture['desktop']},
                    'page wheel did not scroll exactly its intended container or switched desktop')
            completion = wheel.get('completion', {})
            end = completion.get('event', {})
            settled = completion.get('afterTwoFrames', {})
            require(wheel.get('theme') == theme and wheel.get('target') == target and
                    wheel.get('status') == 'completed' and
                    number(wheel.get('startedAt')) and number(wheel.get('observedAt')) and
                    type(event.get('index')) is int and event['index'] >= 0 and
                    completion.get('method') == 'trusted scrollend' and
                    completion.get('supported') is True and completion.get('timeoutMs') == 6000 and
                    end.get('target') == target and end.get('isTrusted') is True and
                    end.get('wheelEventIndex') == event['index'] and number(end.get('at')) and
                    wheel['startedAt'] <= event['at'] <= end['at'] and
                    end in after['scrollEndEvents'] and
                    {key:end.get(key) for key in ('root', 'nested')} == result and
                    end.get('scrollTop') == result[target] and
                    end.get('scrollLeft') == after[target]['scrollLeft'] and
                    completion.get('positions') == result and
                    {key:settled.get(key) for key in ('root', 'nested')} == result and
                    number(completion.get('observedAt')) and number(settled.get('at')) and
                    end['at'] <= completion['observedAt'] <= settled['at'] == wheel['observedAt'] <= after['at'],
                    'wheel completion lacks its own trusted scrollend and stable final positions')
            require(not completed_wheels or completed_wheels[-1]['observedAt'] <= wheel['startedAt'],
                    'next native wheel began before the preceding scroll completed')
            completed_wheels.append(wheel)
            running = result
        require(running == {key:after[key]['scrollTop'] for key in ('root', 'nested')},
                'scrollbar final page scroll differs from delivered wheel evidence')
        shot = row.get('screenshot', {})
        require(shot.get('source') == 'guest WebContents.capturePage' and shot.get('nativeComposite') is False and
                shot.get('filename') == 'mouse-629-scrollbars-'+theme+'.png',
                'scrollbar guest capture source was mislabelled')
        frame = image(read, shot['filename'], shot['pixelSize'])
        scale_x, scale_y = frame['width']/viewport['width'], frame['height']/viewport['height']
        require(scale_x > 0 and scale_y > 0 and abs(scale_x-scale_y) <= .01,
                'scrollbar screenshot is not an unwarped guest viewport')
        # The fixture leaves the top-right interior empty. This decoded pixel
        # checks that the archived guest still displays the unchanged site;
        # it is not represented as proof of the macOS compositor or hardware.
        body = png_pixel(frame, math.floor((viewport['width']-25)*scale_x), math.floor(8*scale_y))
        require(body[3] == 255 and all(abs(v-22) <= 3 for v in body[:3]),
                'scrollbar screenshot does not preserve the fixture page background')
        if theme == 'dark':
            require(facts.get('wheel') == wheels, 'summary wheel evidence differs from the dark native run')
        previous = after
    require(facts.get('wheelAttempts') == completed_wheels and
            [wheel['event']['index'] for wheel in completed_wheels] == [0, 1, 2, 3],
            'scrollbar wheel attempt journal is incomplete or refers to another input')
    return {'themes':2, 'nativeWheelScrolls':4, 'guestCaptures':2,
            'trustedScrollEnds':4, 'nativeComposite':False, 'physicalTrackpadVerified':False}


def verify_ui_regressions(facts, read):
    require(facts.get('version') == '6.0.29' and facts.get('baselineVersion') == '6.0.27' and
            facts.get('platform') == 'darwin' and facts.get('arch') == 'arm64' and
            facts.get('paneCount') == 7 and facts.get('restored') is True and
            'error' not in facts and 'cleanupError' not in facts,
            'UI native fixture version/platform/restoration incomplete')
    separators, panes = verify_separators(facts.get('separators'), read)
    nora = verify_nora(facts.get('nora'), read, panes)
    scrollbars = verify_scrollbars(facts.get('scrollbars'), read)
    return {'baselineVersion':'6.0.27', 'separators':separators, 'nora':nora, 'scrollbars':scrollbars}


def verify(read):
    docs = {}
    for name in JSON_NAMES:
        raw = read(name)
        limit = 72 * 1024**2 if name.endswith('trace.json') else 16 * 1024**2
        require(0 < len(raw) <= limit, 'missing or oversized JSON ' + name)
        docs[name] = json.loads(raw)
    retained = verify_retained(read, docs)
    gesture = verify_gesture(docs['mouse-629-swipe-tutorial.json'], read)
    ui = verify_ui_regressions(docs['mouse-629-ui-regressions.json'], read)
    return {'version':'6.0.29', 'retained':retained, 'gesture':gesture, 'ui':ui}


if __name__ == '__main__':
    import sys
    import zipfile
    with zipfile.ZipFile(sys.argv[1]) as archive:
        print(json.dumps(verify(archive.read), indent=2))
