#!/usr/bin/env python3
"""Retained UI/tutorial and hidden-scrollbar checks for 632; synthetic inputs only."""
import ast
import copy
import importlib.util
import math
import pathlib
import struct
import unittest
from unittest import mock
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mouse632_ui_evidence', ROOT/'tools/mouse632-ui-evidence.py')
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


def png(width=1, height=1, pixels=None):
    def chunk(kind, data):
        return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data)&0xffffffff)
    return (b'\x89PNG\r\n\x1a\n'+
            chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))+
            chunk(b'IDAT', zlib.compress(b''.join(b'\0'+(pixels[y*width*4:(y+1)*width*4]
                 if pixels is not None else b'\x20\x20\x20\xff'*width) for y in range(height))))+
            chunk(b'IEND', b''))


def wheel_evidence(axis='x', direction=1, duplicate=False):
    event = {'type':'mouseWheel', 'x':100, 'y':200,
             'deltaX':120*direction if axis == 'x' else 0,
             'deltaY':120*direction if axis == 'y' else 0}
    observed = {**event, 'isTrusted':True, 'inPicker':True, 'deltaMode':0, 'at':10}
    observed.pop('type')
    return {'nativeInput':event, 'observedInput':observed,
            'duplicateInput':dict(observed, at=11) if duplicate else None}


def fixture():
    """Synthetic validator unit fixture; never an artifact or a native PASS."""
    initial = {'desktopId':'desk-a', 'nora':{'open':True},
               'gesture':{'hintVisible':True, 'learned':False}}
    learned = {'nora':{'open':True},
               'gesture':{'hintVisible':False, 'learned':True,
                          'lastResult':{'completed':True}}}
    records = [dict(kind='first-use', **copy.deepcopy(initial)),
               dict(kind='ordinary-controls-and-animation', **copy.deepcopy(initial)),
               dict(kind='failed-native-switch',
                    blockedInputs=[dict(before=0, **wheel_evidence(axis)) for axis in ('x', 'y')],
                    packetsBefore=0, packetsAfter=0, packetDelta=0,
                    **copy.deepcopy(initial))]
    for theme in ('light', 'dark'):
        for direction in (1, -1):
            records.append({'kind':'successful-native-switch', 'theme':theme,
                            'direction':direction,
                            **wheel_evidence('x' if theme == 'light' else 'y', direction, duplicate=True),
                            'dispatch':{'packet':{'source':'nora-wheel',
                                       'direction':'left' if direction == 1 else 'right'}},
                            'before':dict(initial, desktopId='desk-a' if direction == 1 else 'desk-b'),
                            'after':dict(learned, desktopId='desk-b' if direction == 1 else 'desk-a'),
                            'duplicateSuppressed':True, 'persisted':{'completed':True}})
    records += [dict(kind='reopened', **copy.deepcopy(learned)),
                {'kind':'private-session', 'first':copy.deepcopy(initial),
                 'after':dict(copy.deepcopy(learned), desktopId='desk-private-b'),
                 'normalValue':{'completed':True},
                 'dispatch':{'packet':{'source':'nora-wheel'}}, **wheel_evidence('y')},
                dict(kind='fresh-private-session', **copy.deepcopy(initial))]
    return {'version':'6.0.32', 'recognizer':'two-finger-or-wheel', 'source':'nora-wheel',
            'syntheticNativeEvent':True, 'physicalTrackpadVerified':False,
            **{key:True for key in ('firstUseShown','nonSwitchRetained','successHidden',
                                   'reopenHidden','restartHidden','privateIsolated','restored')},
            'writePid':100, 'writeMainTimeOrigin':1000, 'writeRendererTimeOrigin':1100,
            'records':records,
            'restart':{'pid':200, 'mainTimeOrigin':2000, 'timeOrigin':2100,
                       'version':'6.0.32', 'persisted':{'completed':True},
                       'gesture':{'learned':True}, 'hintHidden':True, 'noraOpen':True}}


