#!/usr/bin/env python3
"""Fail-closed Mouse627 trace evidence checks; no direct DOM/model ID claim.

The sanitized Chromium trace has no shared identifier between Blink Animation
and compositor KeyframeModel. Derived cc group/property and state transitions
separate compositor generations; group is neither a global nor a DOM identity.
This gate checks their uniqueness and narrow temporal correlation with the
startup and DOM completion facts. Chromium removal need not emit a cc terminal;
missing coverage is reported as unknown, never as an inferred END or deletion.
PASS does not prove continuous compositor execution or the separate native
visual release checks. No saved report is an input.
"""

import argparse
import bisect
import collections
import json
import math
from pathlib import Path
import statistics


ALGORITHM = 'mouse627-motion-trace-evidence-v1'
MAX_TRACE_BYTES = 72 * 1024 * 1024
MAX_MOTION_BYTES = 16 * 1024 * 1024
MAX_EVENTS = 200000
MAX_ANCHOR_SPREAD_MS = 1.0
# This is an evidence-correlation bound, not an animation/performance override.
# A wider separation is inconclusive and must not select an unrelated model.
MAX_FINISH_SKEW_MS = 20.0
PINNED_VERSIONS = {'electron': '44.5.0', 'chrome': '152.0.7977.130'}
STAGES = ('request', 'players-paused', 'prepare-await-ready', 'pause-ready',
          'preparation-frame-1', 'preparation-frame-2', 'play-request',
          'play-pending', 'play-ready', 'complete')
CC_TERMINAL = {'FINISHED', 'ABORTED', 'WAITING_FOR_DELETION'}
CC_STATES = CC_TERMINAL | {'WAITING_FOR_TARGET_AVAILABILITY', 'STARTING',
                         'RUNNING', 'PAUSED', 'PAUSED_EXCLUSIVE',
                         'ABORTED_BUT_NEEDS_COMPLETION'}


class MotionTraceError(ValueError):
    """Missing, rejected, or ambiguous native trace evidence."""


def require(condition, message):
    if not condition:
        raise MotionTraceError(message)


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def whole(value):
    return type(value) is int and value >= 0


def object_(value, label):
    require(isinstance(value, dict), label + ' must be an object')
    return value


def list_(value, label):
    require(isinstance(value, list), label + ' must be an array')
    return value


def identity(event):
    ident = event.get('id2')
    if isinstance(ident, dict) and len(ident) == 1:
        kind, value = next(iter(ident.items()))
        require(kind in ('local', 'global') and
                (isinstance(value, str) or whole(value)), 'Invalid async identity')
        return (kind, value)
    value = event.get('id')
    require(isinstance(value, str) or whole(value), 'Missing async identity')
    return ('id', value)


def quality(trace):
    meta = object_(trace.get('mouseMotionTrace'), 'Trace metadata')
    require(meta.get('schemaVersion') == 1 and
            meta.get('source') == 'Chromium CDP Tracing', 'Unsupported trace schema/source')
    require(meta.get('complete') is True and meta.get('reason') == 'motion-complete',
            'Trace did not finish the complete motion scenario')
    require(meta.get('dataLossOccurred') is False and meta.get('limitedEvents') == 0
            and meta.get('errors') == [], 'Trace data loss, limit, or error')
    versions = object_(meta.get('versions'), 'Trace versions')
    require(all(versions.get(k) == v for k, v in PINNED_VERSIONS.items()),
            'Unreviewed Chromium/Electron trace semantics')
    events = list_(trace.get('traceEvents'), 'Trace events')
    require(0 < len(events) <= MAX_EVENTS and meta.get('eventCount') == len(events),
            'Trace event count mismatch or limit')
    require(whole(meta.get('droppedEvents')) and whole(meta.get('bytes')) and meta['bytes'] > 0,
            'Invalid trace size/sanitization metadata')
    for event in events:
        object_(event, 'Trace event')
        require(isinstance(event.get('name'), str) and isinstance(event.get('ph'), str),
                'Malformed trace event name/phase')
        if 'ts' in event:
            require(number(event['ts']) and event['ts'] >= 0, 'Invalid trace timestamp')
    return meta, sorted(events, key=lambda e: e.get('ts', -1))


