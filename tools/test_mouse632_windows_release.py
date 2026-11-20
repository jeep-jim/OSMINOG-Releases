#!/usr/bin/env python3
"""Offline publisher contract tests; every report below is a synthetic fixture.

These tests exercise rejection rules only. They do not install Mouse, run an
updater, inspect native windows, or constitute Windows release evidence.
"""
from pathlib import Path
from copy import deepcopy
from contextlib import redirect_stdout
import ast
import io
import json
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name('mouse632-windows-release.py')
with patch.object(subprocess, 'run', side_effect=AssertionError('No external commands in fixture tests')), \
        patch.object(subprocess, 'check_output', side_effect=AssertionError('No external commands in fixture tests')):
    PUBLISHER = runpy.run_path(str(SCRIPT))


def report_fixture():
    """Return an in-memory schema example, never a claim about a real run."""
    install = {'exitCode': 0, 'peMachine': '0x8664', 'unicodeAndSpaces': True}
    return {
        'ok': True,
        'version': '6.0.32',
        'platform': 'win32',
        'arch': 'x64',
        'checks': {
            'taskAndFiftyTabs': {'exitCode': 0,
                'requiredMarkers': ['MOUSE_631_TASK_ONLY_NATIVE_PASS', 'MOUSE_631_FIFTY_TABS_FIVE_DESKTOPS_NATIVE_PASS', 'MOUSE_631_INSTALLED_TASK_STRESS_PASS', 'MOUSE_632_STATIONARY_MEDIA_PASS'],
                'reportSha256': 'a'*64, 'taskSha256': 'b'*64, 'stressSha256': 'c'*64, 'mediaSha256':'d'*64},
            'versionUpgrade': {'ok': True, 'fromVersion': '6.0.29', 'toVersion': '6.0.32',
                'closedProfileUnchanged': True, 'closedProfileSha256': 'd'*64,
                'oldReportSha256': 'e'*64, 'newReportSha256': 'f'*64,
                'baseline': {'url': 'https://github.com/jeep-jim/OSMINOG-Releases/releases/download/mouse-windows-v6.0.29-x64/Mouse-Browser-6.0.29-Windows-x64.exe',
                    'size': 125623123, 'sha256': '18bf6e78eb5519e37d2ceb0e45acd1ea88d8f519e715e1d94d2fbc3c476e2e9d'},
                'oldInstallation': dict(install), 'oldWrite': {'exitCode': 0, 'pid': 303},
                'replacement': dict(install), 'newRead': {'exitCode': 0, 'pid': 404},
                'preserved': {'previousVersion': '6.0.29', 'currentVersion': '6.0.32',
                    'differentProcess': True, 'preferencesPreserved': True, 'cookiePreserved': True,
                    'localStoragePreserved': True, 'bookmarkPreserved': True}},
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
        'version': '6.0.32', 'ready': True, 'sourceBranch': 'main',
        'previous': deepcopy(PUBLISHER['PREVIOUS_WINDOWS']),
        'source': '1' * 40, 'sourceMerge': '2' * 40,
        'artifactSHA256': '3' * 64, 'verificationSHA256': '4' * 64,
        'sourcePR': 172, 'run': 1, 'attempt': 1, 'job': 2, 'artifact': 3,
        'verificationArtifact': 4,
        'package': {'name': 'Mouse-Browser-6.0.32-Windows-x64.exe',
                    'size': 100 * 1024**2, 'sha256': '5' * 64},
    }


class WindowsPublisherSourceBranch(unittest.TestCase):
    def validate_pin(self, value, owner='Publish verified Mouse Browser 6.0.32 Windows x64'):
        with tempfile.TemporaryDirectory(prefix='mouse-publisher-pin-fixture-') as temporary:
            stage = Path(temporary)
            (stage / 'pin.json').write_text(json.dumps(value), encoding='utf-8')
            if owner is not None:
                (stage / 'PUBLISH_OWNER').write_text(owner, encoding='utf-8')
            with patch.dict(PUBLISHER['pin'].__globals__, {'STAGE': stage}):
                return PUBLISHER['pin']()

    def test_shared_main_pin_branch_is_accepted(self):
        value = pin_fixture()
        self.assertEqual(self.validate_pin(value), value)
        self.assertEqual(PUBLISHER['SOURCE_BRANCH'], 'main')

    def test_pipeline_retry_still_requires_the_exact_owner_trigger(self):
        for owner in ['', 'UNSET', 'Publish verified Mouse Browser 6.0.31 Windows x64']:
            with self.subTest(owner=owner), self.assertRaisesRegex(ValueError, 'publication trigger'):
                self.validate_pin(pin_fixture(), owner=owner)
        with self.assertRaises(FileNotFoundError):
            self.validate_pin(pin_fixture(), owner=None)

    def test_unready_staging_cannot_publish_placeholder_provenance(self):
        stage = SCRIPT.parents[1] / 'staging/mouse/6.0.32-windows-x64/pin.json'
        value = json.loads(stage.read_text(encoding='utf-8'))
        if value['ready'] is False:
            with self.assertRaisesRegex(ValueError, 'pin is not ready'):
                self.validate_pin(value)
        value = pin_fixture()
        for ready in [False, None, 1, 'true']:
            with self.subTest(ready=ready):
                value['ready'] = ready
                with self.assertRaisesRegex(ValueError, 'pin is not ready'):
                    self.validate_pin(value)

    def test_candidate_still_requires_every_immutable_hash_and_run_identity(self):
        for field in ['source', 'sourceMerge', 'artifactSHA256', 'verificationSHA256',
                      'sourcePR', 'run', 'attempt', 'job', 'artifact', 'verificationArtifact']:
            value = pin_fixture()
            value.pop(field)
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate_pin(value)

    def test_pin_rejects_missing_and_maintenance_branches(self):
        for branch in [None, '', 'release/mouse-6.0.29', 'release/mouse-6.0.30', 'refs/heads/main']:
            with self.subTest(branch=branch):
                value = pin_fixture()
                if branch is None:
                    value.pop('sourceBranch')
                else:
                    value['sourceBranch'] = branch
                with self.assertRaisesRegex(ValueError, 'fixed 6.0.32 source branch'):
                    self.validate_pin(value)

    def source_merge(self, *, base='main', merged=True,
                     head=None, merge=None, status='ahead', behind=0):
        value = pin_fixture()
        calls = []

        def fixture_api(repo, resource):
            self.assertEqual(repo, 'jeep-jim/OSMINOG')
            calls.append(resource)
            if resource == 'pulls/172':
                return {'merged': merged, 'head': {'sha': head or value['source']},
                        'merge_commit_sha': merge or value['sourceMerge'], 'base': {'ref': base}}
            self.assertEqual(resource, 'compare/' + value['source'] + '...main')
            return {'status': status, 'behind_by': behind}

        with patch.dict(PUBLISHER['verify_source_merge'].__globals__, {'api': fixture_api}):
            PUBLISHER['verify_source_merge'](value)
        return calls

    def test_merged_source_is_compared_to_shared_main(self):
        for status in ['ahead', 'identical']:
            with self.subTest(status=status):
                self.assertEqual(len(self.source_merge(status=status)), 2)

    def test_merge_into_maintenance_or_another_branch_is_rejected(self):
        for base in ['release/mouse-6.0.29', 'release/mouse-6.0.30', '']:
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


def release_notes_fixture(p, publisher='current'):
    return (f'Source: https://github.com/jeep-jim/OSMINOG/commit/{p["source"]}\n'
            f'Source checks: https://github.com/jeep-jim/OSMINOG/actions/runs/{p["run"]}\n'
            f'Independent installation: fixture-{publisher}\n\n'
            + p['package']['sha256'] + '  ' + p['package']['name'] + '\n')


def release_fixture(p, release_id=71, draft=True):
    return {'id': release_id, 'url': f'https://api.github.com/repos/jeep-jim/OSMINOG-Releases/releases/{release_id}',
            'tag_name': 'mouse-windows-v6.0.32-x64', 'name': 'Mouse Browser 6.0.32 — Windows x64',
            'draft': draft, 'prerelease': True, 'assets': [], 'body': release_notes_fixture(p, 'previous'),
            'published_at': None if draft else '2026-01-01T00:00:00Z'}


class WindowsPublisherDraftLookup(unittest.TestCase):
    def lookup(self, *, published=None, pages=None, records=None):
        p = pin_fixture()
        calls = []
        pages = [[]] if pages is None else pages
        records = {} if records is None else records

        def fixture_api(repo, resource, method='GET', payload=None, missing=False):
            self.assertEqual(repo, 'jeep-jim/OSMINOG-Releases')
            self.assertEqual(method, 'GET', 'Lookup must not create or modify a release')
            self.assertIsNone(payload)
            calls.append(resource)
            if resource == 'releases/tags/mouse-windows-v6.0.32-x64':
                self.assertTrue(missing)
                return deepcopy(published)
            if resource.startswith('releases?per_page=100&page='):
                return deepcopy(pages[int(resource.rsplit('=', 1)[1]) - 1])
            return deepcopy(records[int(resource.split('/')[1])])

        with patch.dict(PUBLISHER['find_release'].__globals__, {'api': fixture_api}):
            result = PUBLISHER['find_release'](p)
        return result, calls

    def test_published_release_reuses_same_id_without_duplicate_listing_match(self):
        release = release_fixture(pin_fixture(), draft=False)
        result, calls = self.lookup(published=release, pages=[[release]], records={71: release})
        self.assertEqual(result, release)
        self.assertEqual(calls, ['releases/tags/mouse-windows-v6.0.32-x64',
                                 'releases?per_page=100&page=1', 'releases/71'])

    def test_exact_draft_on_later_page_survives_public_tag_404(self):
        release = release_fixture(pin_fixture())
        unrelated = [{'id': i + 100, 'tag_name': f'other-{i}', 'draft': True} for i in range(100)]
        result, calls = self.lookup(pages=[unrelated, [release]], records={71: release})
        self.assertEqual(result, release)
        self.assertEqual(calls[-2:], ['releases?per_page=100&page=2', 'releases/71'])
        self.assertEqual(sum('/tags/' in call for call in calls), 1)

    def test_multiple_exact_drafts_across_pages_are_ambiguous(self):
        p = pin_fixture()
        first = [release_fixture(p)] + [{'tag_name': f'other-{i}'} for i in range(99)]
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            self.lookup(pages=[first, [release_fixture(p, 72)]])

    def test_published_release_plus_another_draft_is_ambiguous(self):
        p = pin_fixture()
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            self.lookup(published=release_fixture(p, draft=False), pages=[[release_fixture(p, 72)]])

    def test_full_page_bound_cannot_be_mistaken_for_no_existing_draft(self):
        pages = [[{'tag_name': f'other-{i}'} for i in range(100)]] * PUBLISHER['RELEASE_PAGE_LIMIT']
        with self.assertRaisesRegex(ValueError, 'bounded pagination'):
            self.lookup(pages=pages)

    def test_existing_release_must_match_repository_id_tag_and_source(self):
        p = pin_fixture()
        changes = [{'id': True}, {'id': 0}, {'url': 'https://api.github.com/repos/foreign/repo/releases/71'},
                   {'tag_name': 'quadro-macos-v6.0.32-arm64'}, {'name': 'Unrelated release'},
                   {'draft': 'true'}, {'prerelease': False}, {'assets': None},
                   {'body': release_notes_fixture({**p, 'source': '6' * 40})},
                   {'body': release_notes_fixture({**p, 'run': 999})},
                   {'body': release_notes_fixture({**p, 'package': {**p['package'], 'sha256': '7' * 64}})}]
        for change in changes:
            with self.subTest(change=change):
                value = release_fixture(p)
                value.update(change)
                with self.assertRaises(ValueError):
                    PUBLISHER['release_identity'](value, p)
        with self.assertRaisesRegex(ValueError, 'identity'):
            PUBLISHER['release_identity'](release_fixture(p, 72), p, 71)

    def test_authenticated_listing_error_cannot_trigger_creation(self):
        def failed_api(repo, resource, **kwargs):
            if resource.startswith('releases/tags/'):
                return None
            raise RuntimeError('HTTP 403')
        with patch.dict(PUBLISHER['find_release'].__globals__, {'api': failed_api}):
            with self.assertRaisesRegex(RuntimeError, 'HTTP 403'):
                PUBLISHER['find_release'](pin_fixture())


class WindowsPublisherDraftPublication(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='mouse-publisher-draft-fixture-')
        self.addCleanup(temporary.cleanup)
        self.out = Path(temporary.name)
        self.p = pin_fixture()
        installer = b'MZ synthetic fixture; never executed'
        self.p['package'].update(size=len(installer), sha256=PUBLISHER['sha'](installer))
        self.files = {PUBLISHER['INSTALLER']: installer,
                      'SHA256SUMS.txt': (self.p['package']['sha256'] + '  ' + PUBLISHER['INSTALLER'] + '\n').encode(),
                      'mouse-windows-build.json': b'{"synthetic":true}\n',
                      'mouse-windows-verification.json': (json.dumps(report_fixture()) + '\n').encode(),
                      'RELEASE_NOTES.md': release_notes_fixture(self.p).encode()}
        for name, data in self.files.items():
            (self.out / name).write_bytes(data)
        self.release = release_fixture(self.p)
        self.existing = True
        self.calls = []
        self.uploads = []
        self.corrupt_upload = False
        self.feedback_calls = 0
        self.feedback_error = None

    def asset(self, name):
        data = self.files[name]
        return {'name': name, 'state': 'uploaded', 'size': len(data), 'digest': 'sha256:' + PUBLISHER['sha'](data)}

    def fixture_api(self, repo, resource, method='GET', payload=None, missing=False):
        self.assertEqual(repo, 'jeep-jim/OSMINOG-Releases')
        self.calls.append((resource, method, deepcopy(payload)))
        if method == 'POST':
            self.assertEqual(resource, 'releases')
            self.assertFalse(self.existing, 'An existing draft must never cause another POST')
            self.assertTrue(payload['draft'])
            self.assertTrue(payload['prerelease'])
            self.assertEqual(payload['make_latest'], 'false')
            self.assertEqual(payload['tag_name'], PUBLISHER['TAG'])
            self.release = release_fixture(self.p, 72)
            self.release.update(payload)
            self.existing = True
            return deepcopy(self.release)
        if resource.startswith('releases/tags/'):
            self.assertEqual(method, 'GET')
            self.assertEqual(sum('/tags/' in call[0] for call in self.calls), 1,
                             'Draft operations must never repeat public-by-tag lookup')
            return deepcopy(self.release) if self.existing and not self.release['draft'] else None
        if resource == 'releases?per_page=100&page=1':
            self.assertEqual(method, 'GET')
            return [deepcopy(self.release)] if self.existing else []
        self.assertEqual(resource, f'releases/{self.release["id"]}')
        if method == 'PATCH':
            self.assertEqual(len(self.release['assets']), 4, 'Publish must wait for all asset uploads')
            self.assertEqual(payload, {'draft': False, 'prerelease': True, 'make_latest': 'false',
                                      'body': self.files['RELEASE_NOTES.md'].decode()})
            self.release.update(payload)
            self.release['published_at'] = '2026-01-01T00:00:00Z'
        else:
            self.assertEqual(method, 'GET')
        return deepcopy(self.release)

    def fixture_upload(self, release_id, name):
        self.assertEqual(release_id, self.release['id'])
        self.assertFalse(any(a['name'] == name for a in self.release['assets']), 'Never overwrite an existing asset')
        asset = self.asset(name)
        if self.corrupt_upload and name == PUBLISHER['INSTALLER']:
            asset['digest'] = 'sha256:' + '0' * 64
        self.release['assets'].append(asset)
        self.uploads.append((release_id, name))

    def publish(self):
        def feedback(read):
            self.feedback_calls += 1
            self.assertEqual(read('mouse-windows-verification.json'), self.files['mouse-windows-verification.json'])
            if self.feedback_error:
                raise ValueError(self.feedback_error)
            return {'synthetic':True}
        with patch.dict(PUBLISHER['publish'].__globals__, {'OUT': self.out, 'pin': lambda: self.p,
                         'api': self.fixture_api, 'upload_release_asset': self.fixture_upload,
                         'verify_feedback_evidence':feedback}), \
                patch.object(subprocess, 'run', side_effect=AssertionError('No network in synthetic publication')), \
                redirect_stdout(io.StringIO()):
            PUBLISHER['publish']()

    def test_existing_empty_draft_is_reused_and_published_by_stable_id(self):
        self.publish()
        self.assertFalse(any(method == 'POST' for _, method, _ in self.calls))
        self.assertTrue(all(release_id == 71 for release_id, _ in self.uploads))
        self.assertEqual(self.release['body'], self.files['RELEASE_NOTES.md'].decode())
        self.assertFalse(self.release['draft'])
        self.assertEqual(json.loads((self.out / 'public-release-verification.json').read_text())['id'], 71)
        self.assertEqual(self.feedback_calls, 1)

    def test_failed_current_feedback_blocks_any_remote_release_action(self):
        self.feedback_error = 'actual Mouse632 feedback evidence failed'
        with self.assertRaisesRegex(ValueError, 'actual Mouse632 feedback evidence failed'):
            self.publish()
        self.assertEqual(self.calls, [])
        self.assertEqual(self.uploads, [])

    def test_new_draft_uses_the_id_returned_by_create_api(self):
        self.existing = False
        self.publish()
        self.assertEqual(sum(method == 'POST' for _, method, _ in self.calls), 1)
        self.assertTrue(all(release_id == 72 for release_id, _ in self.uploads))
        self.assertEqual(self.release['id'], 72)

    def test_immutable_mismatch_stops_before_any_upload_or_publication(self):
        asset = self.asset('mouse-windows-build.json')
        asset['digest'] = 'sha256:' + '0' * 64
        self.release['assets'] = [asset]
        with self.assertRaisesRegex(ValueError, 'Refusing to overwrite'):
            self.publish()
        self.assertEqual(self.uploads, [])
        self.assertFalse(any(method in ('POST', 'PATCH') for _, method, _ in self.calls))

    def test_duplicate_or_incomplete_existing_asset_blocks_publication(self):
        asset = self.asset(PUBLISHER['INSTALLER'])
        for assets in [[asset, deepcopy(asset)], [{**asset, 'state': 'starter'}]]:
            with self.subTest(assets=assets):
                self.calls.clear()
                self.release['assets'] = assets
                with self.assertRaisesRegex(ValueError, 'Unexpected existing'):
                    self.publish()
                self.assertEqual(self.uploads, [])

    def test_uploaded_bytes_must_match_before_draft_can_be_published(self):
        self.corrupt_upload = True
        with self.assertRaisesRegex(ValueError, 'Remote release asset checksum mismatch'):
            self.publish()
        self.assertTrue(self.release['draft'])
        self.assertFalse(any(method == 'PATCH' for _, method, _ in self.calls))

    def test_public_rerun_keeps_original_assets_and_original_install_report(self):
        self.release['draft'] = False
        self.release['published_at'] = '2026-01-01T00:00:00Z'
        self.release['assets'] = [self.asset(name) for name in [*PUBLISHER['ASSETS'], 'mouse-windows-verification.json']]
        self.release['assets'][-1]['digest'] = 'sha256:' + '8' * 64
        self.publish()
        self.assertEqual(self.uploads, [])
        self.assertFalse(any(method in ('POST', 'PATCH') for _, method, _ in self.calls))
        self.assertEqual(self.release['assets'][-1]['digest'], 'sha256:' + '8' * 64)

    def test_binary_upload_uses_exact_numeric_id_without_tag_resolution_or_overwrite(self):
        with patch.dict(PUBLISHER['upload_release_asset'].__globals__, {'OUT': self.out}), \
                patch.object(subprocess, 'run') as command:
            PUBLISHER['upload_release_asset'](71, PUBLISHER['INSTALLER'])
        args = command.call_args.args[0]
        self.assertEqual(args, ['gh', 'api',
            'https://uploads.github.com/repos/jeep-jim/OSMINOG-Releases/releases/71/assets?name=Mouse-Browser-6.0.32-Windows-x64.exe',
            '--method', 'POST', '--header', 'Content-Type: application/octet-stream',
            '--input', str(self.out / PUBLISHER['INSTALLER'])])
        self.assertTrue(command.call_args.kwargs['check'])
        self.assertEqual(command.call_args.kwargs['timeout'], 300)
        self.assertEqual((self.out / PUBLISHER['INSTALLER']).read_bytes(), self.files[PUBLISHER['INSTALLER']])


class WindowsCanonicalCheckout(unittest.TestCase):
    def test_pipeline_retry_is_scoped_to_this_windows_version_on_main(self):
        path = SCRIPT.parents[1] / '.github/workflows/publish-mouse632-windows.yml'
        workflow = path.read_text()
        push = workflow.split('  push:\n', 1)[1].split('  workflow_dispatch:\n', 1)[0]
        fields = dict(line.strip().split(': ', 1) for line in push.splitlines() if line.strip())
        self.assertEqual(fields['branches'], '[main]')
        self.assertEqual(ast.literal_eval(fields['paths']), [
            'staging/mouse/6.0.32-windows-x64/PUBLISH_OWNER',
            '.github/workflows/publish-mouse632-windows.yml'])
        publisher = workflow.split('  publish-windows:\n', 1)[1]
        for gate in ["    if: github.event_name != 'pull_request'\n", '    needs: contract\n',
                     '      group: mouse-windows-x64-release\n', '      cancel-in-progress: false\n']:
            self.assertIn(gate, publisher)

    def test_windows_publisher_disables_crlf_conversion_before_checkout(self):
        workflow = SCRIPT.parents[1] / '.github/workflows/publish-mouse632-windows.yml'
        publisher = workflow.read_text().split('  publish-windows:\n', 1)[1]
        steps = publisher.split('    steps:\n', 1)[1]
        before_checkout = steps.split('      - uses: actions/checkout@v4\n', 1)[0]
        self.assertIn('      - name: Preserve exact publisher source bytes on Windows\n', before_checkout)
        self.assertIn('        shell: pwsh\n', before_checkout)
        self.assertIn('        run: git config --global core.autocrlf false\n', before_checkout)

    def test_actual_git_checkout_keeps_the_unchanged_frozen_dependency_chain(self):
        # Controlled Git fixture, not a native Windows or publication result.
        # The real shared checker and its historical hashes run unmodified.
        root = SCRIPT.parents[1]
        sources = [root / '.gitattributes', *sorted(SCRIPT.parent.glob('*.py'))]
        canonical = {path.relative_to(root): path.read_bytes() for path in sources}
        frozen = Path('tools/mouse629-evidence.py')
        with tempfile.TemporaryDirectory(prefix='mouse632-canonical-checkout-') as directory:
            checkout = Path(directory)

            def git(*args):
                return subprocess.run(['git', *args], cwd=checkout, check=True,
                                      capture_output=True, text=True)

            git('init', '-q')
            git('config', 'core.autocrlf', 'false')
            for name, raw in canonical.items():
                path = checkout / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            git('add', '--', '.gitattributes', 'tools')
            for autocrlf in ['true', 'false']:
                with self.subTest(autocrlf=autocrlf):
                    git('config', 'core.autocrlf', autocrlf)
                    for name in canonical:
                        (checkout / name).unlink()
                    git('checkout-index', '--all', '--force')
                    actual = (checkout / frozen).read_bytes()
                    result = subprocess.run([sys.executable, '-c',
                        "import runpy; runpy.run_path('tools/mouse632-ui-evidence.py', "
                        "run_name='controlled_frozen_checker')"], cwd=checkout,
                        env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'},
                        capture_output=True, text=True)
                    if autocrlf == 'true':
                        self.assertNotEqual(actual, canonical[frozen])
                        self.assertEqual(actual.replace(b'\r\n', b'\n'), canonical[frozen])
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('Accepted Mouse629 evidence validator changed', result.stderr)
                    else:
                        self.assertEqual(actual, canonical[frozen])
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        self.assertIn('MOUSE627_REVIEWED_PUBLISHER_TEMPLATE_GATES_PASS', result.stdout)


class WindowsCurrentFeedbackGate(unittest.TestCase):
    @staticmethod
    def wrapper():
        return {'version':'6.0.32', 'platform':'win32', 'arch':'x64', 'restored':True,
                'scrollbars':{'version':'6.0.32', 'synthetic':True}}

    def test_both_independent_contracts_receive_the_actual_archive_reader(self):
        report = self.wrapper()
        raw = json.dumps(report).encode() + b'\n'
        # The source uploads this wrapper, never its temporary standalone JSON.
        files = {'mouse-629-ui-regressions.json':raw}
        read, calls = files.__getitem__, []

        def checker(path, run_name):
            def feedback(actual_read, **target):
                self.assertIs(actual_read, read)
                self.assertEqual(target, {'expected_platform':'win32', 'expected_arch':'x64'})
                calls.append('feedback')
                return {'synthetic':True}

            def scrollbars(facts, actual_read):
                self.assertEqual(facts, report['scrollbars'])
                self.assertIs(actual_read, read)
                calls.append('scrollbars')
                return {'nativeWheelScrolls':12}

            if Path(path).name == 'mouse632-feedback-evidence.py':
                return {'verify':feedback}
            self.assertEqual(Path(path).name, 'mouse632-ui-evidence.py')
            return {'verify_scrollbars':scrollbars}

        with patch.object(runpy, 'run_path', side_effect=checker):
            result = PUBLISHER['verify_feedback_evidence'](read)
        self.assertEqual(calls, ['feedback', 'scrollbars'])
        self.assertEqual(result['scrollbarReport'], 'mouse-629-ui-regressions.json')
        self.assertEqual(result['scrollbarSHA256'], PUBLISHER['sha'](raw))
        self.assertEqual(result['scrollbars']['nativeWheelScrolls'], 12)

    def test_a_failed_feedback_or_scrollbar_checker_cannot_be_ignored(self):
        for failed in ['feedback', 'scrollbars']:
            def checker(path, run_name):
                def verify(*args, **kwargs):
                    if ('feedback' in Path(path).name) is (failed == 'feedback'):
                        raise ValueError('independent '+failed+' rejection')
                    return {'synthetic':True}
                return {'verify':verify, 'verify_scrollbars':verify}

            with self.subTest(failed=failed), patch.object(runpy, 'run_path', side_effect=checker):
                with self.assertRaisesRegex(ValueError, 'independent '+failed+' rejection'):
                    PUBLISHER['verify_feedback_evidence'](lambda name:json.dumps(self.wrapper()).encode())

    def test_wrong_platform_or_failed_ui_wrapper_cannot_supply_scrollbar_evidence(self):
        changes = [{'version':'6.0.29'}, {'platform':'darwin'}, {'arch':'arm64'},
                   {'restored':False}, {'error':'native scrollbar fixture failed'},
                   {'scrollbars':None}, {'scrollbars':[]}]
        for change in changes:
            report = {**self.wrapper(), **change}
            with self.subTest(change=change), patch.object(runpy, 'run_path',
                    return_value={'verify':lambda *args, **kwargs:{'synthetic':True}}):
                with self.assertRaisesRegex(ValueError, 'installed Windows UI report'):
                    PUBLISHER['verify_feedback_evidence'](lambda name:json.dumps(report).encode())

    def test_missing_or_nonobject_actual_wrapper_is_rejected(self):
        for raw in [b'', b'null', b'[]', b'{}', '{}']:
            with self.subTest(raw=raw), patch.object(runpy, 'run_path',
                    return_value={'verify':lambda *args, **kwargs:{'synthetic':True}}):
                with self.assertRaises(ValueError):
                    PUBLISHER['verify_feedback_evidence'](lambda name:raw)


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

    def test_632_task_stress_markers_and_byte_bindings_are_required(self):
        for field in ['requiredMarkers', 'reportSha256', 'taskSha256', 'stressSha256', 'mediaSha256']:
            with self.subTest(field=field):
                self.reject(lambda r: r['checks']['taskAndFiftyTabs'].pop(field))
        self.reject(lambda r: r['checks']['taskAndFiftyTabs'].update(exitCode=1))

    def test_632_upgrade_requires_actual629_bytes_and_distinct_processes(self):
        self.reject(lambda r: r['checks']['versionUpgrade']['baseline'].update(sha256='0'*64))
        self.reject(lambda r: r['checks']['versionUpgrade']['baseline'].update(size=1))
        self.reject(lambda r: r['checks']['versionUpgrade']['newRead'].update(pid=303))
        self.reject(lambda r: r['checks']['versionUpgrade'].update(fromVersion='6.0.28'))
        for field in ['oldInstallation', 'oldWrite', 'replacement', 'newRead']:
            with self.subTest(field=field):
                self.reject(lambda r: r['checks']['versionUpgrade'][field].update(exitCode=1))

    def test_632_all_real_profile_values_and_hashes_are_required(self):
        for field in ['differentProcess', 'preferencesPreserved', 'cookiePreserved', 'localStoragePreserved', 'bookmarkPreserved']:
            with self.subTest(field=field):
                self.reject(lambda r: r['checks']['versionUpgrade']['preserved'].update({field:False}))
        for field in ['closedProfileSha256', 'oldReportSha256', 'newReportSha256']:
            with self.subTest(field=field):
                self.reject(lambda r: r['checks']['versionUpgrade'].pop(field))

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
