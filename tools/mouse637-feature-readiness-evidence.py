#!/usr/bin/env python3
"""Additive Mac publisher gate for the explicitly adapted CI fixture driver.

This does not replace or reinterpret any existing source=False native gate.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re

SOURCE = '0021084ccb9537e657d21e6f0c8e812dee6b461f'
VERSION = '6.0.37'
ORIGINAL_SHA = 'a87573de7ebf2c380dffeaf64246739d68d3b3d8308dca424a90512174e0fd7d'
ORIGINAL_BLOB = 'ad6301bbf4d873a199fed6d26b7cfb7861ff0a6f'
ADAPTED_SHA = 'f51b604dcd72b48081b33932718f6a7e185d9bc4e3a13bb9e55718d0de3f7b07'
MAIN_SHA = 'f3c9ba7794cb5c659c75fdc981faeda6b45851ceb0e70b61291128a04387914f'
VERIFIER_SHA = '2f662f0de5d81a8013f77ef9cf24262eb50e96df2cfdd59eeb02691fddb22dc7'
ASAR_SHA = '62b5472c62e475b28935b110330a602311fa8227b79666f375269fcdc8eb260e'
OBSERVATIONS = ['owned-id-and-requested-label-before-click',
                'owned-id-unpin-label-and-original-one-pin-count-after-russian-pin']
COMPONENTS = {'Contents/MacOS/Mouse Browser', 'Contents/Resources/app.asar',
              'Contents/Resources/app.asar.unpacked/mouse-native-menu.node',
              'Contents/Resources/app.asar.unpacked/mouse-screen-capture.node'}


def need(value, message):
    if not value:
        raise ValueError('Mouse637 feature readiness: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def number(value):
    return type(value) in (float, int) and math.isfinite(value)


def positive_pid(value):
    return type(value) is int and value > 0


def verify(directory, *, tools_root=None, publisher_sha=None):
    directory = Path(directory)
    tools_root = Path(tools_root) if tools_root is not None else Path(__file__).parent
    publisher_sha = publisher_sha or os.environ.get('GITHUB_SHA')
    need(isinstance(publisher_sha, str) and re.fullmatch('[0-9a-f]{40}', publisher_sha), 'exact publisher SHA required')
    inputs = {}

    def raw(name):
        need(Path(name).name == name, 'evidence filename must be local')
        file = directory / name
        need(file.is_file() and not file.is_symlink(), 'missing regular evidence: ' + name)
        value = file.read_bytes()
        inputs[name] = sha(value)
        return value

    def read(name):
        return json.loads(raw(name))

    summary = read('mouse-637-feature-readiness-summary.json')
    need(summary.get('schema') == 1 and summary.get('kind') == 'mouse637-external-feature-readiness'
         and summary.get('ok') is True and summary.get('source') == SOURCE and summary.get('version') == VERSION
         and summary.get('publisherSHA') == publisher_sha and (summary.get('platform'), summary.get('arch')) == ('darwin', 'arm64'),
         'summary identity or success differs')
    need(summary.get('verifierSha256') == VERIFIER_SHA, 'original verifier bytes differ')
    for field, name in [('wrapperSha256', 'mouse637-feature-readiness.py'), ('controllerSha256', 'mouse637-feature-readiness.cjs')]:
        need(summary.get(field) == sha((tools_root / name).read_bytes()), 'reviewed publisher tool differs: ' + name)
    need(sha(raw('mouse-637-feature-readiness-original.cjs')) == ORIGINAL_SHA and
         sha(raw('mouse-637-feature-readiness-adapted.cjs')) == ADAPTED_SHA, 'actual compiled source evidence differs')
    need(hashlib.sha1(b'blob ' + str(len(raw('mouse-637-feature-readiness-original.cjs'))).encode() + b'\0' +
                     raw('mouse-637-feature-readiness-original.cjs')).hexdigest() == ORIGINAL_BLOB, 'packaged source Git blob differs')
    executable, app_path, profile = (summary.get(k) for k in ('executable', 'appPath', 'profile'))
    need(all(isinstance(x, str) and x.startswith('/') for x in (executable, app_path, profile)), 'owned absolute paths missing')
    need(app_path == str(Path(executable).parent.parent / 'Resources/app.asar') and
         Path(executable).name == 'Mouse Browser' and Path(profile).name == 'features637', 'owned installed/profile layout differs')
    before, after = summary.get('before', {}), summary.get('after', {})
    need(before.get('components') == after.get('components') and set(before.get('components', {})) == COMPONENTS,
         'installed executable/ASAR/native bytes changed or incomplete')
    native_names = sorted(name for name in COMPONENTS if name.endswith('.node'))
    for state in (before, after):
        need(state.get('nativeInventory') == native_names, 'native addon inventory differs')
        for entry in state['components'].values():
            need(type(entry.get('size')) is int and entry['size'] > 0 and
                 isinstance(entry.get('sha256'), str) and re.fullmatch('[0-9a-f]{64}', entry['sha256']), 'invalid component byte observation')
        need(state['components']['Contents/Resources/app.asar']['sha256'] == ASAR_SHA, 'installed ASAR is not accepted source002')
    for label, state in [('before', before), ('after', after)]:
        code = state.get('codesign', {})
        name = 'mouse-637-feature-readiness-codesign-' + label + '.log'
        need(code.get('exitCode') == 0 and code.get('command') == ['codesign', '--verify', '--deep', '--strict']
             and code.get('log') == name and code.get('logSha256') == sha(raw(name)), 'actual strict codesign receipt differs')
    rows = summary.get('launches', [])
    need(len(rows) == 2 and [row.get('phase') for row in rows] == ['write', 'read'], 'both actual feature launches required')
    processes = read('mouse-637-features-processes.json')
    final_raw = raw('mouse-637-features.json')
    final = json.loads(final_raw)
    need(processes.get('reportSha256') == sha(final_raw), 'final feature process binding differs')
    nonces, pids = set(), set()
    for row, phase, flag, limit, marker, report_name in zip(rows, ('write', 'read'),
            ('--mouse-637-features-smoke', '--mouse-637-features-restore-read'), (270000, 120000),
            ('MOUSE_637_FEATURES_WRITE_PASS', 'MOUSE_637_FEATURES_NATIVE_PASS'),
            ('mouse-637-features-write.json', 'mouse-637-features.json')):
        nonce, pid, controller_pid, port = (row.get(key) for key in ('nonce', 'pid', 'controllerPid', 'port'))
        need(isinstance(nonce, str) and re.fullmatch('[0-9a-f]{64}', nonce) and nonce not in nonces,
             'fresh phase nonce missing or repeated')
        need(positive_pid(pid) and pid not in pids and positive_pid(controller_pid) and controller_pid != pid and
             type(port) is int and 0 < port < 65536,
             'actual child/controller/port identities differ')
        nonces.add(nonce); pids.add(pid)
        need(row.get('flag') == flag and row.get('profile') == profile and row.get('originalArgv') == [executable, flag]
             and row.get('argv') == [executable, '--inspect-brk=127.0.0.1:' + str(port), flag]
             and row.get('addedEnvironment') == {'MOUSE_637_FEATURE_READINESS_NONCE': nonce}, 'scoped original launch differs')
        need(row.get('controllerExitCode') == 0 and number(row.get('bootstrapElapsedMs')) and
             0 <= row['bootstrapElapsedMs'] <= 30000 and not row.get('bootstrapError'), 'bounded controller did not succeed')
        prefix = 'mouse-637-feature-readiness-'
        names = {'receipt': prefix + phase + '.json', 'controllerReceipt': prefix + 'controller-' + phase + '.json',
                 'config': prefix + 'config-' + phase + '.json', 'controllerLog': prefix + 'controller-' + phase + '.log'}
        for key, name in names.items():
            need(row.get(key) == name and row.get(key + 'Sha256') == sha(raw(name)), 'controller artifact binding differs: ' + key)
        receipt, control, config = (read(names[key]) for key in ('receipt', 'controllerReceipt', 'config'))
        expected = {'schema': 1, 'kind': 'mouse637-publisher-fixture-readiness', 'source': SOURCE, 'version': VERSION,
                    'phase': phase, 'flag': flag, 'pid': pid, 'controllerPid': controller_pid, 'nonce': nonce,
                    'executable': executable, 'appPath': app_path, 'profile': profile,
                    'target': app_path + '/mouse-637-features-smoke.cjs', 'platform': 'darwin', 'arch': 'arm64',
                    'originalSha256': ORIGINAL_SHA, 'originalGitBlob': ORIGINAL_BLOB, 'adaptedSha256': ADAPTED_SHA,
                    'mainSha256': MAIN_SHA, 'applications': 1, 'observations': OBSERVATIONS, 'loaderRestored': True,
                    'inspectorClosed': True, 'inspectorUrl': None, 'receiptBeforeFixtureInvocation': True}
        need(all(receipt.get(key) == value and type(receipt.get(key)) is type(value) for key, value in expected.items()),
             'owned in-process fixture receipt differs')
        need(isinstance(receipt.get('versions'), dict) and receipt['versions'].get('electron') == '44.5.0'
             and isinstance(receipt['versions'].get('node'), str), 'actual embedded runtime identity missing')
        need(all(config.get(k) == v for k, v in {'schema': 1, 'phase': phase, 'flag': flag, 'pid': pid, 'nonce': nonce,
             'port': port, 'executable': executable, 'appPath': app_path, 'profile': profile}.items()), 'bootstrap config identity differs')
        need(number(row.get('bootstrapStartedAt')) and config.get('deadlineEpochMs') == row['bootstrapStartedAt'] + 30000,
             'bootstrap deadline differs from original launch observation')
        need(number(control.get('startedAt')) and number(control.get('finishedAt')) and
             0 <= control['finishedAt'] - control['startedAt'] <= 30000, 'controller observed duration differs')
        need(config.get('output') == summary.get('output') and config.get('receipt') == summary['output'] + '/' + names['receipt']
             and config.get('controllerReceipt') == summary['output'] + '/' + names['controllerReceipt'], 'bootstrap output scope differs')
        need(control.get('schema') == 1 and control.get('ok') is True and control.get('phase') == phase
             and control.get('pid') == pid and control.get('controllerPid') == controller_pid and control.get('nonce') == nonce
             and control.get('port') == port and control.get('host') == '127.0.0.1' and control.get('serverUnavailable') is True
             and control.get('receiptSha256') == sha(raw(names['receipt']))
             and control.get('controllerSha256') == summary['controllerSha256'], 'owned inspector shutdown proof differs')
        process = processes.get(phase, {})
        log_name = 'mouse-637-features-' + phase + '.log'
        log = raw(log_name)
        native_raw = raw(report_name)
        native = json.loads(native_raw)
        need(process.get('pid') == pid and process.get('exitCode') == 0 and number(process.get('elapsedMs'))
             and 0 < process['elapsedMs'] <= limit and process.get('requiredMarkers') == [marker]
             and process.get('log') == log_name and process.get('logSha256') == sha(log)
             and process.get('report') == report_name and process.get('reportSha256') == sha(native_raw),
             'original actual Electron process/report/log binding differs')
        lines = log.decode('utf-8').splitlines()
        need(marker in lines, 'original native success marker missing')
        hook_rows = [json.loads(line.split(' ', 1)[1]) for line in lines if line.startswith('MOUSE_637_FEATURE_READINESS_ADAPTER ')]
        need(hook_rows == [receipt], 'actual native log must contain exactly its adapter receipt')
        phase_pid = native.get('pid') if phase == 'write' else native.get('restart', {}).get('pid')
        need(phase_pid == pid, 'feature facts belong to another actual process')
        first = next((entry for entry in native.get('nativeInputs', []) if entry.get('pid') == pid), None)
        need(first is not None and number(first.get('at')) and number(receipt.get('closedAt'))
             and number(receipt.get('compiledAt')) and receipt['closedAt'] <= receipt['compiledAt'] <= first['at'],
             'inspector/loader completion must precede actual native input')
    return {'schema': 1, 'ok': True, 'source': SOURCE, 'publisherSHA': publisher_sha,
            'gate': 'mouse637-external-feature-readiness-v1', 'observations': OBSERVATIONS,
            'inputs': inputs, 'nativePids': sorted(pids), 'originalNativeGatesRemainRequired': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.directory)
    with (args.directory / 'mouse-637-feature-readiness-independent.json').open('x', encoding='utf-8') as target:
        json.dump(result, target, indent=2, allow_nan=False)
        target.write('\n')
    print('MOUSE_637_EXTERNAL_FEATURE_READINESS_EVIDENCE_PASS')
