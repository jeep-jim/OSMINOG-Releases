#!/usr/bin/env python3
"""Current633 workspace geometry, real OS corner pixels and native input.

The historical629 bottom-corner evidence remains unchanged. This supplement
adds the owner's external spacing/top-corner contract and real AI bottom masks.
"""
import hashlib
import json
import math
import re
import runpy
from pathlib import Path

UI = runpy.run_path(str(Path(__file__).with_name('mouse633-ui-evidence.py')))
GAP, RADIUS = 6, 12
LINE = {'light': [199, 207, 223], 'dark': [67, 83, 107]}
PANEL = {'light': [255, 255, 255], 'dark': [25, 33, 46]}
AI_COLOR = [211, 92, 53]


def need(value, message):
    if not value:
        raise ValueError('Mouse633 workspace geometry: ' + message)


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def near(value, expected, message):
    need(number(value) and abs(value-expected) <= 1e-6, message)


def outer_near(value, expected, message):
    need(number(value) and abs(value-expected) <= 1/16
         and jsround(value) == jsround(expected), message)


def rect(value):
    need(isinstance(value, dict) and all(number(value.get(k)) for k in ('x','y','width','height'))
         and value['width'] > 0 and value['height'] > 0, 'invalid measured rectangle')
    return value


def right(value): return value['x'] + value['width']
def bottom(value): return value['y'] + value['height']
def sha(raw): return hashlib.sha256(raw).hexdigest()
def jsround(value): return math.floor(value + .5)


def geometry(value, ai):
    need(isinstance(value, dict), 'missing actual renderer geometry')
    workspace, stage = rect(value.get('workspace')), rect(value.get('stage'))
    toolbar, footer = rect(value.get('toolbar')), rect(value.get('footer'))
    viewport = value.get('viewport', {})
    need(all(number(viewport.get(k)) and viewport[k] > 0 for k in ('width','height')), 'viewport missing')
    need(value.get('padding') == {'top':6,'right':0,'bottom':6,'left':0}, 'outer vertical gap or horizontal padding differs')
    near(workspace['x'], 0, 'workspace left is not flush')
    near(right(workspace), viewport['width'], 'workspace right is not flush')
    near(workspace['y'], bottom(toolbar), 'workspace does not follow the toolbar')
    near(bottom(workspace), footer['y'], 'workspace does not end at the footer')
    near(stage['x'], 0, 'stage left has an external gutter')
    near(stage['y'], workspace['y']+GAP, 'top gap differs from pane gap')
    near(bottom(stage), bottom(workspace)-GAP, 'bottom gap differs from pane gap')
    panes, dividers = value.get('panes', []), value.get('dividers', [])
    need(len(panes) == 7 and all(isinstance(p.get('id'), str) and p['id'] for p in panes)
         and len({p['id'] for p in panes}) == 7, 'seven distinct main panes required')
    need(len(dividers) >= 6 and {d.get('axis') for d in dividers} == {'x','y'}, 'both divider axes are required')
    for divider in dividers:
        bounds = rect(divider.get('bounds'))
        near(bounds['width' if divider['axis'] == 'x' else 'height'], GAP, 'divider thickness differs')
    for pane in panes:
        bounds, slot = rect(pane.get('bounds')), rect(pane.get('slot'))
        need(pane.get('radii') == [12]*4 and pane.get('roundTop') == pane.get('roundBottom') == 12,
             'all main-pane corners must be twelve pixels')
        need(bounds['width'] > 24 and bounds['height'] > 40 and bounds['x'] >= stage['x']
             and right(bounds) <= right(stage)+1e-6 and bounds['y'] >= stage['y']
             and bottom(bounds) <= bottom(stage)+1e-6, 'pane is outside the actual stage')
        near(slot['x'], bounds['x'], 'native slot left differs')
        near(right(slot), right(bounds), 'native slot right differs')
        near(bottom(slot), bottom(bounds), 'native slot bottom differs')
        need(slot['y'] > bounds['y'], 'pane header is missing')
    for actual, expected in ((min(p['bounds']['x'] for p in panes), stage['x']),
                             (max(right(p['bounds']) for p in panes), right(stage)),
                             (min(p['bounds']['y'] for p in panes), stage['y']),
                             (max(bottom(p['bounds']) for p in panes), bottom(stage))):
        outer_near(actual, expected, 'outer pane does not reach its stage edge')
    panel = value.get('ai')
    need((panel is not None) is ai, 'wrong AI scene')
    if ai:
        need(isinstance(panel.get('id'), str) and panel['id'] and panel['id'] not in {p['id'] for p in panes}
             and panel.get('radii') == [12]*4, 'AI identity or four corners differ')
        bounds, slot, divider = rect(panel.get('bounds')), rect(panel.get('slot')), rect(panel.get('divider'))
        for actual, expected in ((bounds['y'], workspace['y']+GAP), (bottom(bounds), bottom(workspace)-GAP),
                                 (right(bounds), viewport['width']), (bounds['x']-right(stage), GAP),
                                 (divider['width'], GAP), (divider['x'], right(stage)),
                                 (slot['x'], bounds['x']), (right(slot), right(bounds)), (bottom(slot), bottom(bounds))):
            near(actual, expected, 'AI gap, edge or native slot differs')
        need(slot['y'] > bounds['y'], 'AI controls are missing')
    else:
        near(right(stage), viewport['width'], 'outer right has a gutter without AI')
    return panes + ([panel] if ai else [])


