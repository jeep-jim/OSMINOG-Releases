"""Contract fixtures only; these unit tests do not claim native acceptance."""
import copy
import importlib.util
import json
import math
import struct
import unittest
import zlib
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('mouse_631_acceptance', Path(__file__).with_name('mouse632-task-evidence.py'))
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


def png(width, height, pixels, channels=4, filters=None):
    def chunk(kind, value):
        return struct.pack('>I', len(value)) + kind + value + struct.pack('>I', zlib.crc32(kind + value) & 0xffffffff)
    rows, previous = [], [0] * (width * channels)
    for y in range(height):
        row = list(pixels[y * width * channels:(y + 1) * width * channels])
        method = filters[y % len(filters)] if filters else 0
        encoded = []
        for x, value in enumerate(row):
            a, b, c = row[x - channels] if x >= channels else 0, previous[x], previous[x - channels] if x >= channels else 0
            p = a + b - c
            pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            predictor = [0, a, b, (a + b) // 2, a if pa <= pb and pa <= pc else b if pb <= pc else c][method]
            encoded.append((value - predictor) & 255)
        rows.append(bytes([method] + encoded))
        previous = row
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6 if channels == 4 else 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b''.join(rows))) + chunk(b'IEND', b''))


def owned(index, *, task=False):
    return {'id': ('task-' if task else 'page-') + str(index), 'index': index,
            'desk': 'd0' if task else 'd' + str(index // 4 if index < 20 else (index - 20) // 6),
            'webContentsId': 100 + index, 'url': f'http://127.0.0.1:31337/page/{index}/', 'navigationEpoch': 1,
            'identity': f'owned-identity-{index}', 'timeOrigin': 1000000 + index, 'field': f'preserved-{index}-данные',
            'scrollX': 0, 'scrollY': 130 + index, 'cookie': f'mouse631_{index}=owned-identity-{index}', 'ticks': 10}


def capture(files, name, pages, *, shell=False, pill_ids=None):
    width, height = 240, 440 if len(pages) == 4 else 240
    pixels = bytearray([240, 237, 225, 255] * (width * height))

    def fill(box, rgba):
        for y in range(box['y'], box['y'] + box['height']):
            for x in range(box['x'], box['x'] + box['width']):
                at = (y * width + x) * 4
                pixels[at:at + 4] = bytes(rgba)

    result = {'filename': name, 'displayFilename': name[:-4] + '-display.png', 'source': 'globalCapture.acquire(display)',
              'kind': 'screen', 'backend': 'unit-fixture-not-native', 'display': {'bounds': {'x': 0, 'y': 0, 'width': width, 'height': height}, 'scaleFactor': 1},
              'contentBounds': {'x': 0, 'y': 0, 'width': width, 'height': height}, 'screenPixelSize': {'width': width, 'height': height},
              'cropPixels': {'x': 0, 'y': 0, 'width': width, 'height': height}, 'mapping': {'scaleX': 1, 'scaleY': 1, 'originX': 0, 'originY': 0},
              'pixelSize': {'width': width, 'height': height}, 'native': [], 'content': [], 'probes': [], 'attempts': [{'accepted': True}]}
    pill_regions = []
    for number, page in enumerate(pages):
        box = {'x': 10 + number % 2 * 110, 'y': 50 + number // 2 * 190, 'width': 100, 'height': 180}
        result['native'].append({'tabId': page['id'], 'index': page['index'], 'desk': page['desk'], 'webContentsId': page['webContentsId'],
                                 'bounds': box, 'viewBounds': box.copy(), 'parentBounds': None, 'actualBounds': box.copy(),
                                 'visible': True, 'parentVisible': True, 'cachedVisible': True, 'attached': True})
        content = {'tabId': page['id'], 'index': page['index'], 'identity': page['identity'], 'regions': []}
        result['content'].append(content)
        for part, left in enumerate((10, 60)):
            local = {'x': left, 'y': 25, 'width': 30, 'height': 20}
            rgb = CHECK.color(page['index'], part)
            fill({**local, 'x': box['x'] + left, 'y': box['y'] + 25}, rgb + [255])
            content['regions'].append({'part': 'ab'[part], 'bounds': local, 'color': 'rgb(' + ', '.join(map(str, rgb)) + ')'})
            for dx, dy in ((0, 0), (-6, 0), (6, 0), (0, -6), (0, 6)):
                point = {'x': box['x'] + left + 15 + dx, 'y': box['y'] + 35 + dy}
                result['probes'].append({'tabId': page['id'], 'index': page['index'], 'webContentsId': page['webContentsId'], 'desk': page['desk'],
                                         'region': 'ab'[part], 'localBounds': local, 'offset': {'x': dx, 'y': dy}, 'cssPoint': point,
                                         'x': point['x'], 'y': point['y'], 'expectedRGB': rgb, 'actualRGBA': rgb + [255], 'tolerance': 3})
        if shell and (pill_ids is None or page['id'] in pill_ids):
            pill_box = {'x': box['x'], 'y': box['y'] - 25, 'width': 100, 'height': 20}
            fill(pill_box, [40, 45, 50, 255])
            fill({'x': box['x'] + 4, 'y': 30, 'width': 15, 'height': 4}, [210, 210, 210, 255])
            fill({'x': box['x'] + 30, 'y': 30, 'width': 5, 'height': 6}, [180, 140, 20, 255])
            pill_regions.append({'label': 'unit fixture text', 'bounds': pill_box})
    blob = png(width, height, pixels)
    for filename in (name, result['displayFilename']):
        files[filename] = blob
    result['sha256'] = result['displaySha256'] = CHECK.digest(blob)
    if shell:
        reference = name[:-4] + '-shell-reference.png'
        files[reference] = blob
        result['shell'] = {'filename': reference, 'sha256': CHECK.digest(blob), 'pixelSize': result['pixelSize'], 'regions': pill_regions}
    return result


def task_value(page, name, percent, eta, phase='running'):
    return {'id': page['id'] + '-' + name, 'taskId': name, 'tabId': page['id'], 'desk': page['desk'], 'source': 'page',
            'phase': phase, 'percent': percent, 'etaSeconds': eta, 'kind': 'observed' if name == 'site-dom' else 'reported',
            'createdAt': 1000000, 'updatedAt': 1000000}


def ui(pages, values, theme='light', at=1000000):
    panes = []
    for number, page in enumerate(pages):
        value = next((item for item in values if item['tabId'] == page['id']), None)
        visible = None
        if value:
            if value['phase'] != 'running':
                timing = {'timeKind': '', 'remainingSeconds': '', 'elapsedSeconds': '', 'estimateUpdatedAt': '', 'label': 'данные сайта'}
            elif value['etaSeconds'] is not None:
                seconds = math.ceil(max(0, value['etaSeconds'] - (at - value['updatedAt']) / 1000))
                timing = {'timeKind': 'eta' if seconds else 'expired', 'remainingSeconds': str(seconds), 'elapsedSeconds': '',
                          'estimateUpdatedAt': str(value['updatedAt']),
                          'label': f'Осталось ≈{seconds} с · оценка сайта' if seconds else 'Оценка истекла · ждём ответ'}
            else:
                seconds = math.floor(max(0, at - value['createdAt']) / 1000)
                timing = {'timeKind': 'elapsed', 'remainingSeconds': '', 'elapsedSeconds': str(seconds), 'estimateUpdatedAt': '',
                          'label': f'В работе {seconds} с'}
            visible = {**value, 'ariaNow': str(value['percent']) if value['percent'] is not None else None,
                       'value': str(value['percent']) + '%' if value['percent'] is not None else '…',
                       'indeterminate': str(value['percent'] is None).lower(), 'etaSeconds': '' if value['etaSeconds'] is None else str(value['etaSeconds']),
                       **timing, 'timeRenderedAt': str(at),
                       'bounds': {'x': 10 + number * 110, 'y': 25, 'width': 100, 'height': 20}}
        panes.append({'tabId': page['id'], 'pill': visible})
    return {'sampledAt': at, 'theme': theme, 'desk': 'd0', 'panes': panes}


def stress_progress(pages, values, captured, target, stream_id):
    actual_ui = ui(pages, values)
    actual_ui['desk'] = target
    for pane, native in zip(actual_ui['panes'], captured['native']):
        box = native['bounds']
        value = pane.pop('pill')
        pane['pills'] = [value] if value else []
        pane['header'] = {**box, 'y': box['y'] - 50, 'height': 25}
        pane['dock'] = {'hidden': value is None, 'bounds': {**box, 'y': box['y'] - 25, 'height': 25}}
        pane['slot'] = box.copy()
    return {'streamId': stream_id, 'state': {'tasks': copy.deepcopy(values)}, 'ui': actual_ui}


def fixtures():
    files = {}
    pages = [owned(0, task=True), owned(1, task=True)]
    first, second = pages
    api, dom = task_value(first, 'site-api', 37, 90), task_value(second, 'site-dom', 64, 45)
    values = [api, dom]
    state = lambda items: {'tasks': copy.deepcopy(items)}
    task = {'version': CHECK.VERSION, 'platform': 'win32', 'arch': 'x64', 'ok': True, 'restored': True, 'elapsedMs': 20000,
            'cleanup': {'restored': True, 'desktopStateRestored': True}, 'pages': pages, 'observations': {}, 'themes': [],
            'events': [{'mainFrame': True, 'tabId': second['id'], 'taskId': 'site-dom', 'percent': 64, 'etaSeconds': 45}]}
    obs = task['observations']
    obs['ordinaryLoading'] = {'elapsedMs': 800, 'networkPending': 1, 'loading': True, 'state': state([]), 'ui': ui(pages, [])}
    obs['ordinaryLoaded'] = {'loading': False, 'state': state([]), 'ui': ui(pages, []),
                             'capture': capture(files, 'mouse-631-task-ordinary.png', pages)}
    obs['siteETA'] = {'reported': api, 'observed': dom, 'dom': {'value': 128, 'max': 200, 'etaSeconds': '45', 'phase': 'running'},
                      'before': {'at': 1, 'state': state(values), 'ui': ui(pages, values)},
                      'after': {'at': 1251, 'state': state(values), 'ui': ui(pages, values, at=1001250)}}
    for theme in ('light', 'dark'):
        task['themes'].append({'theme': theme, 'state': state(values), 'ui': ui(pages, values, theme, at=1002000),
                               'capture': capture(files, 'mouse-631-task-' + theme + '.png', pages, shell=True)})
    zero, unknown = task_value(first, 'site-api', 37, 0), task_value(first, 'site-api', None, None)
    obs['zeroETA'] = {'task': zero, 'ui': ui(pages, [zero, dom])}
    short = task_value(first, 'site-api', 37, 1)
    obs['expiredETA'] = {'task': short, 'state': short, 'before': ui(pages, [short, dom]),
                         'after': ui(pages, [short, dom], at=1001500), 'layoutCalls': 0}
    obs['unknown'] = {'task': unknown, 'ui': ui(pages, [unknown, dom], at=1006500),
                      'after': ui(pages, [unknown, dom], at=1008000), 'layoutCalls': 0}
    obs['sameDocument'] = {'before': first.copy(), 'after': {**first, 'url': first['url'] + '#owned-spa'}, 'task': api}
    updated = task_value(first, 'site-api', 52, 17)
    obs['desktopReturn'] = {'from': 'd0', 'other': 'd1', 'inactiveUI': {'panes': []}, 'inactiveState': state([updated, dom]), 'returned': state([updated, dom])}
    obs['hiddenProducer'] = {'state': state([updated, task_value(second, 'site-dom', 72, 45)])}
    for name in ('apiCompleted', 'domCompleted'):
        obs[name] = {'visibleAfter': state([]), 'ui': ui(pages, []), 'elapsedMs': 100}
    failed, cancelled = task_value(first, 'error-case', 31, None, 'error'), task_value(second, 'cancel-case', 48, None, 'cancelled')
    obs['failedAndCancelled'] = {'errorTask': failed, 'cancelTask': cancelled, 'ui': ui(pages, [failed, cancelled])}
    obs['finalStatesExpired'] = {'state': state([])}
    obs['newDocument'] = {'before': first.copy(), 'after': {**first, 'identity': 'new-document', 'timeOrigin': 2000000}, 'state': state([])}
    obs['closed'] = {'tabExists': False, 'state': state([])}
    desks = ['d' + str(i) for i in range(5)]
    stress = {'version': CHECK.VERSION, 'platform': 'win32', 'arch': 'x64', 'ok': True, 'restored': True, 'elapsedMs': 60000,
              'cleanup': {'restored': True, 'desktopStateRestored': True}, 'desks': desks, 'renderFailures': [],
              'baselineComparison': {'performed': False, 'reason': 'This is a unit contract fixture, not a benchmark.'}, 'stages': []}
    distribution = {'count': 10, 'min': 1, 'p50': 2, 'p95': 3, 'max': 4}
    for total, switches in ((20, 5), (50, 10)):
        pages = [owned(i) for i in range(total)]
        stream_owners = [pages[d * 4 if total == 20 else 20 + d * 6] for d in range(5)]
        stream_tasks = [task_value(page, f'stream-stage{total}-desk{d}', None, None) for d, page in enumerate(stream_owners)]
        row = {'ownedPageCount': total, 'totalBrowserPages': total + 1, 'deskCount': 5, 'pagesPerDesk': [total // 5] * 5,
               'switchCount': switches, 'beforePages': copy.deepcopy(pages), 'afterPages': [{**page, 'ticks': 100} for page in pages],
               'requests': [{'index': page['index'], 'path': '/page/' + str(page['index']) + '/'} for page in pages],
               'switches': [], 'streams': [], 'nora': {'held': True, 'before': [2] * 5, 'after': [3] * 5,
                                                     'diagnostics': {'lastCapture': {'paintProof': True}, 'lastPaint': {'ready': True}}},
               'mainEventLoop': distribution.copy(), 'switchLatencyMs': distribution.copy(),
               'renderer': {'frames': 100, 'maxGapMs': 4, 'longTasks': [], 'gapDistribution': distribution.copy()},
               'layoutCalls': 10, 'counts': dict.fromkeys(('capturePage', 'getVisible', 'setVisible', 'setBounds', 'nativeCorners', 'state'), 10),
               'previewsAfter': {'enabled': True, **dict.fromkeys(('captures', 'resizes', 'bitmapCopies', 'jpegEncodes', 'cacheHits', 'retainedBytes'), 10)},
               'metadata': [{'index': page['index'], 'updates': 12} for page in pages]}
        for number in range(1, switches + 1):
            target = desks[number % 5]
            visible = [page for page in pages if page['desk'] == target and page['index'] < 20]
            calls = []
            for desk in (desks[(number - 1) % 5], target):
                owners = [page for page in pages if page['desk'] == desk and page['index'] < 20]
                calls.append({'error': None, 'diagnostics': {'lastCapture': {'complete': True, 'paintProof': False,
                               'requestedIds': [page['id'] for page in owners], 'pages': [{'id': page['id'], 'webContentsId': page['webContentsId'], 'bitmapReadouts': 0,
                               **dict.fromkeys(('queueMs', 'captureMs', 'pngMs', 'base64Ms', 'previewMs'), .1)} for page in owners]}}})
            captured = capture(files, f'mouse-631-stress-{total}-switch-{number}.png', visible,
                               shell=total == 20, pill_ids={stream_owners[number % 5]['id']})
            row['switches'].append({'sequence': number, 'from': desks[(number - 1) % 5], 'to': target, 'elapsedMs': 400,
                                   'slide': {'phase': 'complete', 'animated': True, 'decoded': True, 'totalDurationMs': 399},
                                   'visiblePageIds': [page['id'] for page in visible], 'surfaceCalls': calls,
                                   'progress': stress_progress(visible, stream_tasks, captured, target, f'stage{total}-desk{number % 5}'),
                                   'capture': captured})
        row['afterNoraCapture'] = capture(files, f'mouse-631-stress-{total}-after-nora.png', pages[:4])
        for d, desk in enumerate(desks):
            chunks = ['owned-one', 'owned-two', 'owned-three-данные']
            row['streams'].append({'desk': desk, 'id': f'stage{total}-desk{d}', 'tabId': stream_owners[d]['id'],
                                   'index': stream_owners[d]['index'], 'before': {'chunks': chunks[:2]},
                                   'server': {'requestCount': 1, 'values': chunks, 'sentAt': [{'activeDesk': 'other', 'noraHeld': True}] * 3,
                                              'digest': CHECK.digest('\n'.join(chunks).encode())},
                                   'after': {'requests': 1, 'done': True, 'error': None, 'chunks': chunks, 'expected': 3}})
        stress['stages'].append(row)
    files['mouse-631-task.json'] = json.dumps(task).encode()
    files['mouse-631-stress.json'] = json.dumps(stress).encode()
    return files, task, stress


class AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.task, cls.stress = fixtures()

    def test_complete_two_workloads_and_task_contract_is_accepted(self):
        result = CHECK.verify(self.files.__getitem__, expected_platform='win32', expected_arch='x64')
        self.assertTrue(result['ok'])
        self.assertEqual(result['task']['pixelProbes'], 60)
        self.assertEqual(result['stress']['pixelProbes'], 680)
        self.assertEqual(result['stress']['switches'], 15)

    def test_decoder_reads_all_five_real_png_filters_rgb_and_rgba(self):
        for channels in (3, 4):
            raw = bytes((i * 31 + 17) % 256 for i in range(7 * 5 * channels))
            image = CHECK.decode_png(png(7, 5, raw, channels, list(range(5))))
            self.assertEqual(image['pixels'], raw)

    def test_decoder_rejects_corruption_and_trailing_bytes(self):
        original = self.files['mouse-631-task-ordinary.png']
        for damaged in (original[:-1], original + b'junk', original[:40] + bytes([original[40] ^ 1]) + original[41:]):
            with self.assertRaises(ValueError):
                CHECK.decode_png(damaged)

    def test_json_and_rehashed_wrong_png_cannot_claim_live_native_content(self):
        record = copy.deepcopy(self.task['observations']['ordinaryLoaded']['capture'])
        name = record['filename']
        image = CHECK.decode_png(self.files[name])
        probe = record['probes'][0]
        offset = (probe['y'] * image['width'] + probe['x']) * 4
        image['pixels'][offset:offset + 4] = bytes([0, 0, 0, 255])
        wrong = png(image['width'], image['height'], image['pixels'])
        files = {**self.files, name: wrong, record['displayFilename']: wrong}
        record['sha256'] = record['displaySha256'] = CHECK.digest(wrong)
        record['probes'][0]['actualRGBA'] = [0, 0, 0, 255]
        with self.assertRaisesRegex(ValueError, 'missing the live page content'):
            CHECK.verify_capture(files.__getitem__, record, name, self.task['pages'])

    def test_wrong_dpi_or_owner_cannot_relabel_native_pixels(self):
        original = self.task['observations']['ordinaryLoaded']['capture']
        for mutate in (lambda value: value['mapping'].update(scaleX=2),
                       lambda value: value['native'][0].update(webContentsId=999),
                       lambda value: value['probes'][0].update(tolerance=99)):
            record = copy.deepcopy(original)
            mutate(record)
            with self.assertRaises(ValueError):
                CHECK.verify_capture(self.files.__getitem__, record, record['filename'], self.task['pages'])

    def test_stress_task_requires_the_real_running_stream_owner(self):
        for change in ('missing', 'foreign-pill', 'nonrunning', 'foreign-stream'):
            with self.subTest(change=change):
                facts = copy.deepcopy(self.stress)
                switch = facts['stages'][0]['switches'][0]
                if change == 'missing':
                    switch.pop('progress')
                elif change == 'foreign-pill':
                    switch['progress']['ui']['panes'][0]['pills'][0]['tabId'] = 'page-0'
                elif change == 'nonrunning':
                    switch['progress']['state']['tasks'][1]['phase'] = 'completed'
                else:
                    facts['stages'][0]['streams'][1]['tabId'] = 'page-5'
                with self.assertRaises(ValueError):
                    CHECK.verify_stress(self.files.__getitem__, facts)

    def test_stress_task_pixel_region_is_bound_to_the_actual_pill_and_native_dock(self):
        for change in ('missing-reference', 'foreign-region', 'native-cover'):
            with self.subTest(change=change):
                facts = copy.deepcopy(self.stress)
                switch = facts['stages'][0]['switches'][0]
                if change == 'missing-reference':
                    switch['capture'].pop('shell')
                elif change == 'foreign-region':
                    switch['capture']['shell']['regions'][0]['bounds']['x'] += 1
                else:
                    switch['capture']['native'][0]['bounds']['y'] = 25
                with self.assertRaisesRegex(ValueError, 'bound to the actual owning task pill|covers its owning task pill'):
                    CHECK.verify_stress(self.files.__getitem__, facts)

    def test_rehashed_native_page_pixels_cannot_cover_the_stress_task_pill(self):
        for forge_reference in (False, True):
            with self.subTest(forge_reference=forge_reference):
                facts = copy.deepcopy(self.stress)
                captured = facts['stages'][0]['switches'][0]['capture']
                image = CHECK.decode_png(self.files[captured['filename']])
                box = captured['shell']['regions'][0]['bounds']
                for y in range(box['y'], box['y'] + box['height']):
                    for x in range(box['x'], box['x'] + box['width']):
                        offset = (y * image['width'] + x) * 4
                        image['pixels'][offset:offset + 4] = bytes([240, 237, 225, 255])
                wrong = png(image['width'], image['height'], image['pixels'])
                files = {**self.files, captured['filename']: wrong, captured['displayFilename']: wrong}
                captured['sha256'] = captured['displaySha256'] = CHECK.digest(wrong)
                if forge_reference:
                    files[captured['shell']['filename']] = wrong
                    captured['shell']['sha256'] = CHECK.digest(wrong)
                with self.assertRaisesRegex(ValueError, 'OS task pill differs|blank rectangle'):
                    CHECK.verify_stress(files.__getitem__, facts)

    def test_fifty_page_hidden_streams_cannot_claim_visible_pills(self):
        facts = copy.deepcopy(self.stress)
        row = facts['stages'][1]
        switch = row['switches'][0]
        switch['progress']['ui']['panes'][0]['pills'] = [copy.deepcopy(self.stress['stages'][0]['switches'][0]['progress']['ui']['panes'][0]['pills'][0])]
        with self.assertRaisesRegex(ValueError, 'hidden stream owners need no visible pills'):
            CHECK.verify_stress(self.files.__getitem__, facts)

    def test_task_shell_still_requires_two_pills_by_default(self):
        captured = copy.deepcopy(self.task['themes'][0]['capture'])
        captured['shell']['regions'].pop()
        image = CHECK.decode_png(self.files[captured['filename']])
        with self.assertRaisesRegex(ValueError, '2 real task pills'):
            CHECK.verify_shell(self.files.__getitem__, captured, image)

    def test_reload_and_form_loss_fail_even_when_native_id_is_reused(self):
        before = owned(7)
        for mutate in (lambda value: value.update(timeOrigin=999), lambda value: value.update(field='lost'),
                       lambda value: value.update(scrollY=0), lambda value: value.update(cookie='')):
            after = before.copy()
            mutate(after)
            with self.assertRaises(ValueError):
                CHECK.verify_identity(before, after)

    def test_missing_fifty_page_workload_is_rejected(self):
        facts = copy.deepcopy(self.stress)
        facts['stages'].pop()
        with self.assertRaisesRegex(ValueError, 'both 20 and 50'):
            CHECK.verify_stress(self.files.__getitem__, facts)

    def test_ordinary_load_task_and_modified_raw_site_eta_are_rejected(self):
        for ordinary in (True, False):
            facts = copy.deepcopy(self.task)
            if ordinary:
                facts['observations']['ordinaryLoading']['state']['tasks'].append({'kind': 'navigation'})
            else:
                facts['observations']['siteETA']['after']['state']['tasks'][0]['etaSeconds'] = 89
            with self.assertRaisesRegex(ValueError, 'ordinary page loading|raw ETA metadata'):
                CHECK.verify_task(self.files.__getitem__, facts)

    def test_countdown_must_derive_from_site_receipt_and_actual_paint_time(self):
        facts = copy.deepcopy(self.task)
        facts['observations']['siteETA']['after']['ui']['panes'][0]['pill']['remainingSeconds'] = '81'
        with self.assertRaisesRegex(ValueError, 'solely from the site estimate'):
            CHECK.verify_task(self.files.__getitem__, facts)

    def test_expiry_cannot_report_completion_or_trigger_native_layout(self):
        for key, value in (('layoutCalls', 1), ('state', {'phase': 'completed', 'percent': 100, 'etaSeconds': 1})):
            facts = copy.deepcopy(self.task)
            facts['observations']['expiredETA'][key] = value
            with self.assertRaisesRegex(ValueError, 'completed the task or triggered native layout'):
                CHECK.verify_task(self.files.__getitem__, facts)

    def test_native_failed_cleanup_or_wrong_platform_is_rejected(self):
        for key, value in (('restored', False), ('platform', 'linux'), ('elapsedMs', 65001)):
            facts = copy.deepcopy(self.task)
            facts[key] = value
            files = {**self.files, 'mouse-631-task.json': json.dumps(facts).encode()}
            with self.assertRaises(ValueError):
                CHECK.verify(files.__getitem__)

    def test_stream_restart_and_lost_bytes_fail_with_all_switches_present(self):
        for key, value in (('requests', 2), ('chunks', ['lost'])):
            facts = copy.deepcopy(self.stress)
            facts['stages'][0]['streams'][0]['after'][key] = value
            with self.assertRaisesRegex(ValueError, 'restarted, interrupted or lost bytes'):
                CHECK.verify_stress(self.files.__getitem__, facts)


if __name__ == '__main__':
    unittest.main()