def native_fixture_capture(images, name, viewport, background, probes):
    """Synthetic parser input: deliberately not native application evidence."""
    width, height = viewport['width'], viewport['height']
    pixels = bytearray(bytes(background+[255])*(width*height))
    for probe in probes:
        x, y = math.floor(probe['point']['x']), math.floor(probe['point']['y'])
        probe.update(x=x, y=y, rgba=probe['expected']+[255])
        pixels[(y*width+x)*4:(y*width+x+1)*4] = bytes(probe['rgba'])
    display_width, display_height = width+40, height+60
    full = bytearray(b'\0\0\0\xff'*(display_width*display_height))
    for y in range(height):
        start = ((y+30)*display_width+20)*4
        full[start:start+width*4] = pixels[y*width*4:(y+1)*width*4]
    images[name+'.png'] = png(width, height, pixels)
    images[name+'-display.png'] = png(display_width, display_height, full)
    return {'source':'globalCapture.acquire(display)', 'kind':'screen', 'backend':'synthetic-unit-test',
            'display':{'id':1, 'bounds':{'x':0, 'y':0, 'width':display_width, 'height':display_height},
                       'scaleFactor':1},
            'contentBounds':{'x':20, 'y':30, 'width':width, 'height':height},
            'screenPixelSize':{'width':display_width, 'height':display_height},
            'pixelSize':dict(viewport), 'cropPixels':{'x':20, 'y':30, 'width':width, 'height':height},
            'mapping':{'scaleX':1, 'scaleY':1, 'originX':0, 'originY':0},
            'capture':name+'.png', 'screenCapture':name+'-display.png'}


def keyboard_fixture(previous):
    """Synthetic trusted-event schema; never native input evidence."""
    rows = []
    nested, root = copy.deepcopy(previous['nested']), copy.deepcopy(previous['root'])
    at = previous['at']+20
    for theme in ('light', 'dark'):
        for key, axis in [('Right', 'scrollLeft'), ('Down', 'scrollTop')]:
            before = copy.deepcopy(nested)
            nested[axis] += 40
            event = {'isTrusted':True, 'key':'Arrow'+key, 'at':at+1}
            end = {'isTrusted':True, 'target':'nested', 'at':at+30,
                   'scrollLeft':nested['scrollLeft'], 'scrollTop':nested['scrollTop'],
                   'root':root['scrollTop'], 'nested':nested['scrollTop']}
            rows.append({'theme':theme, 'keyCode':key, 'input':{'type':'keyDown', 'keyCode':key},
                         'beforeAt':at, 'afterAt':at+32, 'timeOrigin':previous['timeOrigin'],
                         'before':before, 'after':copy.deepcopy(nested),
                         'rootBefore':copy.deepcopy(root), 'rootAfter':copy.deepcopy(root),
                         'event':event, 'completion':{'method':'trusted scrollend', 'event':end}})
            at += 50
    return rows


def encapsulated_fixture():
    """Synthetic closed-shadow and cross-origin rejection fixtures only."""
    rows, previous = [], {}
    for theme in ('light', 'dark'):
        for index, kind in enumerate(('open', 'closed', 'same-frame', 'cross-frame')):
            frame = kind.endswith('frame')
            origin = {'x':12+232*(index%2) if frame else 0, 'y':194 if frame else 0}
            rect = {'left':0 if frame else 12+232*(index%2), 'top':0 if frame else 32,
                    'width':212, 'height':132}
            point = {'x':origin['x']+rect['left']+106, 'y':origin['y']+rect['top']+66}
            before = copy.deepcopy(previous[kind]) if kind in previous else {
                'width':'auto', 'overflowX':'scroll', 'overflowY':'scroll', 'gapX':0, 'gapY':0,
                'x':0, 'y':0, 'scrollWidth':900, 'scrollHeight':700, 'clientWidth':210, 'clientHeight':130,
                'timeOrigin':2000+index, 'rect':rect, 'events':{'wheel':[], 'end':[], 'key':[]}}
            before.update(at=1000+len(rows)*100, dark=theme=='dark')
            after = copy.deepcopy(before)
            after.update(x=before['x']+80, y=before['y']+160, at=before['at']+50)
            after['events']['wheel'].append({'isTrusted':True, 'at':before['at']+1, 'x':80, 'y':160})
            after['events']['end'].append({'isTrusted':True, 'at':before['at']+45, 'x':after['x'], 'y':after['y']})
            rows.append({'theme':theme, 'kind':kind, 'pageURL':'http://127.0.0.1:12345/mouse632-encapsulated',
                         'frameURL':('http://127.0.0.1:12345/mouse632-frame' if kind=='same-frame' else
                                     'http://127.0.0.1:23456/mouse632-cross-frame' if kind=='cross-frame' else None),
                         'before':before, 'after':after, 'point':point, 'origin':origin,
                         'input':{'type':'mouseWheel', **point, 'deltaX':-80, 'deltaY':-160},
                         'hit':{'inside':True, 'id':kind if frame else kind+'-host',
                                'viewport':{'width':500, 'height':450}},
                         'desktopBefore':{'bank':'desk-a', 'shell':'desk-a'},
                         'desktopAfter':{'bank':'desk-a', 'shell':'desk-a'}})
            previous[kind] = after
    return rows


