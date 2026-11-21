#!/usr/bin/env python3
"""Bind the actual636 process to inline settings, removed search and faster desks."""
from pathlib import Path
import re
import runpy

def module(name):
    return runpy.run_path(str(Path(__file__).with_name(name)))

N = module('mouse636-native-evidence.py')
L = module('mouse636-library-evidence.py')
A = module('mouse636-agent-inline-evidence.py')
D = module('mouse636-pane-layout-evidence.py')
S = module('mouse636-search-removal-evidence.py')
P = module('mouse636-performance-evidence.py')
need, sha = N['need'], N['sha']
NAME = 'mouse-636-owner-feedback.json'
MARKERS = ['MOUSE_635_LIBRARY_STABLE_PASS', A['MARKER'], 'MOUSE_636_PINNED_PANES_PASS',
           S['MARKER'], P['MARKER'], 'MOUSE_636_OWNER_FEEDBACK_PASS']


def verify(read, *, expected_platform=None, expected_arch=None):
    evidence = N['Evidence'](read)
    raw, facts = evidence.json(NAME)
    platform, arch, pid = facts.get('platform'), facts.get('arch'), facts.get('pid')
    need((platform, arch) in (('darwin', 'arm64'), ('win32', 'x64'), ('linux', 'x64'))
         and (expected_platform is None or platform == expected_platform)
         and (expected_arch is None or arch == expected_arch), 'owner636 installed target differs')
    need(facts.get('schema') == 1 and facts.get('version') == '6.0.36' and N['positive'](pid)
         and facts.get('budgetMs') == 240000 and N['finite'](facts.get('elapsedMs'))
         and 0 < facts['elapsedMs'] <= 240000, 'owner636 actual process identity/budget missing')
    N['flags'](facts, ('ok', 'packaged', 'profileIsolated', 'restored'), 'owner636 did not finish and restore')
    need(facts.get('stage') == 'complete' and facts.get('source') ==
         'Installed native UI, retained document identity, real local fixture requests, and same-run desktop performance'
         and facts.get('physicalUserDeviceVerified') is False and not facts.get('error')
         and not facts.get('cleanupErrors') and not facts.get('failureCaptureError'), 'owner636 failed or overstated scope')
    log = read('mouse-636-owner-feedback.log')
    need(isinstance(log, bytes) and 0 < len(log) <= 16 * 1024**2, 'owner636 actual process log missing')
    lines = log.decode('utf-8').splitlines()
    need(all(marker in lines for marker in MARKERS), 'owner636 mandatory native behavior marker missing')
    if platform in ('win32', 'linux'):
        _, wrapper = evidence.json('mouse-' + ('windows' if platform == 'win32' else 'linux') + '-verification.json')
        process = wrapper.get('checks', {}).get('ownerFeedback636', {})
        need(process.get('exitCode') == 0 and process.get('pid') == pid and N['finite'](process.get('elapsedMs'))
             and 0 < process['elapsedMs'] <= 270000 and process.get('requiredMarkers') == MARKERS
             and process.get('reportSha256') == sha(raw), 'owner636 wrapper/process/raw report binding differs')
        if platform == 'linux':
            need(process.get('log') == 'mouse-636-owner-feedback.log' and process.get('logSha256') == sha(log),
                 'owner636 actual Linux log bytes differ')
    else:
        returned = [re.fullmatch(r'MOUSE_NATIVE_PROCESS_RETURN pid=(\d+) code=(\d+) elapsedMs=(\d+)', line) for line in lines]
        returned = [row for row in returned if row]
        need(len(returned) == 1 and int(returned[0][1]) == pid and int(returned[0][2]) == 0
             and 0 < int(returned[0][3]) <= 270000, 'owner636 actual macOS process exit receipt missing')
    cleanup = facts.get('cleanup', {})
    N['flags'](cleanup, ('restored', 'desktopStateRestored'), 'owner636 original workspace did not restore')
    need(all(type(cleanup.get(key)) is int and cleanup[key] >= 0 for key in ('ownedPagesClosed', 'originalPagesPreserved')),
         'owner636 original/fixture page accounting missing')
    native = facts.get('nativeInputs')
    need(isinstance(native, list) and 20 <= len(native) <= 100, 'owner636 actual input ledger missing')
    for row in native:
        N['input_event'](row, platform, row.get('selector'))
    library = L['verify'](read, expected_platform=platform, expected_arch=arch, owner=facts)
    agent = A['verify'](read, owner=facts)
    panes = D['verify'](read, owner=facts)
    search = S['verify'](read, owner=facts)
    performance = P['verify'](read, owner=facts)
    captures = facts.get('captures', [])
    expected = [row['filename'] for row in facts['library']['captures']] + A['CAPTURES'] + D['CAPTURES'] + search['canonicalCaptures']
    need([row.get('filename') for row in captures] == expected and len(set(expected)) == len(expected)
         and captures[:8] == facts['library']['captures'], 'owner636 actual native frame ledger differs from its child reports')
    inputs = {NAME: sha(raw), 'mouse-636-owner-feedback.log': sha(log)}
    for result in (library, agent, panes, search, performance):
        inputs.update(result['inputs'])
    return {'ok': True, 'version': '6.0.36', 'platform': platform, 'arch': arch, 'pid': pid,
            'reportSha256': sha(raw), 'nativeInputSource': N['source'](platform), 'library': library,
            'agentInline': agent, 'paneLayout': panes, 'searchRemoval': search, 'performance': performance,
            'inputs': inputs, 'nativeCaptures': library['nativeCaptures'] + agent['nativeCaptures'] + panes['nativeCaptures'] + search['nativeCaptures'],
            'canonicalCaptures': expected, 'physicalUserDeviceVerified': False}
