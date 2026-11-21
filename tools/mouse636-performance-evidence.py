#!/usr/bin/env python3
"""Recompute636 comparisons from both real installed stress runs and raw PNGs."""
import math
from pathlib import Path
import re
import runpy

N = runpy.run_path(str(Path(__file__).with_name('mouse636-native-evidence.py')))
U = runpy.run_path(str(Path(__file__).with_name('mouse636-upgrade-evidence.py')))
need, finite, sha = N['need'], N['finite'], N['sha']
NAME = 'mouse-636-performance.json'
MARKER = 'MOUSE_636_PERFORMANCE_PASS'
FOLDER = 'mouse-636-baseline-performance'
CRITERIA = {'p95MaxMs': 250, 'maxMaxMs': 600, 'medianMustImprove': True}
SOURCES = {'darwin': '0d4a1390fced54b59c2cf7b49c9d9394549456ac',
           'win32': 'bc4cafb5c2db9cfc80165a7c470c813f0235cd04',
           'linux': 'bc4cafb5c2db9cfc80165a7c470c813f0235cd04'}
MARKERS = ['MOUSE_631_TASK_ONLY_NATIVE_PASS', 'MOUSE_631_FIFTY_TABS_FIVE_DESKTOPS_NATIVE_PASS',
           'MOUSE_631_INSTALLED_TASK_STRESS_PASS', 'MOUSE_632_STATIONARY_MEDIA_PASS']


def distribution(values):
    need(isinstance(values, list) and values and all(finite(value) and value >= 0 for value in values),
         'raw timing samples are absent or invalid')
    ordered = sorted(values)
    return {'count': len(values), 'min': ordered[0], 'p50': ordered[math.floor((len(values)-1)*.5)],
            'p95': ordered[math.floor((len(values)-1)*.95)], 'max': ordered[-1]}


def stages(report, candidate):
    rows = report.get('stages', [])
    need([row.get('ownedPageCount') for row in rows] == [20, 50], 'performance workloads differ')
    output = []
    for row, count in zip(rows, (5, 10)):
        need(row.get('deskCount') == 5 and row.get('switchCount') == count
             and len(row.get('switches', [])) == count, 'performance switch/desktop counts differ')
        samples = [value.get('elapsedMs') for value in row['switches']]
        calculated = distribution(samples)
        need(row.get('switchLatencyMs') == calculated, 'reported percentiles differ from actual samples')
        if candidate:
            need(row.get('mainEventLoop') == distribution(row.get('mainEventLoopSamplesMs'))
                 and row.get('renderer', {}).get('gapDistribution') == distribution(row.get('renderer', {}).get('gaps')),
                 'candidate renderer/main-loop samples differ from their summaries')
        output.append({'ownedPageCount': row['ownedPageCount'], 'deskCount': 5, 'switchCount': count,
                       'switchLatencyMs': calculated, 'switchSamplesMs': samples,
                       'switchCaptures': sum(value['counts']['capturePage'] for value in row['switches']),
                       'mainEventLoop': row['mainEventLoop'],
                       **({'mainEventLoopSamplesMs': row['mainEventLoopSamplesMs']} if candidate else {}),
                       'renderer': row['renderer']})
    return output


def compare(baseline, candidate):
    old, new = stages(baseline, False), stages(candidate, True)
    rows = []
    for before, after in zip(old, new):
        need(0 < after['switchLatencyMs']['p50'] < before['switchLatencyMs']['p50'],
             'median must improve against the actual predecessor on this runner')
        need(after['switchCaptures'] == 0 and before['switchCaptures'] > 0,
             'candidate must eliminate predecessor snapshot work')
        rows.append({'ownedPageCount': after['ownedPageCount'], 'deskCount': 5,
                     'switchCount': after['switchCount'], 'baseline': before, 'candidate': after,
                     'medianRatio': before['switchLatencyMs']['p50'] / after['switchLatencyMs']['p50']})
    need(rows[1]['candidate']['switchLatencyMs']['p95'] <= CRITERIA['p95MaxMs']
         and rows[1]['candidate']['switchLatencyMs']['max'] <= CRITERIA['maxMaxMs'],
         'fifty-page native switch exceeds the fixed250/600ms performance budget')
    return rows


