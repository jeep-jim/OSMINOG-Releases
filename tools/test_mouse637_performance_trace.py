import ast
import contextlib
import hashlib
import io
from pathlib import Path
import runpy
import subprocess
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent
M = runpy.run_path(str(HERE / 'mouse637-performance-trace.py'))
VERIFIER = HERE / 'fixtures/mouse637-readiness-002-verifier.py'


class Child:
    pid = 24680

    def __init__(self):
        self.returncode = None
        self.killed = False

    def poll(self):
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -9

    def wait(self, timeout=None):
        return self.returncode


class DiagnosticLauncherTests(unittest.TestCase):
    def test_exact_definitions_and_original_process_budgets(self):
        namespace = M['original_functions'](VERIFIER)
        self.assertTrue(callable(namespace['run_logged']))
        self.assertTrue(callable(namespace['sample_native_exit']))
        tree = ast.parse((HERE / 'mouse637-performance-trace.py').read_text())
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Subscript) and isinstance(node.func.slice, ast.Constant)
                 and node.func.slice.value == 'run_logged']
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].args[-1].value, 400)
        parent = (HERE / 'fixtures/mouse637-performance-002-native.cjs').read_text()
        stress = (HERE / 'fixtures/mouse637-performance-002-stress.cjs').read_text()
        self.assertIn('budgetMs:350000', parent)
        self.assertIn('budgetMs:200000', stress)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'modified.py'
            path.write_bytes(VERIFIER.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'verifier differs'):
                M['original_functions'](path)

    def test_actual_popen_object_returns_while_bootstrap_is_blocked(self):
        child = Child()
        calls = []
        entered, release = threading.Event(), threading.Event()

        def actual(args, **kwargs):
            calls.append((args, kwargs))
            return child

        launch = M['StressLaunch']('/owned/Mouse Browser', '/output', '/profiles/task-stress-631', '/tools/controller.cjs', 'a' * 40, popen=actual)
        launch._control = lambda *_: (entered.set(), release.wait(5))
        try:
            result = launch(['/owned/Mouse Browser', '--mouse-631-smoke'],
                            env={'CI': 'true', 'MOUSE_TEST_PROFILE': '/profiles/task-stress-631'},
                            stdout=types.SimpleNamespace(name='/output/mouse-631-native.log'))
            self.assertIs(result, child)
            self.assertTrue(entered.wait(1))
            self.assertFalse(release.is_set())
            self.assertEqual(len(calls), 1)
            argv, kwargs = calls[0]
            self.assertEqual(argv[0], '/owned/Mouse Browser')
            self.assertRegex(argv[1], r'^--inspect-brk=127\.0\.0\.1:\d+$')
            self.assertEqual(argv[2], '--mouse-631-smoke')
            self.assertEqual(kwargs['env']['MOUSE_637_PERFORMANCE_TRACE_NONCE'], launch.records[0]['nonce'])
            self.assertEqual(launch.records[0]['pid'], child.pid)
            with self.assertRaisesRegex(ValueError, 'One exact'):
                launch(['/owned/Mouse Browser', '--mouse-631-smoke'])
        finally:
            release.set()
            for thread in launch.threads:
                thread.join(1)

    def test_unchanged_original_timer_expires_while_sidecar_remains_blocked(self):
        child = Child()
        release, entered = threading.Event(), threading.Event()
        launch = M['StressLaunch']('/owned/Mouse Browser', '/output', '/profiles/task-stress-631', '/tools/controller.cjs', 'a' * 40,
                                  popen=lambda *args, **kwargs: child)
        launch._control = lambda *_: (entered.set(), release.wait(5))
        namespace = M['original_functions'](VERIFIER)
        try:
            with tempfile.TemporaryDirectory() as temporary, patch.object(subprocess, 'Popen', launch), contextlib.redirect_stdout(io.StringIO()):
                log = Path(temporary) / 'mouse-631-native.log'
                with self.assertRaises(subprocess.TimeoutExpired):
                    namespace['run_logged'](['/owned/Mouse Browser', '--mouse-631-smoke'],
                                            {'CI': 'true', 'MOUSE_TEST_PROFILE': '/profiles/task-stress-631'}, log, .01)
                self.assertIn('MOUSE_NATIVE_PROCESS_TIMEOUT pid=24680', log.read_text())
            self.assertTrue(child.killed)
            self.assertTrue(entered.is_set())
            self.assertFalse(release.is_set())
        finally:
            release.set()
            for thread in launch.threads:
                thread.join(1)

    def test_unrelated_launch_passes_through_and_wrong_profile_rejects_before_popen(self):
        calls = []
        child = Child()
        launch = M['StressLaunch']('/owned/Mouse Browser', '/output', '/profiles/task-stress-631', '/tools/controller.cjs', 'a' * 40,
                                  popen=lambda *args, **kwargs: (calls.append((args, kwargs)), child)[1])
        self.assertIs(launch(['node', '/tools/controller.cjs']), child)
        self.assertEqual(len(launch.records), 0)
        with self.assertRaisesRegex(ValueError, 'CI/profile'):
            launch(['/owned/Mouse Browser', '--mouse-631-smoke'], env={'CI': 'true', 'MOUSE_TEST_PROFILE': '/wrong'})
        self.assertEqual(len(calls), 1)

    def test_summary_hash_or_write_failure_preserves_original_exception_identity(self):
        save = M['save_summary']
        original = subprocess.TimeoutExpired(['owned-electron'], 400)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'native.log').write_text('original failure')
            metadata = OSError('stat/hash failure')
            summary = {'ok': False}
            with patch.dict(save.__globals__, {'sha': lambda _: (_ for _ in ()).throw(metadata)}):
                self.assertIs(save(directory, summary, original), original)
            self.assertIn('metadataError', summary)
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stderr(io.StringIO()):
            writing = OSError('disk full')
            with patch.dict(save.__globals__, {'write_new': lambda *_: (_ for _ in ()).throw(writing)}):
                self.assertIs(save(Path(temporary), {'ok': False}, original), original)
                self.assertIs(save(Path(temporary), {'ok': True}, None), writing)

    def test_package_bytes_are_exact_and_not_replaced_by_labels(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            names = ['Mouse-Browser-6.0.37-mac-arm64.dmg', 'Mouse-Browser-6.0.37-mac-arm64.zip']
            packages = {}
            for name in names:
                data = ('owned-' + name).encode()
                (folder / name).write_bytes(data)
                packages[name] = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
            pin = {'source': M['SOURCE'], 'version': '6.0.37', 'packages': packages}
            self.assertEqual(M['package_snapshot'](folder, pin), packages)
            (folder / names[0]).write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'immutable pin'):
                M['package_snapshot'](folder, pin)

    def test_diagnostic_workflow_has_no_publication_or_writable_token(self):
        text = (HERE.parent / '.github/workflows/diagnose-mouse637-macos-performance.yml').read_text()
        self.assertIn('contents: read', text)
        self.assertIn('actions: read', text)
        self.assertNotIn('contents: write', text)
        self.assertNotIn('actions: write', text)
        self.assertIn('mouse637-performance-diagnostic', text)
        self.assertIn('mouse637-performance-trace.py', text)
        self.assertNotRegex(text, r'mouse637-release\.py\s+(?:publish|channel)\b')
        self.assertNotIn('source=False', text)
        self.assertNotIn('gh release', text)


if __name__ == '__main__':
    unittest.main()
