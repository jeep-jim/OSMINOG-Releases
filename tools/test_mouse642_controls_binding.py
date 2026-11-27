"""Synthetic tests of642 publication byte/process bindings, not native runs.

The deeper user-flow reader has its own adversarial tests. A labelled stub is
used here only to isolate the surrounding source/installed manifest binding.
"""
import ast
import copy
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parent
EXTRA = runpy.run_path(str(TOOLS / 'mouse642-extra-evidence.py'))


def fixture(platform='linux'):
    encode = lambda value: (json.dumps(value, indent=2) + '\n').encode()
    accepted = {'syntheticUnitBindingFixture': True, 'ok': True, 'version': '6.0.42'}
    processes = {'executable': '/installed/Mouse', 'executableSha256': 'a' * 64, 'profile': '/isolated/profile',
                 'write': {'pid': 101}, 'read': {'pid': 102}, 'reportSha256': 'b' * 64}
    files = {'mouse-642-controls.json': encode({'syntheticUnitBindingFixture': True}),
             'mouse-642-controls-acceptance.json': encode(accepted), 'mouse-642-controls-processes.json': encode(processes)}
    reference = lambda name: {'file': name, 'sha256': EXTRA['sha'](files[name])}
    binding = {**reference('mouse-642-controls-acceptance.json'), 'report': reference('mouse-642-controls.json'),
               'processes': reference('mouse-642-controls-processes.json')}
    install = {key: processes[key] for key in ('executable', 'executableSha256')}
    checks = {'controls642': {**copy.deepcopy(processes), 'acceptanceSha256': binding['sha256']}}
    if platform != 'darwin':
        keys = ('debInstallation', 'debReinstallation') if platform == 'linux' else ('installation', 'reinstallation')
        for key in keys: checks[key] = copy.deepcopy(install)
    verification = {'checks': checks}
    build = {'tests': list(EXTRA['CONTROLS_TOKENS']), 'controls642': binding, 'verification': {'result': verification}}
    return files, processes, accepted, build, verification


