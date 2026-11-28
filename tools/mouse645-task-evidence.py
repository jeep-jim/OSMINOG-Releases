#!/usr/bin/env python3
"""Independent, dependency-free verification of installed Mouse 6.0.45 evidence.

verify(read) accepts a bounded filename -> bytes reader, including ZipFile.read.
It decodes the archived native PNGs; JSON success flags alone are insufficient.
"""
import argparse
import hashlib
import json
import math
import re
import struct
import sys
import zlib
from pathlib import Path

VERSION = '6.0.45'
IDENTITY_FIELDS = ('id', 'index', 'desk', 'webContentsId', 'url', 'navigationEpoch',
                   'identity', 'timeOrigin', 'field', 'scrollX', 'scrollY', 'cookie')


def need(condition, message):
    if not condition:
        raise ValueError('Mouse631: ' + message)


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def integer(value, minimum=0):
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def rectangle(value, label):
    need(isinstance(value, dict) and all(finite(value.get(key)) for key in ('x', 'y', 'width', 'height'))
         and value['width'] > 0 and value['height'] > 0, label + ' rectangle is invalid')
    return value


def size(value, label):
    need(isinstance(value, dict) and all(integer(value.get(key), 1) for key in ('width', 'height')),
         label + ' pixel size is invalid')
    return value


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def decode_png(blob, label='screenshot'):
    # Same bounded RGB8/RGBA8 formats emitted by Electron's real PNG encoder.
    need(isinstance(blob, bytes) and blob.startswith(b'\x89PNG\r\n\x1a\n') and len(blob) <= 16 * 1024**2,
         label + ' is not a bounded PNG')
    offset, header, compressed, ended = 8, None, bytearray(), False
    while offset < len(blob):
        need(offset + 12 <= len(blob), label + ' has a truncated chunk')
        length = struct.unpack_from('>I', blob, offset)[0]
        kind = blob[offset + 4:offset + 8]
        end = offset + 12 + length
        need(end <= len(blob), label + ' has a truncated payload')
        chunk = blob[offset + 8:offset + 8 + length]
        crc = struct.unpack_from('>I', blob, offset + 8 + length)[0]
        need(zlib.crc32(kind + chunk) & 0xffffffff == crc, label + ' PNG checksum differs')
        need(header is not None or kind == b'IHDR', label + ' has no first header')
        if kind == b'IHDR':
            need(header is None and length == 13, label + ' has an ambiguous header')
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', chunk)
            channels = {2: 3, 6: 4}.get(color)
            need(channels and depth == 8 and not compression and not filtering and not interlace
                 and 0 < width <= 8192 and 0 < height <= 8192 and width * height * 4 <= 64 * 1024**2,
                 label + ' uses an unsupported or oversized PNG format')
            header = width, height, channels
        elif kind == b'IDAT':
            compressed.extend(chunk)
        elif kind == b'IEND':
            need(not length and end == len(blob), label + ' has an invalid PNG end')
            ended = True
            break
        elif kind == b'tRNS' or kind[0] & 32 == 0 and kind != b'PLTE':
            raise ValueError('Mouse631: ' + label + ' has an unsupported critical chunk')
        offset = end
    need(ended and header and compressed, label + ' is incomplete')
    width, height, channels = header
    stride, expected = width * channels, (width * channels + 1) * height
    decoder = zlib.decompressobj()
    try:
        raw = decoder.decompress(compressed, expected + 1)
    except zlib.error as error:
        raise ValueError('Mouse631: corrupt PNG pixels in ' + label) from error
    need(len(raw) == expected and decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data,
         label + ' has an invalid decompressed length')
    pixels, previous = bytearray(stride * height), bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        method, row = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        need(method in range(5), label + ' has an invalid row filter')
        # Browser captures contain long unchanged scanline runs. Up and Paeth
        # with zero residuals both reproduce the previous row exactly. Avoid
        # a Python iteration for every screen byte while retaining full PNG,
        # checksum, decompressed-length and independently sampled pixel checks.
        if method in (2, 4) and not any(row):
            row = previous[:]
        elif method == 2:
            row = bytearray((value + above) & 255 for value, above in zip(row, previous))
        elif method:
            for x in range(stride):
                a = row[x - channels] if x >= channels else 0
                b = previous[x]
                c = previous[x - channels] if x >= channels else 0
                if method == 1:
                    predictor = a
                elif method == 2:
                    predictor = b
                elif method == 3:
                    predictor = (a + b) // 2
                else:
                    p = a + b - c
                    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                    predictor = a if pa <= pb and pa <= pc else b if pb <= pc else c
                row[x] = (row[x] + predictor) & 255
        pixels[y * stride:(y + 1) * stride] = row
        previous = row
    return {'width': width, 'height': height, 'channels': channels, 'pixels': pixels}


def pixel(image, x, y):
    need(integer(x) and integer(y) and x < image['width'] and y < image['height'], 'PNG sample lies outside its image')
    start = (y * image['width'] + x) * image['channels']
    value = list(image['pixels'][start:start + image['channels']])
    return value if image['channels'] == 4 else value + [255]


def color(index, part):
    return [40 + (index * 47 + part * 101) % 160,
            55 + (index * 71 + part * 37) % 150,
            65 + (index * 29 + part * 83) % 140]


