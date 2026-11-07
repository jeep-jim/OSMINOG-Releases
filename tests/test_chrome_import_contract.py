"""Local, network-free checks of the Chrome publication boundary.

The integration fixture exercises the real importer against recorded-shaped
GitHub responses. It does not replace the workflow/head/artifact checks.
"""
import base64
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock
import zipfile

MODULE_PATH = pathlib.Path(__file__).resolve().parents[1]/'tools/import_verified_chrome_ci.py'
SPEC = importlib.util.spec_from_file_location('chrome_import', MODULE_PATH)
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)

VERSION = '4.0.37'
PACKAGE = 'OSMINOG-Chrome-4.0.37.zip'
HELPER = 'OSMINOG-Update-Recovery.html'
HEAD = 'a'*40
MERGE = 'b'*40
KEY = 'fixture-only-canonical-key'
UPDATER = b'globalThis.OSMINOGFolderUpdater={version:"2.0.0"};'


def archive_bytes(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries:
            archive.writestr(name, data)
    return stream.getvalue()


def recovery_bytes(version=VERSION, key=KEY, updater=UPDATER):
    config = dict(schema='osminog-updater-recovery/v1', product='OSMINOG', manifestVersion=3,
        manifestKey=key, minimumPackageVersion=version, minimumUpdaterVersion='2.0.0',
        updaterSha256=IMPORTER.digest(updater))
    script = '\nconst configuration = '+json.dumps(config)+';\n'+updater.decode()+'\n'
    csp = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    return ('<!doctype html><meta http-equiv="Content-Security-Policy" content="script-src '
        "'sha256-"+csp+"'"+'"><script>'+script+'</script>').encode()


def recovery_metadata(data):
    return {'filename': HELPER, 'size': len(data), 'sha256': IMPORTER.digest(data)}


class MetadataContractTests(unittest.TestCase):
    def test_new_build_does_not_claim_owner_runtime_verification(self):
        build = dict(version=VERSION, manifestVersion=VERSION, artifact=PACKAGE,
            ciVerified=True, runtimeVerified=False)
        IMPORTER.validate_build(build, VERSION, PACKAGE)
        for override in ({'runtimeVerified': True}, {'ciVerified': False}, {'runtimeVerified': None}):
            with self.subTest(override=override), self.assertRaises(ValueError):
                IMPORTER.validate_build({**build, **override}, VERSION, PACKAGE)

    def test_legacy_build_contract_is_retained(self):
        legacy = dict(version='4.0.36', manifestVersion='4.0.36', artifact='old.zip', runtimeVerified=True)
        IMPORTER.validate_build(legacy, '4.0.36', 'old.zip')
        with self.assertRaises(ValueError):
            IMPORTER.validate_build({**legacy, 'runtimeVerified': False}, '4.0.36', 'old.zip')

    def test_legacy_updater_cannot_install_new_release(self):
        self.assertEqual(IMPORTER.minimum_updater({}, '4.0.36'), '1.0.0')
        self.assertEqual(IMPORTER.minimum_updater({'minUpdaterVersion':'2.0.0'}, VERSION), '2.0.0')
        for value in ({}, {'minUpdaterVersion':'1.0.0'}, {'minUpdaterVersion':True},
                {'minUpdaterVersion':'2.0.0\nunsafe'}, {'minUpdaterVersion':'2'}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                IMPORTER.minimum_updater(value, VERSION)

    def test_recovery_bytes_bind_to_same_version_identity_and_updater(self):
        data = recovery_bytes()
        manifest = {'key': KEY}
        payload = {'osminog-folder-updater.js': UPDATER}
        IMPORTER.validate_recovery_page(data, recovery_metadata(data), VERSION, manifest, payload)
        cases = [
            (recovery_bytes(version='4.0.36'), manifest, payload),
            (recovery_bytes(key='wrong-key'), manifest, payload),
            (recovery_bytes(updater=b'old updater'), manifest, payload),
            (data.replace(b'script-src', b'broken-src'), manifest, payload),
            (data+b'<script src="https://example.invalid/execute.js"></script>', manifest, payload),
        ]
        for candidate, expected_manifest, expected_payload in cases:
            with self.subTest(candidate=candidate[:50]), self.assertRaises(ValueError):
                IMPORTER.validate_recovery_page(candidate, recovery_metadata(candidate), VERSION,
                    expected_manifest, expected_payload)

    def test_recovery_rejects_mismatched_digest_and_unsafe_paths(self):
        data = recovery_bytes()
        expected = recovery_metadata(data)
        for change in ({'filename':'../'+HELPER}, {'filename':'OSMINOG-../bad.html'},
                {'filename':'OSMINOG-evil\\name.html'}, {'size':True}, {'size':IMPORTER.RECOVERY_LIMIT+1},
                {'sha256':'x'*64}, {'sha256':'0'*64}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                IMPORTER.validate_recovery_page(data, {**expected, **change}, VERSION,
                    {'key':KEY}, {'osminog-folder-updater.js':UPDATER})

    def test_outer_archive_must_contain_exactly_one_requested_helper(self):
        data = recovery_bytes()
        for entries in ([], [(HELPER,data), ('artifacts/'+HELPER,data)]):
            with self.subTest(entries=len(entries)), zipfile.ZipFile(io.BytesIO(archive_bytes(entries))) as archive:
                with self.assertRaises(ValueError):
                    IMPORTER.artifact_member(archive, HELPER, IMPORTER.RECOVERY_LIMIT)


class ImportBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.manifest = {'name':'OSMINOG', 'manifest_version':3, 'version':VERSION, 'key':KEY}
        self.build = dict(version=VERSION, manifestVersion=VERSION, artifact=PACKAGE,
            ciVerified=True, runtimeVerified=False)
        self.package = archive_bytes([
            ('manifest.json',json.dumps(self.manifest)),
            ('OSMINOG_BUILD.json',json.dumps(self.build)),
            ('osminog-folder-updater.js',UPDATER),
        ])
        self.helper = recovery_bytes()
        self.outer = archive_bytes([('artifacts/'+PACKAGE,self.package), ('artifacts/'+HELPER,self.helper)])
        self.request = dict(version=VERSION, sourceRepository=IMPORTER.SOURCE,
            sourceCommit=HEAD, sourceMergeCommit=MERGE, pullRequestNumber=99,
            sourceWorkflowRun=11, artifactId=31, package=PACKAGE, size=len(self.package),
            sha256=IMPORTER.digest(self.package), verificationRuns=[11,12,13], notes='Fixture release',
            minUpdaterVersion='2.0.0', recovery=recovery_metadata(self.helper))
        self.responses = {
            'actions/runs/11': dict(id=11,workflow_id=IMPORTER.CHROME_WORKFLOW,head_sha=HEAD,status='completed',conclusion='success'),
            'actions/runs/12': dict(id=12,workflow_id=351443074,head_sha=HEAD,status='completed',conclusion='success'),
            'actions/runs/13': dict(id=13,workflow_id=351468502,head_sha=HEAD,status='completed',conclusion='success'),
            'pulls/99': dict(merged=True,state='closed',base={'ref':'main'},head={'sha':HEAD},merge_commit_sha=MERGE),
            'compare/'+MERGE+'...main': dict(status='ahead',behind_by=0),
            'actions/artifacts/31': dict(expired=False,workflow_run={'id':11,'head_sha':HEAD},digest='sha256:'+IMPORTER.digest(self.outer)),
            'actions/artifacts/31/zip': self.outer,
        }
        feed = self.root/'channels/dev/chrome-extension.json'
        feed.parent.mkdir(parents=True)
        self.original_feed = json.dumps({'signed':{'latest':{'version':'4.0.36'}}}).encode()
        feed.write_bytes(self.original_feed)

    def run_import(self):
        request_path = self.root/f'staging/chrome-extension/{VERSION}/import-ci.json'
        request_path.parent.mkdir(parents=True,exist_ok=True)
        request_path.write_text(json.dumps(self.request))
        with mock.patch.object(IMPORTER,'ROOT',self.root), \
                mock.patch.object(IMPORTER,'IDENTITY',IMPORTER.digest(KEY.encode())), \
                mock.patch.object(IMPORTER,'api',side_effect=lambda path,binary=False:self.responses[path]), \
                contextlib.redirect_stdout(io.StringIO()):
            IMPORTER.main(VERSION)

    def test_exact_helper_is_archived_without_advancing_feed(self):
        self.run_import()
        directory = self.root/f'platforms/chrome-extension/releases/{VERSION}'
        self.assertEqual((directory/PACKAGE).read_bytes(),self.package)
        self.assertEqual((directory/HELPER).read_bytes(),self.helper)
        metadata = json.loads((directory/'release-v2.json').read_text())
        self.assertEqual(metadata['minUpdaterVersion'],'2.0.0')
        self.assertIs(metadata['ciVerified'],True)
        self.assertIs(metadata['runtimeVerified'],False)
        self.assertEqual(metadata['recovery'],self.request['recovery'])
        self.assertEqual((self.root/'channels/dev/chrome-extension.json').read_bytes(),self.original_feed)

    def test_three_source_gates_still_required(self):
        self.request['verificationRuns'] = [11,12]
        with self.assertRaisesRegex(ValueError,'Missing required verification'):
            self.run_import()

    def test_failed_or_different_head_gate_stops_import(self):
        for change in ({'conclusion':'failure'}, {'head_sha':'c'*40}):
            with self.subTest(change=change):
                self.responses['actions/runs/12'].update(change)
                with self.assertRaisesRegex(ValueError,'Source verification'):
                    self.run_import()
                self.responses['actions/runs/12'].update(conclusion='success',head_sha=HEAD)

    def test_unmerged_source_cannot_import_recovery(self):
        self.responses['pulls/99']['merged'] = False
        with self.assertRaisesRegex(ValueError,'not merged'):
            self.run_import()

    def test_artifact_from_another_head_cannot_import_recovery(self):
        self.responses['actions/artifacts/31']['workflow_run']['head_sha'] = 'c'*40
        with self.assertRaisesRegex(ValueError,'Wrong source artifact'):
            self.run_import()

    def test_helper_digest_mismatch_cannot_create_release_files(self):
        self.request['recovery']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError,'Recovery artifact byte size'):
            self.run_import()
        self.assertFalse((self.root/'platforms').exists())

    def test_existing_helper_bytes_cannot_be_overwritten(self):
        directory = self.root/f'platforms/chrome-extension/releases/{VERSION}'
        directory.mkdir(parents=True)
        (directory/HELPER).write_bytes(b'previous immutable bytes')
        with self.assertRaisesRegex(ValueError,'immutable recovery'):
            self.run_import()
        self.assertEqual((directory/HELPER).read_bytes(),b'previous immutable bytes')
        self.assertFalse((directory/PACKAGE).exists())


if __name__ == '__main__':
    unittest.main()