def native_panels(row, panes):
    native = row.get('nativePanels', [])
    need(len(native) == len(panes) and {p.get('id') for p in native} == {p['id'] for p in panes},
         'native pane ownership differs')
    need(all(type(p.get('webContentsId')) is int and p['webContentsId'] > 0 for p in native)
         and len({p['webContentsId'] for p in native}) == len(native), 'native WebContents identities differ')
    for pane in panes:
        page = next(p for p in native if p['id'] == pane['id'])
        need(all(page.get(key) is True for key in ('visible','viewVisible','parentVisible','attached')),
             'a native page is not visible and attached')
        slot = pane['slot']
        expected = {'x':jsround(slot['x']), 'y':jsround(slot['y']),
                    'width':jsround(right(slot))-jsround(slot['x']),
                    'height':jsround(bottom(slot))-jsround(slot['y'])}
        need(page.get('bounds') == page.get('actualBounds') == expected,
             'actual native viewport differs from the rounded DOM endpoints')
    return {p['id']:p for p in native}


def identities(before, after, native, *, geometry_bound=True):
    need(isinstance(before, list) and len(before) == 7 and before == after
         and len({p.get('id') for p in before}) == 7, 'main page identity or viewport was replaced')
    for page in before:
        owner = native.get(page.get('id'))
        need(owner is not None and page.get('webContentsId') == owner['webContentsId']
             and isinstance(page.get('url'), str) and re.fullmatch(r'http://127\.0\.0\.1:\d+/[0-6]', page['url'])
             and number(page.get('identity')) and number(page.get('timeOrigin')) and page['timeOrigin'] > 0
             and type(page.get('epoch')) is int and page['epoch'] >= 0
             and page.get('field') == 'retained-'+page['url'].rsplit('/',1)[1], 'main page live identity is incomplete')
        if geometry_bound:
            need(page.get('bounds') == owner['bounds'], 'identity belongs to different native bounds')


def expected_points(value, theme, native):
    points, workspace = [], value['workspace']
    for edge in ('top','bottom'):
        for fraction in (.2,.5,.8):
            points.append({'kind':'workspace-gap','edge':edge,'point':{'x':workspace['x']+workspace['width']*fraction,
                           'y':workspace['y']+3 if edge == 'top' else bottom(workspace)-3},'expected':LINE[theme]})
    for pane in value['panes']+([value['ai']] if value.get('ai') else []):
        bounds = pane['bounds']
        for side in ('left','right'):
            for u in (.65,1.6,3):
                for v in (.65,1.6,3):
                    if math.hypot(12-u,12-v) > 13.5:
                        points.append({'kind':'pane-top-cutout','id':pane['id'],'side':side,'paneBounds':bounds,
                                       'point':{'x':bounds['x']+u if side == 'left' else right(bounds)-u,'y':bounds['y']+v},'expected':LINE[theme]})
            points.append({'kind':'pane-top-interior','id':pane['id'],'side':side,'paneBounds':bounds,
                           'point':{'x':bounds['x']+12 if side == 'left' else right(bounds)-12,'y':math.ceil(bounds['y'])+.5},'expected':PANEL[theme]})
    if value.get('ai'):
        pane = value['ai']; bounds = native[pane['id']]['bounds']
        for side in ('left','right'):
            for u in (.65,1.6,3):
                for v in (.65,1.6,3):
                    if math.hypot(12-u,12-v) > 13.5:
                        points.append({'kind':'ai-bottom-cutout','id':pane['id'],'side':side,'guestBounds':bounds,
                                       'point':{'x':bounds['x']+u if side == 'left' else right(bounds)-u,'y':bottom(bounds)-v},'expected':LINE[theme]})
            points.append({'kind':'ai-bottom-interior','id':pane['id'],'side':side,'guestBounds':bounds,
                           'point':{'x':bounds['x']+20 if side == 'left' else right(bounds)-20,'y':bottom(bounds)-3},'expected':AI_COLOR})
    return points