def close_rgba(a, b, tolerance):
    return len(a) == len(b) == 4 and a[3] == b[3] == 255 and all(abs(a[i] - b[i]) <= tolerance for i in range(3))


def read_png(read, name, claimed_digest, claimed_size):
    need(isinstance(name, str) and re.fullmatch(r'mouse-631-[a-z0-9-]+\.png', name), 'unsafe screenshot name')
    blob = read(name)
    need(digest(blob) == claimed_digest, name + ' SHA-256 differs from the native capture')
    image = decode_png(blob, name)
    expected = size(claimed_size, name)
    need(all(image[key] == expected[key] for key in ('width', 'height')), name + ' dimensions differ')
    return image


def verify_capture(read, capture, expected_name, expected_pages, *, shell=False, shell_count=2):
    need(isinstance(capture, dict) and capture.get('filename') == expected_name, 'wrong native screenshot identity')
    need(capture.get('source') == 'globalCapture.acquire(display)' and capture.get('kind') == 'screen'
         and isinstance(capture.get('backend'), str) and capture['backend'], 'capture is not an actual OS display')
    image = read_png(read, expected_name, capture.get('sha256'), capture.get('pixelSize'))
    need(capture.get('displayFilename') == expected_name[:-4] + '-display.png', 'wrong full display screenshot')
    full = read_png(read, capture['displayFilename'], capture.get('displaySha256'), capture.get('screenPixelSize'))
    display = rectangle(capture.get('display', {}).get('bounds'), 'display')
    bounds = rectangle(capture.get('contentBounds'), 'window content')
    sx, sy = full['width'] / display['width'], full['height'] / display['height']
    left, top = (bounds['x'] - display['x']) * sx, (bounds['y'] - display['y']) * sy
    crop = {'x': math.floor(left), 'y': math.floor(top),
            'width': math.ceil(left + bounds['width'] * sx) - math.floor(left),
            'height': math.ceil(top + bounds['height'] * sy) - math.floor(top)}
    need(capture.get('cropPixels') == crop and image['width'] == crop['width'] and image['height'] == crop['height'],
         'native display crop does not follow actual window bounds')
    mapping = capture.get('mapping', {})
    expected_mapping = {'scaleX': sx, 'scaleY': sy, 'originX': left - crop['x'], 'originY': top - crop['y']}
    need(all(finite(mapping.get(key)) and abs(mapping[key] - value) < 1e-8 for key, value in expected_mapping.items()),
         'native DPI coordinate mapping differs')
    need(crop['x'] >= 0 and crop['y'] >= 0 and crop['x'] + crop['width'] <= full['width']
         and crop['y'] + crop['height'] <= full['height'], 'native content is outside the display')
    expected = {page['id']: page for page in expected_pages}
    native, content = capture.get('native'), capture.get('content')
    need(isinstance(native, list) and len(native) == len(expected) and len(expected) >= 2, 'native page count differs')
    need({value.get('tabId') for value in native} == set(expected), 'native page owners differ')
    need(isinstance(content, list) and len(content) == len(native), 'page DOM readbacks are missing')
    for value in native:
        owner = expected[value['tabId']]
        need(all(value.get(key) == owner[key] for key in ('index', 'desk', 'webContentsId')), 'native page identity differs')
        need(all(value.get(key) is True for key in ('visible', 'parentVisible', 'cachedVisible', 'attached')),
             'a displayed native page is hidden or detached')
        page_bounds = rectangle(value.get('bounds'), 'native page')
        view = rectangle(value.get('viewBounds'), 'native view')
        parent = value.get('parentBounds')
        if parent is not None:
            rectangle(parent, 'native parent')
        actual = {'x': view['x'] + (parent['x'] if parent else 0), 'y': view['y'] + (parent['y'] if parent else 0),
                  'width': view['width'], 'height': view['height']}
        need(actual == page_bounds == value.get('actualBounds'), 'native hierarchy does not match page bounds')
        need(page_bounds['x'] >= 0 and page_bounds['y'] >= 0 and page_bounds['x'] + page_bounds['width'] <= bounds['width']
             and page_bounds['y'] + page_bounds['height'] <= bounds['height'], 'native pane exceeds window content')
        dom = next((item for item in content if item.get('tabId') == value['tabId']), None)
        need(dom and dom.get('index') == owner['index'] and dom.get('identity') == owner['identity'], 'displayed document was replaced')
        need({item.get('part') for item in dom.get('regions', [])} == {'a', 'b'}, 'two page content regions are required')
    probes = capture.get('probes')
    need(isinstance(probes, list) and len(probes) == len(native) * 10, 'each native page requires ten independently decoded pixel probes')
    keys = set()
    for probe in probes:
        need(probe.get('tabId') in expected and probe.get('region') in ('a', 'b'), 'unknown content probe owner')
        owner = expected[probe['tabId']]
        value = next(item for item in native if item['tabId'] == owner['id'])
        need(all(probe.get(key) == owner[key] for key in ('index', 'desk', 'webContentsId')), 'pixel ownership differs')
        offset = probe.get('offset', {})
        delta = (offset.get('x'), offset.get('y'))
        need(delta in ((0, 0), (-6, 0), (6, 0), (0, -6), (0, 6)), 'unrecognised interior content probe')
        key = owner['id'], probe['region'], delta
        need(key not in keys, 'duplicate native pixel probe')
        keys.add(key)
        local = rectangle(probe.get('localBounds'), 'DOM content region')
        dom = next(item for item in content if item['tabId'] == owner['id'])
        region = next(item for item in dom['regions'] if item['part'] == probe['region'])
        need(local == region.get('bounds'), 'pixel region differs from actual DOM bounds')
        pb = value['bounds']
        need(local['x'] >= 0 and local['y'] >= 0 and local['x'] + local['width'] <= pb['width']
             and local['y'] + local['height'] <= pb['height'], 'content probe is outside its native page')
        point = {'x': pb['x'] + local['x'] + local['width'] / 2 + delta[0],
                 'y': pb['y'] + local['y'] + local['height'] / 2 + delta[1]}
        x, y = math.floor(mapping['originX'] + point['x'] * sx), math.floor(mapping['originY'] + point['y'] * sy)
        need(probe.get('cssPoint') == point and probe.get('x') == x and probe.get('y') == y, 'pixel coordinate was not derived from its native page')
        expected_color = color(owner['index'], 0 if probe['region'] == 'a' else 1)
        need(probe.get('expectedRGB') == expected_color and probe.get('tolerance') == 3, 'page marker or original tolerance changed')
        need(region.get('color') == 'rgb(' + ', '.join(map(str, expected_color)) + ')', 'DOM marker color differs')
        actual = pixel(image, x, y)
        need(actual == probe.get('actualRGBA') and actual == pixel(full, x + crop['x'], y + crop['y']), 'archived PNG pixels differ from the measured native display')
        need(close_rgba(actual, expected_color + [255], 3), 'actual OS pixels are missing the live page content')
    attempts = capture.get('attempts')
    need(isinstance(attempts, list) and 1 <= len(attempts) <= 10 and attempts[-1].get('accepted') is True,
         'bounded real display acquisition never accepted the content')
    if shell:
        verify_shell(read, capture, image, expected_count=shell_count)
    return len(probes)


