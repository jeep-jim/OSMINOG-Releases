#!/usr/bin/env python3
"""Offline trace evidence contracts; positive trace below is explicitly synthetic.

It preserves observed 23e5 startup and 8de5 structural event schemas, repeated
across the three required scenarios. It is not native proof. Separate exact
8de5/fd27 structural excerpts check pointer reuse, origins and terminal coverage.
"""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location('mouse627_motion_trace', Path(__file__).with_name('mouse627-motion-trace.py'))
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)

# Actual 23e57 run 44350041162 attempt 2, generation 16 startup rows.
# Copied from its verified diagnostics; that run FAILED the visual gate.
# This fixture checks native field compatibility only, not release success.
OBSERVED_LIGHT_CLOSE = json.loads('''[{"event":"request","performanceNow":19838.099999999977,"documentTime":19820.5,"generation":16,"goal":0,"preparing":false,"phase":"open","movement":null,"shade":null,"to":0,"immediate":false},{"event":"players-paused","performanceNow":19838.599999999977,"documentTime":19820.5,"generation":16,"goal":0,"preparing":false,"phase":"open","movement":{"currentTime":300,"startTime":null,"pending":false,"playState":"paused","playbackRate":-1},"shade":{"currentTime":300,"startTime":null,"pending":false,"playState":"paused","playbackRate":-1}},{"event":"prepare-await-ready","performanceNow":19838.79999999999,"documentTime":19820.5,"generation":16,"goal":0,"preparing":true,"phase":"closing","movement":{"currentTime":300,"startTime":null,"pending":false,"playState":"paused","playbackRate":-1},"shade":{"currentTime":300,"startTime":null,"pending":false,"playState":"paused","playbackRate":-1},"to":0},{"event":"pause-ready","performanceNow":19838.79999999999,"documentTime":19820.5,"generation":16,"goal":0,"preparing":true,"phase":"closing","movement":{"currentTime":300,"startTime":null,"pending":false,"playState":"paused","playbackRate":-1},"shade":{"currentTime":300,"startTime":null,"pending":false,"playState":"paused","playbackRate":-1},"to":0},{"event":"preparation-frame-1","performanceNow":19843,"documentTime":19838.1,"generation":16,"goal":0,"preparing":true,"phase":"closing","movement":{"currentTime":300,"startTime":null,"pending":false,"playState":"paused","playbackRate":-1},"shade":{"currentTime":300,"startTime":null,"pending":false,"playState":"paused","playbackRate":-1},"rafTime":19838.1,"to":0},{"event":"preparation-frame-2","performanceNow":19859.79999999999,"documentTime":19852.7,"generation":16,"goal":0,"preparing":true,"phase":"closing","movement":{"currentTime":300,"startTime":null,"pending":false,"playState":"paused","playbackRate":-1},"shade":{"currentTime":300,"startTime":null,"pending":false,"playState":"paused","playbackRate":-1},"rafTime":19852.7,"to":0},{"event":"play-request","performanceNow":19859.79999999999,"documentTime":19852.7,"generation":16,"goal":0,"preparing":false,"phase":"closing","movement":{"currentTime":300,"startTime":null,"pending":false,"playState":"paused","playbackRate":-1},"shade":{"currentTime":300,"startTime":null,"pending":false,"playState":"paused","playbackRate":-1},"to":0},{"event":"play-pending","performanceNow":19859.899999999965,"documentTime":19852.7,"generation":16,"goal":0,"preparing":false,"phase":"closing","movement":{"currentTime":300,"startTime":null,"pending":true,"playState":"running","playbackRate":-1},"shade":{"currentTime":300,"startTime":null,"pending":true,"playState":"running","playbackRate":-1}},{"event":"play-ready","performanceNow":19896.199999999953,"documentTime":19887.1,"generation":16,"goal":0,"preparing":false,"phase":"closing","movement":{"currentTime":265.63100000000617,"startTime":20152.731000000007,"pending":false,"playState":"running","playbackRate":-1},"shade":{"currentTime":265.63100000000617,"startTime":20152.731000000007,"pending":false,"playState":"running","playbackRate":-1}},{"event":"complete","performanceNow":20194.79999999999,"documentTime":20187.5,"generation":16,"goal":0,"preparing":false,"phase":"closing","movement":{"currentTime":0,"startTime":20152.731000000007,"pending":false,"playState":"finished","playbackRate":-1},"shade":{"currentTime":0,"startTime":20152.731000000007,"pending":false,"playState":"finished","playbackRate":-1},"to":0}]''')



def sync_counts(trace, motion):
    meta = trace['mouseMotionTrace']
    meta['eventCount'] = len(trace['traceEvents'])
    motion['trace'] = {'file': 'mouse-627-motion-trace.json', **{k: copy.deepcopy(meta[k]) for k in
        ('complete', 'reason', 'eventCount', 'bytes', 'dataLossOccurred', 'errors')}}