def scene(row, read, capture, theme, ai):
    panes = geometry(row.get('geometry'), ai)
    native = native_panels(row, panes)
    identities(row.get('identityBefore'), row.get('identityAfter'), native)
    image = UI['native_capture'](read, capture)
    need(row['geometry']['viewport'] == {k:image['contentBounds'][k] for k in ('width','height')},
         'renderer viewport differs from the archived real OS frame')
    expected = expected_points(row['geometry'], theme, native)
    probes = row.get('probes', [])
    need(len(probes) == len(expected), 'gap and every corner probe are required')
    for probe, wanted in zip(probes, expected):
        for key in ('kind','edge','id','side','paneBounds','guestBounds','expected'):
            need(probe.get(key) == wanted.get(key), 'corner identity, geometry or expected colour was relabeled')
        for key in ('x','y'):
            near(probe.get('point',{}).get(key), wanted['point'][key], 'corner or gap sample location differs')
        UI['pixel_probe'](image, probe, wanted['expected'])
    # Fractional DOM points can legitimately share a physical pixel at 1x.
    # Each distinct CSS point above remains bound to its exact raw pixel/RGB.
    need(len({(p['point']['x'],p['point']['y']) for p in probes}) == len(probes),
         'duplicate CSS locations cannot prove all corners')
    return native, len(probes), {'capture':capture['capture'],'sha256':sha(read(capture['capture'])),
                               'screenCapture':capture['screenCapture'],'screenSha256':sha(read(capture['screenCapture']))}


def linux_masks(capture, count):
    for phase in ('before','after'):
        state = capture.get('nativePaneCorners',{}).get(phase,{}).get('native',{})
        need(state.get('backend') == 'X11 Shape' and state.get('supported') is True and state.get('ownedParent') is True
             and state.get('reason') in ('ready','cached') and state.get('error') == state.get('queryError') == 0,
             'actual X11 corner query failed')
        need(state.get('paneCount') == count and state.get('cornerCount') == count*2
             and all(number(state.get(k)) and state[k] > 0 for k in ('scaleX','scaleY'))
             and state.get('logicalWidth') == capture['contentBounds']['width']
             and state.get('logicalHeight') == capture['contentBounds']['height'], 'X11 corner ownership or scale differs')
        corners = state.get('corners', [])
        need(len(corners) == count*2 and len({c.get('window') for c in corners}) == count*2
             and all(type(c.get('window')) is int and c['window'] > 0 and c.get('exists') is True
                     and c.get('mapped') is True and c.get('overrideRedirect') is True
                     and type(c.get('inputRectangles')) is int and c['inputRectangles'] == 0 for c in corners),
             'a mapped native X11 corner can intercept input')


def native_input(row, native, capture, platform, main_id, ai_id):
    inputs = row.get('input', [])
    need(len(inputs) == 2 and [p.get('id') for p in inputs] == [main_id, ai_id], 'main and AI corner inputs are required')
    for item in inputs:
        page = native[item['id']]
        bounds, content, factor = page['bounds'], item.get('contentBounds'), item.get('factor')
        need(content == capture['contentBounds'] and number(factor) and .25 <= factor <= 5
             and item.get('guestBounds') == bounds and item.get('webContentsId') == page['webContentsId']
             and item.get('source') == {'darwin':'CGEvent','win32':'User32','linux':'XTest'}[platform], 'corner input target differs')
        side = 'left' if item['id'] == ai_id else 'right'
        need(item.get('side') == side, 'input must use internal main-right and AI-left cutouts')
        point = {'x':jsround(content['x']+bounds['x']+(2 if side == 'left' else bounds['width']-2)),
                 'y':jsround(content['y']+bottom(bounds)-2)}
        need(item.get('point') == point, 'input did not test the transparent corner overlay area')
        expected = {'x':(point['x']-content['x']-bounds['x'])/factor,
                    'y':(point['y']-content['y']-bounds['y'])/factor}
        event = item.get('event', {})
        need(item.get('expectedClient') == expected and event.get('trusted') is True
             and number(event.get('at')) and event['at'] >= 0, 'native pointer event missing')
        need(all(number(event.get(k)) and abs(event[k]-expected[k]) <= 1.5 for k in ('x','y')),
             'trusted pointer was delivered to different page coordinates')


