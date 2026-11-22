"""Synthetic launcher/lifecycle checks; no installed Mac acceptance is claimed."""
import ast
from contextlib import redirect_stdout
import hashlib
import io
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest

TOOLS = Path(__file__).parent
W = runpy.run_path(str(TOOLS / 'mouse637-guest-input-observer.py'))
F = runpy.run_path(str(TOOLS / 'mouse637-feature-readiness.py'))


class Child:
    def __init__(self, pid, returncode=None):
        self.pid, self.returncode, self.kills = pid, returncode, 0

    def poll(self):
        return self.returncode

    def kill(self):
        self.kills += 1
        self.returncode = -9

    def wait(self, timeout=None):
        return self.returncode


class LauncherTests(unittest.TestCase):
    def make(self, popen):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        exe = root / 'Установка Mouse' / 'Mouse Browser.app/Contents/MacOS/Mouse Browser'
        outer = W['RetainedLaunch'](exe, root, root / 'retained636', TOOLS / 'mouse637-guest-input-observer.cjs', 'a' * 40, popen=popen)
        return outer, root, exe

    def test_nested_layers_delegate_exact_child_and_keep_feature_launches_separate(self):
        calls, children = [], []
        def popen(args, **kwargs):
            child = Child(100 + len(children));children.append(child);calls.append((list(args), kwargs));return child
        outer, root, exe = self.make(popen)
        inner = F['FeatureLaunches'](exe, root, root / 'features637', TOOLS / 'mouse637-feature-readiness.cjs', popen=outer)
        release, entered = threading.Event(), threading.Event()
        def blocked(*_):
            entered.set();release.wait(2)
        outer._control = inner._control = blocked
        try:
            for flag, profile, log in [(W['FLAG'], outer.profile, 'mouse-636-retained-owner-feedback.log'),
                    (F['FLAGS']['write'], inner.profile, 'mouse-637-features-write.log'),
                    (F['FLAGS']['read'], inner.profile, 'mouse-637-features-read.log')]:
                environment = {'CI': 'true', 'MOUSE_TEST_PROFILE': str(profile), 'KEEP': 'unchanged'}
                with (root / log).open('w') as output:
                    child = inner([str(exe), flag], env=environment, stdout=output, stderr=subprocess.STDOUT)
                    self.assertIs(child, children[-1]);self.assertTrue(entered.wait(1));self.assertFalse(release.is_set())
                self.assertEqual(environment, {'CI': 'true', 'MOUSE_TEST_PROFILE': str(profile), 'KEEP': 'unchanged'})
            command = ['node', str(TOOLS / 'mouse637-feature-readiness.cjs'), 'control', '/owned/config.json']
            self.assertIs(inner(command, env={'CI': 'true'}), children[-1])
            self.assertEqual(calls[-1][0], command)
            self.assertEqual(len(calls), 4);self.assertEqual(len(outer.records), 1)
            self.assertEqual([row['phase'] for row in inner.records], ['write', 'read'])
            self.assertEqual(calls[0][0][0], str(exe));self.assertEqual(calls[0][0][-1], W['FLAG'])
            self.assertRegex(calls[0][0][1], r'^--inspect-brk=127\.0\.0\.1:\d+$')
            self.assertEqual(calls[0][1]['env']['MOUSE_637_GUEST_INPUT_NONCE'], outer.records[0]['nonce'])
            self.assertNotIn('MOUSE_637_GUEST_INPUT_NONCE', calls[1][1]['env'])
            self.assertNotIn('MOUSE_637_FEATURE_READINESS_NONCE', calls[0][1]['env'])
        finally:
            release.set()
            for thread in outer.threads + inner.threads:thread.join(2)

    def test_wrong_retained_identity_and_duplicate_launch_reject_before_spawning(self):
        calls = []
        def popen(*args, **kwargs):
            calls.append((args, kwargs));return Child(123)
        outer, root, exe = self.make(popen)
        with (root / 'mouse-636-retained-owner-feedback.log').open('w') as log:
            base = {'env': {'CI': 'true', 'MOUSE_TEST_PROFILE': str(outer.profile)}, 'stdout': log}
            cases = [([str(exe), W['FLAG'], '--extra'], base), (['/wrong', W['FLAG']], base),
                ([str(exe), W['FLAG']], {**base, 'shell': True}),
                ([str(exe), W['FLAG']], {**base, 'env': {**base['env'], 'CI': 'false'}}),
                ([str(exe), W['FLAG']], {**base, 'env': {**base['env'], 'MOUSE_TEST_PROFILE': '/wrong'}}),
                ([str(exe), W['FLAG']], {**base, 'env': {**base['env'], 'MOUSE_637_GUEST_INPUT_NONCE': 'inherited'}})]
            for args, kwargs in cases:
                with self.subTest(args=args, kwargs=kwargs):
                    with self.assertRaises(ValueError):outer(args, **kwargs)
            self.assertEqual(calls, [])
            outer._control = lambda *_: None
            outer([str(exe), W['FLAG']], **base)
            with self.assertRaises(ValueError):outer([str(exe), W['FLAG']], **base)
            for thread in outer.threads:thread.join(1)
            self.assertEqual(len(calls), 1)

    def test_original_run_logged_deadline_starts_while_observer_sidecar_is_blocked(self):
        source = (TOOLS / 'fixtures/mouse637-readiness-002-verifier.py').read_text()
        tree = ast.parse(source)
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'run_logged')
        release, entered = threading.Event(), threading.Event()
        actual = []
        def real_owned(args, **kwargs):
            child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(10)'], **kwargs)
            actual.append(child);return child
        outer, root, exe = self.make(real_owned)
        def blocked(*_):
            entered.set();release.wait(2)
        outer._control = blocked
        context = {'subprocess': SimpleNamespace(Popen=outer, STDOUT=subprocess.STDOUT,
            TimeoutExpired=subprocess.TimeoutExpired, CompletedProcess=subprocess.CompletedProcess),
            'time': time, 'sample_native_exit': lambda *_: self.fail('No exit sampling requested')}
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<exact source002 run_logged>', 'exec'), context)
        started = time.monotonic()
        try:
            with redirect_stdout(io.StringIO()), self.assertRaises(subprocess.TimeoutExpired):
                context['run_logged']([str(exe), W['FLAG']], {'CI': 'true', 'MOUSE_TEST_PROFILE': str(outer.profile)},
                    root / 'mouse-636-retained-owner-feedback.log', .08)
            self.assertTrue(entered.is_set());self.assertFalse(release.is_set())
            self.assertLess(time.monotonic() - started, 1)
            self.assertEqual(len(actual), 1);self.assertIs(outer.children[0], actual[0])
            self.assertIsNotNone(actual[0].returncode)
            log = (root / 'mouse-636-retained-owner-feedback.log').read_text()
            self.assertIn('MOUSE_NATIVE_PROCESS_TIMEOUT pid=' + str(actual[0].pid), log)
            self.assertIn('exitRequested=False', log)
        finally:
            release.set();outer.finish(failed=True)
            for child in actual:
                if child.poll() is None:child.kill();child.wait()
        self.assertIn("pathlib.Path('mouse-636-retained-owner-feedback.log'),270)", source)

    def test_bootstrap_failure_terminates_only_its_actual_child_and_records_error(self):
        owned = Child(101)
        controller = Child(102, 1)
        calls = []
        def popen(args, **kwargs):
            calls.append(list(args));return owned if len(calls) == 1 else controller
        outer, root, exe = self.make(popen)
        with (root / 'mouse-636-retained-owner-feedback.log').open('w') as log:
            self.assertIs(outer([str(exe), W['FLAG']], env={'CI': 'true', 'MOUSE_TEST_PROFILE': str(outer.profile)}, stdout=log), owned)
            for thread in outer.threads:thread.join(2)
        self.assertEqual(owned.kills, 1);self.assertEqual(controller.kills, 0)
        self.assertIn('Owned retained Inspector controller failed', outer.records[0]['bootstrapError'])
        self.assertEqual(calls[1][:3], ['node', str(outer.controller), 'control'])
        with self.assertRaises(ValueError):outer.finish()
        outer.finish(failed=True)

    def test_original_feature_wrapper_and_current_workflow_wiring_remain_bound(self):
        digest = hashlib.sha256((TOOLS / 'mouse637-feature-readiness.py').read_bytes()).hexdigest()
        self.assertEqual(digest, W['INNER_SHA'])
        source = (TOOLS / 'mouse637-guest-input-observer.py').read_text()
        self.assertIn("runpy.run_path(str(inner), run_name='__main__')", source)
        self.assertIn('subprocess.Popen, sys.argv = previous_popen, previous_argv', source)
        self.assertNotIn('NODE_OPTIONS=', source)
        self.assertIn('checker[\'verify\'](output)', source)


if __name__ == '__main__':
    unittest.main()