def observed_schema_fixture():
    """Synthetic positive fixture, with realistic reused IDs and an earlier hover."""
    pid, main, compositor, offset = 42, 101, 102, 200000
    trace = {'traceEvents': [], 'mouseMotionTrace': {
        'schemaVersion': 1, 'source': 'Chromium CDP Tracing', 'reason': 'motion-complete',
        'complete': True, 'dataLossOccurred': False, 'limitedEvents': 0, 'droppedEvents': 12,
        'bytes': 100000, 'errors': [], 'versions': {'electron': '44.5.0', 'chrome': '152.0.7977.130', 'node': '24.21.0'},
        'snapshots': []}}
    events = trace['traceEvents']
    events.extend({'name': 'thread_name', 'ph': 'M', 'pid': pid, 'tid': tid, 'args': {'name': name}}
                  for tid, name in [(main, 'CrRendererMain'), (compositor, 'Compositor')])
    def ts(ms):
        return round((ms + offset) * 1000)
    def event(name, phase, at, ident=None, args=None, tid=main, duration=None):
        row = {'pid': pid, 'tid': tid, 'name': name, 'ph': phase, 'ts': ts(at),
               'cat': 'cc' if tid == compositor else 'blink.animations,devtools.timeline', 'args': args or {}}
        if ident is not None:
            row['id2'] = {'local': ident}
        if duration is not None:
            row['dur'] = round(duration * 1000)
        events.append(row)
        return row
    def mark(label, at):
        name = 'mouse627.motion.' + label
        events.append({'name': name, 'cat': 'blink.user_timing', 'ph': 'I', 'pid': pid,
                       'tid': main, 'ts': ts(at) + 50, 'args': {'data': {'startTime': at}}})
        trace['mouseMotionTrace']['snapshots'].append({'label': label, 'value': {
            'native': {'rendererPid': pid, 'visible': True, 'focused': True, 'minimized': False},
            'renderer': {'marker': name, 'markStartTime': at, 'before': at, 'after': at,
                         'visibilityState': 'visible', 'hidden': False, 'hasFocus': True}}})
    def player(current=300, state='paused', pending=False, start=None, rate=-1):
        return {'currentTime': current, 'startTime': start, 'pending': pending,
                'playState': state, 'playbackRate': rate}
    def state(group, prop, old, new, at, tid):
        row = event('ElementAnimations::SetRunState', 'I', at, tid=tid,
                    args={'ccModel': {'group': group, 'targetProperty': prop, 'from': old, 'to': new}})
        row['cat'] = 'cc'
    def model(ident, group, prop, origin, begin, end, main_origin, main_end):
        state(group, prop, 'WAITING_FOR_TARGET_AVAILABILITY', 'STARTING', origin, compositor)
        event('KeyframeModel', 'b', begin, ident, tid=compositor,
              args={'ccModel': {'group': group, 'targetProperty': prop}})
        state(group, prop, 'STARTING', 'RUNNING', begin + .002, compositor)
        event('KeyframeModel', 'e', end, ident, tid=compositor)
        state(group, prop, 'RUNNING', 'FINISHED', end + .002, compositor)
        state(group, prop, 'FINISHED', 'WAITING_FOR_DELETION', end + .004, compositor)
        state(group, prop, 'WAITING_FOR_TARGET_AVAILABILITY', 'STARTING', main_origin, main)
        state(group, prop, 'STARTING', 'RUNNING', main_origin + .01, main)
        state(group, prop, 'RUNNING', 'FINISHED', main_end, main)
    def close(generation, base):
        timings = [0, .5, .7, .7, 4.9, 21.7, 21.7, 21.8, 58.1, 356.7]
        rows = []
        for name, elapsed in zip(GATE.STAGES, timings):
            value = player()
            if name == 'request':
                value = None
            elif name == 'play-pending':
                value = player(state='running', pending=True)
            elif name == 'play-ready':
                value = player(265.631, 'running', start=base + 314.631)
            elif name == 'complete':
                value = player(0, 'finished', start=base + 314.631)
            row = {'event': name, 'performanceNow': base + elapsed, 'documentTime': base + elapsed - 9,
                   'generation': generation, 'goal': 0, 'preparing': name in GATE.STAGES[2:6],
                   'phase': 'open' if name in ('request', 'players-paused') else 'closing',
                   'movement': copy.deepcopy(value), 'shade': copy.deepcopy(value)}
            if name in ('request', 'complete', 'prepare-await-ready', 'pause-ready',
                        'preparation-frame-1', 'preparation-frame-2', 'play-request'):
                row['to'] = 0
            if name == 'request':
                row['immediate'] = False
            if name.startswith('preparation-frame'):
                row['rafTime'] = base + elapsed - 3
            rows.append(row)
        play, finish = base + 21.7, base + 356.7
        # The same Blink local IDs are reused after each lifetime finishes.
        for index, ident in enumerate(('0x8c', '0xc5')):
            node = 1145 + index
            event('Animation', 'b', base + .1 + index * .1, ident,
                  {'data': {'nodeId': node, 'state': 'running'}, 'endData': {'state': 'paused'}})
            event('Animation', 'e', base + .4 + index * .1, ident)
            event('Animation', 'b', play + .022 + index * .023, ident,
                  {'data': {'nodeId': node, 'state': 'running'}, 'endData': {'state': 'finished'}})
            event('Animation', 'n', base + 58.0 + index * .009, ident, {'data': {'state': 'running'}})
            event('Animation', 'e', finish - .094 + index * .025, ident)
            event('Animation', 'n', finish + .32 + index * .019, ident, {'data': {'state': 'idle'}})
        # Earlier hover remains alive during close but must never satisfy it.
        model('0x8f', generation * 10 + 8, 4, play - 11, play - 10.62,
              finish - 97.57, play - 9, finish - 95)
        for index, ident in enumerate(('0xc6', '0xc7')):
            model(ident, generation * 10 + 9, (4, 0)[index], play + 2 + index * .003,
                  play + 3.108 + index * .009, finish - .475 + index * .015,
                  play + 18 + index * .003, finish + 12 + index * .003)
        event('AnimationHost::UpdateAnimationState', 'X', play + 3.095, tid=compositor, duration=.024)
        event('AnimationHost::UpdateAnimationState', 'X', finish - .485, tid=compositor, duration=.029)
        return rows
    mark('before', 500)
    mark('arm-light-closing', 900)
    mark('click-close', 990)
    light = close(16, 1000)
    mark('capture-light-closing', 1400)
    mark('arm-dark-closing', 1900)
    mark('click-close', 1990)
    dark = close(20, 2000)
    mark('capture-dark-closing', 2400)
    mark('click-close', 2990)
    later = close(26, 3000)
    mark('after', 4000)
    def geometry(rows, now, phase='closed'):
        return {'startup': {'enabled': True, 'events': copy.deepcopy(rows),
                            'current': {'performanceNow': now, 'phase': phase}}}
    # A live reverse request has players already; a reduced close has no fresh
    # players-paused event. Neither may become the required third fresh close.
    live = {'event': 'request', 'generation': 24, 'performanceNow': 2700, 'to': 0,
            'movement': player(160, 'running', start=2540), 'shade': player(160, 'running', start=2540)}
    reduced = {'event': 'request', 'generation': 30, 'performanceNow': 3700, 'to': 0,
               'movement': None, 'shade': None}
    motion = {'version': '6.0.27', 'themes': ['light', 'dark'], 'frames': {}, 'geometry': {
        'lightClosing': geometry(light, 1450),
        'darkClosing': geometry(light + dark, 2450),
        'interrupted': geometry(dark + [live], 2800, 'open'),
        'reduced': geometry([live] + later + [reduced], 3900)}}
    sync_counts(trace, motion)
    return trace, motion


