#!/usr/bin/env python3
"""Independent634 downloads, preview, capture, focus and native search acceptance."""
from pathlib import Path
import re
import runpy
N = runpy.run_path(str(Path(__file__).with_name('mouse636-retained-native-evidence.py')))
D = runpy.run_path(str(Path(__file__).with_name('mouse636-download-evidence.py')))
C = runpy.run_path(str(Path(__file__).with_name('mouse636-capture-evidence.py')))
F = runpy.run_path(str(Path(__file__).with_name('mouse636-focused-evidence.py')))
need, near, rect = (N['need'], N['near'], N['rect'])
NAME = 'mouse-636-retained-owner-feedback.json'
MARKER = 'MOUSE_636_RETAINED_OWNER_FEEDBACK_PASS'

def ai_split(value, chat, preview, slots):
    need(value.get('aiId') == chat and value.get('previewId') == preview and (value.get('aiOpen') is True) and (value.get('mainSlots') == slots) and (value.get('gap') == 6), 'AI split changed owner/main slots')
    a, b, column = (rect(value.get('chat')), rect(value.get('preview')), rect(value.get('column')))
    need(b.get('hidden') is False and a.get('hidden') is False, 'AI split pane hidden')
    near(a['height'], b['height'], 'AI halves differ', 1)
    near(b['y'] - N['bottom'](a), 6, 'AI split gap')
    for x, y in ((a['x'], b['x']), (a['width'], b['width']), (a['x'], column['x']), (N['right'](b), N['right'](column))):
        near(x, y, 'AI column bounds differ')
    need(rect(value.get('chatSlot'))['height'] > 100 and rect(value.get('previewSlot'))['height'] > 100, 'AI native content not visible')
    rows = value.get('tabs', [])
    need(len({r.get('id') for r in rows}) == len(rows), 'duplicate native tab records')
    target = next((r for r in rows if r.get('id') == preview), {})
    need(target.get('previewOf') == chat and target.get('lane') == 'side', 'link escaped into a main/background tab')
    return target

def canceled_chat_navigation(ai, platform, origin, preview_origin):
    before, blank, same, after = (ai.get(key) for key in ('chatBefore', 'chatAfterBlank', 'chatAfterSame', 'chatAfter'))
    need(isinstance(before, dict) and before.get('index') == 2, 'AI chat owner differs')
    N['identity'](before, blank, origin)
    N['input_event'](ai.get('sameClick'), platform, '#link-same', before)
    witness = ai.get('chatNavigation', {})
    events = witness.get('events')
    need(witness.get('source') == 'WebContents navigation events for one native same-window link click' and witness.get('tabId') == before['id'] and (witness.get('webContentsId') == before['webContentsId']) and (witness.get('targetURL') == preview_origin + '/page/4/') and isinstance(events, list) and ([event.get('type') for event in events] == ['did-start-navigation', 'will-navigate']), 'same-window chat requires its exact canceled navigation witness without commit or finish-load')
    need(type(blank.get('navigationEpoch')) is int and blank['navigationEpoch'] >= 0, 'chat security epoch is absent')
    expected_epoch = blank['navigationEpoch'] + 1
    need(all((event.get('url') == witness['targetURL'] and event.get('mainFrame') is True and (event.get('sameDocument') is False) and (type(event.get('navigationEpoch')) is int) and (event['navigationEpoch'] == expected_epoch) and N['positive'](event.get('at')) for event in events)) and events[1].get('prevented') is True and (events[0]['at'] <= events[1]['at']), 'chat navigation was not exactly one prevented main-frame attempt')
    N['identity']({**blank, 'navigationEpoch': expected_epoch}, same, origin)
    N['identity'](same, ai.get('chatAfterClose'), origin)
    N['identity'](ai['chatAfterClose'], after, origin)
    return after