def scrollbar_fixture(images):
    site = {'background':'rgb(22, 22, 22)', 'color':'rgb(237, 237, 237)', 'rootScheme':'light',
            'input':{'background':'rgb(255, 255, 255)', 'color':'rgb(0, 0, 0)', 'scheme':'light',
                     'border':'rgb(118, 118, 118)', 'appearance':'auto'}}
    facts = {'version':'6.0.32', 'source':'installed guest WebContents + native hide-scrollbars + bundled preload',
             'nativeHideScrollbars':True, 'physicalTrackpadVerified':False, 'restored':True,
             'fixture':{'tabId':'scroll-page', 'webContentsId':10, 'desktop':'desk-a',
                        'url':'http://127.0.0.1:12345/mouse629-scrollbars',
                        'authorScrollbar':{'width':'auto', 'rootThumb':'#aaaaaa', 'nestedThumb':'#cccccc',
                                           'track':'white', 'priority':'important'}}, 'themes':[], 'wheelAttempts':[]}
    tops, events, ends, previous = {'root':300, 'nested':80}, [], [], None
    for theme in ('dark', 'light'):
        thumb, track = (104, 23) if theme == 'dark' else (139, 245)
        style = {'width':'none', 'color':f'rgb({thumb}, {thumb}, {thumb}) rgb({track}, {track}, {track})',
                 'corner':f'rgb({track}, {track}, {track})', 'scheme':'light',
                 'overflowX':'scroll', 'overflowY':'scroll', 'clientWidth':320, 'clientHeight':220,
                 'offsetWidth':322, 'offsetHeight':222, 'scrollWidth':900, 'scrollHeight':1000, 'scrollLeft':40}
        measured = {'viewport':{'width':500, 'height':450, 'devicePixelRatio':1}, 'timeOrigin':1000,
                    'at':100+len(events)*100, 'scrollEndSupported':{'root':True, 'nested':True},
                    'scrollEndEvents':copy.deepcopy(ends),
                    'media':{'dark':theme == 'dark', 'forcedColors':False}, 'site':copy.deepcopy(site),
                    'wheelEvents':copy.deepcopy(events),
                    **{key:dict(style, scrollTop=value) for key, value in tops.items()}}
        measured['root'].update(clientWidth=500, clientHeight=450)
        before_theme = copy.deepcopy(previous or measured)
        wheels = {}
        for target in ('root', 'nested'):
            point = {'x':100 if target == 'nested' else 455, 'y':190 if target == 'nested' else 395,
                     'nested':target == 'nested', 'hit':'DIV' if target == 'nested' else 'BODY', 'inside':True}
            event = {'isTrusted':True, 'nested':target == 'nested', 'x':point['x'], 'y':point['y'],
                     'deltaX':0, 'deltaY':160, 'deltaMode':0, 'index':len(events), 'at':110+len(events)*100}
            after_tops = dict(tops)
            after_tops[target] += 160
            end = {'target':target, 'isTrusted':True, 'at':event['at']+50,
                   'wheelEventIndex':event['index'], **after_tops,
                   'scrollTop':after_tops[target], 'scrollLeft':40}
            wheels[target] = {'input':{'type':'mouseWheel', 'x':point['x'], 'y':point['y'], 'deltaX':0, 'deltaY':-160},
                              'theme':theme, 'target':target, 'status':'completed',
                              'startedAt':event['at']-2, 'observedAt':end['at']+2,
                              'point':point, 'event':event, 'before':dict(tops), 'after':after_tops,
                              'desktopBefore':{'bank':'desk-a', 'shell':'desk-a'},
                              'desktopAfter':{'bank':'desk-a', 'shell':'desk-a'},
                              'completion':{'method':'trusted scrollend', 'timeoutMs':6000, 'supported':True,
                                            'event':end, 'observedAt':end['at']+1, 'positions':dict(after_tops),
                                            'afterTwoFrames':{'at':end['at']+2, **after_tops}}}
            facts['wheelAttempts'].append(wheels[target])
            tops = after_tops
            events.append(event)
            ends.append(end)
        after = copy.deepcopy(measured)
        after['wheelEvents'] = copy.deepcopy(events)
        after['scrollEndEvents'] = copy.deepcopy(ends)
        after['at'] = 100+len(events)*100
        for key in ('root', 'nested'):
            after[key]['scrollTop'] = tops[key]
        filename = 'mouse-629-scrollbars-'+theme+'.png'
        images[filename] = png(500, 450, bytearray(b'\x16\x16\x16\xff'*(500*450)))
        facts['themes'].append({'theme':theme, 'beforeTheme':before_theme, 'measured':measured,
                                'afterWheels':after, 'wheels':wheels,
                                'screenshot':{'filename':filename, 'path':'/synthetic/'+filename,
                                              'pixelSize':{'width':500, 'height':450},
                                              'source':'guest WebContents.capturePage', 'nativeComposite':False}})
        if theme == 'dark':
            facts['wheel'] = copy.deepcopy(wheels)
        previous = after
    facts['keyboard'] = keyboard_fixture(previous)
    facts['encapsulated'] = encapsulated_fixture()
    return facts