def align(events, meta):
    marks = collections.defaultdict(list)
    for event in events:
        if event['name'].startswith('mouse627.motion.') and 'blink.user_timing' in event.get('cat', ''):
            require(event.get('ph') == 'I' and number(event.get('ts')), 'Unexpected renderer mark event')
            start = object_(object_(event.get('args'), 'Mark args').get('data'), 'Mark data').get('startTime')
            require(number(start), 'Renderer mark lacks its performance startTime')
            # The two JSON writers serialize the same double differently
            # (observed: ...000006 versus ...00001). Normalize only sub-ns
            # numeric serialization noise, not distinct performance marks.
            marks[(event.get('pid'), event['name'], round(start, 6))].append(event)
    snapshots = list_(meta.get('snapshots'), 'Trace snapshots')
    require(6 <= len(snapshots) <= 64, 'Insufficient or excessive renderer anchors')
    anchors, labels, used, pids = [], collections.defaultdict(list), set(), set()
    for snapshot in snapshots:
        object_(snapshot, 'Snapshot')
        value = object_(snapshot.get('value'), 'Snapshot value')
        native = object_(value.get('native'), 'Snapshot native state')
        renderer = object_(value.get('renderer'), 'Snapshot renderer state')
        pid, label = native.get('rendererPid'), snapshot.get('label')
        require(whole(pid) and pid > 0 and isinstance(label, str), 'Invalid anchor renderer/label')
        name, start = renderer.get('marker'), renderer.get('markStartTime')
        require(name == 'mouse627.motion.' + label and number(start), 'Inconsistent renderer anchor')
        key = (pid, name, round(start, 6))
        require(key not in used and len(marks.get(key, [])) == 1,
                'Missing, repeated, or ambiguous renderer mark anchor: ' + label)
        used.add(key); pids.add(pid)
        event = marks[key][0]
        anchors.append(event['ts'] / 1000 - start)
        labels[label].append(start)
    require(len(pids) == 1, 'Motion spans multiple renderer processes')
    pid = next(iter(pids))
    require(sum(len(v) for k, v in marks.items() if k[0] == pid) == len(used),
            'Unmatched renderer marks; clock attribution is ambiguous')
    spread = max(anchors) - min(anchors)
    require(spread <= MAX_ANCHOR_SPREAD_MS, 'Renderer/trace clock anchors disagree')
    offset = statistics.median(anchors)
    # performance.now() is quantized independently of trace microseconds.
    margin = max(abs(x - offset) for x in anchors) + 0.2
    for label in ('before', 'after', 'arm-light-closing', 'capture-light-closing',
                  'arm-dark-closing', 'capture-dark-closing'):
        require(len(labels[label]) == 1, 'Missing/ambiguous phase anchor: ' + label)
    require(labels['before'][0] < labels['after'][0], 'Invalid motion trace bounds')
    return pid, offset, margin, labels, len(anchors), spread


def scenario(motion, labels):
    geometry = object_(motion.get('geometry'), 'Motion geometry')
    merged, rows_by_geometry = {}, {}
    for name, value in geometry.items():
        if not isinstance(value, dict) or 'startup' not in value:
            continue
        startup = object_(value['startup'], name + ' startup')
        require(startup.get('enabled') is True, name + ' startup diagnostics are disabled')
        rows = list_(startup.get('events'), name + ' startup events')
        rows_by_geometry[name] = rows
        for row in rows:
            object_(row, 'Startup event')
            require(whole(row.get('generation')) and isinstance(row.get('event'), str)
                    and number(row.get('performanceNow')), 'Malformed motion startup event')
            key = (row['generation'], row['event'], row['performanceNow'])
            require(key not in merged or merged[key] == row, 'Conflicting copies of startup evidence')
            merged[key] = row
    generations = collections.defaultdict(lambda: collections.defaultdict(list))
    for row in merged.values():
        generations[row['generation']][row['event']].append(row)
    fresh = {}
    for generation, by_event in generations.items():
        for request in by_event.get('request', []):
            if (request.get('to') == 0 and request.get('movement') is None and
                    request.get('shade') is None and by_event.get('players-paused') and
                    labels['before'][0] <= request['performanceNow'] <= labels['after'][0]):
                require(generation not in fresh, 'Repeated fresh-close request')
                stages = {}
                for name in STAGES:
                    require(len(by_event.get(name, [])) == 1,
                            f'Fresh close {generation}: missing/repeated {name}')
                    stages[name] = by_event[name][0]
                stages['releaseEvents'] = by_event.get('release', [])
                fresh[generation] = stages
    require(len(fresh) == 3, f'Fresh close scenario incomplete/ambiguous: expected 3, found {len(fresh)}')
    selected = []
    for theme in ('light', 'dark'):
        name = theme + 'Closing'
        lo, hi = labels['arm-' + theme + '-closing'][0], labels['capture-' + theme + '-closing'][0]
        require(lo < hi, 'Invalid closing phase anchors: ' + theme)
        matches = [(g, s) for g, s in fresh.items() if lo < s['request']['performanceNow'] < hi]
        require(len(matches) == 1, 'Closing anchor window is not unique: ' + theme)
        generation, stages = matches[0]
        require(any(row['generation'] == generation and row['event'] == 'request'
                    for row in rows_by_geometry.get(name, [])), 'Phase/generation mismatch: ' + name)
        selected.append((name, generation, stages))
    remaining = [(g, s) for g, s in fresh.items() if g not in {row[1] for row in selected}]
    require(len(remaining) == 1, 'Later fresh-close generation is ambiguous')
    generation, stages = remaining[0]
    interrupted = object_(geometry['interrupted'].get('startup'), 'Interrupted startup')
    current = object_(interrupted.get('current'), 'Interrupted current state')
    require(number(current.get('performanceNow')) and current.get('phase') == 'open',
            'Interrupted scenario did not restore open state')
    require(stages['request']['performanceNow'] > current['performanceNow'] >
            selected[1][2]['complete']['performanceNow'], 'Later close is not after the interruption scenario')
    require(any(row['generation'] == generation and row['event'] == 'request'
                for row in rows_by_geometry.get('reduced', [])), 'Later close absent from final startup diagnostics')
    selected.append(('laterClosing', generation, stages))
    require(selected[0][2]['complete']['performanceNow'] < selected[1][2]['request']['performanceNow'],
            'Light/dark closing scenarios overlap or are reversed')
    return selected


