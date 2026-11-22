#!/usr/bin/env python3
"""Read-only completeness check for one nonpublishing performance diagnosis.

This is not a release acceptance reader. It checks the original native workload
receipts and a bounded, owned CDP trace; it does not infer a performance cause or
claim coverage of all guest renderers. Renderer, main, epoch and trace clocks are
kept separate. A zero bufferUsage.eventCount is valid in pinned Chromium152.
"""
import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import runpy
import subprocess

SOURCE = '0021084ccb9537e657d21e6f0c8e812dee6b461f'
VERSION = '6.0.37'
PREFIX = 'mouse-637-performance-trace-'
FLAG = '--mouse-631-smoke'
ORIGINAL_SHA = 'd3b4797b42d63c364462dcb01c6bad4316c91d5b3cbb64065f12b571a5655ebf'
ORIGINAL_BLOB = 'ec3d20f157e2ae74e86bf665344f63c326a8eee5'
PARENT_SHA = '2c35d8c9d77ea761712e5fc54a8b22b1e18cdf6b3d048cd9c6b0e5dc316cc208'
PARENT_BLOB = 'aef2796e206bbbc5d13754b4744ca81ceab81e06'
MAIN_SHA = 'f3c9ba7794cb5c659c75fdc981faeda6b45851ceb0e70b61291128a04387914f'
VERIFIER_SHA = '2f662f0de5d81a8013f77ef9cf24262eb50e96df2cfdd59eeb02691fddb22dc7'
NATIVE_READER_SHA = '5d1d700f1d8ef19663d2e7fe15c21ee40967aee12f598910ca6192eddaeeb7a8'
SNAPSHOT_SHA = '767217ed097c52703f8f8015fa1bf26e43c727447e05c74cfcbc43aaafcc255d'
CONNECTOR_SHA = '41462a9634ea481ad73883eb3039cc3f38af7b37c913272cf455bb73fce2c49b'
LISTENER_SHA = '850ac3505d149319227283dbfa7b5597d7e547de2e0c5c98c8e2c45cdd972b56'
LISTENER_READER_SHA = 'cc5858537f77b21d4e5205007ba9c062c0490e6583dfba8151169c7da9b6a2d4'
FUNCTION_SHAS = {'sample_native_exit': 'a368760a8189b1f13b8fd8bec2e4c020501f37153917dfd7ec13e85b8b81f0a1',
                'run_logged': 'aa0e5b101922ca42b0374635b07569328f35cb0add5921e24da5b7e6f73fc052'}
CATEGORIES = ['toplevel', 'devtools.timeline', 'blink.user_timing', 'mojom', 'mojom.flow']
LIMITS = {'eventBufferKiB': 16384, 'maxOutputBytes': 67108864, 'readBytes': 262144,
          'maxReads': 257, 'activeMs': 20000, 'setupMs': 10000, 'drainMs': 15000,
          'apiRows': 300, 'bufferEvents': 32}
SCOPE = 'Diagnostic shell/main and available GPU trace; no release acceptance or promised coverage of every guest renderer'
MARKERS = ['MOUSE_631_TASK_ONLY_NATIVE_PASS', 'MOUSE_631_FIFTY_TABS_FIVE_DESKTOPS_NATIVE_PASS',
           'MOUSE_631_INSTALLED_TASK_STRESS_PASS', 'MOUSE_632_STATIONARY_MEDIA_PASS']
RUNTIME = {'electron': '44.5.0', 'chrome': '152.0.7977.130', 'node': '24.21.0', 'v8': '15.2.124.28-electron.0'}
# Pinned Perfetto9c7ce420 DynamicStringWriter::AppendDouble uses "%.16g".
# The marker's args.data.startTime is the same Blink double returned through
# Runtime.evaluate; its decimal serialization can round the last of16 digits.
MARK_SERIALIZATION_DIGITS = 16
COMPONENTS = {
    'Contents/MacOS/Mouse Browser': {'size': 52688, 'sha256': '10265cedd820b04e308d318e236206f963e834329653bcba73b4db85c35ced59'},
    'Contents/Resources/app.asar': {'size': 9731873, 'sha256': '62b5472c62e475b28935b110330a602311fa8227b79666f375269fcdc8eb260e'},
    'Contents/Resources/app.asar.unpacked/mouse-native-menu.node': {'size': 117120, 'sha256': 'af86174cc2d157171e34c0c8dc65ce5c34881cd5fdc459b6f8274dc9749c828d'},
    'Contents/Resources/app.asar.unpacked/mouse-screen-capture.node': {'size': 118912, 'sha256': '808a5852febd89a3d8ecc15cff29805da383ced1f01e6d6a207a2fea0ae95f88'},
}
TOOL_FILES = ['tools/mouse637-performance-trace.py', 'tools/mouse637-performance-trace.cjs',
              'tools/mouse637-performance-trace-evidence.py',
              'tools/fixtures/mouse637-performance-002-native.cjs',
              'tools/fixtures/mouse637-performance-002-stress.cjs',
              'tools/mouse637-feature-readiness.py', 'tools/mouse637-feature-readiness.cjs',
              'tools/mouse637-guest-input-observer.cjs', 'tools/mouse637-guest-input-observer-evidence.py',
              'staging/mouse/6.0.37-arm64/pin.json']


