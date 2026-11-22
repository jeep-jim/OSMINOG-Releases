#!/usr/bin/env python3
"""Malformed637 appearance/input/process evidence must not satisfy acceptance."""
import copy
import json
from pathlib import Path
import runpy
import unittest

F = runpy.run_path(str(Path(__file__).with_name('mouse637-features-evidence.py')))


def state(mode='rounded', tone=55, theme='dark'):
    channel = int(160 + 95 * tone / 100 + .5)
    radius = 0 if mode == 'square' else 12
    return {'model': {'paneMode': mode, 'whiteTone': tone}, 'stored': {'paneMode': mode, 'whiteTone': tone},
            'theme': theme, 'primary': '#' + format(channel, '02x') * 3, 'textColor': 'rgb(%d, %d, %d)' % (channel, channel, channel),
            'gap': 0 if mode == 'square' else 6, 'radius': radius,
            'workspace': {'x': 0, 'y': 0, 'width': 800, 'height': 500}, 'stage': {'x': 0, 'y': 0, 'width': 800, 'height': 500},
            'panes': [{'id': str(i), 'bounds': {'x': i * 400, 'y': 0, 'width': 400, 'height': 500}, 'topRadius': radius, 'bottomRadius': radius} for i in range(2)],
            'settings': {'open': True, 'square': mode == 'square', 'tone': tone, 'value': str(tone)}}


class AppearanceState(unittest.TestCase):
    def test_clean_first_light_default_need_not_have_written_local_storage(self):
        value = state(theme='light'); value['stored'] = None
        F['appearance_state'](value, 'rounded', 55, 'light', settings=True, allow_unstored_default=True)
        with self.assertRaises(ValueError):
            F['appearance_state'](value, 'rounded', 55, 'light', settings=True)
        value = state(tone=0, theme='light'); value['stored'] = None
        with self.assertRaises(ValueError):
            F['appearance_state'](value, 'rounded', 0, 'light', allow_unstored_default=True)
        value = state(theme='dark'); value['stored'] = None
        with self.assertRaises(ValueError):
            F['appearance_state'](value, 'rounded', 55, 'dark', allow_unstored_default=True)

    def test_extremes_and_exact_default_are_recomputed(self):
        for mode in ('rounded', 'square'):
            for tone, color in ((0, '#a0a0a0'), (55, '#d4d4d4'), (100, '#ffffff')):
                value = state(mode, tone)
                F['appearance_state'](value, mode, tone, 'dark', settings=True)
                self.assertEqual(value['primary'], color)

    def test_css_color_storage_control_and_corner_forgeries_fail(self):
        mutations = [lambda x: x.update(primary='#ffffff'), lambda x: x['stored'].update(whiteTone=100),
                     lambda x: x.update(textColor='rgb(255, 255, 255)'), lambda x: x.update(gap=6),
                     lambda x: x['panes'][0].update(bottomRadius=12), lambda x: x['settings'].update(square=False)]
        for mutation in mutations:
            value = state('square')
            mutation(value)
            with self.assertRaises(ValueError):
                F['appearance_state'](value, 'square', 55, 'dark', settings=True)

    def test_report_without_separate_restart_witness_is_rejected(self):
        with self.assertRaises(ValueError):
            F['verify_appearance']({'initial': F['INITIAL'], 'range': F['RANGE'], 'writeVerified': True}, 11, 22, 'http://127.0.0.1:12000')


class NativeInput(unittest.TestCase):
    def row(self):
        return {'selector': '#settings-square-grid', 'pid': 11, 'source': 'User32', 'point': {'x': 4, 'y': 5}, 'at': 100,
                'events': [{'type': 'click', 'trusted': True, 'matches': True}]}

    def test_untrusted_foreign_or_wrong_backend_clicks_fail(self):
        F['input_event'](self.row(), 'win32', {11, 22})
        for mutation in [lambda x: x.update(pid=33), lambda x: x.update(source='JavaScript'),
                         lambda x: x['events'][0].update(trusted=False), lambda x: x['events'][0].update(matches=False)]:
            row = self.row(); mutation(row)
            with self.assertRaises(ValueError): F['input_event'](row, 'win32', {11, 22})

    def test_square_header_handle_requires_native_down_and_up(self):
        row = {'selector': '.divider[data-path=""] > .divider-hit', 'action': 'drag', 'pid': 11, 'source': 'XTest',
               'from': {'x': 400, 'y': 10}, 'to': {'x': 432, 'y': 10},
               'events': [{'type': 'pointerdown', 'trusted': True, 'matches': True}, {'type': 'pointerup', 'trusted': True}]}
        F['input_event'](row, 'linux', {11, 22})
        row['events'].pop()
        with self.assertRaises(ValueError): F['input_event'](row, 'linux', {11, 22})


class NativeProcessBinding(unittest.TestCase):
    def fixture(self):
        raw, written = b'{"final":true}', b'{"write":true}'
        facts = {'pid': 11, 'restart': {'pid': 22}}
        blobs, process = {}, {'reportSha256': F['sha'](raw)}
        for phase, pid, marker, name, data in [('write', 11, F['WRITE_MARKER'], F['WRITE'], written), ('read', 22, F['MARKER'], F['NAME'], raw)]:
            log = 'mouse-637-features-' + phase + '.log'
            blobs[log] = (marker + '\n').encode()
            process[phase] = {'pid': pid, 'exitCode': 0, 'elapsedMs': 100, 'requiredMarkers': [marker], 'log': log,
                              'logSha256': F['sha'](blobs[log]), 'report': name, 'reportSha256': F['sha'](data)}
        return blobs, process, facts, raw, written

    def verify(self, blobs, process, facts, raw, written):
        blobs['mouse-637-features-processes.json'] = json.dumps(process).encode()
        return F['process_binding'](F['N']['Evidence'](blobs.__getitem__), facts, raw, written, 'darwin')

    def test_two_exact_processes_logs_and_report_hashes_are_bound(self):
        self.verify(*self.fixture())
        for change in [lambda p: p['read'].update(pid=11), lambda p: p['write'].update(exitCode=1),
                       lambda p: p['read'].update(reportSha256='f'*64), lambda p: p['read'].update(elapsedMs=120001),
                       lambda p: p['write'].update(logSha256='f'*64)]:
            blobs, process, facts, raw, written = self.fixture(); change(process)
            with self.assertRaises(ValueError): self.verify(blobs, process, facts, raw, written)

    def test_success_flags_without_raw_frames_cannot_pass(self):
        blobs = {F['NAME']: b'{"ok":true,"version":"6.0.37"}', F['WRITE']: b'{}'}
        with self.assertRaises(ValueError): F['verify'](blobs.__getitem__)


if __name__ == '__main__':
    unittest.main()
