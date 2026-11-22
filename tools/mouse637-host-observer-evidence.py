#!/usr/bin/env python3
"""Read bounded external host observations without replacing release gates.

This reader executes no native workload and does not call the existing guest,
feature, source=False, publishing or public-channel acceptance gates.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import struct
import subprocess

SOURCE = '0021084ccb9537e657d21e6f0c8e812dee6b461f'
PREFIX = 'mouse-637-host-observer-'
PHASES = ('baseline', 'candidate')
BUDGETS = {'baseline': 900000, 'candidate': 400000}
LIMITS = {'maxOwned': 256, 'maxImages': 512, 'maxRecords': 65536, 'maxOutputBytes': 67108864}
INTERVAL_MS = 250
MAX_LINE_BYTES = 65536
MAX_INPUT_BYTES = 256 * 1024 * 1024
BASELINE_SHA = '7603d348b4a125ecf73bad82e2cf24eb57d17b7b03dac02eb12527552c38eb6e'
PIN_SHA = '4f1466fdf0a8c8d850804d5edca42ddc8bb1cd785b6001bb35a0e5d13e195b09'
TOOLS = ('mouse637-host-observer.c', 'mouse637-host-observer.py',
         'mouse637-host-observer-build.py', 'mouse637-host-observer-evidence.py')
MARKERS = ('MOUSE_631_TASK_ONLY_NATIVE_PASS', 'MOUSE_631_FIFTY_TABS_FIVE_DESKTOPS_NATIVE_PASS',
           'MOUSE_631_INSTALLED_TASK_STRESS_PASS', 'MOUSE_632_STATIONARY_MEDIA_PASS')
COMPONENTS = {
    'Contents/MacOS/Mouse Browser': {'size': 52688, 'sha256': '10265cedd820b04e308d318e236206f963e834329653bcba73b4db85c35ced59'},
    'Contents/Resources/app.asar': {'size': 9731873, 'sha256': '62b5472c62e475b28935b110330a602311fa8227b79666f375269fcdc8eb260e'},
    'Contents/Resources/app.asar.unpacked/mouse-native-menu.node': {'size': 117120, 'sha256': 'af86174cc2d157171e34c0c8dc65ce5c34881cd5fdc459b6f8274dc9749c828d'},
    'Contents/Resources/app.asar.unpacked/mouse-screen-capture.node': {'size': 118912, 'sha256': '808a5852febd89a3d8ecc15cff29805da383ced1f01e6d6a207a2fea0ae95f88'},
}
BASELINE_PACKAGE = {
    'name': 'Mouse-Browser-6.0.36-mac-arm64.dmg', 'tag': 'quadro-macos-v6.0.36-arm64',
    'size': 137981934, 'sha256': '8688b4db4bd8d9541d93508ecdb3260727d9c6a975f336cfcd2b086caae704fb',
    'url': 'https://github.com/jeep-jim/OSMINOG-Releases/releases/download/quadro-macos-v6.0.36-arm64/Mouse-Browser-6.0.36-mac-arm64.dmg',
}
OLD_CODE = {
    'mouse637-guest-input-observer.py': '7fa48d60f514c82eb68a2d775dd06d1b34111a4f423e3b6c66cb81bac82fe517',
    'mouse637-guest-input-observer.cjs': '850ac3505d149319227283dbfa7b5597d7e547de2e0c5c98c8e2c45cdd972b56',
    'mouse637-guest-input-observer-evidence.py': 'cc5858537f77b21d4e5205007ba9c062c0490e6583dfba8151169c7da9b6a2d4',
    'mouse637-feature-readiness.py': '767217ed097c52703f8f8015fa1bf26e43c727447e05c74cfcbc43aaafcc255d',
    'mouse637-feature-readiness.cjs': '41462a9634ea481ad73883eb3039cc3f38af7b37c913272cf455bb73fce2c49b',
    'mouse637-feature-readiness-evidence.py': '177308e85d5d15abc845f0148ab8d4d282ea1d1c8f3a74a38b59f14102e53f84',
    'fixtures/mouse637-readiness-002-verifier.py': '2f662f0de5d81a8013f77ef9cf24262eb50e96df2cfdd59eeb02691fddb22dc7',
    'fixtures/mouse637-host-002-baseline-performance.py': BASELINE_SHA,
}


def need(value, message):
    if not value:
        raise ValueError('Host observer evidence: ' + message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def integer(value, low=0, high=(1 << 64) - 1):
    return type(value) is int and low <= value <= high


def number(value, low=0):
    return type(value) in (int, float) and math.isfinite(value) and value >= low


def hex_sha(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'duplicate JSON key: ' + key)
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError('Host observer evidence: nonfinite JSON value: ' + value)


def json_value(data):
    return json.loads(data.decode('utf-8'), object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)


class Inputs:
    """Only bounded regular files contained in the supplied evidence directory."""

    def __init__(self, directory):
        self.root = Path(directory).resolve(strict=True)
        need(self.root.is_dir(), 'evidence directory missing')
        self.inputs = {}
        self.total = 0

    def read(self, relative, limit=16 * 1024 * 1024):
        need(isinstance(relative, str) and '\x00' not in relative and '\\' not in relative,
             'invalid evidence filename')
        name = PurePosixPath(relative)
        need(not name.is_absolute() and name.parts and '..' not in name.parts and
             str(name) == relative, 'noncanonical evidence filename')
        path = self.root.joinpath(*name.parts)
        need(path.is_file() and not path.is_symlink() and
             path.resolve(strict=True).is_relative_to(self.root), 'missing or unsafe raw file: ' + relative)
        need(path.stat().st_size <= limit, 'raw file exceeds cap: ' + relative)
        data = path.read_bytes()
        need(len(data) <= limit, 'raw file grew beyond cap: ' + relative)
        entry = {'size': len(data), 'sha256': sha(data)}
        if relative in self.inputs:
            need(self.inputs[relative] == entry, 'raw file changed while reading: ' + relative)
        else:
            self.total += len(data)
            need(self.total <= MAX_INPUT_BYTES, 'total consumed evidence exceeds cap')
            self.inputs[relative] = entry
        return data

    def json(self, relative, limit=16 * 1024 * 1024):
        return json_value(self.read(relative, limit))


def json_lines(data):
    need(isinstance(data, bytes) and 0 < len(data) <= LIMITS['maxOutputBytes'], 'JSONL bytes cap')
    need(data.endswith(b'\n') and b'\r' not in data and b'\x00' not in data, 'JSONL is incomplete or noncanonical')
    lines = data.splitlines()
    need(2 <= len(lines) <= LIMITS['maxRecords'] + 2, 'JSONL record count cap')
    rows = []
    for line in lines:
        need(0 < len(line) <= MAX_LINE_BYTES, 'JSONL blank/oversized record')
        row = json_value(line)
        need(type(row) is dict, 'JSONL record is not an object')
        rows.append(row)
    return rows


def committed_code(tools_root, publisher_sha, names):
    need(isinstance(publisher_sha, str) and re.fullmatch('[0-9a-f]{40}', publisher_sha),
         'exact publisher SHA required')
    tools_root = Path(tools_root).resolve(strict=True)
    root = tools_root.parent
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    need(head == publisher_sha, 'checkout differs from explicit publisher SHA')
    result = {}
    for name in sorted(set(names) | set(OLD_CODE)):
        path = tools_root / name
        need(path.is_file() and not path.is_symlink(), 'publisher tool missing: ' + name)
        current = path.read_bytes()
        original = subprocess.check_output(['git', 'show', publisher_sha + ':tools/' + name], cwd=root)
        need(current == original, 'publisher tool differs from committed bytes: ' + name)
        digest = sha(current)
        if name in OLD_CODE:
            need(digest == OLD_CODE[name], 'unchanged prior gate differs: ' + name)
        result[name] = digest
    return result


def exact(row, expected, label):
    need(type(row) is dict, label + ' is not an object')
    for key, value in expected.items():
        need(key in row and type(row[key]) is type(value) and row[key] == value,
             label + ' differs: ' + key)


def keys(row, names, label):
    need(type(row) is dict and set(row) == set(names.split()), label + ' fields differ')


def text(value, maximum=4096):
    return isinstance(value, str) and 0 < len(value.encode('utf-8')) <= maximum and '\x00' not in value


def absolute(value):
    return text(value) and PurePosixPath(value).is_absolute() and str(PurePosixPath(value)) == value and '..' not in PurePosixPath(value).parts


def utc_us(value):
    need(text(value, 64), 'UTC timestamp missing')
    try:
        date = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise ValueError('Host observer evidence: invalid UTC timestamp') from error
    need(date.utcoffset() == datetime.timedelta(0), 'timestamp must explicitly use UTC')
    delta = date - datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds


def bound(inputs, filename, receipt, *, named=False, limit=16 * 1024 * 1024):
    need(type(receipt) is dict and integer(receipt.get('size')) and hex_sha(receipt.get('sha256')),
         'file binding missing: ' + filename)
    if named:
        need(receipt.get('filename') == filename, 'file binding name differs: ' + filename)
    data = inputs.read(filename, limit)
    need(receipt['size'] == len(data) and receipt['sha256'] == sha(data), 'actual file bytes differ: ' + filename)
    return data


def macho_arm64(data):
    need(len(data) >= 40, 'sampler Mach-O truncated')
    magic, cpu, _subtype, filetype, count, size, _flags, _reserved = struct.unpack_from('<8I', data)
    need(magic == 0xFEEDFACF and cpu == 0x0100000C and filetype == 2 and
         0 < count <= 4096 and count * 8 <= size <= len(data) - 32, 'sampler is not an arm64 executable Mach-O')
    offset = 32
    for _ in range(count):
        need(offset + 8 <= 32 + size, 'sampler load commands truncated')
        _command, length = struct.unpack_from('<2I', data, offset)
        need(length >= 8 and length % 4 == 0 and offset + length <= 32 + size, 'sampler load-command range invalid')
        offset += length
    need(offset == 32 + size, 'sampler load-command size differs')


def build_identity(inputs, summary, tools_root, code):
    filename = PREFIX + 'build.json'
    build = json_value(bound(inputs, filename, summary.get('build'), named=True))
    exact(build, {'schema': 1, 'kind': 'mouse637-host-observer-build', 'ok': True,
                  'platform': 'darwin', 'arch': 'arm64', 'publisherSHA': summary['publisherSHA'], 'errors': []}, 'build')
    binary_name = PREFIX + 'sampler.bin'
    binary = bound(inputs, binary_name, summary.get('sampler'), named=True)
    macho_arm64(binary)
    expected_binary = {'filename': binary_name, 'path': summary['output'] + '/' + binary_name,
                       'size': len(binary), 'sha256': sha(binary), 'arch': 'arm64'}
    exact(build.get('binary'), expected_binary, 'compiled binary')
    commands = build.get('commands')
    need(type(commands) is list and len(commands) == 10, 'complete compiler command receipts required')
    for row in commands:
        keys(row, 'argv returncode output', 'build command')
        need(type(row['argv']) is list and row['argv'] and all(text(x) for x in row['argv']) and
             row['returncode'] == 0 and type(row['returncode']) is int and
             isinstance(row['output'], str) and len(row['output'].encode('utf-8')) <= 1048576,
             'build command failed or exceeded cap')
    source_path = commands[1]['argv'][2] if len(commands[1]['argv']) == 3 else None
    need(absolute(source_path) and source_path.endswith('/tools/mouse637-host-observer.c'), 'compiled source path invalid')
    source_root = str(PurePosixPath(source_path).parent)
    builder_path = source_root + '/mouse637-host-observer-build.py'
    compile_command = ['xcrun', 'clang', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                       source_path, '-o', expected_binary['path']]
    expected_commands = [
        ['git', 'rev-parse', 'HEAD'], ['git', 'hash-object', source_path],
        ['git', 'rev-parse', 'HEAD:tools/mouse637-host-observer.c'],
        ['git', 'hash-object', builder_path], ['git', 'rev-parse', 'HEAD:tools/mouse637-host-observer-build.py'],
        ['xcrun', 'clang', '--version'], ['xcrun', '--show-sdk-path'], ['xcrun', '--show-sdk-version'],
        compile_command, ['xcrun', 'lipo', '-archs', expected_binary['path']],
    ]
    need([r['argv'] for r in commands] == expected_commands and build.get('command') == compile_command,
         'actual build commands differ')
    need(commands[0]['output'].strip() == summary['publisherSHA'] and commands[9]['output'].strip() == 'arm64',
         'build commit or lipo architecture differs')
    for field, name, first in [('source', 'mouse637-host-observer.c', 1), ('builder', 'mouse637-host-observer-build.py', 3)]:
        data = (tools_root / name).read_bytes()
        exact(build.get(field), {'path': 'tools/' + name, 'size': len(data), 'sha256': code[name]}, field + ' build binding')
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\x00' + data).hexdigest()
        need(commands[first]['output'].strip() == blob == commands[first + 1]['output'].strip(), 'compiled Git blob differs')
    for field, index in [('compilerVersion', 5), ('sdkPath', 6), ('sdkVersion', 7)]:
        need(text(build.get(field), 1048576) and build[field] == commands[index]['output'].strip(), 'SDK/compiler receipt differs')
    need(absolute(build['sdkPath']), 'SDK path must be absolute')
    need(utc_us(build['startedAtUTC']) <= utc_us(build['finishedAtUTC']) <= summary['startedAtEpochUs'],
         'build did not precede original observation')
    return build


def phase_records(data, launch):
    """Validate the actual bounded stream; no native workload or clock fitting."""
    rows = json_lines(data)
    header, eof = rows[0], rows[-1]
    keys(header, 'type sequence schema kind phase nonce samplerPid rootPid expectedRootParentPid uid expectedRootPath launchBeforeEpochUs launchAfterEpochUs budgetMs intervalMs limits clock counterUnits timebaseNumer timebaseDenom logicalCpus kernel machine', 'header')
    exact(header, {'type': 'header', 'sequence': 0, 'schema': 1, 'kind': 'mouse637-host-observer',
                   'phase': launch['phase'], 'nonce': launch['nonce'], 'samplerPid': launch['helperPid'],
                   'rootPid': launch['pid'], 'expectedRootParentPid': launch['parentPid'], 'uid': launch['uid'],
                   'expectedRootPath': launch['expectedRootPath'], 'launchBeforeEpochUs': launch['launchBeforeEpochUs'],
                   'launchAfterEpochUs': launch['launchAfterEpochUs'], 'budgetMs': BUDGETS[launch['phase']],
                   'intervalMs': INTERVAL_MS, 'limits': LIMITS, 'clock': 'mach_absolute_time',
                   'counterUnits': 'mach_absolute_time', 'machine': 'arm64'}, 'header')
    need(integer(header['timebaseNumer'], 1, (1 << 32) - 1) and integer(header['timebaseDenom'], 1, (1 << 32) - 1) and
         integer(header['logicalCpus'], 1, 65536) and text(header['kernel'], 127), 'host clock/machine invalid')
    interval = INTERVAL_MS * 1000000 * header['timebaseDenom'] // header['timebaseNumer']
    need(interval > 0, 'sampling interval invalid')
    keys(eof, 'type sequence ok reason rootGone errorCode recordCount storedRecordCount droppedRecords ownedCount imageCount samplingStartMach samplingEndMach deadlineMach missedIntervals maxReadTicks maxLagTicks selfUserUs selfSystemUs payloadBytesBeforeEOF selfCpuUs observedDurationMach selfCpuLimitNumerator selfCpuLimitDenominator withinSelfCpuLimit discoveryGone discoveryMoved dumpStartMach dumpEndMach selfCpuAccounting unmeasuredResidual', 'EOF')
    exact(eof, {'type': 'eof', 'sequence': len(rows) - 1, 'ok': True, 'reason': 'root-exited', 'rootGone': True,
                'errorCode': 0, 'recordCount': len(rows) - 2, 'storedRecordCount': len(rows) - 2,
                'droppedRecords': 0, 'selfCpuLimitNumerator': 1, 'selfCpuLimitDenominator': 100,
                'withinSelfCpuLimit': True, 'selfCpuAccounting': 'startup+collection+flushed-data-before-eof',
                'unmeasuredResidual': 'eof-write-close-free'}, 'EOF')
    for key in ('ownedCount', 'imageCount', 'samplingStartMach', 'samplingEndMach', 'deadlineMach', 'missedIntervals',
                'maxReadTicks', 'maxLagTicks', 'selfUserUs', 'selfSystemUs', 'payloadBytesBeforeEOF',
                'selfCpuUs', 'observedDurationMach', 'discoveryGone', 'discoveryMoved', 'dumpStartMach', 'dumpEndMach'):
        need(integer(eof[key]), 'invalid EOF counter: ' + key)
    before_eof = data[:data.rfind(b'\n', 0, len(data) - 1) + 1]
    need(eof['payloadBytesBeforeEOF'] == len(before_eof), 'EOF payload byte count differs')
    need(eof['samplingStartMach'] < eof['samplingEndMach'] and
         eof['observedDurationMach'] == eof['samplingEndMach'] - eof['samplingStartMach'], 'nonpositive or inconsistent observed duration')
    need(eof['samplingEndMach'] <= eof['dumpStartMach'] <= eof['dumpEndMach'], 'record dump/CPU accounting order differs')
    need(eof['selfCpuUs'] == eof['selfUserUs'] + eof['selfSystemUs'] and
         eof['selfCpuUs'] * 1000 * 100 * header['timebaseDenom'] <= eof['observedDurationMach'] * header['timebaseNumer'],
         'sampler CPU exceeds one percent of one core')
    identities, images, active, hosts, samples, events = [], [], {}, [], [], []
    max_read, root_exit = 0, False
    common = 'type sequence identityIndex readStartMach readEndMach'
    identity_keys = common + ' imageIndex pid ppid uid parentIndex startSec startUsec startAbstime uuid path'
    for sequence, row in enumerate(rows[1:-1], 1):
        need(type(row.get('sequence')) is int and row['sequence'] == sequence, 'record order is not contiguous')
        kind = row.get('type')
        start, end = row.get('readStartMach'), row.get('readEndMach')
        need(integer(start) and integer(end) and eof['samplingStartMach'] <= start <= end <= eof['samplingEndMach'],
             'record read interval invalid')
        max_read = max(max_read, end - start)
        if kind == 'host':
            need(not root_exit, 'new sampling cycle appears after observed root exit')
            keys(row, 'type sequence scheduledMach readStartMach readEndMach cpuTicks selfUserUs selfSystemUs', 'host record')
            need(integer(row['scheduledMach']) and eof['samplingStartMach'] <= row['scheduledMach'] <= start and
                 type(row['cpuTicks']) is list and len(row['cpuTicks']) == 4 and all(integer(x, 0, (1 << 32) - 1) for x in row['cpuTicks']) and
                 integer(row['selfUserUs']) and integer(row['selfSystemUs']), 'host accounting invalid')
            if hosts:
                previous = hosts[-1]
                gap = row['scheduledMach'] - previous['scheduledMach']
                need(gap >= interval and gap % interval == 0 and start >= previous['readEndMach'] and
                     row['selfUserUs'] >= previous['selfUserUs'] and row['selfSystemUs'] >= previous['selfSystemUs'], 'host schedule or self counters regress')
            hosts.append(row)
            continue
        need(integer(row.get('identityIndex'), 0, LIMITS['maxOwned'] - 1), 'identity index invalid')
        index = row['identityIndex']
        if kind in ('identity', 'image'):
            keys(row, identity_keys, kind + ' record')
            need(integer(row['pid'], 1, (1 << 31) - 1) and integer(row['ppid'], 1, (1 << 31) - 1) and
                 row['uid'] == launch['uid'] and type(row['uid']) is int and row['pid'] != launch['helperPid'] and
                 integer(row['startSec'], 1) and integer(row['startUsec'], 0, 999999) and integer(row['startAbstime'], 1, end) and
                 isinstance(row['uuid'], str) and re.fullmatch('[0-9a-f]{32}', row['uuid']) and absolute(row['path']), 'process birth/image invalid')
            need(type(row['imageIndex']) is int and row['imageIndex'] == len(images) < LIMITS['maxImages'], 'image order differs')
            if kind == 'identity':
                need(index == len(identities) and row['pid'] not in active, 'identity order/active PID reuse differs')
                previous_births = [s['birth'] for s in identities if s['birth']['pid'] == row['pid']]
                need(all(row['startAbstime'] > birth['startAbstime'] for birth in previous_births),
                     'retired PID was silently reintroduced with its old birth')
                if index == 0:
                    exact(row, {'pid': launch['pid'], 'ppid': launch['parentPid'], 'parentIndex': -1,
                                'path': launch['expectedRootPath'], 'readStartMach': eof['samplingStartMach']}, 'root identity')
                    birth_us = row['startSec'] * 1000000 + row['startUsec']
                    need(launch['launchBeforeEpochUs'] <= birth_us <= launch['launchAfterEpochUs'], 'root birth outside original Popen bracket')
                else:
                    parent = row['parentIndex']
                    need(integer(parent, 0, index - 1) and identities[parent]['alive'] and row['ppid'] == identities[parent]['birth']['pid'] and
                         row['startAbstime'] >= identities[parent]['birth']['startAbstime'], 'child lacks a live birth-owned parent')
                state = {'birth': row.copy(), 'alive': True, 'image': row['imageIndex'], 'ppid': row['ppid'],
                         'lastStart': start, 'lastEnd': end, 'lastCounters': None, 'samples': 0, 'images': [row['imageIndex']]}
                identities.append(state)
                active[row['pid']] = index
            else:
                need(0 < index < len(identities) and identities[index]['alive'], 'unowned or root image change')
                state = identities[index]
                for field in ('pid', 'ppid', 'uid', 'parentIndex', 'startSec', 'startUsec', 'startAbstime'):
                    need(type(row[field]) is int and row[field] == state['birth'][field], 'image changed process birth: ' + field)
                previous = images[state['image']]
                need((row['path'], row['uuid']) != (previous['path'], previous['uuid']), 'image change did not change image')
                state['image'] = row['imageIndex']
                state['images'].append(row['imageIndex'])
            images.append(row.copy())
        else:
            need(index < len(identities) and identities[index]['alive'], 'record references missing/retired identity')
            state = identities[index]
            if kind == 'sample':
                keys(row, common + ' imageIndex userTime systemTime runnableTime startAbstime', 'sample')
                need(row['imageIndex'] == state['image'] and type(row['imageIndex']) is int and
                     row['startAbstime'] == state['birth']['startAbstime'] and type(row['startAbstime']) is int,
                     'sample image or birth differs')
                counters = tuple(row.get(k) for k in ('userTime', 'systemTime', 'runnableTime'))
                need(all(integer(x) for x in counters) and (state['lastCounters'] is None or all(x >= y for x, y in zip(counters, state['lastCounters']))),
                     'process cumulative counters regress')
                # Runnable accumulates a scheduler timer. It is neither pure wait
                # nor required to be >= CPU timers sampled by a different method.
                state['lastCounters'] = counters
                state['samples'] += 1
                samples.append(row)
            else:
                keys(row, common + ' code otherPid observedStartSec observedStartUsec observedStartAbstime', 'lifecycle record')
                need(kind in ('exit', 'reparent', 'reuse'), 'error or unknown lifecycle record')
                need(integer(row['code'], 0, (1 << 31) - 1) and integer(row['otherPid'], 0, (1 << 31) - 1) and
                     all(integer(row[k]) for k in ('observedStartSec', 'observedStartUsec', 'observedStartAbstime')), 'lifecycle PID/code invalid')
                if kind == 'exit':
                    need(row['code'] in (2, 3) and row['otherPid'] == 0 and
                         [row[k] for k in ('observedStartSec', 'observedStartUsec', 'observedStartAbstime')] == [0, 0, 0], 'exit receipt invalid')
                    state['alive'] = False
                    active.pop(state['birth']['pid'])
                    root_exit = root_exit or index == 0
                elif kind == 'reparent':
                    need(row['code'] == state['ppid'] and row['otherPid'] > 0 and row['otherPid'] != state['ppid'] and
                         [row[k] for k in ('observedStartSec', 'observedStartUsec', 'observedStartAbstime')] == [0, 0, 0], 'reparent receipt invalid')
                    state['ppid'] = row['otherPid']
                else:
                    observed = (row['observedStartSec'], row['observedStartUsec'], row['observedStartAbstime'])
                    birth = tuple(state['birth'][k] for k in ('startSec', 'startUsec', 'startAbstime'))
                    need(index > 0 and row['code'] == 0 and row['otherPid'] == 0 and integer(observed[0], 1) and
                         integer(observed[1], 0, 999999) and integer(observed[2], 1, end) and observed != birth,
                         'PID reuse lacks a changed birth')
                    state['alive'] = False
                    active.pop(state['birth']['pid'])
                events.append(row)
        state = identities[index]
        need(start >= state['lastStart'] and end >= state['lastEnd'], 'per-identity read intervals regress')
        state['lastStart'], state['lastEnd'] = start, end
    need(identities and root_exit and hosts and samples and identities[0]['samples'] > 0, 'root/host/process coverage incomplete')
    need(eof['ownedCount'] == len(identities) and eof['imageCount'] == len(images) and eof['maxReadTicks'] == max_read,
         'EOF identity/image/read counts differ')
    missed = sum((b['scheduledMach'] - a['scheduledMach']) // interval - 1 for a, b in zip(hosts, hosts[1:]))
    need(eof['missedIntervals'] == missed and eof['maxLagTicks'] == max(h['readStartMach'] - h['scheduledMach'] for h in hosts),
         'EOF sampling gaps/lag differ')
    need(eof['selfUserUs'] >= hosts[-1]['selfUserUs'] and eof['selfSystemUs'] >= hosts[-1]['selfSystemUs'], 'final sampler CPU regresses')
    deadline = identities[0]['birth']['startAbstime'] + BUDGETS[launch['phase']] * 1000000 * header['timebaseDenom'] // header['timebaseNumer']
    need(eof['deadlineMach'] == deadline and all(h['readStartMach'] < deadline for h in hosts), 'original phase deadline differs')
    return {'header': header, 'eof': eof, 'identities': identities, 'images': images, 'samples': samples, 'hosts': hosts, 'events': events}


def launch_identity(inputs, row, summary, phase, build):
    exact(row, {'phase': phase, 'budgetMs': BUDGETS[phase], 'parentPid': summary['pid'], 'uid': summary['uid'],
                'helperExitCode': 0, 'originalExitCodeObserved': 0, 'completed': True,
                'originalLog': 'mouse-637-baseline-performance.log' if phase == 'baseline' else 'mouse-631-native.log'}, 'launch')
    need(not any(row.get(k) for k in ('observerError', 'evidenceError', 'helperCleanupErrors', 'originalPollError')), 'observer launch failed')
    early_exit = row.get('originalExitCodeAtSamplerExit')
    need('originalExitCodeAtSamplerExit' in row and (early_exit is None or type(early_exit) is int and early_exit == 0),
         'early original process exit observation conflicts with final success')
    need(integer(row.get('pid'), 1, (1 << 31) - 1) and integer(row.get('helperPid'), 1, (1 << 31) - 1) and
         len({row['pid'], row['helperPid'], row['parentPid']}) == 3 and hex_sha(row.get('nonce')), 'launch process/nonce identity invalid')
    for k in ('launchBeforeEpochUs', 'launchAfterEpochUs', 'launchBeforeMonotonicNs', 'launchAfterMonotonicNs', 'finishedMonotonicNs'):
        need(integer(row.get(k), 1), 'launch clock missing: ' + k)
    need(summary['startedAtEpochUs'] <= row['launchBeforeEpochUs'] <= row['launchAfterEpochUs'] <= summary['finishedAtEpochUs'] and
         row['launchBeforeMonotonicNs'] <= row['launchAfterMonotonicNs'] <= row['finishedMonotonicNs'], 'launch chronology invalid')
    need(absolute(row.get('expectedRootPath')), 'root executable path missing')
    argv = row.get('argv')
    if phase == 'baseline':
        need(type(argv) is list and len(argv) == 4 and absolute(argv[0]) and
             argv[1:] == [summary['output'] + '/mouse-637-baseline-performance.py', '--output', summary['output']] and row.get('profile') is None,
             'original baseline argv/profile changed')
    else:
        need(argv == [summary['executable'], '--mouse-631-smoke'] and row['expectedRootPath'] == summary['executable'] and
             absolute(row.get('profile')) and row['profile'].endswith('/mouse-profiles/task-stress-631'), 'original candidate argv/profile changed')
    name = PREFIX + phase
    config = json_value(bound(inputs, name + '.json', row.get('config'), named=True))
    copied = ('phase', 'budgetMs', 'pid', 'parentPid', 'uid', 'argv', 'expectedRootPath', 'nonce', 'originalLog', 'profile',
              'launchBeforeEpochUs', 'launchAfterEpochUs', 'launchBeforeMonotonicNs', 'launchAfterMonotonicNs')
    expected = {k: row[k] for k in copied}
    raw_path = summary['output'] + '/' + name + '.jsonl'
    binary = build['binary']['path']
    command = [binary, phase, str(row['pid']), str(row['parentPid']), row['expectedRootPath'],
               str(row['launchBeforeEpochUs']), str(row['launchAfterEpochUs']), str(row['budgetMs']), row['nonce'], raw_path, str(row['uid'])]
    expected.update(schema=1, kind='mouse637-host-observer-config', source=SOURCE, publisherSHA=summary['publisherSHA'],
                    helperPid=None, helperExitCode=None, sampler=binary, samplerSha256=summary['sampler']['sha256'],
                    output=raw_path, helperArgv=command)
    need(config == expected, 'exact original launch/sampler config differs')
    need(bound(inputs, name + '.log', row.get('helperLog'), named=True) == b'', 'external sampler emitted errors')
    raw = bound(inputs, name + '.jsonl', row.get('raw'), named=True, limit=LIMITS['maxOutputBytes'])
    return phase_records(raw, row)


def native_log(data, pid, budget_ms, marker=None):
    value = data.decode('utf-8')
    found = re.findall(r'^MOUSE_NATIVE_PROCESS_RETURN pid=(\d+) code=(-?\d+) elapsedMs=(\d+)\s*$', value, re.M)
    need(len(found) == 1 and found[0][0] == str(pid) and found[0][1] == '0' and 0 < int(found[0][2]) <= budget_ms,
         'actual original process exit/budget receipt differs')
    if marker:
        need(value.splitlines().count(marker) == 1, 'original success marker missing')
    need('MOUSE_637_HOST_OBSERVER_SUMMARY_SAVE_FAILED' not in value, 'late observer summary save failed')


def native_bindings(inputs, summary, phases):
    envelope = inputs.json('mouse-637-baseline-performance.json')
    process = inputs.json('mouse-637-baseline-process.json')
    exact(envelope, {'schema': 1, 'kind': 'published-baseline-stress-run', 'ok': True, 'version': '6.0.37',
                     'platform': 'darwin', 'arch': 'arm64', 'baselineVersion': '6.0.36',
                     'baselineSource': '7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3', 'baseline': BASELINE_PACKAGE,
                     'rawDirectory': 'mouse-637-baseline-performance', 'process': process, 'physicalUserDeviceVerified': False}, 'baseline envelope')
    exact(envelope.get('runner'), {'runId': summary['runId'], 'runAttempt': summary['runAttempt'], 'job': summary['job'],
                                  'sha': summary['publisherSHA'], 'system': 'Darwin', 'machine': 'arm64'}, 'baseline runner')
    baseline_exe = envelope.get('executable', {}).get('path')
    need(absolute(baseline_exe), 'baseline executable path missing')
    exact(envelope['executable'], {'size': 52688, 'sha256': 'aa3f21d6da8c42799fd603a5c896f1d2ba9004f2a30a9341541f6be3957d287f'}, 'baseline executable bytes')
    exact(process, {'argv': [baseline_exe, '--mouse-631-smoke'], 'exitCode': 0, 'budgetMs': 400000,
                    'requiredMarkers': list(MARKERS), 'cwd': summary['output'] + '/mouse-637-baseline-performance',
                    'log': 'mouse-637-baseline-performance/mouse-631-native.log'}, 'baseline native process')
    need(integer(process.get('pid'), 1) and number(process.get('elapsedMs'), 0) and 0 < process['elapsedMs'] <= 400000 and
         absolute(process.get('profile')) and process['profile'].endswith('/Isolated previous-version performance profile') and
         utc_us(process['startedAt']) < utc_us(process['finishedAt']), 'baseline original process identity invalid')
    baseline_app_root = PurePosixPath(baseline_exe).parents[4]
    need(PurePosixPath(process['profile']).parent == baseline_app_root and baseline_app_root.name.startswith('mouse637-baseline-'),
         'baseline profile is not its isolated original workspace')
    runner_temp = PurePosixPath(summary['launches'][1]['profile']).parent.parent
    need(baseline_app_root.parent == runner_temp, 'baseline and candidate runner workspace differ')
    native_info = {}
    for phase, version, pid, exe in [('baseline', '6.0.36', process['pid'], baseline_exe),
                                     ('candidate', '6.0.37', summary['launches'][1]['pid'], summary['executable'])]:
        raw_prefix = 'mouse-637-baseline-performance/' if phase == 'baseline' else ''
        observed = phases[phase]
        matches = [i for i, state in enumerate(observed['identities']) if state['birth']['pid'] == pid and
                   any(observed['images'][n]['path'] == exe for n in state['images'])]
        need(len(matches) == 1, 'actual original native process not present in owned tree: ' + phase)
        identity = matches[0]
        state = observed['identities'][identity]
        need((identity > 0 and state['birth']['parentIndex'] == 0) if phase == 'baseline' else identity == 0,
             'baseline child/candidate root ownership differs')
        need(any(r['identityIndex'] == identity and observed['images'][r['imageIndex']]['path'] == exe for r in observed['samples']),
             'native executable has no observed CPU sample')
        report_name, stress_name, log_name = (raw_prefix + n for n in ('mouse-631-native.json', 'mouse-631-stress.json', 'mouse-631-native.log'))
        if phase == 'baseline':
            for name in (report_name, stress_name, log_name):
                bound(inputs, name, envelope.get('files', {}).get(name))
        native, stress = inputs.json(report_name), inputs.json(stress_name)
        exact(native, {'ok': True, 'version': version, 'platform': 'darwin', 'arch': 'arm64', 'pid': pid, 'budgetMs': 350000}, 'original native report')
        need(number(native.get('elapsedMs')) and 0 < native['elapsedMs'] <= 350000 and
             [s.get('name') for s in native.get('stages', [])] == ['taskOnly', 'fiftyTabs', 'stationaryMedia'] and
             all(s.get('ok') is True and number(s.get('elapsedMs')) for s in native['stages']), 'original native stages differ')
        exact(stress, {'ok': True, 'version': version, 'platform': 'darwin', 'arch': 'arm64', 'budgetMs': 200000}, 'original stress report')
        need(number(stress.get('elapsedMs')) and 0 < stress['elapsedMs'] <= 200000 and
             [s.get('ownedPageCount') for s in stress.get('stages', [])] == [20, 50], 'original stress coverage/budget differs')
        metric_pids = set()
        for stage in stress['stages']:
            for key in ('processesBefore', 'processesAfter'):
                metrics = stage.get(key)
                need(type(metrics) is list and metrics and all(type(p) is dict and integer(p.get('pid'), 1) for p in metrics), 'native process metrics missing')
                need([p['pid'] for p in metrics if p.get('type') == 'Browser'] == [pid], 'native stress Browser PID differs')
                metric_pids.update(p['pid'] for p in metrics)
        native_bytes = inputs.read(log_name)
        lines = native_bytes.decode('utf-8').splitlines()
        need(all(lines.count(marker) == 1 for marker in MARKERS), 'original native completion markers missing')
        if phase == 'baseline':
            need(process.get('logSha256') == sha(native_bytes), 'baseline process log hash differs')
            native_log(inputs.read(summary['launches'][0]['originalLog']), summary['launches'][0]['pid'], 900000,
                       'MOUSE_637_BASELINE_PERFORMANCE_PASS')
        else:
            native_log(native_bytes, pid, 400000)
        sampled_pids = {observed['identities'][r['identityIndex']]['birth']['pid'] for r in observed['samples']}
        native_info[phase] = {'nativePid': pid, 'identityIndex': identity, 'nativeReport': report_name, 'stressReport': stress_name,
                              'metricPids': sorted(metric_pids), 'sampledMetricPids': sorted(metric_pids & sampled_pids),
                              'metricPidsWithoutSample': sorted(metric_pids - sampled_pids)}
    return native_info


def verify(directory, *, tools_root=None, publisher_sha=None):
    tools_root = Path(tools_root or Path(__file__).resolve().parent).resolve(strict=True)
    publisher_sha = publisher_sha or os.environ.get('GITHUB_SHA')
    code = committed_code(tools_root, publisher_sha, TOOLS)
    pin_path = tools_root.parent / 'staging/mouse/6.0.37-arm64/pin.json'
    pin = pin_path.read_bytes()
    need(sha(pin) == PIN_SHA and pin == subprocess.check_output(['git', 'show', publisher_sha + ':staging/mouse/6.0.37-arm64/pin.json'], cwd=tools_root.parent),
         'immutable accepted source/package pin changed')
    inputs = Inputs(directory)
    summary = inputs.json(PREFIX + 'summary.json')
    exact(summary, {'schema': 1, 'kind': 'mouse637-external-host-observer-summary', 'source': SOURCE, 'version': '6.0.37',
                    'publisherSHA': publisher_sha, 'platform': 'darwin', 'arch': 'arm64', 'ok': True, 'originalSucceeded': True,
                    'releaseAcceptance': False, 'causalConclusionEstablished': False,
                    'wrapperSha256': code['mouse637-host-observer.py'], 'samplerSourceSha256': code['mouse637-host-observer.c'],
                    'innerWrapperSha256': OLD_CODE['mouse637-guest-input-observer.py'],
                    'verifierSha256': OLD_CODE['fixtures/mouse637-readiness-002-verifier.py'], 'baselineHelperSha256': BASELINE_SHA}, 'summary')
    need(not summary.get('error') and not summary.get('cleanupError'), 'original verifier or observation failed')
    need(integer(summary.get('pid'), 1, (1 << 31) - 1) and integer(summary.get('uid'), 0, (1 << 31) - 1) and
         absolute(summary.get('output')) and absolute(summary.get('executable')), 'original runner identity missing')
    need(all(isinstance(summary.get(k), str) and re.fullmatch('[1-9][0-9]*', summary[k]) for k in ('runId', 'runAttempt')) and
         text(summary.get('job'), 256), 'actual CI run/attempt/job missing')
    need(integer(summary.get('startedAtEpochUs'), 1) and integer(summary.get('finishedAtEpochUs'), summary['startedAtEpochUs']), 'summary chronology invalid')
    for name, digest in [('mouse-verify.py', summary['verifierSha256']), ('mouse-637-baseline-performance.py', BASELINE_SHA)]:
        need(sha(inputs.read(name)) == digest, 'actual original source helper differs: ' + name)
    build = build_identity(inputs, summary, tools_root, code)
    launches = summary.get('launches')
    need(type(launches) is list and len(launches) == 2 and [r.get('phase') for r in launches] == list(PHASES), 'both original phases required exactly once')
    phases = {phase: launch_identity(inputs, launch, summary, phase, build) for phase, launch in zip(PHASES, launches)}
    need(launches[0]['nonce'] != launches[1]['nonce'] and
         launches[0]['launchAfterMonotonicNs'] <= launches[1]['launchBeforeMonotonicNs'], 'phase nonce/order differs')
    evidence_names = {'mouse-637-baseline-process.json', 'mouse-637-baseline-performance.json',
                      'mouse-637-baseline-performance/mouse-631-native.json', 'mouse-631-native.json',
                      'mouse-637-baseline-performance.log', 'mouse-631-native.log',
                      'mouse-637-guest-input-observer-summary.json', 'mouse-637-feature-readiness-summary.json'}
    evidence = summary.get('evidence')
    need(type(evidence) is dict and set(evidence) == evidence_names, 'original evidence inventory incomplete')
    for name in sorted(evidence):
        bound(inputs, name, evidence[name])
    for name, kind, wrapper in [('mouse-637-guest-input-observer-summary.json', 'mouse637-passive-guest-input-summary', 'mouse637-guest-input-observer.py'),
                                ('mouse-637-feature-readiness-summary.json', 'mouse637-external-feature-readiness', 'mouse637-feature-readiness.py')]:
        prior = inputs.json(name)
        exact(prior, {'schema': 1, 'kind': kind, 'source': SOURCE, 'version': '6.0.37', 'ok': True,
                      'publisherSHA': publisher_sha, 'platform': 'darwin', 'arch': 'arm64', 'output': summary['output'],
                      'executable': summary['executable'], 'wrapperSha256': OLD_CODE[wrapper]}, 'prior separate gate summary')
        need(not prior.get('error') and not prior.get('cleanupError'), 'prior separate gate failed')
        if wrapper == 'mouse637-feature-readiness.py':
            for when in ('before', 'after'):
                need(prior.get(when, {}).get('components') == COMPONENTS, 'original installed package components changed')
    native = native_bindings(inputs, summary, phases)
    need(committed_code(tools_root, publisher_sha, TOOLS) == code, 'publisher tool bytes changed while reading')
    for name in list(inputs.inputs):
        inputs.read(name, LIMITS['maxOutputBytes'])
    return {'ok': True, 'gate': 'mouse637-external-host-observer-v1', 'source': SOURCE, 'publisherSHA': publisher_sha,
            'runId': summary['runId'], 'runAttempt': summary['runAttempt'], 'job': summary['job'],
            'code': code, 'pinSha256': PIN_SHA, 'inputs': inputs.inputs,
            'phases': {phase: {**native[phase], 'rootPid': phases[phase]['header']['rootPid'],
                               'samplerPid': phases[phase]['header']['samplerPid'], 'nonce': phases[phase]['header']['nonce'],
                               'timebaseNumer': phases[phase]['header']['timebaseNumer'], 'timebaseDenom': phases[phase]['header']['timebaseDenom'],
                               'hostSamples': len(phases[phase]['hosts']), 'processSamples': len(phases[phase]['samples']),
                               'eof': phases[phase]['eof']} for phase in PHASES},
            'counterMeaning': 'Raw Mach cumulative CPU and runnable timers; runnable is not pure waiting time.',
            'clockMeaning': 'Mach observations, Unix launch brackets and renderer clocks are separate; no clock fit is inferred.',
            'sampleCoverageMeaning': 'Owned processes observed at 250 ms intervals; short-lived processes can disappear before adoption.',
            'selfCpuQualityLimit': {'numerator': 1, 'denominator': 100, 'logicalCpuNormalization': False,
                                    'includes': 'C sampler startup, collection and flushed data dump',
                                    'excludes': 'final EOF write/close/free, Python wrapper and wider OS effects'},
            'releaseAcceptance': False, 'originalReleaseGatesExecutedHere': False,
            'causalConclusionEstablished': False, 'nativeExecutionPerformedHere': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?')
    parser.add_argument('--directory', dest='directory_option')
    parser.add_argument('--publisher-sha', default=os.environ.get('GITHUB_SHA'))
    args = parser.parse_args()
    need(bool(args.directory) != bool(args.directory_option), 'provide one evidence directory')
    print(json.dumps(verify(args.directory or args.directory_option, publisher_sha=args.publisher_sha), sort_keys=True))


if __name__ == '__main__':
    main()
