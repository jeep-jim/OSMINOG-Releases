#!/usr/bin/env python3
"""Offline publisher contract tests; every report below is a synthetic fixture.

These tests exercise rejection rules only. They do not install Mouse, run an
updater, inspect native windows, or constitute Windows release evidence.
"""
from pathlib import Path
from copy import deepcopy
import json
import runpy
import subprocess
import tempfile
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


def pin_fixture():
    """Synthetic provenance for branch guards; never a real candidate pin."""
    return {
        'version': '6.0.29', 'ready': True, 'sourceBranch': 'release/mouse-6.0.29',
        'source': '1' * 40, 'sourceMerge': '2' * 40,
        'artifactSHA256': '3' * 64, 'verificationSHA256': '4' * 64,
        'sourcePR': 172, 'run': 1, 'attempt': 1, 'job': 2, 'artifact': 3,
        'verificationArtifact': 4,
        'package': {'name': 'Mouse-Browser-6.0.29-Windows-x64.exe',
                    'size': 100 * 1024**2, 'sha256': '5' * 64},
    }


class WindowsPublisherSourceBranch(unittest.TestCase):
    def validate_pin(self, value):
        with tempfile.TemporaryDirectory(prefix='mouse-publisher-pin-fixture-') as temporary:
            stage = Path(temporary)
            (stage / 'pin.json').write_text(json.dumps(value), encoding='utf-8')
            (stage / 'PUBLISH_OWNER').write_text('Publish verified Mouse Browser 6.0.29 Windows x64', encoding='utf-8')
            with patch.dict(PUBLISHER['pin'].__globals__, {'STAGE': stage}):
                return PUBLISHER['pin']()

    def test_fixed_629_pin_branch_is_accepted(self):
        value = pin_fixture()
        self.assertEqual(self.validate_pin(value), value)
        self.assertEqual(PUBLISHER['SOURCE_BRANCH'], 'release/mouse-6.0.29')

    def test_pin_rejects_main_missing_and_other_release_branches(self):
        for branch in [None, '', 'main', 'release/mouse-6.0.30', 'refs/heads/release/mouse-6.0.29']:
            with self.subTest(branch=branch):
                value = pin_fixture()
                if branch is None:
                    value.pop('sourceBranch')
                else:
                    value['sourceBranch'] = branch
                with self.assertRaisesRegex(ValueError, 'fixed 6.0.29 source branch'):
                    self.validate_pin(value)

    def source_merge(self, *, base='release/mouse-6.0.29', merged=True,
                     head=None, merge=None, status='ahead', behind=0):
        value = pin_fixture()
        calls = []

        def fixture_api(repo, resource):
            self.assertEqual(repo, 'jeep-jim/OSMINOG')
            calls.append(resource)
            if resource == 'pulls/172':
                return {'merged': merged, 'head': {'sha': head or value['source']},
                        'merge_commit_sha': merge or value['sourceMerge'], 'base': {'ref': base}}
            self.assertEqual(resource, 'compare/' + value['source'] + '...release%2Fmouse-6.0.29')
            return {'status': status, 'behind_by': behind}

        with patch.dict(PUBLISHER['verify_source_merge'].__globals__, {'api': fixture_api}):
            PUBLISHER['verify_source_merge'](value)
        return calls

    def test_merged_source_is_compared_to_only_the_fixed_release_branch(self):
        for status in ['ahead', 'identical']:
            with self.subTest(status=status):
                self.assertEqual(len(self.source_merge(status=status)), 2)

    def test_merge_into_main_or_another_branch_is_rejected(self):
        for base in ['main', 'release/mouse-6.0.30', '']:
            with self.subTest(base=base):
                with self.assertRaisesRegex(ValueError, 'not merged into the fixed'):
                    self.source_merge(base=base)

    def test_exact_tested_head_and_merge_are_still_required(self):
        for change in [{'merged': False}, {'head': '6' * 40}, {'merge': '7' * 40}]:
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError, 'not merged into the fixed'):
                    self.source_merge(**change)

    def test_diverged_or_behind_source_cannot_be_published(self):
        for change in [{'status': 'diverged'}, {'status': 'behind'}, {'behind': 1}]:
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError, 'not an ancestor'):
                    self.source_merge(**change)


def source_run_fixture():
    """Synthetic completed workflow with both required Windows host jobs."""
    p = pin_fixture()
    run = {'head_sha': p['source'], 'path': '.github/workflows/mouse-windows.yml',
           'status': 'completed', 'conclusion': 'success', 'run_attempt': p['attempt']}
    identity = {'run_id': p['run'], 'run_attempt': p['attempt'], 'head_sha': p['source'],
                'status': 'completed', 'conclusion': 'success'}
    build_steps = ['Run retained and Windows Mouse tests', 'Build Mouse Browser NSIS installer',
                   'Verify installed app, native UI, restart and profile preservation',
                   'Bind verified installer bytes to source and test evidence',
                   'Require both unit and installed acceptance']
    modern_steps = ['Verify immutable installer and source evidence',
                    'Verify same installed app on modern Windows',
                    'Upload modern Windows verification evidence']
    jobs = [{**identity, 'id': p['job'], 'name': 'mouse-windows-x64',
             'steps': [{'name': name, 'status': 'completed', 'conclusion': 'success'} for name in build_steps]},
            {**identity, 'id': 99, 'name': 'mouse-windows-x64-modern',
             'steps': [{'name': name, 'status': 'completed', 'conclusion': 'success'} for name in modern_steps]}]
    return p, run, jobs