def verify(read, *, owner):
    evidence = N['Evidence'](read)
    raw, facts = evidence.json(NAME)
    platform, arch = owner.get('platform'), owner.get('arch')
    need(owner.get('performance') == {**facts, 'reportFile': NAME, 'reportSha256': sha(raw)}
         and facts.get('pid') == owner.get('pid') and facts.get('platform') == platform
         and facts.get('arch') == arch and facts.get('version') == '6.0.36',
         'performance owner/report identity or bytes differ')
    need(facts.get('schema') == 1 and facts.get('ok') is True and not facts.get('error')
         and facts.get('kind') == 'installed-desktop-performance-comparison'
         and facts.get('source') == 'Exact published predecessor and candidate installed processes on the same native CI runner'
         and facts.get('physicalUserDeviceVerified') is False
         and facts.get('percentileMethod') == 'sorted[floor((count-1)*quantile)]'
         and facts.get('criteria') == CRITERIA, 'performance scope, algorithm or fixed budget differs')
    files = {'baselineEnvelope': FOLDER + '.json', 'baselineStress': FOLDER + '/mouse-631-stress.json',
             'candidateStress': 'mouse-631-stress.json', 'candidateNative': 'mouse-631-native.json'}
    reports, inputs = {}, {NAME: sha(raw)}
    need(set(facts.get('sourceReports', {})) == set(files), 'performance raw source reports missing')
    for key, name in files.items():
        data, value = evidence.json(name)
        need(facts['sourceReports'][key] == {'filename': name, 'bytes': len(data), 'sha256': sha(data)},
             'performance source bytes differ: ' + name)
        reports[key], inputs[name] = value, sha(data)
    envelope, native = reports['baselineEnvelope'], reports['candidateNative']
    old_version = U['old_version'](platform)
    baseline = U['BASELINES'][platform]['deb'] if platform == 'linux' else U['BASELINES'][platform]
    baseline = {**baseline, 'url': 'https://github.com/jeep-jim/OSMINOG-Releases/releases/download/' + baseline['tag'] + '/' + baseline['name']}
    need(envelope.get('schema') == 1 and envelope.get('kind') == 'published-baseline-stress-run'
         and envelope.get('version') == '6.0.36' and envelope.get('baselineVersion') == old_version
         and envelope.get('platform') == platform and envelope.get('arch') == arch
         and envelope.get('baseline') == baseline and envelope.get('baselineSource') == SOURCES[platform]
         and envelope.get('ok') is True and not envelope.get('error')
         and envelope.get('rawDirectory') == FOLDER and envelope.get('physicalUserDeviceVerified') is False,
         'baseline must be the exact released predecessor in this native run')
    process, runner = envelope.get('process', {}), envelope.get('runner', {})
    need(process.get('exitCode') == 0 and N['positive'](process.get('pid'))
         and process['pid'] != native.get('pid') and process.get('budgetMs') == 400000
         and finite(process.get('elapsedMs')) and 0 < process['elapsedMs'] <= 400000
         and process.get('requiredMarkers') == MARKERS, 'baseline process receipt missing')
    need(all(isinstance(runner.get(key), str) and runner[key] for key in
             ('runId', 'runAttempt', 'job', 'workflow', 'sha', 'host', 'system', 'machine'))
         and re.fullmatch('[0-9a-f]{40}', runner['sha']) and 'display' in runner,
         'actual baseline runner identity missing')
    need(facts.get('baseline') == {'version': old_version, 'source': SOURCES[platform],
         'package': baseline, 'process': process, 'runner': runner}
         and facts.get('candidate') == {'version': '6.0.36', 'pid': native.get('pid'), 'source': runner['sha']},
         'comparison must use the same recorded runner and exact processes')
    inventory = envelope.get('files', {})
    need(isinstance(inventory, dict) and inventory, 'raw predecessor inventory absent')
    for name, expected in inventory.items():
        need(re.fullmatch(FOLDER + r'/mouse-(?:631|632)-[a-z0-9-]+\.(?:json|png|log)', name), 'unsafe baseline evidence path')
        data = read(name)
        need(isinstance(data, bytes) and 0 < len(data) <= 64 * 1024**2
             and expected == {'size': len(data), 'sha256': sha(data)}, 'baseline archived bytes differ: ' + name)
        inputs[name] = sha(data)
    prefix = lambda name: read(FOLDER + '/' + name)
    baseline_raw, baseline_native = evidence.json(FOLDER + '/mouse-631-native.json')
    need(baseline_native.get('pid') == process['pid'] and baseline_native.get('ok') is True
         and baseline_native.get('budgetMs') == 350000 and baseline_native.get('version') == old_version,
         'baseline wrapper belongs to another process')
    log = prefix('mouse-631-native.log')
    need(sha(log) == process.get('logSha256') and all(marker in log.decode('utf-8').splitlines() for marker in MARKERS),
         'baseline native log/markers differ')
    old = runpy.run_path(str(Path(__file__).with_name('mouse' + ('635' if platform == 'darwin' else '634') + '-task-evidence.py')))
    old['verify'](prefix, expected_platform=platform, expected_arch=arch)
    current = runpy.run_path(str(Path(__file__).with_name('mouse636-task-evidence.py')))
    current['verify'](read, expected_platform=platform, expected_arch=arch)
    calculated = compare(reports['baselineStress'], reports['candidateStress'])
    need(facts.get('stages') == calculated, 'saved performance comparison does not match raw measurements')
    need(facts.get('checks') == dict.fromkeys(('sameRunner', 'workloadMatched', 'zeroSwitchCaptures',
         'medianImproved', 'p95WithinBudget', 'maxWithinBudget', 'restored'), True), 'performance comparison did not complete')
    return {'ok': True, 'reportSha256': sha(raw), 'stages': calculated, 'inputs': inputs,
            'physicalUserDeviceVerified': False, 'sameRunner': runner}