def need(value, message):
    if not value:
        raise ValueError('Mouse637 diagnostic trace: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def integer(value, minimum=0, maximum=2**53 - 1):
    return type(value) is int and minimum <= value <= maximum


def text(value, maximum=4096, empty=False):
    return isinstance(value, str) and len(value) <= maximum and (empty or bool(value)) and '\0' not in value


def same(actual, expected, label):
    need(isinstance(actual, dict) and all(k in actual and type(actual[k]) is type(v) and actual[k] == v
                                        for k, v in expected.items()), label + ' differs')


def exact(actual, expected, label):
    same(actual, expected, label)
    need(set(actual) == set(expected), label + ' field inventory differs')


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Nonfinite JSON constant: ' + value)
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid)


def git_tools(tools_root, publisher_sha):
    root = tools_root.resolve().parent
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.PIPE)
    need(git('rev-parse', 'HEAD').decode().strip() == publisher_sha, 'checkout is not the explicit publisher commit')
    result = {}
    for name in TOOL_FILES:
        file = root / name
        need(file.is_file() and not file.is_symlink() and file.resolve().is_relative_to(root), 'committed tool missing: ' + name)
        data = file.read_bytes()
        need(data == git('show', publisher_sha + ':' + name), 'committed tool bytes differ: ' + name)
        result[name] = sha(data)
    for name, digest in [('mouse637-feature-readiness.py', SNAPSHOT_SHA),
                         ('mouse637-feature-readiness.cjs', CONNECTOR_SHA),
                         ('mouse637-guest-input-observer.cjs', LISTENER_SHA),
                         ('mouse637-guest-input-observer-evidence.py', LISTENER_READER_SHA)]:
        need(result['tools/' + name] == digest, 'unchanged shared dependency differs: ' + name)
    return result


def runtime_identity(value, config, early=False):
    same(value, {'platform': 'darwin', 'arch': 'arm64', 'CI': 'true',
                 'profile': config['profile'], 'nonce': config['nonce']}, 'runtime environment')
    expected = {'pid': config['pid'], 'execPath': config['executable'],
                'argv': [config['executable'], '--inspect-brk=127.0.0.1:' + str(config['port']), FLAG]}
    for key, kind in [('pid', 'number'), ('execPath', 'string'), ('argv', 'object')]:
        if early:
            available = value.get('availability', {}).get(key)
            if available == 'undefined':
                need(key in value and value[key] is None, 'early unavailable runtime field must be null: ' + key)
                continue
            need(available == kind, 'early runtime type differs: ' + key)
        need(type(value.get(key)) is type(expected[key]) and value[key] == expected[key], 'runtime identity differs: ' + key)


def clock_order(values, label, maximum=None):
    need(all(number(v) and v >= 0 for v in values) and values == sorted(values), label + ' clock order invalid')
    if maximum is not None:
        need(values[-1] - values[0] <= maximum, label + ' deadline exceeded')


def marker_expression(name):
    return ('(()=>{const name=' + json.dumps(name) + ';performance.mark(name);const entries=performance.getEntriesByName(name,"mark");'
            'if(entries.length!==1)throw Error("Diagnostic mark collision");return{name,startTime:entries[0].startTime,'
            'timeOrigin:performance.timeOrigin,now:performance.now()};})()')


def marker_precision(value):
    # Half the final decimal unit, plus one binary ULP for parsing/arithmetic.
    # This is a numeric identity check, not a native timing allowance.
    decimal = 0 if value == 0 else .5 * 10.0 ** (math.floor(math.log10(abs(value))) - MARK_SERIALIZATION_DIGITS + 1)
    return decimal + math.ulp(value)


