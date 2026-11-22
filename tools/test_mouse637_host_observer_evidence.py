#!/usr/bin/env python3
"""Synthetic adversarial contracts, never native execution or release acceptance."""
import ast
import copy
import datetime
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import struct
import subprocess
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parent
E = runpy.run_path(str(TOOLS / 'mouse637-host-observer-evidence.py'))
PREFIX = E['PREFIX']
ENC = lambda value: (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode()
SHA = E['sha']
ROOT = '/Users/runner/work/OSMINOG-Releases/OSMINOG-Releases'
OUTPUT = ROOT + '/mouse637-release'
TEMP = '/Users/runner/work/_temp'
EXE = TEMP + '/Установка Mouse/Mouse Browser.app/Contents/MacOS/Mouse Browser'
BASE_APP = TEMP + '/mouse637-baseline-synthetic'
BASE_EXE = BASE_APP + '/Installed previous Mouse/Mouse Browser.app/Contents/MacOS/Mouse Browser'
EPOCH = 1795350000000000


def utc(microseconds):
    return (datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(microseconds=microseconds)).isoformat()


def receipt(data, filename=None):
    return {**({'filename': filename} if filename is not None else {}), 'size': len(data), 'sha256': SHA(data)}


def serial_stream(rows, *, refresh=True):
    """Rebind checksums/counts after a mutation, leaving semantic faults intact."""
    rows = copy.deepcopy(rows)
    if refresh:
        for index, row in enumerate(rows):
            row['sequence'] = index
        rows[-1]['recordCount'] = rows[-1]['storedRecordCount'] = len(rows) - 2
    prefix = b''.join(ENC(row) for row in rows[:-1])
    if refresh:
        rows[-1]['payloadBytesBeforeEOF'] = len(prefix)
    return prefix + ENC(rows[-1])


def stream_fixture(launch):
    phase = launch['phase']
    start = 10000000000 + (10000000000 if phase == 'candidate' else 0)
    end = start + 1000000000
    root_birth = start - 100000
    epoch = launch['launchBeforeEpochUs'] + 100
    rows = [{'type': 'header', 'sequence': 0, 'schema': 2, 'kind': 'mouse637-host-observer',
             'phase': phase, 'nonce': launch['nonce'], 'samplerPid': launch['helperPid'], 'rootPid': launch['pid'],
             'expectedRootParentPid': launch['parentPid'], 'uid': launch['uid'], 'expectedRootPath': launch['expectedRootPath'],
             'launchBeforeEpochUs': launch['launchBeforeEpochUs'], 'launchAfterEpochUs': launch['launchAfterEpochUs'],
             'budgetMs': launch['budgetMs'], 'intervalMs': 250, 'limits': copy.deepcopy(E['LIMITS']),
             'clock': 'mach_absolute_time', 'counterUnits': 'mach_absolute_time', 'timebaseNumer': 1, 'timebaseDenom': 1,
             'logicalCpus': 3, 'kernel': '24.6.0', 'machine': 'arm64',
             'rootImagePolicy': {'kind': 'fixed', 'parentInitial': None, 'parentRecheck': None}}]

    def identity(index, pid, parent, path, at, birth):
        return {'type': 'identity', 'identityIndex': index, 'imageIndex': index, 'pid': pid,
                'ppid': launch['parentPid'] if parent == -1 else (launch['pid'] if parent == 0 else 101),
                'uid': launch['uid'], 'parentIndex': parent, 'startSec': (epoch + index) // 1000000,
                'startUsec': (epoch + index) % 1000000, 'startAbstime': birth,
                'uuid': f'{index + 1:032x}', 'path': path, 'readStartMach': at, 'readEndMach': at + 100}

    states = [identity(0, launch['pid'], -1, launch['expectedRootPath'], start, root_birth)]
    rows.append(states[0])
    if phase == 'baseline':
        rows[0]['rootImagePolicy'] = {
            'kind': 'python-parent-runtime', 'parentRecheck': None,
            'parentInitial': {'pid': launch['parentPid'], 'ppid': 7, 'uid': launch['uid'],
                              'startSec': (epoch - 10000000) // 1000000, 'startUsec': 0,
                              'startAbstime': root_birth - 100000000,
                              'uuid': 'e' * 32,
                              'path': '/Library/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python',
                              'readStartMach': start + 200, 'readEndMach': start + 300},
        }
    child_path = BASE_EXE if phase == 'baseline' else TEMP + '/Установка Mouse/Mouse Browser.app/Contents/Frameworks/Mouse Browser Helper (Renderer).app/Contents/MacOS/Mouse Browser Helper (Renderer)'
    states.append(identity(1, 101 if phase == 'baseline' else 201, 0, child_path, start + 1400, start + 1200))
    if phase == 'baseline':
        states.append(identity(2, 102, 1, BASE_APP + '/Installed previous Mouse/Mouse Browser.app/Contents/Frameworks/Mouse Browser Helper (Renderer).app/Contents/MacOS/Mouse Browser Helper (Renderer)',
                               start + 1800, start + 1600))
    for cycle in range(4):
        scheduled = start + 1000 + cycle * 250000000
        rows.append({'type': 'host', 'scheduledMach': scheduled, 'readStartMach': scheduled, 'readEndMach': scheduled + 100,
                     'cpuTicks': [100 + cycle, 200 + cycle, 300 + cycle, 400 + cycle],
                     'selfUserUs': 100 * (cycle + 1), 'selfSystemUs': 50 * (cycle + 1)})
        if cycle == 3:
            rows.append({'type': 'exit', 'identityIndex': 0, 'readStartMach': scheduled + 200, 'readEndMach': scheduled + 300,
                         'code': 3, 'otherPid': 0, 'observedStartSec': 0, 'observedStartUsec': 0, 'observedStartAbstime': 0})
            continue
        for index, state in enumerate(states):
            if cycle == 0 and index:
                rows.append(state)
            at = scheduled + 200 + index * 400
            if cycle == 0 and index:
                at = state['readEndMach'] + 100
            rows.append({'type': 'sample', 'identityIndex': index, 'imageIndex': index,
                         'readStartMach': at, 'readEndMach': at + 100,
                         'userTime': 10000 + cycle * 1000, 'systemTime': 20000 + cycle * 1000,
                         # Intentionally smaller than CPU: not a wait timer.
                         'runnableTime': 200 + cycle, 'startAbstime': state['startAbstime']})
    rows.append({'type': 'eof', 'ok': True, 'reason': 'root-exited', 'rootGone': True, 'errorCode': 0,
                 'recordCount': 0, 'storedRecordCount': 0, 'droppedRecords': 0, 'ownedCount': len(states), 'imageCount': len(states),
                 'samplingStartMach': start, 'samplingEndMach': end, 'observedDurationMach': end - start,
                 'deadlineMach': root_birth + launch['budgetMs'] * 1000000, 'missedIntervals': 0, 'maxReadTicks': 100, 'maxLagTicks': 0,
                 'selfUserUs': 3000, 'selfSystemUs': 2000, 'selfCpuUs': 5000,
                 'selfCpuLimitNumerator': 1, 'selfCpuLimitDenominator': 100, 'withinSelfCpuLimit': True,
                 'discoveryGone': 2, 'discoveryMoved': 1, 'dumpStartMach': end + 100,
                 'dumpEndMach': end + 1000000, 'selfCpuAccounting': 'startup+collection+flushed-data-before-eof',
                 'unmeasuredResidual': 'eof-write-close-free', 'payloadBytesBeforeEOF': 0})
    return json.loads(ENC(launch)), [json.loads(line) for line in serial_stream(rows).splitlines()]


def runtime_handoff(rows, *, initially_runtime=False):
    """Synthetic actual-schema witnesses; no Python/native process is launched."""
    rows = copy.deepcopy(rows)
    policy = rows[0]['rootImagePolicy']
    parent = policy['parentInitial']
    root = rows[1]
    if initially_runtime:
        root.update(path=parent['path'], uuid=parent['uuid'])
        return rows
    sample_at = next(i for i, row in enumerate(rows) if row['type'] == 'sample' and
                     row['identityIndex'] == 0 and row['userTime'] == 11000)
    sample = rows[sample_at]
    image = {**root, 'type': 'image', 'imageIndex': rows[-1]['imageCount'], 'path': parent['path'], 'uuid': parent['uuid'],
             'readStartMach': sample['readStartMach'], 'readEndMach': sample['readEndMach']}
    rows.insert(sample_at, image)
    policy['parentRecheck'] = {**parent, 'readStartMach': image['readEndMach'] + 10, 'readEndMach': image['readEndMach'] + 110}
    for row in rows[sample_at + 1:]:
        if row['type'] == 'sample' and row['identityIndex'] == 0:
            row['imageIndex'] = image['imageIndex']
    rows[-1]['imageCount'] += 1
    return rows


def fixture(code_root, publisher):
    data = {}
    code = {name: SHA((code_root / name).read_bytes()) for name in set(E['TOOLS']) | set(E['OLD_CODE'])}
    binary_name = PREFIX + 'sampler.bin'
    # A synthetic minimal arm64 Mach-O container, never executed.
    binary = struct.pack('<8I', 0xFEEDFACF, 0x0100000C, 0, 2, 1, 24, 0, 0) + struct.pack('<2I', 0x1B, 24) + bytes(16)
    data[binary_name] = binary
    data['mouse-verify.py'] = (code_root / 'fixtures/mouse637-readiness-002-verifier.py').read_bytes()
    data['mouse-637-baseline-performance.py'] = (code_root / 'fixtures/mouse637-host-002-baseline-performance.py').read_bytes()
    compile_command = ['xcrun', 'clang', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', ROOT + '/tools/mouse637-host-observer.c', '-o', OUTPUT + '/' + binary_name]
    commands = [(['git', 'rev-parse', 'HEAD'], publisher + '\n')]
    for name in ('mouse637-host-observer.c', 'mouse637-host-observer-build.py'):
        original = (code_root / name).read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(original)).encode() + b'\x00' + original).hexdigest()
        commands.extend([(['git', 'hash-object', ROOT + '/tools/' + name], blob + '\n'),
                         (['git', 'rev-parse', 'HEAD:tools/' + name], blob + '\n')])
    commands.extend([(['xcrun', 'clang', '--version'], 'Apple clang synthetic contract fixture\n'),
                     (['xcrun', '--show-sdk-path'], '/Applications/Xcode.app/Contents/Developer/SDKs/MacOSX.sdk\n'),
                     (['xcrun', '--show-sdk-version'], '15.5\n'), (compile_command, ''),
                     (['xcrun', 'lipo', '-archs', OUTPUT + '/' + binary_name], 'arm64\n')])
    build = {'schema': 1, 'kind': 'mouse637-host-observer-build', 'ok': True, 'platform': 'darwin', 'arch': 'arm64',
             'publisherSHA': publisher, 'errors': [], 'startedAtUTC': utc(EPOCH - 4000000), 'finishedAtUTC': utc(EPOCH - 3000000),
             'commands': [{'argv': argv, 'returncode': 0, 'output': output} for argv, output in commands],
             'command': compile_command, 'compilerVersion': commands[5][1].strip(), 'sdkPath': commands[6][1].strip(),
             'sdkVersion': commands[7][1].strip(), 'binary': {**receipt(binary, binary_name), 'path': OUTPUT + '/' + binary_name, 'arch': 'arm64'}}
    for field, name in [('source', 'mouse637-host-observer.c'), ('builder', 'mouse637-host-observer-build.py')]:
        build[field] = {'path': 'tools/' + name, **receipt((code_root / name).read_bytes())}
    data[PREFIX + 'build.json'] = ENC(build)
    summary = {'schema': 1, 'kind': 'mouse637-external-host-observer-summary', 'source': E['SOURCE'], 'version': '6.0.37',
               'publisherSHA': publisher, 'platform': 'darwin', 'arch': 'arm64', 'runId': '45099999999', 'runAttempt': '1',
               'job': 'mouse-release', 'pid': 55, 'uid': 501, 'ok': True, 'originalSucceeded': True, 'releaseAcceptance': False,
               'causalConclusionEstablished': False, 'startedAtEpochUs': EPOCH - 2000000, 'finishedAtEpochUs': EPOCH + 20000000,
               'wrapperSha256': code['mouse637-host-observer.py'], 'samplerSourceSha256': code['mouse637-host-observer.c'],
               'innerWrapperSha256': E['OLD_CODE']['mouse637-guest-input-observer.py'],
               'verifierSha256': E['OLD_CODE']['fixtures/mouse637-readiness-002-verifier.py'], 'baselineHelperSha256': E['BASELINE_SHA'],
               'sampler': receipt(binary, binary_name), 'build': receipt(data[PREFIX + 'build.json'], PREFIX + 'build.json'),
               'executable': EXE, 'output': OUTPUT, 'launches': []}
    for index, phase in enumerate(E['PHASES']):
        name = PREFIX + phase
        before = EPOCH + index * 10000000
        mono = 100000000000 + index * 10000000000
        exe = '/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11' if phase == 'baseline' else EXE
        argv = [exe, OUTPUT + '/mouse-637-baseline-performance.py', '--output', OUTPUT] if phase == 'baseline' else [exe, '--mouse-631-smoke']
        row = {'phase': phase, 'budgetMs': E['BUDGETS'][phase], 'pid': 100 + index * 100, 'parentPid': 55, 'uid': 501,
               'argv': argv, 'expectedRootPath': exe, 'nonce': ('a' if phase == 'baseline' else 'b') * 64,
               'originalLog': 'mouse-637-baseline-performance.log' if phase == 'baseline' else 'mouse-631-native.log',
               'profile': None if phase == 'baseline' else TEMP + '/mouse-profiles/task-stress-631',
               'launchBeforeEpochUs': before, 'launchAfterEpochUs': before + 1000,
               'launchBeforeMonotonicNs': mono, 'launchAfterMonotonicNs': mono + 1000000,
               'helperPid': None, 'helperExitCode': None}
        command = [OUTPUT + '/' + binary_name, phase, str(row['pid']), '55', exe, str(before), str(before + 1000),
                   str(row['budgetMs']), row['nonce'], OUTPUT + '/' + name + '.jsonl', '501']
        config = {'schema': 1, 'kind': 'mouse637-host-observer-config', 'source': E['SOURCE'], 'publisherSHA': publisher,
                  **row, 'sampler': OUTPUT + '/' + binary_name, 'samplerSha256': SHA(binary),
                  'output': OUTPUT + '/' + name + '.jsonl', 'helperArgv': command}
        data[name + '.json'] = ENC(config)
        data[name + '.log'] = b''
        row.update(helperPid=300 + index, helperExitCode=0, completed=True, originalExitCodeObserved=0, originalExitCodeAtSamplerExit=None,
                   finishedMonotonicNs=mono + 2000000000)
        _launch, rows = stream_fixture(row)
        data[name + '.jsonl'] = serial_stream(rows)
        for field, suffix in [('config', '.json'), ('raw', '.jsonl'), ('helperLog', '.log')]:
            row[field] = receipt(data[name + suffix], name + suffix)
        summary['launches'].append(row)
    marker_log = ''.join(marker + '\n' for marker in E['MARKERS'])
    data['mouse-637-baseline-performance/mouse-631-native.log'] = marker_log.encode()
    data['mouse-637-baseline-performance.log'] = (marker_log + 'MOUSE_637_BASELINE_PERFORMANCE_PASS\nMOUSE_NATIVE_PROCESS_RETURN pid=100 code=0 elapsedMs=2000\n').encode()
    data['mouse-631-native.log'] = (marker_log + 'MOUSE_NATIVE_PROCESS_RETURN pid=200 code=0 elapsedMs=2000\n').encode()
    for phase, version, pid, other_pid in [('baseline', '6.0.36', 101, 102), ('candidate', '6.0.37', 200, 201)]:
        prefix = 'mouse-637-baseline-performance/' if phase == 'baseline' else ''
        native = {'ok': True, 'version': version, 'platform': 'darwin', 'arch': 'arm64', 'pid': pid, 'budgetMs': 350000,
                  'elapsedMs': 600, 'stages': [{'name': name, 'ok': True, 'elapsedMs': 200} for name in ('taskOnly', 'fiftyTabs', 'stationaryMedia')]}
        metrics = [{'pid': pid, 'type': 'Browser'}, {'pid': other_pid, 'type': 'Tab'}]
        stress = {'ok': True, 'version': version, 'platform': 'darwin', 'arch': 'arm64', 'budgetMs': 200000, 'elapsedMs': 500,
                  'stages': [{'ownedPageCount': pages, 'processesBefore': metrics, 'processesAfter': metrics} for pages in (20, 50)]}
        data[prefix + 'mouse-631-native.json'] = ENC(native)
        data[prefix + 'mouse-631-stress.json'] = ENC(stress)
    process = {'argv': [BASE_EXE, '--mouse-631-smoke'], 'startedAt': utc(EPOCH + 2000), 'pid': 101, 'exitCode': 0,
               'elapsedMs': 500, 'budgetMs': 400000, 'requiredMarkers': list(E['MARKERS']),
               'profile': BASE_APP + '/Isolated previous-version performance profile',
               'cwd': OUTPUT + '/mouse-637-baseline-performance', 'log': 'mouse-637-baseline-performance/mouse-631-native.log',
               'finishedAt': utc(EPOCH + 502000), 'logSha256': SHA(data['mouse-637-baseline-performance/mouse-631-native.log'])}
    data['mouse-637-baseline-process.json'] = ENC(process)
    baseline = {'schema': 1, 'kind': 'published-baseline-stress-run', 'version': '6.0.37', 'ok': True, 'platform': 'darwin', 'arch': 'arm64',
                'baselineVersion': '6.0.36', 'baselineSource': '7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3',
                'baseline': copy.deepcopy(E['BASELINE_PACKAGE']), 'rawDirectory': 'mouse-637-baseline-performance',
                'physicalUserDeviceVerified': False, 'process': process,
                'runner': {'runId': summary['runId'], 'runAttempt': '1', 'job': 'mouse-release', 'sha': publisher, 'system': 'Darwin', 'machine': 'arm64'},
                'executable': {'path': BASE_EXE, 'size': 52688, 'sha256': 'aa3f21d6da8c42799fd603a5c896f1d2ba9004f2a30a9341541f6be3957d287f'},
                'files': {name: receipt(data[name]) for name in data if name.startswith('mouse-637-baseline-performance/')}}
    data['mouse-637-baseline-performance.json'] = ENC(baseline)
    for kind, name, wrapper in [('mouse637-passive-guest-input-summary', 'mouse-637-guest-input-observer-summary.json', 'mouse637-guest-input-observer.py'),
                                ('mouse637-external-feature-readiness', 'mouse-637-feature-readiness-summary.json', 'mouse637-feature-readiness.py')]:
        prior = {'schema': 1, 'kind': kind, 'source': E['SOURCE'], 'version': '6.0.37', 'ok': True, 'publisherSHA': publisher,
                 'platform': 'darwin', 'arch': 'arm64', 'output': OUTPUT, 'executable': EXE, 'wrapperSha256': E['OLD_CODE'][wrapper]}
        if 'feature' in kind:
            prior.update(before={'components': copy.deepcopy(E['COMPONENTS'])}, after={'components': copy.deepcopy(E['COMPONENTS'])})
        data[name] = ENC(prior)
    summary['evidence'] = {name: receipt(data[name]) for name in ('mouse-637-baseline-process.json', 'mouse-637-baseline-performance.json',
                           'mouse-637-baseline-performance/mouse-631-native.json', 'mouse-631-native.json',
                           'mouse-637-baseline-performance.log', 'mouse-631-native.log',
                           'mouse-637-guest-input-observer-summary.json', 'mouse-637-feature-readiness-summary.json')}
    data[PREFIX + 'summary.json'] = ENC(summary)
    return data