def verify_shell(read, capture, image, *, expected_count=2):
    shell = capture.get('shell')
    need(isinstance(shell, dict) and shell.get('filename') == capture['filename'][:-4] + '-shell-reference.png', 'task pill reference is missing')
    reference = read_png(read, shell['filename'], shell.get('sha256'), shell.get('pixelSize'))
    bounds, mapping = capture['contentBounds'], capture['mapping']
    rsx, rsy = reference['width'] / bounds['width'], reference['height'] / bounds['height']
    regions = shell.get('regions')
    need(expected_count in (1, 2) and isinstance(regions, list) and len(regions) == expected_count,
         str(expected_count) + ' real task pills must be presented')
    for region in regions:
        box = rectangle(region.get('bounds'), 'task pill')
        trim = min(1, box['width'] / 4, box['height'] / 4)
        left, top = math.ceil((box['x'] + trim) * rsx), math.ceil((box['y'] + trim) * rsy)
        right = math.floor((box['x'] + box['width'] - trim) * rsx)
        bottom = math.floor((box['y'] + box['height'] - trim) * rsy)
        need(right > left and bottom > top, 'task pill has no pixels')
        colors_a, colors_b = set(), set()
        for y in range(top, bottom):
            for x in range(left, right):
                ax = math.floor(mapping['originX'] + (x + .5) / rsx * mapping['scaleX'])
                ay = math.floor(mapping['originY'] + (y + .5) / rsy * mapping['scaleY'])
                a, b = pixel(reference, x, y), pixel(image, ax, ay)
                need(close_rgba(a, b, 2), 'actual OS task pill differs from the current rendered text')
                if len(colors_a) < 3:
                    colors_a.add(tuple(a))
                if len(colors_b) < 3:
                    colors_b.add(tuple(b))
        need(len(colors_a) >= 3 and len(colors_b) >= 3, 'task pill is a blank rectangle, not rendered content')


def tasks(snapshot):
    need(isinstance(snapshot, dict) and isinstance(snapshot.get('tasks'), list), 'progress snapshot is missing')
    return snapshot['tasks']


def find_task(snapshot, tab, task_id):
    found = [item for item in tasks(snapshot) if item.get('tabId') == tab and item.get('taskId') == task_id]
    need(len(found) == 1, 'one owning task is required: ' + task_id)
    return found[0]


def pill(ui, tab):
    found = [item for item in ui.get('panes', []) if item.get('tabId') == tab and item.get('pill')]
    need(len(found) == 1, 'owning visible task pill is missing')
    value = found[0]['pill']
    need(value.get('tabId') == tab and value.get('desk') == ui.get('desk'), 'task pill migrated to a foreign owner')
    return value


