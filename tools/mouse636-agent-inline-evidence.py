#!/usr/bin/env python3
"""Independently bind inline Agent settings to native pages, input and OS bytes.

The model and its HTTP/SSE replies are explicitly owned acceptance fixtures.
This gate proves installed UI/worker behavior, never an external model service.
"""
from pathlib import Path
import re
import runpy

N = runpy.run_path(str(Path(__file__).with_name('mouse636-native-evidence.py')))
need = N['need']
NAME = 'mouse-636-agent-inline.json'
MARKER = 'MOUSE_636_AGENT_INLINE_PASS'
SOURCE = 'Installed Agent Mouse inline settings with an explicitly owned HTTP/SSE model fixture'
SCENES = [('dark', 400), ('light', 400), ('dark', 300), ('light', 300)]
CAPTURES = [f'mouse-636-agent-{part}-{theme}-{width}.png'
            for theme, width in SCENES for part in ('chat', 'settings')]
MODEL = 'mouse636-chat-fixture'
MODEL_CONTROLS = ['agent-endpoint', 'agent-model', 'agent-key', 'agent-vision']
QUESTION = 'Запомни слово «фиолетовый».'
ANSWER = 'Привет! Запомнил слово «фиолетовый».'
FOLLOWUP = 'Какое слово я назвал? Покажи цвет фона.'
STOP_QUESTION = 'Начни длинный ответ для проверки остановки.'
ERROR_QUESTION = 'Проверь сообщение об ошибке.'
OWNERSHIP = ('id', 'index', 'desk', 'webContentsId', 'url', 'navigationEpoch',
             'identity', 'timeOrigin', 'field', 'cookie')
INPUT_COUNTS = {'#agent-settings-open': 8, '#agent-settings-done': 5,
                '#agent-settings-close': 3, '#agent-settings-stop': 1,
                '#agent-endpoint': 1, '#agent-model': 1, '#agent-task-input': 8,
                '#agent-run': 4, '#agent-new-chat': 1}


def color(value):
    match = re.fullmatch(r'rgb\(\s*(\d+),\s*(\d+),\s*(\d+)\s*\)', value or '')
    need(match is not None, 'inline Agent needs opaque observed RGB colors')
    channels = [int(part) for part in match.groups()]
    need(all(0 <= part <= 255 for part in channels), 'inline Agent RGB channel is invalid')
    linear = [part / 255 / 12.92 if part / 255 <= .04045 else
              ((part / 255 + .055) / 1.055) ** 2.4 for part in channels]
    return sum(part * weight for part, weight in zip(linear, (.2126, .7152, .0722)))


def contrast(background, foreground):
    a, b = color(background), color(foreground)
    need((max(a, b) + .05) / (min(a, b) + .05) >= 4.5,
         'inline Agent observed text contrast is insufficient')


def inside(outer, inner, label):
    a, b = N['rect'](outer), N['rect'](inner)
    need(b['x'] >= a['x'] - 1 and b['y'] >= a['y'] - 1
         and N['right'](b) <= N['right'](a) + 1 and N['bottom'](b) <= N['bottom'](a) + 1,
         'inline Agent rectangle lies outside ' + label)


def transcript(ui):
    rows = ui.get('conversation')
    need(isinstance(rows, list) and len(rows) % 2 == 0 and len(rows) <= 8,
         'inline Agent conversation is not the actual fixture transcript')
    identifiers = []
    for index, row in enumerate(rows):
        need(isinstance(row, dict) and isinstance(row.get('id'), str) and row['id']
             and row.get('role') == ('user' if index % 2 == 0 else 'assistant')
             and row.get('status') in ('complete', 'streaming', 'stopped', 'error')
             and isinstance(row.get('text'), str) and row['text']
             and not re.search(r'list_directory|write_file|UNTRUSTED TOOL RESULT|Шаг \d', row['text']),
             'inline Agent transcript is missing a message or exposes a technical log')
        identifiers.append(row['id'])
        if row['role'] == 'user':
            need(row['status'] == 'complete', 'inline Agent user message is not complete')
        if ui.get('chatVisible'):
            bubble = N['rect'](row.get('bounds'))
            need(bubble['x'] >= ui['chatScroll']['x'] - 1
                 and N['right'](bubble) <= N['right'](ui['chatScroll']) + 1,
                 'inline Agent message overflows horizontally')
    need(len(set(identifiers)) == len(identifiers), 'inline Agent message IDs are duplicated')
    return [{key: row[key] for key in ('id', 'role', 'text', 'status')} for row in rows]


