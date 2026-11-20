"""Exercise the actual publisher wrapper functions without loading pending pins.

PNG/task semantics have their own unchanged twelve-case checker suite. Here only
that expensive downstream dependency is mocked; all publisher wrapper and byte
binding decisions execute the exact function AST read from the publisher files.
"""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parent
MARKERS = ('MOUSE_631_TASK_ONLY_NATIVE_PASS', 'MOUSE_631_FIFTY_TABS_FIVE_DESKTOPS_NATIVE_PASS',
           'MOUSE_631_INSTALLED_TASK_STRESS_PASS', 'MOUSE_632_STATIONARY_MEDIA_PASS')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def wrapper(platform):
    return {'ok': True, 'version': '6.0.32', 'platform': platform,
            'arch': 'arm64' if platform == 'darwin' else 'x64', 'pid': 3120,
            'budgetMs': 350000, 'elapsedMs': 120000,
            'physicalUserDeviceVerified': False, 'liveExternalAccountsVerified': False,
            'stages': [{'name': 'taskOnly', 'ok': True, 'elapsedMs': 20000},
                       {'name': 'fiftyTabs', 'ok': True, 'elapsedMs': 70000},
                       {'name': 'stationaryMedia', 'ok': True, 'elapsedMs': 20000}]}


def extract(platform, verifier):
    filename = 'mouse632-release.py' if platform == 'darwin' else 'mouse632-windows-release.py'
    name = 'verify_631' if platform == 'darwin' else 'verify_task_evidence'
    path = ROOT / filename
    functions = [node for node in ast.parse(path.read_text()).body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(functions) != 1:
        raise AssertionError('Expected one actual publisher function: ' + name)
    namespace = {'json': json, 'sha': sha, 'Path': Path, 'V': '6.0.32', 'VERSION': '6.0.32',
                 '__file__': str(path), '_tasks': {'verify': verifier}}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[name]


class NativeReportTests(unittest.TestCase):
    def invoke(self, platform, native=None, *, raw=None, markers=MARKERS, wrong_binding=None, archive=False,
               checker_error=None):
        report = wrapper(platform) if native is None else native
        data = json.dumps(report).encode() if raw is None else raw
        files = {'mouse-631-native.json': data, 'mouse-631-native.log': ('\n'.join(markers) + '\n').encode(),
                 'mouse-631-task.json': b'{"unit":"task"}', 'mouse-631-stress.json': b'{"unit":"stress"}',
                 'mouse-632-media.json': b'{"unit":"stationaryMedia"}'}
        keys = {'mouse-631-native.json': 'reportSha256', 'mouse-631-task.json': 'taskSha256',
                'mouse-631-stress.json': 'stressSha256', 'mouse-632-media.json': 'mediaSha256'}
        bound = {key: sha(files[name]) for name, key in keys.items()}
        if wrong_binding:
            bound[wrong_binding] = '0' * 64
        value = {'checks': {'taskAndFiftyTabs': bound}}
        checker = mock.Mock(return_value={'ok': True, 'downstreamChecked': True}, side_effect=checker_error)
        function = extract(platform, checker)

        def run(read):
            with mock.patch('runpy.run_path', return_value={'verify': checker}):
                result = function(read) if platform == 'darwin' else function(read, value)
            self.assertEqual(result['nativeReportSHA256'], sha(data))
            self.assertTrue(result['downstreamChecked'])
            checker.assert_called_once_with(read, expected_platform=platform,
                                            expected_arch='arm64' if platform == 'darwin' else 'x64')
            return result

        if archive:
            memory = io.BytesIO()
            with zipfile.ZipFile(memory, 'w') as output:
                for name, contents in files.items():
                    output.writestr(name, contents)
            with zipfile.ZipFile(io.BytesIO(memory.getvalue())) as source:
                return run(source.read)
        return run(files.__getitem__)

    def test_valid_directory_and_archive_readers_keep_wrapper_sha_and_downstream_gate(self):
        for platform in ('darwin', 'win32'):
            for archive in (False, True):
                with self.subTest(platform=platform, archive=archive):
                    self.invoke(platform, archive=archive)

    def test_failed_wrong_identity_or_unsupported_scope_is_rejected(self):
        changes = [('ok', False), ('error', {'message': 'native failed'}), ('version', '6.0.30'),
                   ('platform', 'linux'), ('arch', 'ia32'), ('physicalUserDeviceVerified', True),
                   ('liveExternalAccountsVerified', True), ('liveExternalAccountsVerified', None)]
        for platform in ('darwin', 'win32'):
            for key, value in changes:
                with self.subTest(platform=platform, field=key, value=value):
                    native = wrapper(platform)
                    native[key] = value
                    with self.assertRaises(ValueError):
                        self.invoke(platform, native)

    def test_missing_oversized_or_nonobject_wrapper_cannot_pass(self):
        for platform in ('darwin', 'win32'):
            for raw in (b'', b' ' * (64 * 1024 + 1), b'[]', b'null', b'{}', b'invalid json'):
                with self.subTest(platform=platform, size=len(raw)):
                    with self.assertRaises(ValueError):
                        self.invoke(platform, raw=raw)

    def test_pid_and_fixed_budget_must_be_real_and_positive(self):
        for platform in ('darwin', 'win32'):
            for key, value in [('pid', 0), ('pid', -1), ('pid', True), ('pid', 31.2), ('pid', '3120'),
                               ('budgetMs', 350001), ('budgetMs', 349999), ('budgetMs', None)]:
                with self.subTest(platform=platform, field=key, value=value):
                    native = wrapper(platform)
                    native[key] = value
                    with self.assertRaises(ValueError):
                        self.invoke(platform, native)

    def test_overall_duration_must_fit_the_original_process_budget(self):
        for platform in ('darwin', 'win32'):
            for value in (0, -1, 350001, float('nan'), float('inf'), True, '120000'):
                with self.subTest(platform=platform, elapsed=value):
                    native = wrapper(platform)
                    native['elapsedMs'] = value
                    with self.assertRaises(ValueError):
                        self.invoke(platform, native)

    def test_exact_three_successful_ordered_stages_are_required(self):
        for platform in ('darwin', 'win32'):
            valid = wrapper(platform)['stages']
            changes = [None, [], valid[:1], valid[:2], valid[::-1], valid + [valid[0]],
                       [valid[0], valid[1], valid[1]],
                       [valid[0], {**valid[1], 'ok': False}, valid[2]],
                       [valid[0], valid[1], {**valid[2], 'ok': False}],
                       [valid[0], valid[1], {'name': 'stationaryMedia', 'ok': True}]]
            for stages in changes:
                with self.subTest(platform=platform, stages=stages):
                    native = wrapper(platform)
                    native['stages'] = copy.deepcopy(stages)
                    with self.assertRaises(ValueError):
                        self.invoke(platform, native)

    def test_stage_time_cannot_be_invalid_or_exceed_the_complete_process(self):
        for platform in ('darwin', 'win32'):
            for value in (0, -1, 120001, float('nan'), float('inf'), True, '90000'):
                with self.subTest(platform=platform, elapsed=value):
                    native = wrapper(platform)
                    native['stages'][1]['elapsedMs'] = value
                    with self.assertRaises(ValueError):
                        self.invoke(platform, native)
            native = wrapper(platform)
            native['stages'][0]['elapsedMs'] = 80000
            with self.assertRaisesRegex(ValueError, 'durations exceed'):
                self.invoke(platform, native)

    def test_mac_requires_each_exact_native_success_log_line(self):
        for index in range(len(MARKERS)):
            for replacement in ('', 'prefix-' + MARKERS[index]):
                markers = list(MARKERS)
                markers[index] = replacement
                with self.subTest(marker=MARKERS[index], replacement=replacement):
                    with self.assertRaisesRegex(ValueError, 'success marker missing'):
                        self.invoke('darwin', markers=markers)

    def test_windows_retains_all_four_report_hash_bindings(self):
        for name in ('reportSha256', 'taskSha256', 'stressSha256', 'mediaSha256'):
            with self.subTest(binding=name):
                with self.assertRaisesRegex(ValueError, 'evidence bytes differ'):
                    self.invoke('win32', wrong_binding=name)

    def test_successful_wrapper_cannot_bypass_independent_pixel_or_task_failure(self):
        for platform in ('darwin', 'win32'):
            with self.subTest(platform=platform):
                with self.assertRaisesRegex(ValueError, 'actual pixel mismatch'):
                    self.invoke(platform, checker_error=ValueError('actual pixel mismatch'))


if __name__ == '__main__':
    unittest.main()