def ui_fixture():
    images = {}
    panes = [{'id':'page-'+str(i), 'bounds':{'x':10+i*80, 'y':80, 'width':70, 'height':100}} for i in range(7)]
    facts = {'version':'6.0.32', 'baselineVersion':'6.0.27', 'platform':'darwin', 'arch':'arm64',
             'paneCount':7, 'restored':True, 'separators':[], 'nora':[]}
    for theme in ('light', 'dark'):
        hex_color, color = evidence.VEINS_627[theme]
        for variant in ('initial', 'resized'):
            viewport = {'width':640 if variant == 'initial' else 603,
                        'height':360 if variant == 'initial' else 337}
            probes = [{'kind':'divider', 'point':{'x':20+i*30, 'y':20}, 'expected':color} for i in range(18)]
            for i, pane in enumerate(panes):
                rect = pane['bounds']
                for side in ('left', 'right'):
                    for u in (.65, 1.6, 3):
                        for v in (.65, 1.6, 3):
                            if math.hypot(12-u, 12-v) <= 13.5:
                                continue
                            point = {'x':rect['x']+u if side == 'left' else rect['x']+rect['width']-u,
                                     'y':rect['y']+rect['height']-v}
                            probes.append({'kind':'corner-cutout', 'id':pane['id'], 'side':side,
                                           'guestBounds':dict(rect), 'point':point, 'expected':color})
                    probes.append({'kind':'page-interior', 'id':pane['id'], 'side':side,
                                   'guestBounds':dict(rect), 'expected':evidence.PAGE_COLORS[i],
                                   'point':{'x':rect['x']+20 if side == 'left' else rect['x']+rect['width']-20,
                                            'y':rect['y']+rect['height']-3}})
            capture = native_fixture_capture(images, 'mouse-test-separators-'+theme+'-'+variant, viewport, color, probes)
            facts['separators'].append({'theme':theme, 'variant':variant, 'expectedHex':hex_color,
                                        'expectedRGB':color, 'actualToken':hex_color,
                                        'stageColor':'rgb('+', '.join(map(str, color))+')',
                                        'dividerColors':['rgb('+', '.join(map(str, color))+')']*6,
                                        'paneCount':7, 'viewport':viewport, 'nativePanels':copy.deepcopy(panes),
                                        'probes':probes, 'nativeCapture':capture})
        fill = evidence.NORA_FILL[theme]
        probes = [{'kind':'nora-fill', 'overlapGuestId':pane['id'], 'guestBounds':dict(pane['bounds']),
                   'point':{'x':pane['bounds']['x']+20, 'y':100}, 'expected':fill} for pane in panes[:3]]
        capture = native_fixture_capture(images, 'mouse-test-nora-'+theme, {'width':603, 'height':337}, fill, probes)
        facts['nora'].append({'theme':theme, 'holdActive':True, 'overlayBlocked':True,
                              'nativeHidden':[{'id':p['id'], 'view':False, 'clip':False} for p in panes],
                              'snapshots':[{'id':p['id'], 'complete':True, 'width':70, 'height':100} for p in panes],
                              'panelFill':fill, 'panelBounds':{'x':0, 'y':50, 'width':603, 'height':280},
                              'probes':probes, 'nativeCapture':capture,
                              'identityPreserved':True, 'boundsPreserved':True})
    facts['scrollbars'] = scrollbar_fixture(images)
    return facts, images


