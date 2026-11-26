"""Mutation tests for the independent reader; these images are unit fixtures,
never installed-app evidence or release screenshots."""
import copy
import importlib.util
import struct
import unittest
import zlib
from pathlib import Path

spec = importlib.util.spec_from_file_location('mouse638_acceptance', Path(__file__).with_name('mouse641-rendering-evidence.py'))
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)


def png(width, height, rows):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    raw = b''.join(b'\0' + bytes(channel for pixel in row for channel in pixel) for row in rows)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


def canvas(width=200, height=150, color=(80, 90, 100)):
    return [[list(color) for _ in range(width)] for _ in range(height)]


def paint(rows, bounds, color):
    for y in range(bounds['y'], bounds['y'] + bounds['height']):
        for x in range(bounds['x'], bounds['x'] + bounds['width']):
            rows[y][x] = list(color)


def captured(rows, *, name='mouse-638-unit.png', reference=None):
    height, width = len(rows), len(rows[0])
    blob = png(width, height, rows)
    files = {name: blob, name[:-4] + '-display.png': blob}
    dimensions = {'width': width, 'height': height}
    value = {'filename': name, 'sha256': V.P.digest(blob), 'pixelSize': dimensions,
             'displayFilename': name[:-4] + '-display.png', 'displaySha256': V.P.digest(blob), 'screenPixelSize': dimensions,
             'source': 'globalCapture.acquire(display)', 'kind': 'screen', 'backend': 'unit-fixture-only',
             'display': {'bounds': {'x': 0, 'y': 0, **dimensions}}, 'contentBounds': {'x': 0, 'y': 0, **dimensions},
             'cropPixels': {'x': 0, 'y': 0, **dimensions}, 'mapping': {'originX': 0, 'originY': 0, 'scaleX': 1, 'scaleY': 1}, 'probes': []}
    if reference is not None:
        ref = png(width, height, reference)
        files[name[:-4] + '-reference.png'] = ref
        value['reference'] = {'filename': name[:-4] + '-reference.png', 'sha256': V.P.digest(ref), 'pixelSize': dimensions}
    return files, value


def newtab_fixture():
    rows = canvas()
    regions = []
    for i, cls in enumerate(('home-welcome', 'home-favorites-title', 'home-site-label')):
        b = {'x': 30, 'y': 25 + i * 20, 'width': 25, 'height': 10}
        paint(rows, {**b, 'width': 5}, [255] * 3)
        regions.append({'kind': 'text', 'className': cls, 'text': 'LABEL', 'color': 'rgb(255, 255, 255)', 'bounds': b})
    icon = {'x': 100, 'y': 40, 'width': 20, 'height': 20}
    paint(rows, icon, [235] * 3)
    paint(rows, {**icon, 'width': 5}, [50, 60, 70])
    regions.append({'kind': 'icon', 'className': 'home-site-icon', 'text': '1', 'color': 'rgb(52, 71, 91)', 'bounds': icon})
    receipt = {'name': 'unit-only', 'capture': 'mouse-638-unit.png', 'state': {'background': 'aurora', 'backgroundImage': 'linear-gradient(unit-only)', 'zoom': .8,
               'bounds': {'x': 0, 'y': 0, 'width': 200, 'height': 150}, 'regions': regions}}
    return rows, receipt


def native(width, height):
    bounds = {'x': 0, 'y': 0, 'width': width, 'height': height}
    return {'visible': True, 'parentVisible': True, 'cachedVisible': True, 'attached': True,
            'bounds': bounds, 'viewBounds': bounds, 'parentBounds': None, 'actualBounds': bounds}


