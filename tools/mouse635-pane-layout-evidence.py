#!/usr/bin/env python3
"""Require the installed native layout menu and explicit pinned-pane checks."""
from pathlib import Path
import re
import runpy

N = runpy.run_path(str(Path(__file__).with_name('mouse635-native-evidence.py')))
C = runpy.run_path(str(Path(__file__).with_name('mouse635-context-evidence.py')))
need = N['need']
MARKER = 'MOUSE_635_PINNED_PANES_PASS'
SOURCE = 'Installed native Electron Menu, live pane identities and explicit pin IPC'
CAPTURES = ['mouse-635-layout-native-menu.png', 'mouse-635-pane-pinned.png']
GUARDS = ('close', 'replace', 'split', 'resize', 'preset', 'drag', 'transfer')
GRID = ['mouse-context-layout-' + value for value in ('1', '2-x', '2-y', '3', '4', '6', '8', '9', '12')]
DIVIDER = '.divider[data-path=""]'


def resize_state(state, ratio):
    need(isinstance(state, dict) and N['finite'](state.get('ratio')) and abs(state['ratio'] - ratio) < .0001
         and state.get('focused') is True and state.get('activeElement') == {'tag': 'DIV', 'id': '', 'path': ''}
         and state.get('locked') is False and state.get('dragging') is False,
         'native keyboard resize lost divider focus, geometry or unlocked state')


def pin_path(tree, pane):
    if 'id' in tree:
        return [] if tree['id'] == pane else None
    for edge in ('a', 'b'):
        child = pin_path(tree[edge], pane)
        if child is not None:
            return [(tree['axis'], tree['ratio'], edge), *child]
    return None