def view(ui, settings):
    need(isinstance(ui, dict) and ui.get('panelHidden') is False and ui.get('modals') == []
         and ui.get('settingsTag') == 'section' and ui.get('settingsParent') == 'agent-panel'
         and 'settingsRole' in ui and ui['settingsRole'] is None
         and 'settingsAriaModal' in ui and ui['settingsAriaModal'] is None
         and ui.get('settingsPosition') in ('static', 'relative'),
         'Agent settings are not an internal nonmodal sidebar page')
    need(ui.get('view') == ('settings' if settings else 'chat')
         and ui.get('settingsOpen') is settings and ui.get('settingsVisible') is settings
         and ui.get('chatVisible') is (not settings) and ui.get('composerVisible') is (not settings)
         and ui.get('gearExpanded') == str(settings).lower(), 'inline Agent page visibility is inconsistent')
    need(ui.get('detailsOpen') is False and ui.get('terminalOpen') is False
         and ui.get('rawToolsInChat') is False, 'inline Agent leaks default technical details or terminal')
    need(ui.get('theme') in ('dark', 'light') and ui.get('connection') in ('idle', 'connecting', 'connected', 'error'),
         'inline Agent theme or connection readback is missing')
    parts = ('panel', 'header', 'settings', 'settingsHeader', 'settingsContent', 'settingsFooter') if settings else (
        'panel', 'header', 'chat', 'chatScroll', 'composer')
    for part in parts:
        box = N['rect'](ui.get(part))
        need(N['finite'](box.get('clientWidth')) and box['clientWidth'] > 0
             and N['finite'](box.get('scrollWidth')) and box['scrollWidth'] >= 0
             and box['scrollWidth'] <= box['clientWidth'] + 1, 'inline Agent horizontal overflow: ' + part)
        inside(ui['panel'], box, 'the same Agent panel: ' + part)
    need(N['bottom'](ui['header']) <= ui['settings' if settings else 'chat']['y'] + 1,
         'inline Agent common header overlaps its page')
    if settings:
        need(ui.get('backVisible') is True and ui.get('doneVisible') is True
             and ui.get('sendVisible') is False and ui.get('stopVisible') is False,
             'inline Agent settings lack the return path or show the hidden composer')
        need(N['bottom'](ui['settingsHeader']) <= ui['settingsContent']['y'] + 1
             and N['bottom'](ui['settingsContent']) <= ui['settingsFooter']['y'] + 1,
             'inline Agent settings header/content/footer overlap')
    else:
        need(ui.get('controlsHidden') is True and ui.get('backVisible') is False
             and ui.get('doneVisible') is False and ui.get('settingsStopVisible') is False,
             'inline Agent chat exposes settings controls')
        need(N['bottom'](ui['chatScroll']) <= ui['composer']['y'] + 1,
             'inline Agent messages overlap the composer')
    controls = ui.get('modelControls')
    need(isinstance(controls, list) and [row.get('id') for row in controls] == MODEL_CONTROLS
         and all(type(row.get('disabled')) is bool and row.get('visible') is settings for row in controls),
         'inline Agent model controls have the wrong ownership or visibility')
    draft, selection = ui.get('input'), ui.get('selection', {})
    need(isinstance(draft, str) and all(type(selection.get(k)) is int for k in ('start', 'end'))
         and 0 <= selection['start'] <= selection['end'] <= len(draft)
         and selection.get('direction') in ('none', 'forward', 'backward')
         and isinstance(ui.get('focus'), str) and N['finite'](ui.get('scrollTop')) and ui['scrollTop'] >= 0,
         'inline Agent draft/caret/focus readback is missing')
    colors = ui.get('contrast', {})
    contrast(colors.get('background'), colors.get('text'))
    contrast(colors.get('background'), colors.get('muted'))
    if settings:
        contrast(colors.get('settingsBackground'), colors.get('settingsText'))
    return transcript(ui)