# Exact rows from native8de5 run44364503705 (overall later614FAIL).
# Includes every renderer KeyframeModel boundary and all state events for the
# three close groups plus preexisting258/338 and extra379. No omitted END is reconstructed.
# Columns: ts,tid,phase,pointer-id,group,property,from,to.
OBSERVED_8DE5_CC_ROWS = json.loads('''[
  [280643289,32508,"b","0x6e",207,4,null,null],
  [280816462,32508,"e","0x6e",null,null,null,null],
  [281003003,32508,"b","0x6e",217,4,null,null],
  [281003013,32508,"b","0x86",217,0,null,null],
  [282567623,32508,"b","0xb9",244,0,null,null],
  [283095194,32508,"I",null,258,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [283096632,32508,"b","0xc5",258,4,null,null],
  [283096635,32508,"I",null,258,4,"STARTING","RUNNING"],
  [283110348,32497,"I",null,258,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [283110358,32497,"I",null,258,4,"STARTING","RUNNING"],
  [283110932,32508,"I",null,259,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [283110935,32508,"I",null,259,0,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [283112028,32508,"b","0xc7",259,4,null,null],
  [283112033,32508,"I",null,259,4,"STARTING","RUNNING"],
  [283112035,32508,"b","0xc8",259,0,null,null],
  [283112036,32508,"I",null,259,0,"STARTING","RUNNING"],
  [283126806,32497,"I",null,259,0,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [283126811,32497,"I",null,259,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [283126815,32497,"I",null,259,0,"STARTING","RUNNING"],
  [283126816,32497,"I",null,259,4,"STARTING","RUNNING"],
  [283269094,32497,"I",null,258,4,"RUNNING","FINISHED"],
  [283271559,32508,"e","0xc5",null,null,null,null],
  [283271561,32508,"I",null,258,4,"RUNNING","FINISHED"],
  [283271568,32508,"I",null,258,4,"FINISHED","WAITING_FOR_DELETION"],
  [283442808,32508,"I",null,259,4,"RUNNING","FINISHED"],
  [283442808,32508,"e","0xc7",null,null,null,null],
  [283442815,32508,"I",null,259,4,"FINISHED","WAITING_FOR_DELETION"],
  [283442817,32508,"I",null,259,0,"RUNNING","FINISHED"],
  [283442817,32508,"e","0xc8",null,null,null,null],
  [283442819,32508,"I",null,259,0,"FINISHED","WAITING_FOR_DELETION"],
  [283455358,32497,"I",null,259,0,"RUNNING","FINISHED"],
  [283455427,32497,"I",null,259,4,"RUNNING","FINISHED"],
  [284278756,32508,"b","0xc5",279,4,null,null],
  [284457185,32508,"e","0xc5",null,null,null,null],
  [284740619,32508,"b","0xc5",290,4,null,null],
  [284740637,32508,"b","0xc7",290,0,null,null],
  [285148701,32508,"e","0xc5",null,null,null,null],
  [285148746,32508,"e","0xc7",null,null,null,null],
  [285816323,32508,"b","0xc5",319,0,null,null],
  [285920586,32508,"b","0xc7",1,0,null,null],
  [286310792,32508,"I",null,338,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [286313080,32508,"b","0xc8",338,4,null,null],
  [286313092,32508,"I",null,338,4,"STARTING","RUNNING"],
  [286327325,32497,"I",null,338,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [286327343,32497,"I",null,338,4,"STARTING","RUNNING"],
  [286328719,32508,"I",null,339,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [286328769,32508,"I",null,339,0,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [286331039,32508,"b","0xb9",339,4,null,null],
  [286331053,32508,"I",null,339,4,"STARTING","RUNNING"],
  [286331057,32508,"b","0xe1",339,0,null,null],
  [286331059,32508,"I",null,339,0,"STARTING","RUNNING"],
  [286343826,32497,"I",null,339,0,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [286343839,32497,"I",null,339,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [286343848,32497,"I",null,339,0,"STARTING","RUNNING"],
  [286343851,32497,"I",null,339,4,"STARTING","RUNNING"],
  [286490161,32508,"e","0xc8",null,null,null,null],
  [286490162,32508,"I",null,338,4,"RUNNING","FINISHED"],
  [286490168,32508,"I",null,338,4,"FINISHED","WAITING_FOR_DELETION"],
  [286490755,32497,"I",null,338,4,"RUNNING","FINISHED"],
  [286662759,32508,"e","0xb9",null,null,null,null],
  [286662762,32508,"I",null,339,4,"RUNNING","FINISHED"],
  [286662777,32508,"I",null,339,4,"FINISHED","WAITING_FOR_DELETION"],
  [286662779,32508,"e","0xe1",null,null,null,null],
  [286662781,32508,"I",null,339,0,"RUNNING","FINISHED"],
  [286662783,32508,"I",null,339,0,"FINISHED","WAITING_FOR_DELETION"],
  [286670629,32497,"I",null,339,0,"RUNNING","FINISHED"],
  [286670713,32497,"I",null,339,4,"RUNNING","FINISHED"],
  [286900024,32508,"b","0xc8",351,4,null,null],
  [287060863,32508,"e","0xc8",null,null,null,null],
  [287289104,32508,"b","0xc8",365,4,null,null],
  [287289124,32508,"b","0xe1",365,0,null,null],
  [287541992,32508,"b","0xed",374,4,null,null],
  [287542001,32508,"b","0xee",1,4,null,null],
  [287542003,32508,"b","0xef",1,0,null,null],
  [287579970,32508,"b","0xc8",1,4,null,null],
  [287579976,32508,"b","0xe1",1,0,null,null],
  [287769655,32508,"I",null,379,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [287806925,32497,"I",null,379,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [287806952,32497,"I",null,379,4,"STARTING","RUNNING"],
  [287808537,32508,"b","0xf1",379,4,null,null],
  [287808567,32508,"I",null,379,4,"STARTING","RUNNING"],
  [287808988,32508,"I",null,380,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [287808993,32508,"I",null,380,0,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [287909909,32508,"b","0xc8",380,4,null,null],
  [287909912,32508,"I",null,380,4,"STARTING","RUNNING"],
  [287909916,32508,"b","0xf2",380,0,null,null],
  [287909927,32508,"I",null,380,0,"STARTING","RUNNING"],
  [287910099,32497,"I",null,380,0,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [287910106,32497,"I",null,380,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [287910110,32497,"I",null,380,0,"STARTING","RUNNING"],
  [287910111,32497,"I",null,380,4,"STARTING","RUNNING"],
  [288014878,32508,"I",null,379,4,"RUNNING","FINISHED"],
  [288014878,32508,"e","0xf1",null,null,null,null],
  [288014885,32508,"I",null,379,4,"FINISHED","WAITING_FOR_DELETION"],
  [288016121,32497,"I",null,379,4,"RUNNING","FINISHED"],
  [288328015,32508,"e","0xc8",null,null,null,null],
  [288328023,32508,"I",null,380,4,"RUNNING","FINISHED"],
  [288328038,32508,"I",null,380,4,"FINISHED","WAITING_FOR_DELETION"],
  [288328041,32508,"e","0xf2",null,null,null,null],
  [288328043,32508,"I",null,380,0,"RUNNING","FINISHED"],
  [288328045,32508,"I",null,380,0,"FINISHED","WAITING_FOR_DELETION"],
  [288332097,32497,"I",null,380,0,"RUNNING","FINISHED"],
  [288332111,32497,"I",null,380,4,"RUNNING","FINISHED"]
]''')


