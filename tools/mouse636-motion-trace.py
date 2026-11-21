#!/usr/bin/env python3
"""636 trace compatibility for one pinned Chromium activation finish path.

The byte-frozen 628 checker still decides startup, selected model identities,
group/property uniqueness, every state chain, DOM endpoints, timing bounds and
unknown-terminal coverage. Only its FINISHED host-operation lookup is extended.
No input event, timestamp or receipt is changed; saved reports are not inputs.

Pinned Chromium 152.0.7977.130 implements ActivateSyncTree -> ActivateAnimations
-> ActivateKeyframeModels + UpdateState(false). The latter may mark models
FINISHED when they no longer affect either active or pending elements. This is
an observed lifecycle operation, not proof of natural compositor completion.
"""

import argparse
import hashlib
import json
from pathlib import Path
import runpy
from types import FunctionType


ALGORITHM = 'mouse636-motion-trace-evidence-v1'
BASE_SHA256 = '76715b9ff5951e92bae4771da644341d3de988edce24dab0f6a4eb73aa7720a9'
CHROMIUM_VERSION = '152.0.7977.130'
SOURCE_URLS = [
    'https://github.com/chromium/chromium/blob/152.0.7977.130/cc/animation/animation_host.cc',
    'https://github.com/chromium/chromium/blob/152.0.7977.130/cc/animation/keyframe_effect.cc',
    'https://github.com/chromium/chromium/blob/152.0.7977.130/cc/trees/layer_tree_host_impl.cc',
]
UPDATE = 'AnimationHost::UpdateAnimationState'
ACTIVATE = 'AnimationHost::ActivateAnimations'
PARENT = 'LayerTreeHostImpl::ActivateSyncTree'
_path = Path(__file__).with_name('mouse628-motion-trace.py')
if hashlib.sha256(_path.read_bytes()).hexdigest() != BASE_SHA256:
    raise ValueError('Immutable 628 motion trace validator changed')
_base = runpy.run_path(str(_path))
MotionTraceError = _base['MotionTraceError']
require, number = _base['require'], _base['number']


def _covering(events, name, pid, tid, timestamps, *, category=False):
    return [event for event in events
            if event['name'] == name and event.get('pid') == pid and event.get('tid') == tid
            and event.get('ph') == 'X' and number(event.get('ts'))
            and number(event.get('dur')) and event['dur'] >= 0
            and (not category or 'cc' in event.get('cat', '').split(','))
            and event['ts'] <= min(timestamps)
            and event['ts'] + event['dur'] >= max(timestamps)]


