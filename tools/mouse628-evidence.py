#!/usr/bin/env python3
"""Independent, bounded checks of archived Mouse 6.0.28 native evidence.

These checks complement the fresh installed run. A JSON success flag cannot
replace the corresponding archived, decoded display or presentation pixels.
"""
import hashlib
import json
import pathlib
import runpy
import sys

BASE = pathlib.Path(__file__).with_name('mouse627-release.py')
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == 'a1b416cba4f2d9824df4df6654a61f5cee97894a70a79c12cd34b01801932053'
saved_argv = sys.argv
try:
    sys.argv = [str(BASE), 'validate-template']
    reviewed = runpy.run_path(str(BASE), run_name='reviewed_mouse627')
finally:
    sys.argv = saved_argv
decode_png, png_pixel = reviewed['decode_png'], reviewed['png_pixel']

JSON_NAMES = ('mouse-628-local.json', 'mouse-628-progress.json',
              'mouse-628-borderless.json', 'mouse-628-motion.json',
              'mouse-628-desktop-transition.json', 'mouse-628-swipe-tutorial.json',
              'mouse-628-motion-trace.json')
NATIVE_MARKERS = ('MOUSE_628_LOCAL_MCP_NATIVE_PASS',
                  'MOUSE_628_PER_PANE_PROGRESS_NATIVE_PASS',
                  'MOUSE_628_BORDERLESS_NATIVE_PASS',
                  'MOUSE_628_NORA_CONTENT_FIT_NATIVE_PASS',
                  'MOUSE_628_OPEN_NORA_DESKTOP_SLIDE_NATIVE_PASS',
                  'MOUSE_628_THREE_FINGER_TUTORIAL_WRITE_PASS',
                  'MOUSE_628_THREE_FINGER_TUTORIAL_NATIVE_PASS',
                  'MOUSE_628_BURROW_CONTENT_FIT_CONTROLS_PASS',
                  'MOUSE_628_ACTIVE_TAB_FLOW_BORDERLESS_BOTH_THEMES_PASS',
                  'MOUSE_628_BORDERLESS_UPDATE_BADGE_BOTH_THEMES_PASS')


def require(condition, message):
    if not condition:
        raise ValueError('Mouse628 evidence: ' + message)


def image(read, name, size=None):
    require(isinstance(name, str) and name.startswith('mouse-') and name.endswith('.png'),
            'invalid image name')
    raw = read(name)
    require(0 < len(raw) <= 16 * 1024**2, 'missing or oversized image ' + name)
    result = decode_png(raw, name)
    if size is not None:
        require((result['width'], result['height']) == (size['width'], size['height']),
                'image dimensions differ: ' + name)
    return result


def display_crop(read, item):
    """Compare sampled exact pixels in the original display and archived crop."""
    crop = image(read, item['capture'], item['pixelSize'])
    display = image(read, item['screenCapture'], item['screenPixelSize'])
    rect = item['cropPixels']
    require(rect['width'] == crop['width'] and rect['height'] == crop['height'] and
            0 <= rect['x'] < display['width'] and 0 <= rect['y'] < display['height'] and
            rect['x'] + rect['width'] <= display['width'] and
            rect['y'] + rect['height'] <= display['height'], 'invalid native crop geometry')
    xs = sorted({0, crop['width']//4, crop['width']//2, crop['width']*3//4, crop['width']-1})
    ys = sorted({0, crop['height']//4, crop['height']//2, crop['height']*3//4, crop['height']-1})
    for x in xs:
        for y in ys:
            require(png_pixel(crop, x, y) == png_pixel(display, x+rect['x'], y+rect['y']),
                    'crop differs from original display at ' + item['capture'])


def verify(read):
    docs = {}
    for name in JSON_NAMES:
        raw = read(name)
        limit = 72 * 1024**2 if name.endswith('trace.json') else 16 * 1024**2
        require(0 < len(raw) <= limit, 'missing or oversized JSON ' + name)
        docs[name] = json.loads(raw)
    local, progress, border, motion, slides, swipe, trace = (docs[n] for n in JSON_NAMES)
    for name, doc in docs.items():
        if name != 'mouse-628-motion-trace.json':
            require(doc.get('version') == '6.0.28', 'version mismatch: ' + name)

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
    require(swipe.get('syntheticNativeEvent') is True and
            swipe.get('physicalTrackpadVerified') is False and
            all(swipe.get(k) is True for k in ('firstUseShown', 'nonSwitchRetained',
                'successHidden', 'reopenHidden', 'restartHidden', 'privateIsolated', 'restored')),
            'gesture first-use lifecycle or physical verification claim')
    image(read, 'mouse-628-swipe-first-use.png')
    meta = trace.get('mouseMotionTrace', {})
    require(meta.get('complete') is True and meta.get('dataLossOccurred') is False and
            meta.get('limitedEvents') == 0 and meta.get('errors') == [] and
            meta.get('eventCount') == len(trace.get('traceEvents', [])),
            'lossless complete compositor trace')
    return {'version':'6.0.28', 'localCaptures':4, 'progressRows':4,
            'borderlessRows':24, 'desktopSlides':4, 'traceEvents':meta['eventCount']}


if __name__ == '__main__':
    import zipfile
    with zipfile.ZipFile(sys.argv[1]) as archive:
        print(json.dumps(verify(archive.read), indent=2))
