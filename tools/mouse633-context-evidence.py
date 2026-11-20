#!/usr/bin/env python3
"""Independent633 native context-menu evidence; no saved verdict is trusted.

The OS pixels accompany the original Electron Menu observation, trusted guest
right-click, native keyboard selection and resulting real layout/library state.
Pixel differences alone are not treated as proof that a menu was displayed.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import runpy

VERSION = '6.0.33'
NAME = 'mouse-633-context-menu.json'
MARKER = 'MOUSE_633_NATIVE_CONTEXT_MENU_PASS'
SOURCE = 'Installed native Electron Menu and OS input'
DIFFERENCE = 'Full OS frame; any RGB channel absolute difference > tolerance; no masking or freezing'
PREFIX = 'mouse-context-'
GRID = [PREFIX + 'layout-' + value for value in ('1', '2-x', '2-y', '3', '4', '6', '8', '9', '12')]
SCENARIOS = ['favorite-light', 'split-x', 'split-y', 'grid-2-y', 'grid-4', 'grid-12', 'private-favorite-dark']
IDENTITY = ('id', 'index', 'desk', 'webContentsId', 'url', 'navigationEpoch', 'identity', 'timeOrigin', 'field', 'cookie')
_task = runpy.run_path(str(Path(__file__).with_name('mouse633-task-evidence.py')))
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))
_geometry = _reuse['load']('mouse632-feedback-evidence.py')


def need(value, message):
    if not value:
        raise ValueError('Mouse633 context evidence: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def positive(value):
    return type(value) is int and value > 0


def hash_value(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value)


def rectangle(value, label):
    return _task['rectangle'](value, label)


def layout(value):
    need(isinstance(value, dict), 'native layout missing')
    leaves = []

    def visit(node):
        need(isinstance(node, dict) and len(leaves) < 12, 'invalid native layout tree')
        if 'id' in node:
            need(set(node) == {'id'} and isinstance(node['id'], str) and re.fullmatch(r'p\d{1,8}', node['id'])
                 and node['id'] not in leaves, 'invalid or duplicate native pane')
            leaves.append(node['id'])
            return
        need(set(node) == {'axis', 'ratio', 'a', 'b'} and node['axis'] in ('x', 'y')
             and finite(node['ratio']) and .08 <= node['ratio'] <= .92, 'invalid native split')
        visit(node['a'])
        visit(node['b'])

    visit(value.get('tree'))
    slots = value.get('slots')
    need(isinstance(slots, dict) and set(slots) <= set(leaves)
         and all(isinstance(tab, str) for tab in slots.values())
         and len([tab for tab in slots.values() if tab]) == len({tab for tab in slots.values() if tab})
         and value.get('active') in leaves, 'native slot ownership differs')
    return leaves


def preserved(before, after, baseline=None):
    need(isinstance(before, list) and isinstance(after, list) and len(before) == len(after) == 2
         and {row.get('index') for row in before} == {0, 1}
         and len({row.get('id') for row in before}) == len({row.get('webContentsId') for row in before}) == 2,
         'both original native pages are required')
    for old, new in zip(before, after):
        need(all(key in old and old[key] == new.get(key) for key in IDENTITY)
             and positive(old.get('webContentsId')) and finite(old.get('timeOrigin')) and old['timeOrigin'] > 0
             and isinstance(old.get('identity'), str) and old['identity']
             and type(old.get('ticks')) is int and type(new.get('ticks')) is int
             and 0 <= old['ticks'] <= new['ticks'], 'an original page reloaded, froze or lost its state')
        need(isinstance(old.get('url'), str) and re.fullmatch(r'http://127\.0\.0\.1:\d+/page/[01]/', old['url'])
             and old['url'].endswith('/page/' + str(old['index']) + '/')
             and old.get('field') == 'preserved-' + str(old['index']) + '-данные'
             and 'mouse631_' + str(old['index']) + '=' + old['identity'] in old.get('cookie', ''),
             'page state is not the owned native HTTP fixture')
        if baseline is not None:
            initial = next((row for row in baseline if row.get('id') == old['id']), {})
            need(all(initial.get(key) == old[key] for key in IDENTITY), 'context pages differ from their owner process')


def png(read, row):
    name = row.get('filename')
    need(isinstance(name, str) and re.fullmatch(r'mouse-633-context-[a-z0-9-]+\.png', name), 'unsafe native PNG name')
    raw = read(name)
    need(isinstance(raw, bytes) and 0 < len(raw) <= 32*1024**2 and sha(raw) == row.get('sha256'),
         'native PNG bytes/hash differ: ' + name)
    image = _task['decode_png'](raw, name)
    need(row.get('pixelSize') == {'width': image['width'], 'height': image['height']}, 'native PNG dimensions differ')
    return image


def icon(read, row, platform):
    image = png(read, row)
    need(row['filename'] == 'mouse-633-context-icon-' + row['sha256'][:20] + '.png'
         and row.get('logicalSize') == {'width': 16, 'height': 16}
         and image['width'] == image['height'] == 32 and image['channels'] == 4,
         'menu icon is not the actual transparent 2x native image')
    scales = row.get('scales')
    need(isinstance(scales, list) and 2 in scales and all(finite(value) and 0 < value <= 4 for value in scales)
         and len(set(scales)) == len(scales)
         and (row.get('template') is True if platform == 'darwin' else row.get('template') is False or row.get('template') is None),
         'native icon scale/template differs')
    data = image['pixels']
    alpha = data[3::4]
    need(any(0 < value < 255 for value in alpha) and any(value == 255 for value in alpha)
         and all(alpha[y*32+x] == 0 for y in range(32) for x in range(32) if x in (0, 31) or y in (0, 31)),
         'menu icon is clipped or lacks smooth transparent edges')
    need(all(max(data[i:i+3])-min(data[i:i+3]) <= 2 for i in range(0, len(data), 4) if data[i+3]),
         'native icon is not the supplied neutral style')
    return {'filename': row['filename'], 'sha256': row['sha256']}


def display_capture(read, row):
    image = png(read, row)
    need(row.get('source') == 'globalCapture.acquire(display)' and isinstance(row.get('backend'), str) and row['backend']
         and row.get('theme') in ('light', 'dark') and row.get('scope') in ('normal', 'private')
         and row.get('phase') in ('before', 'open'), 'capture is not the actual native display')
    display = row.get('display', {})
    bounds = rectangle(display.get('bounds'), 'context display')
    content = rectangle(row.get('contentBounds'), 'context window')
    need(image['width'] >= 800 and image['height'] >= 500 and finite(display.get('scaleFactor'))
         and display['scaleFactor'] > 0 and content['x'] >= bounds['x'] and content['y'] >= bounds['y']
         and content['x']+content['width'] <= bounds['x']+bounds['width']
         and content['y']+content['height'] <= bounds['y']+bounds['height'],
         'native menu display/window ownership differs')
    return image


def pixel_difference(before, after):
    need((before['width'], before['height']) == (after['width'], after['height']), 'menu display changed dimensions')
    width, height = before['width'], before['height']
    count, left, top, right, bottom = 0, width, height, -1, -1
    a, b = before['pixels'], after['pixels']
    ac, bc = before['channels'], after['channels']
    for y in range(height):
        if ac == bc and a[y*width*ac:(y+1)*width*ac] == b[y*width*bc:(y+1)*width*bc]:
            continue
        for x in range(width):
            p = y*width+x
            if any(abs(a[p*ac+c]-b[p*bc+c]) > 8 for c in (0, 1, 2)):
                count += 1
                left, top, right, bottom = min(left, x), min(top, y), max(right, x), max(bottom, y)
    return {'algorithm': DIFFERENCE, 'region': {'x': 0, 'y': 0, 'width': width, 'height': height},
            'changedPixels': count, 'tolerance': 8,
            'bounds': {'x': left, 'y': top, 'width': right-left+1, 'height': bottom-top+1} if count else None}


def capture_pair(read, row, captures, decoded):
    pair = row.get('capture', {})
    names = []
    for phase in ('before', 'open'):
        facts = pair.get(phase, {})
        name = 'mouse-633-context-' + row['name'] + '-' + phase + '.png'
        need(facts.get('filename') == name and captures.get(name) == facts
             and facts.get('scope') == row['scope'] and facts.get('phase') == phase,
             'menu capture is not bound to its native scenario')
        names.append(name)
    old, new = (pair[key] for key in ('before', 'open'))
    need(old['display'] == new['display'] and old['contentBounds'] == new['contentBounds'] and old['theme'] == new['theme'],
         'display/window/theme changed across the native popup')
    expected = pixel_difference(decoded[names[0]], decoded[names[1]])
    need(pair.get('difference') == expected and expected['changedPixels'] > 500,
         'archived OS menu pixel differences do not match')
    bounds = new['display']['bounds']
    sx, sy = new['pixelSize']['width']/bounds['width'], new['pixelSize']['height']/bounds['height']
    mapping = {'scaleX': sx, 'scaleY': sy, 'originX': bounds['x'], 'originY': bounds['y']}
    need(pair.get('mapping') == mapping, 'native menu display DPI mapping differs')
    point = row['input']['rightClick']
    anchor = {'x': math.floor((point['x']-bounds['x'])*sx+.5), 'y': math.floor((point['y']-bounds['y'])*sy+.5)}
    need(pair.get('anchorPixel') == anchor and 0 <= anchor['x'] < new['pixelSize']['width']
         and 0 <= anchor['y'] < new['pixelSize']['height'], 'menu anchor is outside the captured display')
    return names


def menu_contract(row, icons, source):
    menu = row.get('menu', {})
    need(finite(menu.get('shownAt')) and finite(menu.get('closedAt')) and 0 < menu['shownAt'] <= menu['closedAt']
         and positive(menu.get('popup', {}).get('windowId'))
         and menu['popup'].get('x') is None and menu['popup'].get('y') is None,
         'original native guest Menu popup/close was not observed')
    items = menu.get('items', [])
    need(isinstance(items, list) and 5 <= len(items) <= 100
         and [item.get('id') for item in items[:5]] == [PREFIX+'bookmark', '', PREFIX+'split-x', PREFIX+'split-y', PREFIX+'grid']
         and items[1].get('type') == 'separator', 'native menu action order differs')
    grid = items[4].get('submenu', [])
    need([item.get('id') for item in grid] == GRID, 'native grid choices differ')
    wanted = [items[0], items[2], items[3], items[4], *grid]
    labels = {
        PREFIX+'bookmark': ('Добавить в избранное', 'Add to favorites') if row['name'] in ('favorite-light', 'private-favorite-dark') else ('Уже в избранном', 'Already in favorites'),
        PREFIX+'split-x': ('Разделить справа', 'Split to the right'),
        PREFIX+'split-y': ('Разделить снизу', 'Split below'),
        PREFIX+'grid': ('Расположение окон', 'Pane layout'),
        **{PREFIX+'layout-'+str(count): (str(count)+' '+('окно' if count == 1 else 'окна' if count <= 4 else 'окон'), str(count)+' '+('pane' if count == 1 else 'panes')) for count in (1, 3, 4, 6, 8, 9, 12)},
        PREFIX+'layout-2-x': ('2 окна · рядом', '2 panes · side by side'),
        PREFIX+'layout-2-y': ('2 окна · друг над другом', '2 panes · stacked')}
    for item in wanted:
        image = item.get('icon', {})
        need(item.get('visible') is True and isinstance(item.get('enabled'), bool)
             and item.get('label') in labels[item['id']] and icons.get(image.get('filename')) == image,
             'native menu label/visibility/icon differs')
        expected_enabled = item['id'] != PREFIX+'bookmark' or row['name'] in ('favorite-light', 'private-favorite-dark')
        need(item['enabled'] is expected_enabled, 'native action availability differs')
    need(len({item['icon']['sha256'] for item in grid}) == 9
         and items[4]['icon']['sha256'] == grid[4]['icon']['sha256']
         and len({items[2]['icon']['sha256'], items[3]['icon']['sha256'], grid[1]['icon']['sha256'],
                  grid[2]['icon']['sha256'], grid[4]['icon']['sha256'], grid[8]['icon']['sha256']}) == 6,
         'split directions and grids do not have distinct native shapes')
    action = PREFIX+'bookmark' if 'favorite' in row['name'] else PREFIX+row['name'] if row['name'].startswith('split-') else PREFIX+'grid'
    choices = [item for item in items if item.get('visible') and item.get('enabled') and item.get('type') != 'separator']
    index = next((i for i, item in enumerate(choices) if item.get('id') == action), None)
    need(index is not None, 'chosen native action was unavailable')
    keys = ['HOME'] + ['DOWN']*index
    if action == PREFIX+'grid':
        sub = PREFIX+'layout-'+row['name'][5:]
        keys += ['RIGHT', 'HOME'] + ['DOWN']*GRID.index(sub)
    keys += ['ENTER']
    input_facts = row.get('input', {})
    events = input_facts.get('keys', [])
    need(input_facts.get('source') == source and [event.get('key') for event in events] == keys
         and all(event.get('source') == source and finite(event.get('at')) and menu['shownAt'] <= event['at']
                 for event in events)
         and all(a['at'] <= b['at'] for a, b in zip(events, events[1:])), 'selection did not use the required native menu keys')
    # The ENTER timestamp is recorded after the synchronous OS dispatch. A
    # menu-will-close callback may therefore precede that timestamp slightly.
    need(events[-2]['at'] <= menu['closedAt'] if len(events) > 1 else True, 'menu closed before native selection')
    event = input_facts.get('contextEvent', {})
    need(event.get('isTrusted') is True and finite(event.get('timeStamp')) and event['timeStamp'] >= 0
         and all(finite(event.get(key)) and event[key] >= 0 for key in ('x', 'y'))
         and all(finite(input_facts.get('rightClick', {}).get(key)) for key in ('x', 'y')),
         'real OS right-click did not produce a trusted guest contextmenu')


def changed_tree(tree, target, axis, new_id):
    if 'id' in tree:
        return {'axis': axis, 'ratio': .5, 'a': {'id': target}, 'b': {'id': new_id}} if tree['id'] == target else tree
    return {**tree, 'a': changed_tree(tree['a'], target, axis, new_id), 'b': changed_tree(tree['b'], target, axis, new_id)}


def grid_cells(tree, x=0, y=0, width=1, height=1):
    if 'id' in tree:
        return [(x, y, width, height)]
    ratio = tree['ratio']
    if tree['axis'] == 'x':
        return grid_cells(tree['a'], x, y, width*ratio, height) + grid_cells(tree['b'], x+width*ratio, y, width*(1-ratio), height)
    return grid_cells(tree['a'], x, y, width, height*ratio) + grid_cells(tree['b'], x, y+height*ratio, width, height*(1-ratio))


def effect_contract(row, baseline, private):
    old, new = row.get('beforeLayout'), row.get('afterLayout')
    before, after = layout(old), layout(new)
    target = row.get('target', {})
    normal = row.get('scope') == 'normal'
    page = baseline[1] if normal else {'id': private.get('privateTabId'), 'webContentsId': private.get('privateWebContentsId'), 'url': row.get('effect', {}).get('url')}
    need(target.get('id') == page.get('id') and target.get('webContentsId') == page.get('webContentsId')
         and target.get('source') == 'guest' and target.get('pane') in before
         and old['slots'].get(target['pane']) == target['id']
         and isinstance(target.get('desk'), str) and target['desk']
         and row['input']['contextEvent'].get('url') == page.get('url'), 'action targeted a different native page/pane')
    if normal:
        need(target['desk'] == page['desk'] and len(before) == 2, 'normal context desktop/initial layout differs')
        preserved(row.get('pagesBefore'), row.get('pagesAfter'), baseline)
        _geometry['native_views'](row.get('nativePages'), row['pagesAfter'])
        need(all(item['id'] in new['slots'].values() for item in baseline), 'a context layout hid an original page')
    else:
        need(row.get('pagesBefore') == row.get('pagesAfter') == [] and len(before) == 1,
             'private action borrowed normal-page identities')
    effect = row.get('effect', {})
    if 'favorite' in row['name']:
        bookmark = effect.get('bookmark', {})
        need(effect.get('action') == 'bookmark' and effect.get('library') == row['scope']
             and old['tree'] == new['tree'] and old['slots'] == new['slots']
             and effect.get('url') == page['url'] == bookmark.get('url')
             and isinstance(effect.get('title'), str) and effect['title'] == bookmark.get('title')
             and isinstance(bookmark.get('id'), str) and bookmark['id'], 'favorite did not preserve the layout or exact target')
        if normal:
            need(old['active'] != target['pane'] and effect['url'] != baseline[0]['url'], 'favorite targeted the active page instead of the clicked page')
        else:
            need(private.get('privateBookmarksAfter') == [bookmark], 'private favorite differs from the isolated library')
    elif row['name'].startswith('split-'):
        axis = row['name'][-1]
        new_id = 'p' + str(max(int(pane[1:]) for pane in before)+1)
        need(effect == {'action': 'split', 'axis': axis, 'targetPane': target['pane'], 'beforeCount': 2, 'afterCount': 3}
             and new['tree'] == changed_tree(old['tree'], target['pane'], axis, new_id)
             and len(after) == 3 and all(new['slots'].get(pane) == old['slots'].get(pane) for pane in before),
             'native split changed the wrong pane or direction')
    else:
        count = int(row['name'].split('-')[1])
        axis = 'y' if count == 2 else None
        need(effect == {'action': 'layout', 'count': count, 'axis': axis, 'firstPane': after[0],
                        'firstTabId': target['id'], 'paneIds': after}
             and len(after) == count and new['slots'].get(after[0]) == target['id']
             and (axis is None or new['tree'].get('axis') == axis), 'grid did not retain its requested count/axis/clicked first tab')
        columns, lines = (1, 2) if count == 2 else (2, 2) if count == 4 else (4, 3)
        expected = [(x/columns, y/lines, 1/columns, 1/lines) for x in range(columns) for y in range(lines)]
        need(all(all(abs(a-b) < 1e-8 for a, b in zip(actual, wanted))
                 for actual, wanted in zip(grid_cells(new['tree']), expected)), 'native grid cell geometry differs from its selected preset')


def verify(read, *, expected_platform=None, expected_arch=None, expected_pid=None, expected_pages=None, binding=None):
    raw = read(NAME)
    need(isinstance(raw, bytes) and 0 < len(raw) <= 4*1024**2, 'native context report missing or oversized')
    facts = json.loads(raw)
    need(isinstance(facts, dict), 'native context report must be an object')
    platform, arch = facts.get('platform'), facts.get('arch')
    need(facts.get('schema') == 1 and facts.get('version') == VERSION
         and (platform, arch) in (('darwin', 'arm64'), ('win32', 'x64'), ('linux', 'x64'))
         and (expected_platform is None or platform == expected_platform)
         and (expected_arch is None or arch == expected_arch) and positive(facts.get('pid'))
         and (expected_pid is None or facts['pid'] == expected_pid), 'wrong context native process/runtime')
    need(facts.get('ok') is True and facts.get('restored') is True and not facts.get('error') and not facts.get('cleanupError')
         and facts.get('source') == SOURCE and facts.get('physicalUserDeviceVerified') is False
         and facts.get('budgetMs') == 60000 and finite(facts.get('elapsedMs')) and 0 < facts['elapsedMs'] <= 60000,
         'context process failed, exceeded budget or overstated its scope')
    if binding is not None:
        need(binding == {'report': NAME, 'sha256': sha(raw), 'marker': MARKER}, 'owner-to-context raw report binding differs')
    normal, private = facts.get('normal', {}), facts.get('private', {})
    preserved(normal.get('beforePages'), normal.get('afterPages'), expected_pages)
    baseline = normal['beforePages']
    need(hash_value(normal.get('bookmarksBeforeSHA256')) and normal['bookmarksBeforeSHA256'] == normal.get('bookmarksAfterSHA256'),
         'normal bookmarks were not restored after the owned fixture')
    need(hash_value(private.get('normalBeforeSHA256')) and private['normalBeforeSHA256'] == private.get('normalAfterSHA256')
         and private.get('privateBookmarksBefore') == [] and isinstance(private.get('privateBookmarksAfter'), list)
         and len(private['privateBookmarksAfter']) == 1 and private.get('closed') is True
         and private.get('normalUnchanged') is True and private.get('noPrivateProfileMarker') is True
         and positive(private.get('privateWebContentsId')) and private['privateWebContentsId'] not in {page['webContentsId'] for page in baseline}
         and isinstance(private.get('privateTabId'), str) and private['privateTabId'] not in {page['id'] for page in baseline},
         'private favorite leaked into the normal library/profile or retained its native page')
    private_url = private['privateBookmarksAfter'][0].get('url', '')
    need(re.fullmatch(r'http://127\.0\.0\.1:\d+/mouse633-private-context-[a-z0-9-]+', private_url), 'private favorite is not the separately owned HTTP fixture')
    rows = facts.get('scenarios')
    need(isinstance(rows, list) and [row.get('name') for row in rows] == SCENARIOS
         and [row.get('scope') for row in rows] == ['normal']*6+['private'], 'native context scenario coverage differs')
    icon_rows = facts.get('icons')
    need(isinstance(icon_rows, list) and 12 <= len(icon_rows) <= 20
         and len({row.get('filename') for row in icon_rows}) == len(icon_rows), 'native menu icon archive missing or duplicated')
    icons = {row['filename']: row for row in icon_rows}
    checked_icons = [icon(read, row, platform) for row in icon_rows]
    capture_rows = facts.get('captures')
    need(isinstance(capture_rows, list) and len(capture_rows) == 6
         and len({row.get('filename') for row in capture_rows}) == 6, 'both normal themes and private native menu frames are required')
    captures = {row['filename']: row for row in capture_rows}
    decoded = {name: display_capture(read, row) for name, row in captures.items()}
    used_captures = []
    source = {'darwin': 'CGEvent', 'win32': 'User32', 'linux': 'XTest'}[platform]
    for row in rows:
        menu_contract(row, icons, source)
        effect_contract(row, baseline, private)
        if row['name'] in ('favorite-light', 'split-x', 'private-favorite-dark'):
            used_captures.extend(capture_pair(read, row, captures, decoded))
            theme = 'light' if row['name'] == 'favorite-light' else 'dark'
            need(row['capture']['open']['theme'] == theme, 'native menu theme coverage differs')
        else:
            need('capture' not in row, 'unexpected native menu capture scene')
    need(set(used_captures) == set(captures), 'unbound native menu capture')
    log = read('mouse-633-owner-feedback.log')
    need(isinstance(log, bytes) and 0 < len(log) <= 32*1024**2 and MARKER in log.decode('utf-8').splitlines(),
         'actual native context success marker missing')
    return {'ok': True, 'version': VERSION, 'platform': platform, 'arch': arch, 'pid': facts['pid'],
            'reportSha256': sha(raw), 'nativeScenarios': SCENARIOS, 'icons': checked_icons,
            'captures': [{'filename': name, 'sha256': captures[name]['sha256']} for name in used_captures],
            'normalPagesPreserved': True, 'privateLibraryIsolated': True, 'physicalUserDeviceVerified': False}
