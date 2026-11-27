"""Synthetic adversarial reader fixtures; these do not represent native runs."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import unittest
import zlib

spec = importlib.util.spec_from_file_location('mouse642_controls', Path(__file__).with_name('mouse642-controls-evidence.py'))
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)


def encode(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def png(width, height, pixels):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    rows = b''.join(b'\0' + bytes(pixels[y * width * 4:(y + 1) * width * 4]) for y in range(height))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')


def identity(read=False):
    return {'id': 'owned-read' if read else 'owned-write', 'index': 0, 'desk': 'owned-desk', 'webContentsId': 80 if read else 70,
            'identity': 'document-read' if read else 'document-write', 'timeOrigin': 12000 if read else 10000,
            'url': 'http://127.0.0.1:' + ('4101' if read else '4100') + '/page/0/', 'navigationEpoch': 1, 'ticks': 10}


def screen(name, read=False, shell_only=False):
    width, height = 400, 300
    pixels = bytearray([240, 240, 240, 255] * width * height)
    for y in range(10, 110):
        for x in range(10, 270):
            at = (y * width + x) * 4
            pixels[at:at + 4] = bytes(([25, 30, 40, 255], [120, 130, 140, 255], [240, 245, 250, 255])[(x + y) % 3])
    owner = identity(read)
    page = {'x': 0, 'y': 130, 'width': 400, 'height': 170}
    native = {'tabId': owner['id'], 'index': 0, 'desk': owner['desk'], 'webContentsId': owner['webContentsId'],
              'visible': True, 'parentVisible': True, 'cachedVisible': True, 'attached': True,
              'bounds': page, 'viewBounds': page, 'parentBounds': None, 'actualBounds': page}
    regions, probes = [], []
    for part, x, color in [('a', 32, [40, 55, 65]), ('b', 224, [141, 92, 148])]:
        box = {'x': x, 'y': 78, 'width': 144, 'height': 34}
        regions.append({'part': part, 'bounds': box, 'color': 'rgb(' + ', '.join(map(str, color)) + ')'})
        for py in range(page['y'] + box['y'], page['y'] + box['y'] + box['height']):
            for px in range(x, x + box['width']):
                at = (py * width + px) * 4; pixels[at:at + 4] = bytes(color + [255])
        for dx, dy in ((0, 0), (-6, 0), (6, 0), (0, -6), (0, 6)):
            point = {'x': x + 72 + dx, 'y': 130 + 78 + 17 + dy}
            probes.append({'tabId': owner['id'], 'index': 0, 'desk': owner['desk'], 'webContentsId': owner['webContentsId'],
                           'region': part, 'offset': {'x': dx, 'y': dy}, 'localBounds': box, 'cssPoint': point,
                           'x': point['x'], 'y': point['y'], 'expectedRGB': color, 'actualRGBA': color + [255], 'tolerance': 3})
    full = bytearray([20, 20, 20, 255] * 480 * 360)
    for y in range(height):
        full[((y + 30) * 480 + 40) * 4:((y + 30) * 480 + 40 + width) * 4] = pixels[y * width * 4:(y + 1) * width * 4]
    raw, full_raw = png(width, height, pixels), png(480, 360, full)
    full_name, reference = name[:-4] + '-display.png', name[:-4] + '-shell-reference.png'
    label = '#settings-language' if shell_only else '#input-correction-bubble' if 'correction-offer' in name else '#temperature-panel'
    region = {'x': 20, 'y': 20, 'width': 143, 'height': 22} if shell_only else {'x': 10, 'y': 10, 'width': 240, 'height': 90}
    receipt = {'filename': name, 'source': 'globalCapture.acquire(display)', 'kind': 'screen', 'backend': 'synthetic-test-only',
               'sha256': C.sha(raw), 'pixelSize': {'width': width, 'height': height}, 'displayFilename': full_name,
               'displaySha256': C.sha(full_raw), 'screenPixelSize': {'width': 480, 'height': 360},
               'display': {'bounds': {'x': 0, 'y': 0, 'width': 480, 'height': 360}},
               'contentBounds': {'x': 40, 'y': 30, 'width': width, 'height': height},
               'cropPixels': {'x': 40, 'y': 30, 'width': width, 'height': height},
               'mapping': {'originX': 0, 'originY': 0, 'scaleX': 1, 'scaleY': 1},
               'native': [] if shell_only else [native], 'content': [] if shell_only else [{'tabId': owner['id'], 'index': 0, 'identity': owner['identity'], 'regions': regions}],
               'probes': [] if shell_only else probes, 'attempts': [{'sequence': 1, 'accepted': True}],
               'shell': {'filename': reference, 'sha256': C.sha(raw), 'pixelSize': {'width': width, 'height': height}, 'regions': [{'label': label, 'bounds': region}]}}
    if shell_only: receipt.update(pid=101, shellOnly=True)
    return receipt, {name: raw, full_name: full_raw, reference: raw}


def tone(index):
    values = [(55, 0, 55, 0, 'light', '#D4D4D4', '#172033', '#F3F5F9', '#FFFFFF'),
              (80, 50, 55, 0, 'light', '#ECE5DC', '#172033', '#F3EEE9', '#FFF8EF'),
              (99, 50, 55, 0, 'light', '#FEF7EE', '#172033', '#F3EEE9', '#FFF8EF'),
              (99, 50, 1, 75, 'dark', '#FEF7EE', '#010101', '#070708', '#101318'),
              (99, 50, 1, 99, 'dark', '#FEF7EE', '#010101', '#090705', '#121315')]
    white, temperature, black, black_temperature, theme, white_color, black_color, background, panel = values[index]
    controls = {'whiteTone': white, 'whiteTemperature': temperature, 'blackTone': black, 'blackTemperature': black_temperature}
    appearance = {'paneMode': 'rounded', 'whiteTone': white}
    custom = {key: value for key, value in [('whiteTemperature', temperature), ('blackTone', black), ('blackTemperature', black_temperature)]
              if value != {'whiteTemperature': 0, 'blackTone': 55, 'blackTemperature': 0}[key]}
    if custom: appearance['tones'] = custom
    return {'appearance': appearance, 'stored': None if index == 0 else copy.deepcopy(appearance), 'quick': controls, 'settings': copy.deepcopy(controls),
            'theme': theme, 'white': white_color, 'black': black_color, 'background': background, 'panel': panel}


def input_receipt(selector, pid=101, tab_id=None):
    return {'selector': selector, 'pid': pid, 'tabId': tab_id, 'source': 'XTest', 'at': 1500,
            'point': {'x': 60, 'y': 80}, 'events': [{'type': 'click', 'trusted': True, 'matches': True}]}


def language_fixture():
    def state(code):
        return {'available': True, 'platform': 'linux', 'currentId': 'layout-' + code,
                'layouts': [{'id': 'layout-' + item, 'language': item, 'label': item.upper(), 'active': item == code} for item in ('en', 'ru')]}
    return {'before': state('en'), 'restored': state('en'), 'ruId': 'layout-ru', 'enId': 'layout-en', 'ru': state('ru'), 'en': state('en'),
            'oneTap': {'currentId': 'layout-ru', 'locale': 'ru'},
            'physicalKeys': [{'language': code, 'layoutId': 'layout-' + code, 'value': char, 'indicator': code.upper(),
                              'delivery': {'source': 'XTest', 'key': 'physical-G', 'unicodeInjection': False},
                              'events': [{'trusted': True, 'value': char, 'inputType': 'insertText'}]} for code, char in [('ru', 'п'), ('en', 'g')]]}


def correction_fixture():
    edit = {'value': C.EXPECTED, 'events': [{'trusted': True, 'value': C.EXPECTED, 'inputType': 'insertText'}]}
    return {'sample': C.SAMPLE, 'expected': C.EXPECTED, 'before': C.SAMPLE, 'noAutoReplacement': True, 'capture': C.CAPTURES[3],
            'insertion': {'method': 'WebContents.insertText', 'events': [{'trusted': True, 'value': C.SAMPLE, 'inputType': 'insertText'}]},
            'accepted': {**copy.deepcopy(edit), 'token': '12345678-1234-4234-8234-123456789abc'},
            'editable': copy.deepcopy(edit), 'shell': copy.deepcopy(edit),
            'paragraph': {'value': C.EXPECTED, 'prefix': 'Earlier paragraph stays.',
                          'beforeText': 'Earlier paragraph stays.' + C.SAMPLE, 'afterText': 'Earlier paragraph stays.' + C.EXPECTED,
                          'hostPreserved': True, 'wrappersPreserved': True, 'textNodesPreserved': True,
                          'unmodifiedTextNodesPreserved': True, 'editedTextNodeReplaced': False,
                          'undo': {'value': C.SAMPLE, 'prefix': 'Earlier paragraph stays.', 'hostPreserved': True,
                                   'wrappersPreserved': True, 'source': 'WebContents.undo'},
                          'events': [{'trusted': True, 'value': 'Earlier paragraph stays.' + C.EXPECTED, 'inputType': 'insertText'}]},
            'undo': {'value': C.SAMPLE, 'source': 'WebContents.undo'}, 'rejected': {'value': C.SAMPLE, 'visible': False},
            'stale': {'result': {'ok': False, 'reason': 'stale-target'}, 'value': C.SAMPLE + 'x'},
            'safe': [{'selector': selector, **({'kind': kind} if kind else {}), 'suggestion': False, 'valueUnchanged': True}
                     for selector, kind in [('#password', None), ('#mail', None), ('#field', 'english'), ('#field', 'russian'), ('#field', 'mixed')]],
            'pageBefore': identity(), 'pageAfter': {**identity(), 'ticks': 20}}


def fixture():
    files, captures = {}, []
    for index, name in enumerate(C.CAPTURES):
        receipt, raw = screen(name, read=index == 4, shell_only=index == 2); captures.append(receipt); files.update(raw)
    selectors = ['#input-language-more', '#input-language-button', '[data-input-layout="layout-ru"]', '[data-input-layout="layout-en"]',
                 '#temperature-button', '[data-tone-kind-tab=white]', '[data-tone-kind-tab=black]',
                 '#temperature-panel [data-tone-family=white][data-tone-preset=paper]', '#temperature-panel [data-tone-family=black][data-tone-preset="warm"]',
                 '#temperature-panel [data-tone-theme=light]', '#temperature-panel [data-tone-theme=dark]', '#quick-white-tone', '#quick-black-tone',
                 '#settings-button', '.settings-nav-item[data-settings-page=appearance]', '#settings-black-temperature', '[data-input-correction=reject]',
                 '#field', '#editor', '#password', '#mail', '#mouse642-shell-edit'] + ['[data-input-correction=accept]'] * 4
    inputs = [input_receipt(selector, tab_id='owned-write' if selector in ('#field', '#editor', '#password', '#mail') else None) for selector in selectors]
    tones = {'initial': tone(0), 'changes': [{'kind': kind, 'state': tone(index)} for index, kind in enumerate(['white-preset', 'white-slider', 'black-slider', 'settings-slider'], 1)],
             'light': {**tone(2), 'capture': C.CAPTURES[0]}, 'dark': {**tone(3), 'capture': C.CAPTURES[1]}, 'saved': tone(4)}
    for key, selector, value in [('whiteRange', '#quick-white-tone', 99), ('blackRange', '#quick-black-tone', 1), ('settingsRange', '#settings-black-temperature', 99)]:
        tones[key] = {'selector': selector, 'value': value, 'source': 'XTest', 'events': [{'trusted': True, 'value': value}]}
    written = {'schema': 1, 'version': '6.0.42', 'platform': 'linux', 'arch': 'x64', 'pid': 101, 'writePid': 101,
               'packaged': True, 'profile': '/isolated/controls642', 'physicalUserDeviceVerified': False, 'phase': 'write',
               'ok': False, 'writeComplete': True, 'awaitingRestart': True, 'elapsedMs': 5000,
               'fixtureOrigin': 'http://127.0.0.1:4100', 'nativeInputs': inputs, 'captures': captures[:-1],
               'cleanup': {'restored': True, 'desktopStateRestored': True},
               'write': {'pid': 101, 'startedAt': 1000, 'completedAt': 4000, 'tones': tones, 'language': language_fixture(), 'correction': correction_fixture(),
                         'footer': {'hasInterfaceLocale': False, 'hasTemperature': True, 'hasInputIndicator': True, 'hasSettingsLocale': True, 'locale': 'ru'},
                         'settingsArrow': {'appearance': 'none', 'paddingRight': 37, 'backgroundPosition': 'calc(100% - 14px) 50%',
                                           'capture': C.CAPTURES[2], 'bounds': {'x': 15, 'y': 15, 'width': 153, 'height': 32}}}}
    facts = {**copy.deepcopy(written), 'phase': 'read', 'ok': True, 'awaitingRestart': False, 'fixtureOrigin': 'http://127.0.0.1:4101',
             'captures': captures, 'nativeInputs': inputs + [input_receipt('#temperature-button', pid=102)],
             'restart': {**tone(4), 'pid': 102, 'startedAt': 10000, 'completedAt': 12000, 'capture': C.CAPTURES[4]}}
    processes = {'schema': 1, 'version': '6.0.42', 'platform': 'linux', 'arch': 'x64', 'executable': '/installed/mouse-browser',
                 'executableSha256': 'a' * 64, 'profile': '/isolated/controls642'}
    for phase, pid, marker in [('write', 101, 'MOUSE_642_CONTROLS_WRITE_PASS'), ('read', 102, 'MOUSE_642_CONTROLS_NATIVE_PASS')]:
        log = 'mouse-642-controls-' + phase + '.log'; files[log] = (marker + '\nMOUSE_642_PROCESS_RETURN pid=' + str(pid) + ' code=0 elapsedMs=5000\n').encode()
        processes[phase] = {'pid': pid, 'exitCode': 0, 'elapsedMs': 5000, 'log': log, 'logSha256': C.sha(files[log]), 'requiredMarkers': [marker]}
    return files, facts, written, processes


def sealed(files, facts, written, processes):
    files = dict(files)
    files['mouse-642-controls.json'] = encode(facts); files['mouse-642-controls-write.json'] = encode(written)
    processes = copy.deepcopy(processes)
    for phase, name in [('write', 'mouse-642-controls-write.json'), ('read', 'mouse-642-controls.json')]:
        processes[phase].update(report=name, reportSha256=C.sha(files[name]))
    processes['reportSha256'] = C.sha(files['mouse-642-controls.json']); files['mouse-642-controls-processes.json'] = encode(processes)
    return files


class Controls642Reader(unittest.TestCase):
    def test_exact_key_mapping_retains_the_owner_typo_without_spelling_changes(self):
        self.assertEqual(C.EXPECTED, 'пример текста для демонстран=ции не верной раскладки пользователя -')
        C.correction(correction_fixture())
        changed = correction_fixture(); changed['expected'] = changed['expected'].replace('демонстран=ции', 'демонстрации')
        with self.assertRaisesRegex(ValueError, 'exact physical-key'): C.correction(changed)

    def test_real_layouts_require_nonunicode_physical_input_and_unchanged_original_sources(self):
        C.language(language_fixture(), 'ru', 'linux')
        for mutate in [lambda value: value['physicalKeys'][0]['delivery'].update(unicodeInjection=True),
                       lambda value: value['physicalKeys'][0].update(value='g'),
                       lambda value: value['physicalKeys'][1]['events'][0].update(trusted=False),
                       lambda value: value['ru'].update(currentId='layout-en'),
                       lambda value: value['restored']['layouts'].pop(),
                       lambda value: value['oneTap'].update(locale='en')]:
            value = language_fixture(); mutate(value)
            with self.assertRaises(ValueError): C.language(value, 'ru', 'linux')

    def test_tone_color_computation_and_quick_settings_storage_bindings(self):
        for index in range(5): C.tone_state(tone(index), allow_unstored_default=index == 0)
        for mutate in [lambda value: value.update(white='#FFFFFF'), lambda value: value.update(black='#777777'),
                       lambda value: value.update(background='#10151E'), lambda value: value['quick'].update(whiteTone=3),
                       lambda value: value.update(stored=None)]:
            value = tone(4); mutate(value)
            with self.assertRaises(ValueError): C.tone_state(value)
        with self.assertRaises(ValueError): C.tone_state(tone(0))

    def test_consent_cannot_bypass_undo_stale_sensitive_or_normal_text_guards(self):
        for mutate in [lambda value: value.update(noAutoReplacement=False), lambda value: value['undo'].update(value=C.EXPECTED),
                       lambda value: value['stale']['result'].update(ok=True), lambda value: value['rejected'].update(value=C.EXPECTED),
                       lambda value: value['safe'][0].update(suggestion=True), lambda value: value['safe'].pop(),
                       lambda value: value['accepted']['events'][0].update(trusted=False), lambda value: value['paragraph'].update(value=C.SAMPLE),
                       lambda value: value['paragraph'].update(textNodesPreserved=False), lambda value: value['paragraph'].update(afterText=C.EXPECTED),
                       lambda value: value['pageAfter'].update(identity='new-document')]:
            value = correction_fixture(); mutate(value)
            with self.assertRaises(ValueError): C.correction(value)

    def test_actual_input_requires_native_source_target_and_trusted_click(self):
        C.native_input(input_receipt('#button'), 'linux', 101)
        for mutation in [{'source': 'script'}, {'pid': 102}, {'events': [{'type': 'click', 'trusted': False, 'matches': True}]}, {'point': {}}]:
            value = input_receipt('#button'); value.update(mutation)
            with self.assertRaises(ValueError): C.native_input(value, 'linux', 101)

    def test_plain_paragraph_accepts_native_edited_node_replacement_with_unchanged_other_nodes_and_undo(self):
        for replaced in (False, True):
            value = correction_fixture()
            value['paragraph'].update(textNodesPreserved=not replaced, editedTextNodeReplaced=replaced)
            with self.subTest(editedTextNodeReplaced=replaced):
                C.correction(value)

    def test_plain_paragraph_rejects_changes_to_untouched_nodes_or_untruthful_edited_node_receipts(self):
        changes = [lambda p: p.update(unmodifiedTextNodesPreserved=False), lambda p: p.pop('unmodifiedTextNodesPreserved'),
                   lambda p: p.update(hostPreserved=False), lambda p: p.update(wrappersPreserved=False),
                   lambda p: p.update(textNodesPreserved=False, editedTextNodeReplaced=False),
                   lambda p: p.update(textNodesPreserved=True, editedTextNodeReplaced=True),
                   lambda p: p.update(textNodesPreserved=1), lambda p: p.update(editedTextNodeReplaced=0),
                   lambda p: p.pop('editedTextNodeReplaced'), lambda p: p.pop('textNodesPreserved')]
        for change in changes:
            value = correction_fixture(); change(value['paragraph'])
            with self.assertRaises(ValueError): C.correction(value)

    def test_plain_paragraph_requires_actual_undo_preserving_original_prefix_host_and_wrappers(self):
        changes = [lambda p: p.pop('undo'), lambda p: p['undo'].update(value=C.EXPECTED),
                   lambda p: p['undo'].update(prefix='changed earlier text'),
                   lambda p: p['undo'].update(hostPreserved=False), lambda p: p['undo'].update(wrappersPreserved=False),
                   lambda p: p['undo'].update(hostPreserved=1), lambda p: p['undo'].update(wrappersPreserved=1),
                   lambda p: p['undo'].update(source='synthetic DOM replacement')]
        for change in changes:
            value = correction_fixture(); change(value['paragraph'])
            with self.assertRaisesRegex(ValueError, 'paragraph native undo'): C.correction(value)

    def test_full_reader_binds_two_processes_and_every_actual_png(self):
        files = sealed(*fixture()); result = C.verify(files.__getitem__, expected_platform='linux', expected_arch='x64')
        self.assertTrue(result['ok']); self.assertEqual(result['processes'], {'writePid': 101, 'readPid': 102})
        self.assertEqual({row['file'] for row in result['artifacts']}, set(files))
        for item in result['artifacts']: self.assertEqual(item['sha256'], C.sha(files[item['file']]))

    def test_coherent_rehashing_cannot_hide_wrong_process_or_incomplete_native_actions(self):
        changes = [lambda f, w, p: p['read'].update(pid=101), lambda f, w, p: p.update(executableSha256='missing'),
                   lambda f, w, p: f['restart'].update(appearance={}), lambda f, w, p: f['nativeInputs'][-1].update(source='script'),
                   lambda f, w, p: f['captures'].pop(), lambda f, w, p: w['write']['footer'].update(hasInterfaceLocale=True)]
        for change in changes:
            files, facts, written, processes = fixture(); change(facts, written, processes)
            with self.assertRaises(ValueError): C.verify(sealed(files, facts, written, processes).__getitem__)

    def test_rehashed_wrong_pixels_or_probe_owners_do_not_pass_the_native_frame_reader(self):
        name = C.CAPTURES[0]
        for mutate in [lambda row: row['probes'][0].update(actualRGBA=[0, 0, 0, 255]),
                       lambda row: row['probes'][0].update(webContentsId=999),
                       lambda row: row['mapping'].update(scaleX=2),
                       lambda row: row['shell']['regions'][0].update(label='#unrelated'),
                       lambda row: row['native'][0].update(visible=False)]:
            row, files = screen(name); mutate(row)
            with self.assertRaises(ValueError): C.capture(files.__getitem__, row, name)

    def test_settings_frame_is_bound_to_shell_pixels_without_fabricating_unoccluded_guest_pixels(self):
        name = C.CAPTURES[2]; row, files = screen(name, shell_only=True)
        self.assertIsNone(C.capture(files.__getitem__, row, name, shell_only=True))
        row['native'] = [{'visible': True}]
        with self.assertRaisesRegex(ValueError, 'unoccluded'): C.capture(files.__getitem__, row, name, shell_only=True)

    def test_nondefault_tones_must_survive_a_real_distinct_restart(self):
        _, facts, _, _ = fixture(); C.tones(facts['write']['tones'], facts['restart'], 'linux')
        facts['restart']['quick']['blackTemperature'] = 75
        with self.assertRaises(ValueError): C.tones(facts['write']['tones'], facts['restart'], 'linux')

    def test_receipt_names_cannot_escape_the_artifact_directory(self):
        files, facts, written, processes = fixture(); facts['captures'][0]['shell']['filename'] = '../private.png'
        with self.assertRaises(ValueError): C.verify(sealed(files, facts, written, processes).__getitem__)

    def test_coherently_changed_settings_arrow_or_footer_is_rejected(self):
        for key, replacement in [('paddingRight', 4), ('backgroundPosition', 'right 2px center')]:
            files, facts, written, processes = fixture()
            facts['write']['settingsArrow'][key] = replacement; written['write']['settingsArrow'][key] = replacement
            with self.assertRaisesRegex(ValueError, 'arrow'): C.verify(sealed(files, facts, written, processes).__getitem__)
        files, facts, written, processes = fixture()
        for value in (facts, written): value['write']['footer']['hasInterfaceLocale'] = True
        with self.assertRaisesRegex(ValueError, 'footer'): C.verify(sealed(files, facts, written, processes).__getitem__)


if __name__ == '__main__':
    unittest.main()