def tone_fixture():
    rows = canvas(200, 150, (24, 24, 24))
    elements = []
    for i, (ident, color, tag) in enumerate((('neutral-light', [160] * 3, 'text'), ('colored-link', [45, 145, 235], None), ('light-panel', [190] * 3, None))):
        bounds = {'x': 20, 'y': 15 + i * 30, 'width': 80, 'height': 20}
        paint(rows, {**bounds, 'width': 6}, color)
        elements.append({'id': ident, 'bounds': bounds, 'color': 'rgb('+', '.join(map(str, color))+')', 'fill': 'rgb('+', '.join(map(str, color))+')', 'tag': tag})
    media = {'x': 20, 'y': 110, 'width': 40, 'height': 20}
    paint(rows, media, [235, 40, 155])
    elements.append({'id': 'media', 'bounds': media})
    for i, ident in enumerate(('inherit-light', 'inherit-blue')):
        bounds = {'x': 110, 'y': 15 + i * 30, 'width': 40, 'height': 20}
        paint(rows, {**bounds, 'width': 6}, [255] * 3)
        elements.append({'id': ident, 'bounds': bounds, 'color': 'rgb(255, 255, 255)', 'fill': 'rgb(255, 255, 255)', 'tag': None})
    svg = {'x': 110, 'y': 110, 'width': 40, 'height': 20}
    paint(rows, svg, [255] * 3)
    elements.append({'id': 'inherit-svg', 'bounds': svg, 'color': 'rgb(255, 255, 255)', 'fill': 'rgb(255, 255, 255)', 'svgFill': 'rgb(255, 255, 255)'})
    files, value = captured(rows)
    value['probes'] = [{'kind': 'media', 'point': {'x': 40, 'y': 120}, 'expectedRGB': [235, 40, 155], 'x': 40, 'y': 120,
                        'actualRGBA': [235, 40, 155, 255], 'tolerance': 3},
                       {'kind': 'currentColor-svg', 'point': {'x': 130, 'y': 120}, 'expectedRGB': [255] * 3, 'x': 130, 'y': 120,
                        'actualRGBA': [255] * 4, 'tolerance': 3}]
    receipt = {'name': 'minimum', 'channel': 160, 'capture': value['filename'], 'native': native(200, 150),
               'appearance': {'theme': 'dark', 'whiteTone': 0}, 'pageTone': {'theme': 'dark', 'whiteTone': 0, 'color': '#A0A0A0'}, 'dom': {'elements': elements}}
    return rows, files, value, receipt


def store_control_fixture():
    # Unit-only receipt and pixels: never copied into native release evidence.
    ident = 'eimadpbcbfnmbkopoojfekhnkhdbieeh'
    url = 'https://chromewebstore.google.com/detail/dark-reader/' + ident + '?hl=en'
    files, detail = captured(canvas(), name='mouse-638-unit-store-detail.png')
    other, control = captured(canvas(), name='mouse-638-unit-store-control.png')
    files.update(other)
    detail['pid'] = control['pid'] = 123
    selector = '#mouse-extensions-install-page'
    click = {'action': 'click', 'selector': selector, 'tabId': None, 'pid': 123, 'source': 'CGEvent', 'at': 1001,
             'point': {'x': 90, 'y': 56}, 'events': [{'type': 'click', 'trusted': True, 'matches': True, 'selector': selector, 'x': 90, 'y': 56}]}
    installed = {'installPath': 'browser-control', 'pid': 123, 'storeURL': url, 'storePage': {'url': url, 'api': 'undefined', 'button': None},
                 'storeOwner': {'tabId': 'owned-store', 'webContentsId': 7, 'url': url,
                                'native': {**native(200, 150), 'tabId': 'owned-store', 'webContentsId': 7}},
                 'shellWebContentsId': 2, 'storeCapture': detail['filename'], 'installInput': click,
                 'installControl': {'selector': selector, 'tabId': 'owned-store', 'managerOpen': True, 'visible': True, 'disabled': False,
                                    'bounds': {'x': 20, 'y': 40, 'width': 140, 'height': 32}, 'capture': control['filename']},
                 'bridge': {'requestSource': 'browser-control', 'completionSource': 'browser-control', 'tabId': 'owned-store', 'webContentsId': 7,
                            'nativeGestureWebContentsId': 2, 'extensionId': ident, 'url': url, 'result': 'success',
                            'nativeGestureType': 'mouseDown', 'nativeGestureAt': 1000, 'beginAt': 1010, 'installedAt': 1200, 'completeAt': 1210}}
    facts = {'pid': 123, 'platform': 'darwin', 'nativeInputs': [click]}
    return ident, files, installed, facts, {detail['filename']: detail, control['filename']: control}