def lifetimes(events, name, pid, tid):
    groups, latest = [], {}
    for event in events:
        if event['name'] != name or event.get('pid') != pid or event.get('tid') != tid:
            continue
        if event.get('ph') not in ('b', 'e', 'n'):
            continue
        key = identity(event)
        require(number(event.get('ts')), 'Async event lacks timestamp')
        if event['ph'] == 'b':
            previous = latest.get(key)
            overlap = previous is not None and previous['end'] is None
            if overlap:
                previous['invalid'] = True
            group = {'id': key, 'begin': event, 'end': None, 'events': [event], 'invalid': overlap}
            groups.append(group); latest[key] = group
        elif key in latest:
            group = latest[key]
            group['events'].append(event)
            if event['ph'] == 'e':
                if group['end'] is not None:
                    group['invalid'] = True
                group['end'] = event
    return groups


def complete_lifetime(group, label):
    require(not group['invalid'] and group['end'] is not None and
            group['begin']['ts'] < group['end']['ts'], 'Incomplete/overlapping ' + label + ' lifetime')


def startup_contract(stages, phase):
    times = [stages[name]['performanceNow'] for name in STAGES]
    require(times == sorted(times) and times[0] < times[-1], phase + ': startup stages out of order')
    request = stages['request']
    require(request.get('to') == 0 and request.get('goal') == 0 and
            request.get('immediate') is False and request.get('phase') == 'open',
            phase + ': not a normal fresh close from open')
    for stage in STAGES[1:7]:
        for player in ('movement', 'shade'):
            state = object_(stages[stage].get(player), phase + ' ' + stage + ' ' + player)
            require(state.get('currentTime') == 300 and state.get('playbackRate') == -1
                    and state.get('playState') == 'paused' and state.get('pending') is False
                    and state.get('startTime') is None, phase + ': fresh direction/endpoint preparation is wrong')
    for player in ('movement', 'shade'):
        pending = object_(stages['play-pending'].get(player), phase + ' pending ' + player)
        require(pending.get('pending') is True and pending.get('playState') == 'running'
                and pending.get('playbackRate') == -1 and pending.get('currentTime') == 300,
                phase + ': missing real pending play')
        ready = object_(stages['play-ready'].get(player), phase + ' ready ' + player)
        require(ready.get('pending') is False and ready.get('playState') == 'running'
                and ready.get('playbackRate') == -1 and number(ready.get('currentTime'))
                and 0 < ready['currentTime'] <= 300 and number(ready.get('startTime')),
                phase + ': player did not become ready during closing')
        finish = object_(stages['complete'].get(player), phase + ' complete ' + player)
        require(finish.get('pending') is False and finish.get('playState') == 'finished'
                and finish.get('playbackRate') == -1 and finish.get('currentTime') == 0,
                phase + ': closing did not finish at the closed endpoint')
    for stage in ('play-ready', 'complete'):
        a, b = stages[stage]['movement'], stages[stage]['shade']
        require(number(a.get('startTime')) and number(b.get('startTime')) and
                abs(a['startTime'] - b['startTime']) <= 0.001,
                phase + ': players have different resolved timelines')
    first, second = stages['preparation-frame-1'], stages['preparation-frame-2']
    require(number(first.get('rafTime')) and number(second.get('rafTime')) and
            first['rafTime'] < second['rafTime'], phase + ': two preparation frames are not demonstrated')


def host_update(events, pid, tid, timestamps, label):
    candidates = [e for e in events if e['name'] == 'AnimationHost::UpdateAnimationState'
                  and e.get('pid') == pid and e.get('tid') == tid and e.get('ph') == 'X'
                  and number(e.get('ts')) and number(e.get('dur')) and e['dur'] >= 0
                  and e['ts'] <= min(timestamps) and e['ts'] + e['dur'] >= max(timestamps)]
    require(len(candidates) == 1, label + ': pair is not in one unambiguous compositor host update')
    event = candidates[0]
    return {'startTraceUs': event['ts'], 'endTraceUs': event['ts'] + event['dur']}


def cc_key(event, transition=False):
    """Read only the sanitizer's bounded structural fields, never infer labels."""
    model = object_(object_(event.get('args'), 'Compositor args').get('ccModel'),
                    'Missing/invalid structural ccModel')
    group, prop = model.get('group'), model.get('targetProperty')
    require(type(group) is int and 0 < group <= 2147483647 and
            type(prop) is int and 0 <= prop <= 11,
            'Invalid compositor group/property')
    if transition:
        require(isinstance(model.get('from'), str) and isinstance(model.get('to'), str) and
                model['from'] in CC_STATES and model['to'] in CC_STATES,
                'Unknown compositor state transition')
    return group, prop


