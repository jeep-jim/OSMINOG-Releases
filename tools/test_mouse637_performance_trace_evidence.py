#!/usr/bin/env python3
"""Synthetic diagnostic receipts, never native execution or release evidence.

The positive fixture runs the actual reviewed transform in ordinary Node,
uses the real committed helper/fixture bytes in an isolated temporary Git repo,
and constructs explicitly synthetic process/CDP/native records. Semantic mutants
rebind their enclosing hashes so an outer checksum is not the rejection reason.
"""
import base64
import copy
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parent
E = runpy.run_path(str(TOOLS / 'mouse637-performance-trace-evidence.py'))
P = E['PREFIX']


def encoded(value):
    return value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def at(value, *path):
    for key in path:
        value = value[key]
    return value


def change(value, path, replacement):
    parent = at(value, *path[:-1])
    parent[path[-1]] = replacement


class SyntheticProof:
    """No BrowserWindow, installed app, native input, package or release is run."""
    def __init__(self, repo, publisher, adapted):
        self.repo, self.publisher = repo, publisher
        self.data = {}
        self.pid, self.shell, self.sidecar, self.port = 81001, 81002, 81003, 49221
        self.nonce = 'd1' * 32
        self.epoch = 1795350000000
        self.output = '/Users/runner/work/OSMINOG-Releases/OSMINOG-Releases/mouse637-performance-diagnostic'
        self.exe = '/Users/runner/work/_temp/Установка Mouse/Mouse Browser.app/Contents/MacOS/Mouse Browser'
        self.app = '/Users/runner/work/_temp/Установка Mouse/Mouse Browser.app/Contents/Resources/app.asar'
        self.profile = '/Users/runner/work/_temp/mouse-profiles/task-stress-631'
        self.argv = [self.exe, '--inspect-brk=127.0.0.1:' + str(self.port), E['FLAG']]
        common = {'schema': 1, 'diagnosticOnly': True, 'releaseAcceptance': False, 'source': E['SOURCE'],
                  'publisherSHA': publisher, 'pid': self.pid, 'nonce': self.nonce}
        source = {'parent': self.app + '/mouse-631-smoke.cjs', 'target': self.app + '/mouse-631-stress-smoke.cjs',
                  'parentSha256': E['PARENT_SHA'], 'originalSha256': E['ORIGINAL_SHA'],
                  'adaptedSha256': hashlib.sha256(adapted).hexdigest()}
        runtime = {'pid': self.pid, 'execPath': self.exe, 'argv': self.argv,
                   'platform': 'darwin', 'arch': 'arm64', 'CI': 'true', 'profile': self.profile, 'nonce': self.nonce}
        self.data[P + 'config.json'] = {'schema': 1, 'phase': 'performance-trace', 'flag': E['FLAG'],
            'pid': self.pid, 'nonce': self.nonce, 'port': self.port, 'publisherSHA': publisher,
            'executable': self.exe, 'appPath': self.app, 'profile': self.profile, 'output': self.output,
            'deadlineEpochMs': self.epoch + 31000,
            **{key: self.output + '/' + P + suffix + '.json' for key, suffix in
               [('receipt', 'bootstrap'), ('moduleReceipt', 'module'), ('controllerReceipt', 'controller'), ('listenerReceipt', 'listener')]}}
        self.data[P + 'bootstrap.json'] = {**common, **source, 'kind': 'mouse637-performance-trace-bootstrap',
            'phase': 'performance-trace', 'flag': E['FLAG'], 'controllerPid': self.sidecar,
            'executable': self.exe, 'appPath': self.app, 'profile': self.profile, 'mainSha256': E['MAIN_SHA'],
            'versions': E['RUNTIME'].copy(), 'fullRuntimeIdentity': copy.deepcopy(runtime), 'parentLoads': 1,
            'parentBytesDelegated': True, 'inspectorClosed': True, 'inspectorUrl': None,
            'closedAt': self.epoch + 2000, 'parentCompileStartedAt': self.epoch + 2001,
            'parentCompileFinishedAt': self.epoch + 2003, 'stressStillDeferred': True,
            'loaderStillPending': True, 'receiptBeforeParentInvocation': True}
        self.data[P + 'module.json'] = {**common, **source, 'kind': 'mouse637-performance-trace-module',
            'originalGitBlob': E['ORIGINAL_BLOB'], 'applications': 1, 'parentLoads': 1,
            'loaderRestored': True, 'inspectorClosed': True, 'closedAt': self.epoch + 2000,
            'compileStartedAt': self.epoch + 15000, 'compiledAt': self.epoch + 15002,
            'receiptBeforeStressInvocation': True}
        self.data[P + 'listener.json'] = {'schema': 1, 'kind': 'mouse637-inspector-listener',
            'pid': self.pid, 'port': self.port, 'host': '127.0.0.1', 'exitCode': 0, 'signal': None, 'ok': True,
            'command': ['/usr/sbin/lsof', '-nP', '-a', '-iTCP:' + str(self.port), '-sTCP:LISTEN', '-F', 'pfnPT', '-Ts'],
            'startedAt': self.epoch + 1300, 'finishedAt': self.epoch + 1310,
            'stdout': 'p81001\nf17\nPTCP\nn127.0.0.1:49221\nTST=LISTEN\n', 'stderr': '',
            'parsed': {'pid': self.pid, 'fd': '17', 'protocol': 'TCP', 'endpoint': '127.0.0.1:49221', 'state': 'LISTEN'}}
        self.data[P + 'controller.json'] = {**common, 'kind': 'mouse637-performance-trace-controller', 'ok': True,
            'controllerPid': self.sidecar, 'host': '127.0.0.1', 'port': self.port,
            'startedAt': self.epoch + 1200, 'finishedAt': self.epoch + 2100,
            'earlyRuntimeIdentity': {**copy.deepcopy(runtime), 'pid': None, 'execPath': None, 'argv': None,
                'availability': {'pid': 'undefined', 'execPath': 'undefined', 'argv': 'undefined'}},
            'fullRuntimeIdentity': copy.deepcopy(runtime), 'ownershipBeforeResume': True, 'serverUnavailable': True}
        self.data[P + 'controller.log'] = b'SYNTHETIC unit-test controller receipt\n'
        self.data[P + 'original.cjs'] = (repo / 'tools/fixtures/mouse637-performance-002-stress.cjs').read_bytes()
        self.data[P + 'parent.cjs'] = (repo / 'tools/fixtures/mouse637-performance-002-native.cjs').read_bytes()
        self.data[P + 'adapted.cjs'] = adapted
        native = {'ok': True, 'version': E['VERSION'], 'platform': 'darwin', 'arch': 'arm64'}
        self.data['mouse-631-native.json'] = {**native, 'pid': self.pid, 'budgetMs': 350000, 'elapsedMs': 47000,
            'physicalUserDeviceVerified': False, 'liveExternalAccountsVerified': False,
            'stages': [{'name': name, 'ok': True, 'elapsedMs': time} for name, time in
                       [('taskOnly', 10000), ('fiftyTabs', 30000), ('stationaryMedia', 5000)]]}
        self.data['mouse-631-task.json'] = {**native, 'budgetMs': 65000, 'elapsedMs': 9500, 'restored': True}
        slide = {'phase': 'complete', 'strategy': 'live', 'presented': True,
                 'snapshotCaptures': 0, 'animated': False, 'decoded': False}
        self.data['mouse-631-stress.json'] = {**native, 'budgetMs': 200000, 'elapsedMs': 29500,
            'restored': True, 'renderFailures': [], 'baselineComparison': {'performed': False},
            'stages': [{'ownedPageCount': pages, 'switchCount': count,
                'switches': [{'sequence': n + 1, 'elapsedMs': 50 + n, 'slide': slide.copy()} for n in range(count)],
                'processesBefore': [{'pid': self.pid, 'type': 'Browser'}, {'pid': self.shell, 'type': 'Tab'}],
                'processesAfter': [{'pid': self.pid, 'type': 'Browser'}, {'pid': self.shell, 'type': 'Tab'}]}
                for pages, count in [(20, 5), (50, 10)]]}
        self.data['mouse-631-acceptance.json'] = {**native, 'physicalUserDeviceVerified': False,
            'externalAccountsVerified': False, 'task': {'themes': 2}, 'stress': {'workloads': [20, 50], 'switches': 15}}
        self.data['mouse-631-native.log'] = ('SYNTHETIC UNIT TEST; NO NATIVE EXECUTION\n' + '\n'.join(E['MARKERS']) +
            '\nMOUSE_NATIVE_PROCESS_RETURN pid=81001 code=0 elapsedMs=50000\n').encode()
        start = {'transferMode': 'ReturnAsStream', 'streamFormat': 'json', 'streamCompression': 'none',
            'bufferUsageReportingInterval': 1000, 'traceConfig': {'recordMode': 'recordUntilFull',
            'traceBufferSizeInKb': 16384, 'enableSampling': False, 'enableSystrace': False,
            'includedCategories': E['CATEGORIES']}}
        self.names = ['mouse637-trace-' + self.nonce + '-' + kind for kind in ('begin', 'end')]
        self.data[P + 'session.json'] = {**common, 'kind': 'mouse637-nonpublishing-performance-trace',
            'originalSha256': E['ORIGINAL_SHA'], 'adaptedSha256': source['adaptedSha256'],
            'versions': E['RUNTIME'].copy(), 'limits': E['LIMITS'].copy(), 'categories': E['CATEGORIES'].copy(), 'coverage': E['SCOPE'],
            'originalStressBudgetMs': 200000, 'fixtureStartedAt': 1000, 'fixtureDeadline': 201000,
            'clock': 'main.performance.now', 'errors': [], 'ok': True, 'collected': True,
            'listenerAttached': True, 'listenerRemoved': True, 'activeCapExceeded': False, 'outputCapExceeded': False,
            'streamClosed': True, 'streamEOF': True, 'loopCompleted': True, 'marksCleared': True,
            'mainPid': self.pid, 'shellPid': self.shell, 'shellWebContentsId': 1,
            'startSubmitted': True, 'startAcknowledged': True, 'startPendingAtDisposal': False,
            'browserVersion': {'protocolVersion': '1.3', 'product': 'Chrome/152.0.7977.130', 'revision': '@synthetic',
                               'userAgent': 'Synthetic unit-test fixture', 'jsVersion': E['RUNTIME']['v8']},
            'supported': {'categories': E['CATEGORIES'] + ['synthetic-extra']}, 'startParams': start,
            'startRequestedAt': 1109, 'startedAt': 1110.5, 'loopReadyAt': 1114, 'loopReturnAt': 1500,
            'endReason': 'loop-complete', 'endRequestedAt': 1503,
            'completion': {'at': 1506, 'dataLossOccurred': False, 'stream': 'synthetic-stream-1',
                           'traceFormat': 'json', 'streamCompression': 'none'},
            'finishedAt': 30500, 'finishedEpochMs': self.epoch + 45000,
            'marks': [{'kind': kind, 'name': name, 'startTime': time, 'now': time + .025,
                       'timeOrigin': self.epoch + 5000, 'clock': 'renderer.performance.now'}
                      for kind, name, time in zip(('begin', 'end'), self.names, (5.125, 300.125))],
            'bufferUsage': [{'at': 1200, 'eventCount': 0, 'percentFull': 0.01, 'value': 0.01}],
            'switches': copy.deepcopy(self.data['mouse-631-stress.json']['stages'][0]['switches'])}
        def command(method, params, start, end):
            return {'method': method, 'params': params, 'startedAt': start, 'endedAt': end, 'ok': True}
        self.commands = [command('Browser.getVersion', {}, 1100, 1101), command('Tracing.getCategories', {}, 1102, 1103),
            command('Tracing.start', start, 1110, 1111),
            command('Runtime.evaluate', {'expression': E['marker_expression'](self.names[0]), 'returnByValue': True}, 1112, 1113),
            command('Runtime.evaluate', {'expression': E['marker_expression'](self.names[1]), 'returnByValue': True}, 1501, 1502),
            command('Tracing.end', {}, 1504, 1505)]
        self.trace = {'traceEvents': [
            {'pid': self.pid, 'tid': 0, 'ph': 'M', 'name': 'process_name', 'args': {'name': 'Browser'}},
            {'pid': self.shell, 'tid': 0, 'ph': 'M', 'name': 'process_name', 'args': {'name': 'Renderer'}},
            {'pid': self.pid, 'tid': 1, 'ph': 'X', 'name': 'Synthetic main task', 'cat': 'toplevel', 'ts': 1000100, 'dur': 50},
            {'pid': self.shell, 'tid': 2, 'ph': 'I', 'name': self.names[0], 'cat': 'blink.user_timing', 'ts': 1000000,
             'args': {'data': {'startTime': 5.125}}},
            {'pid': self.shell, 'tid': 2, 'ph': 'I', 'name': self.names[1], 'cat': 'blink.user_timing', 'ts': 1295000,
             'args': {'data': {'startTime': 300.125}}},
            {'pid': self.shell, 'tid': 2, 'ph': 'X', 'name': 'Synthetic shell task', 'cat': 'devtools.timeline',
             'ts': 1000300, 'dur': 250}], 'metadata': {'syntheticUnitTest': True}}
        self.rechunk()
        pin = json.loads((repo / 'staging/mouse/6.0.37-arm64/pin.json').read_text())
        self.data[P + 'summary.json'] = {**native, 'schema': 1, 'kind': 'mouse637-nonpublishing-performance-summary',
            'diagnosticOnly': True, 'releaseAcceptance': False, 'source': E['SOURCE'], 'publisherSHA': publisher,
            'startedAt': self.epoch, 'finishedAt': self.epoch + 60000, 'executable': self.exe, 'appPath': self.app,
            'profile': self.profile, 'output': self.output, 'candidate': str(Path(self.output).parent / 'mouse637-release'),
            'wrapperSha256': digest((repo / 'tools/mouse637-performance-trace.py').read_bytes()),
            'controllerSha256': digest((repo / 'tools/mouse637-performance-trace.cjs').read_bytes()),
            'snapshotToolSha256': E['SNAPSHOT_SHA'], 'verifierSha256': E['VERIFIER_SHA'],
            'nativeValidatorSha256': E['NATIVE_READER_SHA'], 'nativeValidatorExitCode': 0,
            'originalFunctionASTs': E['FUNCTION_SHAS'].copy(),
            'pinSha256': digest((repo / 'staging/mouse/6.0.37-arm64/pin.json').read_bytes()),
            'budgetsMs': {'outer': 400000, 'native': 350000, 'stress': 200000, 'bootstrap': 30000},
            'packagesBefore': copy.deepcopy(pin['packages']), 'packagesAfter': copy.deepcopy(pin['packages']),
            'native': {'pid': self.pid, 'exitCode': 0, 'elapsedMs': 50000, 'log': 'mouse-631-native.log',
                       'requiredMarkers': E['MARKERS'].copy()},
            'launches': [{'phase': 'performance-trace', 'flag': E['FLAG'], 'pid': self.pid, 'nonce': self.nonce,
                'port': self.port, 'originalArgv': [self.exe, E['FLAG']], 'argv': self.argv, 'profile': self.profile,
                'addedEnvironment': {'MOUSE_637_PERFORMANCE_TRACE_NONCE': self.nonce}, 'bootstrapStartedAt': self.epoch + 1000,
                'bootstrapFinishedAt': self.epoch + 2200, 'controllerExitCode': 0, 'controllerPid': self.sidecar, 'processExitCode': 0}]}
        for label in ('before', 'after'):
            filename = 'mouse-637-feature-readiness-codesign-trace-' + label + '.log'
            self.data[filename] = b''
            self.data[P + 'summary.json']['installed' + label.capitalize()] = {
                'components': copy.deepcopy(E['COMPONENTS']), 'nativeInventory': sorted(k for k in E['COMPONENTS'] if k.endswith('.node')),
                'codesign': {'exitCode': 0, 'command': ['codesign', '--verify', '--deep', '--strict'], 'log': filename, 'logSha256': digest(b'')}}
        self.refresh()

    def rechunk(self, chunks=None, base64_flags=None, terminal_empty=True):
        """Bind actual synthetic raw bytes to genuine per-read reconstruction."""
        raw = encoded(self.trace) if not isinstance(self.trace, bytes) else self.trace
        self.data[P + 'data.json'] = raw
        if chunks is None:
            chunks = [raw] + ([b''] if terminal_empty else [])
        if base64_flags is None:
            base64_flags = [False] * len(chunks)
        session = self.data[P + 'session.json']
        commands = copy.deepcopy(self.commands)
        reads = []
        consumed = 0
        for index, (chunk, as_base64) in enumerate(zip(chunks, base64_flags)):
            requested = min(E['LIMITS']['readBytes'], max(1, E['LIMITS']['maxOutputBytes'] - consumed))
            sequence = len(commands) + 1
            commands.append({'sequence': sequence, 'method': 'IO.read', 'params': {'handle': 'synthetic-stream-1', 'size': requested},
                             'startedAt': 1507 + index * 2, 'endedAt': 1508 + index * 2, 'ok': True})
            returned = base64.b64encode(chunk) if as_base64 else chunk
            reads.append({'apiSequence': sequence, 'requestedSize': requested, 'base64Encoded': as_base64,
                          'eof': index == len(chunks) - 1, 'decodedBytes': len(chunk), 'returnedDataUTF8Bytes': len(returned),
                          'returnedDataSHA256': digest(returned), 'decodedSHA256': digest(chunk)})
            consumed += len(chunk)
        start = 1507 + len(chunks) * 2
        clear = '(()=>{for(const name of ' + json.dumps(self.names, separators=(',', ':')) + ')performance.clearMarks(name);return true;})()'
        commands.extend([{'method': 'IO.close', 'params': {'handle': 'synthetic-stream-1'}, 'startedAt': start, 'endedAt': start + 1, 'ok': True},
                         {'method': 'Runtime.evaluate', 'params': {'expression': clear, 'returnByValue': True},
                          'startedAt': start + 2, 'endedAt': start + 3, 'ok': True}])
        for index, command in enumerate(commands, 1):
            command['sequence'] = index
        session.update(api=commands, reads=reads, readCount=len(reads), outputBytes=len(raw),
                       trace={'filename': P + 'data.json', 'size': len(raw), 'sha256': digest(raw)})

    def refresh(self):
        """Rebind only byte envelopes, preserving every semantic mutation."""
        d = self.data
        acceptance = d['mouse-631-acceptance.json']
        acceptance.update(taskReportSHA256=digest(d['mouse-631-task.json']), stressReportSHA256=digest(d['mouse-631-stress.json']))
        d[P + 'native-validation.log'] = ('MOUSE_631_INDEPENDENT_EVIDENCE_PASS\n' +
            json.dumps(acceptance, ensure_ascii=False, sort_keys=True) + '\n').encode()
        control = d[P + 'controller.json']
        control.update(listenerReceiptSha256=digest(d[P + 'listener.json']), receiptSha256=digest(d[P + 'bootstrap.json']),
                       controllerSha256=digest((self.repo / 'tools/mouse637-performance-trace.cjs').read_bytes()))
        summary = d[P + 'summary.json']
        summary['launches'][0].update(receiptSha256=digest(d[P + 'bootstrap.json']), controllerReceiptSha256=digest(control))
        summary['native']['logSha256'] = digest(d['mouse-631-native.log'])
        summary['evidence'] = {name: {'size': len(encoded(value)), 'sha256': digest(value)}
                               for name, value in d.items() if name != P + 'summary.json'}

    def write(self, directory):
        self.refresh()
        for name, value in self.data.items():
            (directory / name).write_bytes(encoded(value))


class TraceEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.TemporaryDirectory(prefix='synthetic-mouse-trace-checker-')
        cls.repo = Path(cls.root.name) / 'publisher'
        cls.repo.mkdir()
        for name in E['TOOL_FILES']:
            destination = cls.repo / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(TOOLS.parent / name, destination)
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=cls.repo, stderr=subprocess.PIPE)
        git('init', '--quiet')
        git('add', '.')
        git('-c', 'user.name=Synthetic Unit Test', '-c', 'user.email=unit@example.invalid', 'commit', '--quiet', '-m', 'Synthetic checker fixture; never native evidence')
        cls.publisher = git('rev-parse', 'HEAD').decode().strip()
        script = 'const fs=require("node:fs"),m=require("./tools/mouse637-performance-trace.cjs");process.stdout.write(m.transform(fs.readFileSync("./tools/fixtures/mouse637-performance-002-stress.cjs","utf8")));'
        cls.adapted = subprocess.check_output(['node', '-e', script], cwd=cls.repo)
        cls.baseline = SyntheticProof(cls.repo, cls.publisher, cls.adapted)

    @classmethod
    def tearDownClass(cls):
        cls.root.cleanup()

    def check(self, proof, expected=True, after_write=None):
        with tempfile.TemporaryDirectory(prefix='synthetic-trace-raw-') as temporary:
            directory = Path(temporary)
            proof.write(directory)
            if after_write:
                after_write(directory)
            call = lambda: E['verify'](directory, tools_root=self.repo / 'tools', publisher_sha=self.publisher)
            if expected:
                return call()
            with self.assertRaises((ValueError, KeyError, TypeError, AttributeError, UnicodeError, subprocess.CalledProcessError)):
                call()

    def mutant(self, path, value):
        proof = copy.deepcopy(self.baseline)
        change(proof.data, path, value)
        self.check(proof, False)

    def test_full_positive_is_diagnostic_only_with_zero_event_count_and_optional_metadata(self):
        result = self.check(copy.deepcopy(self.baseline))
        self.assertTrue(result['ok'])
        self.assertTrue(result['diagnosticOnly'])
        for key in ('releaseAcceptance', 'causalConclusionEstablished', 'nativeExecutedByReader', 'packagesRehashedByReader'):
            self.assertFalse(result[key])
        self.assertEqual(result['trace']['flowEventCounts'], {'s': 0, 't': 0, 'f': 0})
        self.assertEqual(result['trace']['rendererMarkerDurationMilliseconds'], 295)
        self.assertEqual(len(result['committedTools']), len(E['TOOL_FILES']))
        self.assertEqual(set(result['inputs']), set(self.baseline.data))
        proof = copy.deepcopy(self.baseline)
        proof.data[P + 'session.json']['browserVersion']['jsVersion'] = '15.2.124.28'
        proof.data[P + 'session.json']['completion'].update(traceFormat=None, streamCompression=None)
        proof.data[P + 'session.json']['bufferUsage'] = []
        # An actual trace interval may begin before our mark and overlap it.
        proof.trace['traceEvents'][2].update(ts=999999, dur=201)
        # Actual pinned Perfetto serializes this same Blink double with16g.
        value = 1.2345678901234567
        serialized = float(format(value, '.16g'))
        self.assertNotEqual(value, serialized)
        proof.data[P + 'session.json']['marks'][0]['startTime'] = value
        proof.trace['traceEvents'][3]['args']['data']['startTime'] = serialized
        proof.rechunk()
        self.check(proof)

    def test_original_deadline_uses_exact_construction_without_float_cancellation(self):
        proof = copy.deepcopy(self.baseline)
        session = proof.data[P + 'session.json']
        started = 99912.34560709613
        self.assertNotEqual((started + 200000) - started, 200000)
        session['fixtureStartedAt'] = started
        session['fixtureDeadline'] = started + 200000
        for key in ('startRequestedAt', 'startedAt', 'loopReadyAt', 'loopReturnAt', 'endRequestedAt', 'finishedAt'):
            session[key] += 100000
        for command in session['api']:
            command['startedAt'] += 100000
            command['endedAt'] += 100000
        session['completion']['at'] += 100000
        for event in session['bufferUsage']:
            event['at'] += 100000
        self.check(proof)
        session['fixtureDeadline'] += 1
        self.check(proof, False)

    def test_real_current_module_and_committed_byte_bindings(self):
        for name in ('parent', 'original', 'adapted'):
            proof = copy.deepcopy(self.baseline)
            proof.data[P + name + '.cjs'] += b'\n// synthetic mutation\n'
            with self.subTest(name=name):
                self.check(proof, False)
        for path, value in [
            ((P + 'summary.json', 'controllerSha256'), '0' * 64),
            ((P + 'summary.json', 'wrapperSha256'), '0' * 64),
            ((P + 'summary.json', 'snapshotToolSha256'), '0' * 64),
            ((P + 'summary.json', 'pinSha256'), '0' * 64),
            ((P + 'summary.json', 'verifierSha256'), '0' * 64),
            ((P + 'summary.json', 'nativeValidatorSha256'), '0' * 64),
            ((P + 'summary.json', 'installedAfter', 'components', 'Contents/Resources/app.asar', 'sha256'), '0' * 64),
            ((P + 'summary.json', 'packagesAfter', 'Mouse-Browser-6.0.37-mac-arm64.zip', 'size'), 1),
        ]:
            with self.subTest(path=path):
                self.mutant(path, value)

    def test_rehashed_foreign_runtime_and_receipt_owners_fail(self):
        cases = [
            ((P + 'summary.json', 'publisherSHA'), '0' * 40), ((P + 'summary.json', 'source'), '0' * 40),
            ((P + 'summary.json', 'releaseAcceptance'), True), ((P + 'summary.json', 'diagnosticOnly'), False),
            ((P + 'summary.json', 'launches', 0, 'controllerPid'), 81001),
            ((P + 'summary.json', 'launches', 0, 'processExitCode'), 1),
            ((P + 'config.json', 'nonce'), 'a' * 64), ((P + 'config.json', 'deadlineEpochMs'), 1795350099999),
            ((P + 'config.json', 'receipt'), '/tmp/foreign.json'),
            ((P + 'bootstrap.json', 'parentBytesDelegated'), False), ((P + 'bootstrap.json', 'stressStillDeferred'), False),
            ((P + 'bootstrap.json', 'receiptBeforeParentInvocation'), False), ((P + 'bootstrap.json', 'inspectorUrl'), 'ws://127.0.0.1/live'),
            ((P + 'module.json', 'applications'), 2), ((P + 'module.json', 'parentLoads'), 0),
            ((P + 'module.json', 'loaderRestored'), False), ((P + 'module.json', 'receiptBeforeStressInvocation'), False),
            ((P + 'module.json', 'compileStartedAt'), 1795350000001),
            ((P + 'controller.json', 'serverUnavailable'), False), ((P + 'controller.json', 'ownershipBeforeResume'), False),
            ((P + 'controller.json', 'fullRuntimeIdentity', 'pid'), 89999),
            ((P + 'controller.json', 'fullRuntimeIdentity', 'argv'), [self.baseline.exe, '--mouse-636-retained-smoke']),
            ((P + 'controller.json', 'earlyRuntimeIdentity', 'availability', 'pid'), 'number'),
            ((P + 'listener.json', 'stdout'), 'p99999\nf17\nPTCP\nn127.0.0.1:49221\nTST=LISTEN\n'),
            ((P + 'listener.json', 'stderr'), 'permission denied'),
            ((P + 'listener.json', 'stdout'), self.baseline.data[P + 'listener.json']['stdout'] + 'f18\nPTCP\nn127.0.0.1:49221\nTST=LISTEN\n'),
        ]
        for path, value in cases:
            with self.subTest(path=path):
                self.mutant(path, value)
        proof = copy.deepcopy(self.baseline)
        runtime = copy.deepcopy(proof.data[P + 'controller.json']['fullRuntimeIdentity'])
        runtime['availability'] = {'pid': 'number', 'execPath': 'string', 'argv': 'object'}
        proof.data[P + 'controller.json']['earlyRuntimeIdentity'] = runtime
        self.check(proof)

    def test_rehashed_loss_caps_errors_and_phase_deadlines_fail(self):
        s = P + 'session.json'
        cases = [
            ((s, 'completion', 'dataLossOccurred'), True), ((s, 'completion', 'traceFormat'), 'proto'),
            ((s, 'completion', 'streamCompression'), 'gzip'), ((s, 'completion', 'at'), 1499),
            ((s, 'bufferUsage', 0, 'percentFull'), 1), ((s, 'bufferUsage', 0, 'value'), 1),
            ((s, 'bufferUsage', 0, 'eventCount'), -1), ((s, 'bufferUsage'), [{}] * 33),
            ((s, 'activeCapExceeded'), True), ((s, 'outputCapExceeded'), True), ((s, 'streamEOF'), False),
            ((s, 'streamClosed'), False), ((s, 'marksCleared'), False), ((s, 'listenerRemoved'), False),
            ((s, 'startAcknowledged'), False), ((s, 'startPendingAtDisposal'), True),
            ((s, 'startRejected'), True), ((s, 'startWaitTimedOut'), True),
            ((s, 'lateStartAcknowledgment'), True), ((s, 'errors'), [{'where': 'stop', 'message': 'lost', 'at': 1510}]),
            ((s, 'endReason'), 'active-cap'), ((s, 'fixtureDeadline'), 301000),
            ((s, 'limits', 'activeMs'), 21000), ((s, 'supported', 'categories'), E['CATEGORIES'][:-1]),
            ((s, 'categories'), ['*']), ((s, 'browserVersion', 'product'), 'Chrome/151.0.0.0'),
            ((s, 'browserVersion', 'jsVersion'), '15.2'), ((s, 'versions', 'chrome'), '153.0.0.0'),
            ((s, 'api', 0, 'startedAt'), -10000), ((s, 'api', 7, 'endedAt'), 17000),
            ((s, 'finishedAt'), 201001), ((s, 'api', 2, 'params', 'transferMode'), 'ReportEvents'),
        ]
        for path, value in cases:
            with self.subTest(path=path):
                self.mutant(path, value)
        proof = copy.deepcopy(self.baseline)
        proof.data['mouse-631-native.log'] += b'MOUSE_637_DIAGNOSTIC_TRACE_SAVE_FAILED late receipt\n'
        self.check(proof, False)

    def test_actual_read_stream_reconstruction_base64_short_reads_and_empty_eof(self):
        proof = copy.deepcopy(self.baseline)
        raw = encoded(proof.trace)
        proof.rechunk([raw[:30], raw[30:], b''], [True, False, False])
        self.check(proof)
        proof.rechunk([raw], [True], terminal_empty=False)
        self.check(proof)
        s = P + 'session.json'
        for path, value in [
            ((s, 'reads', 0, 'base64Encoded'), True), ((s, 'reads', 0, 'base64Encoded'), 'false'),
            ((s, 'reads', 0, 'eof'), True), ((s, 'reads', 1, 'eof'), False),
            ((s, 'reads', 0, 'decodedBytes'), 0), ((s, 'reads', 0, 'decodedBytes'), 262145),
            ((s, 'reads', 0, 'returnedDataSHA256'), '0' * 64), ((s, 'reads', 0, 'decodedSHA256'), '0' * 64),
            ((s, 'reads', 0, 'returnedDataUTF8Bytes'), 1), ((s, 'reads', 0, 'apiSequence'), 8),
            ((s, 'api', 6, 'params', 'handle'), 'foreign'), ((s, 'api', -2, 'params', 'handle'), 'foreign'),
            ((s, 'api', 6, 'params', 'size'), 10 * 1024 * 1024), ((s, 'readCount'), 257),
            ((s, 'outputBytes'), 67108865), ((s, 'trace', 'sha256'), '0' * 64),
        ]:
            with self.subTest(path=path):
                self.mutant(path, value)

    def test_rehashed_trace_json_and_actual_nonce_timing_coverage_fail_closed(self):
        mutations = [
            lambda t: t['traceEvents'].clear(),
            lambda t: t['traceEvents'].pop(0),
            lambda t: t['traceEvents'].pop(2),
            lambda t: t['traceEvents'].pop(3),
            lambda t: t['traceEvents'].append(copy.deepcopy(t['traceEvents'][3])),
            lambda t: t['traceEvents'][3].update(pid=89999),
            lambda t: t['traceEvents'][4].update(tid=3),
            lambda t: t['traceEvents'][4].update(ts=999999),
            lambda t: t['traceEvents'][3].update(cat='toplevel'),
            lambda t: t['traceEvents'][3].update(name='mouse637-trace-foreign-begin'),
            lambda t: t['traceEvents'][3].update(ph='M'),
            lambda t: t['traceEvents'][3]['args']['data'].update(startTime=5.126),
            lambda t: t['traceEvents'][3].pop('args'),
            lambda t: t['traceEvents'][2].update(ts='100'),
            lambda t: t['traceEvents'][2].update(ts=999900, dur=50),
            lambda t: t['traceEvents'][5].update(ts=1295001),
            lambda t: t['traceEvents'].pop(5),
        ]
        for index, mutation in enumerate(mutations):
            proof = copy.deepcopy(self.baseline)
            mutation(proof.trace)
            proof.rechunk()
            with self.subTest(mutation=index):
                self.check(proof, False)
        for path, value in [
            ((P + 'session.json', 'marks', 0, 'clock'), 'Date.now'),
            ((P + 'session.json', 'marks', 1, 'timeOrigin'), 2),
            ((P + 'session.json', 'marks', 0, 'now'), 600),
            ((P + 'session.json', 'marks', 1, 'startTime'), 2),
            ((P + 'session.json', 'api', 3, 'params', 'expression'), 'performance.mark("foreign")'),
            ((P + 'session.json', 'api', -1, 'params', 'expression'), 'performance.clearMarks()'),
        ]:
            with self.subTest(path=path):
                self.mutant(path, value)

    def test_rehashed_original_workload_and_process_identity_must_match(self):
        cases = [
            (('mouse-631-native.json', 'pid'), 89999), (('mouse-631-native.json', 'stages', 2, 'ok'), False),
            (('mouse-631-native.json', 'elapsedMs'), 350001), (('mouse-631-task.json', 'restored'), False),
            (('mouse-631-stress.json', 'renderFailures'), ['crashed']),
            (('mouse-631-stress.json', 'baselineComparison', 'performed'), True),
            (('mouse-631-stress.json', 'stages', 0, 'processesBefore', 0, 'pid'), 89999),
            (('mouse-631-stress.json', 'stages', 0, 'processesAfter', 1, 'pid'), 89999),
            (('mouse-631-stress.json', 'stages', 0, 'processesBefore', 1, 'type'), 'GPU'),
            (('mouse-631-stress.json', 'stages', 0, 'switches', 0, 'elapsedMs'), 100),
            (('mouse-631-stress.json', 'stages', 1, 'ownedPageCount'), 20),
            (('mouse-631-acceptance.json', 'ok'), False),
            ((P + 'summary.json', 'nativeValidatorExitCode'), 1), ((P + 'summary.json', 'native', 'elapsedMs'), 400001),
        ]
        for path, value in cases:
            with self.subTest(path=path):
                self.mutant(path, value)
        for old, new in [(b'pid=81001', b'pid=99999'), (b'code=0', b'code=1'),
                         (b'MOUSE_631_FIFTY_TABS_FIVE_DESKTOPS_NATIVE_PASS', b'OMITTED')]:
            proof = copy.deepcopy(self.baseline)
            proof.data['mouse-631-native.log'] = proof.data['mouse-631-native.log'].replace(old, new)
            self.check(proof, False)

    def test_malformed_partial_and_nonfinite_raw_cannot_pass_rehashed_envelopes(self):
        for raw in (b'{"traceEvents": [', b'{"traceEvents":[],"traceEvents":[]}', b'{"traceEvents":[],"x":NaN}', b'[]', b'\xff'):
            proof = copy.deepcopy(self.baseline)
            proof.trace = raw
            proof.rechunk(base64_flags=[True, True])
            with self.subTest(raw=raw):
                self.check(proof, False)
        self.check(copy.deepcopy(self.baseline), False, lambda d: (d / (P + 'module.json')).unlink())
        self.check(copy.deepcopy(self.baseline), False, lambda d: (d / (P + 'data.json')).write_bytes(b'{}'))

    def test_current_tool_bytes_and_explicit_commit_are_required(self):
        file = self.repo / 'tools/mouse637-performance-trace.cjs'
        original = file.read_bytes()
        try:
            file.write_bytes(original + b'\n// mutated after review\n')
            self.check(copy.deepcopy(self.baseline), False)
        finally:
            file.write_bytes(original)
        proof = copy.deepcopy(self.baseline)
        with tempfile.TemporaryDirectory(prefix='synthetic-wrong-commit-') as temporary:
            proof.write(Path(temporary))
            with self.assertRaises(ValueError):
                E['verify'](temporary, tools_root=self.repo / 'tools', publisher_sha='0' * 40)


if __name__ == '__main__':
    unittest.main()
