#!/usr/bin/env python3
"""Reject incomplete637 publication manifests before native runners start."""
from contextlib import redirect_stdout
import ast
import copy
import io
import json
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
with redirect_stdout(io.StringIO()):
    RELEASE = runpy.run_path(str(ROOT / 'tools/mouse637-release.py'))
FEATURES = runpy.run_path(str(ROOT / 'tools/mouse637-features-evidence.py'))


class FeatureManifest(unittest.TestCase):
    def source_build_tokens(self):
        fixture = json.loads((ROOT / 'tools/fixtures/mouse637-macos-build-feature-tokens.json').read_text(encoding='utf-8'))
        self.assertEqual(fixture['sourceBase'], '554fbd5c1da7dbe385fab1385d8f51dc06595d4f')
        self.assertEqual(fixture['change'], 'owner-requested-agent-removal')
        self.assertRegex(fixture['workflowSHA256'], r'^[0-9a-f]{64}$')
        self.assertEqual(fixture['path'], '.github/workflows/mouse-macos.yml')
        return fixture['tests']

    def check_source_build_tokens(self, tokens):
        # Execute the actual retained import predicate against the current
        # runtime requirements; no native facts or reports are substituted.
        tree = RELEASE['_reuse']['adapted_tree']('mouse632-release.py')
        importer = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef) and node.name == 'import_candidate')
        guards = [node for node in importer.body if isinstance(node, ast.If) and any(
            isinstance(part, ast.Name) and part.id == 'FEATURE_TOKENS_632'
            for part in ast.walk(node.test))]
        self.assertEqual(len(guards), 1)
        scope = RELEASE['import_candidate'].__globals__.copy()
        scope['b'] = {'tests': tokens}
        exec(compile(ast.Module(body=guards, type_ignores=[]), '<production-manifest-guard>', 'exec'), scope)

    def test_exact_source_build_declaration_satisfies_current_import_gate(self):
        self.check_source_build_tokens(self.source_build_tokens())

    def test_missing_or_different_published_predecessor_declaration_is_rejected(self):
        token = 'real-636-to-637-profile-preserving-replacement'
        for replacement in (None, 'real-published-predecessor-to-637-profile-preserving-replacement',
                            'real-635-to-637-profile-preserving-replacement',
                            'real-634-to-637-profile-preserving-replacement'):
            with self.subTest(replacement=replacement):
                tokens = [value for value in self.source_build_tokens() if value != token]
                if replacement is not None:
                    tokens.append(replacement)
                with self.assertRaisesRegex(ValueError, 'owner feedback features incomplete'):
                    self.check_source_build_tokens(tokens)

    def test_source_build_still_requires_every_retained_owner_feature(self):
        tokens = self.source_build_tokens()
        for token in RELEASE['FEATURE_TOKENS_632']:
            with self.subTest(token=token):
                with self.assertRaisesRegex(ValueError, 'owner feedback features incomplete'):
                    self.check_source_build_tokens([value for value in tokens if value != token])

    def check_schema(self, schema):
        validator = RELEASE['validate_template']
        scope, previous = validator.__globals__, validator.__globals__['STAGE']
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            (stage / 'evidence.schema.json').write_text(json.dumps(schema), encoding='utf-8')
            (stage / 'RELEASE_NOTES.md').write_text('# Mouse Browser 6.0.37\n', encoding='utf-8')
            try:
                scope['STAGE'] = stage
                with redirect_stdout(io.StringIO()):
                    validator()
            finally:
                scope['STAGE'] = previous

    def schema(self):
        return json.loads((ROOT / 'staging/mouse/6.0.37-arm64/evidence.schema.json').read_text(encoding='utf-8'))

    def test_complete_manifest_tracks_native_scenarios_and_dependencies(self):
        schema = self.schema()
        self.check_schema(schema)
        gate = schema['x-current637FeaturesGate']
        self.assertEqual(gate['nativeCaptures'], 36)
        self.assertEqual(gate['writeNativeCaptures'], 34)
        self.assertEqual(gate['readNativeCaptures'], 2)
        self.assertEqual(gate['nativeCaptureNames'], FEATURES['CAPTURES'])
        self.assertEqual(len(set(gate['nativeCaptureNames'])), 36)
        self.assertTrue({'mouse637-presets-evidence.py', 'mouse637-sidebar-focus-evidence.py', 'mouse637-library-actions-evidence.py', 'mouse637-update-ui-evidence.py'} <= set(gate['dependencies']))

    def test_old_counts_missing_frames_and_stale_dependency_bytes_fail(self):
        mutations = [lambda gate: gate.update(nativeCaptures=21),
                     lambda gate: gate.update(writeNativeCaptures=19),
                     lambda gate: gate.update(readNativeCaptures=1),
                     lambda gate: gate['nativeCaptureNames'].pop(),
                     lambda gate: gate['dependencies'].pop('mouse637-library-actions-evidence.py'),
                     lambda gate: gate['dependencies'].pop('mouse637-update-ui-evidence.py'),
                     lambda gate: gate['dependencies'].update({'mouse637-presets-evidence.py': '0' * 64})]
        for mutate in mutations:
            schema = copy.deepcopy(self.schema())
            mutate(schema['x-current637FeaturesGate'])
            with self.assertRaises(ValueError):
                self.check_schema(schema)

    def test_each_publisher_retains_actual_text_file_drop_bytes(self):
        for suffix, folder in [('', 'mouse637-release'), ('-windows', 'mouse637-windows-release'), ('-linux', 'mouse637-linux-release')]:
            text = (ROOT / ('.github/workflows/publish-mouse637' + suffix + '.yml')).read_text(encoding='utf-8')
            self.assertIn(folder + '/mouse-637-library-source.txt', text)
            self.assertIn(folder + '/*.png', text)


if __name__ == '__main__':
    unittest.main()