def verify_task_time(task, visible, sampled_at):
    need(integer(sampled_at, 1) and isinstance(visible.get('timeRenderedAt'), str)
         and re.fullmatch(r'\d+', visible['timeRenderedAt']), 'actual task timer paint timestamp is missing')
    rendered = int(visible['timeRenderedAt'])
    need(0 < rendered <= sampled_at, 'task timer paint occurs after its UI readback')
    if task.get('phase') != 'running':
        need(visible.get('timeKind') == '' and visible.get('remainingSeconds') == '' and visible.get('elapsedSeconds') == '',
             'a completed, failed or cancelled task retained a running time estimate')
        return
    eta = task.get('etaSeconds')
    if eta is not None:
        need(finite(eta) and eta >= 0 and integer(task.get('updatedAt'), 1)
             and rendered >= task['updatedAt'] and visible.get('estimateUpdatedAt') == str(task['updatedAt']), 'displayed ETA does not use the actual site receipt time')
        remainder = max(0, eta - max(0, rendered - task['updatedAt']) / 1000)
        seconds = math.ceil(remainder)
        kind = 'eta' if remainder > 0 else 'expired'
        need(visible.get('timeKind') == kind and visible.get('remainingSeconds') == str(seconds)
             and visible.get('elapsedSeconds') == '', 'remaining time was not derived solely from the site estimate and elapsed time')
        label = visible.get('label', '')
        need(('Осталось ≈' + str(seconds) + ' с · оценка сайта' in label) if kind == 'eta'
             else ('Оценка истекла · ждём ответ' in label), 'the actual estimate/expiry label differs')
    else:
        need(integer(task.get('createdAt'), 1) and rendered >= task['createdAt'], 'unknown ETA has no actual observed task start')
        seconds = math.floor(max(0, rendered - task['createdAt']) / 1000)
        need(visible.get('timeKind') == 'elapsed' and visible.get('elapsedSeconds') == str(seconds)
             and visible.get('remainingSeconds') == '' and visible.get('estimateUpdatedAt') == ''
             and 'В работе ' + str(seconds) + ' с' in visible.get('label', ''), 'unknown ETA was replaced with an invented remaining time')