# Exact fd274 native run44366767902 excerpt (overall later620FAIL).
# Every renderer model boundary plus the six close/extra structural groups;
# target320 has no END or terminal State. This excerpt does not invent either.
OBSERVED_FD27_CC_ROWS = json.loads('''[
  [280495525,32445,"b","0x7b",174,4,null,null],
  [280670854,32445,"e","0x7b",null,null,null,null],
  [280670866,32445,"b","0x7b",179,4,null,null],
  [280670869,32445,"b","0x8a",179,0,null,null],
  [281128450,32445,"e","0x7b",null,null,null,null],
  [281128460,32445,"e","0x8a",null,null,null,null],
  [281949176,32445,"b","0x7b",204,0,null,null],
  [282203312,32445,"e","0x7b",null,null,null,null],
  [282329814,32445,"I",null,212,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [282331883,32445,"b","0x7b",212,4,null,null],
  [282331889,32445,"I",null,212,4,"STARTING","RUNNING"],
  [282344011,32435,"I",null,212,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [282344017,32435,"I",null,212,4,"STARTING","RUNNING"],
  [282344530,32445,"I",null,213,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [282344532,32445,"I",null,213,0,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [282345540,32445,"b","0x8a",213,4,null,null],
  [282345545,32445,"I",null,213,4,"STARTING","RUNNING"],
  [282345546,32445,"b","0xc0",213,0,null,null],
  [282345547,32445,"I",null,213,0,"STARTING","RUNNING"],
  [282363548,32435,"I",null,213,0,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [282363553,32435,"I",null,213,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [282363557,32435,"I",null,213,0,"STARTING","RUNNING"],
  [282363559,32435,"I",null,213,4,"STARTING","RUNNING"],
  [282500615,32435,"I",null,212,4,"RUNNING","FINISHED"],
  [282660774,32445,"e","0x8a",null,null,null,null],
  [282660779,32445,"I",null,213,4,"RUNNING","FINISHED"],
  [282660787,32445,"I",null,213,4,"FINISHED","WAITING_FOR_DELETION"],
  [282660790,32445,"e","0xc0",null,null,null,null],
  [282660791,32445,"I",null,213,0,"RUNNING","FINISHED"],
  [282660793,32445,"I",null,213,0,"FINISHED","WAITING_FOR_DELETION"],
  [282667918,32435,"I",null,213,0,"RUNNING","FINISHED"],
  [282667927,32435,"I",null,213,4,"RUNNING","FINISHED"],
  [283294382,32445,"b","0x8a",230,4,null,null],
  [283482114,32445,"e","0x8a",null,null,null,null],
  [283482128,32445,"b","0x8a",235,4,null,null],
  [283482136,32445,"b","0xc0",235,0,null,null],
  [284298767,32445,"b","0xd3",258,10,null,null],
  [284518614,32445,"b","0xd4",265,0,null,null],
  [284635380,32445,"b","0xd5",1,0,null,null],
  [284961617,32445,"I",null,280,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [284962181,32435,"I",null,280,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [284962186,32435,"I",null,280,4,"STARTING","RUNNING"],
  [284962400,32445,"I",null,281,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [284962405,32445,"I",null,281,0,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [284963406,32445,"b","0xd7",280,4,null,null],
  [284963412,32445,"I",null,280,4,"STARTING","RUNNING"],
  [284977341,32435,"I",null,281,0,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [284977351,32435,"I",null,281,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [284977359,32435,"I",null,281,0,"STARTING","RUNNING"],
  [284977362,32435,"I",null,281,4,"STARTING","RUNNING"],
  [284978558,32445,"b","0xd8",281,4,null,null],
  [284978564,32445,"I",null,281,4,"STARTING","RUNNING"],
  [284978566,32445,"b","0xd9",281,0,null,null],
  [284978567,32445,"I",null,281,0,"STARTING","RUNNING"],
  [285120614,32435,"I",null,280,4,"RUNNING","FINISHED"],
  [285342096,32445,"e","0xd8",null,null,null,null],
  [285342101,32445,"I",null,281,4,"RUNNING","FINISHED"],
  [285342108,32445,"I",null,281,4,"FINISHED","WAITING_FOR_DELETION"],
  [285342110,32445,"e","0xd9",null,null,null,null],
  [285342112,32445,"I",null,281,0,"RUNNING","FINISHED"],
  [285342114,32445,"I",null,281,0,"FINISHED","WAITING_FOR_DELETION"],
  [285349817,32435,"I",null,281,0,"RUNNING","FINISHED"],
  [285349822,32435,"I",null,281,4,"RUNNING","FINISHED"],
  [285556939,32445,"b","0xd8",294,4,null,null],
  [285878108,32445,"b","0xd9",307,4,null,null],
  [285878116,32445,"b","0xea",307,0,null,null],
  [286072994,32445,"b","0xeb",314,4,null,null],
  [286073002,32445,"b","0xec",1,4,null,null],
  [286073005,32445,"b","0xed",1,0,null,null],
  [286139160,32445,"b","0xd9",1,4,null,null],
  [286139181,32445,"e","0xd9",null,null,null,null],
  [286139191,32445,"b","0xea",1,4,null,null],
  [286139195,32445,"b","0xd4",1,0,null,null],
  [286281514,32445,"I",null,319,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [286328904,32435,"I",null,319,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [286328911,32435,"I",null,319,4,"STARTING","RUNNING"],
  [286329701,32445,"b","0xd9",319,4,null,null],
  [286329702,32445,"I",null,319,4,"STARTING","RUNNING"],
  [286329881,32445,"I",null,320,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [286329883,32445,"I",null,320,0,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [286351766,32435,"I",null,320,0,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [286351773,32435,"I",null,320,4,"WAITING_FOR_TARGET_AVAILABILITY","STARTING"],
  [286351778,32435,"I",null,320,0,"STARTING","RUNNING"],
  [286351779,32435,"I",null,320,4,"STARTING","RUNNING"],
  [286351826,32445,"b","0xee",320,4,null,null],
  [286351830,32445,"I",null,320,4,"STARTING","RUNNING"],
  [286351832,32445,"b","0xef",320,0,null,null],
  [286351833,32445,"I",null,320,0,"STARTING","RUNNING"],
  [286482327,32435,"I",null,319,4,"RUNNING","FINISHED"]
]''')


def structural_fixture_events(rows, pid):
    events = []
    for at, tid, phase, ident, group, prop, old, new in rows:
        event = {'pid': pid, 'tid': tid, 'ts': at, 'cat': 'cc', 'ph': phase,
                 'name': 'ElementAnimations::SetRunState' if phase == 'I' else 'KeyframeModel', 'args': {}}
        if ident is not None:
            event['id2'] = {'local': ident}
        if group is not None:
            event['args']['ccModel'] = {'group': group, 'targetProperty': prop}
            if phase == 'I':
                event['args']['ccModel'].update({'from': old, 'to': new})
        events.append(event)
    return sorted(events, key=lambda e: e['ts'])