class GestureEvidenceTests(unittest.TestCase):
    def verify(self, facts):
        return evidence.verify_gesture(facts, lambda name:png())

    def test_valid_synthetic_contract_reports_physical_trackpad_unverified(self):
        result = self.verify(fixture())
        self.assertEqual(result['nativeWheelSwitches'], 4)
        self.assertFalse(result['physicalTrackpadVerified'])

    def test_old_three_finger_record_is_rejected(self):
        facts = fixture()
        facts['recognizer'] = 'macos-three-finger-swipe'
        with self.assertRaisesRegex(ValueError, 'version/source'):
            self.verify(facts)

    def test_success_flags_without_wheel_witness_are_rejected(self):
        facts = fixture()
        facts['records'][3].pop('nativeInput')
        with self.assertRaisesRegex(ValueError, 'native mouseWheel witness'):
            self.verify(facts)

    def test_nonfinite_or_zero_wheel_cannot_prove_input(self):
        for event in ({'type':'mouseWheel','x':1,'y':1,'deltaX':0,'deltaY':0},
                      {'type':'mouseWheel','x':1,'y':1,'deltaX':float('nan'),'deltaY':1},
                      {'type':'mouseWheel','x':-1,'y':1,'deltaX':0,'deltaY':64}):
            with self.subTest(event=event):
                facts = fixture()
                facts['records'][3]['nativeInput'] = event
                with self.assertRaisesRegex(ValueError, 'native mouseWheel witness'):
                    self.verify(facts)

    def test_both_horizontal_and_vertical_wheel_contracts_work(self):
        self.verify(fixture())

    def test_only_horizontal_witness_does_not_prove_mouse_wheel_route(self):
        facts = fixture()
        for row in facts['records']:
            if row.get('kind') == 'successful-native-switch':
                row.update(wheel_evidence('x', row['direction'], duplicate=True))
        with self.assertRaisesRegex(ValueError, 'routes both required'):
            self.verify(facts)

    def test_busy_renderer_cannot_dispatch_or_learn(self):
        for changes in ({'packetDelta':1}, {'gesture':{'hintVisible':False,'learned':True}}):
            facts = fixture()
            facts['records'][2].update(changes)
            with self.assertRaisesRegex(ValueError, 'busy wheel'):
                self.verify(facts)

    def test_no_op_and_wrong_direction_cannot_count_as_success(self):
        facts = fixture()
        facts['records'][3]['after']['desktopId'] = facts['records'][3]['before']['desktopId']
        with self.assertRaisesRegex(ValueError, 'wheel switch'):
            self.verify(facts)
        facts = fixture()
        facts['records'][3]['dispatch']['packet']['direction'] = 'right'
        with self.assertRaisesRegex(ValueError, 'wheel switch'):
            self.verify(facts)

    def test_missing_direction_or_theme_is_rejected(self):
        facts = fixture()
        facts['records'].pop(3)
        with self.assertRaisesRegex(ValueError, 'direction/theme matrix'):
            self.verify(facts)

    def test_requery_of_same_process_is_not_a_restart(self):
        facts = fixture()
        facts['restart']['pid'] = facts['writePid']
        with self.assertRaisesRegex(ValueError, 'new native application process'):
            self.verify(facts)

    def test_private_hint_leaking_to_next_session_is_rejected(self):
        facts = fixture()
        facts['records'][-1]['gesture']['learned'] = True
        with self.assertRaisesRegex(ValueError, 'leaks between sessions'):
            self.verify(facts)

    def test_physical_trackpad_claim_is_rejected(self):
        facts = fixture()
        facts['physicalTrackpadVerified'] = True
        with self.assertRaisesRegex(ValueError, 'physical verification'):
            self.verify(facts)

    def test_missing_or_invalid_native_capture_is_rejected(self):
        with self.assertRaises(ValueError):
            evidence.verify_gesture(fixture(), lambda name:b'not a PNG')

    def test_untrusted_dom_wheel_cannot_stand_in_for_native_input(self):
        facts = fixture()
        facts['records'][3]['observedInput']['isTrusted'] = False
        with self.assertRaisesRegex(ValueError, 'trusted event'):
            self.verify(facts)

    def test_claimed_duplicate_suppression_requires_delivered_duplicate(self):
        facts = fixture()
        facts['records'][3]['duplicateInput'] = None
        with self.assertRaisesRegex(ValueError, 'trusted event'):
            self.verify(facts)


class UiEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original, cls.images = ui_fixture()

    def setUp(self):
        self.facts = copy.deepcopy(self.original)

    def verify(self):
        return evidence.verify_ui_regressions(self.facts, self.images.__getitem__)

    def test_valid_synthetic_pixel_contract_is_not_physical_evidence(self):
        result = self.verify()
        self.assertEqual(result['separators']['scenes'], 4)
        self.assertEqual(result['nora']['decodedOverlapProbes'], 6)
        self.assertEqual(result['scrollbars']['nativeWheelScrolls'], 12)
        self.assertEqual(result['scrollbars']['nativeKeyScrolls'], 4)
        self.assertEqual(result['scrollbars']['encapsulatedScrolls'], 8)
        self.assertFalse(result['scrollbars']['nativeComposite'])

    def test_separator_colour_cannot_be_relabelled_as_627(self):
        self.facts['separators'][0]['expectedRGB'] = [243, 245, 249]
        with self.assertRaisesRegex(ValueError, 'exact 6.0.27 palette'):
            self.verify()

    def test_correct_colour_flags_do_not_replace_actual_png_pixels(self):
        self.facts['separators'][0]['probes'][0]['rgba'] = [243, 245, 249, 255]
        with self.assertRaisesRegex(ValueError, 'archived display pixels'):
            self.verify()

    def test_display_crop_cannot_be_replaced_with_shell_screenshot(self):
        self.facts['separators'][0]['nativeCapture']['source'] = 'win.capturePage'
        with self.assertRaisesRegex(ValueError, 'native display capture'):
            self.verify()

    def test_wrong_retina_mapping_is_recomputed(self):
        self.facts['separators'][0]['nativeCapture']['mapping']['scaleX'] = 2
        with self.assertRaisesRegex(ValueError, 'pixel mapping differs'):
            self.verify()

    def test_corner_probe_cannot_be_moved_to_a_plain_background(self):
        row = self.facts['separators'][0]
        probe = next(p for p in row['probes'] if p['kind'] == 'corner-cutout')
        probe.update(point={'x':600, 'y':40}, x=600, y=40)
        with self.assertRaisesRegex(ValueError, 'outside its guest viewport'):
            self.verify()

    def test_missing_resized_scene_is_rejected(self):
        self.facts['separators'][1]['variant'] = 'initial'
        with self.assertRaisesRegex(ValueError, 'theme/resize matrix'):
            self.verify()

    def test_nora_native_guest_still_above_panel_is_rejected(self):
        self.facts['nora'][0]['nativeHidden'][0]['view'] = True
        with self.assertRaisesRegex(ValueError, 'remains visible above Nora'):
            self.verify()

    def test_nora_overlap_cannot_claim_invented_guest_bounds(self):
        self.facts['nora'][0]['probes'][0]['guestBounds']['width'] = 999
        with self.assertRaisesRegex(ValueError, 'owned native guest'):
            self.verify()

    def test_nora_needs_three_distinct_native_overlap_pixels(self):
        self.facts['nora'][0]['probes'].pop()
        with self.assertRaisesRegex(ValueError, 'three distinct'):
            self.verify()

    def test_white_author_scrollbar_cannot_pass_dark_browser_theme(self):
        self.facts['scrollbars']['themes'][0]['measured']['root']['width'] = 'auto'
        with self.assertRaisesRegex(ValueError, 'author white style'):
            self.verify()

    def test_native_suppression_must_be_installed_before_document_css(self):
        self.facts['scrollbars']['nativeHideScrollbars'] = False
        with self.assertRaisesRegex(ValueError, 'source, physical scope'):
            self.verify()

    def test_claimed_hidden_style_does_not_replace_actual_zero_gutters(self):
        for target, dimension in [('root', 'clientWidth'), ('nested', 'clientHeight')]:
            self.facts = copy.deepcopy(self.original)
            self.facts['scrollbars']['themes'][0]['measured'][target][dimension] -= 18
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, 'occupies a gutter'):
                self.verify()

    def test_all_four_native_keyboard_routes_are_required(self):
        self.facts['scrollbars']['keyboard'].pop()
        with self.assertRaisesRegex(ValueError, 'keyboard matrix'):
            self.verify()

    def test_synthetic_key_or_wrong_native_key_cannot_prove_scrolling(self):
        for change in [{'isTrusted':False}, {'key':'ArrowLeft'}]:
            self.facts = copy.deepcopy(self.original)
            self.facts['scrollbars']['keyboard'][0]['event'].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'trusted native key'):
                self.verify()

    def test_keyboard_cannot_move_root_or_unrequested_nested_axis(self):
        for target, field in [('rootAfter', 'scrollTop'), ('after', 'scrollTop')]:
            self.facts = copy.deepcopy(self.original)
            self.facts['scrollbars']['keyboard'][0][target][field] += 10
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, 'only its intended nested axis'):
                self.verify()

    def test_old_or_untrusted_keyboard_scrollend_cannot_complete_input(self):
        for change in [{'isTrusted':False}, {'at':0}, {'scrollLeft':999}]:
            self.facts = copy.deepcopy(self.original)
            self.facts['scrollbars']['keyboard'][0]['completion']['event'].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'own trusted scrollend'):
                self.verify()

    def test_both_shadow_modes_and_both_frame_origins_are_required_in_both_themes(self):
        self.facts['scrollbars']['encapsulated'][1]['kind'] = 'open'
        with self.assertRaisesRegex(ValueError, 'shadow/frame scrollbar theme matrix'):
            self.verify()

    def test_frame_hiding_must_not_depend_on_page_preload_css(self):
        self.facts['scrollbars']['encapsulated'][2]['before']['width'] = 'none'
        with self.assertRaisesRegex(ValueError, 'author scrolling was disabled'):
            self.verify()

    def test_shadow_roots_can_receive_user_origin_styles_without_changing_scroll_proof(self):
        for row in self.facts['scrollbars']['encapsulated']:
            if row['kind'] in ('open', 'closed'):
                row['before']['width'] = row['after']['width'] = 'none'
        result = self.verify()
        self.assertEqual(result['scrollbars']['encapsulatedScrolls'], 8)

    def test_closed_shadow_zero_gutter_is_measured_in_both_axes(self):
        for axis in ('gapX', 'gapY'):
            self.facts = copy.deepcopy(self.original)
            self.facts['scrollbars']['encapsulated'][1]['after'][axis] = 18
            with self.subTest(axis=axis), self.assertRaisesRegex(ValueError, 'still occupy gutters'):
                self.verify()

    def test_cross_origin_frame_cannot_be_relabelled_same_origin(self):
        self.facts['scrollbars']['encapsulated'][3]['frameURL'] = 'http://127.0.0.1:12345/mouse632-cross-frame'
        with self.assertRaisesRegex(ValueError, 'cross-origin frame was not exercised'):
            self.verify()

    def test_shadow_frame_scroll_requires_both_native_axes_to_move(self):
        row = self.facts['scrollbars']['encapsulated'][0]
        row['after']['x'] = row['before']['x']
        with self.assertRaisesRegex(ValueError, 'scroll both axes'):
            self.verify()

    def test_offscreen_frame_or_wrong_hit_target_cannot_pass(self):
        for change in [{'inside':False}, {'id':'different-element'}, {'viewport':{'width':10, 'height':10}}]:
            self.facts = copy.deepcopy(self.original)
            self.facts['scrollbars']['encapsulated'][2]['hit'].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'visibly hit'):
                self.verify()

    def test_untrusted_shadow_wheel_cannot_be_native_input(self):
        self.facts['scrollbars']['encapsulated'][1]['after']['events']['wheel'][0]['isTrusted'] = False
        with self.assertRaisesRegex(ValueError, 'fresh trusted wheel'):
            self.verify()

    def test_stale_cross_frame_scrollend_cannot_complete_new_wheel(self):
        row = self.facts['scrollbars']['encapsulated'][3]
        row['after']['events']['end'][0]['at'] = row['before']['at']-1
        with self.assertRaisesRegex(ValueError, 'own trusted scrollend'):
            self.verify()

    def test_nested_scroll_cannot_switch_desktop(self):
        self.facts['scrollbars']['encapsulated'][0]['desktopAfter']['bank'] = 'other-desk'
        with self.assertRaisesRegex(ValueError, 'switched the active Mouse desktop'):
            self.verify()

    def test_theme_switch_cannot_reload_a_frame(self):
        row = self.facts['scrollbars']['encapsulated'][6]
        row['before']['timeOrigin'] += 1
        row['after']['timeOrigin'] += 1
        with self.assertRaisesRegex(ValueError, 'replaced or moved the scrolling document'):
            self.verify()

    def test_theme_changes_cannot_restyle_the_site_input(self):
        self.facts['scrollbars']['themes'][0]['measured']['site']['input']['scheme'] = 'dark'
        with self.assertRaisesRegex(ValueError, 'restyled the website'):
            self.verify()

    def test_page_wheel_cannot_switch_a_mouse_desktop(self):
        self.facts['scrollbars']['themes'][0]['wheels']['root']['desktopAfter']['bank'] = 'desk-b'
        with self.assertRaisesRegex(ValueError, 'switched desktop'):
            self.verify()

    def test_page_wheel_cannot_scroll_both_containers(self):
        self.facts['scrollbars']['themes'][0]['wheels']['root']['after']['nested'] += 5
        with self.assertRaisesRegex(ValueError, 'intended container'):
            self.verify()

    def test_guest_screenshot_cannot_claim_native_compositor_capture(self):
        self.facts['scrollbars']['themes'][0]['screenshot']['nativeComposite'] = True
        with self.assertRaisesRegex(ValueError, 'source was mislabelled'):
            self.verify()

    def test_fixed_delay_cannot_substitute_for_scroll_completion(self):
        self.facts['scrollbars']['themes'][0]['wheels']['root']['completion'] = {'method':'120ms sleep'}
        with self.assertRaisesRegex(ValueError, 'own trusted scrollend'):
            self.verify()

    def test_previous_wheel_scrollend_cannot_complete_next_wheel(self):
        self.facts['scrollbars']['themes'][0]['wheels']['nested']['completion']['event']['wheelEventIndex'] = 0
        with self.assertRaisesRegex(ValueError, 'own trusted scrollend'):
            self.verify()

    def test_motion_after_scrollend_cannot_pass_completed_input(self):
        self.facts['scrollbars']['themes'][0]['wheels']['root']['completion']['afterTwoFrames']['root'] += 2
        with self.assertRaisesRegex(ValueError, 'stable final positions'):
            self.verify()

    def test_failed_or_unobserved_scrollend_cannot_complete_wheel(self):
        for target in ('status', 'trusted'):
            self.facts = copy.deepcopy(self.original)
            wheel = self.facts['scrollbars']['themes'][0]['wheels']['root']
            if target == 'status':
                wheel['status'] = 'failed'
            else:
                wheel['completion']['event']['isTrusted'] = False
            with self.assertRaisesRegex(ValueError, 'own trusted scrollend'):
                self.verify()