def snapshot(value, settings, origin, owned):
    need(isinstance(value, dict) and value.get('blocked') is False and value.get('surfaceHeld') is False
         and type(value.get('gateSequence')) is int and value['gateSequence'] >= 0,
         'inline Agent settings blocked or held native pages')
    messages = view(value.get('ui'), settings)
    identities, native = value.get('identities'), value.get('native')
    need(isinstance(identities, list) and len(identities) == 2
         and isinstance(native, list) and len(native) == 2,
         'inline Agent must retain two actual live native pages')
    for index, (identity, row) in enumerate(zip(identities, native)):
        need(identity.get('index') == 201 + index, 'inline Agent owned page order differs')
        N['identity'](identity, identity, origin)
        N['native'](row, identity)
        need(all(identity.get(key) == owned[index].get(key) for key in OWNERSHIP),
             'inline Agent changed the owned page/document across scenarios')
    need(len({row['webContentsId'] for row in identities}) == 2
         and len({row['id'] for row in identities}) == 2
         and identities[0]['desk'] == identities[1]['desk'], 'inline Agent page owners are duplicated or cross desktops')
    host = value.get('host', {})
    need(host.get('enabled') is False and host.get('port') == 0 and host.get('folder') == ''
         and host.get('writeAllowed') is False and host.get('commandsAllowed') is False
         and host.get('terminal') is False and host.get('chatDesk') == identities[0]['desk']
         and type(host.get('running')) is bool, 'ordinary inline chat gained browser/file/terminal access')
    running = host['running']
    need(all(row['disabled'] is running for row in value['ui']['modelControls']),
         'inline Agent model can change during an active reply')
    need(value['ui'].get('settingsStopVisible') is (settings and running)
         and value['ui'].get('stopVisible') is (not settings and running)
         and value['ui'].get('sendVisible') is (not settings and not running),
         'inline Agent generation/stop controls do not follow the active page')
    return messages


