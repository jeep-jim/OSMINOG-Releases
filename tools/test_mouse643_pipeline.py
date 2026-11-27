#!/usr/bin/env python3
"""Synthetic publisher rejection tests; these do not claim native acceptance."""
import ast
import copy
from contextlib import contextmanager, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'
STAGE = ROOT / 'staging/mouse/6.0.43-arm64'
PLAN = runpy.run_path(str(TOOLS / 'mouse643-publish-plan.py'))
REUSE = runpy.run_path(str(TOOLS / 'mouse643-reuse.py'))
EXTRA = runpy.run_path(str(TOOLS / 'mouse643-extra-evidence.py'))
with redirect_stdout(io.StringIO()):
    RELEASE = runpy.run_path(str(TOOLS / 'mouse643-release.py'))


def unready():
    value = json.loads((STAGE / 'pin.json').read_text())
    value['ready'] = False
    for key in PLAN['CLAIMS']:
        value[key] = None
    for package in value['packages'].values():
        package.update(size=None, sha256=None)
    return value


class FrozenPredecessor(unittest.TestCase):
    def test_accepted642_bytes_and_inherited_lineage_are_immutable(self):
        REUSE['verify_frozen']()
        scope = REUSE['checked'].__globals__
        with patch.dict(scope, {'FROZEN': {**REUSE['FROZEN'], 'mouse642-reuse.py': '0' * 64}}):
            with self.assertRaisesRegex(ValueError, 'Immutable642'):
                REUSE['checked']('mouse642-reuse.py')
        with self.assertRaisesRegex(ValueError, 'Unreviewed643'):
            REUSE['checked']('unreviewed.py')

    def test_predecessor_is_actual_published642_mac_bytes_only(self):
        previous = REUSE['previous']('darwin')
        self.assertEqual(previous['version'], '6.0.42')
        self.assertEqual(previous['source'], 'ac51d80d4190bce54d8cc5f7017359dcb8fa838c')
        self.assertEqual(previous['updaterBlobSHA'], '91ab363f926774825caf8055b2d3d81bf0d51264')
        self.assertEqual(previous['packages'], json.loads((ROOT / 'staging/mouse/6.0.42-arm64/pin.json').read_text())['packages'])
        self.assertEqual(REUSE['baselines'](), {'darwin': {'name': 'Mouse-Browser-6.0.42-mac-arm64.dmg',
            'tag': 'quadro-macos-v6.0.42-arm64', 'size': 131605262,
            'sha256': 'b3d7d3a29ea2faea1b5d34974cac841e74607a1e02d32c03dafac123db1a0b69'}})
        for platform in ('linux', 'win32', 'darwin-x64'):
            with self.subTest(platform=platform), self.assertRaises(ValueError):
                REUSE['previous'](platform)

    def test_current_identity_retains_truthful_upgrade_and_active_box_gates(self):
        current = runpy.run_path(str(TOOLS / 'mouse643-current.py'))
        update = runpy.run_path(str(TOOLS / 'mouse643-update-button-evidence.py'))
        self.assertEqual((RELEASE['V'], update['VERSION'], update['PREVIOUS']), ('6.0.43', '6.0.43', '6.0.42'))
        self.assertEqual(current['PUBLISHED_SOURCE'], REUSE['PUBLISHED_SOURCE'])
        self.assertTrue({'mouse-643-polish-run.py', 'mouse-643-polish-acceptance.py'} <= set(current['HELPERS']))
        declared = set(json.loads((TOOLS / 'fixtures/mouse643-macos-build-feature-tokens.json').read_text())['tests'])
        self.assertTrue(RELEASE['FEATURE_TOKENS_632'] <= declared)
        self.assertTrue(set(EXTRA['POLISH_TOKENS']) <= declared)
        self.assertIn('active-tab-box-both-themes', declared)
        self.assertNotIn('active-tab-flow-borderless-both-themes', declared)
        for old in ('mouse632-release.py', 'mouse637-current.py', 'mouse637-upgrade-evidence.py', 'mouse637-update-button-evidence.py'):
            constants = [n.value for n in ast.walk(REUSE['adapted_tree'](old)) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
            self.assertFalse(any('real-641-to-642-' in s or 'MOUSE_642_REAL_' in s for s in constants), old)
        constants = [n.value for n in ast.walk(REUSE['adapted_tree']('mouse632-release.py')) if isinstance(n, ast.Constant)]
        self.assertIn('MOUSE_643_ACTIVE_TAB_BOX_BOTH_THEMES_PASS', constants)
        self.assertNotIn('MOUSE_628_ACTIVE_TAB_FLOW_BORDERLESS_BOTH_THEMES_PASS', constants)
        baseline_constants = [n.value for n in ast.walk(REUSE['adapted_tree']('mouse637-performance-evidence.py')) if isinstance(n, ast.Constant)]
        self.assertIn('mouse642-task-evidence.py', baseline_constants)

    def test_schema_upgrade_markers_equal_the_executed_current_readers(self):
        schema = json.loads((STAGE / 'evidence.schema.json').read_text())
        expected = [runpy.run_path(str(TOOLS / name))['MARKER'] for name in
                    ('mouse643-upgrade-evidence.py', 'mouse643-update-button-evidence.py')]
        self.assertEqual(expected, ['MOUSE_643_REAL_642_TO_643_PROFILE_PASS',
                                    'MOUSE_643_REAL_642_TO_643_UPDATE_BUTTON_PASS'])
        self.assertEqual([marker for marker in schema['x-nativeMarkers'] if '_REAL_' in marker], expected)

    def test_actual_import_guard_requires_box_token_and_all_current_features(self):
        declared = json.loads((TOOLS / 'fixtures/mouse643-macos-build-feature-tokens.json').read_text())['tests']
        tree = REUSE['adapted_tree']('mouse632-release.py')
        importer = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'import_candidate')
        required = next(n for n in importer.body if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == 'required' for t in n.targets))
        def feature_fields(condition):
            return {part.slice.value for part in ast.walk(condition) if isinstance(part, ast.Subscript)
                    and isinstance(part.value, ast.Name) and part.value.id == 'b' and isinstance(part.slice, ast.Constant)}
        guards = [n for n in importer.body if isinstance(n, ast.If) and feature_fields(n.test) == {'tests'}]
        self.assertGreater(len(guards), 5)
        code = compile(ast.Module(body=[required, *guards], type_ignores=[]), '<actual-source-feature-guards>', 'exec')
        def check(tokens):
            scope = RELEASE.copy(); scope['b'] = {'tests': tokens}; exec(code, scope)
        check(declared)
        required_tokens = RELEASE['FEATURE_TOKENS_632'] | {'active-tab-box-both-themes'}
        for token in required_tokens:
            with self.subTest(token=token), self.assertRaises(ValueError): check([t for t in declared if t != token])


