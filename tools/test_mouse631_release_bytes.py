"""Exercise the actual final Mac package gates without loading pending pins.

The small files below are synthetic package bytes, not installable artifacts.
Publisher functions are compiled unchanged from their source AST so a missing
gate at either public mutation entry point fails these contracts.
"""
import ast
import base64
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name('mouse631-release.py')
DMG = 'Mouse-Browser-6.0.31-mac-arm64.dmg'
ZIP = 'Mouse-Browser-6.0.31-mac-arm64.zip'
ALIAS = 'Quadro-Browser-6.0.31-mac-arm64.dmg'
NAMES = [DMG, ZIP, ALIAS, 'SHA256SUMS.txt', 'mouse-build.json']
FUNCTIONS = {'sha', 'verify_package_bytes', 'local_assets', 'verify_release',
             'published', 'publish', 'channel'}


class FinalPackageBytesTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='mouse631-final-bytes-')
        self.addCleanup(self.directory.cleanup)
        self.out = Path(self.directory.name)
        self.original = {DMG: b'pinned-dmg-v631', ZIP: b'pinned-zip-v631'}
        self.pin = {'packages': {name: {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                                 for name, data in self.original.items()}}
        for name, data in {**self.original, ALIAS: self.original[DMG],
                           'SHA256SUMS.txt': b'synthetic checksum fixture\n',
                           'mouse-build.json': b'{"syntheticUnitFixture":true}\n'}.items():
            (self.out / name).write_bytes(data)
        self.calls = []
        self.namespace = {'hashlib': hashlib, 'json': json, 'base64': base64,
                          'OUT': self.out, 'PIN': self.pin, 'DMG': DMG, 'ZIP': ZIP,
                          'ALIAS': ALIAS, 'NAMES': NAMES, 'V': '6.0.31',
                          'TAG': 'quadro-macos-v6.0.31-arm64', 'REPO': 'jeep-jim/OSMINOG-Releases',
                          'api': self.api}
        functions = [node for node in ast.parse(SCRIPT.read_text()).body
                     if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS]
        self.assertEqual({node.name for node in functions}, FUNCTIONS)
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(SCRIPT), 'exec'), self.namespace)

    def assets(self):
        return [{'name': name, 'state': 'uploaded', 'size': (self.out / name).stat().st_size,
                 'digest': 'sha256:' + hashlib.sha256((self.out / name).read_bytes()).hexdigest(),
                 'browser_download_url': 'https://github.com/fixture/' + name}
                for name in NAMES]

    def api(self, repo, resource, method='GET', payload=None, missing=False):
        self.calls.append((resource, method, payload))
        self.assertEqual(repo, 'jeep-jim/OSMINOG-Releases')
        if resource == 'releases/tags/quadro-macos-v6.0.31-arm64':
            return {'draft': False, 'published_at': '2026-11-19T00:00:00Z', 'assets': self.assets()}
        if resource == 'contents/channels/mouse/macos-arm64.json?ref=main':
            self.assertTrue(missing)
            return None
        if resource == 'contents/channels/mouse/macos-arm64.json' and method == 'PUT':
            return {'accepted': True}
        raise AssertionError('Unexpected public operation: ' + resource + ' ' + method)

    def mutate(self, name):
        data = (self.out / name).read_bytes()
        (self.out / name).write_bytes(bytes([data[0] ^ 1]) + data[1:])

    def test_valid_packages_and_alias_match_the_pins_without_changing_files(self):
        before = {name: (self.out / name).read_bytes() for name in NAMES}
        self.namespace['verify_package_bytes']()
        self.assertEqual(before, {name: (self.out / name).read_bytes() for name in NAMES})
        self.assertEqual(self.calls, [])

    def test_same_size_changed_dmg_or_zip_is_rejected(self):
        for name in (DMG, ZIP):
            with self.subTest(name=name):
                self.mutate(name)
                with self.assertRaisesRegex(ValueError, 'Pinned release package changed: ' + name):
                    self.namespace['verify_package_bytes']()
                (self.out / name).write_bytes(self.original[name])

    def test_matching_hash_cannot_override_a_wrong_pinned_size(self):
        for name in (DMG, ZIP):
            with self.subTest(name=name):
                self.pin['packages'][name]['size'] += 1
                with self.assertRaisesRegex(ValueError, 'Pinned release package changed: ' + name):
                    self.namespace['verify_package_bytes']()
                self.pin['packages'][name]['size'] -= 1

    def test_compatibility_alias_must_match_the_pinned_dmg(self):
        self.mutate(ALIAS)
        with self.assertRaisesRegex(ValueError, 'Pinned release package changed: ' + ALIAS):
            self.namespace['verify_package_bytes']()

    def test_missing_package_or_alias_fails_closed(self):
        for name in (DMG, ZIP, ALIAS):
            with self.subTest(name=name):
                path = self.out / name
                data = path.read_bytes()
                path.unlink()
                with self.assertRaises(FileNotFoundError):
                    self.namespace['verify_package_bytes']()
                path.write_bytes(data)

    def test_publish_and_channel_reject_changed_bytes_before_any_public_operation(self):
        for action in ('publish', 'channel'):
            for name in (DMG, ZIP, ALIAS):
                with self.subTest(action=action, name=name):
                    data = (self.out / name).read_bytes()
                    self.mutate(name)
                    with self.assertRaisesRegex(ValueError, 'Pinned release package changed: ' + name):
                        self.namespace[action]()
                    self.assertEqual(self.calls, [])
                    (self.out / name).write_bytes(data)

    def test_self_consistent_changed_local_and_remote_dmg_cannot_advance_channel(self):
        self.mutate(DMG)
        (self.out / ALIAS).write_bytes((self.out / DMG).read_bytes())
        # The old local-versus-remote comparison alone accepts these matching
        # changed bytes. The channel must first bind both files to the pin.
        self.namespace['verify_release']({'assets': self.assets()})
        with self.assertRaisesRegex(ValueError, 'Pinned release package changed: ' + DMG):
            self.namespace['channel']()
        self.assertEqual(self.calls, [])

    def test_valid_channel_checks_public_assets_then_writes_only_pinned_metadata(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.namespace['channel']()
        self.assertEqual([(resource, method) for resource, method, _ in self.calls], [
            ('releases/tags/quadro-macos-v6.0.31-arm64', 'GET'),
            ('contents/channels/mouse/macos-arm64.json?ref=main', 'GET'),
            ('contents/channels/mouse/macos-arm64.json', 'PUT')])
        payload = self.calls[-1][2]
        metadata = json.loads(base64.b64decode(payload['content']))
        self.assertEqual(metadata['version'], '6.0.31')
        self.assertEqual(metadata['size'], self.pin['packages'][DMG]['size'])
        self.assertEqual(metadata['digest'], 'sha256:' + self.pin['packages'][DMG]['sha256'])
        self.assertEqual(metadata, json.loads((self.out / 'CHANNEL_RESULT.json').read_text()))


if __name__ == '__main__':
    unittest.main()
