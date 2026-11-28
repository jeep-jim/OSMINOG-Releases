#!/usr/bin/env python3
"""Explicit641 user-flow replacements; frozen predecessor security gates stay.

These functions verify raw installed receipts. They never translate old facts
into a passing641 claim or treat fixture setup as native input.
"""
from pathlib import Path
import re
import runpy

TOOLS = Path(__file__).resolve().parent


def reader():
    return runpy.run_path(str(TOOLS / 'mouse644-flexible-workspace-evidence.py'))


def need(value, message):
    if not value:
        raise ValueError('Mouse641 retained owner contract: ' + message)


def settings_branding(value):
    for phase in ('initial', 'afterReload'):
        state = value.get(phase, {})
        branding = state.get('branding', {})
        heading, version = branding.get('settingsHeading'), branding.get('versionLabel')
        need(type(branding.get('controlCount')) is int and branding['controlCount'] == 0
             and branding.get('footerText') == '' and branding.get('footerIcon') is True
             and isinstance(heading, str) and heading.strip() and 'mouse browser' not in heading.lower()
             and isinstance(version, str) and version.split()[:1] == ['v6.0.44']
             and 'mouse browser' not in version.lower(),
             'removed brand caption or control returned, or icon/version disappeared: ' + phase)
        toggles = state.get('toggles')
        need(isinstance(toggles, list) and all(isinstance(row, dict)
             and row.get('key') != 'showBrandName' for row in toggles),
             'removed brand control remains in the actual Settings readback: ' + phase)


def link_input(value, platform, pids):
    W = reader()
    need(value.get('action') == 'intercepted-link' and value.get('pid') in pids
         and value.get('source') == W['NATIVE'][platform]
         and value.get('selector') in ('#link-blank', '#link-same', '#ai-preview-link')
         and value.get('evidence') == 'Trusted pointerdown on the exact anchor before isolated click interception'
         and isinstance(value.get('tabId'), str) and value['tabId']
         and type(value.get('webContentsId')) is int and value['webContentsId'] > 0
         and W['P'].finite(value.get('at')) and all(W['P'].finite(value.get('point', {}).get(axis)) for axis in ('x', 'y')),
         'intercepted link is not bound to the actual native process/page/control')
    events = value.get('events', [])
    need(isinstance(events, list) and 0 < len(events) <= 100 and any(
         event.get('type') == 'pointerdown' and event.get('id') == value['selector'][1:]
         and event.get('trusted') is True and event.get('isTrusted') is True and event.get('matches') is True
         and event.get('button') == 0 and event.get('pointerType') == 'mouse'
         and isinstance(event.get('href'), str) and re.fullmatch(r'http://localhost:\d+/page/[34]/', event['href'])
         and W['P'].finite(event.get('at')) for event in events), 'exact owned anchor lacks a trusted primary mouse press')


def compact_headers(compact, keyboard):
    need(len(compact.get('panes', [])) == len(keyboard.get('panes', [])) == 2,
         'tiny/keyboard header receipts are missing')
    for state in (compact, keyboard):
        for pane in state['panes']:
            bounds, header = pane.get('bounds', {}), pane.get('header', {})
            need(header.get('height', 0) >= 28 and header.get('width', 0) > 0
                 and header.get('y', -1) >= bounds.get('y', 0) - 1
                 and header.get('y', 0) + header['height'] <= bounds.get('y', 0) + bounds.get('height', 0) + 1,
                 'a tiny pane hides or clips its header')
    need(compact['panes'][0]['bounds'].get('height', 0) <= 140
         and keyboard['panes'][0].get('focused') is True, 'small-height or native keyboard focus proof missing')


def preview_setup(value, chat, preview, url, source):
    need(value == {'source': source, 'action': 'browser.command(open)', 'url': url,
                   'lane': 'side', 'previewOf': chat, 'id': preview},
         'retained lower preview must be explicitly labelled fixture setup')


def preview_routes(value, platform, pid, inputs):
    rows = value.get('linkRouting', [])
    reader()['verify_ai_link_routes'](rows, platform=platform, pid=pid, inputs=inputs, selectors=['#ai-preview-link'])
    link_input(rows[0]['input'], platform, {pid})
    need(value.get('nativeLinkClick') in rows[0]['input']['events']
         and value['nativeLinkClick'].get('type') == 'pointerdown', 'AI primary pointer receipt differs from its route')