class NativePixels(unittest.TestCase):
    def test_actual_png_hash_crop_mapping_and_full_screen_are_bound(self):
        rows = canvas()
        files, value = captured(rows)
        V.capture(files.__getitem__, value)
        bad = copy.deepcopy(value)
        bad['mapping']['scaleX'] = .8
        with self.assertRaisesRegex(ValueError, 'DPI'):
            V.capture(files.__getitem__, bad)
        files[value['displayFilename']] = png(200, 150, canvas(color=(20, 20, 20)))
        value['displaySha256'] = V.P.digest(files[value['displayFilename']])
        with self.assertRaisesRegex(ValueError, 'actual full display'):
            V.capture(files.__getitem__, value)

    def test_newtab_missing_background_text_and_icons_fail_even_with_rehashed_success_metadata(self):
        original, receipt = newtab_fixture()
        files, value = captured(original, reference=original)
        result = V.verify_newtab(files.__getitem__, receipt, {value['filename']: value})
        self.assertEqual(result['backgroundSamples'], 14)
        for defect in ('opaque-upper-page', 'missing-heading', 'missing-icon'):
            rows = copy.deepcopy(original)
            if defect == 'opaque-upper-page':
                paint(rows, {'x': 0, 'y': 0, 'width': 200, 'height': 105}, [16, 21, 30])
            elif defect == 'missing-heading':
                paint(rows, receipt['state']['regions'][0]['bounds'], [80, 90, 100])
            else:
                paint(rows, receipt['state']['regions'][-1]['bounds'], [235] * 3)
            changed, report = captured(rows, reference=original)
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                V.verify_newtab(changed.__getitem__, receipt, {report['filename']: report})

    def test_blank_compositor_reference_cannot_make_blank_os_text_pass(self):
        rows, receipt = newtab_fixture()
        paint(rows, receipt['state']['regions'][1]['bounds'], [80, 90, 100])
        files, value = captured(rows, reference=rows)
        with self.assertRaisesRegex(ValueError, 'blank label'):
            V.verify_newtab(files.__getitem__, receipt, {value['filename']: value})

    def test_tone_requires_actual_glyphs_and_protects_coloured_fill_and_media(self):
        rows, files, value, receipt = tone_fixture()
        V.verify_tone(files.__getitem__, receipt, {value['filename']: value})
        bad = copy.deepcopy(receipt)
        bad['dom']['elements'][1]['fill'] = 'rgb(160, 160, 160)'
        with self.assertRaisesRegex(ValueError, 'text-fill'):
            V.verify_tone(files.__getitem__, bad, {value['filename']: value})
        paint(rows, receipt['dom']['elements'][0]['bounds'], [24] * 3)
        changed, replacement = captured(rows)
        replacement['probes'] = value['probes']
        with self.assertRaisesRegex(ValueError, 'glyph colour'):
            V.verify_tone(changed.__getitem__, receipt, {replacement['filename']: replacement})

    def test_native_probe_rejects_rewritten_expected_rgb_and_actual_json(self):
        files, value = captured(canvas())
        pixels, mapping = V.capture(files.__getitem__, value)
        expected = {'kind': 'seam', 'point': {'x': 10, 'y': 10}, 'expectedRGB': [80, 90, 100]}
        actual = {**expected, 'x': 10, 'y': 10, 'actualRGBA': [80, 90, 100, 255], 'tolerance': 3}
        V.verify_probe(pixels, mapping, actual, expected)
        for mutation in ({'expectedRGB': [16, 21, 30]}, {'actualRGBA': [16, 21, 30, 255]}, {'tolerance': 100}):
            with self.assertRaises(ValueError):
                V.verify_probe(pixels, mapping, {**actual, **mutation}, expected)

    def test_zero_or_fractional_square_separator_is_rejected_before_pixel_read(self):
        state = {'appearance': {'paneMode': 'square'}, 'theme': 'dark', 'gap': 0, 'radius': 0, 'seam': '#354357'}
        for gap in (0, .5, 2):
            state['gap'] = gap
            with self.assertRaisesRegex(ValueError, 'grid seam'):
                V.verify_grid(lambda _: b'', {'state': state}, {}, {})