class Controls642PublicationBinding(unittest.TestCase):
    def check(self, files, accepted, platform='linux', **kwargs):
        calls = []
        def load(path):
            self.assertEqual(Path(path), TOOLS / 'mouse642-controls-evidence.py')
            def verify(read, *, expected_platform, expected_arch):
                calls.append((expected_platform, expected_arch, read('mouse-642-controls.json')))
                return copy.deepcopy(accepted)
            return {'verify': verify}
        with patch.object(EXTRA['runpy'], 'run_path', side_effect=load):
            result = EXTRA['controls'](files.__getitem__, platform=platform, arch='arm64' if platform == 'darwin' else 'x64', **kwargs)
        self.assertEqual(calls, [(platform, 'arm64' if platform == 'darwin' else 'x64', files['mouse-642-controls.json'])])
        return result

    def test_all_platform_source_manifests_and_fresh_installed_verification_use_exact_bytes(self):
        for platform in ('darwin', 'linux', 'win32'):
            files, _, accepted, build, verification = fixture(platform); before = copy.deepcopy(files)
            self.assertEqual(self.check(files, accepted, platform, build=build), accepted)
            self.assertEqual(self.check(files, accepted, platform, verification=verification), accepted)
            self.assertEqual(files, before)

    def test_every_new_feature_token_and_all_source_manifest_hashes_are_required(self):
        for token in EXTRA['CONTROLS_TOKENS']:
            files, _, accepted, build, _ = fixture(); build['tests'].remove(token)
            with self.assertRaisesRegex(ValueError, 'feature gates'): self.check(files, accepted, build=build)
        for key in ('sha256', 'report', 'processes'):
            files, _, accepted, build, _ = fixture()
            if key == 'sha256': build['controls642'][key] = '0' * 64
            else: build['controls642'][key]['sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'actual642'): self.check(files, accepted, build=build)

    def test_fresh_and_modern_windows_process_wrapper_cannot_be_relabelled(self):
        for platform in ('linux', 'win32'):
            for key, value in [('profile', '/other'), ('write', {'pid': 999}), ('acceptanceSha256', '0' * 64)]:
                files, _, accepted, _, verification = fixture(platform)
                verification['checks']['controls642'][key] = value
                with self.assertRaisesRegex(ValueError, 'wrapper differs'):
                    self.check(files, accepted, platform, verification=verification)

    def test_coherently_rehashed_foreign_executable_still_fails_actual_installation_binding(self):
        for platform in ('linux', 'win32'):
            files, processes, accepted, build, verification = fixture(platform)
            processes['executable'] = '/other/Mouse'; processes['executableSha256'] = 'c' * 64
            files['mouse-642-controls-processes.json'] = json.dumps(processes).encode()
            build['controls642']['processes']['sha256'] = EXTRA['sha'](files['mouse-642-controls-processes.json'])
            verification['checks']['controls642'] = {**processes, 'acceptanceSha256': build['controls642']['sha256']}
            for context in ({'build': build}, {'verification': verification}):
                with self.assertRaisesRegex(ValueError, 'another executable'):
                    self.check(files, accepted, platform, **context)

    def test_saved_summary_never_substitutes_actual_reader_or_complete_raw_evidence(self):
        files, _, accepted, build, _ = fixture()
        files['mouse-642-controls-acceptance.json'] = json.dumps({**accepted, 'invented': True}).encode()
        with self.assertRaisesRegex(ValueError, 'acceptance differs'): self.check(files, accepted, build=build)
        with self.assertRaises((ValueError, KeyError)):
            EXTRA['controls']({'mouse-642-controls-acceptance.json': json.dumps(accepted).encode()}.__getitem__, platform='linux', arch='x64')

    def test_independent_reader_hash_dependencies_required_files_and_native_gate_scope_are_bound(self):
        stage = TOOLS.parent / 'staging/mouse/6.0.42-arm64'
        EXTRA['validate_controls_contract'](stage)
        original = json.loads((stage / 'evidence.schema.json').read_text())
        changes = [lambda v: v.update(sha256='0' * 64), lambda v: v['dependencies'].update({'mouse642-current.py': '0' * 64}),
                   lambda v: v['required'].remove('mouse-642-controls-read.log'), lambda v: v['featureTokens'].pop(),
                   lambda v: v.update(sourceAndFreshInstalled=False), lambda v: v.update(savedReportAcceptedAsInput=True),
                   lambda v: v.update(runtimeVersion='6.0.41'), lambda v: v.update(realOSInputLanguage=False),
                   lambda v: v.update(explicitConsentBeforeReplacement=False), lambda v: v.update(nativeUndo=False)]
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for change in changes:
                value = copy.deepcopy(original); change(value['x-current642ControlsGate'])
                (target / 'evidence.schema.json').write_text(json.dumps(value))
                with self.assertRaises(ValueError): EXTRA['validate_controls_contract'](target)

    def test_fresh_installed_gate_replays_controls_on_every_platform(self):
        for platform in ('darwin', 'linux', 'win32'):
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory)
                if platform != 'darwin':
                    name = 'mouse-linux-verification.json' if platform == 'linux' else 'mouse-windows-verification.json'
                    (output / name).write_text(json.dumps({'syntheticBindingFixture': True}))
                calls = []
                def controls(read, **kwargs):
                    calls.append(kwargs)
                    return {'syntheticBindingFixture': True, 'ok': True}
                scope = EXTRA['fresh'].__globals__
                previous = {name: (lambda *_args, **_kwargs: {'syntheticBindingFixture': True})
                            for name in ('feedback', 'adblock', 'settings', 'workspace')}
                with patch.dict(scope, {**previous, 'controls': controls}):
                    EXTRA['fresh']({'OUT': output}, platform)
                self.assertEqual(len(calls), 1)
                self.assertEqual(calls[0]['platform'], platform)
                self.assertTrue((output / 'installed642-controls-independent.json').is_file())
                with patch.dict(scope, {**previous, 'controls': lambda *_a, **_k: (_ for _ in ()).throw(ValueError('rejected controls'))}):
                    with self.assertRaisesRegex(ValueError, 'rejected controls'): EXTRA['fresh']({'OUT': output}, platform)

    def test_a_failed_fresh_gate_prevents_asset_publication_on_every_platform(self):
        for filename in ('mouse642-release.py', 'mouse642-linux-release.py', 'mouse642-windows-release.py'):
            module = runpy.run_path(str(TOOLS / filename)); calls = []
            def rejected(*_args):
                raise ValueError('controls not accepted')
            with patch.dict(module['publish'].__globals__, {'_extra638': {'fresh': rejected}, '_original638_publish': lambda: calls.append('uploaded')}):
                with self.assertRaisesRegex(ValueError, 'controls not accepted'): module['publish']()
            self.assertEqual(calls, [])

    def test_retained_interface_language_proof_moves_exactly_one_selector_to_settings(self):
        reuse = runpy.run_path(str(TOOLS / 'mouse642-reuse.py'))
        tree = reuse['adapted_tree']('mouse637-features-evidence.py')
        constants = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant)]
        self.assertEqual(constants.count('#settings-language'), 1)
        self.assertNotIn('#language-select', constants)
        original = reuse['legacy']()['adapted_tree']('mouse637-features-evidence.py', current_native=False)
        for duplicate in (False, True):
            altered = copy.deepcopy(original)
            old = [node for node in ast.walk(altered) if isinstance(node, ast.Constant) and node.value == '#language-select']
            self.assertEqual(len(old), 1)
            if duplicate:
                altered.body.append(ast.Expr(value=ast.Constant(value='#language-select')))
            else:
                old[0].value = '#unrelated-control'
            with patch.dict(reuse['adapted_tree'].__globals__, {'legacy': lambda: {'adapted_tree': lambda *_args, **_kwargs: altered}}):
                with self.assertRaisesRegex(ValueError, 'exact frozen selector'):
                    reuse['adapted_tree']('mouse637-features-evidence.py')

    def test_retained_footer_requires_temperature_then_real_input_language(self):
        reuse = runpy.run_path(str(TOOLS / 'mouse642-reuse.py'))
        tree = reuse['adapted_tree']('mouse636-feedback-evidence.py')
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and len(node.args) == 2
                 and isinstance(node.args[1], ast.Constant) and node.args[1].value == 'requested footer order differs']
        self.assertEqual(len(calls), 1)
        predicate = compile(ast.Expression(calls[0].args[0]), '<retained-footer-contract>', 'eval')
        correct = {'left': ['website'], 'right': ['footer-library', 'ai-toggle', 'version-button', 'temperature-button',
                   'input-language-button', 'input-language-more', 'theme-button', 'settings-button'], 'themeBeforeSettings': True}
        self.assertTrue(eval(predicate, {'c': correct}))
        for changed in [lambda value: value['right'].remove('temperature-button'),
                        lambda value: value['right'].insert(3, 'language-select'),
                        lambda value: value['right'].reverse(),
                        lambda value: value['right'].insert(3, 'input-language-button'),
                        lambda value: value.update(left=['website', 'privacy']),
                        lambda value: value.update(themeBeforeSettings=False)]:
            value = copy.deepcopy(correct); changed(value)
            self.assertFalse(eval(predicate, {'c': value}))
        current = runpy.run_path(str(TOOLS / 'mouse642-feedback-evidence.py'))['verify_footer']
        self.assertIn('temperature-button', current.__code__.co_consts)


if __name__ == '__main__':
    unittest.main()
