#!/usr/bin/env python3
"""Synthetic fail-closed publisher contracts; never native release evidence."""
import ast
import copy
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'
PLAN = runpy.run_path(str(TOOLS / 'mouse641-publish-plan.py'))
EXTRA = runpy.run_path(str(TOOLS / 'mouse641-extra-evidence.py'))
REUSE = runpy.run_path(str(TOOLS / 'mouse641-reuse.py'))
with redirect_stdout(io.StringIO()):
    RELEASE = runpy.run_path(str(TOOLS / 'mouse641-release.py'))


def unready_pin_fixture(value):
    """Start synthetic scenarios independently of live staging activation."""
    value = copy.deepcopy(value)
    value['ready'] = False
    for key in PLAN['CLAIMS']:
        if key in value:
            value[key] = None
    for package in (value.get('packages') or {'installer': value['package']}).values():
        package.update(size=None, sha256=None)
    return value


class OrderedPublication(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder, *_ in PLAN['PLATFORMS'].values():
            stage = self.root / 'staging/mouse' / folder
            shutil.copytree(ROOT / 'staging/mouse' / folder, stage)
            pin = unready_pin_fixture(json.loads((stage / 'pin.json').read_text()))
            (stage / 'pin.json').write_text(json.dumps(pin))
            (stage / 'PUBLISH_OWNER').unlink(missing_ok=True)
        self.loaded, self.public = [], []

    def stage(self, platform):
        return self.root / 'staging/mouse' / PLAN['PLATFORMS'][platform][0]

    def ready(self, platform, **changes):
        stage = self.stage(platform)
        value = json.loads((stage / 'pin.json').read_text())
        value.update(ready=True, source='a' * 40, sourceMerge='b' * 40, sourcePR=203)
        value.update(changes)
        (stage / 'pin.json').write_text(json.dumps(value))
        (stage / 'PUBLISH_OWNER').write_text(PLAN['PLATFORMS'][platform][3] + '\n')

    def load(self, path):
        self.loaded.append(Path(path).name)
        return {'validate': lambda: None, 'pin': lambda: None}

    def check(self, platform, pin):
        self.public.append(platform)

    def run_plan(self, platform, check=None):
        return PLAN['publication_ready'](platform, root=self.root, load=self.load, check_public=check or self.check)

    def test_unready_pins_never_load_a_publisher_or_access_the_network(self):
        for platform in PLAN['PLATFORMS']:
            self.assertFalse(self.run_plan(platform))
        self.assertEqual(self.loaded + self.public, [])

    def test_mac_can_publish_before_later_candidates_are_ready(self):
        self.ready('macos-arm64')
        self.assertTrue(self.run_plan('macos-arm64'))
        self.assertEqual(self.loaded, ['mouse641-release.py'])
        self.assertEqual(self.public, [])

    def test_linux_requires_mac_pin_and_actual_public_proof(self):
        self.ready('linux-x64')
        self.assertFalse(self.run_plan('linux-x64'))
        self.ready('macos-arm64')
        def rejected(*_):
            raise ValueError('Mac public bytes are not accepted')
        with self.assertRaisesRegex(ValueError, 'public bytes'):
            self.run_plan('linux-x64', rejected)
        self.assertTrue(self.run_plan('linux-x64'))
        self.assertEqual(self.public, ['macos-arm64'])

    def test_windows_requires_mac_and_linux_in_that_order(self):
        self.ready('macos-arm64'); self.ready('windows-x64')
        self.assertFalse(self.run_plan('windows-x64'))
        self.ready('linux-x64')
        self.assertTrue(self.run_plan('windows-x64'))
        self.assertEqual(self.public, ['macos-arm64', 'linux-x64'])

    def test_mixed_source_merge_or_pr_is_rejected(self):
        self.ready('macos-arm64')
        for change in ({'source': 'c' * 40}, {'sourceMerge': 'c' * 40}, {'sourcePR': 202}):
            with self.subTest(change=change):
                self.ready('linux-x64', **change)
                with self.assertRaises(ValueError):
                    self.run_plan('linux-x64')

    def test_unready_provenance_and_owner_triggers_are_rejected(self):
        stage = self.stage('macos-arm64')
        original = (stage / 'pin.json').read_text()
        for key, value in [('source', 'a' * 40), ('sourceJob', 123), ('verificationSHA256', 'b' * 64)]:
            pin = json.loads(original); pin[key] = value
            (stage / 'pin.json').write_text(json.dumps(pin))
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.run_plan('macos-arm64')
        (stage / 'pin.json').write_text(original)
        (stage / 'PUBLISH_OWNER').write_text(PLAN['PLATFORMS']['macos-arm64'][3])
        with self.assertRaises(ValueError):
            self.run_plan('macos-arm64')


class ReadyPublisherContracts(unittest.TestCase):
    """Actual publisher functions over synthetic local pins; no CI or network."""
    def fixture(self, platform):
        folder, filename, _, owner = PLAN['PLATFORMS'][platform]
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        stage = Path(temporary.name) / folder
        shutil.copytree(ROOT / 'staging/mouse' / folder, stage)
        value = unready_pin_fixture(json.loads((stage / 'pin.json').read_text()))
        value.update(ready=True, source='a' * 40, sourceMerge='b' * 40, sourcePR=123,
                     run=456, attempt=1, job=789, artifact=790, artifactSHA256='c' * 64,
                     verificationArtifact=791, verificationSHA256='d' * 64)
        for package in (value.get('packages') or {'installer': value['package']}).values():
            package.update(size=60 * 1024**2, sha256='e' * 64)
        prefix = 'noble' if platform == 'linux-x64' else 'modern'
        value.update({prefix + 'Job': 792, prefix + 'Artifact': 793, prefix + 'SHA256': 'f' * 64})
        (stage / 'pin.json').write_text(json.dumps(value))
        (stage / 'PUBLISH_OWNER').write_text(owner + '\n')
        module = runpy.run_path(str(TOOLS / filename))
        scoped_stage = patch.dict(module['pin'].__globals__, {'STAGE': stage})
        scoped_stage.start()
        self.addCleanup(scoped_stage.stop)
        return module, value, stage, owner, prefix

    def test_actual_ready_template_and_pin_return_retained_validated_mapping(self):
        for platform in ('linux-x64', 'windows-x64'):
            with self.subTest(platform=platform):
                module, value, _, _, _ = self.fixture(platform)
                # This executes the inherited pin(), including its global
                # validate_template dispatch, rather than a mocked plan loader.
                self.assertEqual(module['pin'](), value)
                original = module['_original638_validate_template']
                returned = []
                def retain():
                    checked = original()
                    returned.append(checked)
                    return checked
                with patch.dict(module['validate_template'].__globals__, {'_original638_validate_template': retain}):
                    actual = module['validate_template']()
                self.assertEqual(actual, value)
                self.assertIs(actual, returned[0])

    def test_actual_ready_pin_keeps_base_and_additional_native_rejections(self):
        for platform in ('linux-x64', 'windows-x64'):
            module, original, stage, owner, prefix = self.fixture(platform)
            for defect in ('owner', 'source', 'merge', 'previous', 'currentPrevious',
                           'extra-job', 'extra-artifact', 'extra-sha', 'package-sha'):
                value = copy.deepcopy(original)
                if defect == 'source': value['source'] = 'invalid-source'
                if defect == 'merge': value['sourceMerge'] = 'invalid-merge'
                if defect in ('previous', 'currentPrevious'): value[defect]['version'] = '6.0.36'
                if defect == 'extra-job': value[prefix + 'Job'] = 0
                if defect == 'extra-artifact': value[prefix + 'Artifact'] = None
                if defect == 'extra-sha': value[prefix + 'SHA256'] = 'invalid-digest'
                if defect == 'package-sha':
                    next(iter((value.get('packages') or {'installer': value['package']}).values()))['sha256'] = 'invalid-digest'
                (stage / 'pin.json').write_text(json.dumps(value))
                (stage / 'PUBLISH_OWNER').write_text(('wrong owner' if defect == 'owner' else owner) + '\n')
                with self.subTest(platform=platform, defect=defect), self.assertRaises(ValueError):
                    module['pin']()

    def test_actual_unready_template_returns_mapping_without_enabling_publication(self):
        for platform in ('linux-x64', 'windows-x64'):
            with self.subTest(platform=platform):
                module, value, stage, _, _ = self.fixture(platform)
                value = unready_pin_fixture(value)
                (stage / 'pin.json').write_text(json.dumps(value))
                (stage / 'PUBLISH_OWNER').unlink()
                self.assertEqual(module['validate_template'](), value)
                with self.assertRaises(ValueError):
                    module['pin']()


class PublicBytes(unittest.TestCase):
    def fixture(self, platform):
        path, os_name, arch, tag = PLAN['CHANNELS'][platform]
        names = ['Mouse-Browser-6.0.41-mac-arm64.dmg', 'Mouse-Browser-6.0.41-mac-arm64.zip'] if os_name == 'darwin' else [
            'Mouse-Browser-6.0.41-Linux-x64.AppImage', 'Mouse-Browser-6.0.41-Linux-x64.deb']
        blobs = {name: ('synthetic unit package: ' + name).encode() for name in names}
        pin = {'packages': {n: {'size': len(b), 'sha256': hashlib.sha256(b).hexdigest()} for n, b in blobs.items()}}
        values = {n: {'url': 'https://github.com/jeep-jim/OSMINOG-Releases/releases/download/' + tag + '/' + n,
                      'size': p['size'], 'digest': 'sha256:' + p['sha256']} for n, p in pin['packages'].items()}
        feed = {'version': '6.0.41', 'platform': os_name, 'arch': arch, **values[names[0]]}
        if os_name == 'linux':
            feed['packages'] = dict(zip(('appimage', 'deb'), values.values()))
        release = {'id': 123, 'tag_name': tag, 'draft': False, 'published_at': '2026-11-23T00:00:00Z',
                   'assets': [{'name': n, 'browser_download_url': v['url'], 'size': v['size'], 'digest': v['digest']} for n, v in values.items()]}
        fetch = lambda url: feed if 'raw.githubusercontent' in url else release
        download = lambda url, **_: io.BytesIO(blobs[url.rsplit('/', 1)[1]])
        return pin, feed, release, blobs, fetch, download

    def test_prior_public_feed_release_and_all_package_bytes_are_bound(self):
        for platform in ('macos-arm64', 'linux-x64'):
            pin, _, _, blobs, fetch, download = self.fixture(platform)
            before = copy.deepcopy(blobs)
            with patch('urllib.request.urlopen', side_effect=download):
                result = PLAN['verify_previous_public'](platform, pin, fetch=fetch)
            self.assertTrue(result['anonymousDownloadsVerified'])
            self.assertEqual(blobs, before)

    def test_637_feed_wrong_asset_digest_or_changed_download_cannot_unlock_next_platform(self):
        for defect in ('old-version', 'wrong-release', 'wrong-digest', 'wrong-feed-url', 'changed-bytes'):
            pin, feed, release, blobs, fetch, download = self.fixture('macos-arm64')
            if defect == 'old-version': feed['version'] = '6.0.38'
            if defect == 'wrong-release': release['draft'] = True
            if defect == 'wrong-digest': release['assets'][0]['digest'] = 'sha256:' + '0' * 64
            if defect == 'wrong-feed-url': feed['url'] += '?other'
            if defect == 'changed-bytes':
                name = next(iter(blobs)); blobs[name] = b'X' * len(blobs[name])
            with self.subTest(defect=defect), patch('urllib.request.urlopen', side_effect=download), self.assertRaises(ValueError):
                PLAN['verify_previous_public']('macos-arm64', pin, fetch=fetch)


class ExtraProvenance(unittest.TestCase):
    def test_additional_native_jobs_need_pinned_ids_and_hashes(self):
        for platform, prefix, folder in [('linux', 'noble', 'linux-x64'), ('win32', 'modern', 'windows-x64')]:
            value = unready_pin_fixture(json.loads((ROOT / 'staging/mouse' / ('6.0.41-' + folder) / 'pin.json').read_text()))
            EXTRA['validate_pin'](value, platform)
            value['ready'] = True
            with self.assertRaises(ValueError): EXTRA['validate_pin'](value, platform)
            value.update({prefix + 'Job': 123, prefix + 'Artifact': 456, prefix + 'SHA256': 'c' * 64})
            EXTRA['validate_pin'](value, platform)
            value['currentPrevious']['version'] = '6.0.36'
            with self.assertRaises(ValueError): EXTRA['validate_pin'](value, platform)

    def test_wrong_source_attempt_job_or_skipped_step_is_rejected(self):
        pin = {'source': 'a' * 40, 'run': 123, 'attempt': 2, 'nobleJob': 456}
        row = {'id': 456, 'name': 'mouse-linux-install-noble', 'head_sha': pin['source'], 'run_id': 123,
               'run_attempt': 2, 'status': 'completed', 'conclusion': 'success',
               'steps': [{'name': 'native gate', 'status': 'completed', 'conclusion': 'success'}]}
        api = lambda *_: {'jobs': [row]}
        EXTRA['job'](api, pin, 'nobleJob', 'mouse-linux-install-noble', ['native gate'])
        for key, value in [('head_sha', 'b' * 40), ('run_attempt', 1), ('run_id', 122), ('conclusion', 'failure'), ('steps', [])]:
            with self.subTest(key=key):
                original = row[key]; row[key] = value
                with self.assertRaises(ValueError): EXTRA['job'](api, pin, 'nobleJob', 'mouse-linux-install-noble', ['native gate'])
                row[key] = original

    def test_archive_bytes_and_entry_names_are_preserved_and_wrong_sha_rejected(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('mouse-638-unit.txt', b'explicit synthetic archive fixture\n')
        raw = buffer.getvalue()
        pin = {'source': 'a' * 40, 'run': 123, 'nobleArtifact': 456, 'nobleSHA256': hashlib.sha256(raw).hexdigest()}
        record = {'id': 456, 'name': 'unit-evidence', 'expired': False, 'size_in_bytes': len(raw),
                  'workflow_run': {'id': 123, 'head_sha': pin['source']}}
        def download(command, *, stdout, **kwargs): stdout.write(raw)
        with tempfile.TemporaryDirectory() as temporary, patch('subprocess.run', side_effect=download):
            output = Path(temporary)
            arguments = {'id_key': 'nobleArtifact', 'hash_key': 'nobleSHA256', 'name': 'unit-evidence', 'output': output}
            with EXTRA['artifact'](lambda *_: record, pin, **arguments) as archive:
                self.assertEqual(archive.namelist(), ['mouse-638-unit.txt'])
                self.assertEqual(archive.read('mouse-638-unit.txt'), b'explicit synthetic archive fixture\n')
            self.assertEqual((output / 'unit-evidence.zip').read_bytes(), raw)
            pin['nobleSHA256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'ZIP hash'):
                with EXTRA['artifact'](lambda *_: record, pin, **arguments): pass

    def test_source_checker_and_crx_proof_must_match_independent_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            originals = {'mouse-638-acceptance.py': (TOOLS / 'mouse641-rendering-evidence.py').read_bytes().replace(
                            b'mouse641-task-evidence.py', b'mouse-631-acceptance.py'),
                         'mouse-638-crx-proof.cjs': (TOOLS / 'mouse-638-crx-proof.cjs').read_bytes(),
                         'mouse-639-acceptance.py': (TOOLS / 'mouse641-adblock-evidence.py').read_bytes().replace(
                             b'mouse641-task-evidence.py', b'mouse-631-acceptance.py'),
                         'mouse-640-settings-acceptance.py': (TOOLS / 'mouse641-settings-evidence.py').read_bytes().replace(
                             b'mouse641-task-evidence.py', b'mouse-631-acceptance.py'),
                         'mouse-641-workspace-acceptance.py': (TOOLS / 'mouse641-flexible-workspace-evidence.py').read_bytes().replace(
                             b'mouse641-task-evidence.py', b'mouse-631-acceptance.py')}
            for name, raw in originals.items(): (output / name).write_bytes(raw)
            EXTRA['verify_helper_bytes'](output)
            for name, raw in originals.items():
                (output / name).write_bytes(raw + b'\n# changed\n')
                with self.subTest(name=name), self.assertRaises(ValueError): EXTRA['verify_helper_bytes'](output)
                (output / name).write_bytes(raw)
            self.assertEqual({n: (output / n).read_bytes() for n in originals}, originals)


class Ubuntu24Acceptance(unittest.TestCase):
    def fixture(self):
        pixels = runpy.run_path(str(TOOLS / 'test_mouse641_rendering.py'))
        png = pixels['png'](40, 30, pixels['canvas'](40, 30))
        name = 'Mouse-Browser-6.0.41-Linux-x64.deb'
        pin = {'source': 'a' * 40, 'run': 123, 'attempt': 2,
               'packages': {name: {'size': 123456, 'sha256': 'b' * 64}}}
        files, reports = {}, {}
        def receipt(log, markers, pid):
            files[log] = ('Synthetic unit log; no native process ran\n' + '\n'.join(markers) + '\n').encode()
            return {'log': log, 'exitCode': 0, 'pid': pid, 'elapsedMs': 1000, 'logSha256': EXTRA['sha'](files[log]), 'requiredMarkers': markers}
        facts = {'ok': True, 'source': pin['source'], 'version': '6.0.41', 'platform': 'linux', 'arch': 'x64',
                 'runId': '123', 'runAttempt': '2', 'package': {'name': name, **pin['packages'][name]},
                 'osRelease': 'ID=ubuntu\nVERSION_ID="24.04"\n', 'ownerDeviceVerified': False,
                 'policyBefore': {'apparmor_restrict_unprivileged_userns': '1'},
                 'policyAfter': {'apparmor_restrict_unprivileged_userns': '1'},
                 'containerImage': ['ubuntu@sha256:' + 'c' * 64],
                 'apparmorProfile': {'path': '/etc/apparmor.d/mouse-browser', 'sha256': 'd' * 64},
                 'cleanDependencies': receipt('mouse-linux-clean-dependencies.log', ['MOUSE_LINUX_CLEAN_DEB_DEPENDENCIES_PASS'], 99),
                 'nativeProcesses': {}}
        executable = '/opt/Mouse Browser/mouse-browser'
        facts['installation'] = {**receipt('mouse-linux-noble-install.log', [], 100), 'packageName': 'mouse-browser',
            'version': '6.0.41', 'executable': executable, 'desktopFile': '/usr/share/applications/mouse-browser.desktop',
            'desktopSha256': '1' * 64, 'executableSha256': '2' * 64}
        for phase, pid, marker in [('write', 101, 'MOUSE_LINUX_PROFILE_WRITE_PASS'), ('read', 102, 'MOUSE_LINUX_PROFILE_RESTART_PASS')]:
            facts['nativeProcesses'][phase] = receipt('mouse-linux-noble-' + phase + '.log', [marker, 'MOUSE_LINUX_X64_SMOKE_PASS'], pid)
            report = {'ok': True, 'version': '6.0.41', 'platform': 'linux', 'arch': 'x64', 'pid': pid,
                      'packageFormat': 'deb', 'executable': executable, 'physicalUserDeviceVerified': False,
                      'asarSha256': 'e' * 64, 'captures': [], 'sandbox': {'disabledFlags': [], 'renderers': [
                          {'seccomp': 2, 'noNewPrivs': 1, 'uid': 1001, 'preferences': {
                              'sandbox': True, 'contextIsolation': True, 'nodeIntegration': False, 'webSecurity': True}}
                          for _ in range(2)]}}
            for theme in ('dark', 'light'):
                filename = 'mouse-linux-' + phase + '-' + theme + '.png'; files[filename] = png
                report['captures'].append({'theme': theme, 'filename': filename, 'sha256': EXTRA['sha'](png),
                    'source': 'globalCapture.acquire(display)', 'backend': 'desktopCapturer', 'screenPixelSize': {'width': 40, 'height': 30}})
            report['profile'] = {'written': True, 'tokenSha256': 'f' * 64, 'pageId': 'unit-page'} if phase == 'write' else {
                'differentProcess': True, 'preferencesPreserved': True, 'cookiePreserved': True, 'localStoragePreserved': True,
                'bookmarkPreserved': True, 'previousPid': 101, 'currentPid': 102, 'tokenSha256': 'f' * 64, 'pageId': 'unit-page'}
            reports[phase] = report
        native = runpy.run_path(str(TOOLS / 'test_mouse641_adblock.py'))
        ad_files, _, ad_refresh = native['fixture']()
        ad_refresh.processes.update(executable=executable, executableSha256='2' * 64)
        ad_refresh()
        accepted = native['A'].verify(ad_files.__getitem__, expected_platform='linux', expected_arch='x64')
        acceptance = (json.dumps(accepted, indent=2) + '\n').encode()
        ad_files['mouse-639-acceptance.json'] = acceptance
        files.update(ad_files)
        facts['adblock639'] = {**ad_refresh.processes, 'acceptanceSha256': EXTRA['sha'](acceptance)}
        def refresh():
            for phase, report in reports.items():
                filename = 'mouse-linux-smoke-' + phase + '.json'; files[filename] = json.dumps(report).encode()
                facts['nativeProcesses'][phase].update(report=filename, reportSha256=EXTRA['sha'](files[filename]))
            files['mouse-linux-install-noble.json'] = json.dumps(facts).encode()
        refresh()
        return pin, facts, reports, files, refresh

    def test_additional_install_evidence_is_bound_without_rewriting_bytes(self):
        pin, facts, reports, files, refresh = self.fixture()
        before = copy.deepcopy(files)
        result = EXTRA['noble'](files.__getitem__, pin, expected_asar='e' * 64)
        self.assertTrue(result['ok']); self.assertFalse(result['ownerDeviceVerified'])
        self.assertTrue(result['adblock639']['ok'])
        self.assertEqual(files, before)

    def test_noble_requires_adblock_from_the_exact_installed_executable(self):
        pin, facts, _, files, refresh = self.fixture()
        facts.pop('adblock639'); refresh()
        with self.assertRaisesRegex(ValueError, 'AdBlock639'):
            EXTRA['noble'](files.__getitem__, pin, expected_asar='e' * 64)
        for field, value in (('executable', '/foreign/mouse-browser'), ('executableSha256', '0' * 64)):
            pin, facts, _, files, refresh = self.fixture()
            name = 'mouse-639-adblock-processes.json'
            processes = json.loads(files[name]); processes[field] = value
            files[name] = json.dumps(processes).encode()
            reader = runpy.run_path(str(TOOLS / 'mouse641-adblock-evidence.py'))
            accepted = reader['verify'](files.__getitem__, expected_platform='linux', expected_arch='x64')
            files['mouse-639-acceptance.json'] = json.dumps(accepted).encode()
            facts['adblock639'] = {**processes, 'acceptanceSha256': EXTRA['sha'](files['mouse-639-acceptance.json'])}
            refresh()
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'different installed executable'):
                EXTRA['noble'](files.__getitem__, pin, expected_asar='e' * 64)

    def test_wrong_source_package_platform_policy_and_report_version_fail(self):
        mutations = [lambda f, r: f.update(source='0' * 40), lambda f, r: f.update(runAttempt='1'),
            lambda f, r: f['package'].update(sha256='0' * 64), lambda f, r: f.update(osRelease='ID=ubuntu\nVERSION_ID="22.04"\n'),
            lambda f, r: f['policyAfter'].update(apparmor_restrict_unprivileged_userns='0'),
            lambda f, r: r['read'].update(version='6.0.38'), lambda f, r: r['write'].update(executable='/tmp/other/mouse-browser')]
        for index, mutation in enumerate(mutations):
            pin, facts, reports, files, refresh = self.fixture(); mutation(facts, reports); refresh()
            with self.subTest(index=index), self.assertRaises(ValueError): EXTRA['noble'](files.__getitem__, pin, expected_asar='e' * 64)

    def test_sandbox_profile_pid_screen_and_asar_forgery_fail_even_after_rehash(self):
        mutations = [lambda f, r: r['write']['sandbox'].update(disabledFlags=['no-sandbox']),
            lambda f, r: r['read']['sandbox']['renderers'][0].update(seccomp=0),
            lambda f, r: r['read']['profile'].update(cookiePreserved=False),
            lambda f, r: r['read']['profile'].update(tokenSha256='0' * 64),
            lambda f, r: r['read'].update(pid=101), lambda f, r: r['read'].update(asarSha256='0' * 64),
            lambda f, r: r['write']['captures'][0].update(screenPixelSize={'width': 1, 'height': 1})]
        for index, mutation in enumerate(mutations):
            pin, facts, reports, files, refresh = self.fixture(); mutation(facts, reports); refresh()
            with self.subTest(index=index), self.assertRaises(ValueError): EXTRA['noble'](files.__getitem__, pin, expected_asar='e' * 64)


class RetainedIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        retained = runpy.run_path(str(TOOLS / 'test_mouse641_retained.py'))
        suite = retained['load_tests'](unittest.defaultTestLoader, unittest.TestSuite(), None)
        def flatten(value):
            for test in value:
                if isinstance(test, unittest.TestSuite): yield from flatten(test)
                else: yield test
        test = next(t for t in flatten(suite) if type(t).__name__ == 'CurrentAcceptance')
        cls.fixture_scope = test.test_actual_button_all_three_platforms_requires_four_processes.__globals__

    def test_retained_current_upgrade_accepts638_without_rewriting_archived_evidence(self):
        for platform in ('darwin', 'linux', 'win32'):
            value, facts, reports, files, refresh = self.fixture_scope['fixture'](platform)
            before = copy.deepcopy(files)
            args = {'expected_platform': platform, 'expected_arch': 'arm64' if platform == 'darwin' else 'x64',
                    'expected_packages' if platform == 'linux' else 'expected_package': value}
            self.assertTrue(self.fixture_scope['E']['verify'](files.__getitem__, **args)['ok'])
            self.assertEqual(files, before)
            facts['toVersion'] = '6.0.38'; refresh()
            with self.assertRaises(ValueError): self.fixture_scope['E']['verify'](files.__getitem__, **args)

    def test_all_frozen_dependencies_still_match_archived_hashes(self):
        for name, digest in REUSE['FROZEN'].items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256(REUSE['checked'](name)).hexdigest(), digest)
        with patch.dict(REUSE['checked'].__globals__['FROZEN'], {'mouse639-current.py': '0' * 64}):
            with self.assertRaisesRegex(ValueError, 'dependency changed'): REUSE['checked']('mouse639-current.py')

    def test_actual_source_feature_declaration_and_each_retained_requirement(self):
        fixture = json.loads((TOOLS / 'fixtures/mouse641-macos-build-feature-tokens.json').read_text())
        self.assertTrue(fixture['notNativeEvidence'])
        self.assertEqual(fixture['version'], '6.0.41')
        tree = REUSE['adapted_tree']('mouse632-release.py')
        importer = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'import_candidate')
        guards = [n for n in importer.body if isinstance(n, ast.If) and any(
            isinstance(part, ast.Name) and part.id == 'FEATURE_TOKENS_632' for part in ast.walk(n.test))]
        self.assertEqual(len(guards), 1)
        def check(tokens):
            scope = RELEASE.copy(); scope['b'] = {'tests': tokens}
            exec(compile(ast.Module(body=guards, type_ignores=[]), '<actual-manifest-guard>', 'exec'), scope)
        check(fixture['tests'])
        self.assertIn('real-640-to-641-profile-preserving-replacement', RELEASE['FEATURE_TOKENS_632'])
        for token in RELEASE['FEATURE_TOKENS_632']:
            with self.subTest(token=token), self.assertRaises(ValueError): check([t for t in fixture['tests'] if t != token])


if __name__ == '__main__':
    unittest.main()