def rebind(data):
    """Rebind outer receipts so mutants reach independent semantic predicates."""
    summary = json.loads(data[PREFIX + 'summary.json'])
    for row in summary['launches']:
        for field, suffix in [('config', '.json'), ('raw', '.jsonl'), ('helperLog', '.log')]:
            name = PREFIX + row['phase'] + suffix
            if name in data:
                row[field] = receipt(data[name], name)
    build_name = PREFIX + 'build.json'
    summary['build'] = receipt(data[build_name], build_name)
    binary_name = PREFIX + 'sampler.bin'
    summary['sampler'] = receipt(data[binary_name], binary_name)
    baseline_name = 'mouse-637-baseline-performance.json'
    baseline = json.loads(data[baseline_name])
    baseline['files'] = {name: receipt(data[name]) for name in baseline['files'] if name in data}
    data[baseline_name] = ENC(baseline)
    for name in list(summary['evidence']):
        if name in data:
            summary['evidence'][name] = receipt(data[name])
    data[PREFIX + 'summary.json'] = ENC(summary)
    return data


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='mouse637-host-reader-contract-')
        cls.repo = Path(cls.temporary.name) / 'synthetic-git'
        cls.repo.mkdir()
        cls.tools = cls.repo / 'tools'
        for name in set(E['TOOLS']) | set(E['OLD_CODE']):
            destination = cls.tools / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(TOOLS / name, destination)
        pin = cls.repo / 'staging/mouse/6.0.37-arm64/pin.json'
        pin.parent.mkdir(parents=True)
        shutil.copyfile(TOOLS.parent / 'staging/mouse/6.0.37-arm64/pin.json', pin)
        subprocess.run(['git', 'init', '-q', str(cls.repo)], check=True)
        subprocess.run(['git', 'add', 'tools', 'staging'], cwd=cls.repo, check=True)
        subprocess.run(['git', '-c', 'user.name=Synthetic contract fixture', '-c', 'user.email=fixture@example.invalid',
                        'commit', '-q', '-m', 'Synthetic host reader test bytes only'], cwd=cls.repo, check=True)
        cls.publisher = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=cls.repo, text=True).strip()
        cls.good = fixture(cls.tools, cls.publisher)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def verify(self, data):
        with tempfile.TemporaryDirectory(prefix='mouse637-host-raw-fixture-') as directory:
            for name, value in data.items():
                path = Path(directory) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(value)
            return E['verify'](directory, tools_root=self.tools, publisher_sha=self.publisher)

    def change_json(self, data, name, change):
        value = json.loads(data[name]); change(value); data[name] = ENC(value)

    def test_complete_synthetic_evidence_and_no_acceptance_claim(self):
        result = self.verify(copy.deepcopy(self.good))
        self.assertTrue(result['ok'])
        self.assertFalse(result['releaseAcceptance'])
        self.assertFalse(result['originalReleaseGatesExecutedHere'])
        self.assertFalse(result['nativeExecutionPerformedHere'])
        self.assertFalse(result['causalConclusionEstablished'])
        self.assertEqual(result['phases']['baseline']['nativePid'], 101)
        self.assertEqual(result['phases']['candidate']['nativePid'], 200)
        self.assertEqual(result['phases']['baseline']['metricPidsWithoutSample'], [])
        self.assertIn('mouse-637-baseline-performance.py', result['inputs'])
        self.assertIn(PREFIX + 'sampler.bin', result['inputs'])

    def test_deep_header_and_launch_identity_mutations_reject(self):
        name = PREFIX + 'baseline.jsonl'
        cases = [('schema', 1), ('phase', 'candidate'), ('nonce', 'c' * 64), ('rootPid', 999), ('samplerPid', 999),
                 ('expectedRootParentPid', 999), ('uid', 0), ('expectedRootPath', '/foreign/python'),
                 ('budgetMs', 900001), ('intervalMs', 500), ('machine', 'x86_64'), ('timebaseNumer', 0),
                 ('timebaseDenom', 0), ('clock', 'epoch'), ('counterUnits', 'nanoseconds'), ('logicalCpus', True),
                 ('launchBeforeEpochUs', EPOCH + 2000)]
        for key, value in cases:
            with self.subTest(key=key):
                data = copy.deepcopy(self.good)
                rows = [json.loads(line) for line in data[name].splitlines()]
                rows[0][key] = value
                data[name] = serial_stream(rows)
                with self.assertRaises(ValueError): self.verify(rebind(data))
        for field, value in [('pid', 999), ('helperPid', 999), ('parentPid', 999), ('completed', False),
                             ('helperExitCode', 1), ('originalExitCodeObserved', None), ('originalExitCodeAtSamplerExit', 1), ('nonce', 'short'),
                             ('profile', '/wrong'), ('budgetMs', 500000)]:
            with self.subTest(launch=field):
                data = copy.deepcopy(self.good)
                self.change_json(data, PREFIX + 'summary.json', lambda s: s['launches'][1].__setitem__(field, value))
                with self.assertRaises(ValueError): self.verify(rebind(data))

    def test_jsonl_truncation_duplicates_caps_and_extra_records_reject(self):
        name = PREFIX + 'candidate.jsonl'
        raw = self.good[name]
        cases = {'no-newline': raw[:-1], 'missing-eof': raw[:raw.rfind(b'\n', 0, len(raw) - 1) + 1],
                 'extra': raw + b'{}\n', 'blank': raw + b'\n', 'duplicate-key': raw.replace(b'"schema": 2', b'"schema": 2, "schema": 2', 1),
                 'nan': raw.replace(b'"logicalCpus": 3', b'"logicalCpus": NaN', 1),
                 'oversize-line': raw.splitlines(keepends=True)[0] + b' ' * (E['MAX_LINE_BYTES'] + 1) + b'\n',
                 'out-of-order': raw.replace(b'"sequence": 2', b'"sequence": 999', 1)}
        for label, value in cases.items():
            with self.subTest(label=label):
                data = copy.deepcopy(self.good); data[name] = value
                with self.assertRaises(ValueError): self.verify(rebind(data))
        with self.assertRaises(ValueError): E['json_lines'](b'{}\n' * (E['LIMITS']['maxRecords'] + 3))

    def test_deep_eof_failures_and_exact_one_percent_boundary(self):
        name = PREFIX + 'candidate.jsonl'
        original = [json.loads(line) for line in self.good[name].splitlines()]
        row = json.loads(self.good[PREFIX + 'summary.json'])['launches'][1]
        cases = [('ok', False), ('reason', 'phase-budget'), ('rootGone', False), ('errorCode', 1),
                 ('droppedRecords', 1), ('ownedCount', 1), ('imageCount', 1), ('maxReadTicks', 0), ('maxLagTicks', 1),
                 ('missedIntervals', 1), ('deadlineMach', 1), ('samplingEndMach', 0), ('observedDurationMach', 0),
                 ('selfCpuUs', 0), ('withinSelfCpuLimit', False), ('selfCpuLimitDenominator', 101),
                 ('dumpEndMach', 1), ('selfCpuAccounting', 'collection-only'), ('unmeasuredResidual', 'none')]
        for key, value in cases:
            with self.subTest(key=key):
                data = copy.deepcopy(self.good); rows = copy.deepcopy(original); rows[-1][key] = value
                data[name] = serial_stream(rows)
                with self.assertRaises(ValueError): self.verify(rebind(data))
        for key in ('recordCount', 'storedRecordCount', 'payloadBytesBeforeEOF'):
            rows = copy.deepcopy(original); rows[-1][key] += 1
            with self.subTest(key=key), self.assertRaises(ValueError): E['phase_records'](serial_stream(rows, refresh=False), row)
        exact = copy.deepcopy(original)
        exact[-1].update(selfUserUs=8000, selfSystemUs=2000, selfCpuUs=10000)
        self.assertEqual(E['phase_records'](serial_stream(exact), row)['eof']['selfCpuUs'], 10000)
        above = copy.deepcopy(exact); above[-1].update(selfUserUs=8001, selfCpuUs=10001)
        with self.assertRaisesRegex(ValueError, 'one percent'): E['phase_records'](serial_stream(above), row)
        # More logical CPUs do not dilute this one-core bound.
        above[0]['logicalCpus'] = 1024
        with self.assertRaisesRegex(ValueError, 'one percent'): E['phase_records'](serial_stream(above), row)

    def test_birth_parent_image_counter_and_read_interval_mutations_reject(self):
        name = PREFIX + 'baseline.jsonl'
        original = [json.loads(line) for line in self.good[name].splitlines()]
        identity = next(i for i, r in enumerate(original) if r['type'] == 'identity' and r['identityIndex'] == 1)
        sample = [i for i, r in enumerate(original) if r['type'] == 'sample' and r['identityIndex'] == 1][1]
        cases = [(identity, 'pid', 100), (identity, 'ppid', 999), (identity, 'parentIndex', 1),
                 (identity, 'uid', 0), (identity, 'startAbstime', 1), (identity, 'startUsec', 1000000),
                 (identity, 'imageIndex', 9), (identity, 'uuid', 'bad'), (identity, 'path', 'relative'),
                 (sample, 'identityIndex', 255), (sample, 'imageIndex', 2), (sample, 'startAbstime', 1),
                 (sample, 'userTime', 0), (sample, 'systemTime', -1), (sample, 'runnableTime', 0),
                 (sample, 'readStartMach', 1), (sample, 'readEndMach', original[sample]['readStartMach'] - 1)]
        for index, key, value in cases:
            with self.subTest(index=index, key=key):
                data = copy.deepcopy(self.good); rows = copy.deepcopy(original); rows[index][key] = value
                data[name] = serial_stream(rows)
                with self.assertRaises(ValueError): self.verify(rebind(data))

    def test_valid_exec_reparent_explicit_pid_reuse_and_host_counter_wrap(self):
        name = PREFIX + 'candidate.jsonl'
        rows = [json.loads(line) for line in self.good[name].splitlines()]
        launch = json.loads(self.good[PREFIX + 'summary.json'])['launches'][1]
        child = next(r for r in rows if r['type'] == 'identity' and r['identityIndex'] == 1)
        second = next(i for i, r in enumerate(rows) if r['type'] == 'sample' and r['identityIndex'] == 1 and r['userTime'] == 11000)
        window = {k: rows[second][k] for k in ('readStartMach', 'readEndMach')}
        lifecycle = {'type': 'reparent', 'identityIndex': 1, **window, 'code': 200, 'otherPid': 1,
                     'observedStartSec': 0, 'observedStartUsec': 0, 'observedStartAbstime': 0}
        image = {**child, **window, 'type': 'image', 'imageIndex': 2, 'path': '/owned/new-exec-image', 'uuid': 'd' * 32}
        rows[second:second] = [lifecycle, image]
        for r in rows[second + 2:]:
            if r['type'] == 'sample' and r['identityIndex'] == 1: r['imageIndex'] = 2
        # Explicit reuse retires old birth; a later live owned parent can adopt a
        # new birth with the same PID. Prior ppid=1 never grants new ownership.
        third = next(i for i, r in enumerate(rows) if r['type'] == 'sample' and r['identityIndex'] == 1 and r['userTime'] == 12000)
        at = rows[third]['readStartMach']; birth = at - 50
        reuse = {'type': 'reuse', 'identityIndex': 1, 'readStartMach': at, 'readEndMach': at + 10,
                 'code': 0, 'otherPid': 0, 'observedStartSec': child['startSec'] + 1,
                 'observedStartUsec': child['startUsec'], 'observedStartAbstime': birth}
        adopted = {**child, 'identityIndex': 2, 'imageIndex': 3, 'parentIndex': 0, 'ppid': 200,
                   'startSec': child['startSec'] + 1, 'startAbstime': birth, 'readStartMach': at + 20, 'readEndMach': at + 30}
        sample = {**rows[third], 'identityIndex': 2, 'imageIndex': 3, 'startAbstime': birth,
                  'readStartMach': at + 40, 'readEndMach': at + 50, 'userTime': 1, 'systemTime': 1, 'runnableTime': 0}
        rows[third:third + 1] = [reuse, adopted, sample]
        rows[-1].update(ownedCount=3, imageCount=4)
        hosts = [r for r in rows if r['type'] == 'host']
        hosts[0]['cpuTicks'][0] = (1 << 32) - 1
        hosts[1]['cpuTicks'][0] = 0
        result = E['phase_records'](serial_stream(rows), launch)
        self.assertEqual(len(result['identities']), 3)
        self.assertEqual(len(result['images']), 4)
        self.assertFalse(result['identities'][1]['alive'])
        # Silent same-PID adoption without retirement must fail.
        bad = [r for r in copy.deepcopy(rows) if r['type'] != 'reuse']
        with self.assertRaises(ValueError): E['phase_records'](serial_stream(bad), launch)

    def test_root_exit_during_parent_revalidation_remains_observed_after_child_exit(self):
        rows = [json.loads(line) for line in self.good[PREFIX + 'candidate.jsonl'].splitlines()]
        launch = json.loads(self.good[PREFIX + 'summary.json'])['launches'][1]
        root_exit = rows[-2]
        self.assertEqual((root_exit['type'], root_exit['identityIndex']), ('exit', 0))
        # The actual producer can notice root disappearance inside discover()
        # and finish already-owned child reads in that same sampling cycle.
        child_exit = {**root_exit, 'identityIndex': 1, 'readStartMach': root_exit['readEndMach'] + 100,
                      'readEndMach': root_exit['readEndMach'] + 200}
        rows.insert(-1, child_exit)
        result = E['phase_records'](serial_stream(rows), launch)
        self.assertTrue(result['eof']['rootGone'])
        self.assertFalse(result['identities'][0]['alive'])
        self.assertFalse(result['identities'][1]['alive'])

    def test_python_parent_runtime_initial_and_single_forward_handoff(self):
        name = PREFIX + 'baseline.jsonl'
        original = [json.loads(line) for line in self.good[name].splitlines()]
        launch = json.loads(self.good[PREFIX + 'summary.json'])['launches'][0]
        for initially_runtime in (False, True):
            with self.subTest(initially_runtime=initially_runtime):
                rows = runtime_handoff(original, initially_runtime=initially_runtime)
                result = E['phase_records'](serial_stream(rows), launch)
                self.assertEqual(result['rootInitialImageWasParentRuntime'], initially_runtime)
                self.assertEqual(result['acceptedRootImageTransitions'], 0 if initially_runtime else 1)
                data = copy.deepcopy(self.good); data[name] = serial_stream(rows)
                full = self.verify(rebind(data))
                self.assertEqual(full['phases']['baseline']['acceptedRootImageTransitions'], 0 if initially_runtime else 1)
                self.assertFalse(full['releaseAcceptance'])
        # The bounded native sampler fixture can use the same witnessed policy;
        # verify() still accepts only the two original baseline/candidate phases.
        fixture_launch = {**launch, 'phase': 'fixture', 'budgetMs': 8000}
        rows = runtime_handoff(original)
        rows[0].update(phase='fixture', budgetMs=8000)
        rows[-1]['deadlineMach'] = rows[1]['startAbstime'] + 8000 * 1000000
        self.assertEqual(E['phase_records'](serial_stream(rows), fixture_launch)['acceptedRootImageTransitions'], 1)
        # Same launch and parent image means runtime was already final.
        rows = runtime_handoff(original, initially_runtime=True)
        launch_same = {**launch, 'expectedRootPath': rows[1]['path']}
        rows[0]['expectedRootPath'] = rows[1]['path']
        self.assertTrue(E['phase_records'](serial_stream(rows), launch_same)['rootInitialImageWasParentRuntime'])

    def test_parent_witness_birth_image_and_bracket_mutations_reject(self):
        name = PREFIX + 'baseline.jsonl'
        launch = json.loads(self.good[PREFIX + 'summary.json'])['launches'][0]
        original = [json.loads(line) for line in self.good[name].splitlines()]
        accepted = runtime_handoff(original)
        root = accepted[1]
        parent = accepted[0]['rootImagePolicy']['parentInitial']
        image = next(row for row in accepted if row['type'] == 'image' and row['identityIndex'] == 0)
        cases = [
            ('parentInitial', 'pid', 999), ('parentInitial', 'uid', 0), ('parentInitial', 'ppid', 0),
            ('parentInitial', 'startSec', 0), ('parentInitial', 'startUsec', 1000000),
            ('parentInitial', 'startAbstime', root['startAbstime'] + 1),
            ('parentInitial', 'readStartMach', root['readEndMach'] - 1),
            ('parentInitial', 'readEndMach', accepted[-1]['samplingEndMach'] + 1),
            ('parentInitial', 'uuid', 'bad'), ('parentInitial', 'path', 'relative'),
            ('parentRecheck', 'pid', 999), ('parentRecheck', 'ppid', 8), ('parentRecheck', 'uid', 0),
            ('parentRecheck', 'startSec', parent['startSec'] + 1), ('parentRecheck', 'startUsec', 1),
            ('parentRecheck', 'startAbstime', parent['startAbstime'] + 1),
            ('parentRecheck', 'path', '/foreign/runtime'), ('parentRecheck', 'uuid', 'f' * 32),
            ('parentRecheck', 'readStartMach', image['readEndMach'] - 1),
            ('parentRecheck', 'readEndMach', image['readEndMach']),
        ]
        for witness, key, value in cases:
            with self.subTest(witness=witness, key=key):
                rows = copy.deepcopy(accepted); rows[0]['rootImagePolicy'][witness][key] = value
                data = copy.deepcopy(self.good); data[name] = serial_stream(rows)
                with self.assertRaises(ValueError): self.verify(rebind(data))
        for witness in ('parentInitial', 'parentRecheck'):
            rows = copy.deepcopy(accepted); rows[0]['rootImagePolicy'][witness] = None
            with self.subTest(missing=witness), self.assertRaises(ValueError): E['phase_records'](serial_stream(rows), launch)
        # A valid recheck timestamp without a matching accepted image is not proof.
        rows = copy.deepcopy(original); rows[0]['rootImagePolicy']['parentRecheck'] = copy.deepcopy(accepted[0]['rootImagePolicy']['parentRecheck'])
        with self.assertRaises(ValueError): E['phase_records'](serial_stream(rows), launch)
        # Parent revalidation must still be included in the original max-read fact.
        rows = copy.deepcopy(accepted)
        rows[0]['rootImagePolicy']['parentRecheck']['readEndMach'] += 50
        with self.assertRaisesRegex(ValueError, 'read counts'): E['phase_records'](serial_stream(rows), launch)
        # An internally well-formed, rehashed witness cannot be postponed until
        # after the next fresh root read or its exit. The same-window prefetched
        # image/sample remains valid in the positive handoff case above.
        later_root = [row for row in accepted if row.get('identityIndex') == 0 and
                      row.get('readStartMach', 0) > image['readStartMach']]
        for later in (later_root[0], later_root[-1]):
            rows = copy.deepcopy(accepted)
            rows[0]['rootImagePolicy']['parentRecheck'].update(
                readStartMach=later['readStartMach'] + 1,
                readEndMach=later['readStartMach'] + 101)
            data = copy.deepcopy(self.good); data[name] = serial_stream(rows)
            with self.subTest(late_recheck=later['type']), self.assertRaisesRegex(ValueError, 'subsequent distinct root read'):
                self.verify(rebind(data))

    def test_candidate_fixed_and_reverse_third_or_rejected_root_images_reject(self):
        name = PREFIX + 'baseline.jsonl'
        launch = json.loads(self.good[PREFIX + 'summary.json'])['launches'][0]
        original = [json.loads(line) for line in self.good[name].splitlines()]
        accepted = runtime_handoff(original)
        at = next(i for i, row in enumerate(accepted) if row['type'] == 'image' and row['identityIndex'] == 0)
        for path, uuid in [(launch['expectedRootPath'], original[1]['uuid']), ('/foreign/third-image', 'f' * 32)]:
            with self.subTest(path=path):
                rows = copy.deepcopy(accepted)
                second = {**rows[at], 'imageIndex': rows[-1]['imageCount'], 'path': path, 'uuid': uuid,
                          'readStartMach': rows[at]['readEndMach'] + 200, 'readEndMach': rows[at]['readEndMach'] + 300}
                rows.insert(at + 2, second); rows[-1]['imageCount'] += 1
                with self.assertRaises(ValueError): E['phase_records'](serial_stream(rows), launch)
        rows = runtime_handoff(original, initially_runtime=True)
        forged = {**rows[1], 'type': 'image', 'imageIndex': rows[-1]['imageCount'], 'path': launch['expectedRootPath'],
                  'readStartMach': rows[2]['readStartMach'] + 200, 'readEndMach': rows[2]['readStartMach'] + 300}
        rows.insert(3, forged); rows[-1]['imageCount'] += 1
        with self.assertRaises(ValueError): E['phase_records'](serial_stream(rows), launch)
        # A parent-shaped path with another UUID is not the parent runtime.
        rows = copy.deepcopy(accepted); rows[at]['uuid'] = 'f' * 32
        with self.assertRaises(ValueError): E['phase_records'](serial_stream(rows), launch)
        # Root reparenting cannot grant a new runtime capability.
        rows = copy.deepcopy(accepted)
        reparent = {'type': 'reparent', 'identityIndex': 0, 'readStartMach': rows[at]['readStartMach'],
                    'readEndMach': rows[at]['readEndMach'], 'code': launch['parentPid'], 'otherPid': 1,
                    'observedStartSec': 0, 'observedStartUsec': 0, 'observedStartAbstime': 0}
        rows.insert(at, reparent)
        with self.assertRaises(ValueError): E['phase_records'](serial_stream(rows), launch)
        # The original parent is invariant on every read, including a fixed
        # candidate or a baseline that never changes executable image.
        for phase in ('baseline', 'candidate'):
            rows = [json.loads(line) for line in self.good[PREFIX + phase + '.jsonl'].splitlines()]
            fixed_launch = json.loads(self.good[PREFIX + 'summary.json'])['launches'][E['PHASES'].index(phase)]
            last_sample = next(row for row in reversed(rows) if row['type'] == 'sample' and row['identityIndex'] == 0)
            rows.insert(-2, {**reparent, 'code': fixed_launch['parentPid'],
                             'readStartMach': last_sample['readEndMach'] + 10,
                             'readEndMach': last_sample['readEndMach'] + 110})
            with self.subTest(root_reparent=phase), self.assertRaisesRegex(ValueError, 'original root parent changed'):
                E['phase_records'](serial_stream(rows), fixed_launch)
        rows = copy.deepcopy(original)
        rejected = {'type': 'image-rejected', 'identityIndex': 0, 'imageIndex': 0,
                    'readStartMach': rows[2]['readStartMach'] + 200, 'readEndMach': rows[2]['readStartMach'] + 300,
                    'path': '/foreign/image', 'uuid': 'f' * 32, 'code': 100}
        rows.insert(3, rejected)
        with self.assertRaises(ValueError): E['phase_records'](serial_stream(rows), launch)
        candidate = [json.loads(line) for line in self.good[PREFIX + 'candidate.jsonl'].splitlines()]
        candidate_launch = json.loads(self.good[PREFIX + 'summary.json'])['launches'][1]
        candidate[0]['rootImagePolicy'] = copy.deepcopy(original[0]['rootImagePolicy'])
        with self.assertRaises(ValueError): E['phase_records'](serial_stream(candidate), candidate_launch)
        candidate = [json.loads(line) for line in self.good[PREFIX + 'candidate.jsonl'].splitlines()]
        changed = {**candidate[1], 'type': 'image', 'imageIndex': candidate[-1]['imageCount'], 'path': '/foreign/runtime',
                   'readStartMach': candidate[2]['readStartMach'] + 200, 'readEndMach': candidate[2]['readStartMach'] + 300}
        candidate.insert(3, changed); candidate[-1]['imageCount'] += 1
        with self.assertRaises(ValueError): E['phase_records'](serial_stream(candidate), candidate_launch)

    def test_actual_c_writer_parent_runtime_and_fixed_candidate_parity(self):
        # Compile the unchanged portable production core with the author's
        # synthetic Ops driver. Only harness metadata selects real phase budgets
        # and the declared target architecture; no dumped JSON is rewritten.
        tree = ast.parse((TOOLS / 'test_mouse637_host_observer.py').read_text())
        driver = ast.literal_eval(next(node.value for node in tree.body if isinstance(node, ast.Assign) and
                                      any(isinstance(target, ast.Name) and target.id == 'DRIVER' for target in node.targets)))
        for before, after in [
            ('strcpy(s->phase,"fixture");', 'strcpy(s->phase,"baseline");s->budget_ms=900000;'),
            ('strcpy(s->machine,"fixture");', 'strcpy(s->machine,"arm64");'),
        ]:
            self.assertEqual(driver.count(before), 1)
            driver = driver.replace(before, after)
        self.assertEqual(driver.count('#include SOURCE'), 1)
        driver = driver.replace('#include SOURCE', '#include ' + json.dumps(str(TOOLS / 'mouse637-host-observer.c')))
        compiler = shutil.which('cc')
        self.assertIsNotNone(compiler, 'actual portable C writer parity requires a C compiler')
        with tempfile.TemporaryDirectory(prefix='mouse-host-reader-c-writer-') as directory:
            source, binary = Path(directory) / 'driver.c', Path(directory) / 'driver'
            source.write_text(driver)
            subprocess.run([compiler, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-Wno-unused-function',
                            str(source), '-o', str(binary)], check=True, capture_output=True, timeout=30)
            for mode, phase, initially_runtime, transitions in [
                (0, 'baseline', False, 0), (18, 'baseline', False, 1),
                (19, 'baseline', True, 0), (34, 'candidate', False, 0),
            ]:
                with self.subTest(mode=mode, phase=phase):
                    raw = subprocess.run([str(binary), str(mode)], check=True, capture_output=True, timeout=5).stdout
                    launch = {'phase': phase, 'nonce': 'a' * 64, 'pid': 101, 'parentPid': 9, 'helperPid': 202,
                              'uid': 1000, 'expectedRootPath': '/owned/root', 'launchBeforeEpochUs': 100000000,
                              'launchAfterEpochUs': 100000010, 'budgetMs': E['BUDGETS'][phase]}
                    result = E['phase_records'](raw, launch)
                    self.assertEqual(result['rootInitialImageWasParentRuntime'], initially_runtime)
                    self.assertEqual(result['acceptedRootImageTransitions'], transitions)
                    self.assertEqual(result['header']['budgetMs'], 900000 if phase == 'baseline' else 400000)

    def test_config_build_binary_and_original_helper_mutations_reject(self):
        for label, filename, change in [
            ('config-arg', PREFIX + 'candidate.json', lambda c: c['helperArgv'].append('--extra')),
            ('config-pid', PREFIX + 'baseline.json', lambda c: c.__setitem__('pid', 999)),
            ('config-nonce', PREFIX + 'baseline.json', lambda c: c.__setitem__('nonce', 'e' * 64)),
            ('config-before-helper', PREFIX + 'baseline.json', lambda c: c.__setitem__('helperPid', 300)),
            ('build-commit', PREFIX + 'build.json', lambda b: b.__setitem__('publisherSHA', 'e' * 40)),
            ('build-error', PREFIX + 'build.json', lambda b: b['errors'].append('compiler failure')),
            ('build-command', PREFIX + 'build.json', lambda b: b['command'].append('-DCHANGE')),
            ('build-gitblob', PREFIX + 'build.json', lambda b: b['commands'][2].__setitem__('output', 'e' * 40)),
            ('build-returncode', PREFIX + 'build.json', lambda b: b['commands'][8].__setitem__('returncode', 1)),
            ('build-sdk', PREFIX + 'build.json', lambda b: b.__setitem__('sdkVersion', 'wrong')),
            ('build-end-time', PREFIX + 'build.json', lambda b: b.__setitem__('finishedAtUTC', utc(EPOCH + 1))),
            ('build-source', PREFIX + 'build.json', lambda b: b['source'].__setitem__('sha256', 'e' * 64)),
        ]:
            with self.subTest(label=label):
                data = copy.deepcopy(self.good); self.change_json(data, filename, change)
                with self.assertRaises(ValueError): self.verify(rebind(data))
        for label, binary in [('truncated', b'bad'), ('wrong-arch', self.good[PREFIX + 'sampler.bin'][:4] + struct.pack('<I', 0x01000007) + self.good[PREFIX + 'sampler.bin'][8:])]:
            with self.subTest(label=label):
                data = copy.deepcopy(self.good); data[PREFIX + 'sampler.bin'] = binary
                self.change_json(data, PREFIX + 'build.json', lambda b: b['binary'].update(receipt(binary, PREFIX + 'sampler.bin')))
                with self.assertRaises(ValueError): self.verify(rebind(data))
        for name in ('mouse-verify.py', 'mouse-637-baseline-performance.py'):
            with self.subTest(original=name):
                data = copy.deepcopy(self.good); data[name] += b'\n# changed\n'
                with self.assertRaises(ValueError): self.verify(rebind(data))

    def test_original_native_and_phase_bindings_cannot_be_replaced_by_observer(self):
        cases = [('baseline-pid', 'mouse-637-baseline-process.json', lambda p: p.__setitem__('pid', 999)),
                 ('baseline-budget', 'mouse-637-baseline-process.json', lambda p: p.__setitem__('budgetMs', 400001)),
                 ('baseline-profile', 'mouse-637-baseline-process.json', lambda p: p.__setitem__('profile', '/foreign/Isolated previous-version performance profile')),
                 ('candidate-pid', 'mouse-631-native.json', lambda p: p.__setitem__('pid', 999)),
                 ('candidate-failed', 'mouse-631-native.json', lambda p: p.__setitem__('ok', False)),
                 ('candidate-stage', 'mouse-631-native.json', lambda p: p['stages'].pop()),
                 ('native-budget', 'mouse-631-native.json', lambda p: p.__setitem__('budgetMs', 350001)),
                 ('stress-budget', 'mouse-631-stress.json', lambda p: p.__setitem__('budgetMs', 200001)),
                 ('metrics-pid', 'mouse-631-stress.json', lambda p: p['stages'][0]['processesBefore'][0].__setitem__('pid', 999)),
                 ('prior-guest-failed', 'mouse-637-guest-input-observer-summary.json', lambda p: p.__setitem__('ok', False)),
                 ('prior-feature-failed', 'mouse-637-feature-readiness-summary.json', lambda p: p.__setitem__('ok', False)),
                 ('asar-changed', 'mouse-637-feature-readiness-summary.json', lambda p: p['after']['components']['Contents/Resources/app.asar'].__setitem__('sha256', 'e' * 64))]
        for label, filename, change in cases:
            with self.subTest(label=label):
                data = copy.deepcopy(self.good); self.change_json(data, filename, change)
                if filename == 'mouse-637-baseline-process.json':
                    self.change_json(data, 'mouse-637-baseline-performance.json', lambda p: p.__setitem__('process', json.loads(data[filename])))
                with self.assertRaises(ValueError): self.verify(rebind(data))
        for label, content in [('wrong-exit-pid', b'MOUSE_NATIVE_PROCESS_RETURN pid=999 code=0 elapsedMs=2000'),
                               ('failed-exit', b'MOUSE_NATIVE_PROCESS_RETURN pid=200 code=1 elapsedMs=2000'),
                               ('overbudget', b'MOUSE_NATIVE_PROCESS_RETURN pid=200 code=0 elapsedMs=400001')]:
            with self.subTest(label=label):
                data = copy.deepcopy(self.good)
                data['mouse-631-native.log'] = data['mouse-631-native.log'].replace(b'MOUSE_NATIVE_PROCESS_RETURN pid=200 code=0 elapsedMs=2000', content)
                with self.assertRaises(ValueError): self.verify(rebind(data))

    def test_unchanged_committed_tools_pin_and_all_required_files(self):
        for name in ('mouse637-host-observer.c', 'mouse637-guest-input-observer.py', 'fixtures/mouse637-readiness-002-verifier.py'):
            path = self.tools / name; old = path.read_bytes()
            try:
                path.write_bytes(old + b'\n')
                with self.subTest(code=name), self.assertRaises(ValueError): self.verify(copy.deepcopy(self.good))
            finally:
                path.write_bytes(old)
        for name in (PREFIX + 'sampler.bin', PREFIX + 'baseline.jsonl', PREFIX + 'candidate.jsonl',
                     'mouse-637-baseline-process.json', 'mouse-631-stress.json', 'mouse-637-baseline-performance.py'):
            data = copy.deepcopy(self.good); del data[name]
            with self.subTest(missing=name), self.assertRaises(ValueError): self.verify(data)
        pin = self.repo / 'staging/mouse/6.0.37-arm64/pin.json'; old = pin.read_bytes()
        try:
            pin.write_bytes(old + b'\n')
            with self.assertRaises(ValueError): self.verify(copy.deepcopy(self.good))
        finally:
            pin.write_bytes(old)


if __name__ == '__main__':
    unittest.main()
