"""Synthetic tests of641 publication byte/process bindings, not native runs.

The deeper user-flow reader has its own adversarial tests. A labelled stub is
used here only to isolate the surrounding source/installed manifest binding.
"""
import copy
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parent
EXTRA = runpy.run_path(str(TOOLS / 'mouse641-extra-evidence.py'))


def fixture(platform='linux'):
    encode = lambda value: (json.dumps(value, indent=2) + '\n').encode()
    accepted = {'syntheticUnitBindingFixture': True, 'ok': True, 'version': '6.0.41'}
    processes = {'executable': '/installed/Mouse', 'executableSha256': 'a' * 64, 'profile': '/isolated/profile',
                 'write': {'pid': 101}, 'read': {'pid': 102}, 'reportSha256': 'b' * 64}
    files = {'mouse-641-workspace.json': encode({'syntheticUnitBindingFixture': True}),
             'mouse-641-workspace-acceptance.json': encode(accepted), 'mouse-641-workspace-processes.json': encode(processes)}
    reference = lambda name: {'file': name, 'sha256': EXTRA['sha'](files[name])}
    binding = {**reference('mouse-641-workspace-acceptance.json'), 'report': reference('mouse-641-workspace.json'),
               'processes': reference('mouse-641-workspace-processes.json')}
    install = {key: processes[key] for key in ('executable', 'executableSha256')}
    checks = {'workspace641': {**copy.deepcopy(processes), 'acceptanceSha256': binding['sha256']}}
    if platform != 'darwin':
        keys = ('debInstallation', 'debReinstallation') if platform == 'linux' else ('installation', 'reinstallation')
        for key in keys: checks[key] = copy.deepcopy(install)
    verification = {'checks': checks}
    build = {'tests': list(EXTRA['WORKSPACE_TOKENS']), 'workspace641': binding, 'verification': {'result': verification}}
    return files, processes, accepted, build, verification


class Workspace641PublicationBinding(unittest.TestCase):
    def check(self, files, accepted, platform='linux', **kwargs):
        calls = []
        def load(path):
            self.assertEqual(Path(path), TOOLS / 'mouse641-flexible-workspace-evidence.py')
            def verify(read, *, expected_platform, expected_arch):
                calls.append((expected_platform, expected_arch, read('mouse-641-workspace.json')))
                return copy.deepcopy(accepted)
            return {'verify': verify}
        with patch.object(EXTRA['runpy'], 'run_path', side_effect=load):
            result = EXTRA['workspace'](files.__getitem__, platform=platform, arch='arm64' if platform == 'darwin' else 'x64', **kwargs)
        self.assertEqual(calls, [(platform, 'arm64' if platform == 'darwin' else 'x64', files['mouse-641-workspace.json'])])
        return result

    def test_all_platform_source_manifests_and_fresh_installed_verification_use_exact_bytes(self):
        for platform in ('darwin', 'linux', 'win32'):
            files, _, accepted, build, verification = fixture(platform); before = copy.deepcopy(files)
            self.assertEqual(self.check(files, accepted, platform, build=build), accepted)
            self.assertEqual(self.check(files, accepted, platform, verification=verification), accepted)
            self.assertEqual(files, before)

    def test_every_new_feature_token_and_all_source_manifest_hashes_are_required(self):
        for token in EXTRA['WORKSPACE_TOKENS']:
            files, _, accepted, build, _ = fixture(); build['tests'].remove(token)
            with self.assertRaisesRegex(ValueError, 'feature gates'): self.check(files, accepted, build=build)
        for key in ('sha256', 'report', 'processes'):
            files, _, accepted, build, _ = fixture()
            if key == 'sha256': build['workspace641'][key] = '0' * 64
            else: build['workspace641'][key]['sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'actual641'): self.check(files, accepted, build=build)

    def test_fresh_and_modern_windows_process_wrapper_cannot_be_relabelled(self):
        for platform in ('linux', 'win32'):
            for key, value in [('profile', '/other'), ('write', {'pid': 999}), ('acceptanceSha256', '0' * 64)]:
                files, _, accepted, _, verification = fixture(platform)
                verification['checks']['workspace641'][key] = value
                with self.assertRaisesRegex(ValueError, 'wrapper differs'):
                    self.check(files, accepted, platform, verification=verification)

    def test_coherently_rehashed_foreign_executable_still_fails_actual_installation_binding(self):
        for platform in ('linux', 'win32'):
            files, processes, accepted, build, verification = fixture(platform)
            processes['executable'] = '/other/Mouse'; processes['executableSha256'] = 'c' * 64
            files['mouse-641-workspace-processes.json'] = json.dumps(processes).encode()
            build['workspace641']['processes']['sha256'] = EXTRA['sha'](files['mouse-641-workspace-processes.json'])
            verification['checks']['workspace641'] = {**processes, 'acceptanceSha256': build['workspace641']['sha256']}
            for context in ({'build': build}, {'verification': verification}):
                with self.assertRaisesRegex(ValueError, 'another executable'):
                    self.check(files, accepted, platform, **context)

    def test_saved_summary_never_substitutes_actual_reader_or_complete_raw_evidence(self):
        files, _, accepted, build, _ = fixture()
        files['mouse-641-workspace-acceptance.json'] = json.dumps({**accepted, 'invented': True}).encode()
        with self.assertRaisesRegex(ValueError, 'acceptance differs'): self.check(files, accepted, build=build)
        with self.assertRaises((ValueError, KeyError)):
            EXTRA['workspace']({'mouse-641-workspace-acceptance.json': json.dumps(accepted).encode()}.__getitem__, platform='linux', arch='x64')

    def test_independent_reader_hash_dependencies_required_files_and_native_gate_scope_are_bound(self):
        stage = TOOLS.parent / 'staging/mouse/6.0.41-arm64'
        EXTRA['validate_workspace_contract'](stage)
        original = json.loads((stage / 'evidence.schema.json').read_text())
        changes = [lambda v: v.update(sha256='0' * 64), lambda v: v['dependencies'].update({'mouse641-owner-contracts.py': '0' * 64}),
                   lambda v: v['required'].remove('mouse-641-http-read.json'), lambda v: v['featureTokens'].pop(),
                   lambda v: v.update(sourceAndFreshInstalled=False), lambda v: v.update(savedReportAcceptedAsInput=True)]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for change in changes:
                value = copy.deepcopy(original); change(value['x-current641WorkspaceGate'])
                (target / 'evidence.schema.json').write_text(json.dumps(value))
                with self.assertRaises(ValueError): EXTRA['validate_workspace_contract'](target)


if __name__ == '__main__':
    unittest.main()