class WindowsPublisherModernSourceGate(unittest.TestCase):
    def validate(self, *, run=None, jobs=None):
        p, default_run, default_jobs = source_run_fixture()
        run = default_run if run is None else run
        jobs = default_jobs if jobs is None else jobs
        calls = []

        def fixture_api(repo, resource):
            self.assertEqual(repo, 'jeep-jim/OSMINOG')
            calls.append(resource)
            if resource == 'actions/runs/1':
                return run
            self.assertEqual(resource, 'actions/runs/1/attempts/1/jobs?per_page=100')
            return {'jobs': jobs}

        with patch.dict(PUBLISHER['verify_source_run'].__globals__, {'api': fixture_api}):
            PUBLISHER['verify_source_run'](p)
        return calls

    def test_complete_current_attempt_with_both_hosts_is_accepted(self):
        self.assertEqual(self.validate(), ['actions/runs/1', 'actions/runs/1/attempts/1/jobs?per_page=100'])

    def test_overall_failed_or_unfinished_run_is_rejected(self):
        for change in [{'conclusion': 'failure'}, {'conclusion': 'cancelled'}, {'conclusion': 'skipped'},
                       {'status': 'in_progress', 'conclusion': None}, {'status': 'queued', 'conclusion': None}]:
            with self.subTest(change=change):
                _, run, _ = source_run_fixture()
                run.update(change)
                with self.assertRaisesRegex(ValueError, 'not completed successfully'):
                    self.validate(run=run)

    def test_overall_run_attempt_must_match_the_pin(self):
        for attempt in [None, 0, 2, '1']:
            with self.subTest(attempt=attempt):
                _, run, _ = source_run_fixture()
                run['run_attempt'] = attempt
                with self.assertRaisesRegex(ValueError, 'not the pinned attempt'):
                    self.validate(run=run)

    def test_modern_job_must_exist_exactly_once(self):
        _, _, complete = source_run_fixture()
        for jobs in [complete[:1], complete + [deepcopy(complete[1])], []]:
            with self.subTest(job_count=len(jobs)):
                with self.assertRaises(ValueError):
                    self.validate(jobs=jobs)

    def test_modern_job_must_complete_successfully(self):
        for change in [{'conclusion': 'failure'}, {'conclusion': 'skipped'}, {'conclusion': 'cancelled'},
                       {'status': 'in_progress', 'conclusion': None}]:
            with self.subTest(change=change):
                _, _, jobs = source_run_fixture()
                jobs[1].update(change)
                with self.assertRaisesRegex(ValueError, 'Modern Windows installed verification job has not passed'):
                    self.validate(jobs=jobs)

    def test_modern_job_must_match_source_run_and_attempt(self):
        for change in [{'run_attempt': 2}, {'run_attempt': None}, {'run_id': 999}, {'head_sha': '6' * 40}]:
            with self.subTest(change=change):
                _, _, jobs = source_run_fixture()
                jobs[1].update(change)
                with self.assertRaisesRegex(ValueError, 'Modern Windows job is not from the pinned source attempt'):
                    self.validate(jobs=jobs)

    def test_every_modern_gate_and_evidence_upload_must_succeed(self):
        for index in range(3):
            for change in [None, {'conclusion': 'failure'}, {'conclusion': 'skipped'}, {'status': 'in_progress'}]:
                with self.subTest(step=index, change=change):
                    _, _, jobs = source_run_fixture()
                    if change is None:
                        jobs[1]['steps'].pop(index)
                    else:
                        jobs[1]['steps'][index].update(change)
                    with self.assertRaisesRegex(ValueError, 'did not execute every modern release gate'):
                        self.validate(jobs=jobs)

    def test_original_build_identity_and_required_unit_gate_still_apply(self):
        for change in [{'id': 999}, {'run_attempt': 2}, {'run_id': 999}, {'head_sha': '6' * 40}]:
            with self.subTest(change=change):
                _, _, jobs = source_run_fixture()
                jobs[0].update(change)
                with self.assertRaises(ValueError):
                    self.validate(jobs=jobs)
        _, _, jobs = source_run_fixture()
        jobs[0]['steps'][0]['conclusion'] = 'skipped'
        with self.assertRaisesRegex(ValueError, 'Source job did not execute every release gate'):
            self.validate(jobs=jobs)

    def test_original_source_workflow_identity_is_still_required(self):
        for change in [{'head_sha': '6' * 40}, {'path': '.github/workflows/unrelated.yml'}]:
            with self.subTest(change=change):
                _, run, _ = source_run_fixture()
                run.update(change)
                with self.assertRaisesRegex(ValueError, 'Pinned run is not the Windows source workflow'):
                    self.validate(run=run)

    def test_import_rejects_missing_modern_job_before_reading_artifacts(self):
        p, run, jobs = source_run_fixture()

        def fixture_api(repo, resource):
            self.assertEqual(repo, 'jeep-jim/OSMINOG')
            if resource == 'actions/runs/1':
                return run
            self.assertEqual(resource, 'actions/runs/1/attempts/1/jobs?per_page=100')
            return {'jobs': jobs[:1]}

        def forbidden(*args, **kwargs):
            raise AssertionError('Incomplete source run must stop before merge/artifact access')

        with patch.dict(PUBLISHER['import_candidate'].__globals__,
                        {'pin': lambda: p, 'api': fixture_api, 'verify_source_merge': forbidden,
                         'read_artifact': forbidden}):
            with self.assertRaisesRegex(ValueError, 'Modern Windows installed verification job has not passed'):
                PUBLISHER['import_candidate']()


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
