#!/usr/bin/env python3
"""Portable full-build regressions: real temporary Git, synthetic Xcode only.

Neither test compiles a native sampler or claims actual Mac acceptance.
"""
import contextlib
import datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock


TOOLS = Path(__file__).resolve().parent
BUILDER = TOOLS / 'mouse637-host-observer-build.py'
FAKE_BINARY = b'SYNTHETIC COMPILER OUTPUT; NOT A NATIVE EXECUTABLE\n'
COMPILER_OUTPUT = b'Synthetic Apple clang fixture, no compiler executed\n'
SDK_PATH = b'/Synthetic Xcode SDK/MacOSX.sdk\n'
SDK_VERSION = b'15.5-synthetic\n'


def digest(data):
    return hashlib.sha256(data).hexdigest()


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='mouse637-builder-contract-')
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / 'Synthetic publisher with spaces'
        self.tools = self.repo / 'tools'
        self.tools.mkdir(parents=True)
        self.builder = self.tools / BUILDER.name
        self.source = self.tools / 'mouse637-host-observer.c'
        shutil.copyfile(BUILDER, self.builder)
        self.source.write_bytes(b'/* Synthetic source; never compiled by these tests. */\nint main(void) { return 0; }\n')
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        subprocess.run(['git', 'add', 'tools'], cwd=self.repo, check=True)
        subprocess.run(['git', '-c', 'user.name=Synthetic builder contract',
                        '-c', 'user.email=fixture@example.invalid', 'commit', '-q',
                        '-m', 'Temporary synthetic builder contract files'], cwd=self.repo, check=True)
        self.head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.repo, text=True).strip()
        self.output = self.repo / 'mouse637-release/mouse-637-host-observer-sampler.bin'
        self.receipt = self.output.with_name('mouse-637-host-observer-build.json')
        spec = importlib.util.spec_from_file_location('mouse637_actual_builder_under_test', BUILDER)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.git_calls, self.xcrun_calls = [], []
        self.stdout = io.StringIO()

    def invoke(self, *, fail_compile=False):
        actual_run = subprocess.run
        compile_argv = ['xcrun', 'clang', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                        str(self.source), '-o', str(self.output)]

        def controlled_external(argv, **kwargs):
            argv = [str(value) for value in argv]
            self.assertEqual(Path(kwargs['cwd']), self.repo)
            self.assertEqual(kwargs['timeout'], 60)
            self.assertIs(kwargs['check'], False)
            self.assertEqual(kwargs['stdout'], subprocess.PIPE)
            self.assertEqual(kwargs['stderr'], subprocess.STDOUT)
            if argv[0] == 'git':
                # Deliberately execute the real Git identity checks from build().
                self.git_calls.append(argv)
                return actual_run(argv, **kwargs)
            self.assertEqual(argv[0], 'xcrun')
            self.xcrun_calls.append(argv)
            if argv == ['xcrun', 'clang', '--version']:
                output, code = COMPILER_OUTPUT, 0
            elif argv == ['xcrun', '--show-sdk-path']:
                output, code = SDK_PATH, 0
            elif argv == ['xcrun', '--show-sdk-version']:
                output, code = SDK_VERSION, 0
            elif argv == compile_argv:
                if fail_compile:
                    output, code = b'Synthetic compiler failure retained verbatim\n', 23
                else:
                    self.output.write_bytes(FAKE_BINARY)
                    output, code = b'', 0
            elif argv == ['xcrun', 'lipo', '-archs', str(self.output)]:
                self.assertEqual(self.output.read_bytes(), FAKE_BINARY)
                output, code = b'arm64\n', 0
            else:
                self.fail('Unexpected external command: ' + repr(argv))
            return subprocess.CompletedProcess(argv, code, stdout=output)

        # __file__ points at the committed copy; execute the actual build() body.
        with mock.patch.object(self.module, '__file__', str(self.builder)), \
                mock.patch.object(self.module.sys, 'platform', 'darwin'), \
                mock.patch.object(self.module.platform, 'machine', return_value='arm64'), \
                mock.patch.dict(os.environ, {'CI': 'true', 'GITHUB_SHA': self.head}), \
                mock.patch.object(self.module.subprocess, 'run', side_effect=controlled_external), \
                contextlib.redirect_stdout(self.stdout):
            return self.module.build(self.output, self.receipt)

    def assert_real_git_and_source_bindings(self, facts):
        self.assertEqual(self.git_calls, [
            ['git', 'rev-parse', 'HEAD'],
            ['git', 'hash-object', str(self.source)],
            ['git', 'rev-parse', 'HEAD:tools/mouse637-host-observer.c'],
            ['git', 'hash-object', str(self.builder)],
            ['git', 'rev-parse', 'HEAD:tools/mouse637-host-observer-build.py'],
        ])
        self.assertEqual(facts['publisherSHA'], self.head)
        for key, path in [('source', self.source), ('builder', self.builder)]:
            original = subprocess.check_output(['git', 'show', self.head + ':tools/' + path.name], cwd=self.repo)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(facts[key], {'path': 'tools/' + path.name, 'size': len(original), 'sha256': digest(original)})
        self.assertEqual(facts['commands'][0]['output'].strip(), self.head)
        for first in (1, 3):
            self.assertEqual(facts['commands'][first]['output'], facts['commands'][first + 1]['output'])
            self.assertRegex(facts['commands'][first]['output'].strip(), r'^[0-9a-f]{40}$')
        self.assertLessEqual(datetime.datetime.fromisoformat(facts['startedAtUTC']),
                             datetime.datetime.fromisoformat(facts['finishedAtUTC']))

    def test_full_build_binds_source_builder_and_actual_output_paths(self):
        result = self.invoke()
        facts = json.loads(self.receipt.read_bytes())
        self.assertEqual(result, facts)
        self.assert_real_git_and_source_bindings(facts)
        self.assertEqual((facts['schema'], facts['kind']), (1, 'mouse637-host-observer-build'))
        self.assertIs(facts['ok'], True)
        self.assertEqual(facts['errors'], [])
        self.assertEqual((facts['platform'], facts['arch']), ('darwin', 'arm64'))
        self.assertEqual(len(facts['commands']), 10)
        self.assertTrue(all(row['returncode'] == 0 for row in facts['commands']))
        self.assertEqual(facts['compilerVersion'], COMPILER_OUTPUT.decode().strip())
        self.assertEqual(facts['sdkPath'], SDK_PATH.decode().strip())
        self.assertEqual(facts['sdkVersion'], SDK_VERSION.decode().strip())
        self.assertEqual(facts['command'], self.xcrun_calls[-2])
        self.assertEqual(facts['binary'], {'filename': self.output.name, 'path': str(self.output),
                                         'size': len(FAKE_BINARY), 'sha256': digest(self.output.read_bytes()), 'arch': 'arm64'})
        self.assertEqual(self.output.read_bytes(), FAKE_BINARY)
        self.assertEqual(self.xcrun_calls[-1], ['xcrun', 'lipo', '-archs', str(self.output)])
        self.assertEqual(self.stdout.getvalue(), 'MOUSE_637_HOST_OBSERVER_BUILD_PASS\n')

    def test_compile_failure_keeps_original_receipt_and_never_runs_lipo(self):
        with self.assertRaisesRegex(RuntimeError, 'Observer build command failed or exceeded its output bound'):
            self.invoke(fail_compile=True)
        facts = json.loads(self.receipt.read_bytes())
        self.assert_real_git_and_source_bindings(facts)
        self.assertIs(facts['ok'], False)
        self.assertEqual(len(facts['commands']), 9)
        self.assertEqual(len(self.xcrun_calls), 4)
        self.assertEqual(facts['commands'][-1], {'argv': facts['command'], 'returncode': 23,
                                               'output': 'Synthetic compiler failure retained verbatim\n'})
        self.assertEqual(facts['errors'], ['RuntimeError: Observer build command failed or exceeded its output bound'])
        self.assertFalse(any('lipo' in argv for argv in self.xcrun_calls))
        self.assertNotIn('binary', facts)
        self.assertFalse(self.output.exists())
        self.assertNotIn('MOUSE_637_HOST_OBSERVER_BUILD_PASS', self.stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
