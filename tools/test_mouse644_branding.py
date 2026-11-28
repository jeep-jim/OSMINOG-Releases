"""Synthetic rejection checks; these fixtures are never publication evidence."""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import unittest

B = runpy.run_path(str(Path(__file__).with_name('mouse644-branding-evidence.py')))


def fixture():
    application = '/owned/installed/Mouse Browser.app'
    after = '/owned/update/Applications/Mouse Browser.app'
    installed = {'ok': True, 'application': application, 'displayName': 'Mouse',
                 'localizedDisplayName': 'Mouse', 'localizedBundleName': 'Mouse',
                 'compatibilityBundleName': 'Mouse Browser.app', 'executable': 'Mouse Browser',
                 'appId': 'com.osminog.desktop.preview', 'version': '6.0.44',
                 'languages': ['en.lproj', 'ru.lproj'], 'verifiedAt': '2026-11-28T03:00:00Z'}
    updated = {**installed, 'application': after}
    facts = {'ok': True, 'version': '6.0.44', 'fromVersion': '6.0.43', 'toVersion': '6.0.44',
             'platform': 'darwin', 'arch': 'arm64', 'oldInstallation': {'target': after},
             'updatedDisplayName': copy.deepcopy(updated)}
    processes = {'version': '6.0.44', 'platform': 'darwin', 'arch': 'arm64',
                 'executable': application + '/Contents/MacOS/Mouse Browser'}
    values = dict(zip(B['FILES'], (installed, updated, facts, processes)))
    build = {'displayName': 'Mouse', 'productName': 'Mouse Browser', 'branding': installed,
             'tests': ['native644-macos-display-name']}
    return values, build


def encode(values):
    return {name: (json.dumps(value, sort_keys=True) + '\n').encode() for name, value in values.items()}


class NativeBrandingBinding(unittest.TestCase):
    def test_binds_both_raw_receipts_and_exact_installed_update_paths(self):
        values, build = fixture(); raw = encode(values)
        result = B['verify'](raw.__getitem__, build=build)
        self.assertEqual(result['physicalUserDeviceVerified'], False)
        self.assertEqual(result['checks'], ['native644-macos-display-name'])
        self.assertEqual(result['artifacts'], [{'file': name, 'bytes': len(raw[name]),
            'sha256': hashlib.sha256(raw[name]).hexdigest()} for name in B['FILES']])
        self.assertEqual(B['verify'](raw.__getitem__), result)

    def test_old_caption_or_changed_bundle_identity_cannot_pass(self):
        for name in B['FILES'][:2]:
            for key, wrong in [('displayName', 'Mouse Browser'), ('localizedDisplayName', 'Браузер'),
                               ('localizedBundleName', 'Mouse Browser'), ('executable', 'Mouse'),
                               ('compatibilityBundleName', 'Mouse.app'), ('appId', 'new.id'),
                               ('version', '6.0.43'), ('languages', ['en.lproj']),
                               ('verifiedAt', 'missing'), ('application', 'relative/Mouse Browser.app')]:
                values, build = fixture(); values = copy.deepcopy(values)
                values[name][key] = wrong
                with self.subTest(name=name, key=key), self.assertRaises(ValueError):
                    B['verify'](encode(values).__getitem__, build=build)

    def test_display_receipt_cannot_be_reused_for_another_native_install_or_update(self):
        changes = [lambda v: v[B['FILES'][3]].update(executable='/other/Mouse Browser.app/Contents/MacOS/Mouse Browser'),
                   lambda v: v[B['FILES'][2]]['oldInstallation'].update(target='/other/Mouse Browser.app'),
                   lambda v: v[B['FILES'][2]].update(fromVersion='6.0.42'),
                   lambda v: v[B['FILES'][2]]['updatedDisplayName'].update(verifiedAt='2026-11-28T04:00:00Z'),
                   lambda v: v[B['FILES'][2]].update(ok=False)]
        for change in changes:
            values, build = fixture(); values = copy.deepcopy(values); change(values)
            with self.assertRaises(ValueError): B['verify'](encode(values).__getitem__, build=build)

    def test_manifest_must_contain_the_same_native_names_and_declared_gate(self):
        for key, value in [('displayName', 'Mouse Browser'), ('productName', 'Mouse'), ('branding', {}), ('tests', [])]:
            values, build = fixture(); build = copy.deepcopy(build); build[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): B['verify'](encode(values).__getitem__, build=build)

    def test_missing_receipts_or_non_mac_platforms_cannot_pass(self):
        for name in B['FILES']:
            values, build = fixture(); del values[name]
            with self.subTest(name=name), self.assertRaises(KeyError): B['verify'](encode(values).__getitem__, build=build)
        for platform, arch in [('darwin', 'x64'), ('win32', 'x64'), ('linux', 'x64')]:
            with self.subTest(platform=platform), self.assertRaises(ValueError):
                B['verify'](lambda _: (_ for _ in ()).throw(AssertionError('must reject before reading')),
                            platform=platform, arch=arch)


if __name__ == '__main__': unittest.main()