class MacOnlyPlan(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.stage = self.root / 'staging/mouse/6.0.43-arm64'
        self.stage.mkdir(parents=True)
        self.original = unready()
        self.save(self.original)
        self.calls = []

    def save(self, value):
        (self.stage / 'pin.json').write_text(json.dumps(value))

    def load(self, path):
        self.calls.append(Path(path).name)
        return {'validate': lambda: self.calls.append('validate')}

    def check(self, platform='macos-arm64'):
        return PLAN['publication_ready'](platform, root=self.root, load=self.load)

    def test_unready_template_cannot_load_publisher_or_trigger_network(self):
        self.assertFalse(self.check())
        self.assertEqual(self.calls, [])

    def test_only_authorized_mac_platform_and_stage_are_admitted(self):
        for platform in ('linux-x64', 'windows-x64', 'macos-x64', 'darwin'):
            with self.subTest(platform=platform), self.assertRaises(ValueError): self.check(platform)
        for folder in ('6.0.43-linux-x64', '6.0.43-windows-x64'):
            forbidden = self.root / 'staging/mouse' / folder; forbidden.mkdir()
            with self.assertRaisesRegex(ValueError, 'not authorized'): self.check()
            forbidden.rmdir()

    def test_unready_pin_cannot_claim_provenance_bytes_or_owner(self):
        for key in PLAN['CLAIMS']:
            value = copy.deepcopy(self.original); value[key] = 123
            self.save(value)
            with self.subTest(key=key), self.assertRaises(ValueError): self.check()
        value = copy.deepcopy(self.original)
        next(iter(value['packages'].values()))['sha256'] = 'a' * 64; self.save(value)
        with self.assertRaisesRegex(ValueError, 'package bytes'): self.check()
        self.save(self.original)
        (self.stage / 'PUBLISH_OWNER').write_text(PLAN['PLATFORMS']['macos-arm64'][3])
        with self.assertRaises(ValueError): self.check()
        self.assertEqual(self.calls, [])

    def test_ready_plan_requires_exact_regular_owner_then_actual_validator(self):
        self.save({**self.original, 'ready': True})
        owner = self.stage / 'PUBLISH_OWNER'
        for text in (None, 'Mouse Browser 6.0.42: publish pinned source and verified Mac packages'):
            if text is not None: owner.write_text(text)
            with self.assertRaisesRegex(ValueError, 'owner'): self.check()
        owner.write_text(PLAN['PLATFORMS']['macos-arm64'][3] + '\n')
        self.assertTrue(self.check())
        self.assertEqual(self.calls, ['mouse643-release.py', 'validate'])
        target = self.stage / 'owner-copy'; owner.rename(target); owner.symlink_to(target.name)
        with self.assertRaisesRegex(ValueError, 'owner'): self.check()

    def test_ready_plan_propagates_validator_rejection(self):
        self.save({**self.original, 'ready': True})
        (self.stage / 'PUBLISH_OWNER').write_text(PLAN['PLATFORMS']['macos-arm64'][3])
        def load(_):
            def reject(): raise ValueError('native provenance incomplete')
            return {'validate': reject}
        with self.assertRaisesRegex(ValueError, 'native provenance incomplete'):
            PLAN['publication_ready']('macos-arm64', root=self.root, load=load)


class ExactCandidateBindings(unittest.TestCase):
    def test_actual_ready_validator_keeps_all_immutable_pin_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory); shutil.copytree(STAGE, stage, dirs_exist_ok=True)
            (stage / 'PUBLISH_OWNER').write_text(PLAN['PLATFORMS']['macos-arm64'][3])
            value = unready()
            value.update(ready=True, source='a' * 40, sourceMerge='b' * 40, sourcePR=123,
                         run=456, artifact=789, verificationArtifact=790, sourceAttempt=2, sourceJob=791,
                         archiveSHA256='c' * 64, verificationSHA256='d' * 64)
            for package in value['packages'].values(): package.update(size=130 * 1024**2, sha256='e' * 64)
            scope = RELEASE['validate'].__globals__
            with patch.dict(scope, {'PIN': value, 'STAGE': stage}), redirect_stdout(io.StringIO()):
                RELEASE['validate']()
            mutations = [lambda v: v.update(source='invalid'), lambda v: v.update(sourceMerge=None),
                         lambda v: v.update(sourceAttempt=0), lambda v: v.update(sourceJob=False),
                         lambda v: v.update(verificationSHA256='a'),
                         lambda v: v['previous'].update(version='6.0.30'),
                         lambda v: v['currentPrevious'].update(source='c' * 40),
                         lambda v: next(iter(v['packages'].values())).update(sha256='invalid')]
            for mutate in mutations:
                changed = copy.deepcopy(value); mutate(changed)
                with patch.dict(scope, {'PIN': changed, 'STAGE': stage}), redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
                    RELEASE['validate']()

    def test_source_manifest_binds_exact_head_run_attempt_platform_and_arch(self):
        pin = {'source': 'a' * 40, 'run': 123, 'sourceAttempt': 2}
        build = {'version': '6.0.43', 'source': pin['source'], 'runId': '123', 'runAttempt': '2', 'platform': 'darwin', 'arch': 'arm64'}
        EXTRA['source_manifest'](build, pin)
        for key, replacement in [('source', 'b' * 40), ('version', '6.0.42'), ('runId', '124'), ('runAttempt', '1'),
                                 ('runAttempt', None), ('runAttempt', True), ('runAttempt', 2.0),
                                 ('platform', 'linux'), ('arch', 'x64')]:
            with self.subTest(key=key, replacement=replacement), self.assertRaises(ValueError):
                EXTRA['source_manifest']({**build, key: replacement}, pin)

    def test_fetched_source_readers_must_match_every_independent_reader_byte(self):
        pairs = {'mouse-638-acceptance.py': 'mouse643-rendering-evidence.py',
                 'mouse-639-acceptance.py': 'mouse643-adblock-evidence.py',
                 'mouse-640-settings-acceptance.py': 'mouse643-settings-evidence.py',
                 'mouse-641-workspace-acceptance.py': 'mouse643-flexible-workspace-evidence.py',
                 'mouse-642-controls-acceptance.py': 'mouse643-controls-evidence.py',
                 'mouse-643-polish-acceptance.py': 'mouse643-polish-evidence.py'}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for source, reader in pairs.items():
                (output / source).write_bytes((TOOLS / reader).read_bytes().replace(b'mouse643-task-evidence.py', b'mouse-631-acceptance.py'))
            shutil.copyfile(TOOLS / 'mouse-638-crx-proof.cjs', output / 'mouse-638-crx-proof.cjs')
            EXTRA['verify_helper_bytes'](output)
            for name in (*pairs, 'mouse-638-crx-proof.cjs'):
                path = output / name; original = path.read_bytes(); path.write_bytes(original + b'\n# changed checker\n')
                with self.subTest(name=name), self.assertRaises(ValueError): EXTRA['verify_helper_bytes'](output)
                path.write_bytes(original)

    def test_only_mac_publication_workflow_and_packages_are_created(self):
        workflow = (ROOT / '.github/workflows/publish-mouse643.yml').read_text()
        self.assertIn('runs-on: macos-15', workflow)
        self.assertIn("needs.contract.outputs.publish == 'true'", workflow)
        self.assertIn('python3 tools/mouse643-publish-plan.py macos-arm64', workflow)
        self.assertIn('MOUSE_643_POLISH_NATIVE_PASS', workflow)
        self.assertIn('MOUSE_643_REAL_642_TO_643_PROFILE_PASS', workflow)
        self.assertNotIn('MOUSE_628_ACTIVE_TAB_FLOW_BORDERLESS_BOTH_THEMES_PASS', workflow)
        self.assertEqual({p.name for p in (ROOT / '.github/workflows').glob('publish-mouse643*')}, {'publish-mouse643.yml'})
        self.assertEqual({p.name for p in (ROOT / 'staging/mouse').glob('6.0.43-*')}, {'6.0.43-arm64'})
        for platform in ('linux', 'windows'):
            self.assertFalse((TOOLS / ('mouse643-' + platform + '-release.py')).exists())


