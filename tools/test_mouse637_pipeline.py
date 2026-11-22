#!/usr/bin/env python3
"""637 publication contracts; synthetic unit evidence is not native completion."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest
TOOLS=Path(__file__).resolve().parent
PLAN=runpy.run_path(str(TOOLS/'mouse637-publish-plan.py'))
TRACE=runpy.run_path(str(TOOLS/'mouse637-motion-trace.py'))
TRACE_FIXTURE=runpy.run_path(str(TOOLS/'test-mouse627-motion-trace.py'))
REUSE=runpy.run_path(str(TOOLS/'mouse637-reuse.py'))

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
        value = {'version': '6.0.37', 'ready': ready, 'source': 'a'*40 if ready else None,
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

class FrozenAndPaletteContracts(unittest.TestCase):
    def test_source_task_algorithm_stays_byte_identical_except_runtime_identity(self):
        old=REUSE['checked']('mouse636-task-evidence.py').decode('utf-8')
        expected=old.replace('verification of installed Mouse 6.0.35 evidence','verification of installed Mouse 6.0.37 evidence').replace("VERSION = '6.0.36'", "VERSION = '6.0.37'")
        self.assertEqual((TOOLS/'mouse637-task-evidence.py').read_text(encoding='utf-8'),expected)

    def test_every_frozen636_dependency_remains_byte_identical(self):
        for name,expected in REUSE['FROZEN'].items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256(REUSE['checked'](name)).hexdigest(),expected)

    def test_only637_uses_the_requested_darker_seam_palette(self):
        for version,color in [('636',[67,83,107]),('637',[53,67,87])]:
            for kind in ['native-evidence','retained-native-evidence','workspace-evidence']:
                with self.subTest(version=version,kind=kind):
                    module=runpy.run_path(str(TOOLS/('mouse'+version+'-'+kind+'.py')))
                    self.assertEqual(module['LINE'],{'light':[199,207,223],'dark':color})
        current=runpy.run_path(str(TOOLS/'mouse637-ui-evidence.py'))
        self.assertEqual(current['VEINS_627']['dark'],('#354357',[53,67,87]))

    def test_retained_report_names_and_new_performance_marker_coexist(self):
        owner=runpy.run_path(str(TOOLS/'mouse637-owner-feedback-evidence.py'))
        self.assertEqual(owner['NAME'],'mouse-636-owner-feedback.json')
        self.assertIn('MOUSE_637_PERFORMANCE_PASS',owner['MARKERS'])
        self.assertIn('MOUSE_636_OWNER_FEEDBACK_PASS',owner['MARKERS'])
        retained=runpy.run_path(str(TOOLS/'mouse637-retained-owner-evidence.py'))
        self.assertEqual(retained['NAME'],'mouse-636-retained-owner-feedback.json')
        self.assertEqual(retained['MARKER'],'MOUSE_636_RETAINED_OWNER_FEEDBACK_PASS')

    def test_new637_native_frame_names_are_bounded(self):
        module=runpy.run_path(str(TOOLS/'mouse637-native-evidence.py'))
        def missing(name):raise KeyError(name)
        evidence=module['Evidence'](missing)
        with self.assertRaises(KeyError):evidence.png({'filename':'mouse-637-appearance-restored.png'})
        for name in ['../mouse-637-escape.png','mouse-638-foreign.png','mouse-637-../../escape.png']:
            with self.subTest(name=name),self.assertRaises(ValueError):evidence.png({'filename':name})

    def test_local_templates_are_unready_and_cannot_start_publication(self):
        root=TOOLS.parent
        pins=PLAN['read_plan'](root)
        self.assertEqual(set(pins),{'macos-arm64','windows-x64','linux-x64'})
        # A ready staged candidate must instead pass every exact pin validator.
        if not all(p['ready'] for p in pins.values()):
            self.assertFalse(PLAN['publication_ready']('macos-arm64',root=root))


if __name__=='__main__':unittest.main()