def verify(read, *, expected_platform=None, expected_arch=None):
    evidence = N['Evidence'](read)
    raw, facts = evidence.json(NAME)
    need(facts.get('removedFeatures') == ['tile-search'] and 'search' not in facts, 'retained636 must declare the removed tiled-search surface')
    platform, arch, pid = (facts.get('platform'), facts.get('arch'), facts.get('pid'))
    need((platform, arch) in (('darwin', 'arm64'), ('win32', 'x64'), ('linux', 'x64')) and (expected_platform is None or platform == expected_platform) and (expected_arch is None or arch == expected_arch), 'current native platform/architecture differs')
    need(facts.get('schema') == 1 and facts.get('version') == N['VERSION'] and N['positive'](pid) and (facts.get('source') == 'Installed app, native pointer input, owned HTTP/download fixtures and actual composed/OS pixels') and (facts.get('stage') == 'complete') and (facts.get('budgetMs') == 240000) and N['finite'](facts.get('elapsedMs')) and (0 < facts['elapsedMs'] <= 240000), 'current native runtime/budget incomplete')
    N['flags'](facts, ('ok', 'restored', 'packaged', 'profileIsolated'), 'current native app did not finish or restore')
    need(facts.get('physicalUserDeviceVerified') is False and facts.get('liveExternalAccountsVerified') is False and (not facts.get('error')) and (not facts.get('cleanupError')) and (facts.get('nativeInputSource') == N['source'](platform)), 'native acceptance scope overstated/failed')
    log = read('mouse-636-retained-owner-feedback.log')
    need(isinstance(log, bytes) and 0 < len(log) <= 16 * 1024 ** 2 and (MARKER in log.decode('utf-8').splitlines()), 'current installed process success log missing')
    if platform in ('win32', 'linux'):
        _, wrapper = evidence.json('mouse-' + ('windows' if platform == 'win32' else 'linux') + '-verification.json')
        process = wrapper.get('checks', {}).get('ownerRetained636', {})
        need(process.get('exitCode') == 0 and N['positive'](process.get('pid')) and (process['pid'] == pid) and N['finite'](process.get('elapsedMs')) and (0 < process['elapsedMs'] <= 270000) and (process.get('requiredMarkers') == [MARKER]) and (process.get('reportSha256') == N['sha'](raw)), 'current installed owner process/report byte binding differs')
        if platform == 'linux':
            need(process.get('log') == 'mouse-636-retained-owner-feedback.log' and process.get('logSha256') == N['sha'](log), 'current Linux owner log byte binding differs')
    origins = facts.get('fixtureOrigins', [])
    need(isinstance(origins, list) and len(origins) == 2 and (len(set(origins)) == 2) and all((isinstance(o, str) and re.fullmatch('http://127\\.0\\.0\\.1:\\d+', o) for o in origins)), 'two owned cross-origin fixtures required')
    primary, preview_origin = origins
    ai = facts.get('aiPreview', {})
    N['flags'](ai, ('ok', 'mainTabsUnchanged', 'previewReused', 'chatRestored'), 'AI preview did not preserve its source chat/main pages')
    main_before, main_after = (ai.get('mainBefore', []), ai.get('mainAfter', []))
    need(len(main_before) == len(main_after) == 2, 'both original main pages required')
    for index, (old, new) in enumerate(zip(main_before, main_after)):
        need(old.get('index') == index, 'main fixture order differs')
        N['identity'](old, new, primary)
    main_same = ai.get('mainAfterSame', [])
    need(len(main_same) == 2, 'both main pages after canceled chat navigation are missing')
    for old, new in zip(main_before, main_same):
        N['identity'](old, new, primary)
    chat = canceled_chat_navigation(ai, platform, primary, preview_origin)
    before, first, second, closed, reopened = (ai.get(key, {}) for key in ('before', 'first', 'second', 'closed', 'reopened'))
    need(before.get('aiId') == chat['id'] and before.get('previewId') == '' and (before.get('aiOpen') is True) and (set(before.get('mainSlots', {}).values()) == {o['id'] for o in main_before}), 'initial AI/main workspace differs')
    slots = before['mainSlots']
    old_tabs = {r['id']: r for r in before.get('tabs', [])}
    need(chat['id'] in old_tabs, 'initial native chat missing')
    first_id = first.get('previewId')
    need(isinstance(first_id, str) and first_id and (first_id not in old_tabs), 'first preview must be a distinct side page')
    target = ai_split(first, chat['id'], first_id, slots)
    need(target.get('url') == preview_origin + '/page/3/', 'target=_blank preview URL differs')
    second_target = ai_split(second, chat['id'], first_id, slots)
    need(second_target.get('url') == preview_origin + '/page/4/', 'same-window link did not reuse the preview')
    for current in (first, second):
        need({r['id']: r for r in current['tabs'] if r['id'] != first_id} == old_tabs and len(current['tabs']) == len(old_tabs) + 1, 'AI link created or replaced an unrelated tab')
    need(closed.get('aiId') == chat['id'] and closed.get('previewId') == '' and (closed.get('preview', {}).get('hidden') is True) and (closed.get('mainSlots') == slots) and ({r['id']: r for r in closed.get('tabs', [])} == old_tabs), 'closing preview altered main tabs/chat')
    need(closed.get('chatSlot') == before.get('chatSlot'), 'closing preview did not restore the full chat viewport')
    reopened_id = reopened.get('previewId')
    need(isinstance(reopened_id, str) and reopened_id and (reopened_id != first_id) and (reopened_id not in old_tabs), 'reopened preview reused a destroyed native tab')
    target = ai_split(reopened, chat['id'], reopened_id, slots)
    need(target.get('url') == preview_origin + '/page/3/' and {r['id']: r for r in reopened['tabs'] if r['id'] != reopened_id} == old_tabs, 'reopened preview/main state differs')
    native = ai.get('native', [])
    need(len(native) == 2 and [r.get('tabId') for r in native] == [chat['id'], first_id], 'first actual split native owners missing')
    N['native'](native[0], chat)
    for row, slot in zip(native, (first['chatSlot'], first['previewSlot'])):
        N['flags'](row, ('visible', 'parentVisible', 'cachedVisible', 'attached'), 'native AI preview hidden')
        need(row.get('bounds') == row.get('actualBounds') == N['endpoints'](slot) and N['positive'](row.get('webContentsId')), 'native AI split bounds differ')
    N['input_event'](ai.get('blankClick'), platform, '#link-blank', chat)
    N['input_event'](ai.get('sameClick'), platform, '#link-same', chat)
    N['input_event'](ai.get('closeClick'), platform, '[data-action="close-ai-preview"]')
    main_downloads = facts.get('downloads', {})
    initial = main_downloads.get('stages', [{}])[0].get('identities', [])
    need(len(initial) == 2, 'initial main download owners missing')
    for old, new in zip(initial, main_before):
        N['identity'](old, new, primary)
    ordinary = D['verify'](evidence, main_downloads, platform, arch, pid, ['a', 'b'], initial, [primary, primary])
    right = ai.get('downloads', {})
    right_initial = right.get('stages', [{}])[0].get('identities', [])
    need(len(right_initial) == 2 and right_initial[0].get('id') == chat['id'] and (right_initial[1].get('id') == reopened_id) and (right_initial[1].get('index') == 3), 'right download owners differ')
    N['identity'](chat, right_initial[0], primary)
    N['identity'](right_initial[1], right_initial[1], preview_origin)
    side = D['verify'](evidence, right, platform, arch, pid, ['chat', 'preview'], right_initial, [primary, preview_origin])
    owners = main_before + right_initial
    corners = C['verify'](evidence, facts.get('captureCorners', {}), platform, owners)
    focused = F['verify'](evidence, facts.get('focusedChrome', {}), platform, arch, pid, owners)
    inputs = facts.get('nativeInputs', [])
    need(isinstance(inputs, list) and 15 <= len(inputs) <= 100, 'actual owner native input ledger missing')
    for item in inputs:
        owner = next((o for o in owners if o['id'] == item.get('tabId')), None) if 'tabId' in item else None
        if 'tabId' in item:
            need(owner is not None, 'foreign native input owner')
        N['input_event'](item, platform, item.get('selector'), owner)
    for item in [*main_downloads['nativeInputs'], *right['nativeInputs'], ai['blankClick'], ai['sameClick'], ai['closeClick'], *facts['focusedChrome']['nativeInputs']]:
        need(item in inputs, 'helper native input absent from actual owner ledger')
    for scene in facts['captureCorners']['scenes']:
        for key in ('openInput', 'closeInput', 'themeInput'):
            if key in scene:
                need(scene[key] in inputs, 'screenshot native input missing from owner ledger')
    capture_rows = facts.get('captures', [])
    need(isinstance(capture_rows, list) and 23 <= len(capture_rows) <= 80 and (len({r.get('filename') for r in capture_rows}) == len(capture_rows)), 'native screenshot ledger missing/duplicated')
    for row in capture_rows:
        evidence.screen(row)
    need({r['filename'] for r in capture_rows} == set(evidence.receipts), 'referenced native capture absent from canonical ledger')
    need(any((row['filename'] == 'mouse-634-ai-preview-new-window.png' for row in capture_rows)), 'actual first preview OS image missing')
    requests = facts.get('requests', [])
    need(isinstance(requests, list) and len(requests) == 6 and ([r.get('index') for r in requests] == [0, 1, 2, 3, 4, 3]) and all((N['finite'](r.get('at')) for r in requests)), 'main/chat unexpectedly reloaded or an extra page was requested')
    cleanup = facts.get('cleanup', {})
    N['flags'](cleanup, ('restored', 'desktopStateRestored'), 'original desktop did not restore')
    need(type(cleanup.get('ownedPagesClosed')) is int and cleanup['ownedPagesClosed'] >= 5 and (type(cleanup.get('originalPagesPreserved')) is int) and (cleanup['originalPagesPreserved'] >= 0), 'owned fixtures not closed or original pages unaccounted')
    return {'ok': True, 'version': N['VERSION'], 'platform': platform, 'arch': arch, 'pid': pid, 'reportSha256': N['sha'](raw), 'nativeInputSource': N['source'](platform), 'downloads': ordinary, 'aiPreview': {'chat': chat['id'], 'preview': reopened_id, 'mainTabsPreserved': True, 'downloads': side}, 'captureCorners': corners, 'focusedChrome': focused, 'nativeCaptures': list(evidence.receipts.values()), 'physicalUserDeviceVerified': False}
