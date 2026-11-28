"""Synthetic gate wiring/rejection tests, never native publication evidence."""
import copy
from contextlib import contextmanager, redirect_stdout
import io
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'
STAGE = ROOT / 'staging/mouse/6.0.44-arm64'
E = runpy.run_path(str(TOOLS / 'mouse644-extra-evidence.py'))
with redirect_stdout(io.StringIO()):
    RELEASE = runpy.run_path(str(TOOLS / 'mouse644-release.py'))


def sync_fixture():
    accepted = {'syntheticUnitBindingFixture': True, 'version': '6.0.44', 'ok': True}
    files = {'mouse-644-sync-acceptance.json': json.dumps(accepted).encode(),
             'mouse-644-sync.json': b'{"syntheticRawReport":true}',
             'mouse-644-sync-processes.json': b'{"syntheticRawProcesses":true}'}
    ref = lambda name: {'file': name, 'sha256': E['sha'](files[name])}
    build = {'tests': list(E['SYNC_TOKENS']), 'sync644': {**ref('mouse-644-sync-acceptance.json'),
             'report': ref('mouse-644-sync.json'), 'processes': ref('mouse-644-sync-processes.json')}}
    return files, accepted, build


class CurrentPublicationBinding(unittest.TestCase):
    def check_sync(self, files, accepted, **kwargs):
        calls = []
        def load(path):
            self.assertEqual(Path(path), TOOLS / 'mouse644-sync-evidence.py')
            def verify(read, *, expected_platform, expected_arch):
                calls.append((expected_platform, expected_arch, read('mouse-644-sync.json')))
                return accepted
            return {'verify': verify}
        with patch.object(E['runpy'], 'run_path', side_effect=load):
            value = E['sync644'](files.__getitem__, platform='darwin', arch='arm64', **kwargs)
        self.assertEqual(calls, [('darwin', 'arm64', files['mouse-644-sync.json'])])
        return value

    def test_sync_recomputes_acceptance_and_binds_each_raw_hash_and_feature(self):
        files, accepted, build = sync_fixture()
        self.assertEqual(self.check_sync(files, accepted, build=build), accepted)
        self.assertEqual(self.check_sync(files, accepted), accepted)
        for token in E['SYNC_TOKENS']:
            changed = copy.deepcopy(build); changed['tests'].remove(token)
            with self.subTest(token=token), self.assertRaises(ValueError):
                self.check_sync(files, accepted, build=changed)
        for field in ('sha256', 'report', 'processes'):
            changed = copy.deepcopy(build)
            if field == 'sha256': changed['sync644'][field] = '0' * 64
            else: changed['sync644'][field]['sha256'] = '0' * 64
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.check_sync(files, accepted, build=changed)
        files['mouse-644-sync-acceptance.json'] = json.dumps({**accepted, 'invented': True}).encode()
        with self.assertRaises(ValueError): self.check_sync(files, accepted)

    def test_sync_rejects_non_mac_before_reading_or_loading(self):
        with patch.object(E['runpy'], 'run_path', side_effect=AssertionError('must reject before loading')):
            for platform, arch in (('darwin', 'x64'), ('linux', 'x64'), ('win32', 'x64')):
                with self.subTest(platform=platform), self.assertRaises(ValueError):
                    E['sync644'](lambda _: b'', platform=platform, arch=arch)

    def test_both_contracts_pin_all_required_behaviors_receipts_and_code(self):
        E['validate_644_contract'](STAGE)
        original = json.loads((STAGE / 'evidence.schema.json').read_text())
        for key in ('x-current644SyncGate', 'x-current644BrandingGate'):
            mutations = [lambda v: v.update(sha256='0' * 64),
                         lambda v: v['dependencies'].update({'mouse644-current.py': '0' * 64}),
                         lambda v: v['required'].pop(), lambda v: v['featureTokens'].pop(),
                         lambda v: v.update(runtimeVersion='6.0.43'),
                         lambda v: v.update(platform='linux'), lambda v: v.update(arch='x64'),
                         lambda v: v.update(savedReportAcceptedAsInput=True)]
            mutations += [lambda v, flag=flag: v.update({flag: False})
                          for flag, value in original[key].items() if value is True]
            with tempfile.TemporaryDirectory() as directory:
                for mutate in mutations:
                    value = copy.deepcopy(original); mutate(value[key])
                    (Path(directory) / 'evidence.schema.json').write_text(json.dumps(value))
                    with self.subTest(gate=key), self.assertRaises(ValueError):
                        E['validate_644_contract'](Path(directory))

    def test_source_import_requires_both_current_readers_and_preserves_rejection(self):
        pin = {'source': 'a' * 40, 'run': 123, 'sourceAttempt': 2}
        build = {'source': pin['source'], 'runId': '123', 'runAttempt': '2',
                 'version': '6.0.44', 'platform': 'darwin', 'arch': 'arm64'}
        @contextmanager
        def artifact(*_a, **_k):
            class Archive:
                read = staticmethod(lambda name: name.encode())
            yield Archive()
        retained = {name: lambda *_a, **_k: {'syntheticRetainedGate': True}
                    for name in ('feedback', 'adblock', 'settings', 'workspace', 'controls', 'polish')}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory); (output / 'mouse-build.json').write_text(json.dumps(build))
            module = {'OUT': output, 'PIN': pin, 'api': lambda *_a: self.fail('no network')}
            for target in ('sync644', 'branding644'):
                calls = []
                def gate(read, **kwargs):
                    calls.append(kwargs); self.assertEqual(read('owned'), b'owned')
                    return {'syntheticCurrentGate': target}
                mocks = {**retained, 'artifact': artifact, 'validate_pin': lambda *_a: None,
                         'verify_helper_bytes': lambda *_a: None,
                         'sync644': lambda *_a, **_k: {}, 'branding644': lambda *_a, **_k: {}, target: gate}
                with patch.dict(E['import_extra'].__globals__, mocks), redirect_stdout(io.StringIO()):
                    E['import_extra'](module, 'darwin')
                self.assertEqual(calls, [{'platform': 'darwin', 'arch': 'arm64', 'build': build}])
                suffix = 'sync' if target == 'sync644' else 'branding'
                self.assertEqual(json.loads((output / ('source644-' + suffix + '-independent.json')).read_text()),
                                 {'syntheticCurrentGate': target})
                def rejected(*_a, **_k): raise ValueError('rejected ' + target)
                with patch.dict(E['import_extra'].__globals__, {**mocks, target: rejected}), self.assertRaises(ValueError):
                    E['import_extra'](module, 'darwin')

    def test_either_fresh_current_gate_failure_prevents_any_asset_upload(self):
        retained = {name: lambda *_a, **_k: {'syntheticRetainedGate': True}
                    for name in ('feedback', 'adblock', 'settings', 'workspace', 'controls', 'polish')}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for target in ('sync644', 'branding644'):
                uploaded = []
                def rejected(*_a, **_k): raise ValueError('rejected ' + target)
                mocks = {**retained, 'verify_helper_bytes': lambda *_a: None,
                         'sync644': lambda *_a, **_k: {}, 'branding644': lambda *_a, **_k: {}, target: rejected}
                def fresh(*_args): E['fresh']({'OUT': output}, 'darwin')
                with patch.dict(E['fresh'].__globals__, mocks), patch.dict(RELEASE['publish'].__globals__,
                        {'_extra638': {'fresh': fresh}, '_original638_publish': lambda: uploaded.append(True)}):
                    with self.assertRaises(ValueError): RELEASE['publish']()
                self.assertEqual(uploaded, [])


if __name__ == '__main__': unittest.main()