def _host_update(events, pid, tid, timestamps, label):
    # Starting inside ActivateAnimations is not an accepted substitute for
    # either original startup boundary or the unique UpdateAnimationState.
    if not label.endswith(' finish'):
        return _base['host_update'](events, pid, tid, timestamps, label)
    updates = _covering(events, UPDATE, pid, tid, timestamps)
    activations = _covering(events, ACTIVATE, pid, tid, timestamps, category=True)
    if updates:
        require(not activations, label + ': competing update and activation finish hosts')
        return dict(_base['host_update'](events, pid, tid, timestamps, label), operation=UPDATE)
    require(len(activations) == 1, label + ': pair lacks one unambiguous activation finish host')
    activation = activations[0]
    require(activation['dur'] > 0, label + ': empty activation finish operation')
    parent_bounds = [activation['ts'], activation['ts'] + activation['dur']]
    parents = _covering(events, PARENT, pid, tid, parent_bounds, category=True)
    require(len(parents) == 1 and parents[0]['dur'] > 0,
            label + ': activation lacks one enclosing ActivateSyncTree operation')
    parent = parents[0]
    pipeline = parent.get('args', {}).get('main_frame_pipeline', {})
    require(isinstance(pipeline, dict) and pipeline.get('step') == 'ACTIVATE'
            and type(pipeline.get('main_frame_id')) is int and pipeline['main_frame_id'] > 0,
            label + ': enclosing operation lacks its real ACTIVATE main-frame provenance')

    # Rebind the exact two END/FINISHED pairs supplied by the frozen caller to
    # the raw pointer segments and complete main/impl chains. No nearest event
    # selection, inferred END, group relabelling or cross-thread pair is used.
    require(len(timestamps) == 4, label + ': two exact END/FINISHED pairs required')
    mains = {event.get('tid') for event in events
             if event['name'] == 'thread_name' and event.get('pid') == pid
             and event.get('args', {}).get('name') == 'CrRendererMain'}
    require(len(mains) == 1 and tid not in mains, label + ': renderer thread provenance differs')
    index = _base['CompositorEvidence'](events, pid, next(iter(mains)), tid)
    selected, bindings = [], []
    for end_ts, finished_ts in zip(timestamps[::2], timestamps[1::2]):
        matches = [model for model in index.models if model['end'] is not None
                   and model['end']['ts'] == end_ts and model['end'].get('tid') == tid]
        require(len(matches) == 1, label + ': ambiguous exact activation END binding')
        model = matches[0]
        chain = index.chain(model, label + ' activation model')
        terminal = chain['impl']['terminal']
        require(terminal is not None and terminal['ts'] == finished_ts
                and terminal.get('pid') == pid and terminal.get('tid') == tid
                and terminal['args']['ccModel']['from'] == 'RUNNING'
                and terminal['args']['ccModel']['to'] == 'FINISHED',
                label + ': activation END does not bind its exact RUNNING-to-FINISHED event')
        selected.append(model)
        bindings.append({'identity': {model['id'][0]: model['id'][1]},
                         'group': model['key'][0], 'targetProperty': model['key'][1],
                         'endTraceUs': end_ts, 'finishedTraceUs': finished_ts})
    require(len({model['id'] for model in selected}) == 2
            and len({model['key'][0] for model in selected}) == 1
            and {model['key'][1] for model in selected} == {0, 4},
            label + ': activation must finish one exact transform/opacity group')
    return {'operation': ACTIVATE, 'startTraceUs': activation['ts'],
            'endTraceUs': activation['ts'] + activation['dur'],
            'rendererPid': pid, 'compositorTid': tid,
            'parent': {'operation': PARENT, 'startTraceUs': parent['ts'],
                       'endTraceUs': parent['ts'] + parent['dur'],
                       'mainFrameId': pipeline['main_frame_id'], 'step': pipeline['step']},
            'terminalBindings': bindings, 'naturalCompositorFinishProven': False}


_original = _base['verify_trace_data']
_checked = FunctionType(_original.__code__,
                        dict(_original.__globals__, host_update=_host_update, ALGORITHM=ALGORITHM),
                        _original.__name__, _original.__defaults__, _original.__closure__)
_checked.__kwdefaults__ = _original.__kwdefaults__


def verify_trace_data(trace, motion, diagnostics_doc=None):
    report = _checked(trace, motion, diagnostics_doc)
    report['compatibility'] = {
        'algorithm': ALGORITHM, 'baseAlgorithm': _base['ALGORITHM'],
        'baseValidatorSHA256': BASE_SHA256, 'chromiumVersion': CHROMIUM_VERSION,
        'sourceURLs': list(SOURCE_URLS), 'rawInputsRewritten': False,
        'activationFinishCount': sum(
            (row['finishHostUpdate'] or {}).get('operation') == ACTIVATE
            for row in report['freshCloses']),
        'meaning': 'A uniquely bound activation lifecycle finish is accepted in addition to '
                   'the original host update. Natural compositor finish remains unproven.'}
    return report


def verify_trace(trace_path, motion_path, diagnostics_path=None):
    return verify_trace_data(_base['_read'](trace_path, _base['MAX_TRACE_BYTES']),
                             _base['_read'](motion_path, _base['MAX_MOTION_BYTES']),
                             _base['_read'](diagnostics_path, _base['MAX_MOTION_BYTES'])
                             if diagnostics_path else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace')
    parser.add_argument('motion')
    parser.add_argument('--diagnostics')
    args = parser.parse_args()
    try:
        print(json.dumps(verify_trace(args.trace, args.motion, args.diagnostics),
                         ensure_ascii=False, indent=2, allow_nan=False))
    except MotionTraceError as error:
        parser.exit(1, 'Mouse636 trace rejected: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
