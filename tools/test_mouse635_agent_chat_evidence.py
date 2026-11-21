#!/usr/bin/env python3
"""Synthetic contract tests, never installed-app acceptance evidence."""
import copy
from pathlib import Path
import runpy
import unittest

HERE = Path(__file__).parent
C = runpy.run_path(str(HERE / 'mouse635-agent-chat-evidence.py'))
L = runpy.run_path(str(HERE / 'test_mouse635_library_evidence.py'))


def fixture(platform='linux', arch='x64'):
    library = L['fixture']()
    template = library['facts']['captures'][0]
    raw, captures = {}, []
    for name in C['CAPTURES']:
        frame = copy.deepcopy(template)
        frame.update(filename=name, displayFilename=name[:-4] + '-display.png')
        raw[name] = library['raw'][template['filename']]
        raw[frame['displayFilename']] = library['raw'][template['displayFilename']]
        captures.append(frame)
    def box(x, y, width, height):
        return {'x': x, 'y': y, 'width': width, 'height': height, 'clientWidth': width, 'scrollWidth': width}
    layouts = []
    for theme, width in C['SCENES']:
        messages = []
        for i, (role, text) in enumerate([
                ('user', 'Запомни слово «фиолетовый».'),
                ('assistant', 'Привет! Запомнил слово «фиолетовый».'),
                ('user', 'Какое слово я назвал? Покажи цвет фона.'),
                ('assistant', 'Вы назвали слово «фиолетовый».\ncssКопироватьbody { background: #f3edff; }')]):
            messages.append({'id': 'message-' + str(i), 'role': role, 'text': text, 'status': 'complete',
                             'bounds': box(500 + (30 if role == 'user' else 14), 110 + i * 85, width - 50, 60)})
        layouts.append({'theme': theme, 'panelHidden': False, 'settingsOpen': False, 'detailsOpen': False,
                        'terminalOpen': False, 'controlsHidden': True, 'rawToolsInChat': False,
                        'connection': 'connected', 'model': 'mouse635-chat-fixture',
                        'panel': box(500, 46, width, 650), 'header': box(500, 46, width, 64),
                        'chat': box(500, 135, width, 460), 'composer': box(512, 607, width - 24, 56),
                        'conversation': messages, 'contrast': {'background': 'rgb(24, 25, 34)' if theme == 'dark' else 'rgb(250, 249, 253)',
                            'text': 'rgb(241, 239, 247)' if theme == 'dark' else 'rgb(39, 35, 49)',
                            'muted': 'rgb(184, 179, 198)' if theme == 'dark' else 'rgb(107, 99, 121)'}})
    facts = {'schema': 1, 'source': C['SOURCE'], 'externalModelVerified': False,
             **dict.fromkeys(('ordinaryChatWithoutBrowserAccess', 'history', 'streaming', 'stop', 'settings',
                              'errorReply', 'cleanTranscript', 'clear'), True),
             'nativeTransport': 'mouse:agent → utilityProcess → HTTP/SSE', 'requestCount': 4, 'elapsedMs': 5000,
             'firstWorkerPid': 81, 'stoppedWorkerPid': 83, 'layouts': layouts, 'captures': C['CAPTURES'],
             'requestMetadata': [{'model': 'mouse635-chat-fixture', 'stream': True,
                                  'roles': ['system'] + ['user', 'assistant'] * index + ['user']} for index in range(4)]}
    native = []
    for selector, count in [('#agent-settings-open', 1), ('#agent-endpoint', 1), ('#agent-model', 1),
                            ('#agent-settings-done', 1), ('#agent-task-input', 4), ('#agent-run', 4),
                            ('#agent-chat-stop', 1), ('#agent-new-chat', 1)]:
        for _ in range(count):
            native.append({'selector': selector, 'source': {'linux': 'XTest', 'win32': 'User32', 'darwin': 'CGEvent'}[platform],
                           'point': {'x': 520, 'y': 650}, 'at': len(native) + 1, 'navigates': False,
                           'events': [{'type': 'click', 'trusted': True, 'matches': True}]})
    raw['mouse-635-owner-feedback.log'] = (C['MARKER'] + '\n').encode()
    return {'raw': raw, 'owner': {'pid': 80, 'platform': platform, 'arch': arch, 'budgetMs': 240000,
                                'agentChat': facts, 'nativeInputs': native, 'captures': captures}}


class AgentChatEvidence(unittest.TestCase):
    def verify(self, value):
        return C['verify'](value['raw'].__getitem__, owner=value['owner'])

    def test_all_platform_native_input_shapes(self):
        for platform, arch in [('linux', 'x64'), ('win32', 'x64'), ('darwin', 'arm64')]:
            result = self.verify(fixture(platform, arch))
            self.assertTrue(result['ok'])
            self.assertEqual(len(result['nativeCaptures']), 4)
            self.assertFalse(result['externalModelVerified'])

    def test_worker_history_streaming_and_model_scope_fail_closed(self):
        for mutate in [lambda f: f.update(externalModelVerified=True), lambda f: f.update(firstWorkerPid=80),
                       lambda f: f.update(stop=False), lambda f: f.update(streaming=False),
                       lambda f: f['requestMetadata'][1].update(roles=['system', 'user']),
                       lambda f: f['requestMetadata'][0].update(stream=False), lambda f: f.update(requestCount=3)]:
            value = fixture(); mutate(value['owner']['agentChat'])
            with self.assertRaises(ValueError): self.verify(value)

    def test_layout_visibility_contrast_and_raw_logs_are_checked(self):
        for mutate in [lambda v: v.update(settingsOpen=True), lambda v: v.update(controlsHidden=False),
                       lambda v: v.update(rawToolsInChat=True), lambda v: v['chat'].update(scrollWidth=500),
                       lambda v: v['composer'].update(y=150), lambda v: v['contrast'].update(text='rgb(24, 25, 34)'),
                       lambda v: v['conversation'][1].update(text='write_file'),
                       lambda v: v['conversation'][0]['bounds'].update(x=999), lambda v: v.update(theme='light')]:
            value = fixture(); mutate(value['owner']['agentChat']['layouts'][0])
            with self.assertRaises(ValueError): self.verify(value)

    def test_native_clicks_and_raw_os_frames_cannot_be_substituted(self):
        value = fixture(); value['owner']['nativeInputs'][0]['events'][0]['trusted'] = False
        with self.assertRaises(ValueError): self.verify(value)
        value = fixture(); value['owner']['captures'][0]['sha256'] = 'f' * 64
        with self.assertRaises(ValueError): self.verify(value)
        value = fixture(); value['raw']['mouse-635-owner-feedback.log'] = b'not a native Agent pass\n'
        with self.assertRaises(ValueError): self.verify(value)
        value = fixture(); value['owner']['agentChat']['captures'] = C['CAPTURES'][:-1]
        with self.assertRaises(ValueError): self.verify(value)


if __name__ == '__main__':
    unittest.main()