class CompositorEvidence:
    """Index actual pointer segments and all renderer-wide structural chains.

    A new BEGIN with another group/property does not complete its predecessor.
    Chromium uses FromPointer tracks; removal can omit END, then a later model
    can reuse that pointer. The later segment needs its own startup; any END
    must link to its own state. Unobserved terminals need the separate DOM,
    release and frame checks below. Same-key reuse/collision is always rejected.
    """

    def __init__(self, events, pid, main_tid, compositor_tid):
        self.events, self.pid = events, pid
        self.main_tid, self.compositor_tid = main_tid, compositor_tid
        self.models, self.by_key = [], collections.defaultdict(list)
        self.states = collections.defaultdict(lambda: collections.defaultdict(list))
        self.thread_states = collections.defaultdict(list)
        self.boundaries = collections.defaultdict(list)
        latest = {}
        for event in events:
            if event.get('pid') != pid or 'cc' not in event.get('cat', '').split(','):
                continue
            name, phase = event['name'], event['ph']
            if name in ('ElementAnimations::SetRunState', 'KeyframeModel'):
                require(number(event.get('ts')) and whole(event.get('tid')),
                        'Structural compositor event lacks timestamp/thread')
            if name == 'ElementAnimations::SetRunState' and phase == 'I':
                key = cc_key(event, True)
                self.states[key][event.get('tid')].append(event)
                self.thread_states[event.get('tid')].append(event)
            elif name == 'KeyframeModel' and phase in ('b', 'e'):
                ident = identity(event)
                self.boundaries[event.get('tid')].append(event)
                if phase == 'b':
                    key = cc_key(event)
                    previous = latest.get(ident)
                    group = {'id': ident, 'key': key, 'begin': event, 'end': None,
                             'invalid': False, 'priorIncomplete': None, 'nextBegin': None}
                    if previous is not None:
                        previous['nextBegin'] = event
                    if previous is not None and previous['end'] is None:
                        group['priorIncomplete'] = previous
                        if previous['key'] == key or previous['begin']['ts'] >= event['ts']:
                            previous['invalid'] = group['invalid'] = True
                    self.models.append(group); self.by_key[key].append(group)
                    latest[ident] = group
                elif ident in latest:
                    group = latest[ident]
                    if group['end'] is not None:
                        group['invalid'] = True
                    group['end'] = event
        self.state_times = {tid: [e['ts'] for e in rows]
                            for tid, rows in self.thread_states.items()}
        self.boundary_times = {tid: [e['ts'] for e in rows]
                               for tid, rows in self.boundaries.items()}

    def boundary_state(self, boundary, key, expected, label):
        # SetRunState emits async BEGIN/END before its instant state event.
        # JSON exports async events separately, so equal timestamp ordering in
        # the JSON array is not meaningful. There must be exactly one next
        # structural state, with no intervening or simultaneous other boundary.
        tid, at = boundary.get('tid'), boundary['ts']
        rows, times = self.thread_states.get(tid, []), self.state_times.get(tid, [])
        index = bisect.bisect_left(times, at)
        require(index < len(rows), label + ': boundary lacks following structural state')
        end = bisect.bisect_right(times, times[index])
        require(end == index + 1, label + ': boundary state is ambiguous at trace precision')
        state = rows[index]
        require(cc_key(state, True) == key and
                (state['args']['ccModel']['from'], state['args']['ccModel']['to']) == expected,
                label + ': boundary/state key or transition mismatch')
        boundaries, stamps = self.boundaries[tid], self.boundary_times[tid]
        first, last = bisect.bisect_left(stamps, at), bisect.bisect_right(stamps, state['ts'])
        require(all(other is boundary for other in boundaries[first:last]),
                label + ': intervening/ambiguous compositor boundary')
        return state

    def chain(self, group, label):
        key = group['key']
        require(key[0] > 1, label + ': reserved/reused compositor group is not attributable')
        require(len(self.by_key[key]) == 1,
                label + ': compositor structural key collision/reuse in full trace')
        require(not group['invalid'], label + ': overlapping compositor structural segment')
        require(group['begin'].get('tid') == self.compositor_tid and
                (group['end'] is None or group['end'].get('tid') == self.compositor_tid),
                label + ': model lifetime has unknown thread provenance')
        if group['end'] is not None:
            require(group['begin']['ts'] < group['end']['ts'], label + ': invalid compositor END order')
        by_thread = self.states[key]
        require(set(by_thread) == {self.main_tid, self.compositor_tid},
                label + ': missing/unknown main or impl state provenance')
        chains = {}
        for role, tid in (('main', self.main_tid), ('impl', self.compositor_tid)):
            rows = by_thread[tid]
            pairs = [(e['args']['ccModel']['from'], e['args']['ccModel']['to']) for e in rows]
            require(len(rows) >= 2 and pairs[:2] == [
                ('WAITING_FOR_TARGET_AVAILABILITY', 'STARTING'), ('STARTING', 'RUNNING')],
                label + ': missing/conflicting ' + role + ' origin/start chain')
            terminal = rows[2] if len(rows) > 2 else None
            if terminal is not None:
                require(pairs[2][0] == 'RUNNING' and pairs[2][1] in CC_TERMINAL,
                        label + ': unknown/active interruption in ' + role + ' chain')
            remaining = list(rows[3:])
            state = pairs[2][1] if terminal is not None else 'RUNNING'
            if remaining and (remaining[0]['args']['ccModel']['from'],
                              remaining[0]['args']['ccModel']['to']) == (state, 'WAITING_FOR_DELETION'):
                require(state != 'WAITING_FOR_DELETION', label + ': repeated terminal transition')
                remaining.pop(0)
            chains[role] = {'origin': rows[0], 'running': rows[1], 'terminal': terminal,
                            'events': rows, 'remaining': remaining}
        # PushPropertiesTo can emit the main ABORTED->DELETION transition on
        # the impl thread immediately after changing the controlling instance.
        main, impl = chains['main'], chains['impl']
        require(not main['remaining'], label + ': conflicting main lifecycle')
        bridge = impl['remaining']
        if bridge:
            require(len(bridge) == 1 and len(main['events']) == 3 and
                    main['terminal'] is not None and impl['terminal'] is not None and
                    main['terminal']['args']['ccModel']['to'] == 'ABORTED' and
                    impl['terminal']['args']['ccModel']['to'] in ('ABORTED', 'WAITING_FOR_DELETION') and
                    bridge[0]['args']['ccModel']['from'] == 'ABORTED' and
                    bridge[0]['args']['ccModel']['to'] == 'WAITING_FOR_DELETION' and
                    main['terminal']['ts'] <= bridge[0]['ts'],
                    label + ': conflicting impl lifecycle or cleanup provenance')
        require(main['terminal'] is None or main['terminal']['args']['ccModel']['to'] in ('FINISHED', 'ABORTED'),
                label + ': unknown main terminal provenance')
        require(main['origin']['ts'] < main['running']['ts'] and
                (main['terminal'] is None or main['running']['ts'] < main['terminal']['ts']) and
                impl['origin']['ts'] < group['begin']['ts'] <= impl['running']['ts'] and
                (group['end'] is None or impl['running']['ts'] < group['end']['ts']),
                label + ': structural lifecycle order is inconsistent')
        require(self.boundary_state(group['begin'], key, ('STARTING', 'RUNNING'), label + ' start')
                is impl['running'], label + ': start state belongs to another chain')
        # SetRunState on a controlling instance emits END and terminal together.
        # Conversely, removal/destruction can emit neither. One without the
        # other is contradictory evidence, never an allowed missing terminal.
        require((group['end'] is None) == (impl['terminal'] is None),
                label + ': async END/impl terminal coverage is inconsistent')
        if impl['terminal'] is not None:
            terminal = impl['terminal']['args']['ccModel']
            require(self.boundary_state(group['end'], key, (terminal['from'], terminal['to']), label + ' end')
                    is impl['terminal'], label + ': terminal state belongs to another chain')
        return chains

    def select(self, lo, hi, label):
        candidates = [g for g in self.models if lo <= g['begin']['ts'] <= hi]
        by_group = collections.defaultdict(list)
        for group in candidates:
            by_group[group['key'][0]].append(group)
        pairs = [rows for rows in by_group.values() if len(rows) == 2 and
                 {g['key'][1] for g in rows} == {0, 4}]
        require(len(pairs) == 1,
                label + ': fresh compositor candidates missing/ambiguous; expected one structural pair')
        selected = pairs[0]
        chains = {g['key']: self.chain(g, label) for g in selected}
        excluded = []
        for group in candidates:
            if group in selected:
                continue
            require(len(by_group[group['key'][0]]) == 1,
                    label + ': competing compositor group is not an attributable singleton')
            chain = self.chain(group, label + ' extra model')
            require(chain['impl']['origin']['ts'] < lo,
                    label + ': extra compositor model has new/unknown origin')
            excluded.append((group, chain))
        # An unaccounted fresh origin on either thread is ambiguous. Main can
        # start after play for an impl model that already started before play;
        # that exception needs its own unique, consistent preexisting startup.
        known = {g['key'] for g in candidates}
        explained_preexisting = []
        for key, by_thread in self.states.items():
            origins = [event for tid in (self.main_tid, self.compositor_tid)
                       for event in by_thread.get(tid, []) if lo <= event['ts'] <= hi and
                       event['args']['ccModel']['from'] == 'WAITING_FOR_TARGET_AVAILABILITY']
            if not origins or key in known:
                continue
            models = self.by_key.get(key, [])
            require(len(models) == 1 and models[0]['begin']['ts'] < lo,
                    label + ': unaccounted main/impl origin without attributable preexisting model')
            model = models[0]
            chain = self.chain(model, label + ' preexisting origin')
            require(chain['impl']['origin']['ts'] < lo,
                    label + ': preexisting model has unknown/new impl origin')
            known.add(key); explained_preexisting.append((model, chain))
        return selected, chains, excluded, explained_preexisting