def verify(read, *, expected_platform, expected_arch):
    need((expected_platform,expected_arch) in (('darwin','arm64'),('win32','x64'),('linux','x64')), 'unsupported target')
    raw = read('mouse-629-ui-regressions.json')
    need(isinstance(raw,bytes) and 0 < len(raw) <= 16*1024**2, 'missing or oversized native report')
    facts = json.loads(raw)
    need((facts.get('version'),facts.get('platform'),facts.get('arch')) == ('6.0.33',expected_platform,expected_arch)
         and facts.get('restored') is True and not facts.get('error') and not facts.get('cleanupError'), 'native runtime or restoration failed')
    supplement = facts.get('workspace633', {})
    need(supplement.get('schema') == 1 and supplement.get('gap') == 6 and supplement.get('radius') == 12,
         'current workspace supplement absent')
    rows = facts.get('separators', [])
    need(len(rows) == 4 and {(r.get('theme'),r.get('variant')) for r in rows} ==
         {(t,v) for t in ('light','dark') for v in ('initial','resized')}, 'theme and fractional-resize coverage incomplete')
    # Keep the accepted historical bottom geometry/colours and raw-pixel checks.
    UI['verify_separators'](rows, read)
    total, captures, first_ids = 0, [], [p['id'] for p in rows[0]['nativePanels']]
    for row in rows:
        native, count, capture = scene(row.get('workspace633',{}), read, row['nativeCapture'], row['theme'], False)
        if expected_platform == 'linux': linux_masks(row['nativeCapture'], 7)
        need({k:v['bounds'] for k,v in native.items()} == {p['id']:p['bounds'] for p in row['nativePanels']},
             'supplement is from different retained native panes')
        total += count; captures.append(capture)
    ai_rows = supplement.get('aiScenes', [])
    need(len(ai_rows) == 2 and {r.get('theme') for r in ai_rows} == {'light','dark'}, 'both native AI themes are required')
    for row in ai_rows:
        need(row.get('variant') == 'ai' and row.get('closed') is True and row.get('restored') is True,
             'AI scene did not close and restore')
        native, count, capture = scene(row, read, row['nativeCapture'], row['theme'], True)
        if expected_platform == 'linux': linux_masks(row['nativeCapture'], 8)
        identities(row.get('beforePages'), row.get('afterPages'), native, geometry_bound=False)
        need(row.get('windowBefore') == row.get('windowAfter') == row['nativeCapture']['contentBounds'], 'AI scene moved or resized the window')
        ai = row['geometry']['ai']; identity = row.get('aiIdentityBefore', {})
        need(identity == row.get('aiIdentityAfter') and identity.get('id') == ai['id']
             and identity.get('webContentsId') == native[ai['id']]['webContentsId'] and identity.get('url') == row.get('url')
             and isinstance(row.get('url'),str) and re.fullmatch(r'http://127\.0\.0\.1:\d+/ai',row['url'])
             and number(identity.get('timeOrigin')) and identity['timeOrigin'] > 0 and number(identity.get('identity'))
             and identity.get('field') == 'retained-7', 'AI page identity was replaced')
        native_input(row, native, row['nativeCapture'], expected_platform, first_ids[0], ai['id'])
        total += count; captures.append(capture)
    return {'ok':True,'version':'6.0.33','platform':expected_platform,'arch':expected_arch,
            'reportSha256':sha(raw),'scenes':6,'mainPanes':7,'aiScenes':2,'decodedPixelProbes':total,
            'nativeCornerInputs':4,'captures':captures}
