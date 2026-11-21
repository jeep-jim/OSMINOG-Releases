#!/usr/bin/env python3
"""Bind the installed Agent chat fixture to real input, layout and OS frames."""
from pathlib import Path
import re
import runpy

N = runpy.run_path(str(Path(__file__).with_name('mouse635-native-evidence.py')))
need = N['need']
MARKER = 'MOUSE_635_AGENT_CHAT_PASS'
SOURCE = 'Installed Agent Mouse UI with an explicitly owned HTTP/SSE model fixture'
SCENES = [('dark', 400), ('light', 400), ('dark', 300)]
CAPTURES = ['mouse-635-agent-settings.png', *[
    'mouse-635-agent-chat-' + theme + '-' + str(width) + '.png' for theme, width in SCENES]]


def color(value):
    match = re.fullmatch(r'rgb\(\s*(\d+),\s*(\d+),\s*(\d+)\s*\)', value or '')
    need(match is not None, 'Agent chat requires opaque observed RGB colors')
    rgb = [int(part) for part in match.groups()]
    need(all(0 <= part <= 255 for part in rgb), 'Agent chat RGB channel is invalid')
    linear = [part / 255 / 12.92 if part / 255 <= .04045 else ((part / 255 + .055) / 1.055) ** 2.4 for part in rgb]
    return sum(part * weight for part, weight in zip(linear, (.2126, .7152, .0722)))


def verify(read, *, owner):
    facts = owner.get('agentChat')
    need(isinstance(facts, dict) and facts.get('schema') == 1 and facts.get('source') == SOURCE,
         'installed Agent chat report missing')
    need(facts.get('externalModelVerified') is False and facts.get('nativeTransport') == 'mouse:agent → utilityProcess → HTTP/SSE'
         and not facts.get('fixtureError'), 'Agent chat fixture scope or transport differs')
    N['flags'](facts, ('ordinaryChatWithoutBrowserAccess', 'history', 'streaming', 'stop', 'settings',
                     'errorReply', 'cleanTranscript', 'clear'), 'Agent chat behavior did not complete')
    need(facts.get('requestCount') == 4 and N['finite'](facts.get('elapsedMs')) and 0 < facts['elapsedMs'] <= owner['budgetMs'],
         'Agent chat request count or process budget differs')
    for field in ('firstWorkerPid', 'stoppedWorkerPid'):
        need(N['positive'](facts.get(field)) and facts[field] != owner['pid'], 'Agent chat did not use a separate model worker')
    requests = facts.get('requestMetadata')
    need(isinstance(requests, list) and len(requests) == 4, 'Agent chat HTTP request metadata missing')
    for index, request in enumerate(requests):
        roles = request.get('roles')
        need(request.get('model') == 'mouse635-chat-fixture' and request.get('stream') is True
             and isinstance(roles, list) and roles[0:1] == ['system'] and roles[-1:] == ['user']
             and all(role in ('system', 'user', 'assistant') for role in roles), 'Agent chat streamed model request differs')
        if index == 1:
            need(roles == ['system', 'user', 'assistant', 'user'], 'Agent chat lost the prior question and reply')
    native = owner.get('nativeInputs', [])
    for selector, count in [('#agent-settings-open', 1), ('#agent-endpoint', 1), ('#agent-model', 1),
                            ('#agent-settings-done', 1), ('#agent-task-input', 4), ('#agent-run', 4),
                            ('#agent-chat-stop', 1), ('#agent-new-chat', 1)]:
        events = [row for row in native if row.get('selector') == selector]
        need(len(events) == count, 'Agent chat actual native control input missing: ' + selector)
        for event in events:
            N['input_event'](event, owner['platform'], selector)
    layouts = facts.get('layouts')
    need(isinstance(layouts, list) and len(layouts) == 3, 'Agent chat light/dark/narrow layouts missing')
    widths = []
    for view, (theme, _) in zip(layouts, SCENES):
        need(view.get('theme') == theme and view.get('panelHidden') is False and view.get('settingsOpen') is False
             and view.get('detailsOpen') is False and view.get('terminalOpen') is False and view.get('controlsHidden') is True
             and view.get('rawToolsInChat') is False and view.get('connection') == 'connected'
             and view.get('model') == 'mouse635-chat-fixture', 'Agent chat main surface leaks settings/logs or loses its model')
        panel = N['rect'](view.get('panel'))
        widths.append(panel['width'])
        for part in ('panel', 'header', 'chat', 'composer'):
            box = N['rect'](view.get(part))
            need(N['finite'](box.get('clientWidth')) and N['finite'](box.get('scrollWidth')) and box['clientWidth'] > 0
                 and box['scrollWidth'] <= box['clientWidth'] + 1, 'Agent chat horizontal content overlap: ' + part)
            need(box['x'] >= panel['x'] - 1 and N['right'](box) <= N['right'](panel) + 1,
                 'Agent chat section lies outside its panel')
        need(N['bottom'](view['header']) <= view['chat']['y'] + 1
             and N['bottom'](view['chat']) <= view['composer']['y'] + 1, 'Agent chat header, messages and composer overlap')
        messages = view.get('conversation')
        need(isinstance(messages, list) and [row.get('role') for row in messages] == ['user', 'assistant', 'user', 'assistant']
             and len({row.get('id') for row in messages}) == 4, 'Agent chat conversation is not a stable two-turn transcript')
        for message in messages:
            need(isinstance(message.get('id'), str) and message['id'] and message.get('status') == 'complete'
                 and isinstance(message.get('text'), str) and message['text']
                 and not re.search(r'list_directory|write_file|UNTRUSTED TOOL RESULT|Шаг \d', message['text']), 'Agent chat exposes a tool trace or incomplete response')
            bubble = N['rect'](message.get('bounds'))
            need(bubble['x'] >= view['chat']['x'] and N['right'](bubble) <= N['right'](view['chat']) + 1,
                 'Agent chat message overflows horizontally')
        need(messages[0]['text'] == 'Запомни слово «фиолетовый».'
             and messages[1]['text'] == 'Привет! Запомнил слово «фиолетовый».'
             and 'Вы назвали слово «фиолетовый».' in messages[3]['text'] and 'body { background: #f3edff; }' in messages[3]['text'],
             'Agent chat loses the actual model reply or code block')
        contrast = view.get('contrast', {})
        background = color(contrast.get('background'))
        for field in ('text', 'muted'):
            foreground = color(contrast.get(field))
            need((max(background, foreground) + .05) / (min(background, foreground) + .05) >= 4.5,
                 'Agent chat observed text contrast is insufficient')
    need(abs(widths[0] - widths[1]) <= 1 and widths[0] - widths[2] >= 50,
         'Agent chat narrow layout did not actually resize the panel')
    need(facts.get('captures') == CAPTURES, 'Agent chat canonical OS frame ledger differs')
    evidence = N['Evidence'](read)
    for name in CAPTURES:
        frames = [row for row in owner.get('captures', []) if row.get('filename') == name]
        need(len(frames) == 1, 'Agent chat OS frame absent from owner process: ' + name)
        evidence.screen(frames[0])
    log = read('mouse-635-owner-feedback.log')
    need(isinstance(log, bytes) and MARKER in log.decode('utf-8').splitlines(), 'Agent chat native process marker missing')
    return {'ok': True, 'fixtureOnly': True, 'externalModelVerified': False, 'requestCount': 4,
            'actualPanelWidths': widths, 'nativeCaptures': list(evidence.receipts.values()),
            'inputs': {name: N['sha'](read(name)) for name in [*CAPTURES, *[name[:-4] + '-display.png' for name in CAPTURES]]}}