def verify_trace_data(trace_doc, motion_doc, diagnostics_doc=None):
    trace = object_(trace_doc, 'Trace'); motion = object_(motion_doc, 'Motion facts')
    geometry = object_(motion.get('geometry'), 'Motion geometry')
    missing = [name for name in ('lightClosing', 'darkClosing', 'interrupted', 'reduced')
               if not isinstance(geometry.get(name), dict)]
    require(not missing, 'Fresh close scenario incomplete: missing ' + ', '.join(missing))
    require(motion.get('version') == '6.0.27' and motion.get('themes') == ['light', 'dark'],
            'Motion version/themes mismatch')
    if diagnostics_doc is not None:
        diagnostics = object_(diagnostics_doc, 'Motion diagnostics')
        require(diagnostics.get('version') == '6.0.27' and
                all(diagnostics.get(k) == motion.get(k) for k in ('frames', 'geometry')),
                'Motion facts and independently retained diagnostics disagree')
    meta, events = quality(trace)
    summary = object_(motion.get('trace'), 'Motion trace summary')
    require(summary.get('file') == 'mouse-627-motion-trace.json' and
            all(summary.get(k) == meta.get(k) for k in
                ('complete', 'reason', 'eventCount', 'bytes', 'dataLossOccurred', 'errors')),
            'Motion facts refer to different/incomplete trace metadata')
    pid, offset, margin, labels, anchor_count, spread = align(events, meta)
    phases = scenario(motion, labels)
    thread_names = collections.defaultdict(set)
    for event in events:
        if event['name'] == 'thread_name' and event.get('pid') == pid:
            thread_names[event.get('tid')].add(object_(event.get('args'), 'Thread metadata').get('name'))
    def thread(name):
        matches = [tid for tid, names in thread_names.items() if names == {name}]
        require(len(matches) == 1 and whole(matches[0]), 'Missing/ambiguous renderer thread: ' + name)
        return matches[0]
    main_tid, compositor_tid = thread('CrRendererMain'), thread('Compositor')
    blink = lifetimes(events, 'Animation', pid, main_tid)
    compositor = None
    to_trace = lambda value: (value + offset) * 1000
    margin_us = margin * 1000
    results, node_pair = [], None
    for phase, generation, stages in phases:
        play, pending, ready, finish = [stages[key]['performanceNow'] for key in
                                        ('play-request', 'play-pending', 'play-ready', 'complete')]
        start_lo, start_hi = to_trace(play) - margin_us, to_trace(pending) + margin_us
        paired = [g for g in blink if start_lo <= g['begin']['ts'] <= start_hi]
        require(len(paired) == 2, phase + ': Blink start window is missing/ambiguous; expected exactly two lifetimes')
        nodes = []
        for group in paired:
            complete_lifetime(group, phase + ' Blink')
            data = object_(object_(group['begin'].get('args'), 'Animation args').get('data'), 'Animation data')
            require(whole(data.get('nodeId')) and data['nodeId'] > 0 and data.get('state') == 'running',
                    phase + ': missing Blink target identity/running state')
            require(object_(group['begin']['args'].get('endData'), 'Blink end data').get('state') == 'finished',
                    phase + ': Blink target did not record finished state')
            nodes.append(data['nodeId'])
            for event in group['events']:
                if not group['begin']['ts'] <= event['ts'] <= group['end']['ts']:
                    continue
                args = object_(event.get('args', {}), 'Animation event args')
                value = object_(args.get('data', {}), 'Animation event data')
                if 'compositeFailed' in value:
                    code = value['compositeFailed']
                    require(whole(code), phase + ': invalid compositor rejection bitmask')
                    require(code == 0, f'{phase}: active-phase compositor rejection compositeFailed={code}')
                require(not value.get('unsupportedProperties'), phase + ': unsupported animated properties')
            require(group['end']['ts'] <= to_trace(finish) + margin_us,
                    phase + ': Blink lifetime extends past completion')
        require(len(set(nodes)) == 2, phase + ': two distinct Blink targets were not observed')
        if node_pair is None:
            node_pair = set(nodes)
        require(set(nodes) == node_pair, phase + ': Blink target pair changed between fresh closes')
        startup_contract(stages, phase)
        if compositor is None:
            compositor = CompositorEvidence(events, pid, main_tid, compositor_tid)
        # Selection uses structural group membership, never nearest completion.
        # Every extra fresh model needs its own provable pre-play origin.
        active_models, chains, excluded, explained_preexisting = compositor.select(
            start_lo, to_trace(finish) + margin_us, phase)
        require(len({g['id'] for g in active_models}) == 2, phase + ': compositor pair reuses one identity')
        model_lo, model_hi = max(g['begin']['ts'] for g in paired), to_trace(ready) + margin_us
        blink_ends = [g['end']['ts'] for g in paired]
        # For non-FINISHED terminals, even the latest clock-aligned complete
        # timestamp must have passed, as must both actual Blink ends. The
        # startup contract above independently requires both DOM players to be
        # finished/currentTime=0. No cancel causality is inferred from timing.
        post_endpoint = max(max(blink_ends), to_trace(finish) + margin_us)
        for group in active_models:
            chain = chains[group['key']]
            require(model_lo <= group['begin']['ts'] <= model_hi,
                    phase + ': compositor start is outside the fresh-play/ready interval')
            require(chain['impl']['origin']['ts'] >= start_lo and
                    start_lo <= chain['main']['origin']['ts'] <= chain['main']['running']['ts'] <=
                    to_trace(finish) + margin_us,
                    phase + ': selected model does not have fresh main/impl origins')
            if group['end'] is not None:
                require(all(abs(group['end']['ts'] - end) <= MAX_FINISH_SKEW_MS * 1000
                            for end in blink_ends), phase + ': compositor/Blink completions disagree')
            elif group['nextBegin'] is not None:
                require(group['nextBegin']['ts'] >= post_endpoint,
                        phase + ': missing-END pointer is reused before both DOM endpoints')
            for role in ('main', 'impl'):
                terminal = chain[role]['terminal']
                if terminal is None:
                    continue
                # Pinned ProxyMain updates main cc lifecycle state after Blink
                # BeginMainFrame work. Main FINISHED is bookkeeping, not a
                # visual-completion timestamp; impl and main abort bounds stay.
                if role != 'main' or terminal['args']['ccModel']['to'] != 'FINISHED':
                    require(all(abs(terminal['ts'] - end) <= MAX_FINISH_SKEW_MS * 1000
                                for end in blink_ends), phase + ': state/Blink completions disagree')
                if terminal['args']['ccModel']['to'] != 'FINISHED':
                    require(terminal['ts'] >= post_endpoint and
                            (role != 'impl' or group['end']['ts'] >= post_endpoint),
                            phase + ': active-phase abort/deletion before both recorded DOM endpoints')
        require(max(g['begin']['ts'] for g in active_models) < min(
            blink_ends + [g['end']['ts'] for g in active_models if g['end'] is not None]),
            phase + ': compositor starts do not overlap before the observed endpoints')
        coverage = None
        if any(g['end'] is None for g in active_models):
            releases = stages['releaseEvents']
            require(len(releases) == 1, phase + ': unknown terminal lacks unique controller release')
            release = releases[0]
            require(release.get('phase') == 'closed' and release.get('goal') == 0 and
                    release.get('preparing') is False and release.get('movement') is None and
                    release.get('shade') is None and finish <= release['performanceNow'] < labels['after'][0],
                    phase + ': unknown terminal lacks release after both DOM endpoints')
            coverage_lo = max(post_endpoint, to_trace(release['performanceNow']) + margin_us)
            coverage_hi = to_trace(labels['after'][0]) + margin_us
            post_frames = {}
            for name in ('BeginFrame', 'Scheduler::BeginImplFrame', 'LayerTreeHostImpl::PrepareToDraw'):
                rows = [e for e in events if e.get('pid') == pid and e.get('tid') == compositor_tid and
                        e['name'] == name and coverage_lo < e.get('ts', -1) <= coverage_hi]
                post_frames[name] = {'count': len(rows),
                                     'firstTraceUs': rows[0]['ts'] if rows else None,
                                     'lastTraceUs': rows[-1]['ts'] if rows else None}
            require(post_frames['Scheduler::BeginImplFrame']['count'] > 0 and
                    post_frames['LayerTreeHostImpl::PrepareToDraw']['count'] > 0,
                    phase + ': unknown terminal lacks subsequent compositor/frame coverage')
            coverage = {'releaseRendererMs': release['performanceNow'],
                        'releaseGeneration': release['generation'], 'playersNull': True,
                        'afterBothDomEndpoints': True, 'traceWindowUs': [coverage_lo, coverage_hi],
                        'frames': post_frames, 'removalObserved': False}
        begin_update = host_update(events, pid, compositor_tid,
                                   [value for g in active_models for value in
                                    (g['begin']['ts'], chains[g['key']]['impl']['running']['ts'])],
                                   phase + ' start')
        finished_terminals = all(chains[g['key']]['impl']['terminal'] is not None and
                                 chains[g['key']]['impl']['terminal']['args']['ccModel']['to'] == 'FINISHED'
                                 for g in active_models)
        # PushPropertiesTo cleanup need not occur inside an AnimationHost
        # update. Its exact boundary/state linkage is still mandatory above.
        end_update = host_update(events, pid, compositor_tid,
                                 [value for g in active_models for value in
                                  (g['end']['ts'], chains[g['key']]['impl']['terminal']['ts'])],
                                 phase + ' finish') if finished_terminals else None
        summarize = lambda g: {'identity': {g['id'][0]: g['id'][1]},
                               'startTraceUs': g['begin']['ts'],
                               'endTraceUs': g['end']['ts'] if g['end'] is not None else None}
        def structural(group, chain):
            return {**summarize(group), 'group': group['key'][0], 'targetProperty': group['key'][1],
                    'mainOriginTraceUs': chain['main']['origin']['ts'],
                    'implOriginTraceUs': chain['impl']['origin']['ts'],
                    'observedTerminalStates': {role: chain[role]['terminal']['args']['ccModel']['to']
                                               if chain[role]['terminal'] is not None else None
                                               for role in ('main', 'impl')},
                    'terminalObservation': 'observed' if group['end'] is not None else 'not-observed',
                    'removalObserved': False, 'continuousCompositorLifetimeProven': False,
                    'quietRemovalSupportedByPinnedSource': True,
                    'nextPointerBegin': {'traceUs': group['nextBegin']['ts'],
                                         'group': cc_key(group['nextBegin'])[0],
                                         'targetProperty': cc_key(group['nextBegin'])[1]}
                                        if group['nextBegin'] is not None else None,
                    'stateChains': {role: [{'traceUs': e['ts'], 'threadId': e['tid'],
                                           'from': e['args']['ccModel']['from'],
                                           'to': e['args']['ccModel']['to']} for e in chain[role]['events']]
                                    for role in ('main', 'impl')},
                    'postCompletionTerminal': any(chain[role]['terminal'] is not None and
                                                  chain[role]['terminal']['args']['ccModel']['to'] != 'FINISHED'
                                                  for role in ('main', 'impl'))}
        prior = []
        for group in active_models:
            old = group['priorIncomplete']
            while old is not None:
                prior.append({'identity': {old['id'][0]: old['id'][1]}, 'group': old['key'][0],
                              'targetProperty': old['key'][1], 'startTraceUs': old['begin']['ts'],
                              'endTraceUs': None, 'status': 'incomplete; different structural generation'})
                old = old['priorIncomplete']
        results.append({'phase': phase, 'generation': generation, 'nodeIds': sorted(nodes),
                        'blinkLifetimes': [dict(summarize(g), nodeId=n) for g, n in zip(paired, nodes)],
                        'compositorLifetimes': [structural(g, chains[g['key']]) for g in active_models],
                        'excludedFreshSingletons': [dict(structural(g, chain),
                            reason='unique structural impl origin precedes fresh play') for g, chain in excluded],
                        'explainedPreexistingOrigins': [dict(structural(g, chain),
                            reason='unique consistent impl startup began before play; main origin may follow')
                            for g, chain in explained_preexisting],
                        'priorIncompletePointerSegments': prior,
                        'blinkStartWindowTraceUs': [start_lo, start_hi],
                        'compositorStartWindowTraceUs': [model_lo, model_hi],
                        'completionRendererMs': finish, 'startHostUpdate': begin_update,
                        'finishHostUpdate': end_update, 'activePhaseRejections': 0,
                        'postEndpointThresholdTraceUs': post_endpoint,
                        'postCompletionCoverage': coverage,
                        'excludedPreexistingModels': sum(g['begin']['ts'] < start_lo and
                            (g['end'] is None or g['end']['ts'] >= start_lo) for g in compositor.models)})
    return {'algorithm': ALGORITHM, 'status': 'pass', 'directIdentityLink': False,
            'attribution': 'temporal-correlation',
            'meaning': 'All three unique compositor startup, eligibility, temporal-correlation and recorded DOM '
                       'completion checks passed. Missing compositor terminals remain unobserved; this does not '
                       'prove a shared DOM/model identity, removal, natural compositor finish or continuous '
                       'compositor execution, and does not replace the native visual gates.',
            'acceptanceScope': 'unique-compositor-starts-and-dom-completion',
            'nativeVisualGateRequired': True, 'continuousCompositorLifetimeProven': False,
            'structuralEvidence': 'ccModel group/property and bounded SetRunState enums; renderer-wide key uniqueness',
            'traceSchemaVersion': meta['schemaVersion'], 'versions': meta['versions'],
            'rendererPid': pid, 'rendererMainTid': main_tid, 'compositorTid': compositor_tid,
            'clock': {'offsetMs': offset, 'anchorCount': anchor_count, 'anchorSpreadMs': spread,
                      'correlationMarginMs': margin, 'nativeCallbackClockUsed': False},
            'maxCompletionSkewMs': MAX_FINISH_SKEW_MS, 'eventCount': len(events),
            'mainFinishedTimestampMeaning': 'Main FINISHED records cc lifecycle bookkeeping, not visual completion; '
                                            'maxCompletionSkewMs does not apply to that timestamp.',
            'freshCloses': results}


def _read(path, limit):
    path = Path(path)
    try:
        require(path.is_file() and 0 < path.stat().st_size <= limit,
                'Missing, empty, or oversized trace evidence: ' + path.name)
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MotionTraceError('Cannot read trace evidence: ' + path.name) from error


def verify_trace(trace_path, motion_path, diagnostics_path=None):
    return verify_trace_data(_read(trace_path, MAX_TRACE_BYTES), _read(motion_path, MAX_MOTION_BYTES),
                             _read(diagnostics_path, MAX_MOTION_BYTES) if diagnostics_path else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace')
    parser.add_argument('motion')
    parser.add_argument('--diagnostics')
    args = parser.parse_args()
    try:
        print(json.dumps(verify_trace(args.trace, args.motion, args.diagnostics), ensure_ascii=False, indent=2))
    except MotionTraceError as error:
        parser.exit(1, 'Mouse627 trace rejected: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
