"""Synthetic publication binding mutations; never native release evidence."""
import copy
import json
from pathlib import Path
import runpy
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parent
FIXTURE = runpy.run_path(str(TOOLS / 'test_mouse640_adblock.py'))
EXTRA = runpy.run_path(str(TOOLS / 'mouse640-extra-evidence.py'))


def bound_fixture(platform='linux'):
    files, facts, refresh = FIXTURE['fixture']()
    arch = 'arm64' if platform == 'darwin' else 'x64'
    facts.update(platform=platform, arch=arch)
    refresh.processes.update(platform=platform, arch=arch)
    for part in (facts['write'], facts['restart']):
        for click in part['inputs']:
            click['source'] = {'darwin': 'CGEvent', 'linux': 'XTest', 'win32': 'User32'}[platform]
    refresh()
    accepted = FIXTURE['A'].verify(files.__getitem__, expected_platform=platform, expected_arch=arch)
    name = 'mouse-639-acceptance.json'
    files[name] = (json.dumps(accepted, indent=2) + '\n').encode()
    reference = lambda filename: {'file': filename, 'sha256': EXTRA['sha'](files[filename])}
    bound = {**reference(name), 'report': reference('mouse-639-adblock.json'),
             'processes': reference('mouse-639-adblock-processes.json'),
             'cache': reference('mouse-639-adblock-cache.json'), 'artifacts': accepted['artifacts']}
    wrapper = {**refresh.processes, 'acceptanceSha256': bound['sha256']}
    checks = {'adblock639': wrapper}
    if platform != 'darwin':
        installation = {key: refresh.processes[key] for key in ('executable', 'executableSha256')}
        key, repeated = ('debInstallation', 'debReinstallation') if platform == 'linux' else ('installation', 'reinstallation')
        checks[key], checks[repeated] = dict(installation), dict(installation)
    build = {'tests': ['native-adblock-network-ui-restart'], 'adblock639': bound,
             'verification': {'result': {'checks': checks}}}
    return files, facts, refresh, accepted, build, wrapper


class AdBlockPublicationBinding(unittest.TestCase):
    def test_all_platforms_bind_exact_raw_bytes_without_rewriting_evidence(self):
        for platform in ('darwin', 'linux', 'win32'):
            with self.subTest(platform=platform):
                files, _, _, accepted, build, wrapper = bound_fixture(platform)
                before = copy.deepcopy(files)
                actual = EXTRA['adblock'](files.__getitem__, platform=platform,
                    arch='arm64' if platform == 'darwin' else 'x64', build=build, wrapper=wrapper)
                self.assertEqual(actual, accepted)
                self.assertEqual(files, before)

    def test_missing_feature_report_hash_or_artifact_inventory_is_rejected(self):
        for defect in ('feature', 'binding', 'report', 'processes', 'cache', 'artifact', 'wrapper'):
            files, _, _, _, build, _ = bound_fixture()
            if defect == 'feature': build['tests'] = []
            if defect == 'binding': build.pop('adblock639')
            if defect in ('report', 'processes', 'cache'): build['adblock639'][defect]['sha256'] = '0' * 64
            if defect == 'artifact': build['adblock639']['artifacts'] = build['adblock639']['artifacts'][:-1]
            if defect == 'wrapper': build['verification']['result']['checks'].pop('adblock639')
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                EXTRA['adblock'](files.__getitem__, platform='linux', arch='x64', build=build)

    def test_fresh_wrapper_must_match_actual_processes_and_acceptance_bytes(self):
        for field, value in (('executableSha256', '0' * 64), ('cacheSeedSha256', '0' * 64),
                             ('acceptanceSha256', '0' * 64), ('profile', '/foreign/profile'), ('write', {})):
            files, _, _, _, _, wrapper = bound_fixture()
            wrapper[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'wrapper differs'):
                EXTRA['adblock'](files.__getitem__, platform='linux', arch='x64', wrapper=wrapper)

    def test_coherently_rehashed_foreign_executable_is_rejected_against_installation(self):
        for platform in ('linux', 'win32'):
            files, _, refresh, _, build, _ = bound_fixture(platform)
            refresh.processes.update(executable='/foreign/Mouse', executableSha256='b' * 64)
            refresh()
            # All raw receipts, acceptance, manifest and wrapper agree with one
            # another. Only the actual installation receipt remains unchanged.
            accepted = FIXTURE['A'].verify(files.__getitem__, expected_platform=platform, expected_arch='x64')
            files['mouse-639-acceptance.json'] = (json.dumps(accepted, indent=2) + '\n').encode()
            binding = build['adblock639']
            binding['sha256'] = EXTRA['sha'](files['mouse-639-acceptance.json'])
            for field in ('report', 'processes', 'cache'):
                binding[field]['sha256'] = EXTRA['sha'](files[binding[field]['file']])
            binding['artifacts'] = accepted['artifacts']
            verification = build['verification']['result']
            verification['checks']['adblock639'] = {**refresh.processes, 'acceptanceSha256': binding['sha256']}
            for context, arguments in (('source', {'build': build}),
                                       ('fresh-or-modern', {'verification': verification})):
                with self.subTest(platform=platform, context=context), self.assertRaisesRegex(ValueError, 'different installed executable'):
                    EXTRA['adblock'](files.__getitem__, platform=platform, arch='x64', **arguments)

    def test_stale_acceptance_or_mutated_native_requests_cannot_be_rebound(self):
        files, _, _, accepted, _, wrapper = bound_fixture()
        accepted['cases'][1]['blocked'] = False
        files['mouse-639-acceptance.json'] = json.dumps(accepted).encode()
        wrapper['acceptanceSha256'] = EXTRA['sha'](files['mouse-639-acceptance.json'])
        with self.assertRaisesRegex(ValueError, 'acceptance differs'):
            EXTRA['adblock'](files.__getitem__, platform='linux', arch='x64', wrapper=wrapper)
        files, facts, refresh, _, _, _ = bound_fixture()
        facts['write']['cases'][1]['dom']['attempted']['advertising'] = 0
        refresh()
        with self.assertRaisesRegex(ValueError, 'attempt both real script requests'):
            EXTRA['adblock'](files.__getitem__, platform='linux', arch='x64')

    def test_missing_raw_evidence_cannot_pass_with_an_existing_acceptance_summary(self):
        files, _, _, _, _, _ = bound_fixture()
        files.pop('mouse-639-adblock-http-read.json')
        with self.assertRaises(KeyError):
            EXTRA['adblock'](files.__getitem__, platform='linux', arch='x64')

    def test_reader_and_dependency_contract_mutations_fail_closed(self):
        stage = TOOLS.parent / 'staging/mouse/6.0.40-arm64'
        original = json.loads((stage / 'evidence.schema.json').read_text())
        EXTRA['validate_adblock_contract'](stage)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for defect in ('reader', 'dependency', 'required', 'fresh'):
                value = copy.deepcopy(original)
                gate = value['x-current639AdblockGate']
                if defect == 'reader': gate['sha256'] = '0' * 64
                if defect == 'dependency': gate['dependencies']['mouse640-extra-evidence.py'] = '0' * 64
                if defect == 'required': gate['required'].remove('mouse-639-adblock-http-read.json')
                if defect == 'fresh': gate['sourceAndFreshInstalled'] = False
                (target / 'evidence.schema.json').write_text(json.dumps(value))
                with self.subTest(defect=defect), self.assertRaises(ValueError):
                    EXTRA['validate_adblock_contract'](target)


if __name__ == '__main__':
    unittest.main()
