#!/usr/bin/env python3
"""Negative acceptance checks for the 629 release validator, not native evidence."""
import copy
import importlib.util
import math
import pathlib
import struct
import unittest
from unittest import mock
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mouse629_evidence', ROOT/'tools/mouse629-evidence.py')
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
    return {'version':'6.0.29', 'recognizer':'two-finger-or-wheel', 'source':'nora-wheel',
            'syntheticNativeEvent':True, 'physicalTrackpadVerified':False,
            **{key:True for key in ('firstUseShown','nonSwitchRetained','successHidden',
                                   'reopenHidden','restartHidden','privateIsolated','restored')},
            'writePid':100, 'writeMainTimeOrigin':1000, 'writeRendererTimeOrigin':1100,
            'records':records,
            'restart':{'pid':200, 'mainTimeOrigin':2000, 'timeOrigin':2100,
                       'version':'6.0.29', 'persisted':{'completed':True},
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


def scrollbar_fixture(images):
    site = {'background':'rgb(22, 22, 22)', 'color':'rgb(237, 237, 237)', 'rootScheme':'light',
            'input':{'background':'rgb(255, 255, 255)', 'color':'rgb(0, 0, 0)', 'scheme':'light',
                     'border':'rgb(118, 118, 118)', 'appearance':'auto'}}
    facts = {'version':'6.0.29', 'source':'installed guest WebContents + bundled preload',
             'physicalTrackpadVerified':False, 'restored':True,
             'fixture':{'tabId':'scroll-page', 'webContentsId':10, 'desktop':'desk-a',
                        'url':'http://127.0.0.1:12345/mouse629-scrollbars',
                        'authorScrollbar':{'width':'auto', 'rootThumb':'#aaaaaa', 'nestedThumb':'#cccccc',
                                           'track':'white', 'priority':'important'}}, 'themes':[]}
    tops, events, previous = {'root':300, 'nested':80}, [], None
    for theme in ('dark', 'light'):
        thumb, track = (104, 23) if theme == 'dark' else (139, 245)
        style = {'width':'thin', 'color':f'rgb({thumb}, {thumb}, {thumb}) rgb({track}, {track}, {track})',
                 'corner':f'rgb({track}, {track}, {track})', 'scheme':'light',
                 'overflowX':'scroll', 'overflowY':'scroll', 'clientWidth':320, 'clientHeight':220,
                 'offsetWidth':322, 'offsetHeight':222, 'scrollWidth':900, 'scrollHeight':1000, 'scrollLeft':40}
        measured = {'viewport':{'width':500, 'height':450, 'devicePixelRatio':1}, 'timeOrigin':1000,
                    'media':{'dark':theme == 'dark', 'forcedColors':False}, 'site':copy.deepcopy(site),
                    'wheelEvents':copy.deepcopy(events),
                    **{key:dict(style, scrollTop=value) for key, value in tops.items()}}
        before_theme = copy.deepcopy(previous or measured)
        wheels = {}
        for target in ('root', 'nested'):
            point = {'x':100 if target == 'nested' else 455, 'y':190 if target == 'nested' else 395,
                     'nested':target == 'nested', 'hit':'DIV' if target == 'nested' else 'BODY', 'inside':True}
            event = {'isTrusted':True, 'nested':target == 'nested', 'x':point['x'], 'y':point['y'],
                     'deltaX':0, 'deltaY':160, 'deltaMode':0, 'at':len(events)+1}
            after_tops = dict(tops)
            after_tops[target] += 160
            wheels[target] = {'input':{'type':'mouseWheel', 'x':point['x'], 'y':point['y'], 'deltaX':0, 'deltaY':-160},
                              'point':point, 'event':event, 'before':dict(tops), 'after':after_tops,
                              'desktopBefore':{'bank':'desk-a', 'shell':'desk-a'},
                              'desktopAfter':{'bank':'desk-a', 'shell':'desk-a'}}
            tops = after_tops
            events.append(event)
        after = copy.deepcopy(measured)
        after['wheelEvents'] = copy.deepcopy(events)
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
    return facts


def ui_fixture():
    images = {}
    panes = [{'id':'page-'+str(i), 'bounds':{'x':10+i*80, 'y':80, 'width':70, 'height':100}} for i in range(7)]
    facts = {'version':'6.0.29', 'baselineVersion':'6.0.27', 'platform':'darwin', 'arch':'arm64',
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
        self.assertEqual(result['scrollbars']['nativeWheelScrolls'], 4)
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
        self.facts['scrollbars']['themes'][0]['measured']['root']['color'] = 'rgb(170, 170, 170) rgb(255, 255, 255)'
        with self.assertRaisesRegex(ValueError, 'author white style'):
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


class ReleaseTemplateTests(unittest.TestCase):
    def test_unready_pin_rejects_validation_without_network_access(self):
        spec = importlib.util.spec_from_file_location('test_mouse629_release', ROOT/'tools/mouse629-release.py')
        publisher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(publisher)
        publisher.PIN = dict(publisher.PIN, ready=False)
        with mock.patch.object(publisher, 'api', side_effect=AssertionError('Unexpected network action')):
            with self.assertRaisesRegex(ValueError, 'successful source artifacts have not been bound'):
                publisher.validate()


if __name__ == '__main__':
    unittest.main()