def trace_identity(session, trace_raw, stress, expected):
    same(session, {'schema': 1, 'kind': 'mouse637-nonpublishing-performance-trace', 'diagnosticOnly': True,
                  'releaseAcceptance': False, **expected, 'ok': True, 'collected': True,
                  'originalStressBudgetMs': 200000, 'clock': 'main.performance.now', 'coverage': SCOPE,
                  'listenerAttached': True, 'listenerRemoved': True, 'startSubmitted': True,
                  'startAcknowledged': True, 'startPendingAtDisposal': False, 'activeCapExceeded': False,
                  'outputCapExceeded': False, 'streamClosed': True, 'streamEOF': True,
                  'marksCleared': True, 'loopCompleted': True, 'endReason': 'loop-complete'}, 'trace session')
    need(session.get('errors') == [] and not session.get('detached') and not session.get('lateStartAcknowledgment') and
         not session.get('startRejected') and not session.get('startWaitTimedOut'),
         'incomplete/late/failed trace collection')
    exact(session.get('limits'), LIMITS, 'diagnostic limits')
    need(session.get('categories') == CATEGORIES, 'trace category allowlist differs')
    same(session.get('versions'), RUNTIME, 'actual embedded runtime')
    pid, shell = session.get('mainPid'), session.get('shellPid')
    need(integer(pid, 1) and pid == expected['pid'] and integer(shell, 1) and shell != pid and
         integer(session.get('shellWebContentsId'), 1), 'actual main/shell owner identity missing')
    need(number(session.get('fixtureStartedAt')) and number(session.get('fixtureDeadline')) and
         session['fixtureDeadline'] == session['fixtureStartedAt'] + 200000, 'original stress deadline changed')
    browser = session.get('browserVersion')
    same(browser, {'protocolVersion': '1.3', 'product': 'Chrome/152.0.7977.130'}, 'actual Browser.getVersion')
    need(browser.get('jsVersion') in ('15.2.124.28', RUNTIME['v8'])
         and text(browser.get('revision'), 512) and text(browser.get('userAgent'), 2048)
         and len(json.dumps(browser).encode()) <= 4096, 'actual browser build identity invalid')
    supported = session.get('supported', {})
    available = supported.get('categories')
    need(isinstance(available, list) and 1 <= len(available) <= 4096 and
         all(text(v, 256) for v in available) and all(v in available for v in CATEGORIES)
         and len(json.dumps(supported).encode()) <= 1048576, 'required actual runtime categories missing')
    start_params = {'transferMode': 'ReturnAsStream', 'streamFormat': 'json', 'streamCompression': 'none',
                    'bufferUsageReportingInterval': 1000,
                    'traceConfig': {'recordMode': 'recordUntilFull', 'traceBufferSizeInKb': 16384,
                                    'enableSampling': False, 'enableSystrace': False, 'includedCategories': CATEGORIES}}
    need(session.get('startParams') == start_params, 'bounded actual Tracing.start configuration differs')
    api = session.get('api')
    reads = session.get('reads')
    need(isinstance(api, list) and 9 <= len(api) <= LIMITS['apiRows'] and
         isinstance(reads, list) and 1 <= len(reads) <= LIMITS['maxReads'], 'bounded command/read receipts missing')
    methods = ['Browser.getVersion', 'Tracing.getCategories', 'Tracing.start', 'Runtime.evaluate',
               'Runtime.evaluate', 'Tracing.end'] + ['IO.read'] * len(reads) + ['IO.close', 'Runtime.evaluate']
    need([v.get('method') for v in api if isinstance(v, dict)] == methods, 'successful API sequence differs')
    for sequence, row in enumerate(api, 1):
        exact(row, {'sequence': sequence, 'method': methods[sequence - 1], 'params': row.get('params'),
                    'startedAt': row.get('startedAt'), 'endedAt': row.get('endedAt'), 'ok': True}, 'API receipt')
        need(isinstance(row['params'], dict), 'API params missing')
        clock_order([row['startedAt'], row['endedAt']], 'API command')
        if sequence > 1:
            need(api[sequence - 2]['endedAt'] <= row['startedAt'], 'API calls overlapped unexpectedly')
    for index in (0, 1, 5):
        need(api[index]['params'] == {}, 'unexpected command parameters')
    need(api[2]['params'] == start_params, 'raw start command differs from recorded configuration')
    times = [session.get(k) for k in ('fixtureStartedAt', 'startRequestedAt', 'startedAt', 'loopReadyAt',
                                      'loopReturnAt', 'endRequestedAt', 'finishedAt', 'fixtureDeadline')]
    clock_order(times, 'main trace lifecycle')
    need(api[0]['startedAt'] >= session['fixtureStartedAt'] and api[2]['startedAt'] >= session['startRequestedAt'] and
         api[2]['startedAt'] <= session['startedAt'] <= api[2]['endedAt'] <= session['loopReadyAt'] and
         api[3]['endedAt'] <= session['loopReadyAt'] and session['loopReturnAt'] <= api[4]['startedAt'] and
         api[4]['endedAt'] <= session['endRequestedAt'] <= api[5]['startedAt'] and
         api[-1]['endedAt'] <= session['finishedAt'], 'main lifecycle does not enclose original loop/commands')
    need(session['loopReadyAt'] - api[0]['startedAt'] <= LIMITS['setupMs'] and
         session['endRequestedAt'] - session['startedAt'] <= LIMITS['activeMs'] and
         api[-1]['endedAt'] - api[4]['startedAt'] <= LIMITS['drainMs'], 'diagnostic phase cap exceeded')
    need(number(session.get('finishedEpochMs')) and session['finishedEpochMs'] > 0, 'receipt epoch clock missing')
    marks = session.get('marks')
    names = ['mouse637-trace-' + expected['nonce'] + '-' + kind for kind in ('begin', 'end')]
    need(isinstance(marks, list) and len(marks) == 2, 'exactly two owned marks required')
    for index, (kind, name, mark) in enumerate(zip(('begin', 'end'), names, marks)):
        exact(mark, {'kind': kind, 'name': name, 'startTime': mark.get('startTime'),
                     'timeOrigin': mark.get('timeOrigin'), 'now': mark.get('now'),
                     'clock': 'renderer.performance.now'}, 'renderer mark')
        clock_order([mark['startTime'], mark['now']], 'renderer mark')
        need(number(mark['timeOrigin']) and mark['timeOrigin'] > 0, 'renderer time origin missing')
        need(api[3 + index]['params'] == {'expression': marker_expression(name), 'returnByValue': True}, 'actual nonce mark command differs')
    need(marks[0]['timeOrigin'] == marks[1]['timeOrigin'] and marks[0]['now'] <= marks[1]['startTime'],
         'renderer marks use different documents/clocks or reverse order')
    clear = '(()=>{for(const name of ' + json.dumps(names, separators=(',', ':')) + ')performance.clearMarks(name);return true;})()'
    need(api[-1]['params'] == {'expression': clear, 'returnByValue': True}, 'cleanup did not clear only the two owned marks')
    completion = session.get('completion')
    need(isinstance(completion, dict), 'actual tracingComplete missing')
    exact(completion, {'at': completion.get('at'), 'dataLossOccurred': False, 'stream': completion.get('stream'),
                       'traceFormat': completion.get('traceFormat'), 'streamCompression': completion.get('streamCompression')}, 'tracingComplete')
    need(text(completion['stream'], 256) and completion['traceFormat'] in (None, 'json') and
         completion['streamCompression'] in (None, 'none'), 'wrong stream transport')
    clock_order([session['endRequestedAt'], completion['at'], api[6]['startedAt']], 'stream completion')
    buffer = session.get('bufferUsage')
    need(isinstance(buffer, list) and len(buffer) <= LIMITS['bufferEvents'], 'buffer event cap exceeded')
    for row in buffer:
        need(isinstance(row, dict) and set(row).issubset({'at', 'eventCount', 'percentFull', 'value'}) and
             number(row.get('at')) and api[2]['startedAt'] <= row['at'] <= completion['at'], 'buffer event clock/fields invalid')
        for key in ('percentFull', 'value', 'eventCount'):
            if key in row:
                need(number(row[key]) and 0 <= row[key] and (key == 'eventCount' or row[key] < 1),
                     'known trace buffer loss/capacity or invalid usage')
    need(integer(session.get('readCount'), 1, LIMITS['maxReads']) and session['readCount'] == len(reads) and
         integer(session.get('outputBytes'), 1, LIMITS['maxOutputBytes']) and session['outputBytes'] == len(trace_raw), 'stream byte/read total differs')
    same(session.get('trace'), {'filename': PREFIX + 'data.json', 'size': len(trace_raw), 'sha256': sha(trace_raw)}, 'actual trace bytes')
    offset = 0
    for index, row in enumerate(reads):
        command = api[6 + index]
        requested = min(LIMITS['readBytes'], max(1, LIMITS['maxOutputBytes'] - offset))
        need(isinstance(row, dict) and set(row) == {'apiSequence', 'requestedSize', 'base64Encoded', 'eof', 'decodedBytes',
             'returnedDataUTF8Bytes', 'returnedDataSHA256', 'decodedSHA256'}, 'read receipt field inventory invalid')
        same(row, {'apiSequence': command['sequence'], 'requestedSize': requested, 'eof': index == len(reads) - 1}, 'read lifecycle')
        need(type(row.get('base64Encoded')) is bool and integer(row.get('decodedBytes'), 0, requested) and
             (row['eof'] or row['decodedBytes'] > 0), 'invalid/stalled read chunk')
        need(command['params'] == {'handle': completion['stream'], 'size': requested}, 'raw read handle/size differs')
        chunk = trace_raw[offset:offset + row['decodedBytes']]
        need(len(chunk) == row['decodedBytes'], 'read chunks exceed actual trace bytes')
        returned = base64.b64encode(chunk) if row['base64Encoded'] else chunk.decode('utf-8').encode('utf-8')
        need(row['decodedSHA256'] == sha(chunk) and row['returnedDataSHA256'] == sha(returned) and
             integer(row['returnedDataUTF8Bytes']) and row['returnedDataUTF8Bytes'] == len(returned), 'actual read chunk encoding/bytes differ')
        offset += len(chunk)
    need(offset == len(trace_raw), 'stream read receipts omit bytes')
    need(api[-2]['params'] == {'handle': completion['stream']}, 'owned stream not explicitly closed')
    stages = stress.get('stages', [])
    need(len(stages) == 2 and [v.get('ownedPageCount') for v in stages] == [20, 50] and
         [v.get('switchCount') for v in stages] == [5, 10], 'original workloads differ')
    for name in ('processesBefore', 'processesAfter'):
        processes = stages[0].get(name)
        need(isinstance(processes, list) and 2 <= len(processes) <= 1024 and
             all(isinstance(v, dict) and integer(v.get('pid'), 1) and text(v.get('type'), 128) for v in processes),
             'original workload process snapshot missing')
        need([v['pid'] for v in processes if v['type'] == 'Browser'] == [pid] and
             sum(v['pid'] == shell and v['type'] == 'Tab' for v in processes) == 1,
             'original workload belongs to another main/shell process')
    switches = [{k: row.get(k) for k in ('sequence', 'elapsedMs', 'slide')} for row in stages[0].get('switches', [])]
    need(len(switches) == 5 and session.get('switches') == switches and
         [v['sequence'] for v in switches] == list(range(1, 6)), 'trace is not bound to the original five20-page switches')
    for row in switches:
        need(number(row['elapsedMs']) and row['elapsedMs'] >= 0, 'original switch time invalid')
        same(row['slide'], {'phase': 'complete', 'strategy': 'live', 'presented': True,
                            'snapshotCaptures': 0, 'animated': False, 'decoded': False}, 'original live switch result')
    trace = decode(trace_raw)
    need(isinstance(trace, dict) and isinstance(trace.get('traceEvents'), list) and
         1 <= len(trace['traceEvents']) <= 1000000, 'complete Chrome trace event object missing')
    events = trace['traceEvents']
    tracks, active = set(), set()
    found = {name: [] for name in names}
    flows = {'s': 0, 't': 0, 'f': 0}
    for event in events:
        need(isinstance(event, dict) and integer(event.get('pid'), -2**31, 2**32 - 1) and
             integer(event.get('tid'), -2**31, 2**32 - 1) and
             text(event.get('ph'), 1) and text(event.get('name'), 16384, True) and
             ('cat' not in event or text(event['cat'], 16384, True)), 'malformed trace event identity')
        if event['ph'] == 'M':
            if event['name'] == 'process_name' and isinstance(event.get('args'), dict) and text(event['args'].get('name'), 1024):
                tracks.add(event['pid'])
        else:
            need(number(event.get('ts')) and event['ts'] >= 0 and
                 ('dur' not in event or number(event['dur']) and event['dur'] >= 0), 'invalid trace clock/duration')
            active.add(event['pid'])
        if event['name'] in found:
            need(event['pid'] == shell and 'blink.user_timing' in event.get('cat', '').split(',') and
                 event['ph'] != 'M' and number(event.get('ts')), 'foreign or invalid nonce trace marker')
            found[event['name']].append(event)
        if event['ph'] in flows:
            flows[event['ph']] += 1
    need({pid, shell}.issubset(tracks) and {pid, shell}.issubset(active), 'main/shell trace track coverage missing')
    need(all(len(found[name]) == 1 for name in names), 'owned UserTiming markers missing or repeated')
    begin, end = (found[name][0] for name in names)
    need(begin['ts'] < end['ts'] and begin['tid'] == end['tid'], 'trace markers use reverse/different shell clocks')
    for event, mark in zip((begin, end), marks):
        args = event.get('args')
        need(isinstance(args, dict), 'trace marker arguments missing')
        data = args.get('data', {})
        need(isinstance(data, dict) and number(data.get('startTime')) and
             abs(data['startTime'] - mark['startTime']) <= marker_precision(mark['startTime']),
             'trace marker does not bind the observed renderer mark value')
    window_counts = {pid: 0, shell: 0}
    for event in events:
        if event['pid'] not in window_counts or event['ph'] == 'M' or event['name'] in names:
            continue
        # All terms here are timestamps/durations from the same trace clock.
        # An interval crossing a mark counts; the two nonce marks do not count
        # as workload activity, and activity outside this window does not count.
        if event['ts'] <= end['ts'] and event['ts'] + event.get('dur', 0) >= begin['ts']:
            window_counts[event['pid']] += 1
    need(all(window_counts.values()), 'measured window lacks main/shell non-marker activity')
    return {'traceEvents': len(events), 'ownedProcessIds': [pid, shell], 'traceProcessIds': sorted(tracks),
            'markerNames': names, 'traceMarkerDurationMicroseconds': end['ts'] - begin['ts'],
            'rendererMarkerDurationMilliseconds': marks[1]['startTime'] - marks[0]['startTime'],
            'markerSerializationSignificantDigits': MARK_SERIALIZATION_DIGITS,
            'markerSerializationBoundsMilliseconds': [marker_precision(v['startTime']) for v in marks],
            'measuredWindowActivityCounts': {str(k): v for k, v in window_counts.items()},
            'flowEventCounts': flows, 'flowCausalityEstablished': False, 'allGuestRenderersCovered': False}


