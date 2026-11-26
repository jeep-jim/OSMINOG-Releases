#!/usr/bin/env python3
"""Independently read641 native user flows, display bytes and restart evidence."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re

_spec = importlib.util.spec_from_file_location('mouse641_pixels', Path(__file__).with_name('mouse641-task-evidence.py'))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)
VERSION = '6.0.41'
SOURCE = 'Installed641 OS input, owned HTTP pages, actual display pixels and separate-process persistence'
NATIVE = {'darwin': 'CGEvent', 'win32': 'User32', 'linux': 'XTest'}
FIELDS = ('id', 'index', 'webContentsId', 'url', 'navigationEpoch', 'identity', 'timeOrigin', 'field', 'scrollX', 'scrollY', 'cookie')


def need(value, message):
    if not value:
        raise ValueError('Mouse641 workspace: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def same_grid(before, after):
    need(isinstance(before.get('slots'), dict) and len(before['slots']) >= 2, 'a real existing grid is required')
    for key in ('tree', 'slots', 'pinnedPanes', 'desktopId'):
        need(key in before and before[key] == after.get(key), 'classic activation changed saved grid ' + key)


def same_page(before, after, *, desktop=True):
    for key in FIELDS + (('desk',) if desktop else ()):
        need(key in before and before[key] == after.get(key), 'live page was reloaded/replaced or changed ' + key)
    need(P.finite(before.get('ticks')) and P.finite(after.get('ticks')) and after['ticks'] >= before['ticks'], 'live page timer restarted')


def classic(value, tab_id):
    panes = value.get('panes', [])
    need(value.get('classicTabId') == tab_id and value.get('mode') == 'classic' and value.get('returnVisible') is True
         and len(panes) == 1 and panes[0].get('id') == 'p0' and panes[0].get('view') == 'classic', 'one active classic page with a visible grid return is required')


def input_receipt(row, platform, pid, ledger=None, *, selector=None, action='click'):
    need(isinstance(row, dict) and row.get('source') == NATIVE[platform] and row.get('pid') == pid
         and isinstance(row.get('selector'), str) and row['selector'] and row.get('action') == action,
         'input source/process/action is not the actual native route')
    need(ledger is None or row in ledger, 'action is absent from its native process ledger')
    need(selector is None or row['selector'] == selector, 'input targeted a different control')
    events = row.get('events', [])
    intercepted = action == 'click' and row.get('interceptedLink') is True
    if intercepted:
        need(row['selector'] in ('#ordinary-link', '#new-tab-link') and isinstance(row.get('linkURL'), str)
             and re.fullmatch(r'http://127\.0\.0\.1:\d+/page/[23]/', row['linkURL']), 'unknown link claims isolated interception')
    required = 'pointerdown' if action == 'drag' or intercepted else action
    need(isinstance(events, list) and 0 < len(events) <= 300 and any(e.get('type') == required and e.get('trusted') is True and e.get('matches') is True for e in events), 'trusted OS input never reached its real target')
    if action == 'drag':
        need(all(P.finite(row.get(key, {}).get(axis)) for key in ('from', 'to') for axis in ('x', 'y'))
             and row.get('released') is True, 'native drag lacks bounded coordinates/release')
    else:
        need(all(P.finite(row.get('point', {}).get(axis)) for axis in ('x', 'y')) and P.finite(row.get('at')), 'native click coordinates/time absent')


def key_receipt(row, platform, pid):
    need(row.get('source') == NATIVE[platform] and row.get('pid') == pid and row.get('key') in ('HOME', 'END', 'ENTER', 'ESC', 'DOWN', 'UP', 'LEFT', 'RIGHT')
         and P.finite(row.get('at')), 'key did not use the actual OS driver')


def windows_html_drag(row, kind, pid):
    """Read the independent child receipt; ordinary shell drags keep their gate."""
    value = row.get('nativeDrag', {})
    need(isinstance(value, dict) and value.get('schema') == 1
         and value.get('method') == 'independent-native-html-input-process'
         and value.get('platform') == 'win32' and value.get('source') == 'User32'
         and value.get('parentPid') == pid and type(value.get('childPid')) is int
         and value['childPid'] > 0 and value['childPid'] != pid and value.get('kind') == kind,
         'Windows HTML drag lacks its separate native input process')
    need(isinstance(value.get('nonce'), str) and re.fullmatch(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}', value['nonce']),
         'Windows HTML drag child identity is absent')
    need(value.get('ok') is True and value.get('released') is True
         and type(value.get('exitCode')) is int and value['exitCode'] == 0 and 'exitSignal' in value and value['exitSignal'] is None
         and value.get('terminationRequested') is False and not value.get('error') and not value.get('releaseError')
         and 'failureCleanup' not in value and not row.get('observationError'),
         'Windows HTML drag child failed, was killed, or did not release')
    budget = value.get('budgetMs'); hold, settle = (1000, 5000) if kind == 'edge' else (400, 200)
    need(type(budget) is int and 0 < budget <= 15000 and value.get('driverCallLimitMs') == 7000
         and value.get('lifecycleLimitMs') == 30000 and value.get('holdMs') == hold and value.get('settleMs') == settle,
         'Windows HTML drag deadline/hold/lifecycle differs')
    need(all(type(value.get(key)) is int for key in ('startedAt', 'completedAt', 'forkedAt', 'exitAt', 'deadlineAt'))
         and P.finite(value.get('elapsedMs')) and value['elapsedMs'] == value['completedAt'] - value['startedAt'],
         'Windows HTML drag raw process timestamps are missing')

    def point(value):
        need(isinstance(value, dict) and set(value) == {'x', 'y'}
             and all(type(value[axis]) is int and abs(value[axis]) <= 2 ** 53 - 1 for axis in ('x', 'y')),
             'Windows HTML drag coordinates are not finite native points')
        return value

    events = value.get('events', []); coordinates = value.get('coordinates', {}); count = 23 if kind == 'edge' else 15
    need(isinstance(events, list) and len(events) == count and isinstance(coordinates, dict)
         and coordinates.get('source') == 'Electron screen.dipToScreenPoint'
         and isinstance(coordinates.get('samples'), list) and len(coordinates['samples']) == count,
         'Windows HTML drag lacks its complete mapped native sequence')
    samples = coordinates['samples']; logical = []
    for index, (event, sample) in enumerate(zip(events, samples)):
        need(isinstance(event, dict) and isinstance(sample, dict), 'Windows HTML drag point receipt is invalid')
        logical.append(point(sample.get('logical'))); physical = point(sample.get('physical'))
        phase = 0 if index == 0 else 2 if index == count - 1 else 1
        need(type(event.get('phase')) is int and event['phase'] == phase and event.get('accepted') is True
             and point({axis: event.get(axis) for axis in ('x', 'y')}) == physical and type(event.get('at')) is int,
             'Windows HTML drag phases/physical coordinates do not match its actual input')
    start, finish = point(row.get('from')), point(row.get('to'))
    need(logical[0] == start and logical[-1] == logical[-2] == finish,
         'Windows HTML drag endpoints differ from the parent input ledger')
    threshold = {'x': start['x'] + 12, 'y': start['y'] + 7}; target = logical[13]
    expected = [start, threshold]
    def segment(a, b, steps):
        # JavaScript Math.round resolves halves towards positive infinity.
        return [{axis: math.floor(a[axis] + (b[axis] - a[axis]) * step / steps + .5)
                 for axis in ('x', 'y')} for step in range(1, steps + 1)]
    expected += segment(threshold, target, 12)
    if kind == 'edge': expected += segment(target, finish, 8)
    expected.append(finish)
    need(logical == expected, 'Windows HTML drag did not execute the planned native path')

    timing = value.get('timing', {})
    need(isinstance(timing, dict) and timing.get('source') == 'process.hrtime.bigint'
         and timing.get('scope') == 'per-process elapsed', 'Windows HTML drag lacks process-local timing')
    child, parent = timing.get('child', {}), timing.get('parent', {})
    need(isinstance(child, dict) and isinstance(parent, dict) and isinstance(child.get('eventNs'), list)
         and len(child['eventNs']) == count, 'Windows HTML drag timing samples are incomplete')
    def ns(value):
        need(isinstance(value, str) and re.fullmatch(r'0|[1-9]\d{0,19}', value), 'Windows HTML drag monotonic offset is invalid')
        return int(value)
    event_ns = [ns(stamp) for stamp in child['eventNs']]; total = ns(child.get('elapsedNs'))
    hold_start, hold_end = ns(child.get('holdStartNs')), ns(child.get('holdEndNs'))
    need(event_ns == sorted(event_ns) and event_ns[-1] <= total <= budget * 1000000
         and event_ns[13] <= hold_start <= hold_end <= event_ns[14]
         and hold_end - hold_start >= hold * 1000000
         and event_ns[-1] - max(event_ns[-2], hold_end) >= settle * 1000000,
         'Windows HTML drag timing does not prove bounded hold, settling and final UP')
    need(ns(parent.get('preparationNs')) + ns(parent.get('elapsedNs')) <= budget * 1000000,
         'Windows HTML drag parent deadline was exceeded including startup and exit')
    return value


def windows_held_drag(row, pid):
    held, receipt = row.get('whileHeld', {}), row['input']['nativeDrag']
    before = row.get('before', {}); origin = before.get('desk'); tab_id = before.get('id')
    need(isinstance(origin, str) and origin and isinstance(tab_id, str) and tab_id
         and isinstance(held, dict) and held.get('observerPid') == pid and held.get('active') is True
         and held.get('sourceTabId') == tab_id and row['input'].get('tabId') == tab_id
         and held.get('originDesk') == origin and held.get('sourceMembership') == origin
         and held.get('sourceMembershipAfterCapture') == origin
         and held.get('mouseDown') is True and held.get('mouseDownAfterCapture') is True,
         'Windows held drag lacks actual original ownership and OS button samples around capture')
    observed, captured = held.get('observedAt'), held.get('captureFinishedAt')
    need(type(observed) is int and type(captured) is int
         and receipt['events'][0]['at'] <= observed <= captured <= receipt['events'][-1]['at'],
         'Windows held capture was observed outside the actual native DOWN/UP interval')
    def ns(value):
        need(isinstance(value, str) and re.fullmatch(r'0|[1-9]\d{0,19}', value), 'Windows held parent timing is invalid')
        return int(value)
    parent = receipt['timing']['parent']
    need(ns(held.get('observedElapsedNs')) <= ns(held.get('captureElapsedNs'))
         <= int(parent['preparationNs']) + int(parent['elapsedNs']),
         'Windows held observations are outside their actual parent process lifetime')
    edge = held.get('edgeObservation', {}); direction = row.get('direction')
    need(isinstance(edge, dict) and edge.get('schema') == 1 and edge.get('clock') == 'renderer performance.now'
         and edge.get('ok') is True and not edge.get('error') and direction in (-1, 1)
         and edge.get('edgeId') == 'mouse-drag-edge-' + ('right' if direction == 1 else 'left')
         and edge.get('originDesktop') == origin and edge.get('destination') == row['after']['desk']
         and all(P.finite(edge.get(key)) for key in ('armedAtMs', 'hoverAtMs', 'switchedAtMs', 'elapsedMs'))
         and 0 <= edge['armedAtMs'] <= edge['hoverAtMs'] <= edge['switchedAtMs']
         and edge['elapsedMs'] == row.get('hoverMs') == edge['switchedAtMs'] - edge['hoverAtMs']
         and edge['elapsedMs'] >= 600,
         'Windows desktop dwell was not observed from the actual renderer edge hover')


def absent_player(value):
    need(value == {'widgetCount': 0, 'scripts': [], 'styles': [], 'mediaPlayerAPI': 'undefined', 'onMediaPlayerAPI': 'undefined'},
         'removed media player DOM/resources/IPC are still present')


def verify_stationary_removal(value):
    need(value.get('schema') == 1 and value.get('ok') is True and value.get('pollWorld') == 1294 and value.get('polls') == []
         and value.get('audioPlaying') is True and P.finite(value.get('elapsedMs')) and 2200 <= value['elapsedMs'] <= 55000
         and value.get('finishedAt', 0) - value.get('startedAt', 0) == value['elapsedMs'], 'stationary website audio lacks observed player/poll removal')
    absent_player(value.get('initial', {})); absent_player(value.get('final', {}))


def verify_media_removal(value, audio, owners, *, platform=None, pid=None, inputs=None):
    need(value.get('schema') == 2 and value.get('ok') is True and value.get('removed') is True
         and value.get('source') == 'Installed website audio, native tab mute and observed removed-player polling world'
         and value.get('pollWorld') == 1294 and value.get('pollIntervalWasMs') == 1000 and value.get('polls') == [], 'removed-player native contract differs')
    need(audio.get('owned') is True and audio.get('format') == 'PCM16 mono WAV'
         and {row.get('name') for row in audio.get('files', [])} == {'one', 'two'}
         and all(type(row.get('bytes')) is int and row['bytes'] > 44 and re.fullmatch('[a-f0-9]{64}', row.get('sha256', '')) for row in audio['files']), 'real owned audio bytes are missing')
    need(any(row.get('path') == '/audio/one.wav' for row in audio.get('requests', []))
         and any(row.get('path') == '/audio/two.wav' for row in audio.get('requests', [])), 'actual site did not request both audio files')
    for key in ('initial', 'other', 'final'):
        absent_player(value.get(key, {}))
    before, after = value.get('before', {}), value.get('after', {})
    need(before.get('playClickTrusted') is True and after.get('replaceClickTrusted') is True and after.get('error') is None
         and before.get('current') == 'audio-one' and after.get('current') == 'audio-two'
         and len(after.get('audio', [])) == 1 and after['audio'][0].get('id') == 'audio-two'
         and after['audio'][0].get('paused') is False and after['audio'][0].get('currentTime', 0) > 0
         and before.get('timeOrigin') == after.get('timeOrigin'), 'site audio native play/replacement failed')
    observation = value.get('observation', {})
    need(P.finite(observation.get('elapsedMs')) and 2200 <= observation['elapsedMs'] <= 10000
         and observation.get('finishedAt', 0) - observation.get('startedAt', 0) == observation['elapsedMs'], 'removed polling was not observed across two former refresh intervals')
    old = observation.get('before', {}).get('audio', [{}])[0]
    new = observation.get('after', {}).get('audio', [{}])[0]
    need(old.get('id') == new.get('id') == 'audio-two' and old.get('paused') is new.get('paused') is False
         and P.finite(old.get('currentTime')) and P.finite(new.get('currentTime')) and new['currentTime'] > old['currentTime'], 'website audio stopped during no-poll observation')
    samples = value.get('samples', [])
    need(len(samples) >= 2 and all(observation['startedAt'] <= row.get('at', 0) <= observation['finishedAt'] for row in samples), 'no-poll observation samples missing')
    for sample in samples:
        absent_player(sample.get('shell', {}))
        need(sample.get('audio', {}).get('audio', [{}])[0].get('paused') is False, 'website audio paused during player absence')
    need(value.get('mute', {}).get('muted') is True and value.get('unmute', {}).get('muted') is False
         and value['mute'].get('audio', {}).get('audio', [{}])[0].get('paused') is False
         and value['unmute'].get('audio', {}).get('audio', [{}])[0].get('paused') is False,
         'ordinary native tab mute did not toggle while audio continued')
    need(value.get('unrelatedPaused') is True and value.get('originDesktop') != value.get('otherDesktop'), 'audio ownership/desktop scope differs')
    events = value.get('nativeEvents', [])
    need(len(events) >= 2 and all(row.get('type') == 'media-started-playing' and P.finite(row.get('at')) for row in events), 'actual Chromium playback events missing')
    need(len(owners) >= 1 and value.get('nativeBefore', {}).get('tabId') == owners[0]['id']
         and value.get('nativeAfter', {}).get('tabId') == owners[0]['id']
         and value['nativeBefore'].get('webContentsId') == value['nativeAfter'].get('webContentsId') == owners[0]['webContentsId'], 'site audio native owner changed')
    if platform is not None:
        for key, selector in [('playInput', '#media-play'), ('replaceInput', '#media-replace')]:
            row = value.get(key, {}); row = {**row, 'action': row.get('action', 'click')}
            input_receipt(row, platform, pid, selector=selector)
            need(any({**candidate, 'action': candidate.get('action', 'click')} == row for candidate in inputs), 'site audio input absent from native ledger')
        for key in ('mute', 'unmute'):
            row = value[key]['input']; normalized = {**row, 'action': row.get('action', 'click')}
            input_receipt(normalized, platform, pid, selector='.tab-item[data-tab="' + owners[0]['id'] + '"] [data-tab-mute]')
            need(row in inputs, 'tab mute input absent from native ledger')
    return {'removed': True, 'siteAudioContinues': True, 'nativeTabMute': True, 'observedNoPollingMs': observation['elapsedMs']}


def verify_ai_link_routes(rows, *, platform, pid=None, inputs=None, selectors=None):
    need(isinstance(rows, list) and len(rows) >= 1, 'real AI links require classic activation evidence')
    if selectors is not None:
        need([row.get('selector') for row in rows] == selectors, 'every requested AI link route must be observed')
    for row in rows:
        before, state, returned = (row.get(k, {}) for k in ('beforeGrid', 'state', 'returnedGrid'))
        tab = row.get('tab', {})
        need(tab.get('lane') == 'main' and not tab.get('previewOf') and type(tab.get('webContentsId')) is int, 'a new AI link still opens a lower preview')
        need(before.get('view') == 'grid' and not before.get('classicTabId') and isinstance(before.get('slots'), dict) and len(before['slots']) >= 2, 'AI route requires the real existing grid')
        for key in ('tree', 'slots', 'aiId', 'previewId'):
            need(key in before and before[key] == state.get(key) == returned.get(key), 'AI classic activation changed saved grid or owner ' + key)
        need(state.get('view') == 'classic' and state.get('classicTabId') == tab.get('id') and state.get('returnVisible') is True
             and state.get('panes') == [{'id': 'p0', 'view': 'classic'}] and tab.get('url') == row.get('url'), 'AI link does not expose its single ordinary page')
        need(returned.get('view') == 'grid' and not returned.get('classicTabId') and returned.get('returnVisible') is False
             and returned.get('panes') == before.get('panes'), 'AI link grid return did not restore every original grid pane')
        same_page(row.get('chatBefore', {}), row.get('chatAfter', {}))
        click = row.get('input', {})
        need(click.get('source') == NATIVE[platform] and click.get('selector') == row.get('selector')
             and click.get('action') == 'intercepted-link' and click.get('tabId') == row['chatBefore']['id']
             and click.get('webContentsId') == row['chatBefore']['webContentsId']
             and click.get('evidence') == 'Trusted pointerdown on the exact anchor before isolated click interception'
             and P.finite(click.get('at')) and all(P.finite(click.get('point', {}).get(axis)) for axis in ('x', 'y'))
             and any(event.get('type') == 'pointerdown' and event.get('trusted') is True and event.get('isTrusted') is True
                     and event.get('matches') is True and event.get('id') == row.get('selector', '')[1:]
                     and event.get('href') == row.get('url') and event.get('button') == 0 and event.get('pointerType') == 'mouse'
                     and P.finite(event.get('at')) for event in click.get('events', [])), 'AI link was not a trusted native press on its exact intercepted anchor')
        back = row.get('returnInput', {})
        need(back.get('selector') == '#return-to-grid' and back.get('source') == NATIVE[platform]
             and any(e.get('type') == 'click' and e.get('trusted') is True and e.get('matches') is True for e in back.get('events', [])), 'AI classic return was not native')
        if inputs is not None:
            need(click in inputs and back in inputs, 'AI link/return inputs missing from actual ledger')
        if pid is not None:
            need(click.get('pid') == back.get('pid') == pid, 'AI native input belongs to another process')


def screen_capture(read, value, pid):
    filename = value.get('filename', '')
    need(re.fullmatch('mouse-641-(write|read)-[a-z-]+\\.png', filename) and value.get('pid') == pid
         and value.get('source') == 'globalCapture.acquire(display)' and value.get('kind') == 'screen'
         and isinstance(value.get('backend'), str) and value['backend'], 'not an actual641 OS display capture')
    full_name = filename[:-4] + '-display.png'
    raw, full_raw = read(filename), read(full_name)
    need(value.get('displayFilename') == full_name and value.get('sha256') == sha(raw) and value.get('displaySha256') == sha(full_raw), 'native capture bytes changed')
    image, full = P.decode_png(raw, filename), P.decode_png(full_raw, full_name)
    need(value.get('pixelSize') == {key: image[key] for key in ('width', 'height')}
         and value.get('screenPixelSize') == {key: full[key] for key in ('width', 'height')}, 'actual PNG dimensions differ')
    display, bounds = P.rectangle(value.get('display', {}).get('bounds'), 'display'), P.rectangle(value.get('contentBounds'), 'content')
    sx, sy = full['width'] / display['width'], full['height'] / display['height']
    x, y = (bounds['x'] - display['x']) * sx, (bounds['y'] - display['y']) * sy
    crop = {'x': math.floor(x), 'y': math.floor(y), 'width': math.ceil(x + bounds['width'] * sx) - math.floor(x), 'height': math.ceil(y + bounds['height'] * sy) - math.floor(y)}
    need(value.get('cropPixels') == crop and image['width'] == crop['width'] and image['height'] == crop['height']
         and crop['x'] >= 0 and crop['y'] >= 0 and crop['x'] + crop['width'] <= full['width'] and crop['y'] + crop['height'] <= full['height'], 'native window crop geometry differs')
    mapping = {'originX': x - crop['x'], 'originY': y - crop['y'], 'scaleX': sx, 'scaleY': sy}
    need(all(P.finite(value.get('mapping', {}).get(key)) and abs(value['mapping'][key] - expected) < 1e-8 for key, expected in mapping.items()), 'native DPI mapping differs')
    for px in range(0, image['width'], max(1, image['width'] // 37)):
        for py in range(0, image['height'], max(1, image['height'] // 31)):
            need(P.pixel(image, px, py) == P.pixel(full, crop['x'] + px, crop['y'] + py), 'window image is not the recorded full display region')
    return image


def gradient(settings, theme, bounds):
    """CSS sRGB line and preblended endpoints, derived without runtime helpers."""
    def rgb(color):
        need(isinstance(color, str) and re.fullmatch('#[A-F0-9]{6}', color), 'surface color is not canonical RGB')
        return [int(color[index:index + 2], 16) for index in (1, 3, 5)]
    base = [16, 21, 30] if theme == 'dark' else [243, 245, 249]
    alpha = settings['opacity'] / 100
    color = lambda value: '#' + ''.join(format(math.floor(channel * alpha + base[i] * (1 - alpha) + .5), '02X') for i, channel in enumerate(rgb(value)))
    radians = settings['angle'] * math.pi / 180; dx, dy = math.sin(radians), -math.cos(radians)
    length = abs(bounds['width'] * dx) + abs(bounds['height'] * dy)
    cx, cy = bounds['x'] + bounds['width'] / 2, bounds['y'] + bounds['height'] / 2
    return {'x0': cx - dx * length / 2, 'y0': cy - dy * length / 2, 'x1': cx + dx * length / 2, 'y1': cy + dy * length / 2,
            'start': color(settings['color']), 'end': color(settings['endColor'])}


def gradient_pixel(value, x, y):
    dx, dy = value['x1'] - value['x0'], value['y1'] - value['y0']
    fraction = min(1, max(0, ((x - value['x0']) * dx + (y - value['y0']) * dy) / (dx * dx + dy * dy)))
    a, b = ([int(value[key][index:index + 2], 16) for index in (1, 3, 5)] for key in ('start', 'end'))
    return [math.floor(start + (end - start) * fraction + .5) for start, end in zip(a, b)]


def verify_corners(rows, theme, appearance, captures):
    need([row.get('stage') for row in rows] == ['before', 'resized'], 'native custom corners need a fresh window resize')
    need(rows[0].get('windowBounds', {}).get('width') - 40 == rows[1].get('windowBounds', {}).get('width'), 'native resize did not change actual window width')
    for row in rows:
        shell = row.get('shell', {})
        need(row.get('theme') == shell.get('theme') == theme and shell.get('appearance') == appearance
             and shell.get('settingsOpen') is shell.get('libraryOpen') is False and 'gradient' in shell.get('gradient', ''), 'native corner scene has a different theme or covering sidebar')
        workspace = P.rectangle(shell.get('workspace'), 'gradient workspace')
        expected = gradient(appearance['surfaces'][theme]['workspace'], theme, workspace)
        need(row.get('capture') in captures, 'custom corner native screenshot missing')
        receipt, image = captures[row['capture']]; mapping = receipt['mapping']
        need(receipt.get('contentBounds') == row.get('contentBounds'), 'custom corner window moved during capture')
        native, masks, probes = row.get('native', []), row.get('masks', []), row.get('probes', [])
        need(len(native) >= 2 and len(masks) == len(native) and len(probes) == len(native) * 2, 'both native bottom corners of every visible pane are required')
        for page, mask in zip(native, masks):
            bounds = P.rectangle(page.get('bounds'), 'native gradient pane')
            view = P.rectangle(page.get('viewBounds'), 'actual native child view')
            parent = None if page.get('parentBounds') is None else P.rectangle(page['parentBounds'], 'actual native clip parent')
            actual = {**view, 'x': view['x'] + (parent['x'] if parent else 0), 'y': view['y'] + (parent['y'] if parent else 0)}
            need(page.get('visible') is page.get('attached') is page.get('parentVisible') is True
                 and page.get('actualBounds') == actual == bounds and (parent is None or parent == bounds)
                 and page.get('panel', {}).get('roundBottom') == 12
                 and all(mask.get(k) == bounds[k] for k in ('x', 'y', 'width', 'height')), 'native corner mask does not cover the actual visible page bounds')
            for submitted in (mask.get('gradient', {}), page['panel'].get('roundGradient', {})):
                need(set(submitted) == set(expected) and all(P.finite(submitted.get(key)) and abs(submitted[key] - expected[key]) < 1e-6 for key in ('x0', 'y0', 'x1', 'y1'))
                     and all(submitted.get(key) == expected[key] for key in ('start', 'end')), 'native gradient submission differs from independently computed workspace geometry')
            own = [p for p in probes if p.get('tabId') == page.get('id')]
            need([p.get('side') for p in own] == ['left', 'right'] and all(p.get('webContentsId') == page.get('webContentsId') for p in own), 'native lower corner owner/side differs')
            for probe in own:
                point = {'x': bounds['x'] + (1 if probe['side'] == 'left' else bounds['width'] - 1), 'y': bounds['y'] + bounds['height'] - 1}
                need(probe.get('point') == point, 'corner probe does not sample the outer rounded cutout')
                x, y = (math.floor(mapping['origin' + axis] + point[coordinate] * mapping['scale' + axis]) for axis, coordinate in [('X', 'x'), ('Y', 'y')])
                need(0 <= x < image['width'] and 0 <= y < image['height'], 'corner pixel is outside the OS capture')
                actual = P.pixel(image, x, y)
                expected_rgb = gradient_pixel(expected, (x + .5 - mapping['originX']) / mapping['scaleX'], (y + .5 - mapping['originY']) / mapping['scaleY'])
                need(actual[3] == 255 and all(abs(actual[i] - expected_rgb[i]) <= 3 for i in range(3)), 'actual native lower corner pixel is stale or differs from its workspace gradient')


def verify_layout(value, platform, pid, inputs):
    #The new installed flow supplies concrete ordered insertion, blank page
    #native drags, a still-held desktop-edge carry and tiny-header samples.
    need(value.get('schema') == 1 and value.get('ok') is True, '641 workspace layout flow missing')
    empty = value.get('empty', {})
    input_receipt(empty.get('input', {}), platform, pid, inputs, selector='#footer-left [data-action="split-x"]')
    home = empty.get('home', {})
    need(empty.get('paneId') and not empty.get('after', {}).get('slots', {}).get(empty['paneId'])
         and home.get('visible') is home.get('search') is home.get('favorites') is True
         and any(row.get('visible') is True for row in home.get('tabs', [])), 'empty pane lost home search/favorites or open tabs')
    insertion = value.get('insertion', {})
    input_receipt(insertion.get('input', {}), platform, pid, inputs, action='drag')
    affordance = insertion.get('affordance', {})
    need(insertion['input']['selector'] == '.tab-item[data-tab="' + insertion.get('insertedId', '') + '"] .tab-title'
         and affordance.get('visible') is True and affordance.get('axis') == 'x' and affordance.get('edge') == 'left'
         and affordance.get('target') and affordance.get('neighbor') and affordance['target'] != affordance['neighbor']
         and affordance.get('svg') is True and affordance.get('text', '').strip(), 'pane insertion did not show a visible split-gap affordance')
    before, after = insertion.get('beforeOrder', []), insertion.get('afterOrder', [])
    need(len(before) == 2 and after == [before[0], insertion.get('insertedId'), before[1]]
         and insertion.get('insertedId') not in before, 'new pane was not inserted between the existing panes')
    need(insertion.get('whileHeld', {}).get('active') is True and insertion['whileHeld'].get('ghost') is True
         and insertion['whileHeld'].get('bodyDragging') is True, 'gap affordance was not observed during the native drag')
    choice = value.get('chooser', {})
    input_receipt(choice.get('input', {}), platform, pid, inputs)
    need(choice.get('paneId') == empty['paneId'] and choice['input']['selector'] == '.pane[data-pane="' + empty['paneId'] + '"] [data-home-tab="' + choice.get('selectedId', '') + '"]'
         and choice.get('after', {}).get('slots', {}).get(empty['paneId']) == choice.get('selectedId'), 'open tab chooser did not fill the empty pane')
    same_page(value.get('fixture', {}).get('third', {}), choice.get('identity', {}))
    for kind in ('blankDrag', 'edgeCarry'):
        row = value.get(kind, {})
        input_receipt(row.get('input', {}), platform, pid, inputs, action='drag')
        if platform == 'win32':
            windows_html_drag(row['input'], 'edge' if kind == 'edgeCarry' else 'blank', pid)
            need(row['input'].get('tabId') == row.get('before', {}).get('id'), 'Windows native HTML drag source differs from its owned live page')
        need(row['input'].get('selector') == '#blank-drag' and row.get('before', {}).get('id') == row.get('after', {}).get('id'), 'blank website drag changed its page identity')
        same_page(row['before'], row['after'], desktop=kind != 'edgeCarry')
        if kind == 'edgeCarry':
            need(row['before'].get('desk') != row['after'].get('desk') and row.get('whileHeld', {}).get('mouseDown') is True
                 and row['whileHeld'].get('desktopId') == row['after']['desk'] and row.get('hoverMs', 0) >= 600, 'desktop did not switch while the same native drag stayed held')
            if platform == 'win32': windows_held_drag(row, pid)
        else:
            need(row.get('beforePane') != row.get('afterPane'), 'blank drag did not move a pane')
    headers = value.get('headers', [])
    need([(row.get('theme'), row.get('stage')) for row in headers] == [(theme, stage) for theme in ('light', 'dark') for stage in ('tiny', 'resized')], 'tiny pane headers need both themes before/after native resize')
    for row in headers:
        need(len(row.get('inputs', [])) == 2, 'both tiny width and height need actual divider resize inputs')
        for receipt in row['inputs']:
            input_receipt(receipt, platform, pid, inputs, action='drag')
            need(receipt['selector'].startswith('.divider[data-path='), 'tiny header was not resized using its real divider')
        pane = row.get('pane', {}); b = P.rectangle(pane.get('bounds'), 'tiny pane'); h = P.rectangle(pane.get('header', {}).get('bounds'), 'header')
        need(pane['header'].get('visible') is True and pane['header'].get('display') != 'none' and pane['header'].get('opacity') == 1
             and pane['header'].get('visibility') == 'visible' and h['height'] >= 28 and h['width'] > 0
             and h['x'] >= b['x'] - 1 and h['y'] >= b['y'] - 1 and h['x'] + h['width'] <= b['x'] + b['width'] + 1
             and h['y'] + h['height'] <= b['y'] + b['height'] + 1, 'small pane header is clipped or hidden')
        if row['stage'] == 'tiny':
            need(b['width'] <= 240 and b['height'] <= 150, 'header fixture did not reach a genuinely small pane')


def verify(read, expected_platform=None, expected_arch=None):
    artifacts = {}
    def bound(name):
        need(isinstance(name, str) and re.fullmatch(r'mouse-(?:637|641)-[a-z0-9.-]+', name) and '..' not in name, 'unsafe641 artifact filename')
        raw = read(name); need(isinstance(raw, bytes) and 0 < len(raw) <= 64 * 1024**2, 'empty or oversized641 artifact')
        artifacts[name] = {'file': name, 'sha256': sha(raw), 'bytes': len(raw)}
        return raw
    facts, written, processes = (json.loads(bound(name)) for name in ('mouse-641-workspace.json', 'mouse-641-workspace-write.json', 'mouse-641-workspace-processes.json'))
    platform, arch, pid = facts.get('platform'), facts.get('arch'), facts.get('pid')
    need((platform, arch) in (('darwin', 'arm64'), ('win32', 'x64'), ('linux', 'x64')) and (expected_platform is None or platform == expected_platform) and (expected_arch is None or arch == expected_arch), '641 native platform differs')
    need(facts.get('schema') == 1 and facts.get('version') == VERSION and facts.get('source') == SOURCE and type(pid) is int and pid > 0
         and all(facts.get(k) is True for k in ('ok', 'restored', 'writeComplete', 'packaged', 'profileIsolated')) and facts.get('awaitingRestart') is False
         and facts.get('physicalUserDeviceVerified') is False and not facts.get('error') and not facts.get('cleanupError'), 'not a successful isolated installed641 process')
    need(written.get('pid') == pid and written.get('write') == facts.get('write') and written.get('writeComplete') is True and written.get('awaitingRestart') is True
         and written.get('ok') is False and written.get('restored') is False, 'restart rewrote the original641 evidence')
    need(processes.get('version') == VERSION and processes.get('platform') == platform and processes.get('arch') == arch
         and processes.get('profile') == facts.get('profile') and re.fullmatch('[a-f0-9]{64}', processes.get('executableSha256', ''))
         and processes.get('reportSha256') == sha(bound('mouse-641-workspace.json')), '641 installed executable/profile/report binding differs')
    seed = json.loads(bound('mouse-641-adblock-cache.json'))
    need(seed.get('synthetic') is True and seed.get('version') == VERSION and seed.get('profile') == facts['profile']
         and processes.get('cacheSeedSha256') == sha(bound('mouse-641-adblock-cache.json')), '641 offline list provenance differs')
    cache = []
    for source in ('easylist', 'ruadlist'):
        name = 'mouse-641-adblock-cache-' + source + '.json'; raw = bound(name); row = json.loads(raw)
        need(row.get('source') == source and row.get('synthetic') is True and row.get('url') == 'https://easylist-downloads.adblockplus.org/' + source + '.txt'
             and sha(row.get('text', '').encode()) == row.get('sha256') and '/mouse-adblock-fixture/advertising-script.js' in row['text'].splitlines(), '641 synthetic filters do not contain the bound request rule')
        cache.append({'source': source, 'sha256': sha(raw), 'textSha256': row['sha256']})
    captures = {}
    for phase, key, budget, process_budget, marker in [('write', 'write', 240000, 270000, 'MOUSE_641_WORKSPACE_WRITE_PASS'), ('read', 'restart', 90000, 120000, 'MOUSE_641_WORKSPACE_NATIVE_PASS')]:
        part, receipt = facts.get(key, {}), processes.get(phase, {})
        phase_pid = part.get('pid'); report = 'mouse-641-workspace-write.json' if phase == 'write' else 'mouse-641-workspace.json'; log = 'mouse-641-workspace-' + phase + '.log'
        need(type(phase_pid) is int and phase_pid > 0 and phase_pid == receipt.get('pid') and (phase_pid == pid if phase == 'write' else phase_pid != pid)
             and part.get('budgetMs') == budget and P.finite(part.get('elapsedMs')) and 0 < part['elapsedMs'] <= budget
             and receipt.get('exitCode') == 0 and P.finite(receipt.get('elapsedMs')) and 0 < receipt['elapsedMs'] <= process_budget,
             'distinct641 native process/budget/exit receipt missing')
        need(receipt.get('report') == report and receipt.get('reportSha256') == sha(bound(report))
             and receipt.get('log') == log and receipt.get('logSha256') == sha(bound(log)) and receipt.get('requiredMarkers') == [marker], 'actual641 process/log/report hashes differ')
        lines = bound(log).decode('utf-8', 'strict').splitlines()
        need(marker in lines and any(line.startswith(f'MOUSE_641_PROCESS_RETURN pid={phase_pid} code=0 ') for line in lines)
             and not any('MOUSE_641_WORKSPACE_FAIL' in line or 'MOUSE_NATIVE_PROCESS_TIMEOUT' in line for line in lines), 'native641 marker/actual successful exit absent')
        need(part.get('cache') == {'seedSha256': sha(bound('mouse-641-adblock-cache.json')), 'records': cache}, 'installed641 process read another cache')
        inputs = part.get('inputs', [])
        need(isinstance(inputs, list) and len(inputs) <= 160, 'dedicated641 input ledger is unbounded')
        for row in inputs:
            input_receipt(row, platform, phase_pid, action=row.get('action'))
        for value in part.get('captures', []):
            need(value.get('filename') not in captures, 'duplicate641 capture')
            captures[value['filename']] = (value, screen_capture(bound, value, phase_pid))
        http_name = 'mouse-641-http-' + phase + '.json'; raw = bound(http_name); http = json.loads(raw)
        need(part.get('http') == {'file': http_name, 'sha256': sha(raw)} and http.get('version') == VERSION and http.get('synthetic') is True
             and http.get('pid') == phase_pid and http.get('origin') == part.get('origin'), 'actual641 HTTP ledger belongs to another process')
    write, restart = facts['write'], facts['restart']; inputs = write['inputs']
    need(len(inputs) >= 35, 'required native641 control sequence was not executed')
    rows = write.get('classic', {}).get('cases', [])
    need([row.get('kind') for row in rows] == ['link', 'blank-link', 'window-open', 'new-tab', 'top-tab'], 'ordinary link, new-window link, new tab and top tab must each activate classic view')
    initial = write.get('identitiesBefore', [])
    need(len(initial) == 2 and len({row.get('webContentsId') for row in initial}) == 2, 'two original live grid pages are required')
    for row in rows:
        same_grid(row['before'], row['state']); same_grid(row['before'], row['returned']); classic(row['state'], row.get('active'))
        input_receipt(row['input'], platform, pid, inputs); input_receipt(row['returnInput'], platform, pid, inputs, selector='#return-to-grid')
        need(row['returned'].get('mode') == 'grid' and not row['returned'].get('classicTabId') and row.get('capture') in captures, '641 classic return/capture missing')
        need(len(row.get('identities', [])) == len(initial), 'original grid pages disappeared')
        for old, new in zip(initial, row['identities']):
            same_page(old, new)
        if row['kind'] == 'new-tab':
            home = row['state']['panes'][0].get('home', {}); need(home.get('visible') is home.get('search') is home.get('favorites') is True, 'classic new tab lost its homepage')
        else:
            need(len(row.get('native', [])) == 1 and row['native'][0].get('id') == row['active'] and row['native'][0].get('attached') is True, 'classic activation left a grid of native pages visible')
            if row['kind'] in ('link', 'blank-link', 'window-open'):
                need(row['native'][0].get('url') == write['origin'] + '/page/' + {'link': '3', 'blank-link': '2', 'window-open': '5'}[row['kind']] + '/', 'real native link opened another URL')
    verify_layout(write.get('layout', {}), platform, pid, inputs)
    exclusions = write.get('exclusions', {}); http = json.loads(bound('mouse-641-http-write.json'))
    input_receipt(exclusions.get('enableInput', {}), platform, pid, inputs, selector='[data-setting="blockAds"]')
    cases = exclusions.get('cases', [])
    need([(row.get('name'), row.get('blocked')) for row in cases] == [('blocked', True), ('context-excluded', False), ('context-enabled', True), ('host-isolation', True), ('settings-excluded', False)], 'site exceptions did not exercise both blocking directions and settings')
    for row in cases:
        token, dom = row.get('token'), row.get('dom', {}); blocked = row['blocked']; expected = {'page': 1, 'allowed': 1, 'advertising': 0 if blocked else 1}
        need(row.get('url') == write['origin'] + '/mouse-adblock-fixture/page?token=' + token and dom.get('url') == row['url'] and dom.get('token') == token
             and dom.get('attempted') == {'allowed': 1, 'advertising': 1} and dom.get('executed') == {'allowed': 1, 'advertising': 0 if blocked else 1}
             and dom.get('settled') == {'allowed': 'load', 'advertising': 'error' if blocked else 'load'} and row.get('counts') == expected and row.get('capture') in captures,
             'site exception was not checked against an actual page request/script result')
        paths = {'page': '/mouse-adblock-fixture/page', 'allowed': '/mouse-adblock-fixture/allowed-script.js', 'advertising': '/mouse-adblock-fixture/advertising-script.js'}
        actual = {key: sum(hit.get('token') == token and hit.get('path') == path for hit in http['hits']) for key, path in paths.items()}
        need(actual == expected and row.get('native', {}).get('visible') is True and row['native'].get('attached') is True, 'server-observed native request count differs')
    for key, checked in [('contextOff', True), ('contextOn', False)]:
        row = exclusions.get(key, {}); need(row.get('source') == NATIVE[platform] and row.get('pid') == pid and row.get('id') == 'mouse-context-adblock'
            and row.get('item', {}).get('type') == 'checkbox' and row['item'].get('checked') is checked and row['item'].get('enabled') is True
            and row['item'] in row.get('items', []) and P.finite(row.get('shownAt')) and P.finite(row.get('closedAt')) and row['closedAt'] >= row['shownAt']
            and any(e.get('type') == 'contextmenu' and e.get('trusted') is True and e.get('matches') is True for e in row.get('events', [])), 'site context checkbox was not a real native menu')
        need(row.get('keys', [])[0].get('key') == 'HOME' and row['keys'][-1].get('key') == 'ENTER', 'native context checkbox was not keyboard-selected')
        for event in row['keys']:
            key_receipt(event, platform, pid)
    for key, selector in [('addURL', '#settings-adblock-exception-add'), ('openChooser', '#settings-adblock-exception-tab'), ('addTab', '#settings-adblock-exception-add-tab')]:
        input_receipt(exclusions.get(key, {}), platform, pid, inputs, selector=selector)
    typed = exclusions.get('url', {}); need(typed.get('value') == 'https://LOCALHOST:443/owned?path=one'
         and typed.get('source') == 'native focus, webContents.sendInputEvent and insertText'
         and any(event.get('type') == 'input' and event.get('trusted') is True for event in typed.get('events', [])), 'settings URL was not entered through its actual control')
    input_receipt(typed.get('input', {}), platform, pid, inputs, selector='#settings-adblock-exception-url')
    input_receipt(exclusions.get('chooseTab', {}), platform, pid, inputs)
    need(exclusions['chooseTab']['selector'] == '#choice-dialog [data-value="' + cases[-1]['native']['tabId'] + '"]'
         and exclusions.get('saved', {}).get('hosts') == ['127.0.0.1', 'localhost'], 'settings open-tab chooser or host normalization differs')
    surfaces = write.get('surfaces', [])
    need([row.get('theme') for row in surfaces] == ['light', 'dark'], 'independent surface settings require both themes')
    for row in surfaces:
        theme = row['theme']; before, after = row.get('before', {}), row.get('after', {})
        need(after.get('theme') == theme and after.get('selectedPage') == 'surfaces' and after.get('model') == after.get('stored') and row.get('capture') in captures, 'theme surfaces were not saved from visible settings')
        settings = after['model'].get('surfaces', {}).get(theme, {})
        colors = {'light': {'top': ['#E9D8FF', '#CCD9FF'], 'bottom': ['#CFEBDC', '#D7E8CE'], 'workspace': ['#F3E6CA', '#F2DCC8']}, 'dark': {'top': ['#51376B', '#263C61'], 'bottom': ['#1E5148', '#243C42'], 'workspace': ['#594B30', '#403C3D']}}[theme]
        for name in ('top', 'bottom', 'workspace'):
            expected_opacity = 100 if name == 'workspace' else 98 if theme == 'light' else 96
            need(settings.get(name, {}).get('mode') == ('solid' if name == 'bottom' else 'gradient') and settings[name].get('color') == colors[name][0]
                 and settings[name].get('endColor') == colors[name][1] and settings[name].get('opacity') == expected_opacity, 'native surface controls produced different independent values')
        if theme == 'dark':
            need(after['model']['surfaces'].get('light') == surfaces[0]['after']['model']['surfaces']['light'], 'editing dark surfaces overwrote light settings')
        verify_corners(row.get('corners', []), theme, after['model'], captures)
        for action in row.get('inputs', []):
            if 'range' in action:
                input_receipt(action['input'], platform, pid, inputs, selector=action['range'])
                for event in action['keys']: key_receipt(event, platform, pid)
            else: input_receipt(action, platform, pid, inputs)
    library = write.get('library', [])
    need([(row.get('theme'), row.get('kind')) for row in library] == [(theme, kind) for theme in ('light', 'dark') for kind in ('bookmarks', 'history', 'downloads')], 'library/history/downloads need both theme routes')
    for row in library:
        input_receipt(row['input'], platform, pid, inputs); state = row.get('state', {})
        need(state.get('open') is True and state.get('theme') == row['theme'] and state.get('kind') == row['kind'] and state.get('title', '').strip()
             and row.get('capture') in captures and len(state.get('tabs', [])) >= 5 and all(tab.get('viewBox') == '0 0 24 24' and tab.get('paths', 0) > 0 and tab.get('tone') for tab in state['tabs']), 'native library category lost its visible title/icons')
        need(all(state.get('surface', {}).get(key) == row.get('settingsSurface', {}).get(key) for key in ('backgroundColor', 'backgroundImage', 'backdropFilter', 'borderColor')), 'library material does not match Settings')
    persisted = write.get('persisted', {})
    need(persisted.get('appearance') == surfaces[-1]['after']['model'] and persisted.get('exceptions', {}).get('hosts') == ['127.0.0.1', 'localhost']
         and restart.get('surfaces') == {'model': persisted['appearance'], 'stored': persisted['appearance']}
         and restart.get('exceptions', {}).get('hosts') == persisted['exceptions']['hosts'] and restart.get('capture') in captures, 'actual641 restart lost theme independence or site exclusions')
    network = restart.get('network', {}); token = network.get('token', ''); http_read = json.loads(bound('mouse-641-http-read.json'))
    need(network.get('url') == restart['origin'] + '/mouse-adblock-fixture/page?token=' + token and network.get('dom', {}).get('token') == token
         and network['dom'].get('executed') == {'allowed': 1, 'advertising': 1} and network['dom'].get('settled') == {'allowed': 'load', 'advertising': 'load'}
         and network.get('counts') == {'page': 1, 'allowed': 1, 'advertising': 1} and network.get('native', {}).get('visible') is True
         and network['native'].get('attached') is True, 'restarted site exclusion did not actually permit its native page requests')
    for suffix in ('page', 'allowed-script.js', 'advertising-script.js'):
        need(sum(hit.get('token') == token and hit.get('path') == '/mouse-adblock-fixture/' + suffix for hit in http_read['hits']) == 1, 'restarted request ledger disagrees with excluded page')
    media_facts = json.loads(bound('mouse-637-features.json')); media_write = json.loads(bound('mouse-637-features-write.json'))
    need(media_facts.get('version') == VERSION and media_facts.get('ok') is True and media_facts.get('packaged') is True and media_facts.get('restored') is True
         and media_facts.get('media') == media_write.get('media'), 'separate media removal evidence is not an installed retained process')
    media = verify_media_removal(media_facts.get('media', {}), media_facts.get('audio', {}), media_facts.get('appearance', {}).get('pages', {}).get('before', []), platform=platform, pid=media_facts.get('pid'), inputs=media_facts.get('nativeInputs', []))
    return {'schema': 1, 'version': VERSION, 'ok': True, 'platform': platform, 'arch': arch,
            'processes': {'writePid': pid, 'readPid': restart['pid']}, 'nativeCaptures': list(captures),
            'classicRoutes': ['link', 'blank-link', 'window-open', 'new-tab', 'top-tab'], 'siteExceptions': True,
            'independentThemes': True, 'libraryGlass': True, 'mediaPlayerRemoved': media,
            'artifacts': list(artifacts.values())}


def run(directory, *, platform=None, arch=None):
    directory = Path(directory)
    result = verify(lambda name: (directory / name).read_bytes(), platform, arch)
    (directory / 'mouse-641-workspace-acceptance.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--platform', choices=['darwin', 'win32', 'linux'])
    parser.add_argument('--arch', choices=['arm64', 'x64'])
    args = parser.parse_args()
    run(args.directory, platform=args.platform, arch=args.arch)
    print('MOUSE_641_INDEPENDENT_WORKSPACE_ACCEPTANCE_PASS')