class NativeProvenance(unittest.TestCase):
    def test_synthetic_events_and_wrong_process_or_backend_cannot_pass_native_input(self):
        entry = {'action': 'click', 'pid': 123, 'source': 'XTest', 'events': [{'type': 'click', 'trusted': True, 'matches': True}]}
        V.verify_input(entry, 'linux', 123)
        for bad in ({**entry, 'pid': 999}, {**entry, 'source': 'DOM.click'}, {**entry, 'events': [{'type': 'click', 'trusted': False, 'matches': True}]}):
            with self.assertRaises(ValueError):
                V.verify_input(bad, 'linux', 123)

    def test_success_booleans_do_not_replace_signed_live_store_bytes(self):
        facts = {'webStore': {'write': {'liveStore': True, 'installed': True, 'installPath': 'browser-control'}, 'restart': {'restored': True, 'removed': True}}}
        with self.assertRaisesRegex(ValueError, 'extension identity'):
            V.verify_webstore(lambda _: b'', facts)


class BrowserControlReceipt(unittest.TestCase):
    def test_real_mouse_control_does_not_require_google_chrome_install_eligibility(self):
        ident, files, installed, facts, captures = store_control_fixture()
        for google_button in (None, {'disabled': True, 'text': 'Add to Chrome'}):
            installed['storePage']['button'] = google_button
            self.assertEqual(V.verify_webstore_install_control(files.__getitem__, installed, facts, captures, ident), installed['bridge'])

    def test_store_source_and_native_owner_cannot_be_swapped(self):
        cases = [('installPath', 'webstore-private'), ('storeURL', 'https://example.test/detail/' + 'eimadpbcbfnmbkopoojfekhnkhdbieeh'),
                 ('storePage.url', 'https://chromewebstore.google.com/'), ('storeOwner.url', 'https://example.test/'),
                 ('storeOwner.native.webContentsId', 99), ('storeOwner.native.tabId', 'another-tab'),
                 ('storeOwner.native.attached', False), ('shellWebContentsId', 7), ('pid', 456)]
        self.reject_mutations(cases)

    def test_mouse_button_and_trusted_click_must_match_the_observed_shell_point(self):
        cases = [('installControl.tabId', 'another-tab'), ('installControl.managerOpen', False), ('installControl.visible', False),
                 ('installControl.disabled', True), ('installControl.bounds.x', -20),
                 ('installInput.tabId', 'owned-store'), ('installInput.selector', 'button.add-to-chrome'),
                 ('installInput.point.x', 190), ('installInput.events.0.trusted', False),
                 ('installInput.events.0.x', 100), ('installInput.events.0.selector', 'button.add-to-chrome')]
        self.reject_mutations(cases)

    def test_production_receipt_must_bind_guest_shell_route_and_time(self):
        cases = [('bridge.requestSource', 'webstore-private'), ('bridge.completionSource', 'completeInstall'),
                 ('bridge.tabId', 'another-tab'), ('bridge.webContentsId', 8), ('bridge.nativeGestureWebContentsId', 7),
                 ('bridge.extensionId', 'a' * 32), ('bridge.url', 'https://example.test/'), ('bridge.result', 'user_cancelled'),
                 ('bridge.nativeGestureType', 'keyDown'), ('bridge.nativeGestureAt', 4000), ('bridge.completeAt', 1100)]
        self.reject_mutations(cases)

    def test_control_images_and_native_input_remain_bound(self):
        ident, files, installed, facts, captures = store_control_fixture()
        facts['nativeInputs'] = []
        with self.assertRaisesRegex(ValueError, 'bound native shell click'):
            V.verify_webstore_install_control(files.__getitem__, installed, facts, captures, ident)
        facts['nativeInputs'] = [installed['installInput']]
        files[installed['installControl']['capture']] = png(200, 150, canvas(color=(0, 0, 0)))
        with self.assertRaisesRegex(ValueError, 'hash differs'):
            V.verify_webstore_install_control(files.__getitem__, installed, facts, captures, ident)

    def reject_mutations(self, cases):
        for path, value in cases:
            ident, files, installed, facts, captures = store_control_fixture()
            target = installed
            keys = path.split('.')
            for key in keys[:-1]:
                target = target[int(key)] if isinstance(target, list) else target[key]
            target[keys[-1]] = value
            with self.subTest(path=path), self.assertRaises(ValueError):
                V.verify_webstore_install_control(files.__getitem__, installed, facts, captures, ident)


if __name__ == '__main__':
    unittest.main()