def verify_task(read, facts):
    obs, pages = facts.get('observations', {}), facts.get('pages')
    need(isinstance(pages, list) and len(pages) == 2 and {page.get('index') for page in pages} == {0, 1}, 'two owned task pages are required')
    first, second = sorted(pages, key=lambda value: value['index'])
    for name in ('ordinaryLoading', 'ordinaryLoaded'):
        row = obs.get(name, {})
        need(tasks(row.get('state')) == [] and all(not pane.get('pill') for pane in row.get('ui', {}).get('panes', [])),
             'ordinary page loading produced a task pill')
    loading = obs['ordinaryLoading']
    need(loading.get('loading') is True and loading.get('networkPending') == 1 and finite(loading.get('elapsedMs'))
         and loading['elapsedMs'] >= 800 and obs['ordinaryLoaded'].get('loading') is False, 'ordinary slow HTTP loading was not exercised')
    probes = verify_capture(read, obs['ordinaryLoaded'].get('capture'), 'mouse-631-task-ordinary.png', pages)
    eta = obs.get('siteETA', {})
    need(eta.get('dom', {}).get('value') == 128 and eta['dom'].get('max') == 200
         and eta['dom'].get('etaSeconds') == '45' and eta['dom'].get('phase') == 'running', 'DOM progress/ETA input differs')
    need(finite(eta.get('before', {}).get('at')) and finite(eta.get('after', {}).get('at'))
         and eta['after']['at'] - eta['before']['at'] >= 1200, 'site ETA was not observed across elapsed time')
    for owner, task_id, percent, seconds in ((first, 'site-api', 37, 90), (second, 'site-dom', 64, 45)):
        for when in ('before', 'after'):
            task = find_task(eta[when].get('state'), owner['id'], task_id)
            visible = pill(eta[when].get('ui', {}), owner['id'])
            need(task.get('phase') == 'running' and task.get('percent') == percent and task.get('etaSeconds') == seconds
                 and visible.get('ariaNow') == str(percent) and visible.get('etaSeconds') == str(seconds),
                 'site percentage or raw ETA metadata was changed')
            verify_task_time(task, visible, eta[when]['ui'].get('sampledAt'))
    before_time = pill(eta['before']['ui'], first['id'])
    after_time = pill(eta['after']['ui'], first['id'])
    need(int(after_time['remainingSeconds']) < int(before_time['remainingSeconds'])
         and int(after_time['timeRenderedAt']) > int(before_time['timeRenderedAt']), 'site-derived remaining time never advances')
    themes = facts.get('themes')
    need(isinstance(themes, list) and [row.get('theme') for row in themes] == ['light', 'dark'], 'both native task themes are required')
    for row in themes:
        need(row.get('ui', {}).get('theme') == row['theme'], 'task theme differs from actual UI')
        for owner, percent, seconds in ((first, 37, 90), (second, 64, 45)):
            value = pill(row['ui'], owner['id'])
            need(value.get('ariaNow') == str(percent) and value.get('value') == str(percent) + '%'
                 and value.get('etaSeconds') == str(seconds) and 'оценка сайта' in value.get('label', ''), 'native task label lacks actual site values')
            verify_task_time(find_task(row.get('state'), owner['id'], 'site-api' if owner is first else 'site-dom'), value, row['ui'].get('sampledAt'))
        regions = row.get('capture', {}).get('shell', {}).get('regions', [])
        need([value.get('bounds') for value in regions] == [pane['pill']['bounds'] for pane in row['ui']['panes'] if pane.get('pill')], 'OS text probes do not cover the actual pills')
        probes += verify_capture(read, row.get('capture'), 'mouse-631-task-' + row['theme'] + '.png', pages, shell=True)
    zero = obs.get('zeroETA', {})
    need(zero.get('task', {}).get('phase') == 'running' and zero['task'].get('etaSeconds') == 0
         and pill(zero.get('ui', {}), first['id']).get('etaSeconds') == '0', 'zero ETA was treated as completion')
    verify_task_time(zero['task'], pill(zero['ui'], first['id']), zero['ui'].get('sampledAt'))
    expired = obs.get('expiredETA', {})
    need(expired.get('state', {}).get('phase') == 'running' and expired['state'].get('percent') == 37
         and expired['state'].get('etaSeconds') == 1 and expired.get('layoutCalls') == 0,
         'elapsed site estimate completed the task or triggered native layout')
    verify_task_time(expired['task'], pill(expired.get('before', {}), first['id']), expired['before'].get('sampledAt'))
    verify_task_time(expired['state'], pill(expired.get('after', {}), first['id']), expired['after'].get('sampledAt'))
    need(pill(expired['after'], first['id']).get('timeKind') == 'expired', 'positive site ETA never visibly expired')
    unknown = obs.get('unknown', {})
    value = pill(unknown.get('ui', {}), first['id'])
    need(unknown.get('task', {}).get('percent') is None and unknown['task'].get('etaSeconds') is None
         and value.get('ariaNow') is None and value.get('value') == '…' and value.get('etaSeconds') == ''
         and value.get('indeterminate') == 'true' and 'Осталось' not in value.get('label', ''), 'unknown task progress or ETA was fabricated')
    verify_task_time(unknown['task'], value, unknown['ui'].get('sampledAt'))
    later = pill(unknown.get('after', {}), first['id'])
    verify_task_time(unknown['task'], later, unknown['after'].get('sampledAt'))
    need(int(later['elapsedSeconds']) > int(value['elapsedSeconds']) and unknown.get('layoutCalls') == 0,
         'observed elapsed time does not advance independently of native layout')
    spa = obs.get('sameDocument', {})
    need(all(spa.get('before', {}).get(key) == spa.get('after', {}).get(key) for key in ('identity', 'timeOrigin', 'field', 'scrollY', 'cookie', 'webContentsId'))
         and spa.get('after', {}).get('url', '').endswith('#owned-spa') and spa.get('task', {}).get('id') == eta['reported']['id'], 'SPA navigation destroyed or replaced its running task')
    returned = obs.get('desktopReturn', {})
    need(returned.get('from') == first['desk'] and returned.get('other') != first['desk'], 'a different desktop was not exercised')
    need(all(pane.get('pill', {}).get('tabId') not in (first['id'], second['id']) for pane in returned.get('inactiveUI', {}).get('panes', []) if pane.get('pill')), 'inactive task leaked onto another desktop')
    for snapshot in ('inactiveState', 'returned'):
        value = find_task(returned.get(snapshot), first['id'], 'site-api')
        need(value.get('id') == eta['reported']['id'] and value.get('desk') == first['desk']
             and value.get('percent') == 52 and value.get('etaSeconds') == 17, 'background desktop task did not retain its owner and progress')
    need(find_task(obs.get('hiddenProducer', {}).get('state'), second['id'], 'site-dom').get('percent') == 72, 'hidden explicit DOM producer lost its running task')
    for name, task_id in (('apiCompleted', eta['reported']['id']), ('domCompleted', eta['observed']['id'])):
        row = obs.get(name, {})
        need(not any(item.get('id') == task_id for item in tasks(row.get('visibleAfter')))
             and not any(pane.get('pill', {}).get('id') == task_id for pane in row.get('ui', {}).get('panes', []) if pane.get('pill')),
             'completed task still displays a success pill')
        need(finite(row.get('elapsedMs')) and row['elapsedMs'] < (1200 if name == 'apiCompleted' else 2500), 'completed task did not promptly leave the UI')
    final = obs.get('failedAndCancelled', {})
    for owner, name, phase, percent in ((first, 'errorTask', 'error', 31), (second, 'cancelTask', 'cancelled', 48)):
        value = final.get(name, {})
        visible = pill(final.get('ui', {}), owner['id'])
        need(value.get('phase') == phase and value.get('percent') == percent and value.get('etaSeconds') is None
             and visible.get('phase') == phase and visible.get('ariaNow') == str(percent) and visible.get('etaSeconds') == '',
             'error or cancellation fabricated completion or retained a stale ETA')
        verify_task_time(value, visible, final['ui'].get('sampledAt'))
    retired = tasks(obs.get('finalStatesExpired', {}).get('state'))
    need(not any(item.get('id') in (final['errorTask']['id'], final['cancelTask']['id']) for item in retired), 'brief final task states never expire')
    navigation = obs.get('newDocument', {})
    before, after = navigation.get('before', {}), navigation.get('after', {})
    need(before.get('identity') != after.get('identity') and before.get('timeOrigin') != after.get('timeOrigin')
         and before.get('webContentsId') == after.get('webContentsId') and not any(item.get('tabId') == first['id'] for item in tasks(navigation.get('state'))),
         'a replacement document retained an old document task')
    closed = obs.get('closed', {})
    need(closed.get('tabExists') is False and not any(item.get('tabId') == second['id'] for item in tasks(closed.get('state'))), 'closed native tab retained a task')
    need(any(event.get('mainFrame') is True and event.get('tabId') == second['id'] and event.get('taskId') == 'site-dom'
             and event.get('percent') == 64 and event.get('etaSeconds') == 45 for event in facts.get('events', [])), 'real owning preload DOM event is missing')
    return {'themes': 2, 'nativeCaptures': 3, 'pixelProbes': probes, 'taskCases': 15}