def verify(directory, *, tools_root=None, publisher_sha=None):
    directory = Path(directory).resolve()
    tools_root = Path(tools_root) if tools_root is not None else Path(__file__).parent
    publisher_sha = publisher_sha or os.environ.get('GITHUB_SHA')
    need(isinstance(publisher_sha, str) and re.fullmatch('[0-9a-f]{40}', publisher_sha), 'explicit publisher SHA required')
    tools = git_tools(tools_root, publisher_sha)
    inputs = {}
    sizes = {}
    def raw(name):
        need(text(name, 256) and PurePosixPath(name).name == name and '\\' not in name, 'unsafe raw filename')
        file = directory / name
        need(file.is_file() and not file.is_symlink() and file.resolve().parent == directory, 'missing regular raw: ' + name)
        need(file.stat().st_size <= LIMITS['maxOutputBytes'], 'raw file exceeds bounded size: ' + name)
        data = file.read_bytes()
        digest = sha(data)
        need(name not in inputs or inputs[name] == digest, 'raw bytes changed while reading: ' + name)
        inputs[name], sizes[name] = digest, len(data)
        return data
    def read(name):
        value = decode(raw(name))
        need(isinstance(value, dict), 'raw JSON object required: ' + name)
        return value
    summary = read(PREFIX + 'summary.json')
    same(summary, {'schema': 1, 'kind': 'mouse637-nonpublishing-performance-summary', 'diagnosticOnly': True,
                   'releaseAcceptance': False, 'ok': True, 'source': SOURCE, 'publisherSHA': publisher_sha,
                   'version': VERSION, 'platform': 'darwin', 'arch': 'arm64', 'verifierSha256': VERIFIER_SHA,
                   'nativeValidatorSha256': NATIVE_READER_SHA, 'nativeValidatorExitCode': 0,
                   'snapshotToolSha256': SNAPSHOT_SHA, 'originalFunctionASTs': FUNCTION_SHAS}, 'summary identity/success')
    need(not summary.get('error') and not summary.get('cleanupError') and not summary.get('metadataError'), 'native/cleanup diagnostic failed')
    exact(summary.get('budgetsMs'), {'outer': 400000, 'native': 350000, 'stress': 200000, 'bootstrap': 30000}, 'original budgets')
    for key, name in [('wrapperSha256', 'mouse637-performance-trace.py'), ('controllerSha256', 'mouse637-performance-trace.cjs')]:
        need(summary.get(key) == tools['tools/' + name], 'actual diagnostic tool receipt differs')
    evidence = summary.get('evidence')
    need(isinstance(evidence, dict) and 15 <= len(evidence) <= 1024 and PREFIX + 'summary.json' not in evidence, 'raw inventory missing/invalid')
    total = 0
    for name, row in evidence.items():
        data = raw(name)
        exact(row, {'size': len(data), 'sha256': sha(data)}, 'actual raw binding: ' + name)
        total += len(data)
        need(total <= 1024**3, 'diagnostic raw inventory exceeds bound')
    executable, app_path, profile, output, candidate = (summary.get(k) for k in ('executable', 'appPath', 'profile', 'output', 'candidate'))
    need(all(text(v) and PurePosixPath(v).is_absolute() and '..' not in PurePosixPath(v).parts for v in
             (executable, app_path, profile, output, candidate)), 'owned absolute paths missing')
    exe = PurePosixPath(executable)
    need(exe.name == 'Mouse Browser' and exe.parent.name == 'MacOS' and
         app_path == str(exe.parent.parent / 'Resources/app.asar') and
         PurePosixPath(profile).name == 'task-stress-631' and PurePosixPath(output).name == 'mouse637-performance-diagnostic' and
         candidate == str(PurePosixPath(output).parent / 'mouse637-release'), 'owned original path layout differs')
    pin = decode((tools_root.parent / 'staging/mouse/6.0.37-arm64/pin.json').read_bytes())
    same(pin, {'source': SOURCE, 'version': VERSION, 'ready': True}, 'immutable package pin')
    need(summary.get('pinSha256') == tools['staging/mouse/6.0.37-arm64/pin.json'] and
         summary.get('packagesBefore') == pin['packages'] == summary.get('packagesAfter'), 'original package byte observations differ')
    for label in ('before', 'after'):
        state = summary.get('installed' + label.capitalize(), {})
        need(state.get('components') == COMPONENTS and state.get('nativeInventory') == sorted(k for k in COMPONENTS if k.endswith('.node')),
             'actual installed executable/ASAR/native bytes differ')
        code_name = 'mouse-637-feature-readiness-codesign-trace-' + label + '.log'
        same(state.get('codesign'), {'exitCode': 0, 'command': ['codesign', '--verify', '--deep', '--strict'],
                                    'log': code_name, 'logSha256': sha(raw(code_name))}, 'actual strict codesign')
    launch = summary.get('launches')
    need(isinstance(launch, list) and len(launch) == 1 and isinstance(launch[0], dict), 'one original native launch required')
    launch = launch[0]
    pid, controller_pid, nonce, port = (launch.get(k) for k in ('pid', 'controllerPid', 'nonce', 'port'))
    need(integer(pid, 1) and integer(controller_pid, 1) and pid != controller_pid and integer(port, 1, 65535) and
         isinstance(nonce, str) and re.fullmatch('[0-9a-f]{64}', nonce), 'owned launch identity invalid')
    same(launch, {'phase': 'performance-trace', 'flag': FLAG, 'profile': profile, 'originalArgv': [executable, FLAG],
                  'argv': [executable, '--inspect-brk=127.0.0.1:' + str(port), FLAG],
                  'addedEnvironment': {'MOUSE_637_PERFORMANCE_TRACE_NONCE': nonce},
                  'controllerExitCode': 0, 'processExitCode': 0}, 'scoped original launch')
    need(not launch.get('error'), 'owned launch failed')
    config, bootstrap, control, module, listener = (read(PREFIX + name + '.json') for name in
                                                   ('config', 'bootstrap', 'controller', 'module', 'listener'))
    same(config, {'schema': 1, 'phase': 'performance-trace', 'flag': FLAG, 'pid': pid, 'nonce': nonce,
                  'port': port, 'publisherSHA': publisher_sha, 'executable': executable, 'appPath': app_path,
                  'profile': profile, 'output': output}, 'bootstrap config')
    need(config.get('deadlineEpochMs') == launch.get('bootstrapStartedAt', -1) + 30000, 'bootstrap deadline changed')
    for key, name in [('receipt', 'bootstrap'), ('moduleReceipt', 'module'), ('controllerReceipt', 'controller'), ('listenerReceipt', 'listener')]:
        need(config.get(key) == output + '/' + PREFIX + name + '.json', 'bootstrap output scope differs')
    controller_text = (tools_root / 'mouse637-performance-trace.cjs').read_text(encoding='utf-8')
    digests = re.findall(r"adaptedSha256:'([0-9a-f]{64})'", controller_text)
    need(len(digests) == 1, 'committed adapted hash absent/ambiguous/unfrozen')
    adapted_sha = digests[0]
    for name, digest, blob, fixture in [('original', ORIGINAL_SHA, ORIGINAL_BLOB, 'stress'),
                                       ('parent', PARENT_SHA, PARENT_BLOB, 'native')]:
        data = raw(PREFIX + name + '.cjs')
        need(sha(data) == digest == tools['tools/fixtures/mouse637-performance-002-' + fixture + '.cjs'] and
             hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == blob, 'actual compiled original source differs')
    need(sha(raw(PREFIX + 'adapted.cjs')) == adapted_sha, 'actual adapted source differs')
    expected = {'diagnosticOnly': True, 'releaseAcceptance': False, 'source': SOURCE, 'publisherSHA': publisher_sha,
                'pid': pid, 'nonce': nonce}
    source = {'parent': app_path + '/mouse-631-smoke.cjs', 'target': app_path + '/mouse-631-stress-smoke.cjs',
              'parentSha256': PARENT_SHA, 'originalSha256': ORIGINAL_SHA, 'adaptedSha256': adapted_sha}
    same(bootstrap, {'schema': 1, 'kind': 'mouse637-performance-trace-bootstrap', **expected, **source,
                     'phase': 'performance-trace', 'flag': FLAG, 'controllerPid': controller_pid,
                     'executable': executable, 'appPath': app_path, 'profile': profile, 'mainSha256': MAIN_SHA,
                     'parentLoads': 1, 'parentBytesDelegated': True, 'inspectorClosed': True, 'inspectorUrl': None,
                     'stressStillDeferred': True, 'loaderStillPending': True, 'receiptBeforeParentInvocation': True}, 'parent bootstrap')
    same(module, {'schema': 1, 'kind': 'mouse637-performance-trace-module', **expected, **source,
                  'originalGitBlob': ORIGINAL_BLOB, 'applications': 1, 'parentLoads': 1,
                  'loaderRestored': True, 'inspectorClosed': True, 'receiptBeforeStressInvocation': True,
                  'closedAt': bootstrap.get('closedAt')}, 'single stress transformation')
    same(bootstrap.get('versions'), RUNTIME, 'bootstrap actual runtime')
    same(control, {'schema': 1, 'kind': 'mouse637-performance-trace-controller', **expected, 'ok': True,
                   'controllerPid': controller_pid, 'port': port, 'host': '127.0.0.1', 'ownershipBeforeResume': True,
                   'serverUnavailable': True, 'listenerReceiptSha256': sha(raw(PREFIX + 'listener.json')),
                   'receiptSha256': sha(raw(PREFIX + 'bootstrap.json')), 'controllerSha256': summary['controllerSha256']}, 'controller proof')
    runtime_identity(control.get('earlyRuntimeIdentity'), config, early=True)
    runtime_identity(control.get('fullRuntimeIdentity'), config)
    need(bootstrap.get('fullRuntimeIdentity') == control['fullRuntimeIdentity'], 'full main identity differs across receipts')
    listener_reader = runpy.run_path(str(tools_root / 'mouse637-guest-input-observer-evidence.py'))
    listener_reader['listener_identity'](listener, pid, port)
    clock_order([launch.get('bootstrapStartedAt'), control.get('startedAt'), listener.get('startedAt'),
                 listener.get('finishedAt'), bootstrap.get('closedAt'), bootstrap.get('parentCompileStartedAt'),
                 bootstrap.get('parentCompileFinishedAt'), control.get('finishedAt'), launch.get('bootstrapFinishedAt')],
                'bootstrap epoch', 30000)
    clock_order([bootstrap['parentCompileFinishedAt'], module.get('compileStartedAt'), module.get('compiledAt')], 'parent/stress compile epoch')
    for key, name in [('receiptSha256', 'bootstrap'), ('controllerReceiptSha256', 'controller')]:
        need(launch.get(key) == sha(raw(PREFIX + name + '.json')), 'actual controller output byte binding differs')
    raw(PREFIX + 'controller.log')
    native, stress, task, acceptance = (read(name) for name in
             ('mouse-631-native.json', 'mouse-631-stress.json', 'mouse-631-task.json', 'mouse-631-acceptance.json'))
    same(native, {'ok': True, 'version': VERSION, 'platform': 'darwin', 'arch': 'arm64', 'pid': pid,
                  'budgetMs': 350000, 'physicalUserDeviceVerified': False, 'liveExternalAccountsVerified': False}, 'original native parent')
    stages = native.get('stages', [])
    need(isinstance(stages, list) and len(stages) == 3 and [v.get('name') for v in stages] == ['taskOnly', 'fiftyTabs', 'stationaryMedia'] and
         all(v.get('ok') is True and number(v.get('elapsedMs')) and v['elapsedMs'] > 0 for v in stages), 'original parent stages incomplete')
    for report, budget, label in [(native, 350000, 'parent'), (task, 65000, 'task'), (stress, 200000, 'stress')]:
        same(report, {'ok': True, 'version': VERSION, 'platform': 'darwin', 'arch': 'arm64', 'budgetMs': budget}, 'original ' + label)
        need(number(report.get('elapsedMs')) and 0 < report['elapsedMs'] <= budget and not report.get('error'), 'original native budget/failure')
    need(task.get('restored') is True and stress.get('restored') is True and stress.get('renderFailures') == [] and
         stress.get('baselineComparison', {}).get('performed') is False, 'original restoration or diagnostic scope differs')
    same(acceptance, {'ok': True, 'version': VERSION, 'platform': 'darwin', 'arch': 'arm64',
                      'taskReportSHA256': sha(raw('mouse-631-task.json')), 'stressReportSHA256': sha(raw('mouse-631-stress.json')),
                      'physicalUserDeviceVerified': False, 'externalAccountsVerified': False}, 'original native reader output')
    native_log = raw('mouse-631-native.log').decode('utf-8')
    need('MOUSE_637_DIAGNOSTIC_TRACE_SAVE_FAILED' not in native_log,
         'late/stale successful session cannot override its receipt-save failure')
    same(summary.get('native'), {'pid': pid, 'exitCode': 0, 'log': 'mouse-631-native.log',
                                'logSha256': sha(raw('mouse-631-native.log')), 'requiredMarkers': MARKERS}, 'original native process')
    elapsed = summary['native'].get('elapsedMs')
    need(number(elapsed) and 0 < elapsed <= 400000 and all(marker in native_log.splitlines() for marker in MARKERS), 'original native workload/outer deadline failed')
    returns = re.findall(r'^MOUSE_NATIVE_PROCESS_RETURN pid=([0-9]+) code=(-?[0-9]+) elapsedMs=([0-9]+)$', native_log, re.M)
    need(len(returns) == 1 and int(returns[0][0]) == pid and int(returns[0][1]) == 0 and
         0 < int(returns[0][2]) <= 400000 and abs(int(returns[0][2]) - elapsed) <= 1, 'actual native process return log differs')
    validation = raw(PREFIX + 'native-validation.log').decode('utf-8').splitlines()
    need(len(validation) == 2 and validation[0] == 'MOUSE_631_INDEPENDENT_EVIDENCE_PASS' and
         decode(validation[1].encode()) == acceptance, 'original native reader log/result differs')
    session = read(PREFIX + 'session.json')
    need(session.get('versions') == bootstrap['versions'], 'actual runtime differs between bootstrap and trace')
    trace_result = trace_identity(session, raw(PREFIX + 'data.json'), stress,
                                  {'source': SOURCE, 'publisherSHA': publisher_sha, 'pid': pid, 'nonce': nonce,
                                   'originalSha256': ORIGINAL_SHA, 'adaptedSha256': adapted_sha})
    clock_order([summary.get('startedAt'), launch['bootstrapStartedAt'], module['compiledAt'], session.get('finishedEpochMs'),
                 summary.get('finishedAt')], 'summary epoch')
    need(set(inputs) - {PREFIX + 'summary.json'} <= set(evidence), 'consumed raw input is absent from summary inventory')
    need(git_tools(tools_root, publisher_sha) == tools, 'committed tools changed while reading')
    return {'ok': True, 'diagnosticOnly': True, 'releaseAcceptance': False, 'causalConclusionEstablished': False,
            'source': SOURCE, 'publisherSHA': publisher_sha, 'pid': pid, 'nonce': nonce,
            'trace': trace_result, 'inputs': inputs, 'committedTools': tools,
            'nativeExecutedByReader': False, 'packagesRehashedByReader': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--publisher-sha')
    args = parser.parse_args()
    print(json.dumps(verify(args.directory, publisher_sha=args.publisher_sha), ensure_ascii=False, sort_keys=True, allow_nan=False))
