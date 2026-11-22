#!/usr/bin/env python3
"""Read-only additive evidence gate for the passive retained CI observer.

Original source=False native acceptance and the feature-readiness gate remain
required. Browser callbacks and primaryDown are observations, not delivery
acknowledgements. No cross-process clock alignment or new pointer sequence gate
is inferred here.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import runpy

SOURCE = '0021084ccb9537e657d21e6f0c8e812dee6b461f'
VERSION = '6.0.37'
ORIGINAL_SHA = '911a5759675d721414d2a4a98c722f634a1bdc9131ae2bf3882a79e9cbc0200d'
ORIGINAL_BLOB = '6548c72795a80a432f531065a5846c28ad5b549d'
MAIN_SHA = 'f3c9ba7794cb5c659c75fdc981faeda6b45851ceb0e70b61291128a04387914f'
INNER_SHA = '767217ed097c52703f8f8015fa1bf26e43c727447e05c74cfcbc43aaafcc255d'
FLAG = '--mouse-636-retained-smoke'
PREFIX = 'mouse-637-guest-input-observer-'
REPORT = 'mouse-636-retained-owner-feedback.json'
LOG = 'mouse-636-retained-owner-feedback.log'
FEATURE = 'mouse-637-feature-readiness-summary.json'
GUEST_SELECTORS = ['#download-a', '#download-b', '#link-blank', '#link-same',
                   '#link-blank', '#download-chat', '#download-preview']
DOM_TYPES = {'pointerdown', 'pointerup', 'pointercancel', 'mousedown', 'mouseup', 'click', 'focus', 'blur'}
SCOPE = ('Passive WebContents/window observations and owned DOM capture events; no DOM mousemove; '
         'input-event is not a delivery acknowledgment')


def need(value, message):
    if not value:
        raise ValueError('Mouse637 guest input observer: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def integer(value, minimum=0, maximum=2**53 - 1):
    return type(value) is int and minimum <= value <= maximum


def same(actual, expected, label):
    need(isinstance(actual, dict), label + ' object missing')
    need(all(k in actual and actual[k] == v and type(actual[k]) is type(v) for k, v in expected.items()), label + ' differs')


def bounded_text(value, size=128, empty=True):
    return isinstance(value, str) and len(value) <= size and (empty or bool(value))


def runtime_identity(value, config, *, early=False):
    same(value, {k: config[k] for k in ('profile', 'nonce')}, 'runtime environment')
    same(value, {'platform': 'darwin', 'arch': 'arm64', 'CI': 'true'}, 'runtime platform')
    for key, kind in [('pid', 'number'), ('execPath', 'string'), ('argv', 'object')]:
        if early:
            available = value.get('availability', {}).get(key)
            if available == 'undefined':
                need(key in value and value[key] is None, 'uninitialized runtime field is not null: ' + key)
                continue
            need(available == kind, 'runtime availability differs: ' + key)
        if key == 'pid':
            need(integer(value.get(key), 1) and value[key] == config['pid'], 'runtime PID differs')
        elif key == 'execPath':
            need(value.get(key) == config['executable'], 'runtime executable differs')
        else:
            argv = value.get(key)
            need(isinstance(argv, list) and 1 <= len(argv) <= 32 and
                 all(bounded_text(x, 4096, False) for x in argv) and argv[0] == config['executable'], 'runtime argv differs')
            need([x for x in argv if x.startswith('--mouse-') and not x.startswith('--mouse-profile')] == [FLAG],
                 'runtime smoke scope differs')


def listener_identity(value, pid, port):
    same(value, {'schema': 1, 'kind': 'mouse637-inspector-listener', 'pid': pid, 'port': port,
                 'host': '127.0.0.1', 'exitCode': 0, 'signal': None, 'ok': True}, 'OS listener identity')
    command = ['/usr/sbin/lsof', '-nP', '-a', '-iTCP:' + str(port), '-sTCP:LISTEN', '-F', 'pfnPT', '-Ts']
    need(value.get('command') == command and not value.get('error'), 'OS listener command/error differs')
    stdout, stderr = value.get('stdout'), value.get('stderr')
    need(bounded_text(stdout, 65536, False) and bounded_text(stderr, 65536) and not stderr.strip(), 'OS listener output missing/error')
    process = None
    sockets = []
    current = None
    for line in stdout.rstrip().split('\n'):
        need(len(line) > 1 and '\r' not in line and '\0' not in line, 'malformed OS listener field')
        field, item = line[0], line[1:]
        if field == 'p':
            need(process is None and re.fullmatch('[1-9][0-9]*', item), 'multiple/invalid listener processes')
            process = int(item)
            need(integer(process, 1), 'unsafe listener PID')
        elif field == 'f':
            need(process is not None and re.fullmatch('[0-9]+', item), 'listener descriptor lacks owner')
            current = {'pid': process, 'fd': item}
            sockets.append(current)
        else:
            key = {'P': 'protocol', 'n': 'endpoint', 'T': 'state'}.get(field)
            need(current is not None and key and key not in current, 'unknown/duplicate listener field')
            if field == 'T':
                need(item.startswith('ST='), 'listener state field differs')
                item = item[3:]
            current[key] = item
    need(len(sockets) == 1, 'exactly one actual listener required')
    parsed = sockets[0]
    same(parsed, {'pid': pid, 'protocol': 'TCP', 'endpoint': '127.0.0.1:' + str(port), 'state': 'LISTEN'}, 'parsed OS listener')
    need(value.get('parsed') == parsed, 'recorded listener parsing differs from actual stdout')
    return parsed


def trace_identity(facts, trace, expected, first_input_at):
    same(trace, {'schema': 1, 'kind': 'mouse637-passive-guest-input', **expected, 'started': True, 'disposed': True}, 'runtime observer')
    same(trace.get('caps'), {'records': 2048, 'posts': 64, 'webContents': 32, 'domPerDocument': 256}, 'observer bounds')
    stats = trace.get('stats', {})
    keys = {'dropped', 'postDropped', 'errors', 'foreignMessages', 'malformedMessages', 'unownedEvents', 'documents'}
    need(set(stats) == keys and all(integer(v, 0, 1000000) for v in stats.values()), 'observer counters invalid')
    need(all(stats[k] == 0 for k in ('dropped', 'postDropped', 'errors', 'malformedMessages')), 'observer trace is incomplete or malformed')
    need(trace.get('semantics') == 'input-event observes browser-side processing, not delivery; DOM has separate clocks; no DOM mousemove',
         'observer semantics label differs')
    inputs, attempts, posts, records, docs, registered = (facts.get('nativeInputs'), facts.get('guestClickAttempts'),
        trace.get('posts'), trace.get('records'), trace.get('documents'), trace.get('registeredWebContents'))
    need(isinstance(inputs, list) and 7 <= len(inputs) <= 64 and isinstance(posts, list) and len(posts) == len(inputs),
         'one original native post per original input required')
    need(isinstance(attempts, list) and [x.get('selector') for x in attempts] == GUEST_SELECTORS, 'original seven guest actions differ')
    need(isinstance(records, list) and 1 <= len(records) <= 2048 and isinstance(docs, list) and 2 <= len(docs) <= 32,
         'bounded real runtime records/documents missing')
    need(isinstance(registered, list) and 2 <= len(registered) <= 32, 'registered WebContents missing')
    need(all(isinstance(x, dict) for values in (inputs, attempts, posts, records, docs, registered) for x in values),
         'runtime rows must be objects')
    wcids = [x.get('id') for x in registered]
    need(all(integer(x, 1) for x in wcids) and len(set(wcids)) == len(wcids), 'registered WebContents IDs invalid/repeated')
    need(all(number(x.get('registeredAt')) and ('destroyed' not in x or x['destroyed'] is True) for x in registered), 'WebContents lifetime facts invalid')
    owners = {}

    def collect(value):
        if isinstance(value, dict):
            wc = value.get('webContentsId')
            tab = value.get('tabId', value.get('id'))
            if integer(wc, 1) and isinstance(tab, str) and re.fullmatch('[0-9a-f-]{36}', tab):
                need(wc not in owners or owners[wc] == tab, 'original guest owner changes identity')
                owners[wc] = tab
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)
    collect({k: v for k, v in facts.items() if k != 'guestInputObserver'})
    shell_ids = {a.get('before', {}).get('native', {}).get('focus', {}).get('webContentsId') for a in attempts
                 if a.get('before', {}).get('native', {}).get('focus', {}).get('shell') is True}
    need(len(shell_ids) == 1 and all(integer(x, 1) for x in shell_ids), 'original shell identity missing/ambiguous')
    shell = next(iter(shell_ids))
    need(shell not in owners and set(owners).issubset(set(wcids)) and shell in wcids, 'observer registered another native owner')
    documents = {}
    requested_indexes = {x.get('index') for x in facts.get('requests', []) if isinstance(x, dict) and integer(x.get('index'))}
    for d in docs:
        same(d, {'cap': 256}, 'document cap')
        need(set(d) == {'id', 'timeOrigin', 'role', 'index', 'webContentsId', 'lastSequence', 'cap'} and
             bounded_text(d.get('id'), 96, False) and number(d.get('timeOrigin')) and
             integer(d.get('index'), -1, 10000) and integer(d.get('lastSequence'), 1, 256), 'document identity/counter invalid')
        wc = d.get('webContentsId')
        need(integer(wc, 1) and ((d['role'] == 'shell' and wc == shell and d['index'] == -1) or
             (d['role'] == 'guest' and wc in owners and d['index'] >= 0)), 'foreign document owner')
        need(d['role'] == 'shell' or d['index'] in requested_indexes, 'document was not requested by the owned fixture')
        key = (wc, d['id'])
        need(key not in documents, 'duplicate document identity')
        documents[key] = d
    need(stats['documents'] == len(documents) and sum(d['role'] == 'shell' for d in docs) == 1, 'document coverage differs')
    dom_sequences = {key: [] for key in documents}
    dom_times = {key: [] for key in documents}
    clicks = []
    for index, event in enumerate(records, 1):
        need(event.get('sequence') == index and type(event.get('sequence')) is int and number(event.get('at')), 'main trace sequence/time invalid')
        source = event.get('source')
        if source == 'window':
            need(set(event) == {'sequence', 'at', 'source', 'event', 'windowId'}, 'unexpected window payload')
            need(event.get('event') in ('focus', 'blur') and integer(event.get('windowId'), 1), 'window observation invalid')
            continue
        need(source in ('dom', 'webContents'), 'unexpected/error runtime record')
        wc = event.get('webContentsId')
        if event.get('role') == 'shell':
            need(wc == shell and event.get('tabId') is None, 'foreign shell record')
        else:
            need(event.get('role') == 'guest' and wc in owners and event.get('tabId') == owners[wc], 'foreign guest record')
        if source == 'webContents':
            need(event.get('event') in ('focus', 'blur', 'before-mouse-event', 'input-event'), 'unknown WebContents observation')
            expected_keys = {'sequence', 'at', 'source', 'event', 'role', 'webContentsId', 'tabId'}
            if event['event'] in ('before-mouse-event', 'input-event'):
                expected_keys |= {'defaultPrevented', 'input'}
            need(set(event) == expected_keys, 'unexpected WebContents payload')
            if event['event'] in ('before-mouse-event', 'input-event'):
                data = event.get('input', {})
                need(set(data) == {'type', 'x', 'y', 'movementX', 'movementY', 'button', 'clickCount', 'modifiers'} and
                     bounded_text(data.get('type'), 128, False) and bounded_text(data.get('button'), 128) and
                     all(data[k] is None or number(data[k]) for k in ('x', 'y', 'movementX', 'movementY', 'clickCount')) and
                     isinstance(data.get('modifiers'), list) and len(data['modifiers']) <= 8 and
                     all(bounded_text(x, 128) for x in data['modifiers']) and type(event.get('defaultPrevented')) is bool,
                     'malformed browser-side input observation')
            continue
        need(set(event) == {'sequence', 'at', 'source', 'role', 'webContentsId', 'tabId', 'document', 'kind',
                           'domSequence', 'domAt', 'domTime', 'emitted', 'dropped', 'type', 'trusted',
                           'defaultPrevented', 'target', 'button', 'buttons', 'pointerId', 'pointerType',
                           'x', 'y', 'documentFocused'}, 'unexpected DOM payload')
        identity = event.get('document', {})
        key = (wc, identity.get('id'))
        need(key in documents and identity == {k: documents[key][k] for k in ('id', 'timeOrigin', 'role', 'index')}, 'DOM record belongs to another document')
        n = event.get('domSequence')
        need(integer(n, 1, 256) and event.get('emitted') == n and type(event.get('emitted')) is int and
             event.get('dropped') == 0 and type(event.get('dropped')) is int and number(event.get('domAt')) and number(event.get('domTime')),
             'DOM sequence/drop/time invalid')
        dom_sequences[key].append(n)
        dom_times[key].append(event['domTime'])
        kind = event.get('kind')
        need(kind in ('ready', 'event', 'dispose') and ((n == 1) == (kind == 'ready')), 'DOM readiness/error/overflow differs')
        if kind == 'event':
            target = event.get('target', {})
            need(event.get('type') in DOM_TYPES and type(event.get('trusted')) is bool and type(event.get('defaultPrevented')) is bool
                 and type(event.get('documentFocused')) is bool and set(target) == {'kind', 'tag', 'id', 'linkId'} and
                 target.get('kind') in ('window', 'document', 'element') and
                 all(bounded_text(target.get(k), 96) for k in ('tag', 'id', 'linkId')), 'malformed DOM event')
            if event['type'] == 'click' and event['trusted'] is True:
                clicks.append(event)
        else:
            need(event.get('type') is None and event.get('target') is None, 'non-event carries event payload')
        need(all(event.get(k) is None or number(event[k]) for k in ('button', 'buttons', 'pointerId', 'x', 'y')) and
             bounded_text(event.get('pointerType'), 128), 'DOM coordinate/type payload invalid')
    for key, d in documents.items():
        need(dom_sequences[key] == list(range(1, d['lastSequence'] + 1)) and
             dom_times[key] == sorted(dom_times[key]), 'missing/out-of-order document observations')
    need(any(e.get('source') == 'webContents' and e.get('event') == 'before-mouse-event' for e in records) and
         any(e.get('source') == 'webContents' and e.get('event') == 'input-event' for e in records), 'browser-side observation coverage missing')
    guest_inputs = [x for x in inputs if 'webContentsId' in x]
    need([x.get('selector') for x in guest_inputs] == GUEST_SELECTORS, 'original native guest input coverage differs')
    used_clicks = set()
    for input_row, attempt in zip(guest_inputs, attempts):
        for key in ('selector', 'point', 'tabId', 'webContentsId'):
            need(input_row.get(key) == attempt.get(key), 'original guest attempt/input binding differs')
        wanted = input_row['selector'][1:]
        events = input_row.get('events')
        need(isinstance(events, list) and any(x.get('id') == wanted and x.get('trusted') is True for x in events), 'original trusted guest click missing')
        need(attempt.get('poll', {}).get('events') == events and attempt.get('posted', {}).get('result') is True and
             not attempt.get('error') and not attempt.get('failedNative'), 'original guest attempt did not pass')
        matches = [e for e in clicks if e['sequence'] not in used_clicks and e['role'] == 'guest' and
                   e['webContentsId'] == input_row['webContentsId'] and e['tabId'] == input_row['tabId'] and
                   e['target']['linkId'] == wanted]
        need(matches, 'real trusted DOM click observation missing for original guest input')
        used_clicks.add(matches[0]['sequence'])
    previous_after = first_input_at
    guest_index = 0
    for index, (post, native) in enumerate(zip(posts, inputs), 1):
        need(set(post) == {'id', 'x', 'y', 'beforeSequence', 'beforeAt', 'primaryBefore', 'returned',
                          'resultType', 'result', 'primaryAfter', 'afterAt', 'afterSequence'}, 'unexpected native post payload')
        same(post, {'id': index, 'returned': True, 'resultType': 'boolean', 'result': True}, 'original native post result')
        point = native.get('point', {})
        need(native.get('source') == 'CGEvent' and number(point.get('x')) and number(point.get('y')) and
             post.get('x') == point['x'] and post.get('y') == point['y'] and not post.get('threw') and not post.get('errorName'), 'native post/input point or failure differs')
        need(number(post.get('beforeAt')) and number(post.get('afterAt')) and previous_after <= post['beforeAt'] <= post['afterAt'] and
             integer(post.get('beforeSequence'), 0, len(records)) and integer(post.get('afterSequence'), post['beforeSequence'], len(records)), 'native post sequence/time invalid')
        previous_after = post['afterAt']
        for key in ('primaryBefore', 'primaryAfter'):
            value = post.get(key, {})
            need(isinstance(value, dict) and (
                (value == {'available': False} and type(value.get('available')) is bool) or
                (value.get('available') is True and set(value) == {'available', 'value'} and type(value.get('value')) is bool) or
                (value.get('available') is True and set(value) == {'available', 'error'} and bounded_text(value.get('error'), 128)) or
                (value.get('available') is True and set(value) == {'available', 'value', 'unexpectedType'} and value.get('value') is None and
                 value.get('unexpectedType') in ('undefined', 'object', 'string', 'number', 'function', 'symbol', 'bigint'))),
                'optional primaryDown observation shape differs')
        if 'webContentsId' in native:
            attempt = attempts[guest_index]
            guest_index += 1
            need(number(attempt.get('before', {}).get('at')) and number(attempt.get('posted', {}).get('at')) and
                 attempt['before']['at'] <= post['beforeAt'] <= post['afterAt'] <= attempt['posted']['at'], 'guest post is outside original main-clock attempt')
        elif native.get('navigates') is not True:
            original_clicks = [e for e in native.get('events', []) if e.get('type') == 'click' and e.get('trusted') is True and e.get('matches') is True]
            need(original_clicks, 'original trusted shell click missing')
            targets = {e.get('target') for e in original_clicks if isinstance(e.get('target'), str)}
            matches = [e for e in clicks if e['sequence'] not in used_clicks and e['role'] == 'shell' and
                       (e['target']['id'] or e['target']['tag']) in targets]
            need(matches, 'real trusted DOM click observation missing for original shell input')
            used_clicks.add(matches[0]['sequence'])
    return {'posts': len(posts), 'guestClicks': len(guest_inputs), 'boundDOMClicks': len(used_clicks),
            'records': len(records), 'documents': len(documents), 'webContents': len(wcids)}


def verify(directory, *, tools_root=None, publisher_sha=None):
    directory = Path(directory)
    tools_root = Path(tools_root) if tools_root is not None else Path(__file__).parent
    publisher_sha = publisher_sha or os.environ.get('GITHUB_SHA')
    need(isinstance(publisher_sha, str) and re.fullmatch('[0-9a-f]{40}', publisher_sha), 'exact publisher SHA required')
    inputs = {}

    def raw(name):
        need(isinstance(name, str) and Path(name).name == name, 'evidence filename must be local')
        file = directory / name
        need(file.is_file() and not file.is_symlink() and file.stat().st_size <= 16 * 1024**2, 'missing/unsafe/big evidence: ' + name)
        value = file.read_bytes()
        inputs[name] = sha(value)
        return value

    def read(name):
        return json.loads(raw(name))

    summary = read(PREFIX + 'summary.json')
    same(summary, {'schema': 1, 'kind': 'mouse637-passive-guest-input-summary', 'source': SOURCE, 'version': VERSION,
                   'publisherSHA': publisher_sha, 'platform': 'darwin', 'arch': 'arm64', 'ok': True}, 'summary')
    need(not summary.get('error') and not summary.get('cleanupError'), 'observer wrapper failed')
    for field, name in [('wrapperSha256', 'mouse637-guest-input-observer.py'), ('controllerSha256', 'mouse637-guest-input-observer.cjs'),
                        ('innerWrapperSha256', 'mouse637-feature-readiness.py')]:
        need(summary.get(field) == sha((tools_root / name).read_bytes()), 'publisher tool bytes differ: ' + name)
    need(summary['innerWrapperSha256'] == INNER_SHA, 'existing feature wrapper changed')
    controller_source = (tools_root / 'mouse637-guest-input-observer.cjs').read_text()
    hashes = re.findall(r"adaptedSha256:'([0-9a-f]{64})'", controller_source)
    need(len(hashes) == 1, 'committed adapted module hash missing/ambiguous')
    adapted_sha = hashes[0]
    original = raw(PREFIX + 'original.cjs')
    need(sha(original) == ORIGINAL_SHA and hashlib.sha1(b'blob ' + str(len(original)).encode() + b'\0' + original).hexdigest() == ORIGINAL_BLOB
         and original == (tools_root / 'fixtures/mouse637-retained-002.cjs').read_bytes(), 'original installed module differs')
    need(sha(raw(PREFIX + 'adapted.cjs')) == adapted_sha, 'actual adapted module differs')
    evidence = summary.get('evidence', {})
    need(set(evidence) == {FEATURE, REPORT, LOG}, 'original summary/report/log bindings incomplete')
    for name, item in evidence.items():
        value = raw(name)
        same(item, {'size': len(value), 'sha256': sha(value)}, 'original evidence bytes ' + name)
    feature_gate = runpy.run_path(str(tools_root / 'mouse637-feature-readiness-evidence.py'))
    feature = feature_gate['verify'](directory, tools_root=tools_root, publisher_sha=publisher_sha)
    for name, digest in feature['inputs'].items():
        need(sha(raw(name)) == digest, 'feature dependency consumed different raw bytes')
    installed = read(FEATURE)
    executable, app_path, profile, output = (summary.get(k) for k in ('executable', 'appPath', 'profile', 'output'))
    need(all(bounded_text(x, 4096, False) and x.startswith('/') for x in (executable, app_path, profile, output)), 'absolute owned paths missing')
    need(executable == installed.get('executable') and app_path == installed.get('appPath') and output == installed.get('output') and
         profile == str(Path(installed['profile']).parent / 'retained636'), 'installed candidate/profile scope differs')
    rows = summary.get('launches')
    need(isinstance(rows, list) and len(rows) == 1, 'exactly one original retained launch required')
    row = rows[0]
    pid, controller_pid, nonce, port = (row.get(k) for k in ('pid', 'controllerPid', 'nonce', 'port'))
    need(integer(pid, 1) and integer(controller_pid, 1) and pid != controller_pid and integer(port, 1, 65535) and
         isinstance(nonce, str) and re.fullmatch('[0-9a-f]{64}', nonce), 'actual process/controller/nonce/port invalid')
    same(row, {'phase': 'retained', 'flag': FLAG, 'profile': profile, 'controllerExitCode': 0, 'processExitCode': 0,
               'originalArgv': [executable, FLAG], 'argv': [executable, '--inspect-brk=127.0.0.1:' + str(port), FLAG],
               'addedEnvironment': {'MOUSE_637_GUEST_INPUT_NONCE': nonce}}, 'original launch')
    need(number(row.get('bootstrapElapsedMs')) and 0 <= row['bootstrapElapsedMs'] <= 30000 and not row.get('bootstrapError'), 'bounded bootstrap failed')
    names = {'receipt': PREFIX + 'bootstrap.json', 'controllerReceipt': PREFIX + 'controller.json', 'config': PREFIX + 'config.json',
             'listenerReceipt': PREFIX + 'listener.json', 'controllerLog': PREFIX + 'controller.log'}
    for key, name in names.items():
        need(row.get(key) == name and row.get(key + 'Sha256') == sha(raw(name)), 'bootstrap raw hash binding differs: ' + key)
    receipt, control, config, listener = (read(names[k]) for k in ('receipt', 'controllerReceipt', 'config', 'listenerReceipt'))
    common = {'schema': 1, 'phase': 'retained', 'pid': pid, 'nonce': nonce, 'publisherSHA': publisher_sha}
    same(config, {**common, 'flag': FLAG, 'port': port, 'executable': executable, 'appPath': app_path, 'profile': profile,
                  'output': output, 'receipt': output + '/' + names['receipt'], 'controllerReceipt': output + '/' + names['controllerReceipt'],
                  'listenerReceipt': output + '/' + names['listenerReceipt']}, 'owned bootstrap config')
    need(number(row.get('bootstrapStartedAt')) and config.get('deadlineEpochMs') == row['bootstrapStartedAt'] + 30000, 'bootstrap deadline changed')
    same(receipt, {**common, 'kind': 'mouse637-passive-guest-input-bootstrap', 'source': SOURCE, 'version': VERSION,
                   'flag': FLAG, 'controllerPid': controller_pid, 'executable': executable, 'appPath': app_path, 'profile': profile,
                   'target': app_path + '/mouse-636-retained-smoke.cjs', 'platform': 'darwin', 'arch': 'arm64',
                   'originalSha256': ORIGINAL_SHA, 'originalGitBlob': ORIGINAL_BLOB, 'adaptedSha256': adapted_sha, 'mainSha256': MAIN_SHA,
                   'applications': 1, 'scope': SCOPE, 'loaderRestored': True, 'inspectorClosed': True, 'inspectorUrl': None,
                   'receiptBeforeFixtureInvocation': True}, 'in-process bootstrap receipt')
    need(receipt.get('versions', {}).get('electron') == '44.5.0' and bounded_text(receipt.get('versions', {}).get('node'), 96, False), 'actual embedded runtime missing')
    same(control, {**common, 'ok': True, 'controllerPid': controller_pid, 'port': port, 'host': '127.0.0.1',
                   'ownershipBeforeResume': True, 'serverUnavailable': True, 'receiptSha256': sha(raw(names['receipt'])),
                   'listenerReceiptSha256': sha(raw(names['listenerReceipt'])), 'controllerSha256': summary['controllerSha256']}, 'controller ownership/shutdown')
    runtime_identity(control.get('earlyRuntimeIdentity'), config, early=True)
    runtime_identity(control.get('fullRuntimeIdentity'), config)
    need(receipt.get('fullRuntimeIdentity') == control['fullRuntimeIdentity'], 'full runtime binding differs')
    listener_identity(listener, pid, port)
    need(number(summary.get('startedAt')) and number(summary.get('finishedAt')) and summary['startedAt'] <= row['bootstrapStartedAt'] <= summary['finishedAt'], 'summary/launch chronology invalid')
    need(all(number(x.get('startedAt')) and number(x.get('finishedAt')) and row['bootstrapStartedAt'] <= x['startedAt'] <= x['finishedAt'] <= config['deadlineEpochMs']
             for x in (control, listener)) and control['startedAt'] <= listener['startedAt'] <= listener['finishedAt'] <= control['finishedAt'], 'bounded controller/listener chronology invalid')
    facts = read(REPORT)
    same(facts, {'schema': 1, 'version': VERSION, 'platform': 'darwin', 'arch': 'arm64', 'pid': pid, 'budgetMs': 240000,
                 'packaged': True, 'profileIsolated': True, 'physicalUserDeviceVerified': False, 'liveExternalAccountsVerified': False,
                 'stage': 'complete', 'ok': True, 'restored': True, 'nativeInputSource': 'CGEvent'}, 'original retained result')
    need(number(facts.get('elapsedMs')) and 0 < facts['elapsedMs'] <= 240000 and not facts.get('error') and
         not facts.get('cleanupError') and not facts.get('cleanupErrors'), 'original retained failure/budget')
    need(number(receipt.get('closedAt')) and number(receipt.get('compiledAt')) and receipt['closedAt'] <= receipt['compiledAt'], 'loader/Inspector closure chronology invalid')
    coverage = trace_identity(facts, facts.get('guestInputObserver'), {'source': SOURCE, 'publisherSHA': publisher_sha, 'pid': pid,
        'nonce': nonce, 'originalSha256': ORIGINAL_SHA, 'adaptedSha256': adapted_sha}, receipt['compiledAt'])
    lines = raw(LOG).decode('utf-8').splitlines()
    need(lines.count('MOUSE_636_RETAINED_OWNER_FEEDBACK_PASS') == 1 and not any('MOUSE_636_RETAINED_OWNER_FEEDBACK_FAILED' in x or 'MOUSE_NATIVE_PROCESS_TIMEOUT' in x for x in lines), 'original retained log did not pass')
    hooks = [json.loads(x.split(' ', 1)[1]) for x in lines if x.startswith('MOUSE_637_GUEST_INPUT_OBSERVER_BOOTSTRAP ')]
    need(hooks == [receipt], 'actual retained log bootstrap differs/missing/repeated')
    exits = [re.fullmatch(r'MOUSE_NATIVE_PROCESS_RETURN pid=(\d+) code=(-?\d+) elapsedMs=(\d+)', x) for x in lines if x.startswith('MOUSE_NATIVE_PROCESS_RETURN ')]
    need(len(exits) == 1 and exits[0] is not None and int(exits[0][1]) == pid and int(exits[0][2]) == 0 and 0 < int(exits[0][3]) <= 270000,
         'original actual retained process exit/budget differs')
    return {'schema': 1, 'ok': True, 'source': SOURCE, 'publisherSHA': publisher_sha,
            'gate': 'mouse637-passive-guest-input-v1', 'inputs': inputs, 'nativePid': pid,
            'coverage': coverage, 'featureReadiness': feature, 'originalNativeGatesRemainRequired': True,
            'causalFixEstablished': False, 'nativeExecutionPerformedHere': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.directory)
    with (args.directory / (PREFIX + 'independent.json')).open('x', encoding='utf-8') as target:
        json.dump(result, target, indent=2, allow_nan=False)
        target.write('\n')
    print('MOUSE_637_PASSIVE_GUEST_INPUT_OBSERVER_EVIDENCE_PASS')