def verify_identity(before, after):
    need(isinstance(before, dict) and isinstance(after, dict) and all(key in before and key in after for key in IDENTITY_FIELDS), 'live page identity fields are missing')
    need(all(before[key] == after[key] for key in IDENTITY_FIELDS), 'a live page was reloaded, moved, replaced or lost form/scroll/cookie state')
    index = before['index']
    need(integer(index) and before.get('field') == 'preserved-' + str(index) + '-данные' and before.get('scrollY') == 130 + index
         and before.get('scrollX') == 0 and 'mouse631_' + str(index) + '=' + before['identity'] in before.get('cookie', ''), 'owned page state does not match the real fixture')
    need(re.fullmatch(r'http://127\.0\.0\.1:\d+/page/' + str(index) + r'/', before.get('url', '')) is not None, 'stress page is not the owned HTTP document')
    need(integer(before.get('webContentsId'), 1) and finite(before.get('timeOrigin')) and before['timeOrigin'] > 0
         and integer(before.get('ticks')) and integer(after.get('ticks')) and after['ticks'] >= before['ticks'], 'real page lifetime or timer restarted')


def verify_distribution(value, label):
    need(isinstance(value, dict) and integer(value.get('count'), 1)
         and all(finite(value.get(key)) and value[key] >= 0 for key in ('min', 'p50', 'p95', 'max'))
         and value['min'] <= value['p50'] <= value['p95'] <= value['max'], label + ' timing measurements are missing')


def verify_switch_progress(switch, total, streams, visible):
    progress = switch.get('progress', {})
    state, ui = progress.get('state'), progress.get('ui', {})
    running = tasks(state)
    need(len(running) == 5 and ui.get('desk') == switch['to'], 'five real stream tasks and the active desktop are required')
    for stream in streams:
        task = find_task(state, stream['tabId'], 'stream-' + stream['id'])
        need(task.get('phase') == 'running' and task.get('desk') == stream['desk'], 'a real background stream task is not running for its owner')
    owner = next(stream for stream in streams if stream['desk'] == switch['to'])
    need(progress.get('streamId') == owner['id'], 'switch task evidence belongs to another HTTP stream')
    panes = ui.get('panes')
    need(isinstance(panes, list) and len(panes) == 4 and {p.get('tabId') for p in panes} == {p['id'] for p in visible}
         and all(isinstance(p.get('pills'), list) for p in panes), 'actual task UI does not belong to all four visible pages')
    pills = [(pane, value) for pane in panes for value in pane['pills']]
    need(len(pills) == (1 if total == 20 else 0), 'a visible stream needs exactly one pill; hidden stream owners need no visible pills')
    if total == 50:
        need(owner['tabId'] not in {p['id'] for p in visible}, 'the fifty-page stream owner must remain hidden')
        return
    pane, value = pills[0]
    task = find_task(state, owner['tabId'], 'stream-' + owner['id'])
    need(pane.get('tabId') == value.get('tabId') == owner['tabId'] and value.get('id') == task.get('id')
         and value.get('taskId') == task.get('taskId') and value.get('desk') == owner['desk']
         and value.get('phase') == 'running' and value.get('indeterminate') == 'true' and value.get('value') == '…',
         'visible stress task pill is missing its real running HTTP owner')
    header, slot = rectangle(pane.get('header'), 'owning address row'), rectangle(pane.get('slot'), 'owning page slot')
    dock_value = pane.get('dock', {})
    need(dock_value.get('hidden') is False, 'owning task dock is hidden')
    dock, box = rectangle(dock_value.get('bounds'), 'owning task dock'), rectangle(value.get('bounds'), 'owning task pill')
    need(box['x'] >= dock['x'] and box['y'] >= dock['y'] and box['x'] + box['width'] <= dock['x'] + dock['width']
         and box['y'] + box['height'] <= dock['y'] + dock['height']
         and abs(dock['y'] - header['y'] - header['height']) <= 1 and abs(slot['y'] - dock['y'] - dock['height']) <= 1,
         'the full task pill must be between its own address row and native page')
    capture = switch.get('capture', {})
    native = [p for p in capture.get('native', []) if p.get('tabId') == owner['tabId']]
    need(len(native) == 1 and abs(native[0]['bounds']['y'] - slot['y']) <= 1
         and native[0]['bounds']['y'] >= box['y'] + box['height'] - 1, 'actual native page covers its owning task pill')
    regions = capture.get('shell', {}).get('regions')
    need(isinstance(regions, list) and len(regions) == 1 and regions[0].get('bounds') == box,
         'stress shell pixels are not bound to the actual owning task pill')


