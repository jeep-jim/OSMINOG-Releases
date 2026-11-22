#!/usr/bin/env python3
"""Bind legacy629 completion, two display processes and actual workload displays."""
import hashlib
import json
import math
import struct


def need(value, message):
    if not value:
        raise ValueError('Mouse637 Windows display: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def document(read, name):
    raw = read(name)
    need(isinstance(raw, bytes) and 0 < len(raw) <= 4 * 1024**2, 'missing/oversized ' + name)
    value = json.loads(raw.decode('utf-8-sig'))
    need(isinstance(value, dict), 'invalid ' + name)
    return raw, value


def process(value, name):
    need(isinstance(value, dict) and type(value.get('pid')) is int and value['pid'] > 0
         and type(value.get('exitCode')) is int and value['exitCode'] == 0, name + ' process failed')
    start, finish = value.get('startedAtMs'), value.get('finishedAtMs')
    need(all(type(v) in (int, float) and math.isfinite(v) for v in (start, finish))
         and 0 <= start < finish, name + ' process chronology missing')
    return start, finish


def verify(read, report):
    checks = report.get('checks', {})
    legacy = checks.get('versionUpgrade', {})
    need(legacy.get('ok') is True and (legacy.get('fromVersion'), legacy.get('toVersion')) == ('6.0.29', '6.0.37'),
         'complete legacy629 replacement missing')
    sequence = []
    for key in ('oldWrite', 'replacement', 'newRead'):
        sequence.append((key, process(legacy.get(key), key)))
    for phase, key, digest, version in (('write', 'oldWrite', 'oldReportSha256', '6.0.29'),
                                        ('read', 'newRead', 'newReportSha256', '6.0.37')):
        raw, value = document(read, 'mouse-631-upgrade/mouse-windows-smoke-' + phase + '.json')
        need(sha(raw) == legacy.get(digest) and value.get('ok') is True
             and (value.get('version'), value.get('platform'), value.get('arch'), value.get('mode')) == (version, 'win32', 'x64', phase)
             and value.get('pid') == legacy[key]['pid'], 'legacy ' + phase + ' report/process binding differs')
    need(legacy['oldWrite']['pid'] != legacy['newRead']['pid'], 'legacy restart reused its process')

    preparation = checks.get('displayPreparation', {})
    need(preparation.get('ok') is True and preparation.get('report') == 'mouse-637-display.json', 'preparation missing')
    raw, receipt = document(read, preparation['report'])
    need(sha(raw) == preparation.get('reportSha256') and receipt.get('ok') is True and not receipt.get('error')
         and (receipt.get('schema'), receipt.get('version'), receipt.get('platform'), receipt.get('scope')) == (1, '6.0.37', 'win32', 'session')
         and receipt.get('source') == 'User32 advertised display modes'
         and receipt.get('minimum') == {'width': 1440, 'height': 900}
         and receipt.get('processExitVerified') is True, 'successful exact display receipt missing')
    for phase, marker in (('prepare', 'MOUSE_637_WINDOWS_DISPLAY_PREPARED'),
                          ('verify', 'MOUSE_637_WINDOWS_DISPLAY_PERSISTENCE_PASS')):
        child = preparation.get(phase)
        sequence.append((phase, process(child, phase)))
        name = 'mouse-637-display-' + phase + '.log'
        need(child.get('log') == name and child.get('requiredMarkers') == [marker], phase + ' log/marker identity differs')
        log = read(name)
        need(isinstance(log, bytes) and sha(log) == child.get('logSha256')
             and marker in log.decode('utf-8-sig').splitlines(), phase + ' actual log differs')
    persistence = receipt.get('persistence', {})
    need(receipt.get('pid') == preparation['prepare']['pid']
         and persistence.get('pid') == preparation['verify']['pid']
         and receipt['pid'] != persistence['pid'], 'two actual independent display processes missing')
    sequence.append(('baselinePerformance', process(checks.get('baselinePerformance'), 'baselinePerformance')))
    need(all(before[1][1] <= after[1][0] for before, after in zip(sequence, sequence[1:])),
         'required legacy WRITE/replacement/READ -> prepare -> verify -> baseline order differs')
    # These receipts already exist for the mandatory current workloads. Their
    # independent content/pixel gates remain responsible for their full proof.
    for key in ('updateFrom636', 'freshUpgrade', 'taskAndFiftyTabs', 'ownerFeedback636'):
        start, _finish = process(checks.get(key), key)
        need(start >= sequence[-1][1][1], key + ' started before the baseline finished')
    for phase in ('write', 'read'):
        start, _finish = process(checks.get('features637', {}).get(phase), 'features637 ' + phase)
        need(start >= sequence[-1][1][1], 'current features started before the baseline finished')

    selected, actual = receipt.get('selected'), persistence.get('actual', {})
    need(isinstance(selected, dict) and selected in receipt.get('advertisedModes', [])
         and actual.get('device') == receipt.get('device') == receipt.get('after', {}).get('device'),
         'selected display was not actually advertised or persisted')
    for snapshot in (receipt.get('after', {}), actual):
        need(all(snapshot.get('mode', {}).get(key) == selected.get(key)
                 for key in ('width', 'height', 'bitDepth', 'frequency', 'flags', 'orientation')),
             'actual mode differs from selected mode')
        bounds = snapshot.get('logicalBounds', {})
        need(type(bounds.get('width')) in (int, float) and bounds['width'] >= 1440
             and type(bounds.get('height')) in (int, float) and bounds['height'] >= 900,
             'actual logical display is too small')
    if receipt.get('changed') is True:
        need(receipt.get('configuration') == {'test': 0, 'flags': 0, 'registryUpdated': False, 'applied': 0},
             'mode was not tested/applied only for the session')
    else:
        need(receipt.get('changed') is False, 'display change state missing')

    displays = []
    for prefix, version in (('mouse-637-baseline-performance/', '6.0.36'), ('', '6.0.37')):
        _raw, geometry = document(read, prefix + 'mouse-631-stress-geometry.json')
        display = geometry.get('display', {})
        need(geometry.get('version') == version and geometry.get('name') == 'stress'
             and display.get('bounds') == actual.get('logicalBounds')
             and display.get('workArea') == actual.get('logicalWorkArea')
             and display.get('scaleFactor') == actual.get('scaleFactor'),
             version + ' actual workload display differs from verified mode')
        png = read(prefix + 'mouse-631-stress-50-switch-1-display.png')
        need(isinstance(png, bytes) and len(png) >= 33 and png[:8] == b'\x89PNG\r\n\x1a\n'
             and png[8:16] == b'\0\0\0\rIHDR'
             and struct.unpack('>II', png[16:24]) == (selected['width'], selected['height']),
             version + ' actual full-screen PNG dimensions differ')
        displays.append(display)
    need(displays[0] == displays[1], 'published636 and current637 used different displays')
    return {'ok': True, 'reportSHA256': sha(raw), 'sequence': [name for name, _times in sequence],
            'independentProcesses': True, 'workloadDisplay': displays[0]}