def retained_chat(ai, platform, origin, preview_origin, N):
    rows = ai.get('linkRouting', [])
    reader()['verify_ai_link_routes'](rows, platform=platform, selectors=['#link-blank', '#link-same'])
    need([row.get('url') for row in rows] == [preview_origin + '/page/3/', preview_origin + '/page/4/'],
         'both actual AI link destinations are required')
    before = ai.get('chatBefore', {})
    need(before.get('index') == 2, 'original AI source owner differs')
    for row in rows:
        N['identity'](before, row.get('chatBefore', {}), origin)
        N['identity'](before, row.get('chatAfter', {}), origin)
    for key in ('chatAfterBlank', 'chatAfterClose', 'chatAfter'):
        N['identity'](before, ai.get(key, {}), origin)
    witness = ai.get('chatNavigation', {})
    need(witness.get('source') == 'WebContents navigation events for one native same-window link click'
         and witness.get('tabId') == before.get('id') and witness.get('webContentsId') == before.get('webContentsId')
         and witness.get('targetURL') == preview_origin + '/page/4/' and witness.get('events') == [],
         'isolated link interception must start no source navigation or security epoch')
    return ai['chatAfter']


def retained_ai(ai, platform, pid, primary, preview_origin, inputs, N, ai_split):
    N['flags'](ai, ('ok', 'mainTabsUnchanged', 'chatRestored'), 'retained AI preview changed its original pages')
    need(ai.get('previewSource') == 'explicit existing-preview fixture', 'manual lower-preview scope is not explicit')
    chat = retained_chat(ai, platform, primary, preview_origin, N)
    rows = ai['linkRouting']
    reader()['verify_ai_link_routes'](rows, platform=platform, inputs=inputs, selectors=['#link-blank', '#link-same'])
    for row in rows:
        link_input(row['input'], platform, {pid})
    main_before, main_after = ai.get('mainBefore', []), ai.get('mainAfter', [])
    need(len(main_before) == len(main_after) == 2, 'both original main pages are required')
    for index, (old, new) in enumerate(zip(main_before, main_after)):
        need(old.get('index') == index, 'main fixture order differs')
        N['identity'](old, new, primary)
    before, first, closed, reopened = (ai.get(key, {}) for key in ('before', 'first', 'closed', 'reopened'))
    need(before.get('aiId') == chat['id'] and before.get('previewId') == '' and before.get('aiOpen') is True
         and set(before.get('mainSlots', {}).values()) == {row['id'] for row in main_before}, 'initial AI/main workspace differs')
    slots = before['mainSlots']; old_tabs = {row['id']: row for row in before.get('tabs', [])}
    need(chat['id'] in old_tabs, 'initial native chat missing')
    for route in rows:
        tab = route['tab']; need(tab['id'] not in old_tabs, 'AI link reused an existing tab')
        old_tabs[tab['id']] = {key: tab[key] for key in ('id', 'lane', 'previewOf', 'url')}
    first_id, reopened_id = first.get('previewId'), reopened.get('previewId')
    need(isinstance(first_id, str) and first_id and first_id not in old_tabs
         and isinstance(reopened_id, str) and reopened_id and reopened_id not in old_tabs and reopened_id != first_id,
         'explicit previews are not distinct retained native pages')
    setups = ai.get('previewSetup', [])
    need(len(setups) == 2, 'both explicit lower-preview preparations are required')
    for state, ident, setup in ((first, first_id, setups[0]), (reopened, reopened_id, setups[1])):
        preview_setup(setup, chat['id'], ident, preview_origin + '/page/3/',
                      'Explicit fixture setup for retained lower-pane controls; not a native-link outcome')
        tab = ai_split(state, chat['id'], ident, slots)
        need(tab.get('url') == preview_origin + '/page/3/'
             and {row['id']: row for row in state['tabs'] if row['id'] != ident} == old_tabs
             and len(state['tabs']) == len(old_tabs) + 1, 'preview setup replaced an original or linked main tab')
    need(closed.get('aiId') == chat['id'] and closed.get('previewId') == '' and closed.get('preview', {}).get('hidden') is True
         and closed.get('mainSlots') == slots and {row['id']: row for row in closed.get('tabs', [])} == old_tabs
         and closed.get('chatSlot') == before.get('chatSlot'), 'native preview close changed main tabs or full source viewport')
    native = ai.get('native', [])
    need(len(native) == 2 and [row.get('tabId') for row in native] == [chat['id'], first_id], 'actual split native owners missing')
    N['native'](native[0], chat)
    for row, slot in zip(native, (first['chatSlot'], first['previewSlot'])):
        N['flags'](row, ('visible', 'parentVisible', 'cachedVisible', 'attached'), 'retained native AI preview hidden')
        need(row.get('bounds') == row.get('actualBounds') == N['endpoints'](slot)
             and N['positive'](row.get('webContentsId')), 'retained native split bounds differ')
    N['input_event'](ai.get('closeClick'), platform, '[data-action="close-ai-preview"]')
    return chat, main_before, reopened_id