class RetainedVersionTests(unittest.TestCase):
    # Synthetic 630 runtime/schema expectations derived from the accepted
    # 629 split. These are unit fixtures, not an observed native 630 run.
    EXPECTED_RUNTIME_VERSIONS = {
        'mouse-628-local.json':'6.0.32',
        'mouse-628-progress.json':'6.0.32',
        'mouse-628-borderless.json':'6.0.28',
        'mouse-628-motion.json':'6.0.28',
        'mouse-628-desktop-transition.json':'6.0.28',
    }

    def facts(self):
        return {name:{'version':version} for name, version in self.EXPECTED_RUNTIME_VERSIONS.items()}

    def test_new_runtime_preserves_historical_geometry_schema_versions(self):
        evidence.verify_retained_versions(self.facts())

    def test_old_application_version_does_not_prove_current_local_or_progress(self):
        for name in ('mouse-628-local.json', 'mouse-628-progress.json'):
            with self.subTest(name=name):
                facts = self.facts()
                facts[name]['version'] = '6.0.28'
                with self.assertRaisesRegex(ValueError, 'retained version mismatch: '+name):
                    evidence.verify_retained_versions(facts)

    def test_geometry_and_motion_schema_cannot_be_silently_relabelled(self):
        for name in ('mouse-628-borderless.json', 'mouse-628-motion.json', 'mouse-628-desktop-transition.json'):
            with self.subTest(name=name):
                facts = self.facts()
                facts[name]['version'] = '6.0.32'
                with self.assertRaisesRegex(ValueError, 'retained version mismatch: '+name):
                    evidence.verify_retained_versions(facts)