def verify(read, *, owner):
    evidence = N['Evidence'](read)
    raw, facts = evidence.json(NAME)
    need(isinstance(owner, dict) and owner.get('agentInline') == {
        **facts, 'reportFile': NAME, 'reportSha256': N['sha'](raw)}, 'inline Agent owner/report bytes differ')
    platform, arch = facts.get('platform'), facts.get('arch')
    need((platform, arch) in (('darwin', 'arm64'), ('linux', 'x64'), ('win32', 'x64'))
         and owner.get('platform') == platform and owner.get('arch') == arch
         and facts.get('version') == '6.0.36' and owner.get('version') == '6.0.36'
         and facts.get('schema') == 1 and facts.get('contract') == 'mouse636-agent-inline-v1'
         and facts.get('source') == SOURCE, 'installed inline Agent identity or contract differs')
    need(facts.get('externalModelVerified') is False
         and facts.get('nativeTransport') == 'mouse:agent → utilityProcess → HTTP/SSE'
         and not facts.get('fixtureError') and not facts.get('error') and not facts.get('cleanupErrors'),
         'inline Agent overstated model verification or hid a fixture/cleanup failure')
    N['flags'](facts, ('ok', 'restored', 'ordinaryChatWithoutBrowserAccess', 'history', 'streaming', 'stop',
                     'settings', 'noNativeSuspension', 'draftRestored', 'errorReply', 'cleanTranscript', 'clear'),
               'inline Agent behavior did not finish or restore')
    need(N['positive'](owner.get('pid')) and owner.get('budgetMs') == 240000
         and N['finite'](facts.get('elapsedMs')) and 0 < facts['elapsedMs'] <= owner['budgetMs']
         and facts.get('requestCount') == 4, 'inline Agent process budget or model request count differs')
    for field in ('firstWorkerPid', 'stoppedWorkerPid'):
        need(N['positive'](facts.get(field)) and facts[field] != owner['pid'],
             'inline Agent did not use a separate model worker')
    roles = [['system', 'user'], ['system', 'user', 'assistant', 'user'],
             ['system', 'user', 'assistant', 'user', 'assistant', 'user'],
             ['system', 'user', 'assistant', 'user', 'assistant', 'user', 'user']]
    requests = facts.get('requestMetadata')
    need(isinstance(requests, list) and len(requests) == 4, 'inline Agent HTTP request metadata is missing')
    for request, expected in zip(requests, roles):
        need(request.get('model') == MODEL and request.get('stream') is True and request.get('roles') == expected,
             'inline Agent lost history, included a stopped reply, or changed its streamed model request')
    native = owner.get('nativeInputs')
    need(isinstance(native, list), 'inline Agent native input ledger is missing')
    for selector, count in INPUT_COUNTS.items():
        rows = [row for row in native if row.get('selector') == selector]
        need(len(rows) == count, 'inline Agent actual native input count differs: ' + selector)
        for row in rows:
            N['input_event'](row, platform, selector)
    used_inputs = []

    def click(row, selector):
        N['input_event'](row, platform, selector)
        matches = [index for index, candidate in enumerate(native) if candidate == row]
        need(len(matches) == 1 and matches[0] not in used_inputs, 'inline Agent click is missing, duplicated or reused')
        used_inputs.append(matches[0])

    initial = facts.get('initial', {})
    owned = initial.get('identities', [])
    need(isinstance(owned, list) and len(owned) == 2, 'inline Agent initial page ownership is missing')
    match = re.fullmatch(r'(http://127\.0\.0\.1:([0-9]{1,5}))/page/201/', owned[0].get('url', ''))
    need(match is not None and 0 < int(match[2]) <= 65535, 'inline Agent pages are not the owned loopback HTTP fixture')
    origin = match[1]
    need(snapshot(initial, False, origin, owned) == [] and initial['ui'].get('connection') == 'idle'
         and initial['host']['running'] is False, 'inline Agent did not start with an unconnected empty conversation')

    def transition(row, close_selector, draft=None, intermediate=None):
        need(isinstance(row, dict), 'inline Agent navigation transition is missing')
        before, settings, after = (row.get(key) for key in ('before', 'settings', 'after'))
        before_messages = snapshot(before, False, origin, owned)
        snapshot(settings, True, origin, owned)
        after_messages = snapshot(after, False, origin, owned)
        values = [settings, after]
        if intermediate:
            value = row.get(intermediate)
            snapshot(value, True, origin, owned)
            values.insert(1, value)
        for value in values:
            need(value['gateSequence'] == before['gateSequence'],
                 'inline Agent published a transient modal barrier')
            need(value['ui']['panel'] == before['ui']['panel'] and value['native'] == before['native'],
                 'inline Agent navigation moved, hid or detached existing native views')
            for old, current in zip(before['identities'], value['identities']):
                N['identity'](old, current, origin)
            need(value['ui']['input'] == before['ui']['input'], 'inline Agent navigation lost its existing draft')
        need(after['ui']['selection'] == before['ui']['selection'] and after['ui']['focus'] == 'agent-task-input',
             'inline Agent return did not restore the composer caret/focus')
        if draft is not None:
            need(before['ui']['input'] == draft
                 and before['ui']['selection']['start'] < before['ui']['selection']['end'],
                 'inline Agent did not exercise a real selected draft')
        click(row.get('openInput'), '#agent-settings-open')
        if intermediate == 'stopped':
            click(row.get('stopInput'), '#agent-settings-stop')
        click(row.get('closeInput'), close_selector)
        return before_messages, transcript(settings['ui']), after_messages

    setup = facts.get('setup')
    need(all(not rows for rows in transition(setup, '#agent-settings-done')),
         'inline Agent initial model settings unexpectedly changed the conversation')
    need(setup['after']['ui'].get('model') == MODEL and setup['after']['ui'].get('connection') == 'idle',
         'inline Agent model selection falsely claims a connection')
    flows = facts.get('transitions')
    need(isinstance(flows, list) and [row.get('name') for row in flows] == [
        'stream-completes-in-settings', 'stop-in-settings'], 'inline Agent streaming/settings transitions are missing')
    streaming, stopping = flows
    before, during, complete = transition(streaming, '#agent-settings-close', FOLLOWUP, 'completed')
    need(len(before) == 2 and before == during and before[0]['text'] == QUESTION
         and before[1]['text'] == 'Привет! ' and before[1]['status'] == 'streaming'
         and len(complete) == 2 and complete[0] == before[0]
         and complete[1] == {**before[1], 'text': ANSWER, 'status': 'complete'}
         and transcript(streaming['completed']['ui']) == complete
         and streaming['before']['host']['running'] is True and streaming['settings']['host']['running'] is True
         and streaming['completed']['host']['running'] is False and streaming['after']['host']['running'] is False,
         'inline Agent reply did not actually complete while settings remained visible')
    layouts = facts.get('layouts')
    need(isinstance(layouts, list) and len(layouts) == 4, 'inline Agent needs both themes at 400 and 300 pixels')
    need(facts.get('captures') == CAPTURES, 'inline Agent canonical OS frame order differs')
    reference_messages = None
    for index, (row, (theme, width)) in enumerate(zip(layouts, SCENES)):
        need(row.get('theme') == theme and row.get('width') == width, 'inline Agent theme/width scenario order differs')
        messages, settings_messages, returned = transition(
            row, '#agent-settings-done', f'Черновик сохраняется · {theme} {width}')
        need(messages == settings_messages == returned and len(messages) == 4
             and messages[:2] == complete and messages[2]['text'] == FOLLOWUP
             and all(message['status'] == 'complete' for message in messages)
             and 'Вы назвали слово «фиолетовый».' in messages[3]['text']
             and 'body { background: #f3edff; }' in messages[3]['text'],
             'inline Agent lost the two-turn conversation or the actual model code reply')
        if reference_messages is None:
            reference_messages = messages
        need(messages == reference_messages, 'inline Agent recreated or changed messages between layouts')
        for key in ('before', 'settings', 'after'):
            ui = row[key]['ui']
            need(ui['theme'] == theme and ui['panel']['width'] == width and ui.get('connection') == 'connected'
                 and ui.get('model') == MODEL and row[key]['host']['running'] is False,
                 'inline Agent captured a different theme, width, model or active reply')
        for capture_key, state_key, name in [('chatCapture', 'before', CAPTURES[index * 2]),
                                              ('settingsCapture', 'settings', CAPTURES[index * 2 + 1])]:
            capture = row.get(capture_key)
            frames = [frame for frame in owner.get('captures', []) if frame.get('filename') == name]
            need(isinstance(capture, dict) and capture.get('filename') == name and frames == [capture],
                 'inline Agent OS frame is not the same owner process capture: ' + name)
            evidence.screen(capture)
            viewport = {'x': 0, 'y': 0, 'width': capture['contentBounds']['width'],
                        'height': capture['contentBounds']['height']}
            inside(viewport, row[state_key]['ui']['panel'], 'the actual captured native window')
            for page in row[state_key]['native']:
                inside(viewport, page['bounds'], 'the actual captured native window')
    before, during, stopped = transition(stopping, '#agent-settings-close', ERROR_QUESTION, 'stopped')
    need(len(before) == 6 and before == during and before[:4] == reference_messages
         and before[4]['text'] == STOP_QUESTION and before[5]['text'] == 'Начал длинный ответ. '
         and before[5]['status'] == 'streaming' and len(stopped) == 6 and stopped[:5] == before[:5]
         and stopped[5]['id'] == before[5]['id'] and stopped[5]['status'] == 'stopped'
         and stopped[5]['text'].startswith(before[5]['text']) and transcript(stopping['stopped']['ui']) == stopped
         and stopping['before']['host']['running'] is True and stopping['settings']['host']['running'] is True
         and stopping['stopped']['host']['running'] is False and stopping['after']['host']['running'] is False
         and stopping['stopped']['ui']['focus'] == 'agent-settings-close',
         'inline Agent settings Stop did not end the same active reply and retain usable focus')
    before, during, after = transition(facts.get('errorSettings'), '#agent-settings-close')
    error_settings = facts['errorSettings']['settings']
    need(before == during == after and len(before) == 8 and before[:6] == stopped
         and before[6]['text'] == ERROR_QUESTION and before[7]['status'] == 'error'
         and '503' in before[7]['text'] and error_settings['ui'].get('connection') == 'error'
         and error_settings['ui'].get('settingsProgressVisible') is True
         and 'Не удалось завершить ответ' in error_settings['ui'].get('settingsProgress', '')
         and error_settings['host']['running'] is False,
         'inline Agent hid the actual API error when switching pages')
    need(used_inputs == sorted(used_inputs), 'inline Agent native navigation inputs are out of order')
    log_name = 'mouse-636-owner-feedback.log'
    log = read(log_name)
    need(isinstance(log, bytes) and 0 < len(log) <= 16 * 1024**2 and MARKER in log.decode('utf-8').splitlines(),
         'inline Agent native process marker is missing')
    names = [NAME, log_name, *CAPTURES, *[name[:-4] + '-display.png' for name in CAPTURES]]
    return {'ok': True, 'version': '6.0.36', 'fixtureOnly': True, 'externalModelVerified': False,
            'requestCount': 4, 'settingsInsidePanel': True, 'noNativeSuspension': True,
            'draftAndSelectionRestored': True, 'streamingAndStopInSettings': True,
            'actualPanelWidths': [width for _, width in SCENES], 'canonicalCaptures': list(CAPTURES),
            'reportSha256': N['sha'](raw), 'nativeCaptures': list(evidence.receipts.values()),
            'inputs': {name: N['sha'](read(name)) for name in names}}
