#!/usr/bin/env python3
"""Offline publisher contract tests; every report below is a synthetic fixture.

These tests exercise rejection rules only. They do not install Mouse, run an
updater, inspect native windows, or constitute Windows release evidence.
"""
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name('mouse629-windows-release.py')
with patch.object(subprocess, 'run', side_effect=AssertionError('No external commands in fixture tests')), \
        patch.object(subprocess, 'check_output', side_effect=AssertionError('No external commands in fixture tests')):
    PUBLISHER = runpy.run_path(str(SCRIPT))


def report_fixture():
    """Return an in-memory schema example, never a claim about a real run."""
    install = {'exitCode': 0, 'peMachine': '0x8664', 'unicodeAndSpaces': True}
    return {
        'ok': True,
        'version': '6.0.29',
        'platform': 'win32',
        'arch': 'x64',
        'checks': {
            'installation': dict(install),
            'write': {'exitCode': 0},
            'read': {'exitCode': 0},
            'reinstallation': {**install, 'profileUnchanged': True},
            'actualUpdateButton': {
                'ok': True,
                'exitCode': 0,
                'pid': 101,
                'sameVersion': True,
                'transport': 'owned local installer stream',
                'publicChannelDownloadVerified': False,
                'downloadButton': True,
                'installButton': True,
                'receiptAcknowledged': True,
                'helperResult': 'Installer completed',
                'newWindow': {
                    'pid': 202,
                    'title': 'Mouse Browser',
                    'minimized': False,
                    'handle': 1048576,
                },
                'profileRetestedAfterward': True,
            },
            'postUpdateProfile': {'exitCode': 0},
            'ordinaryLaunch': {
                'ok': True,
                'nativeCloseExitCode': 0,
                'secondInstance': {'exitCode': 0},
            },
        },
    }


class WindowsPublisherContract(unittest.TestCase):
    def validate(self, value):
        with patch.object(subprocess, 'run', side_effect=AssertionError('Unexpected external command')), \
                patch.object(subprocess, 'check_output', side_effect=AssertionError('Unexpected external command')):
            return PUBLISHER['verification'](value)

    def reject(self, mutate):
        report = report_fixture()
        mutate(report)
        with self.assertRaises(ValueError):
            self.validate(report)

    def test_complete_synthetic_schema_is_accepted(self):
        self.validate(report_fixture())

    def test_01_top_level_success_must_be_true(self):
        for value in [False, None, 1, 'true']:
            with self.subTest(value=value):
                self.reject(lambda r: r.update(ok=value))

    def test_02_version_and_platform_identity_are_exact(self):
        for field, value in [('version', '6.0.28'), ('platform', 'darwin'), ('arch', 'arm64')]:
            with self.subTest(field=field):
                self.reject(lambda r: r.update({field: value}))

    def test_03_every_installed_stage_is_required(self):
        for stage in report_fixture()['checks']:
            with self.subTest(stage=stage):
                self.reject(lambda r: r['checks'].pop(stage))

    def test_04_installer_and_profile_processes_must_exit_successfully(self):
        for stage in ['installation', 'write', 'read', 'reinstallation', 'postUpdateProfile']:
            with self.subTest(stage=stage):
                self.reject(lambda r: r['checks'][stage].update(exitCode=1))

    def test_05_installed_executables_must_be_amd64(self):
        for stage in ['installation', 'reinstallation']:
            with self.subTest(stage=stage):
                self.reject(lambda r: r['checks'][stage].update(peMachine='0xaa64'))

    def test_06_both_installs_must_exercise_unicode_and_spaces(self):
        for stage in ['installation', 'reinstallation']:
            with self.subTest(stage=stage):
                self.reject(lambda r: r['checks'][stage].update(unicodeAndSpaces=False))

    def test_07_reinstallation_must_preserve_profile_bytes(self):
        self.reject(lambda r: r['checks']['reinstallation'].update(profileUnchanged=False))

    def test_08_actual_update_acceptance_flags_cannot_be_missing_or_truthy(self):
        fields = ['ok', 'sameVersion', 'downloadButton', 'installButton',
                  'receiptAcknowledged', 'profileRetestedAfterward']
        for field in fields:
            for value in [False, None, 1, 'true']:
                with self.subTest(field=field, value=value):
                    self.reject(lambda r: r['checks']['actualUpdateButton'].update({field: value}))

    def test_09_update_transport_must_disclose_owned_local_bytes(self):
        self.reject(lambda r: r['checks']['actualUpdateButton'].update(transport='public channel'))

    def test_10_local_update_fixture_must_not_claim_public_download(self):
        for value in [True, None, 0, 'false']:
            with self.subTest(value=value):
                self.reject(lambda r: r['checks']['actualUpdateButton'].update(publicChannelDownloadVerified=value))

    def test_11_update_helper_and_original_app_must_complete(self):
        for change in [{'exitCode': 1}, {'helperResult': 'Installer exited with code 1'}]:
            with self.subTest(change=change):
                self.reject(lambda r: r['checks']['actualUpdateButton'].update(change))

    def test_12_updated_window_must_belong_to_a_new_process(self):
        for pid in [101, 0, -1, '202']:
            with self.subTest(pid=pid):
                self.reject(lambda r: r['checks']['actualUpdateButton']['newWindow'].update(pid=pid))

    def test_13_updated_window_must_be_visible_and_identified(self):
        for change in [{'title': 'Unrelated app'}, {'minimized': True}, {'handle': 0}]:
            with self.subTest(change=change):
                self.reject(lambda r: r['checks']['actualUpdateButton']['newWindow'].update(change))

    def test_14_ordinary_launch_and_native_close_are_required(self):
        for change in [{'ok': False}, {'nativeCloseExitCode': 1}]:
            with self.subTest(change=change):
                self.reject(lambda r: r['checks']['ordinaryLaunch'].update(change))

    def test_15_second_instance_must_finish_without_error(self):
        self.reject(lambda r: r['checks']['ordinaryLaunch']['secondInstance'].update(exitCode=1))


if __name__ == '__main__':
    unittest.main()