def polish_fixture():
    encode = lambda value: (json.dumps(value, indent=2) + '\n').encode()
    accepted = {'syntheticUnitBindingFixture': True, 'version': '6.0.43', 'ok': True}
    files = {'mouse-643-polish-acceptance.json': encode(accepted),
             'mouse-643-polish.json': encode({'syntheticUnitBindingFixture': True}),
             'mouse-643-polish-processes.json': encode({'syntheticUnitBindingFixture': True, 'write': {'pid': 101}, 'read': {'pid': 102}})}
    reference = lambda name: {'file': name, 'sha256': hashlib.sha256(files[name]).hexdigest()}
    build = {'tests': list(EXTRA['POLISH_TOKENS']), 'polish643': {**reference('mouse-643-polish-acceptance.json'),
             'report': reference('mouse-643-polish.json'), 'processes': reference('mouse-643-polish-processes.json')}}
    return files, accepted, build


class PolishPublicationBinding(unittest.TestCase):
    def check(self, files, accepted, **kwargs):
        calls = []
        def load(path):
            self.assertEqual(Path(path), TOOLS / 'mouse643-polish-evidence.py')
            def verify(read, *, expected_platform, expected_arch):
                calls.append((expected_platform, expected_arch, read('mouse-643-polish.json')))
                return copy.deepcopy(accepted)
            return {'verify': verify}
        with patch.object(EXTRA['runpy'], 'run_path', side_effect=load):
            result = EXTRA['polish'](files.__getitem__, platform='darwin', arch='arm64', **kwargs)
        self.assertEqual(calls, [('darwin', 'arm64', files['mouse-643-polish.json'])])
        return result

    def test_source_and_fresh_read_actual_evidence_and_match_saved_acceptance(self):
        files, accepted, build = polish_fixture()
        self.assertEqual(self.check(files, accepted, build=build), accepted)
        self.assertEqual(self.check(files, accepted), accepted)
        files['mouse-643-polish-acceptance.json'] = json.dumps({**accepted, 'invented': True}).encode()
        with self.assertRaisesRegex(ValueError, 'acceptance differs'): self.check(files, accepted, build=build)

    def test_missing_feature_or_manifest_hash_cannot_publish(self):
        for token in EXTRA['POLISH_TOKENS']:
            files, accepted, build = polish_fixture(); build['tests'].remove(token)
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, 'feature gates'): self.check(files, accepted, build=build)
        for key in ('sha256', 'report', 'processes'):
            files, accepted, build = polish_fixture()
            if key == 'sha256': build['polish643'][key] = '0' * 64
            else: build['polish643'][key]['sha256'] = '0' * 64
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'actual643'): self.check(files, accepted, build=build)
        files, accepted, build = polish_fixture(); del files['mouse-643-polish-processes.json']
        with self.assertRaises(KeyError): self.check(files, accepted, build=build)

    def test_non_mac_evidence_is_rejected_before_reader_loading(self):
        with patch.object(EXTRA['runpy'], 'run_path', side_effect=AssertionError('must not load')):
            for platform, arch in (('linux', 'x64'), ('win32', 'x64'), ('darwin', 'x64')):
                with self.subTest(platform=platform), self.assertRaisesRegex(ValueError, 'only macOS arm64'):
                    EXTRA['polish'](lambda _: b'', platform=platform, arch=arch)

    def test_schema_pins_reader_dependency_bytes_and_every_native_behavior(self):
        EXTRA['validate_polish_contract'](STAGE)
        original = json.loads((STAGE / 'evidence.schema.json').read_text())
        changes = [lambda v: v.update(sha256='0' * 64), lambda v: v['dependencies'].update({'mouse643-current.py': '0' * 64}),
                   lambda v: v['required'].remove('mouse-643-polish-read.log'), lambda v: v['featureTokens'].pop(),
                   lambda v: v.update(savedReportAcceptedAsInput=True), lambda v: v.update(runtimeVersion='6.0.42'),
                   lambda v: v.update(platform='linux'), lambda v: v.update(arch='x64')]
        flags = ('sourceAndFreshInstalled', 'nativeDisplayPixels', 'realNativeClickAndDrag', 'rootThemeSurfaceActiveTab',
                 'fixedSquareSeparators', 'realSearchAndAddressActions', 'pageThemeAndRestart', 'sourceManifestAttemptBound')
        changes += [lambda v, flag=flag: v.update({flag: False}) for flag in flags]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for change in changes:
                value = copy.deepcopy(original); change(value['x-current643PolishGate'])
                (target / 'evidence.schema.json').write_text(json.dumps(value))
                with self.assertRaises(ValueError): EXTRA['validate_polish_contract'](target)

    def test_source_import_runs_new_gate_and_preserves_failure(self):
        files, accepted, binding = polish_fixture()
        pin = {'source': 'a' * 40, 'run': 123, 'sourceAttempt': 2}
        build = {**binding, 'source': pin['source'], 'runId': '123', 'runAttempt': '2', 'version': '6.0.43', 'platform': 'darwin', 'arch': 'arm64'}
        @contextmanager
        def artifact(*_args, **_kwargs):
            class Archive:
                read = staticmethod(files.__getitem__)
            yield Archive()
        calls = []
        def polish(read, **kwargs):
            calls.append(kwargs)
            self.assertEqual(read('mouse-643-polish.json'), files['mouse-643-polish.json'])
            return accepted
        retained = {name: lambda *_a, **_k: {'syntheticUnitBindingFixture': True} for name in ('feedback', 'adblock', 'settings', 'workspace', 'controls')}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory); (output / 'mouse-build.json').write_text(json.dumps(build))
            module = {'OUT': output, 'PIN': pin, 'api': lambda *_a: (_ for _ in ()).throw(AssertionError('no network'))}
            mocks = {**retained, 'artifact': artifact, 'validate_pin': lambda *_a: None, 'verify_helper_bytes': lambda *_a: None, 'polish': polish}
            with patch.dict(EXTRA['import_extra'].__globals__, mocks), redirect_stdout(io.StringIO()):
                EXTRA['import_extra'](module, 'darwin')
            self.assertEqual(calls, [{'platform': 'darwin', 'arch': 'arm64', 'build': build}])
            self.assertEqual(json.loads((output / 'source643-polish-independent.json').read_text()), accepted)
            def rejected(*_args, **_kwargs): raise ValueError('polish rejected')
            with patch.dict(EXTRA['import_extra'].__globals__, {**mocks, 'polish': rejected}), self.assertRaisesRegex(ValueError, 'polish rejected'):
                EXTRA['import_extra'](module, 'darwin')

    def test_fresh_gate_runs_before_assets_and_its_failure_prevents_upload(self):
        calls = []
        def polish(_read, **kwargs):
            calls.append(kwargs); return {'syntheticUnitBindingFixture': True, 'ok': True}
        retained = {name: lambda *_a, **_k: {'syntheticUnitBindingFixture': True} for name in ('feedback', 'adblock', 'settings', 'workspace', 'controls')}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.dict(EXTRA['fresh'].__globals__, {**retained, 'verify_helper_bytes': lambda *_a: None, 'polish': polish}):
                EXTRA['fresh']({'OUT': output}, 'darwin')
            self.assertEqual(calls, [{'platform': 'darwin', 'arch': 'arm64'}])
            self.assertTrue((output / 'installed643-polish-independent.json').is_file())
        uploaded = []
        def rejected(*_args): raise ValueError('installed polish rejected')
        with patch.dict(RELEASE['publish'].__globals__, {'_extra638': {'fresh': rejected}, '_original638_publish': lambda: uploaded.append(True)}):
            with self.assertRaisesRegex(ValueError, 'installed polish rejected'): RELEASE['publish']()
        self.assertEqual(uploaded, [])


if __name__ == '__main__':
    unittest.main()
