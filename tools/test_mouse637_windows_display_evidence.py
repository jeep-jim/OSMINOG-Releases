#!/usr/bin/env python3
"""Synthetic process/geometry contracts; these are not native acceptance reports."""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import struct
import unittest
import zlib

GATE = runpy.run_path(str(Path(__file__).with_name('mouse637-windows-display-evidence.py')))


def fixture():
    files = {}
    def encode(name, value):
        files[name] = json.dumps(value).encode()
        return hashlib.sha256(files[name]).hexdigest()
    def process(pid, start):
        return {'pid': pid, 'exitCode': 0, 'startedAtMs': start, 'finishedAtMs': start + 10, 'elapsedMs': 10}
    legacy = {'ok': True, 'fromVersion': '6.0.29', 'toVersion': '6.0.37',
              'oldWrite': process(10, 100), 'replacement': process(11, 120), 'newRead': process(12, 140)}
    for mode, key, digest, version in (('write', 'oldWrite', 'oldReportSha256', '6.0.29'), ('read', 'newRead', 'newReportSha256', '6.0.37')):
        legacy[digest] = encode('mouse-631-upgrade/mouse-windows-smoke-' + mode + '.json',
                               {'ok': True, 'version': version, 'platform': 'win32', 'arch': 'x64', 'mode': mode, 'pid': legacy[key]['pid']})
    selected = {'index': 8, 'width': 1440, 'height': 900, 'bitDepth': 32, 'frequency': 64, 'flags': 0, 'orientation': 0}
    bounds = {'x': 0, 'y': 0, 'width': 1440, 'height': 900}
    work = {**bounds, 'height': 860}
    actual = {'device': 'unit display', 'mode': selected, 'logicalBounds': bounds, 'logicalWorkArea': work, 'scaleFactor': 1}
    receipt = {'schema': 1, 'version': '6.0.37', 'platform': 'win32', 'scope': 'session', 'source': 'User32 advertised display modes',
               'minimum': {'width': 1440, 'height': 900}, 'ok': True, 'pid': 20, 'device': actual['device'], 'selected': selected,
               'advertisedModes': [selected], 'after': actual, 'changed': True,
               'configuration': {'test': 0, 'flags': 0, 'registryUpdated': False, 'applied': 0},
               'persistence': {'pid': 21, 'actual': actual}, 'processExitVerified': True}
    preparation = {'ok': True, 'report': 'mouse-637-display.json', 'reportSha256': encode('mouse-637-display.json', receipt)}
    for phase, pid, start, marker in (('prepare', 20, 160, 'MOUSE_637_WINDOWS_DISPLAY_PREPARED'),
                                      ('verify', 21, 180, 'MOUSE_637_WINDOWS_DISPLAY_PERSISTENCE_PASS')):
        name = 'mouse-637-display-' + phase + '.log'
        files[name] = (marker + '\n').encode()
        preparation[phase] = {**process(pid, start), 'log': name, 'logSha256': hashlib.sha256(files[name]).hexdigest(), 'requiredMarkers': [marker]}
    checks = {'versionUpgrade': legacy, 'displayPreparation': preparation, 'baselinePerformance': process(30, 200)}
    for i, key in enumerate(('updateFrom636', 'freshUpgrade', 'taskAndFiftyTabs', 'ownerFeedback636')):
        checks[key] = process(40 + i, 220 + i * 20)
    checks['features637'] = {'write': process(50, 310), 'read': process(51, 330)}
    display = {'id': 123, 'bounds': bounds, 'workArea': work, 'scaleFactor': 1}
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1440, 900, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress((b'\0' + b'\0' * (1440 * 3)) * 900)) + chunk(b'IEND', b'')
    for prefix, version in (('mouse-637-baseline-performance/', '6.0.36'), ('', '6.0.37')):
        encode(prefix + 'mouse-631-stress-geometry.json', {'version': version, 'name': 'stress', 'display': display})
        files[prefix + 'mouse-631-stress-50-switch-1-display.png'] = png
    return files, {'checks': checks}, receipt, encode


class WindowsDisplayEvidence(unittest.TestCase):
    def test_complete_legacy_then_two_processes_then_same_actual_workload_display(self):
        files, report, _receipt, _encode = fixture()
        result = GATE['verify'](files.__getitem__, report)
        self.assertEqual(result['sequence'], ['oldWrite', 'replacement', 'newRead', 'prepare', 'verify', 'baselinePerformance'])
        self.assertTrue(result['independentProcesses'])

    def test_missing_failed_reused_or_reordered_process_is_rejected(self):
        for case in ('missing verify', 'failed verify', 'same pid', 'before legacy read', 'baseline before verify', 'features before baseline'):
            files, report, receipt, encode = fixture()
            checks = report['checks']; preparation = checks['displayPreparation']
            if case == 'missing verify': del preparation['verify']
            if case == 'failed verify': preparation['verify']['exitCode'] = 1
            if case == 'same pid':
                preparation['verify']['pid'] = receipt['persistence']['pid'] = receipt['pid']
                preparation['reportSha256'] = encode('mouse-637-display.json', receipt)
            if case == 'before legacy read': preparation['prepare']['startedAtMs'] = 145
            if case == 'baseline before verify': checks['baselinePerformance']['startedAtMs'] = 185
            if case == 'features before baseline': checks['features637']['write']['startedAtMs'] = 205
            with self.subTest(case=case), self.assertRaises(ValueError): GATE['verify'](files.__getitem__, report)

    def test_actual_report_log_and_legacy_bytes_cannot_be_substituted(self):
        for name in ('mouse-637-display.json', 'mouse-637-display-verify.log', 'mouse-631-upgrade/mouse-windows-smoke-read.json'):
            files, report, _receipt, _encode = fixture()
            files[name] += b' '
            with self.subTest(name=name), self.assertRaises(ValueError): GATE['verify'](files.__getitem__, report)

    def test_matching_rehashed_claims_do_not_allow_another_display_or_png(self):
        for case in ('baseline display', 'candidate display', 'actual mode', 'unadvertised mode', 'png'):
            files, report, receipt, encode = fixture()
            if case in ('baseline display', 'candidate display'):
                name = ('mouse-637-baseline-performance/' if case == 'baseline display' else '') + 'mouse-631-stress-geometry.json'
                data = json.loads(files[name]); data['display']['bounds']['width'] = 1024; encode(name, data)
            if case == 'actual mode':
                receipt['persistence']['actual'] = copy.deepcopy(receipt['persistence']['actual'])
                receipt['persistence']['actual']['mode']['width'] = 1024
            if case == 'unadvertised mode': receipt['advertisedModes'] = []
            if case == 'png':
                name = 'mouse-631-stress-50-switch-1-display.png'; data = bytearray(files[name]); data[16:20] = struct.pack('>I', 1024); files[name] = bytes(data)
            report['checks']['displayPreparation']['reportSha256'] = encode('mouse-637-display.json', receipt)
            with self.subTest(case=case), self.assertRaises(ValueError): GATE['verify'](files.__getitem__, report)

    def test_already_sufficient_advertised_mode_still_requires_independent_verify(self):
        files, report, receipt, encode = fixture()
        receipt['changed'] = False; del receipt['configuration']
        report['checks']['displayPreparation']['reportSha256'] = encode('mouse-637-display.json', receipt)
        self.assertTrue(GATE['verify'](files.__getitem__, report)['ok'])


if __name__ == '__main__':
    unittest.main()
