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
TRACE = runpy.run_path(str(TOOLS / 'mouse636-motion-trace.py'))
TRACE_FIXTURE = runpy.run_path(str(TOOLS / 'test-mouse627-motion-trace.py'))


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


class MotionActivationEvidence(unittest.TestCase):
    """Synthetic schema contracts, not native completion evidence."""

    def fixture(self, activation=True):
        trace, motion = TRACE_FIXTURE['observed_schema_fixture']()
        motion['version'] = '6.0.28'
        motion['trace']['file'] = 'mouse-628-motion-trace.json'
        if activation:
            host = next(event for event in trace['traceEvents']
                        if event['name'] == TRACE['UPDATE'] and event['ts'] == 201356215)
            host['name'] = TRACE['ACTIVATE']
            trace['traceEvents'].append({
                'name': TRACE['PARENT'], 'ph': 'X', 'cat': 'cc,benchmark',
                'pid': host['pid'], 'tid': host['tid'], 'ts': host['ts'] - 10,
                'dur': host['dur'] + 20,
                'args': {'main_frame_pipeline': {'step': 'ACTIVATE', 'main_frame_id': 123}}})
        self.sync(trace, motion)
        return trace, motion

    def sync(self, trace, motion):
        TRACE_FIXTURE['sync_counts'](trace, motion)
        motion['trace']['file'] = 'mouse-628-motion-trace.json'

    def rejected(self, trace, motion):
        self.sync(trace, motion)
        with self.assertRaises(TRACE['MotionTraceError']):
            TRACE['verify_trace_data'](trace, motion)

    def event(self, trace, name):
        return next(event for event in trace['traceEvents'] if event['name'] == name)

    def test_original_update_and_activation_keep_explicit_algorithm_and_raw_inputs(self):
        for activation in (False, True):
            with self.subTest(activation=activation):
                trace, motion = self.fixture(activation)
                originals = copy.deepcopy((trace, motion))
                report = TRACE['verify_trace_data'](trace, motion)
                self.assertEqual(report['algorithm'], TRACE['ALGORITHM'])
                self.assertEqual(report['compatibility']['activationFinishCount'], int(activation))
                self.assertEqual(report['maxCompletionSkewMs'], 20)
                self.assertFalse(report['directIdentityLink'])
                self.assertFalse(report['continuousCompositorLifetimeProven'])
                self.assertEqual((trace, motion), originals)
                if activation:
                    finish = report['freshCloses'][0]['finishHostUpdate']
                    self.assertEqual(finish['parent']['mainFrameId'], 123)
                    self.assertEqual({row['group'] for row in finish['terminalBindings']}, {169})
                    self.assertEqual({row['targetProperty'] for row in finish['terminalBindings']}, {0, 4})
                    self.assertFalse(finish['naturalCompositorFinishProven'])
                    with self.assertRaises(TRACE['MotionTraceError']):
                        TRACE['_base']['verify_trace_data'](trace, motion)

    def test_activation_does_not_replace_startup_host(self):
        trace, motion = self.fixture(False)
        next(event for event in trace['traceEvents'] if event['name'] == TRACE['UPDATE'])['name'] = TRACE['ACTIVATE']
        self.rejected(trace, motion)

    def test_wrong_host_provenance_and_noncovering_intervals_are_rejected(self):
        for key, value in [('pid', 99), ('tid', 101), ('ph', 'I'), ('cat', 'blink'),
                           ('name', 'UnrelatedActivation'), ('dur', 1), ('dur', -1),
                           ('ts', 201356230)]:
            with self.subTest(key=key, value=value):
                trace, motion = self.fixture()
                self.event(trace, TRACE['ACTIVATE'])[key] = value
                self.rejected(trace, motion)

    def test_parent_identity_interval_and_pipeline_are_mandatory(self):
        for key, value in [('pid', 99), ('tid', 101), ('ph', 'I'), ('cat', 'blink'),
                           ('name', 'UnrelatedParent'), ('dur', 1), ('ts', 201356230)]:
            with self.subTest(key=key, value=value):
                trace, motion = self.fixture()
                self.event(trace, TRACE['PARENT'])[key] = value
                self.rejected(trace, motion)
        for pipeline in ({}, {'step': 'COMMIT', 'main_frame_id': 123},
                         {'step': 'ACTIVATE', 'main_frame_id': True},
                         {'step': 'ACTIVATE', 'main_frame_id': 0}):
            with self.subTest(pipeline=pipeline):
                trace, motion = self.fixture()
                self.event(trace, TRACE['PARENT'])['args']['main_frame_pipeline'] = pipeline
                self.rejected(trace, motion)

    def test_duplicate_or_competing_hosts_and_parents_are_rejected(self):
        for name in (TRACE['ACTIVATE'], TRACE['PARENT'], TRACE['UPDATE']):
            with self.subTest(name=name):
                trace, motion = self.fixture()
                duplicate = copy.deepcopy(self.event(trace, TRACE['PARENT'] if name == TRACE['PARENT']
                                                       else TRACE['ACTIVATE']))
                duplicate['name'] = name
                trace['traceEvents'].append(duplicate)
                self.rejected(trace, motion)
        trace, motion = self.fixture()
        trace['traceEvents'].remove(self.event(trace, TRACE['PARENT']))
        self.rejected(trace, motion)

    def test_separate_host_for_each_property_is_not_one_pair(self):
        trace, motion = self.fixture()
        host = self.event(trace, TRACE['ACTIVATE'])
        second = copy.deepcopy(host)
        host['dur'] = 14
        second['ts'] += 15
        second['dur'] = 14
        trace['traceEvents'].append(second)
        self.rejected(trace, motion)

    def test_exact_group_property_pointer_terminal_and_thread_bindings_remain_required(self):
        for key, value in [('group', 777), ('targetProperty', 5),
                           ('from', 'PAUSED'), ('to', 'ABORTED')]:
            with self.subTest(key=key, value=value):
                trace, motion = self.fixture()
                terminal = next(event for event in trace['traceEvents']
                                if event.get('tid') == 102 and event.get('args', {}).get('ccModel', {}).get('group') == 169
                                and event['args']['ccModel'].get('to') == 'FINISHED')
                terminal['args']['ccModel'][key] = value
                self.rejected(trace, motion)
        for change in ('thread', 'pointer', 'missing-end', 'duplicate-end'):
            with self.subTest(change=change):
                trace, motion = self.fixture()
                end = next(event for event in trace['traceEvents']
                           if event['name'] == 'KeyframeModel' and event['ph'] == 'e' and event['ts'] == 201356225)
                if change == 'thread':
                    end['tid'] = 101
                elif change == 'pointer':
                    end['id2'] = {'local': '0xffff'}
                elif change == 'missing-end':
                    trace['traceEvents'].remove(end)
                else:
                    trace['traceEvents'].append(copy.deepcopy(end))
                self.rejected(trace, motion)

    def test_dom_completion_skew_trace_loss_and_pinned_versions_are_unchanged(self):
        for change in ('dom', 'skew', 'loss', 'version'):
            with self.subTest(change=change):
                trace, motion = self.fixture()
                if change == 'dom':
                    rows = motion['geometry']['lightClosing']['startup']['events']
                    next(row for row in rows if row['event'] == 'complete')['shade']['currentTime'] = 1
                elif change == 'skew':
                    end = next(event for event in trace['traceEvents']
                               if event['name'] == 'Animation' and event['ph'] == 'e' and event['ts'] > 201350000)
                    end['ts'] -= 21000
                elif change == 'loss':
                    trace['mouseMotionTrace']['dataLossOccurred'] = True
                else:
                    trace['mouseMotionTrace']['versions']['chrome'] = '153.0.0.0'
                self.rejected(trace, motion)


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
