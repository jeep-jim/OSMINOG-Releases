#!/usr/bin/env python3
"""Reject incomplete637 publication manifests before native runners start."""
from contextlib import redirect_stdout
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
        self.assertEqual(gate['nativeCaptures'], 38)
        self.assertEqual(gate['writeNativeCaptures'], 36)
        self.assertEqual(gate['readNativeCaptures'], 2)
        self.assertEqual(gate['nativeCaptureNames'], FEATURES['CAPTURES'])
        self.assertEqual(len(set(gate['nativeCaptureNames'])), 38)
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
