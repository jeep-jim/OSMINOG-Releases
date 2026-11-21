#!/usr/bin/env python3
"""Reject incomplete release sets, altered helpers, evidence and timing summaries."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parent
PLAN = runpy.run_path(str(TOOLS / 'mouse636-publish-plan.py'))
PERF = runpy.run_path(str(TOOLS / 'mouse636-performance-evidence.py'))
CURRENT = runpy.run_path(str(TOOLS / 'mouse636-current.py'))
OWNER = runpy.run_path(str(TOOLS / 'mouse636-owner-feedback-evidence.py'))


class PublicationPlan(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.calls = []
        for platform in PLAN['PLATFORMS']:
            self.write(platform, False)

    def write(self, platform, ready, **changes):
        folder, _, _, trigger = PLAN['PLATFORMS'][platform]
        stage = self.root / 'staging/mouse' / folder
        stage.mkdir(parents=True, exist_ok=True)
        value = {'version': '6.0.36', 'ready': ready, 'source': 'a'*40 if ready else None,
                 'sourceMerge': 'b'*40 if ready else None, 'sourcePR': 190 if ready else None,
                 'packages': {'package': {'size': 100 if ready else None, 'sha256': 'c'*64 if ready else None}}, **changes}
        (stage/'pin.json').write_text(json.dumps(value))
        if ready:
            (stage/'PUBLISH_OWNER').write_text(trigger+'\n')
        elif (stage/'PUBLISH_OWNER').exists():
            (stage/'PUBLISH_OWNER').unlink()

    def load(self, path):
        def validate():
            self.calls.append(Path(path).name)
        return {'validate': validate, 'pin': validate}

    def ready(self):
        return PLAN['publication_ready']('macos-arm64', root=self.root, load=self.load)

    def test_templates_never_allocate_a_publisher(self):
        self.assertFalse(self.ready())
        self.assertEqual(self.calls, [])

    def test_partial_platform_set_cannot_publish(self):
        self.write('macos-arm64', True)
        self.write('windows-x64', True)
        self.assertFalse(self.ready())
        self.assertEqual(self.calls, [])

    def test_all_platforms_require_their_full_pin_validator(self):
        for platform in PLAN['PLATFORMS']:
            self.write(platform, True)
        self.assertTrue(self.ready())
        self.assertEqual(self.calls, [v[1] for v in PLAN['PLATFORMS'].values()])

    def test_mixed_commits_and_prs_are_rejected(self):
        for key, changed in [('source', 'd'*40), ('sourceMerge', 'e'*40), ('sourcePR', 191)]:
            with self.subTest(key=key):
                for platform in PLAN['PLATFORMS']:
                    self.write(platform, True)
                self.write('linux-x64', True, **{key: changed})
                with self.assertRaises(ValueError):
                    self.ready()

    def test_unready_claims_and_forged_trigger_are_rejected(self):
        self.write('linux-x64', False, source='a'*40)
        with self.assertRaises(ValueError):
            self.ready()
        self.write('linux-x64', True)
        folder = PLAN['PLATFORMS']['linux-x64'][0]
        (self.root/'staging/mouse'/folder/'PUBLISH_OWNER').write_text('publish something else')
        with self.assertRaises(ValueError):
            self.ready()


class TimingEvidence(unittest.TestCase):
    def reports(self):
        def report(candidate):
            rows = []
            for count, pages in ((5, 20), (10, 50)):
                values = [80+i if candidate else 500+i for i in range(count)]
                event = [1, 2, 3]
                rows.append({'ownedPageCount': pages, 'deskCount': 5, 'switchCount': count,
                    'switches': [{'elapsedMs': value, 'counts': {'capturePage': 0 if candidate else 8}} for value in values],
                    'switchLatencyMs': PERF['distribution'](values), 'mainEventLoopSamplesMs': event,
                    'mainEventLoop': PERF['distribution'](event),
                    'renderer': {'gaps': event, 'gapDistribution': PERF['distribution'](event)}})
            return {'stages': rows}
        return report(False), report(True)

    def test_percentiles_are_recomputed_from_raw_samples(self):
        old, new = self.reports()
        calculated = PERF['compare'](old, new)
        self.assertEqual(calculated[1]['candidate']['switchLatencyMs']['p95'], 88)
        new['stages'][1]['switchLatencyMs']['p95'] = 1
        with self.assertRaises(ValueError):
            PERF['compare'](old, new)

    def test_capture_regression_and_slow_tail_are_rejected(self):
        old, new = self.reports()
        new['stages'][0]['switches'][0]['counts']['capturePage'] = 1
        with self.assertRaises(ValueError):
            PERF['compare'](old, new)
        old, new = self.reports()
        new['stages'][1]['switches'][-1]['elapsedMs'] = 601
        new['stages'][1]['switchLatencyMs'] = PERF['distribution']([v['elapsedMs'] for v in new['stages'][1]['switches']])
        with self.assertRaises(ValueError):
            PERF['compare'](old, new)

    def test_no_improvement_or_bad_samples_are_rejected(self):
        old, new = self.reports()
        for row in new['stages']:
            for value in row['switches']:
                value['elapsedMs'] += 600
            row['switchLatencyMs'] = PERF['distribution']([v['elapsedMs'] for v in row['switches']])
        with self.assertRaises(ValueError):
            PERF['compare'](old, new)
        for values in ([], [float('nan')], [float('inf')], [-1], [True]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                PERF['distribution'](values)


class HelpersAndContracts(unittest.TestCase):
    def test_source_helper_git_blob_identity_is_mandatory(self):
        raw = b'owned helper bytes\n'
        blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        calls = []
        def api(repo, path):
            calls.append((repo, path))
            return {'sha': blob, 'content': base64.b64encode(raw).decode()}
        with tempfile.TemporaryDirectory() as d:
            CURRENT['fetch_helpers'](api, 'jeep-jim/OSMINOG', 'a'*40, Path(d))
            self.assertEqual({p.name for p in Path(d).iterdir()}, set(CURRENT['HELPERS']))
            self.assertTrue(all(path.endswith('?ref='+'a'*40) for _, path in calls))
            with self.assertRaises(ValueError):
                CURRENT['fetch_helpers'](lambda *_: {'sha': 'f'*40, 'content': base64.b64encode(raw).decode()},
                                         'jeep-jim/OSMINOG', 'a'*40, Path(d))

    def test_historical_reuse_bytes_unchanged_and_new_modules_load(self):
        reuse = runpy.run_path(str(TOOLS/'mouse636-reuse.py'))
        for name in reuse['FROZEN']:
            reuse['checked'](name)
        for name in ('mouse636-release.py', 'mouse636-windows-release.py', 'mouse636-linux-release.py',
                     'mouse636-feedback-evidence.py', 'mouse636-owner-feedback-evidence.py'):
            self.assertIsInstance(runpy.run_path(str(TOOLS/name)), dict)

    def test_template_hashes_bind_current_validators(self):
        runpy.run_path(str(TOOLS/'mouse636-release.py'))['validate_template']()
        runpy.run_path(str(TOOLS/'mouse636-linux-release.py'))['validate_template']()
        self.assertIn('MOUSE_636_SEARCH_REMOVAL_PASS', OWNER['MARKERS'])
        self.assertIn('MOUSE_636_AGENT_INLINE_PASS', OWNER['MARKERS'])
        self.assertIn('MOUSE_636_PERFORMANCE_PASS', OWNER['MARKERS'])
        self.assertFalse(any('PUBLIC_SEARCH' in marker or 'AGENT_CHAT' in marker for marker in OWNER['MARKERS']))


if __name__ == '__main__':
    unittest.main()