def verify_stress(read, facts):
    desks, stages = facts.get('desks'), facts.get('stages')
    need(isinstance(desks, list) and len(desks) == len(set(desks)) == 5, 'five distinct desktops are required')
    need(isinstance(stages, list) and [row.get('ownedPageCount') for row in stages] == [20, 50], 'both 20 and 50 live page workloads are required')
    need(facts.get('renderFailures') == [], 'a native renderer crashed during stress')
    need(facts.get('baselineComparison', {}).get('performed') is False and facts['baselineComparison'].get('reason'), 'historical speedup was claimed without a baseline run')
    probes = 0
    for row, total, switch_count in zip(stages, (20, 50), (5, 10)):
        need(row.get('deskCount') == 5 and row.get('pagesPerDesk') == [total // 5] * 5
             and integer(row.get('totalBrowserPages'), total) and row.get('switchCount') == switch_count, 'live page/desktop/switch counts differ')
        before, after = row.get('beforePages'), row.get('afterPages')
        need(isinstance(before, list) and isinstance(after, list) and len(before) == len(after) == total, 'live identity readbacks are incomplete')
        need({page.get('index') for page in before} == set(range(total)) and len({page.get('id') for page in before}) == total
             and len({page.get('webContentsId') for page in before}) == total, 'live native pages are duplicated or missing')
        for first, last in zip(before, after):
            verify_identity(first, last)
            index = first['index']
            need(first['desk'] == desks[index // 4 if index < 20 else (index - 20) // 6], 'page was assigned to the wrong desktop')
        requests = row.get('requests')
        need(isinstance(requests, list) and len(requests) == total and sorted(value.get('index') for value in requests) == list(range(total)), 'one actual HTTP document load per live page is required')
        streams = row.get('streams')
        need(isinstance(streams, list) and len(streams) == 5 and {stream.get('desk') for stream in streams} == set(desks), 'one actual background HTTP stream per desktop is required')
        for desk_index, desk in enumerate(desks):
            stream = next(item for item in streams if item['desk'] == desk)
            owner_index = desk_index * 4 if total == 20 else 20 + desk_index * 6
            owner = next(page for page in before if page['index'] == owner_index)
            need(stream.get('id') == f'stage{total}-desk{desk_index}' and stream.get('tabId') == owner['id']
                 and stream.get('index') == owner_index, 'actual HTTP stream owner does not match its live page')
        switches = row.get('switches')
        need(isinstance(switches, list) and len(switches) == switch_count, 'settled desktop switches are missing')
        for number, switch in enumerate(switches, 1):
            target = desks[number % 5]
            need(switch.get('sequence') == number and switch.get('from') == desks[(number - 1) % 5]
                 and switch.get('to') == target and finite(switch.get('elapsedMs')) and 0 < switch['elapsedMs'] < 12000,
                 'real desktop switch exceeded its retained deadline or chose another desktop')
            slide = switch.get('slide', {})
            need(slide.get('strategy') == 'live' and slide.get('phase') == 'complete'
                 and slide.get('presented') is True and slide.get('animated') is False
                 and slide.get('decoded') is False and slide.get('borrowedHold') is False
                 and slide.get('snapshotCaptures') == 0 and slide.get('layoutCalls') == 1,
                 'ordinary636 switch did not present live native pages without a snapshot pipeline')
            need(all(finite(slide.get(key)) for key in ('startedAt', 'selectedAt', 'layoutAt', 'totalDurationMs'))
                 and 0 <= slide['startedAt'] <= slide['selectedAt'] <= slide['layoutAt']
                 and 0 < slide['totalDurationMs'] < 12000
                 and slide['layoutAt'] - slide['startedAt'] <= slide['totalDurationMs'],
                 'ordinary636 switch timestamps are incomplete or unordered')
            visible = [page for page in before if page['desk'] == target and page['index'] < 20]
            need(switch.get('visiblePageIds') == [page['id'] for page in visible], 'switch does not present all four owning pages')
            need(switch.get('surfaceCalls') == [] and type(switch.get('counts', {}).get('capturePage')) is int
                 and switch['counts']['capturePage'] == 0,
                 'ordinary636 switch captured or encoded native page snapshots')
            verify_switch_progress(switch, total, streams, visible)
            probes += verify_capture(read, switch.get('capture'), f'mouse-631-stress-{total}-switch-{number}.png', visible,
                                     shell=total == 20, shell_count=1)
        nora = row.get('nora', {})
        need(nora.get('held') is True and len(nora.get('before', [])) == len(nora.get('after', [])) == 5
             and all(integer(a) and integer(b) and b > a for a, b in zip(nora['before'], nora['after'])), 'background HTTP consumers stopped while Nora held the pages')
        need(nora.get('diagnostics', {}).get('lastCapture', {}).get('paintProof') is True
             and nora['diagnostics'].get('lastPaint', {}).get('ready') is True, 'Nora lost its real native paint barrier')
        probes += verify_capture(read, row.get('afterNoraCapture'), f'mouse-631-stress-{total}-after-nora.png', [page for page in before if page['desk'] == desks[0] and page['index'] < 20])
        for stream in streams:
            server, old, new = stream.get('server', {}), stream.get('before', {}), stream.get('after', {})
            values, sent = server.get('values'), server.get('sentAt')
            need(isinstance(values, list) and len(values) > len(old.get('chunks', [])) >= 2
                 and isinstance(sent, list) and len(sent) == len(values), 'background stream never advanced')
            need(server.get('requestCount') == 1 and new.get('requests') == 1 and new.get('done') is True
                 and new.get('error') is None and new.get('chunks') == values and new.get('expected') == len(values)
                 and server.get('digest') == digest('\n'.join(values).encode()), 'actual HTTP stream was restarted, interrupted or lost bytes')
            need(any(item.get('activeDesk') != stream['desk'] for item in sent) and any(item.get('noraHeld') is True for item in sent), 'stream was not exercised while its desktop was inactive and Nora open')
        verify_distribution(row.get('mainEventLoop'), 'main event-loop')
        verify_distribution(row.get('switchLatencyMs'), 'desktop switch')
        renderer = row.get('renderer', {})
        need(integer(renderer.get('frames'), 2) and finite(renderer.get('maxGapMs')) and isinstance(renderer.get('longTasks'), list), 'shell renderer health measurements are missing')
        verify_distribution(renderer.get('gapDistribution'), 'renderer RAF')
        need(integer(row.get('layoutCalls')) and all(integer(row.get('counts', {}).get(key)) for key in ('capturePage', 'getVisible', 'setVisible', 'setBounds', 'nativeCorners', 'state')), 'real native operation counters are missing')
        preview = row.get('previewsAfter', {})
        need(preview.get('enabled') is True and all(integer(preview.get(key)) for key in ('captures', 'resizes', 'bitmapCopies', 'jpegEncodes', 'cacheHits', 'retainedBytes'))
             and preview['retainedBytes'] <= 16 * 1024**2, 'actual preview encoding/cache evidence is missing or unbounded')
        metadata = row.get('metadata')
        need(isinstance(metadata, list) and len(metadata) == total and {item.get('index') for item in metadata} == set(range(total))
             and all(integer(item.get('updates'), 1) for item in metadata), 'every live page must produce real metadata during the stress')
    return {'workloads': [20, 50], 'desktops': 5, 'switches': 15, 'nativeCaptures': 17, 'pixelProbes': probes,
            'switchLatencyMs': {str(row['ownedPageCount']): row['switchLatencyMs'] for row in stages}}


def verify(read, *, expected_platform=None, expected_arch=None):
    reports, hashes = {}, {}
    for kind in ('task', 'stress'):
        name = 'mouse-631-' + kind + '.json'
        blob = read(name)
        need(isinstance(blob, bytes) and len(blob) <= 8 * 1024**2, name + ' report is not bounded bytes')
        report = json.loads(blob)
        need(report.get('version') == VERSION and (report.get('platform'), report.get('arch')) in (('win32', 'x64'), ('darwin', 'arm64'), ('linux', 'x64')),
             name + ' has the wrong installed version or native architecture')
        need(report.get('ok') is True and report.get('restored') is True and not report.get('error') and not report.get('cleanupError')
             and report.get('cleanup', {}).get('restored') is True and report['cleanup'].get('desktopStateRestored') is True,
             name + ' native fixture failed or did not restore its original state')
        need(finite(report.get('elapsedMs')) and 0 < report['elapsedMs'] <= (65000 if kind == 'task' else 200000), name + ' exceeded its fixed native budget')
        reports[kind], hashes[kind] = report, digest(blob)
    task, stress = reports['task'], reports['stress']
    need((task['platform'], task['arch']) == (stress['platform'], stress['arch']), 'task/stress reports come from different platforms')
    if expected_platform is not None:
        need(task['platform'] == expected_platform, 'evidence belongs to another operating system')
    if expected_arch is not None:
        need(task['arch'] == expected_arch, 'evidence belongs to another native architecture')
    task_result = verify_task(read, task)
    stress_result = verify_stress(read, stress)
    return {'ok': True, 'version': VERSION, 'platform': task['platform'], 'arch': task['arch'], 'taskReportSHA256': hashes['task'],
            'stressReportSHA256': hashes['stress'], 'task': task_result, 'stress': stress_result,
            'physicalUserDeviceVerified': False, 'externalAccountsVerified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--platform', choices=('win32', 'darwin', 'linux'))
    parser.add_argument('--arch', choices=('x64', 'arm64'))
    args = parser.parse_args()
    root = args.directory.resolve()

    def read(name):
        need(isinstance(name, str) and re.fullmatch(r'mouse-631-[a-z0-9-]+\.(?:json|png)', name), 'unsafe evidence filename')
        target = root / name
        need(not target.is_symlink() and target.resolve().parent == root and target.is_file(), 'evidence path escaped its directory')
        need(target.stat().st_size <= 16 * 1024**2, 'evidence file is oversized')
        return target.read_bytes()

    result = verify(read, expected_platform=args.platform, expected_arch=args.arch)
    (root / 'mouse-631-acceptance.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('MOUSE_631_INDEPENDENT_EVIDENCE_PASS')
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