class TraceEvidenceContract(unittest.TestCase):
    def setUp(self):
        self.trace, self.motion = observed_schema_fixture()

    def test_actual_23e5_light_close_startup_rows_are_supported(self):
        stages = {row['event']: copy.deepcopy(row) for row in OBSERVED_LIGHT_CLOSE}
        self.assertEqual(set(stages), set(GATE.STAGES))
        GATE.startup_contract(stages, 'actual23e5LightClosing')
        stages['play-pending']['movement']['pending'] = False
        with self.assertRaisesRegex(GATE.MotionTraceError, 'missing real pending play'):
            GATE.startup_contract(stages, 'actual23e5LightClosing')

    def reject(self, pattern):
        sync_counts(self.trace, self.motion)
        with self.assertRaisesRegex(GATE.MotionTraceError, pattern):
            GATE.verify_trace_data(self.trace, self.motion)

    def move_hover_begin_after_play(self, new_origin=False):
        rows = [e for e in self.trace['traceEvents'] if e.get('args', {}).get('ccModel', {}).get('group') == 168]
        begin = next(e for e in rows if e['name'] == 'KeyframeModel')
        begin['ts'] = 201024500
        running = next(e for e in rows if e['name'] == 'ElementAnimations::SetRunState' and
                       e['tid'] == 102 and e['args']['ccModel']['to'] == 'RUNNING')
        running['ts'] = begin['ts'] + 2
        if new_origin:
            next(e for e in rows if e['tid'] == 102 and
                 e['args']['ccModel'].get('to') == 'STARTING')['ts'] = begin['ts'] - 100

    def post_completion_terminals(self, impl='WAITING_FOR_DELETION',
                                  end_delay=5000, main_delay=3000, bridge=True):
        """Source-supported synthetic cleanup, not a claim about native8de5."""
        events, finish = self.trace['traceEvents'], 201356700
        begins = [e for e in events if e['name'] == 'KeyframeModel' and e['ph'] == 'b' and
                  e['args']['ccModel']['group'] == 169]
        for index, begin in enumerate(begins):
            prop = begin['args']['ccModel']['targetProperty']
            rows = [e for e in events if e['name'] == 'ElementAnimations::SetRunState' and
                    e['args']['ccModel']['group'] == 169 and e['args']['ccModel']['targetProperty'] == prop]
            end = min((e for e in events if e['name'] == 'KeyframeModel' and e['ph'] == 'e' and
                       e['id2'] == begin['id2'] and e['ts'] > begin['ts']), key=lambda e: e['ts'])
            end['ts'] = finish + end_delay + index * 15
            main_end = next(e for e in rows if e['tid'] == 101 and e['args']['ccModel']['to'] == 'FINISHED')
            main_end['ts'] = finish + main_delay + index * 3
            main_end['args']['ccModel']['to'] = 'ABORTED'
            impl_end = next(e for e in rows if e['tid'] == 102 and e['args']['ccModel']['to'] == 'FINISHED')
            impl_end['ts'] = end['ts'] + 2
            impl_end['args']['ccModel']['to'] = impl
            deletion = next(e for e in rows if e['tid'] == 102 and
                            e['args']['ccModel']['from'] == 'FINISHED')
            events.remove(deletion)
            if impl == 'ABORTED':
                deletion['ts'] = end['ts'] + 4
                deletion['args']['ccModel']['from'] = 'ABORTED'
                events.append(deletion)
            if bridge:
                event = copy.deepcopy(impl_end)
                event['ts'] = end['ts'] + 6
                event['args']['ccModel'].update({'from': 'ABORTED', 'to': 'WAITING_FOR_DELETION'})
                events.append(event)
        # Cleanup from PushPropertiesTo has no AnimationHost update requirement.
        self.trace['traceEvents'] = [e for e in events if not (e['name'] == 'AnimationHost::UpdateAnimationState'
                                   and 201300000 < e['ts'] < 201400000)]
        sync_counts(self.trace, self.motion)

    def omit_compositor_terminals(self, group=169, omit_main=True):
        """Explicitly synthetic absence of both END and impl terminal."""
        events = self.trace['traceEvents']
        begins = [e for e in events if e['name'] == 'KeyframeModel' and e['ph'] == 'b' and
                  e['args']['ccModel']['group'] == group]
        ends = [min((e for e in events if e['name'] == 'KeyframeModel' and e['ph'] == 'e' and
                     e['id2'] == begin['id2'] and e['ts'] > begin['ts']), key=lambda e: e['ts'])
                for begin in begins]
        self.trace['traceEvents'] = [e for e in events if e not in ends and not
            (e['name'] == 'ElementAnimations::SetRunState' and e['args']['ccModel']['group'] == group and
             (e['tid'] == 102 or omit_main) and e['args']['ccModel']['to'] in GATE.CC_TERMINAL)]
        sync_counts(self.trace, self.motion)

    def release_and_post_frames(self, frames=True):
        release = {'event': 'release', 'generation': 16, 'performanceNow': 1356.9,
                   'documentTime': 1355, 'goal': 0, 'preparing': False, 'phase': 'closed',
                   'movement': None, 'shade': None}
        for value in self.motion['geometry'].values():
            rows = value['startup']['events']
            if any(row['generation'] == 16 for row in rows):
                rows.append(copy.deepcopy(release))
        if frames:
            for name, at in [('BeginFrame', 201369000), ('Scheduler::BeginImplFrame', 201370000),
                              ('LayerTreeHostImpl::PrepareToDraw', 201375000)]:
                self.trace['traceEvents'].append({'name': name, 'ph': 'X', 'pid': 42, 'tid': 102,
                                                 'ts': at, 'dur': 100, 'cat': 'cc', 'args': {}})
        sync_counts(self.trace, self.motion)

    def test_actual_8de5_structural_rows_split_pointer_reuse_and_explain_extra_singleton(self):
        events = structural_fixture_events(OBSERVED_8DE5_CC_ROWS, 22260)
        index = GATE.CompositorEvidence(events, 22260, 32497, 32508)
        for lo, hi, expected in [(283109906, 283438570, 259), (286326906, 286654970, 339),
                                  (287806406, 288315770, 380)]:
            pair, chains, excluded, explained = index.select(lo, hi, 'actual8de5')
            self.assertEqual({m['key'] for m in pair}, {(expected, 0), (expected, 4)})
            self.assertTrue(all(chains[m['key']]['impl']['terminal']['args']['ccModel']['to'] == 'FINISHED'
                                for m in pair))
            self.assertEqual([m['key'] for m, _ in excluded], [(379, 4)] if expected == 380 else [])
            self.assertEqual([m['key'] for m, _ in explained],
                             {259: [(258, 4)], 339: [(338, 4)], 380: []}[expected])
            if expected == 339:
                model = next(m for m in pair if m['key'][1] == 4)
                self.assertEqual(model['priorIncomplete']['key'], (244, 0))
                self.assertIsNone(model['priorIncomplete']['end'])
            if expected == 380:
                model = next(m for m in pair if m['key'][1] == 4)
                self.assertEqual(model['priorIncomplete']['key'], (1, 4))
                self.assertEqual(model['priorIncomplete']['priorIncomplete']['key'], (365, 4))
                self.assertIsNone(model['priorIncomplete']['end'])

    def test_actual_fd27_startups_keep_missing_target_and_extra_terminals_unknown(self):
        events = structural_fixture_events(OBSERVED_FD27_CC_ROWS, 22155)
        index = GATE.CompositorEvidence(events, 22155, 32435, 32445)
        for lo, hi, expected in [(282343613, 282652653, 213), (284961913, 285338453, 281),
                                  (286328413, 286645153, 320)]:
            pair, chains, excluded, explained = index.select(lo, hi, 'actualfd27')
            self.assertEqual({m['key'] for m in pair}, {(expected, 0), (expected, 4)})
            self.assertEqual([m['key'] for m, _ in excluded],
                             {213: [], 281: [(280, 4)], 320: [(319, 4)]}[expected])
            self.assertEqual([m['key'] for m, _ in explained], [(212, 4)] if expected == 213 else [])
            for model in pair:
                chain = chains[model['key']]
                if expected == 320:
                    self.assertIsNone(model['end'])
                    self.assertIsNone(chain['impl']['terminal'])
                    self.assertIsNone(chain['main']['terminal'])
                    self.assertEqual(len(chain['impl']['events']), 2)
                    self.assertEqual(len(chain['main']['events']), 2)
                else:
                    self.assertIsNotNone(model['end'])
                    self.assertEqual(chain['impl']['terminal']['args']['ccModel']['to'], 'FINISHED')

    def test_preplay_structural_origin_can_explain_a_later_singleton_begin(self):
        self.move_hover_begin_after_play()
        report = GATE.verify_trace_data(self.trace, self.motion)
        excluded = report['freshCloses'][0]['excludedFreshSingletons']
        self.assertEqual([(row['group'], row['targetProperty']) for row in excluded], [(168, 4)])

    def test_extra_model_with_new_origin_is_not_excluded_by_its_shorter_duration(self):
        self.move_hover_begin_after_play(new_origin=True)
        self.reject('extra compositor model has new/unknown origin')

    def test_extra_model_without_main_provenance_is_not_accepted(self):
        self.move_hover_begin_after_play()
        self.trace['traceEvents'] = [e for e in self.trace['traceEvents'] if not
            (e['name'] == 'ElementAnimations::SetRunState' and e['tid'] == 101 and
             e['args']['ccModel']['group'] == 168)]
        self.reject('main or impl state provenance')

    def test_same_structural_key_before_play_is_a_collision_even_with_another_pointer(self):
        original = next(e for e in self.trace['traceEvents'] if e['name'] == 'KeyframeModel' and
                        e['ph'] == 'b' and e['args']['ccModel']['group'] == 169)
        prior = copy.deepcopy(original)
        prior.update({'ts': 201000000, 'id2': {'local': 'another-pointer'}})
        self.trace['traceEvents'].append(prior)
        self.reject('structural key collision/reuse')

    def test_competing_structural_pair_is_rejected_before_choosing_a_complete_pair(self):
        for index, prop in enumerate((0, 4)):
            self.trace['traceEvents'].append({'name': 'KeyframeModel', 'ph': 'b', 'pid': 42, 'tid': 102,
                'ts': 201025800 + index * 10, 'cat': 'cc', 'id2': {'local': 'competitor-' + str(prop)},
                'args': {'ccModel': {'group': 999, 'targetProperty': prop}}})
        self.reject('fresh compositor candidates missing/ambiguous')

    def test_unaccounted_fresh_impl_origin_without_begin_is_rejected(self):
        self.trace['traceEvents'].append({'name': 'ElementAnimations::SetRunState', 'ph': 'I',
            'pid': 42, 'tid': 102, 'ts': 201025000, 'cat': 'cc', 'args': {'ccModel': {
                'group': 999, 'targetProperty': 7, 'from': 'WAITING_FOR_TARGET_AVAILABILITY', 'to': 'STARTING'}}})
        self.reject('unaccounted main/impl origin')

    def test_unaccounted_fresh_main_only_target_chain_is_rejected(self):
        for at, old, new in [(201025000, 'WAITING_FOR_TARGET_AVAILABILITY', 'STARTING'),
                             (201025010, 'STARTING', 'RUNNING'), (201356600, 'RUNNING', 'FINISHED')]:
            self.trace['traceEvents'].append({'name': 'ElementAnimations::SetRunState', 'ph': 'I',
                'pid': 42, 'tid': 101, 'ts': at, 'cat': 'cc', 'args': {'ccModel': {
                    'group': 999, 'targetProperty': 0, 'from': old, 'to': new}}})
        self.reject('unaccounted main/impl origin')

    def test_delayed_main_origin_is_explained_by_a_complete_preplay_impl_model(self):
        for event in self.trace['traceEvents']:
            cc = event.get('args', {}).get('ccModel', {})
            if event['name'] == 'ElementAnimations::SetRunState' and event['tid'] == 101 and cc['group'] == 168:
                if cc['to'] == 'STARTING':
                    event['ts'] = 201021760
                elif cc['to'] == 'RUNNING':
                    event['ts'] = 201021770
        report = GATE.verify_trace_data(self.trace, self.motion)
        self.assertEqual([(m['group'], m['targetProperty']) for m in
                          report['freshCloses'][0]['explainedPreexistingOrigins']], [(168, 4)])
        self.trace['traceEvents'] = [e for e in self.trace['traceEvents'] if not
            (e['name'] == 'KeyframeModel' and e['ph'] == 'e' and e['id2'] == {'local': '0x8f'} and
             e['ts'] < 202000000)]
        self.reject('END/impl terminal coverage is inconsistent')

    def test_main_start_can_precede_impl_running_without_changing_the_key(self):
        for event in self.trace['traceEvents']:
            cc = event.get('args', {}).get('ccModel', {})
            if event['name'] == 'ElementAnimations::SetRunState' and event['tid'] == 101 and cc['group'] == 169:
                if cc['to'] == 'STARTING':
                    event['ts'] = 201024000 + cc['targetProperty']
                elif cc['to'] == 'RUNNING':
                    event['ts'] = 201024010 + cc['targetProperty']
        self.assertEqual(GATE.verify_trace_data(self.trace, self.motion)['status'], 'pass')

    def test_different_incomplete_pointer_generation_is_retained_without_an_invented_end(self):
        self.trace['traceEvents'].append({'name': 'KeyframeModel', 'ph': 'b', 'pid': 42, 'tid': 102,
            'ts': 201005000, 'cat': 'cc', 'id2': {'local': '0xc6'},
            'args': {'ccModel': {'group': 77, 'targetProperty': 0}}})
        sync_counts(self.trace, self.motion)
        report = GATE.verify_trace_data(self.trace, self.motion)
        prior = report['freshCloses'][0]['priorIncompletePointerSegments']
        self.assertEqual(len(prior), 1)
        self.assertEqual(prior[0]['group'], 77)
        self.assertIsNone(prior[0]['endTraceUs'])

    def test_duplicate_origin_chain_and_reserved_group_fail_closed(self):
        for mutation in ('origin', 'reserved'):
            with self.subTest(mutation=mutation):
                self.trace, self.motion = observed_schema_fixture()
                if mutation == 'origin':
                    row = next(e for e in self.trace['traceEvents'] if e['name'] == 'ElementAnimations::SetRunState'
                               and e['tid'] == 101 and e['args']['ccModel']['group'] == 169)
                    duplicate = copy.deepcopy(row); duplicate['ts'] -= 1000
                    self.trace['traceEvents'].append(duplicate)
                    self.reject('origin/start chain')
                else:
                    for event in self.trace['traceEvents']:
                        if event.get('args', {}).get('ccModel', {}).get('group') == 169:
                            event['args']['ccModel']['group'] = 1
                    self.reject('reserved/reused')

    def test_end_requires_its_own_matching_next_state_and_same_timestamp_is_supported(self):
        model = next(e for e in self.trace['traceEvents'] if e['name'] == 'KeyframeModel' and
                     e['ph'] == 'e' and e['id2'] == {'local': '0xc6'})
        terminal = next(e for e in self.trace['traceEvents'] if e['name'] == 'ElementAnimations::SetRunState' and
                        e['tid'] == 102 and e['args']['ccModel']['group'] == 169 and
                        e['args']['ccModel']['targetProperty'] == 4 and e['args']['ccModel']['to'] == 'FINISHED')
        terminal['ts'] = model['ts']
        self.trace['traceEvents'].reverse()
        self.assertEqual(GATE.verify_trace_data(self.trace, self.motion)['status'], 'pass')
        terminal['ts'] = model['ts'] + 2
        other = copy.deepcopy(terminal)
        other['ts'] = model['ts'] + 1
        other['args']['ccModel']['group'] = 999
        self.trace['traceEvents'].append(other)
        self.reject('boundary/state')

    def test_delayed_main_finished_is_bookkeeping_in_a_synthetic_full_scenario(self):
        # d6b1 had last Blink END 294735570 and main FINISHED p0/p4 at
        # 294790649/294790651. Reuse only these observed lags in this synthetic
        # full scenario; the real d6b1 native visual result remains a failure.
        lag_us = {0: 55079, 4: 55081}
        events = self.trace['traceEvents']
        blink_end = max(e['ts'] for e in events if e['name'] == 'Animation' and
                        e['ph'] == 'e' and 201300000 < e['ts'] < 201400000)
        terminals = [e for e in events if e['name'] == 'ElementAnimations::SetRunState' and
                     e['tid'] == 101 and e['args']['ccModel']['group'] == 169 and
                     e['args']['ccModel']['to'] == 'FINISHED']
        self.assertEqual(len(terminals), 2)
        for event in terminals:
            event['ts'] = blink_end + lag_us[event['args']['ccModel']['targetProperty']]
        report = GATE.verify_trace_data(self.trace, self.motion)
        self.assertEqual(report['status'], 'pass')
        self.assertIn('bookkeeping', report['mainFinishedTimestampMeaning'])
        self.assertIn('not visual completion', report['mainFinishedTimestampMeaning'])
        for model in report['freshCloses'][0]['compositorLifetimes']:
            self.assertEqual(model['stateChains']['main'][-1]['traceUs'] - blink_end,
                             lag_us[model['targetProperty']])
        # The exception is specific to FINISHED; late main ABORTED still keeps
        # its existing skew check as well as the separate active-abort check.
        terminals[0]['args']['ccModel']['to'] = 'ABORTED'
        self.reject('state/Blink completions disagree')

    def test_delayed_impl_end_and_finished_still_fail_completion_skew(self):
        # Synthetic coherent impl pair shifted by 55 ms; its matching END,
        # terminal states and host update move together, so the rejection must
        # come from completion skew, not a broken structural boundary.
        for event in self.trace['traceEvents']:
            model = event.get('args', {}).get('ccModel', {})
            if (event['name'] == 'ElementAnimations::SetRunState' and
                    event['tid'] == 102 and model['group'] == 169 and
                    model['to'] in GATE.CC_TERMINAL):
                event['ts'] += 55000
            elif (event['name'] == 'KeyframeModel' and event['ph'] == 'e' and
                  event.get('id2', {}).get('local') in ('0xc6', '0xc7') and
                  201300000 < event['ts'] < 201400000):
                event['ts'] += 55000
            elif (event['name'] == 'AnimationHost::UpdateAnimationState' and
                  event['tid'] == 102 and 201300000 < event['ts'] < 201400000):
                event['ts'] += 55000
        self.reject('compositor/Blink completions disagree')

    def test_known_post_completion_cleanup_records_actual_state_without_finished_claim(self):
        for terminal in ('WAITING_FOR_DELETION', 'ABORTED'):
            with self.subTest(terminal=terminal):
                self.trace, self.motion = observed_schema_fixture()
                self.post_completion_terminals(impl=terminal)
                report = GATE.verify_trace_data(self.trace, self.motion)
                phase = report['freshCloses'][0]
                self.assertIsNone(phase['finishHostUpdate'])
                self.assertTrue(all(m['postCompletionTerminal'] and m['observedTerminalStates'] ==
                                    {'main': 'ABORTED', 'impl': terminal} for m in phase['compositorLifetimes']))

    def test_abort_within_clock_tolerance_but_before_complete_is_still_rejected(self):
        self.post_completion_terminals(end_delay=-30, main_delay=-40)
        self.reject('active-phase abort/deletion before both recorded DOM endpoints')

    def test_cleanup_does_not_replace_either_dom_finished_endpoint(self):
        self.post_completion_terminals()
        for value in self.motion['geometry'].values():
            for row in value['startup']['events']:
                if row['generation'] == 16 and row['event'] == 'complete':
                    row['shade']['currentTime'] = 1
        self.reject('closed endpoint')

    def test_blink_end_must_explicitly_record_finished_before_cleanup_is_considered(self):
        self.post_completion_terminals()
        row = next(e for e in self.trace['traceEvents'] if e['name'] == 'Animation' and
                   e['ph'] == 'b' and 201020000 < e['ts'] < 201030000)
        row['args']['endData']['state'] = 'paused'
        self.reject('Blink target did not record finished')

    def test_unobserved_terminal_keeps_null_end_and_does_not_claim_removal_or_continuity(self):
        self.omit_compositor_terminals()
        self.release_and_post_frames()
        report = GATE.verify_trace_data(self.trace, self.motion)
        self.assertEqual(report['acceptanceScope'], 'unique-compositor-starts-and-dom-completion')
        self.assertFalse(report['continuousCompositorLifetimeProven'])
        phase = report['freshCloses'][0]
        for model in phase['compositorLifetimes']:
            self.assertIsNone(model['endTraceUs'])
            self.assertEqual(model['terminalObservation'], 'not-observed')
            self.assertEqual(model['observedTerminalStates'], {'main': None, 'impl': None})
            self.assertFalse(model['removalObserved'])
            self.assertFalse(model['continuousCompositorLifetimeProven'])
            self.assertGreater(model['nextPointerBegin']['traceUs'], phase['postEndpointThresholdTraceUs'])
        self.assertTrue(phase['postCompletionCoverage']['playersNull'])
        self.assertEqual(phase['postCompletionCoverage']['frames']['Scheduler::BeginImplFrame']['count'], 1)

    def test_observed_terminal_without_end_or_end_without_terminal_is_contradictory(self):
        for retain in ('terminal', 'end'):
            with self.subTest(retain=retain):
                self.trace, self.motion = observed_schema_fixture()
                original = copy.deepcopy(self.trace['traceEvents'])
                self.omit_compositor_terminals()
                self.release_and_post_frames()
                if retain == 'terminal':
                    row = next(e for e in original if e['name'] == 'ElementAnimations::SetRunState' and
                               e['tid'] == 102 and e['args']['ccModel']['group'] == 169 and
                               e['args']['ccModel']['targetProperty'] == 4 and e['args']['ccModel']['to'] == 'FINISHED')
                else:
                    row = next(e for e in original if e['name'] == 'KeyframeModel' and e['ph'] == 'e' and
                               e['id2'] == {'local': '0xc6'})
                self.trace['traceEvents'].append(row)
                self.reject('END/impl terminal coverage is inconsistent')

    def test_unknown_terminal_needs_release_and_real_subsequent_compositor_coverage(self):
        self.omit_compositor_terminals()
        self.reject('lacks unique controller release')
        self.release_and_post_frames(frames=False)
        self.reject('lacks subsequent compositor/frame coverage')

    def test_unknown_terminal_release_cannot_precede_endpoints_or_retain_a_player(self):
        for mutation in ('early', 'player'):
            with self.subTest(mutation=mutation):
                self.trace, self.motion = observed_schema_fixture()
                self.omit_compositor_terminals(); self.release_and_post_frames()
                for value in self.motion['geometry'].values():
                    for row in value['startup']['events']:
                        if row['generation'] == 16 and row['event'] == 'release':
                            if mutation == 'early':
                                row['performanceNow'] = 1356.6
                            else:
                                row['shade'] = {'playState': 'running'}
                self.reject('release after both DOM endpoints')

    def test_unobserved_end_cannot_hide_raw_pointer_reuse_before_dom_endpoints(self):
        self.omit_compositor_terminals(); self.release_and_post_frames()
        events = self.trace['traceEvents']
        begin = next(e for e in events if e['name'] == 'KeyframeModel' and e['ph'] == 'b' and
                     e['args']['ccModel']['group'] == 168)
        end = next(e for e in events if e['name'] == 'KeyframeModel' and e['ph'] == 'e' and
                   e['id2'] == begin['id2'] and e['ts'] < 202000000)
        begin['id2'] = end['id2'] = {'local': '0xc6'}
        begin['ts'] = 201200000
        next(e for e in events if e['name'] == 'ElementAnimations::SetRunState' and e['tid'] == 102 and
             e['args']['ccModel']['group'] == 168 and e['args']['ccModel']['to'] == 'RUNNING')['ts'] = 201200002
        self.reject('missing-END pointer is reused before both DOM endpoints')

    def test_unknown_impl_terminal_does_not_hide_observed_active_main_abort(self):
        self.omit_compositor_terminals(); self.release_and_post_frames()
        self.trace['traceEvents'].append({'name': 'ElementAnimations::SetRunState', 'ph': 'I',
            'pid': 42, 'tid': 101, 'ts': 201356660, 'cat': 'cc', 'args': {'ccModel': {
                'group': 169, 'targetProperty': 4, 'from': 'RUNNING', 'to': 'ABORTED'}}})
        self.reject('active-phase abort/deletion before both recorded DOM endpoints')

    def test_preplay_singleton_age_does_not_require_an_unobserved_terminal(self):
        self.move_hover_begin_after_play()
        self.omit_compositor_terminals(group=168, omit_main=False)
        report = GATE.verify_trace_data(self.trace, self.motion)
        extra = report['freshCloses'][0]['excludedFreshSingletons'][0]
        self.assertEqual(extra['group'], 168)
        self.assertEqual(extra['terminalObservation'], 'not-observed')
        self.assertEqual(extra['observedTerminalStates'], {'main': 'FINISHED', 'impl': None})
        self.assertIsNone(extra['endTraceUs'])
        self.assertFalse(extra['removalObserved'])

    def test_three_pairs_with_reused_ids_and_earlier_hover_pass_explicit_correlation(self):
        report = GATE.verify_trace_data(self.trace, self.motion)
        self.assertEqual(report['algorithm'], 'mouse627-motion-trace-evidence-v1')
        self.assertFalse(report['directIdentityLink'])
        self.assertEqual(report['attribution'], 'temporal-correlation')
        self.assertEqual([r['generation'] for r in report['freshCloses']], [16, 20, 26])
        self.assertTrue(all(r['excludedPreexistingModels'] == 1 for r in report['freshCloses']))
        self.assertTrue(all({m['identity']['local'] for m in r['compositorLifetimes']} ==
                            {'0xc6', '0xc7'} for r in report['freshCloses']))

    def test_active_rejection_is_not_cleared_by_later_success_or_other_models(self):
        begin = next(e for e in self.trace['traceEvents'] if e['name'] == 'Animation' and
                     e['ph'] == 'b' and e['ts'] > 201020000)
        self.trace['traceEvents'].append({**begin, 'ph': 'n', 'ts': begin['ts'] + 200,
                                         'args': {'data': {'compositeFailed': 4}}})
        self.reject('active-phase compositor rejection compositeFailed=4')

    def test_missing_final_scenario_cannot_be_replaced_by_live_reverse(self):
        del self.motion['geometry']['reduced']
        self.reject('scenario incomplete')

    def test_only_existing_hover_and_no_fresh_models_is_rejected(self):
        self.trace['traceEvents'] = [e for e in self.trace['traceEvents'] if
            not (e['name'] == 'KeyframeModel' and e.get('id2', {}).get('local') in ('0xc6', '0xc7'))]
        self.reject('fresh compositor candidates missing/ambiguous')

    def test_extra_compositor_candidate_is_rejected_without_choosing_nearest_pair(self):
        self.trace['traceEvents'].append({'name': 'KeyframeModel', 'ph': 'b', 'pid': 42, 'tid': 102,
            'ts': 201025000, 'cat': 'cc', 'id2': {'local': 'unrelated'}, 'args': {}})
        self.reject('structural ccModel')

    def test_another_blink_begin_in_the_same_play_window_is_ambiguous(self):
        self.trace['traceEvents'].append({'name': 'Animation', 'ph': 'b', 'pid': 42, 'tid': 101,
            'ts': 201021730, 'cat': 'blink.animations', 'id2': {'local': 'unrelated'},
            'args': {'data': {'nodeId': 999, 'state': 'running'}}})
        self.reject('Blink start window is missing/ambiguous')

    def test_earlier_rejection_on_reused_id_is_not_assigned_to_new_lifetime(self):
        self.trace['traceEvents'].append({'name': 'Animation', 'ph': 'n', 'pid': 42, 'tid': 101,
            'ts': 201000250, 'cat': 'blink.animations', 'id2': {'local': '0x8c'},
            'args': {'data': {'compositeFailed': 4}}})
        sync_counts(self.trace, self.motion)
        self.assertEqual(GATE.verify_trace_data(self.trace, self.motion)['status'], 'pass')

    def test_missing_model_end_is_not_completed_by_a_later_reused_id(self):
        self.trace['traceEvents'] = [e for e in self.trace['traceEvents'] if not
            (e['name'] == 'KeyframeModel' and e['ph'] == 'e' and e.get('id2') == {'local': '0xc6'}
             and e['ts'] < 202000000)]
        self.reject('END/impl terminal coverage is inconsistent')

    def test_unrelated_model_completion_is_rejected(self):
        for e in self.trace['traceEvents']:
            if e['name'] == 'KeyframeModel' and e['ph'] == 'e' and e.get('id2') == {'local': '0xc6'}:
                e['ts'] -= 100000
        self.reject('boundary/state|completions disagree')

    def test_two_models_in_different_host_updates_are_not_a_pair(self):
        self.trace['traceEvents'] = [e for e in self.trace['traceEvents'] if not
            (e['name'] == 'AnimationHost::UpdateAnimationState' and e['ts'] == 201024795)]
        self.reject('one unambiguous compositor host update')

    def test_wrong_direction_on_either_player_is_rejected(self):
        for value in self.motion['geometry'].values():
            for row in value['startup']['events']:
                if row['generation'] == 16 and row['event'] == 'players-paused':
                    row['shade']['playbackRate'] = 1
        self.reject('direction/endpoint')

    def test_changed_dom_pair_between_themes_is_rejected(self):
        for e in self.trace['traceEvents']:
            if e['name'] == 'Animation' and e['ph'] == 'b' and 202020000 < e['ts'] < 202030000:
                e['args']['data']['nodeId'] += 100
        self.reject('Blink target pair changed')

    def test_trace_loss_or_incomplete_finalization_is_never_accepted(self):
        for key, value in [('complete', False), ('dataLossOccurred', True), ('limitedEvents', 1),
                           ('errors', ['drain timeout']), ('reason', 'verification-error')]:
            with self.subTest(field=key):
                trace, motion = observed_schema_fixture()
                trace['mouseMotionTrace'][key] = value
                sync_counts(trace, motion)
                with self.assertRaises(GATE.MotionTraceError):
                    GATE.verify_trace_data(trace, motion)

    def test_missing_or_duplicate_anchor_is_rejected(self):
        anchor = next(e for e in self.trace['traceEvents'] if e['name'] == 'mouse627.motion.arm-dark-closing')
        self.trace['traceEvents'].remove(anchor)
        self.reject('renderer mark anchor')
        self.trace['traceEvents'].extend([anchor, copy.deepcopy(anchor)])
        self.reject('renderer mark anchor')

    def test_clock_disagreement_is_rejected_instead_of_widening_windows(self):
        next(e for e in self.trace['traceEvents'] if e['name'] == 'mouse627.motion.after')['ts'] += 10000
        self.reject('clock anchors disagree')

    def test_two_json_double_serializations_of_the_same_anchor_match(self):
        row = next(e for e in self.trace['traceEvents'] if e['name'] == 'mouse627.motion.before')
        row['args']['data']['startTime'] += 0.00000000001
        self.assertEqual(GATE.verify_trace_data(self.trace, self.motion)['status'], 'pass')

    def test_event_order_does_not_change_the_lifetime_result(self):
        self.trace['traceEvents'].reverse()
        self.assertEqual(GATE.verify_trace_data(self.trace, self.motion)['status'], 'pass')

    def test_different_diagnostics_or_stale_summary_are_rejected(self):
        diagnostics = {k: copy.deepcopy(self.motion[k]) for k in ('version', 'frames', 'geometry')}
        GATE.verify_trace_data(self.trace, self.motion, diagnostics)
        diagnostics['geometry']['reduced']['startup']['current']['performanceNow'] += 1
        with self.assertRaisesRegex(GATE.MotionTraceError, 'diagnostics disagree'):
            GATE.verify_trace_data(self.trace, self.motion, diagnostics)
        self.motion['trace']['eventCount'] += 1
        with self.assertRaisesRegex(GATE.MotionTraceError, 'different/incomplete trace metadata'):
            GATE.verify_trace_data(self.trace, self.motion)

    def test_path_api_reads_actual_inputs_and_missing_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            trace, motion = Path(directory) / 'trace.json', Path(directory) / 'motion.json'
            trace.write_text(json.dumps(self.trace)); motion.write_text(json.dumps(self.motion))
            self.assertEqual(GATE.verify_trace(trace, motion)['status'], 'pass')
            trace.unlink()
            with self.assertRaises(GATE.MotionTraceError):
                GATE.verify_trace(trace, motion)


if __name__ == '__main__':
    unittest.main()
