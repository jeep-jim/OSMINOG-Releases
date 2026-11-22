"""Synthetic negative contracts for the external driver, never native acceptance."""
import copy
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import threading
import unittest

TOOLS = Path(__file__).parent
W = runpy.run_path(str(TOOLS / 'mouse637-feature-readiness.py'))
E = runpy.run_path(str(TOOLS / 'mouse637-feature-readiness-evidence.py'))
PUBLISHER = '1' * 40


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class Proof:
    def __init__(self, root, adapted):
        self.root = root
        self.output = '/owned/evidence'
        self.exe = '/owned/Mouse Browser.app/Contents/MacOS/Mouse Browser'
        self.app = '/owned/Mouse Browser.app/Contents/Resources/app.asar'
        self.profile = '/owned/profiles/features637'
        original = (TOOLS / 'fixtures/mouse637-readiness-002-features.cjs').read_bytes()
        (root / 'mouse-637-feature-readiness-original.cjs').write_bytes(original)
        (root / 'mouse-637-feature-readiness-adapted.cjs').write_bytes(adapted)
        components = {name: {'size': 100, 'sha256': E['ASAR_SHA'] if name.endswith('app.asar') else 'f' * 64}
                      for name in E['COMPONENTS']}
        self.summary = {'schema': 1, 'kind': 'mouse637-external-feature-readiness', 'source': E['SOURCE'],
            'version': '6.0.37', 'platform': 'darwin', 'arch': 'arm64', 'ok': True, 'publisherSHA': PUBLISHER,
            'verifierSha256': E['VERIFIER_SHA'], 'wrapperSha256': sha((TOOLS / 'mouse637-feature-readiness.py').read_bytes()),
            'controllerSha256': sha((TOOLS / 'mouse637-feature-readiness.cjs').read_bytes()),
            'executable': self.exe, 'appPath': self.app, 'profile': self.profile, 'output': self.output, 'launches': []}
        for label in ('before', 'after'):
            name = 'mouse-637-feature-readiness-codesign-' + label + '.log'
            (root / name).write_bytes(b'synthetic codesign observation\n')
            self.summary[label] = {'components': copy.deepcopy(components),
                'nativeInventory': sorted(x for x in E['COMPONENTS'] if x.endswith('.node')),
                'codesign': {'exitCode': 0, 'command': ['codesign', '--verify', '--deep', '--strict'],
                            'log': name, 'logSha256': self.digest(name)}}
        self.receipts, self.controls, self.configs, self.native = {}, {}, {}, {}
        for index, phase in enumerate(('write', 'read')):
            pid, controller, port, nonce = 100 + index, 200 + index, 41000 + index, str(index + 1) * 64
            flag = W['FLAGS'][phase]
            row = {'phase': phase, 'flag': flag, 'pid': pid, 'controllerPid': controller, 'nonce': nonce,
                'port': port, 'profile': self.profile, 'originalArgv': [self.exe, flag],
                'argv': [self.exe, '--inspect-brk=127.0.0.1:' + str(port), flag],
                'addedEnvironment': {'MOUSE_637_FEATURE_READINESS_NONCE': nonce},
                'controllerExitCode': 0, 'bootstrapElapsedMs': 100, 'bootstrapStartedAt': 900 + index * 10000,
                'receipt': 'mouse-637-feature-readiness-' + phase + '.json',
                'controllerReceipt': 'mouse-637-feature-readiness-controller-' + phase + '.json',
                'config': 'mouse-637-feature-readiness-config-' + phase + '.json',
                'controllerLog': 'mouse-637-feature-readiness-controller-' + phase + '.log'}
            self.summary['launches'].append(row)
            (root / row['controllerLog']).write_bytes(b'synthetic controller log\n')
            receipt = {'schema': 1, 'kind': 'mouse637-publisher-fixture-readiness', 'source': E['SOURCE'], 'version': '6.0.37',
                'phase': phase, 'flag': flag, 'pid': pid, 'controllerPid': controller, 'nonce': nonce,
                'executable': self.exe, 'appPath': self.app, 'profile': self.profile,
                'target': self.app + '/mouse-637-features-smoke.cjs', 'platform': 'darwin', 'arch': 'arm64',
                'originalSha256': E['ORIGINAL_SHA'], 'originalGitBlob': E['ORIGINAL_BLOB'], 'adaptedSha256': E['ADAPTED_SHA'],
                'mainSha256': E['MAIN_SHA'], 'applications': 1, 'observations': E['OBSERVATIONS'],
                'loaderRestored': True, 'inspectorClosed': True, 'inspectorUrl': None,
                'receiptBeforeFixtureInvocation': True, 'versions': {'electron': '44.5.0', 'node': 'synthetic'},
                'closedAt': 1000 + index * 10000, 'compiledAt': 1010 + index * 10000}
            self.receipts[phase] = receipt
            self.controls[phase] = {'schema': 1, 'ok': True, 'phase': phase, 'pid': pid, 'controllerPid': controller,
                'nonce': nonce, 'port': port, 'host': '127.0.0.1', 'serverUnavailable': True,
                'startedAt': 900 + index * 10000, 'finishedAt': 1050 + index * 10000,
                'controllerSha256': self.summary['controllerSha256']}
            self.configs[phase] = {'schema': 1, 'phase': phase, 'flag': flag, 'pid': pid, 'nonce': nonce,
                'port': port, 'executable': self.exe, 'appPath': self.app, 'profile': self.profile,
                'output': self.output, 'receipt': self.output + '/' + row['receipt'],
                'deadlineEpochMs': row['bootstrapStartedAt'] + 30000,
                'controllerReceipt': self.output + '/' + row['controllerReceipt']}
            self.native[phase] = {'pid': 100, 'restart': {'pid': 101},
                'nativeInputs': [{'pid': pid, 'at': 1100 + index * 10000}]}
        self.refresh()

    def write(self, name, value):
        (self.root / name).write_text(json.dumps(value, ensure_ascii=False) + '\n')

    def digest(self, name):
        return sha((self.root / name).read_bytes())

    def refresh(self):
        processes = {}
        for row, phase, marker, report in zip(self.summary['launches'], ('write', 'read'),
                ('MOUSE_637_FEATURES_WRITE_PASS', 'MOUSE_637_FEATURES_NATIVE_PASS'),
                ('mouse-637-features-write.json', 'mouse-637-features.json')):
            self.write(row['receipt'], self.receipts[phase])
            self.controls[phase]['receiptSha256'] = self.digest(row['receipt'])
            self.write(row['controllerReceipt'], self.controls[phase])
            self.write(row['config'], self.configs[phase])
            for key in ('receipt', 'controllerReceipt', 'config', 'controllerLog'):
                row[key + 'Sha256'] = self.digest(row[key])
            log = 'mouse-637-features-' + phase + '.log'
            (self.root / log).write_text('MOUSE_637_FEATURE_READINESS_ADAPTER ' + json.dumps(self.receipts[phase]) + '\n' + marker + '\n')
            self.write(report, self.native[phase])
            processes[phase] = {'pid': 100 if phase == 'write' else 101, 'exitCode': 0, 'elapsedMs': 1000,
                'requiredMarkers': [marker], 'log': log, 'logSha256': self.digest(log),
                'report': report, 'reportSha256': self.digest(report)}
        processes['reportSha256'] = self.digest('mouse-637-features.json')
        self.write('mouse-637-features-processes.json', processes)
        self.write('mouse-637-feature-readiness-summary.json', self.summary)

    def verify(self):
        return E['verify'](self.root, publisher_sha=PUBLISHER)


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        node = os.environ.get('CODEX_PRIMARY_RUNTIME_NODE') or shutil.which('node')
        if not node:
            raise RuntimeError('Node is required for the exact external driver contract')
        cls.adapted = subprocess.check_output([node, '-e',
            'const a=require("./tools/mouse637-feature-readiness.cjs"),f=require("fs");process.stdout.write(a.transform(f.readFileSync("tools/fixtures/mouse637-readiness-002-features.cjs","utf8")))'], cwd=TOOLS.parent)

    def make(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return Proof(Path(temporary.name), self.adapted)

    def test_bound_additive_proof_passes_and_freed_port_reuse_is_valid(self):
        proof = self.make()
        self.assertTrue(proof.verify()['ok'])
        port = proof.summary['launches'][0]['port']
        proof.summary['launches'][1]['port'] = port
        proof.summary['launches'][1]['argv'][1] = '--inspect-brk=127.0.0.1:' + str(port)
        proof.controls['read']['port'] = proof.configs['read']['port'] = port
        proof.refresh()
        self.assertTrue(proof.verify()['ok'])

    def test_semantic_receipt_negatives_even_with_fresh_hash_and_log_bindings(self):
        mutations = [lambda p: p.receipts['write'].update(pid=200),
            lambda p: p.receipts['write'].update(nonce='f' * 64),
            lambda p: p.receipts['write'].update(executable='/wrong/exe'),
            lambda p: p.receipts['write'].update(profile='/wrong/profile'),
            lambda p: p.receipts['write'].update(phase='read'),
            lambda p: p.receipts['write'].update(loaderRestored=False),
            lambda p: p.receipts['write'].update(inspectorClosed=False),
            lambda p: p.receipts['write'].update(inspectorUrl='ws://127.0.0.1:123'),
            lambda p: p.receipts['write'].update(applications=2),
            lambda p: p.receipts['write'].update(applications=True),
            lambda p: p.receipts['write'].update(adaptedSha256='f' * 64),
            lambda p: p.receipts['write'].update(originalSha256='f' * 64),
            lambda p: p.receipts['write'].update(observations=[]),
            lambda p: p.receipts['write'].update(compiledAt=1200),
            lambda p: p.controls['write'].update(serverUnavailable=False),
            lambda p: p.configs['write'].update(nonce='f' * 64),
            lambda p: p.configs['write'].update(pid=200),
            lambda p: p.configs['write'].update(deadlineEpochMs=99999999),
            lambda p: p.controls['write'].update(finishedAt=99999999),
            lambda p: p.summary['launches'][0].update(addedEnvironment={}),
            lambda p: p.summary['launches'][0].update(controllerExitCode=1),
            lambda p: p.summary['launches'][0].update(bootstrapElapsedMs=30001),
            lambda p: p.summary['after']['components']['Contents/Resources/app.asar.unpacked/mouse-native-menu.node'].update(sha256='a' * 64),
            lambda p: p.summary['after'].update(nativeInventory=[]),
            lambda p: p.summary['after']['codesign'].update(exitCode=1),
            lambda p: p.summary.update(publisherSHA='2' * 40),
            lambda p: p.summary.update(verifierSha256='f' * 64)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                proof = self.make();mutation(proof);proof.refresh()
                with self.assertRaises(ValueError):
                    proof.verify()

    def test_missing_or_modified_code_raw_receipts_and_original_process_binding_fail(self):
        for name in ['mouse-637-feature-readiness-write.json', 'mouse-637-feature-readiness-original.cjs',
                     'mouse-637-feature-readiness-adapted.cjs', 'mouse-637-feature-readiness-codesign-after.log']:
            with self.subTest(name=name):
                proof = self.make();(proof.root / name).unlink()
                with self.assertRaises(ValueError): proof.verify()
        proof = self.make();(proof.root / 'mouse-637-feature-readiness-adapted.cjs').write_bytes(self.adapted + b'\n')
        with self.assertRaises(ValueError): proof.verify()
        for field, value in [('pid', 200), ('elapsedMs', 270001), ('exitCode', 1), ('requiredMarkers', [])]:
            proof = self.make();processes = json.loads((proof.root / 'mouse-637-features-processes.json').read_text());processes['write'][field] = value
            proof.write('mouse-637-features-processes.json', processes)
            with self.assertRaises(ValueError): proof.verify()


class FakeProcess:
    def __init__(self, pid=711, code=None): self.pid, self.returncode, self.killed = pid, code, False
    def poll(self): return self.returncode
    def kill(self): self.killed = True; self.returncode = -9
    def wait(self, timeout=None): return self.returncode


class LaunchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.directory = Path(temporary.name)
        self.executable = Path('/owned/Mouse Browser.app/Contents/MacOS/Mouse Browser')
        self.profile = Path('/owned/profiles/features637')
        self.calls = [];self.child = FakeProcess()
        def popen(args, **kwargs): self.calls.append((args, kwargs));return self.child
        self.launches = W['FeatureLaunches'](self.executable, self.directory, self.profile, TOOLS / 'mouse637-feature-readiness.cjs', popen)

    def options(self, phase='write'):
        log = (self.directory / ('mouse-637-features-' + phase + '.log')).open('w');self.addCleanup(log.close)
        return {'stdout': log, 'stderr': subprocess.STDOUT, 'text': True,
                'env': {'CI': 'true', 'MOUSE_TEST_PROFILE': str(self.profile), 'UNCHANGED': 'value'}}

    def test_returns_actual_popen_while_bootstrap_still_blocked_and_preserves_original_environment(self):
        entered, release = threading.Event(), threading.Event()
        def blocked(*_): entered.set();release.wait(timeout=2)
        self.launches._control = blocked
        options = self.options();original_env = copy.deepcopy(options['env'])
        process = self.launches([str(self.executable), W['FLAGS']['write']], **options)
        self.assertIs(process, self.child);self.assertTrue(entered.wait(timeout=1));self.assertFalse(release.is_set())
        self.assertEqual(options['env'], original_env)
        called_args, called_options = self.calls[0]
        self.assertEqual(called_args[0], str(self.executable));self.assertEqual(called_args[-1], W['FLAGS']['write'])
        self.assertRegex(called_args[1], r'^--inspect-brk=127\.0\.0\.1:\d+$')
        self.assertEqual(called_options['env'], {**original_env, 'MOUSE_637_FEATURE_READINESS_NONCE': self.launches.records[0]['nonce']})
        release.set();self.launches.finish(failed=True)

    def test_other_native_stages_are_passed_through_without_wrapping(self):
        argv = ['owned', '--mouse-636-retained-smoke'];environment = {'CI': 'true'}
        self.assertIs(self.launches(argv, env=environment), self.child)
        self.assertIs(self.calls[0][0], argv);self.assertIs(self.calls[0][1]['env'], environment);self.assertEqual(self.launches.records, [])

    def test_wrong_child_scope_or_phase_order_cannot_start_process(self):
        for args, options in [(['/other/exe', W['FLAGS']['write']], self.options()),
                ([str(self.executable), W['FLAGS']['write'], '--extra'], self.options()),
                ([str(self.executable), W['FLAGS']['read']], self.options('read'))]:
            with self.subTest(args=args), self.assertRaises(ValueError): self.launches(args, **options)
        self.assertEqual(self.calls, [])
        for environment in [{'CI': 'false', 'MOUSE_TEST_PROFILE': str(self.profile)},
                            {'CI': 'true', 'MOUSE_TEST_PROFILE': '/wrong'}]:
            options = self.options();options['env'] = environment
            with self.assertRaises(ValueError): self.launches([str(self.executable), W['FLAGS']['write']], **options)

    def test_controller_failure_kills_only_owned_actual_child(self):
        controller = FakeProcess(712, 1)
        self.launches.original = lambda *args, **kwargs: controller
        row = {'phase': 'write', 'flag': W['FLAGS']['write'], 'pid': self.child.pid,
               'nonce': 'a' * 64, 'port': 41127, 'bootstrapStartedAt': 1000}
        import time
        self.launches._control(self.child, row, time.monotonic())
        self.assertTrue(self.child.killed);self.assertFalse(controller.killed);self.assertEqual(len(self.launches.errors), 1)

    def test_workflow_keeps_frozen_gates_and_additive_verification_before_publish(self):
        text = (TOOLS.parent / '.github/workflows/publish-mouse637.yml').read_text()
        self.assertIn('python3 ../tools/mouse637-feature-readiness.py "$APP/Contents/MacOS/Mouse Browser"', text)
        self.assertLess(text.index('python3 tools/mouse637-feature-readiness-evidence.py --directory mouse637-release'), text.index('python3 tools/mouse637-release.py publish'))
        self.assertIn('node --test tools/test_mouse637_feature_readiness.cjs', text)
        for retained in ['MOUSE_637_REAL_636_TO_637_PROFILE_PASS', 'MOUSE_636_RETAINED_OWNER_FEEDBACK_PASS', 'MOUSE_637_REAL_636_TO_637_UPDATE_BUTTON_PASS', 'MOUSE_637_FEATURES_NATIVE_PASS']:
            self.assertIn(retained, text)
        self.assertEqual(sha((TOOLS / 'fixtures/mouse637-readiness-002-verifier.py').read_bytes()), W['VERIFIER_SHA'])


if __name__ == '__main__': unittest.main()
