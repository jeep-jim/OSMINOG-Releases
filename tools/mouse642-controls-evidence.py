#!/usr/bin/env python3
"""Independently read installed642 tones, real layouts and consent-only edits."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
import re

_spec = importlib.util.spec_from_file_location('mouse642_control_pixels', Path(__file__).with_name('mouse642-task-evidence.py'))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)
VERSION = '6.0.42'
NATIVE = {'darwin': 'CGEvent', 'win32': 'User32', 'linux': 'XTest'}
SAMPLE = 'ghbvth ntrcnf lkz ltvjycnhfy=wbb yt dthyjq hfcrkflrb gjkmpjdfntkz -'
KEYS_EN = "qwertyuiop[]asdfghjkl;'zxcvbnm,./`QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?~"
KEYS_RU = 'йцукенгшщзхъфывапролджэячсмитьбю.ёЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,Ё'
EXPECTED = SAMPLE.translate(str.maketrans(KEYS_EN, KEYS_RU))
CAPTURES = ('mouse-642-tones-light.png', 'mouse-642-tones-dark.png',
            'mouse-642-settings-locale-inset.png', 'mouse-642-correction-offer.png',
            'mouse-642-restored-tones.png')
TOKENS = ('native642-theme-temperature-and-restart', 'native642-real-os-input-language',
          'native642-consent-layout-correction')


def need(value, message):
    if not value:
        raise ValueError('Mouse642 controls: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def image(read, name, digest, dimensions):
    need(isinstance(name, str) and re.fullmatch(r'mouse-642-[a-z0-9-]+\.png', name), 'unsafe screenshot name')
    raw = read(name)
    need(sha(raw) == digest, 'actual screenshot hash differs')
    decoded = P.decode_png(raw, name)
    need(dimensions == {key: decoded[key] for key in ('width', 'height')}, 'actual screenshot dimensions differ')
    return decoded


def shell_pixels(read, capture, actual):
    """The retained631 two-pixel shell check, with an explicit642 file boundary."""
    shell = capture.get('shell', {})
    need(shell.get('filename') == capture['filename'][:-4] + '-shell-reference.png', 'current shell reference is missing')
    reference = image(read, shell['filename'], shell.get('sha256'), shell.get('pixelSize'))
    bounds, mapping = capture['contentBounds'], capture['mapping']
    sx, sy = reference['width'] / bounds['width'], reference['height'] / bounds['height']
    regions = shell.get('regions', [])
    need(isinstance(regions, list) and len(regions) == 1, 'exactly one complete controls surface is required')
    box = P.rectangle(regions[0].get('bounds'), 'shell control')
    need(box['x'] >= 0 and box['y'] >= 0 and box['x'] + box['width'] <= bounds['width']
         and box['y'] + box['height'] <= bounds['height'], 'shell control exceeds its actual window')
    trim = min(1, box['width'] / 4, box['height'] / 4)
    left, top = math.ceil((box['x'] + trim) * sx), math.ceil((box['y'] + trim) * sy)
    right, bottom = math.floor((box['x'] + box['width'] - trim) * sx), math.floor((box['y'] + box['height'] - trim) * sy)
    need(right > left and bottom > top, 'shell control has no real pixels')
    colors_a, colors_b = set(), set()
    for y in range(top, bottom):
        for x in range(left, right):
            ax = math.floor(mapping['originX'] + (x + .5) / sx * mapping['scaleX'])
            ay = math.floor(mapping['originY'] + (y + .5) / sy * mapping['scaleY'])
            a, b = P.pixel(reference, x, y), P.pixel(actual, ax, ay)
            need(a[3] == b[3] == 255 and P.close_rgba(a, b, 2), 'actual OS control differs from its current rendered shell pixels')
            if len(colors_a) < 3: colors_a.add(tuple(a))
            if len(colors_b) < 3: colors_b.add(tuple(b))
    need(len(colors_a) >= 3 and len(colors_b) >= 3, 'shell control is only a blank rectangle')


def absolute(value, platform):
    return isinstance(value, str) and (PureWindowsPath(value) if platform == 'win32' else PurePosixPath(value)).is_absolute()


def native_input(row, platform, pid):
    need(isinstance(row, dict) and row.get('source') == NATIVE[platform] and row.get('pid') == pid
         and isinstance(row.get('selector'), str) and row['selector'] and P.finite(row.get('at'))
         and all(P.finite(row.get('point', {}).get(axis)) for axis in ('x', 'y')), 'actual OS input source/process/point is missing')
    events = row.get('events', [])
    need(isinstance(events, list) and 0 < len(events) <= 300
         and any(event.get('type') == 'click' and event.get('trusted') is True and event.get('matches') is True for event in events),
         'a trusted OS click never reached the actual control')


def language(value, locale, platform):
    before, restored = value.get('before', {}), value.get('restored', {})
    need(before.get('available') is True and restored.get('available') is True
         and before.get('platform') == restored.get('platform') == platform
         and isinstance(before.get('currentId'), str) and before['currentId']
         and restored.get('currentId') == before['currentId'], 'original real input source was not restored')
    originals = before.get('layouts', [])
    need(originals and sorted(item.get('id', '') for item in originals)
         == sorted(item.get('id', '') for item in restored.get('layouts', [])), 'the installed input-source set changed')
    ids = []
    for code in ('ru', 'en'):
        state, ident = value.get(code, {}), value.get(code + 'Id')
        rows = state.get('layouts', [])
        need(isinstance(ident, str) and ident and state.get('available') is True and state.get('platform') == platform
             and state.get('currentId') == ident and len({item.get('id') for item in rows}) == len(rows), 'actual selected OS layout differs')
        selected = [item for item in rows if item.get('id') == ident]
        need(len(selected) == 1 and re.split('[-_]', selected[0].get('language', ''))[0] == code
             and selected[0].get('active') is True, 'indicator does not represent the actual RU/EN OS source')
        ids.append(ident)
    need(ids[0] != ids[1], 'RU and EN are the same source')
    rows = value.get('physicalKeys', [])
    need(isinstance(rows, list) and len(rows) == 2, 'physical G needs both OS layouts')
    for row, code, character, ident in zip(rows, ('ru', 'en'), ('п', 'g'), ids):
        need(row.get('language') == code and row.get('layoutId') == ident and row.get('value') == character
             and row.get('indicator') == code.upper()
             and row.get('delivery') == {'source': NATIVE[platform], 'key': 'physical-G', 'unicodeInjection': False},
             'OS layout was not proven by the same physical key without Unicode injection')
        need(any(event.get('trusted') is True and event.get('value') == character and event.get('inputType') == 'insertText'
                 for event in row.get('events', [])), 'physical key did not produce trusted text in the installed guest')
    need(value.get('oneTap') == {'currentId': ids[0], 'locale': locale}, 'one-tap input switch changed interface language or selected another layout')


def rounded(value):
    return max(0, min(255, math.floor(value + .5)))


def rgb(value):
    need(isinstance(value, str), 'color is missing')
    if re.fullmatch('#[0-9a-fA-F]{6}', value):
        return [int(value[index:index + 2], 16) for index in (1, 3, 5)]
    match = re.fullmatch(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', value)
    need(match and all(0 <= int(channel) <= 255 for channel in match.groups()), 'unsupported color format')
    return list(map(int, match.groups()))


def tone_state(value, expected=None, *, allow_unstored_default=False):
    appearance = value.get('appearance', {})
    tones = appearance.get('tones', {})
    actual = {'whiteTone': appearance.get('whiteTone'), 'whiteTemperature': tones.get('whiteTemperature', 0),
              'blackTone': tones.get('blackTone', 55), 'blackTemperature': tones.get('blackTemperature', 0)}
    need(appearance.get('paneMode') in ('rounded', 'square') and all(type(number) is int for number in actual.values())
         and 0 <= actual['whiteTone'] <= 100 and 0 <= actual['blackTone'] <= 100
         and -100 <= actual['whiteTemperature'] <= 100 and -100 <= actual['blackTemperature'] <= 100,
         'tone controls are outside their actual range')
    persisted = value.get('stored') == appearance or (allow_unstored_default and value.get('stored') is None
        and actual == {'whiteTone': 55, 'whiteTemperature': 0, 'blackTone': 55, 'blackTemperature': 0})
    need(value.get('quick') == actual == value.get('settings') and persisted,
         'quick controls, Settings and stored appearance disagree')
    need(expected is None or actual == expected, 'native preset/range produced different tone values')
    white = rounded(160 + 95 * actual['whiteTone'] / 100)
    temperature = actual['whiteTemperature']
    offsets = [0, -14, -32] if temperature >= 0 else [-24, -10, 0]
    expected_white = [rounded(white + offset * abs(temperature) / 100) for offset in offsets]
    tone, temperature = actual['blackTone'], actual['blackTemperature']
    base = [channel * tone / 55 if tone <= 55 else channel + (80 - channel) * (tone - 55) / 45 for channel in (23, 32, 51)]
    offsets = [14, 2, -19] if temperature >= 0 else [-10, -3, 12]
    expected_black = [rounded(channel + offset * abs(temperature) / 100 * min(1, tone / 55)) for channel, offset in zip(base, offsets)]
    need(rgb(value.get('white')) == expected_white and rgb(value.get('black')) == expected_black,
         'rendered neutral text colors differ from the independent tone calculation')
    theme = value.get('theme')
    need(theme in ('light', 'dark'), 'unknown actual theme')
    for name, light, dark in [('background', [243, 245, 249], [16, 21, 30]), ('panel', [255, 255, 255], [25, 33, 46])]:
        if theme == 'light':
            temperature = actual['whiteTemperature']; offsets = [0, -14, -32] if temperature >= 0 else [-24, -10, 0]
            color = [rounded(channel + offset * abs(temperature) / 100) for channel, offset in zip(light, offsets)]
        else:
            tone, temperature = actual['blackTone'], actual['blackTemperature']
            shift = -16 * (55 - tone) / 55 if tone < 55 else 10 * (tone - 55) / 45
            offsets = [9, 2, -9] if temperature >= 0 else [-5, -2, 8]
            color = [rounded(channel + shift + offset * abs(temperature) / 100) for channel, offset in zip(dark, offsets)]
        need(rgb(value.get(name)) == color, 'actual theme surface differs from its temperature settings')
    return actual


def tones(value, restart, platform):
    initial = tone_state(value.get('initial', {}), allow_unstored_default=True)
    need(initial == {'whiteTone': 55, 'whiteTemperature': 0, 'blackTone': 55, 'blackTemperature': 0}, 'isolated controls profile did not start with default tones')
    expected = [dict(whiteTone=80, whiteTemperature=50, blackTone=55, blackTemperature=0),
                dict(whiteTone=99, whiteTemperature=50, blackTone=55, blackTemperature=0),
                dict(whiteTone=99, whiteTemperature=50, blackTone=1, blackTemperature=75),
                dict(whiteTone=99, whiteTemperature=50, blackTone=1, blackTemperature=99)]
    changes = value.get('changes', [])
    need([row.get('kind') for row in changes] == ['white-preset', 'white-slider', 'black-slider', 'settings-slider'], 'native tone routes are incomplete')
    for row, target in zip(changes, expected):
        tone_state(row.get('state', {}), target)
    for key, selector, target in [('whiteRange', '#quick-white-tone', 99), ('blackRange', '#quick-black-tone', 1),
                                  ('settingsRange', '#settings-black-temperature', 99)]:
        row = value.get(key, {})
        need(row.get('selector') == selector and row.get('value') == target and row.get('source') == NATIVE[platform]
             and any(event.get('trusted') is True and event.get('value') == target for event in row.get('events', [])),
             'tone slider lacks trusted native input at its required value')
    for key, target in [('light', expected[1]), ('dark', expected[2])]:
        row = value.get(key, {}); tone_state(row, target)
        need(row.get('theme') == key and row.get('capture') == 'mouse-642-tones-' + key + '.png', 'both actual themes require their native frames')
    saved = value.get('saved', {}); tone_state(saved, expected[-1]); tone_state(restart, expected[-1])
    need(saved.get('theme') == 'dark' and restart.get('theme') == saved['theme']
         and restart.get('appearance') == saved.get('appearance') == restart.get('stored')
         and restart.get('capture') == 'mouse-642-restored-tones.png', 'distinct process did not restore the actual saved theme and tones')


def correction(value):
    need(value.get('sample') == SAMPLE and value.get('expected') == EXPECTED and value.get('before') == SAMPLE
         and value.get('noAutoReplacement') is True and value.get('capture') == 'mouse-642-correction-offer.png',
         'proposal was not the exact physical-key example before explicit consent')
    insertion = value.get('insertion', {})
    need(insertion.get('method') == 'WebContents.insertText'
         and any(event.get('trusted') is True and event.get('value') == SAMPLE for event in insertion.get('events', [])),
         'owned wrong-layout text never reached the real guest input')
    for name in ('accepted', 'editable', 'shell'):
        row = value.get(name, {})
        need(row.get('value') == EXPECTED and any(event.get('trusted') is True and event.get('value') == EXPECTED
             and event.get('inputType') in ('insertText', 'insertReplacementText') for event in row.get('events', [])),
             'explicit consent did not edit the actual ' + name + ' target')
    paragraph = value.get('paragraph', {})
    prefix = 'Earlier paragraph stays.'
    need(paragraph.get('value') == EXPECTED and paragraph.get('prefix') == prefix
         and paragraph.get('beforeText') == prefix + SAMPLE and paragraph.get('afterText') == prefix + EXPECTED
         and all(paragraph.get(key) is True for key in ('hostPreserved', 'wrappersPreserved', 'unmodifiedTextNodesPreserved'))
         and any(event.get('trusted') is True and event.get('value') == prefix + EXPECTED
                 and event.get('inputType') in ('insertText', 'insertReplacementText') for event in paragraph.get('events', [])),
         'plain paragraph correction changed earlier text, editor identity or its actual host input')
    # Blink may replace the one edited Text node during its native undoable edit.
    # The receipt must distinguish that from changes to any untouched node.
    need(type(paragraph.get('textNodesPreserved')) is bool and type(paragraph.get('editedTextNodeReplaced')) is bool
         and paragraph['textNodesPreserved'] is (not paragraph['editedTextNodeReplaced']),
         'plain paragraph edited-node receipt is missing or inconsistent')
    undo = paragraph.get('undo', {})
    need(undo == {'value': SAMPLE, 'prefix': prefix, 'hostPreserved': True,
         'wrappersPreserved': True, 'source': 'WebContents.undo'}
         and all(undo.get(key) is True for key in ('hostPreserved', 'wrappersPreserved')),
         'plain paragraph native undo did not restore its original text and editor structure')
    need(re.fullmatch(r'[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}', value['accepted'].get('token', '')),
         'consent lacks its original one-use target token')
    need(value.get('undo') == {'value': SAMPLE, 'source': 'WebContents.undo'}, 'native undo did not restore the exact original text')
    need(value.get('rejected') == {'value': SAMPLE, 'visible': False}, 'declining changed the text or retained a live suggestion')
    stale = value.get('stale', {})
    need(stale.get('result', {}).get('ok') is False and stale.get('value') == SAMPLE + 'x', 'stale consent overwrote newer input')
    safe = value.get('safe', [])
    need([(row.get('selector'), row.get('kind')) for row in safe] == [('#password', None), ('#mail', None),
         ('#field', 'english'), ('#field', 'russian'), ('#field', 'mixed')]
         and all(row.get('suggestion') is False and row.get('valueUnchanged') is True for row in safe), 'sensitive or normal text produced a correction')
    before, after = value.get('pageBefore', {}), value.get('pageAfter', {})
    for key in ('id', 'index', 'desk', 'webContentsId', 'identity', 'timeOrigin', 'url', 'navigationEpoch'):
        need(key in before and before[key] == after.get(key), 'correction replaced or navigated the live document: ' + key)
    need(isinstance(before.get('id'), str) and before['id'] and type(before.get('webContentsId')) is int and before['webContentsId'] > 0
         and isinstance(before.get('identity'), str) and before['identity'] and P.finite(before.get('timeOrigin'))
         and P.finite(before.get('ticks')) and P.finite(after.get('ticks')) and after['ticks'] >= before['ticks'], 'live owned document identity/timer is missing')
    return before


def capture(read, value, expected_name, *, shell_only=False):
    need(value.get('filename') == expected_name and value.get('source') == 'globalCapture.acquire(display)'
         and value.get('kind') == 'screen' and isinstance(value.get('backend'), str) and value['backend'], 'capture is not the required actual OS display')
    decoded = image(read, expected_name, value.get('sha256'), value.get('pixelSize'))
    full_name = expected_name[:-4] + '-display.png'
    need(value.get('displayFilename') == full_name, 'full display filename differs')
    full = image(read, full_name, value.get('displaySha256'), value.get('screenPixelSize'))
    display, bounds = P.rectangle(value.get('display', {}).get('bounds'), 'display'), P.rectangle(value.get('contentBounds'), 'content')
    sx, sy = full['width'] / display['width'], full['height'] / display['height']
    left, top = (bounds['x'] - display['x']) * sx, (bounds['y'] - display['y']) * sy
    crop = {'x': math.floor(left), 'y': math.floor(top), 'width': math.ceil(left + bounds['width'] * sx) - math.floor(left),
            'height': math.ceil(top + bounds['height'] * sy) - math.floor(top)}
    need(value.get('cropPixels') == crop and decoded['width'] == crop['width'] and decoded['height'] == crop['height']
         and crop['x'] >= 0 and crop['y'] >= 0 and crop['x'] + crop['width'] <= full['width']
         and crop['y'] + crop['height'] <= full['height'], 'actual display crop geometry differs')
    mapping = {'originX': left - crop['x'], 'originY': top - crop['y'], 'scaleX': sx, 'scaleY': sy}
    need(all(P.finite(value.get('mapping', {}).get(key)) and abs(value['mapping'][key] - number) < 1e-8 for key, number in mapping.items()), 'actual native DPI mapping differs')
    for x in range(0, decoded['width'], max(1, decoded['width'] // 37)):
        for y in range(0, decoded['height'], max(1, decoded['height'] // 31)):
            need(P.pixel(decoded, x, y) == P.pixel(full, x + crop['x'], y + crop['y']), 'window PNG is not the full display region')
    shell_pixels(read, value, decoded)
    label = '#settings-language' if shell_only else '#input-correction-bubble' if 'correction-offer' in expected_name else '#temperature-panel'
    region = value['shell']['regions'][0]
    need(region.get('label') == label, 'native shell reference belongs to another control')
    box = P.rectangle(region.get('bounds'), '642 control')
    need(box['width'] >= (80 if shell_only else 200) and box['height'] >= (12 if shell_only else 70), 'native control reference is only a trivial patch')
    attempts = value.get('attempts', [])
    need(isinstance(attempts, list) and 1 <= len(attempts) <= 10 and attempts[-1].get('accepted') is True, 'actual screen acquisition did not pass')
    if shell_only:
        need(all(value.get(key) in (None, []) for key in ('native', 'content', 'probes')), 'dimmed Settings frame claims unoccluded guest proof')
        return None
    native, content = value.get('native', []), value.get('content', [])
    need(len(native) == len(content) == 1 and native[0].get('index') == content[0].get('index') == 0, 'exactly one owned live page is required')
    owner, dom = native[0], content[0]
    need(isinstance(owner.get('tabId'), str) and owner['tabId'] and dom.get('tabId') == owner['tabId']
         and isinstance(dom.get('identity'), str) and dom['identity'] and type(owner.get('webContentsId')) is int and owner['webContentsId'] > 0
         and all(owner.get(key) is True for key in ('visible', 'parentVisible', 'cachedVisible', 'attached')), 'native guest ownership/attachment is missing')
    page, view = P.rectangle(owner.get('bounds'), 'native guest'), P.rectangle(owner.get('viewBounds'), 'view')
    parent = owner.get('parentBounds'); parent = P.rectangle(parent, 'parent') if parent is not None else {'x': 0, 'y': 0}
    actual = {'x': view['x'] + parent['x'], 'y': view['y'] + parent['y'], 'width': view['width'], 'height': view['height']}
    need(actual == page == owner.get('actualBounds') and page['x'] >= 0 and page['y'] >= 0
         and page['x'] + page['width'] <= bounds['width'] and page['y'] + page['height'] <= bounds['height'], 'native guest geometry differs')
    regions = dom.get('regions', [])
    need(len(regions) == 2 and {row.get('part') for row in regions} == {'a', 'b'}, 'two actual page regions are missing')
    probes = value.get('probes', []); seen = set()
    need(len(probes) == 10, 'ten independently decoded page probes are required')
    for probe in probes:
        part, offset = probe.get('region'), probe.get('offset', {})
        delta = (offset.get('x'), offset.get('y')); key = (part, delta)
        need(part in ('a', 'b') and delta in ((0, 0), (-6, 0), (6, 0), (0, -6), (0, 6)) and key not in seen,
             'duplicate or foreign page probe'); seen.add(key)
        need(all(probe.get(field) == owner.get(field) for field in ('tabId', 'index', 'webContentsId', 'desk')), 'page probe owner differs')
        row = next(item for item in regions if item['part'] == part); local = P.rectangle(row.get('bounds'), 'page region')
        need(local == probe.get('localBounds') and local['x'] >= 0 and local['y'] >= 0 and local['x'] + local['width'] <= page['width']
             and local['y'] + local['height'] <= page['height'], 'page probe is outside the actual guest')
        point = {'x': page['x'] + local['x'] + local['width'] / 2 + delta[0], 'y': page['y'] + local['y'] + local['height'] / 2 + delta[1]}
        x, y = math.floor(mapping['originX'] + point['x'] * sx), math.floor(mapping['originY'] + point['y'] * sy)
        color = P.color(0, 0 if part == 'a' else 1); actual = P.pixel(decoded, x, y)
        need(probe.get('cssPoint') == point and probe.get('x') == x and probe.get('y') == y and probe.get('expectedRGB') == color
             and probe.get('tolerance') == 3 and row.get('color') == 'rgb(' + ', '.join(map(str, color)) + ')'
             and probe.get('actualRGBA') == actual == P.pixel(full, x + crop['x'], y + crop['y']) and P.close_rgba(actual, color + [255], 3),
             'actual native pixels do not show the unchanged colored page markers')
    return {'id': owner['tabId'], 'index': 0, 'webContentsId': owner['webContentsId'], 'desk': owner.get('desk'), 'identity': dom['identity']}


def verify(read, expected_platform=None, expected_arch=None):
    artifacts = {}
    def bound(name):
        need(isinstance(name, str) and re.fullmatch(r'mouse-642-[a-z0-9.-]+', name) and '..' not in name, 'unsafe artifact name')
        raw = read(name)
        need(isinstance(raw, bytes) and 0 < len(raw) <= 96 * 1024**2, 'empty or oversized controls artifact')
        artifacts[name] = {'file': name, 'sha256': sha(raw), 'bytes': len(raw)}
        return raw
    names = ('mouse-642-controls.json', 'mouse-642-controls-write.json', 'mouse-642-controls-processes.json')
    facts, written, processes = (json.loads(bound(name)) for name in names)
    platform, arch, pid = facts.get('platform'), facts.get('arch'), facts.get('pid')
    need((platform, arch) in (('darwin', 'arm64'), ('win32', 'x64'), ('linux', 'x64'))
         and (expected_platform is None or expected_platform == platform) and (expected_arch is None or expected_arch == arch), 'actual platform/architecture differs')
    need(facts.get('schema') == 1 and facts.get('version') == VERSION and facts.get('packaged') is True
         and facts.get('physicalUserDeviceVerified') is False and facts.get('phase') == 'read' and facts.get('ok') is True
         and facts.get('writeComplete') is True and facts.get('awaitingRestart') is False and type(pid) is int and pid > 0
         and facts.get('writePid') == pid and absolute(facts.get('profile'), platform), 'not a completed installed controls run')
    need(written.get('ok') is False and written.get('phase') == 'write' and written.get('writeComplete') is True
         and written.get('awaitingRestart') is True and written.get('write') == facts.get('write'), 'original write report was replaced during restart')
    for key in ('schema', 'version', 'platform', 'arch', 'packaged', 'physicalUserDeviceVerified', 'profile', 'pid', 'writePid'):
        need(written.get(key) == facts.get(key), 'original process identity changed: ' + key)
    for row in (facts, written):
        need(not any(row.get(key) for key in ('error', 'restoreError', 'cleanupError'))
             and row.get('cleanup', {}).get('restored') is True and row['cleanup'].get('desktopStateRestored') is True,
             'owned native fixture was not cleaned up')
    need(processes.get('schema') == 1 and processes.get('version') == VERSION and processes.get('platform') == platform
         and processes.get('arch') == arch and processes.get('profile') == facts['profile'] and absolute(processes.get('executable'), platform)
         and re.fullmatch('[a-f0-9]{64}', processes.get('executableSha256', '')) and processes.get('reportSha256') == sha(bound(names[0])),
         'installed executable/profile/report hashes differ')
    write, restart = facts.get('write', {}), facts.get('restart', {})
    for phase, part, report, limit, native_limit, marker in (
            ('write', write, names[1], 240000, 210000, 'MOUSE_642_CONTROLS_WRITE_PASS'),
            ('read', restart, names[0], 120000, 90000, 'MOUSE_642_CONTROLS_NATIVE_PASS')):
        receipt = processes.get(phase, {}); phase_pid = part.get('pid'); log_name = 'mouse-642-controls-' + phase + '.log'
        need(type(phase_pid) is int and phase_pid > 0 and phase_pid == receipt.get('pid')
             and (phase_pid == pid if phase == 'write' else phase_pid != pid) and receipt.get('exitCode') == 0
             and P.finite(receipt.get('elapsedMs')) and 0 < receipt['elapsedMs'] <= limit, 'actual distinct process/exit/budget is missing')
        need(P.finite(part.get('startedAt')) and P.finite(part.get('completedAt')) and 0 < part['completedAt'] - part['startedAt'] <= native_limit
             and P.finite((written if phase == 'write' else facts).get('elapsedMs'))
             and 0 < (written if phase == 'write' else facts)['elapsedMs'] <= native_limit, 'native controls exceeded their fixed budget')
        raw = bound(log_name); lines = raw.decode('utf-8', 'strict').splitlines()
        need(receipt.get('report') == report and receipt.get('reportSha256') == sha(bound(report)) and receipt.get('log') == log_name
             and receipt.get('logSha256') == sha(raw) and receipt.get('requiredMarkers') == [marker] and marker in lines
             and any(re.fullmatch(r'MOUSE_642_PROCESS_RETURN pid=' + str(phase_pid) + r' code=0 elapsedMs=\d+', line) for line in lines), 'actual process logs/phase reports differ')
    footer = write.get('footer', {})
    need(footer.get('hasInterfaceLocale') is False and all(footer.get(key) is True for key in ('hasTemperature', 'hasInputIndicator', 'hasSettingsLocale'))
         and footer.get('locale') in ('ru', 'en'), 'footer does not provide tones and actual input language with interface language in Settings')
    language(write.get('language', {}), footer['locale'], platform)
    tones(write.get('tones', {}), restart, platform)
    owner = correction(write.get('correction', {}))
    need(re.fullmatch(r'http://127\.0\.0\.1:\d+', written.get('fixtureOrigin', ''))
         and owner.get('url') == written['fixtureOrigin'] + '/page/0/', 'correction was not bound to the owned HTTP document')
    arrow = write.get('settingsArrow', {})
    need(arrow.get('appearance') == 'none' and P.finite(arrow.get('paddingRight')) and 32 <= arrow['paddingRight'] <= 48
         and re.fullmatch(r'(?:right 14px (?:center|50%)|calc\(100% - 14px\) 50%)', arrow.get('backgroundPosition', ''))
         and arrow.get('capture') == CAPTURES[2], 'Settings language arrow does not have its required independent inset')
    P.rectangle(arrow.get('bounds'), 'Settings language select')
    inputs, original_inputs = facts.get('nativeInputs', []), written.get('nativeInputs', [])
    need(isinstance(inputs, list) and original_inputs and inputs[:len(original_inputs)] == original_inputs
         and len(inputs) > len(original_inputs), 'restart lost or replaced the original native input ledger')
    for index, row in enumerate(inputs): native_input(row, platform, pid if index < len(original_inputs) else restart['pid'])
    selectors = [row['selector'] for row in original_inputs]
    required = {'#input-language-more', '#input-language-button', '#temperature-button', '[data-tone-kind-tab=white]', '[data-tone-kind-tab=black]',
                '#temperature-panel [data-tone-family=white][data-tone-preset=paper]', '#temperature-panel [data-tone-family=black][data-tone-preset="warm"]',
                '#temperature-panel [data-tone-theme=light]', '#temperature-panel [data-tone-theme=dark]', '#quick-white-tone', '#quick-black-tone',
                '#settings-button', '.settings-nav-item[data-settings-page=appearance]', '#settings-black-temperature', '[data-input-correction=reject]',
                '#field', '#editor', '#password', '#mail', '#mouse642-shell-edit'}
    required.update('[data-input-layout=' + json.dumps(write['language'][code + 'Id'], ensure_ascii=False) + ']' for code in ('ru', 'en'))
    need(required <= set(selectors) and selectors.count('[data-input-correction=accept]') >= 4, 'a required native user control or consent action was not exercised')
    for row in original_inputs:
        if row['selector'] in ('#field', '#editor', '#password', '#mail'):
            need(row.get('tabId') == owner['id'], 'native editable click belongs to a different guest')
    captures = facts.get('captures', [])
    need([row.get('filename') for row in captures] == list(CAPTURES) and written.get('captures') == captures[:-1], 'exact native write/restart frame ledger differs')
    arrow_bounds = arrow['bounds']
    expected_arrow = {'x': arrow_bounds['x'] + 5, 'y': arrow_bounds['y'] + 5,
                      'width': max(2, arrow_bounds['width'] - 10), 'height': max(2, arrow_bounds['height'] - 10)}
    need(captures[2].get('pid') == pid and captures[2].get('shellOnly') is True
         and captures[2].get('shell', {}).get('regions', [{}])[0].get('bounds') == expected_arrow,
         'actual Settings select rectangle/process differs from its screen reference')
    for index, row in enumerate(captures):
        actual = capture(bound, row, CAPTURES[index], shell_only=index == 2)
        if actual is not None and index < 4:
            need(all(actual[key] == owner[key] for key in ('id', 'index', 'webContentsId', 'desk', 'identity')), 'controls capture replaced its original live page')
    return {'schema': 1, 'version': VERSION, 'ok': True, 'platform': platform, 'arch': arch,
            'processes': {'writePid': pid, 'readPid': restart['pid']}, 'nativeCaptures': list(CAPTURES),
            'realOSInputLanguage': True, 'physicalKeyBothLayouts': True, 'consentOnlyCorrection': True,
            'nativeUndo': True, 'plainParagraphCorrection': True, 'unmodifiedEditorNodesPreserved': True,
            'plainParagraphNativeUndo': True, 'settingsOnlyInterfaceLanguage': True, 'independentToneControls': True,
            'twoProcessTonePersistence': True, 'artifacts': list(artifacts.values())}


def run(directory, *, platform=None, arch=None):
    directory = Path(directory)
    accepted = verify(lambda name: (directory / name).read_bytes(), platform, arch)
    (directory / 'mouse-642-controls-acceptance.json').write_text(json.dumps(accepted, indent=2) + '\n', encoding='utf-8')
    return accepted


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--platform', choices=('darwin', 'win32', 'linux'))
    parser.add_argument('--arch', choices=('arm64', 'x64'))
    args = parser.parse_args()
    run(args.directory, platform=args.platform, arch=args.arch)
    print('MOUSE_642_CONTROLS_ACCEPTANCE_PASS')
