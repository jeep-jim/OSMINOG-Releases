#!/usr/bin/env python3
"""Retain byte-frozen634 algorithms with explicit635 identities."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name("mouse635-reuse.py")))
_reuse["load"]('mouse634-context-evidence.py',namespace=globals())


# Owner635 adds an explicit pin action. Keep the original OS input, icon,
# pixel, lifecycle and private-context proof, using the new action positions.
def menu_contract(row, icons, source):
    menu = row.get('menu', {})
    need(finite(menu.get('shownAt')) and finite(menu.get('closedAt')) and (0 < menu['shownAt'] <= menu['closedAt']) and positive(menu.get('popup', {}).get('windowId')) and (menu['popup'].get('x') is None) and (menu['popup'].get('y') is None), 'original native guest Menu popup/close was not observed')
    items = menu.get('items', [])
    need(isinstance(items, list) and 6 <= len(items) <= 100 and ([item.get('id') for item in items[:6]] == [PREFIX + 'bookmark', '', PREFIX + 'pin', PREFIX + 'split-x', PREFIX + 'split-y', PREFIX + 'grid']) and (items[1].get('type') == 'separator'), 'native menu action order differs')
    grid = items[5].get('submenu', [])
    need([item.get('id') for item in grid] == GRID, 'native grid choices differ')
    wanted = [items[0], items[2], items[3], items[4], items[5], *grid]
    labels = {PREFIX + 'pin': ('Закрепить окно', 'Pin pane'), PREFIX + 'bookmark': ('Добавить в избранное', 'Add to favorites') if row['name'] in ('favorite-light', 'private-favorite-dark') else ('Уже в избранном', 'Already in favorites'), PREFIX + 'split-x': ('Разделить справа', 'Split to the right'), PREFIX + 'split-y': ('Разделить снизу', 'Split below'), PREFIX + 'grid': ('Расположение окон', 'Pane layout'), **{PREFIX + 'layout-' + str(count): (str(count) + ' ' + ('окно' if count == 1 else 'окна' if count <= 4 else 'окон'), str(count) + ' ' + ('pane' if count == 1 else 'panes')) for count in (1, 3, 4, 6, 8, 9, 12)}, PREFIX + 'layout-2-x': ('2 окна · рядом', '2 panes · side by side'), PREFIX + 'layout-2-y': ('2 окна · друг над другом', '2 panes · stacked')}
    for item in wanted:
        image = item.get('icon', {})
        need(item.get('visible') is True and isinstance(item.get('enabled'), bool) and (item.get('label') in labels[item['id']]) and (icons.get(image.get('filename')) == image), 'native menu label/visibility/icon differs')
        expected_enabled = item['id'] != PREFIX + 'bookmark' or row['name'] in ('favorite-light', 'private-favorite-dark')
        need(item['enabled'] is expected_enabled, 'native action availability differs')
    need(len({item['icon']['sha256'] for item in grid}) == 9 and items[5]['icon']['sha256'] == grid[4]['icon']['sha256'] and (len({items[3]['icon']['sha256'], items[4]['icon']['sha256'], grid[1]['icon']['sha256'], grid[2]['icon']['sha256'], grid[4]['icon']['sha256'], grid[8]['icon']['sha256']}) == 6), 'split directions and grids do not have distinct native shapes')
    need(items[2]['icon']['sha256'] not in {item['icon']['sha256'] for item in [items[0], items[3], items[4], items[5], *grid]}, 'pin and other actions lack distinct native shapes')
    action = PREFIX + 'bookmark' if 'favorite' in row['name'] else PREFIX + row['name'] if row['name'].startswith('split-') else PREFIX + 'grid'
    choices = [item for item in items if item.get('visible') and item.get('enabled') and (item.get('type') != 'separator')]
    index = next((i for i, item in enumerate(choices) if item.get('id') == action), None)
    need(index is not None, 'chosen native action was unavailable')
    keys = ['HOME'] + ['DOWN'] * index
    if action == PREFIX + 'grid':
        sub = PREFIX + 'layout-' + row['name'][5:]
        keys += ['RIGHT', 'HOME'] + ['DOWN'] * GRID.index(sub)
    keys += ['ENTER']
    input_facts = row.get('input', {})
    events = input_facts.get('keys', [])
    need(input_facts.get('source') == source and [event.get('key') for event in events] == keys and all((event.get('source') == source and finite(event.get('at')) and (menu['shownAt'] <= event['at']) for event in events)) and all((a['at'] <= b['at'] for a, b in zip(events, events[1:]))), 'selection did not use the required native menu keys')
    need(events[-2]['at'] <= menu['closedAt'] if len(events) > 1 else True, 'menu closed before native selection')
    event = input_facts.get('contextEvent', {})
    need(event.get('isTrusted') is True and finite(event.get('timeStamp')) and (event['timeStamp'] >= 0) and all((finite(event.get(key)) and event[key] >= 0 for key in ('x', 'y'))) and all((finite(input_facts.get('rightClick', {}).get(key)) for key in ('x', 'y'))), 'real OS right-click did not produce a trusted guest contextmenu')