class AcceptedAlgorithmMigrationTests(unittest.TestCase):
    def test_all_accepted_algorithms_only_change_runtime_versions_and_label(self):
        def functions(path):
            return {node.name:node for node in ast.parse(path.read_text()).body
                    if isinstance(node,ast.FunctionDef)}
        before=functions(ROOT/'tools/mouse631-ui-evidence.py')
        after=functions(ROOT/'tools/mouse632-ui-evidence.py')
        class RuntimeVersion(ast.NodeTransformer):
            def visit_Constant(self,node):
                if node.value=='6.0.31':node.value='6.0.32'
                if node.value=='Mouse630 retained UI evidence: ':node.value='Mouse632 retained UI evidence: '
                return node
        self.assertEqual(set(after)-set(before), {'verify_hidden_keyboard', 'verify_encapsulated_scrollbars'})
        self.assertEqual(set(before)-set(after), set())
        for name,node in before.items():
            if name == 'verify_scrollbars':
                continue
            with self.subTest(function=name):
                self.assertEqual(ast.dump(RuntimeVersion().visit(node)),ast.dump(after[name]))

    def test_old_runtime_cannot_prove_new_tutorial_ui_or_scrollbars(self):
        tutorial=fixture();tutorial['version']='6.0.29'
        with self.assertRaisesRegex(ValueError,'version/source'):
            evidence.verify_gesture(tutorial,lambda name:png())
        facts,images=ui_fixture();facts['version']='6.0.29'
        with self.assertRaisesRegex(ValueError,'version/platform'):
            evidence.verify_ui_regressions(facts,images.__getitem__)
        facts['version']='6.0.32';facts['scrollbars']['version']='6.0.29'
        with self.assertRaisesRegex(ValueError,'source, physical scope'):
            evidence.verify_scrollbars(facts['scrollbars'],images.__getitem__)


if __name__ == '__main__':
    unittest.main()