def verify(read, *, owner):
    facts = owner.get('panes')
    need(isinstance(facts, dict) and facts.get('schema') == 1 and facts.get('source') == SOURCE,
         'installed635 native layout and pinned-pane report missing')
    N['flags'](facts, ('nativeLayoutMenu', 'actualPresetChecked', 'preservesTabOrder', 'pin',
                     'freeSiblingEditable', 'persisted', 'desktopIsolation', 'privateIsolation',
                     'explicitUnpin', 'livePagePreserved'), 'native layout or pinned-pane behavior did not pass')
    guards = facts.get('guards')
    need(isinstance(guards, dict) and set(guards) == set(GUARDS), 'pinned-pane guard coverage differs')
    N['flags'](guards, GUARDS, 'a pinned pane can be modified without an explicit unpin')
    need(N['finite'](facts.get('elapsedMs')) and 0 < facts['elapsedMs'] <= owner['budgetMs'],
         'native layout/pin stage exceeded its process budget')
    before, after = facts.get('pagesBefore'), facts.get('pagesAfter')
    need(isinstance(before, list) and isinstance(after, list) and len(before) == len(after) == 2
         and [page.get('index') for page in before] == [101, 102]
         and len({page.get('id') for page in before}) == len({page.get('webContentsId') for page in before}) == 2,
         'both owned pinned-pane HTTP guests are required')
    for old, new in zip(before, after):
        N['identity'](old, new)
        need(re.fullmatch(r'http://127\.0\.0\.1:\d+/page/' + str(old['index']) + '/', old['url']) is not None,
             'pinned-pane guest is not the actual owned HTTP page')
    initial, pinned, split = (facts.get(name) for name in ('layoutBefore', 'pinned', 'afterFreeSplit'))
    need(C['layout'](initial) == ['p1', 'p2'] and C['layout'](pinned) == ['p1', 'p2']
         and C['layout'](split) == ['p1', 'p3', 'p2'], 'native free-sibling split or original pane order differs')
    need(initial.get('pinnedPanes') == {} and pinned.get('pinnedPanes') == split.get('pinnedPanes') == {'p2': before[1]['id']}
         and initial.get('desktopId') == pinned.get('desktopId') == split.get('desktopId') == before[0]['desk'] == before[1]['desk'],
         'pin belongs to another pane, tab or desktop')
    need(initial['tree'] == {'axis': 'x', 'ratio': .5, 'a': {'id': 'p1'}, 'b': {'id': 'p2'}}
         and pinned['tree'].get('axis') == 'x' and abs(pinned['tree'].get('ratio', 0) - .53) < .0001,
         'native default and custom geometry were not actually exercised')
    pointer = facts.get('resizePointer')
    need(isinstance(pointer, dict) and pointer in owner.get('nativeInputs', []),
         'divider focus was not acquired through the recorded native pointer')
    N['input_event'](pointer, owner['platform'], DIVIDER)
    resize_state(facts.get('resizeAfterClick'), .5)
    inputs = facts.get('resizeInputs')
    need(isinstance(inputs, list) and len(inputs) == 3, 'native repeated keyboard resize receipts missing')
    previous = facts['resizeAfterClick']
    for row, key, before_ratio, after_ratio in zip(inputs, ('RIGHT', 'LEFT', 'RIGHT'), (.5, .53, .5), (.53, .5, .53)):
        need(isinstance(row, dict) and row.get('key') == key and row.get('source') == N['source'](owner['platform'])
             and row.get('before') == previous, 'keyboard resize source, key order or focus continuity differs')
        resize_state(row.get('before'), before_ratio); resize_state(row.get('after'), after_ratio)
        events = row.get('events')
        need(isinstance(events, list) and 0 < len(events) <= 300
             and any(isinstance(event, dict) and event.get('type') == 'keydown'
                     and event.get('key') == ('ArrowRight' if key == 'RIGHT' else 'ArrowLeft')
                     and event.get('trusted') is True and event.get('matches') is True
                     and event.get('selector') == DIVIDER and event.get('target') == 'DIV'
                     and N['finite'](event.get('at')) for event in events),
             'custom geometry lacks the actual trusted focused-divider keydown')
        previous = row['after']
    need(initial['slots'] == pinned['slots'] == {'p1': before[0]['id'], 'p2': before[1]['id']}
         and split['slots'].get('p2') == before[1]['id'] and pin_path(pinned['tree'], 'p2') == pin_path(split['tree'], 'p2'),
         'free-sibling edit changed the pinned tab or ancestor geometry')
    rendered = facts.get('afterFreeSplitRenderer')
    need(C['layout'](rendered) == C['layout'](split) and rendered['tree'] == split['tree']
         and rendered.get('pinnedPanes') == split['pinnedPanes']
         and all((rendered['slots'].get(pane) or '') == (split['slots'].get(pane) or '') for pane in C['layout'](split)),
         'renderer pane geometry differs from the actually committed desktop')
    for name in ('pinnedBoundsBefore', 'pinnedBoundsAfter'):
        N['native'](facts.get(name, {}), before[1])
    need(facts['pinnedBoundsBefore']['bounds'] == facts['pinnedBoundsAfter']['bounds'], 'actual pinned native view moved or resized')
    persistence = facts.get('persistence', {})
    need(persistence.get('key') == 'mouseDesktopsV1' and persistence.get('desktopId') == pinned['desktopId']
         and persistence.get('rehydrated') is True and persistence.get('pinnedPanes') == pinned['pinnedPanes']
         and persistence.get('tree') == split['tree'] and persistence.get('slots') == split['slots'],
         'saved pinned-pane geometry or tab ownership did not survive rehydration')
    private = facts.get('private', {})
    private_before = private.get('before')
    private_panes = C['layout'](private_before)
    need(private_before.get('pinnedPanes') == {}
         and private.get('pinnedPanes') == {private_panes[0]: private_before['slots'].get(private_panes[0]) or ''}
         and not set(private_before['slots'].values()).intersection(page['id'] for page in before),
         'private pin state reused normal pane or tab ownership')
    results = facts.get('guardResults')
    need(isinstance(results, list) and [row.get('action') for row in results] == ['close', 'replace', 'split', 'preset', 'transfer']
         and all(row.get('rejected') is True and isinstance(row.get('message'), str)
                 and re.search('открепите|закреплен|Закрепление', row['message'], re.I) for row in results),
         'actual pinned-pane IPC rejection receipts missing')
    menus = facts.get('menuSnapshots')
    need(isinstance(menus, list) and len(menus) == 5, 'native layout and pin menu snapshots missing')
    for index, menu in enumerate(menus):
        need(N['finite'](menu.get('openedAt')) and N['finite'](menu.get('closedAt'))
             and 0 < menu['openedAt'] <= menu['closedAt']
             and (not index or menus[index-1]['closedAt'] <= menu['openedAt']), 'native menu open/close chronology differs')
        target = menu.get('target', {})
        need(target.get('desk') == pinned['desktopId'] and target.get('pane') in pinned['slots']
             and target.get('id') == pinned['slots'][target['pane']]
             and (index in (1, 2) or target.get('pane') == 'p2'),
             'layout/pin menu belongs to another native tab or desktop')
        items = menu.get('items', [])
        if index < 3:
            need(target.get('kind') == 'layout' and target.get('source') == 'shell'
                 and [item.get('id') for item in items] == GRID
                 and all(item.get('type') == 'checkbox' and item.get('hasIcon') is True and item.get('enabled') is True for item in items),
                 'visible native footer menu lacks the actual nine layout choices')
            need([item['id'] for item in items if item.get('checked')] == ([GRID[1]] if index == 0 else [GRID[2]] if index == 1 else []),
                 'native checked layout does not match actual preset/custom geometry')
        else:
            need(target.get('source') == 'guest' and 'kind' not in target, 'pin action was not a real guest context menu')
            pins = [item for item in items if item.get('id') == 'mouse-context-pin']
            need(len(pins) == 1 and pins[0].get('label') == ('Закрепить окно' if index == 3 else 'Открепить окно')
                 and pins[0].get('enabled') is True and pins[0].get('hasIcon') is True, 'native explicit pin/unpin action differs')
            if index == 4:
                blocked = [item for item in items if item.get('id') in ('mouse-context-split-x', 'mouse-context-split-y')]
                need(len(blocked) == 2 and all(item.get('enabled') is False for item in blocked), 'pinned context menu still permits a split')
    events = [row for row in owner.get('nativeInputs', []) if row.get('selector') == '#layout-menu-button']
    need(events, 'native layout menu was not opened through its visible control')
    for event in events:
        N['input_event'](event, owner['platform'], '#layout-menu-button')
    need(facts.get('captures') == CAPTURES, 'native layout and pinned-pane frame ledger differs')
    evidence = N['Evidence'](read)
    for name in CAPTURES:
        frames = [row for row in owner.get('captures', []) if row.get('filename') == name]
        need(len(frames) == 1, 'native layout or pinned-pane OS frame missing')
        evidence.screen(frames[0])
    log = read('mouse-635-owner-feedback.log')
    need(isinstance(log, bytes) and MARKER in log.decode('utf-8').splitlines(), 'native pinned-pane process marker missing')
    return {'ok': True, 'nativeLayoutMenu': True, 'nativeKeyboardResizeWithRetainedFocus': True,
            'explicitPinAndUnpin': True, 'guards': list(GUARDS),
            'desktopAndPrivateIsolation': True, 'nativeCaptures': list(evidence.receipts.values()),
            'inputs': {name: N['sha'](read(name)) for name in [*CAPTURES, *[name[:-4] + '-display.png' for name in CAPTURES]]}}
