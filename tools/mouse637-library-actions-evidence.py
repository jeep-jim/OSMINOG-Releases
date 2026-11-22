#!/usr/bin/env python3
"""Independently bind compact library UI to native menus and received file bytes."""
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import runpy

N = runpy.run_path(str(Path(__file__).with_name('mouse637-native-evidence.py')))
need, rect, finite, sha = (N[k] for k in ('need', 'rect', 'finite', 'sha'))
TEXT = 'Mouse637 owned library text\nНастоящий текстовый файл — данные для переноса.'
QUERY = 'Mouse637 owned library'
SPECS = [
    ('archive-image', 'captures', 'image/png', QUERY + ' image', 'mouse-637-library-source.png', [218, 55, 96]),
    ('archive-text', 'captures', 'text/plain', QUERY + ' text', 'mouse-637-library-source.txt', None),
    ('download-image', 'downloads', 'image/png', QUERY + ' download.png', 'mouse-637-library-download.png', [37, 143, 191]),
]


def png(raw, color, *, width=160, height=96):
    image = N['T']['decode_png'](raw, 'owned637-library-file.png')
    need((image['width'], image['height']) == (width, height), 'library image dimensions differ')
    channels = image['channels']
    expected = bytes(color + ([255] if channels == 4 else []))
    need(channels in (3, 4) and image['pixels'] == expected * (width * height), 'library file pixels differ from the owned image')
    return image


def image_data_url(value, color, *, thumbnail=False):
    need(isinstance(value, str) and value.startswith('data:image/png;base64,') and len(value) <= 200000, 'library preview is not a bounded real PNG')
    try:
        raw = base64.b64decode(value.split(',', 1)[1], validate=True)
    except Exception as error:
        raise ValueError('Invalid library preview PNG') from error
    if not thumbnail:
        return png(raw, color)
    image = N['T']['decode_png'](raw, 'owned637-library-thumbnail.png')
    need(32 < image['width'] <= 480 and 32 < image['height'] <= 320, 'native download preview is not a bounded real thumbnail')
    at = ((image['height'] // 2) * image['width'] + image['width'] // 2) * image['channels']
    need(all(abs(image['pixels'][at + index] - channel) <= 3 for index, channel in enumerate(color)), 'native download thumbnail lost the owned file pixels')
    return image


def file_row(state, file):
    need(state.get('open') is True and state.get('kind') == file['kind'] and state.get('query') == QUERY
         and state.get('view') in ('list', 'grid') and state.get('theme') in ('light', 'dark'), 'library source section/query differs')
    rows = state.get('rows', [])
    need(isinstance(rows, list) and len({row.get('id') for row in rows}) == len(rows), 'library rows are duplicated')
    matches = [row for row in rows if row.get('id') == file['id']]
    need(len(matches) == 1, 'owned file row missing')
    row = matches[0]
    need(row.get('tag') == 'BUTTON' and row.get('aria') == row.get('title') == file['title']
         and row.get('draggable') is True and row.get('controls') == 0, 'file content action/accessibility differs or persistent actions remain')
    opened = rect(row.get('open'))
    need(opened['width'] > 30 and opened['height'] > 30, 'file content is not an actual usable action')
    check = rect(row.get('checkbox', {}).get('bounds'))
    need(N['right'](opened) <= check['x'] + 1 or N['right'](check) <= opened['x'] + 1
         or N['bottom'](opened) <= check['y'] + 1 or N['bottom'](check) <= opened['y'] + 1, 'file content overlaps its selection control')
    if file['kind'] == 'captures':
        need(row.get('content') == (TEXT if file['type'] == 'text/plain' else ''), 'capture repeats its filename or hides the original text')
    else:
        need(row.get('content') == 'PNG', 'completed image contains filename/action clutter')
    if file['type'] == 'image/png':
        image = row.get('image', {})
        rect(image.get('bounds'))
        decoded = image_data_url(image.get('src'), file['rgb'], thumbnail=file['kind'] == 'downloads')
        need(image.get('loaded') is True and image.get('width') == decoded['width'] and image.get('height') == decoded['height'], 'system icon substituted for the file thumbnail')
    return row


def source_point(value, point, file, field='state'):
    row = file_row(value.get(field, {}), file)
    bounds = rect(value.get('contentBounds'))
    opened = row['open']
    need(all(finite(point.get(key)) for key in ('x', 'y'))
         and opened['x'] - 1 <= point['x'] - bounds['x'] <= N['right'](opened) + 1
         and opened['y'] - 1 <= point['y'] - bounds['y'] <= N['bottom'](opened) + 1, 'native file input started outside its content button')


def native_pair(value, owners):
    need(isinstance(value, list) and len(value) == 2, 'library actual native page pair absent')
    for row, owner in zip(value, owners):
        N['native'](row, owner)
    return value


def guest_probe(native):
    return {'name': 'owned library drop target', 'tabId': native['tabId'], 'webContentsId': native['webContentsId'],
            'point': {'x': native['bounds']['x'] + 98, 'y': native['bounds']['y'] + 230}, 'expectedRGB': [32, 123, 164]}


def verify(value, owners, *, evidence, pid, platform, inputs, input_check, origin, captures):
    need(value.get('schema') == 1 and value.get('source') == 'Owned local files, native context menu and OS file drops into live panes'
         and value.get('ok') is True and not value.get('error') and value.get('query') == QUERY, 'native library file proof incomplete')
    pages = value.get('pages', {})
    before, after = pages.get('before', []), pages.get('after', [])
    need(len(before) == len(after) == len(owners) == 2 and pages.get('identityPreserved') is True, 'library live page identity witnesses absent')
    for old, new, owner in zip(before, after, owners):
        N['identity'](old, new, origin); N['identity'](new, owner, origin)
    files = value.get('files', [])
    need(len(files) == 3 and len({file.get('id') for file in files}) == 3, 'three distinct actual library entries required')
    by_key, raw_by_key, raw_inputs = {}, {}, {}
    for file, (key, kind, mime, title, artifact, color) in zip(files, SPECS):
        need((file.get('key'), file.get('kind'), file.get('type'), file.get('title'), file.get('artifact')) == (key, kind, mime, title, artifact)
             and isinstance(file.get('id'), str) and file['id'] and finite(file.get('at')) and file['at'] > 0, 'owned library entry provenance differs')
        extension = '.txt' if mime == 'text/plain' else '.png'
        drag_name = title + extension if kind == 'captures' else title
        need(file.get('dragName') == drag_name and file.get('archiveType') == ('text' if mime == 'text/plain' else 'image'), 'native dragged filename/type differs')
        if kind == 'captures':
            need(re.fullmatch(r'[a-f0-9-]{36}', file['id']) and file.get('filename') == file['id'] + extension, 'capture is not an owned immutable archive copy')
        else:
            need(re.fullmatch(r'mouse637-[a-f0-9-]{36}', file['id']) and file.get('filename') == title, 'download entry differs')
        raw = evidence.read(artifact)
        need(isinstance(raw, bytes) and 0 < len(raw) < 100000 and len(raw) == file.get('size') and sha(raw) == file.get('sha256'), 'archived original library bytes/hash differ')
        if color:
            need(file.get('rgb') == color, 'owned image palette changed'); png(raw, color)
        else:
            need(raw == TEXT.encode('utf-8'), 'archive text source is not the actual owned content')
        by_key[key], raw_by_key[key], raw_inputs[artifact] = file, raw, sha(raw)
    samples = value.get('samples', [])
    need([(row.get('theme'), row.get('view')) for row in samples] == [('light', 'list'), ('light', 'grid'), ('dark', 'list'), ('dark', 'grid')], 'library both themes/list and grid absent')
    witnesses = {}
    for sample in samples:
        state = sample.get('state', {})
        need(state.get('theme') == sample['theme'] and state.get('view') == sample['view'] and len(state.get('rows', [])) == 2, 'library capture UI differs')
        image_row = file_row(state, by_key['archive-image']); file_row(state, by_key['archive-text'])
        need(image_row.get('checkbox', {}).get('checked') is True, 'selected archive copy lost its checkbox state')
        native = native_pair(sample.get('native'), before)
        name = 'mouse-637-library-captures-' + sample['view'] + '-' + sample['theme'] + '.png'
        need(sample.get('capture') == name and name in captures, 'library content OS frame missing')
        image = image_row['image']['bounds']
        witnesses[name] = [{'name': 'owned archive thumbnail', 'entryId': by_key['archive-image']['id'],
                            'point': {'x': image['x'] + image['width'] / 2, 'y': image['y'] + image['height'] / 2}, 'expectedRGB': [218, 55, 96]}, guest_probe(native[0])]
    menus = value.get('menus', [])
    need(len(menus) == 2, 'archive and download native context menus required')
    for menu, file in zip(menus, (by_key['archive-image'], by_key['download-image'])):
        need(menu.get('id') == file['id'] and menu.get('kind') == file['kind'] and menu.get('locale') in ('en', 'ru')
             and finite(menu.get('shownAt')) and finite(menu.get('closedAt')) and menu['closedAt'] >= menu['shownAt'], 'actual native menu did not show and close')
        event = menu.get('input', {})
        need(event in inputs and event.get('selector') == '.library-row[data-id=' + json.dumps(file['id']) + '] .library-file-open'
             and event.get('action') == 'context-menu', 'native context menu belongs to a different file')
        input_check(event, platform, {pid}); source_point(menu, event['point'], file)
        popup = menu.get('popup', {})
        need(N['positive'](popup.get('windowId')) and all(finite(popup.get(k)) for k in ('x', 'y'))
             and all(abs(popup[k] - (event['point'][k] - menu['contentBounds'][k])) <= 1 for k in ('x', 'y')), 'native menu popup anchor differs')
        info, rows = menu.get('metadata', {}), menu.get('items', [])
        en = menu['locale'] == 'en'
        typ = 'PNG · ' + ('Image' if en else 'Изображение') if file['kind'] == 'captures' else 'PNG'
        expected_iso = datetime.fromtimestamp(file['at'] / 1000, timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        labels = info.get('labels', [])
        need(info.get('name') == file['title'] and info.get('type') == typ and info.get('createdAt') == expected_iso and len(labels) == 3
             and labels[:2] == [file['title'], ('Type: ' if en else 'Тип: ') + typ]
             and isinstance(labels[2], str) and labels[2].startswith('Created: ' if en else 'Создано: ') and len(labels[2]) >= 18, 'native context metadata is not the selected entry type/time')
        actions = ['preview', 'copy', 'remove'] if file['kind'] == 'captures' else ['open', 'show', 'remove']
        need(len(rows) == 7 and [row.get('id') for row in rows] == ['mouse-library-info-0', 'mouse-library-info-1', 'mouse-library-info-2', ''] + ['mouse-library-' + action for action in actions]
             and [row.get('label') for row in rows[:3]] == labels and all(row.get('enabled') is False for row in rows[:3])
             and rows[3].get('type') == 'separator' and all(row.get('visible') is True and row.get('enabled') is True for row in rows[4:]), 'native context actions or metadata rows differ')
        keys = ['HOME', 'ENTER'] if file['kind'] == 'captures' else ['ESC']
        need([row.get('key') for row in menu.get('keys', [])] == keys and all(row.get('source') == N['source'](platform) and finite(row.get('at')) for row in menu['keys'])
             and menu.get('previewSelected') is (file['kind'] == 'captures'), 'native menu keyboard completion missing')
    image_menu = menus[0]
    need(image_menu.get('capture') == 'mouse-637-library-context.png' and image_menu['capture'] in captures, 'native file menu OS frame missing')
    image_data_url(image_menu.get('preview', {}).get('src'), by_key['archive-image']['rgb'])
    need(image_menu.get('preview', {}).get('title') == by_key['archive-image']['title'], 'native menu preview opened another copy')
    menu_native = native_pair(image_menu.get('native'), before)
    witnesses[image_menu['capture']] = [guest_probe(menu_native[0])]
    left_frame, right_frame = captures[samples[1]['capture']], captures[image_menu['capture']]
    need(all(left_frame.get(k) == right_frame.get(k) for k in ('pixelSize', 'contentBounds', 'cropPixels', 'mapping')), 'opening a file menu replaced the native window')
    left, right = evidence.screen(left_frame), evidence.screen(right_frame)
    need((left['width'], left['height'], left['channels']) == (right['width'], right['height'], right['channels']), 'menu display dimensions differ')
    changed = sum(max(abs(left['pixels'][i + channel] - right['pixels'][i + channel]) for channel in range(3)) > 12 for i in range(0, len(left['pixels']), left['channels']))
    need(changed > 500, 'native file menu did not change actual OS display pixels')
    text = value.get('textPreview', {})
    event = text.get('input', {})
    need(event in inputs and event.get('selector') == '.library-row[data-id=' + json.dumps(by_key['archive-text']['id']) + '] .library-file-open', 'text file single click missing')
    input_check(event, platform, {pid})
    need(text.get('state') == {'title': by_key['archive-text']['title'], 'text': TEXT, 'nested': 0}, 'plain text preview changed the file or interpreted HTML')
    file_row(value.get('downloadState', {}), by_key['download-image'])
    transfers = value.get('transfers', [])
    need([(row.get('fileKey'), row.get('targetTabId'), row.get('pane')) for row in transfers]
         == [('archive-image', before[0]['id'], 'p1'), ('archive-text', before[1]['id'], 'p2'), ('download-image', before[0]['id'], 'p1')], 'real files did not reach both intended browser panes')
    for transfer in transfers:
        file = by_key[transfer['fileKey']]
        owner = next(row for row in before if row['id'] == transfer['targetTabId'])
        N['identity'](owner, transfer.get('before', {}), origin); N['identity'](transfer['before'], transfer.get('after', {}), origin)
        N['native'](transfer.get('nativeBefore', {}), owner); N['native'](transfer.get('nativeAfter', {}), owner)
        event = transfer.get('input', {})
        need(event in inputs and event.get('action') == 'file-drag' and event.get('selector') == '.library-row[data-id=' + json.dumps(file['id']) + '] .library-file-open', 'file transfer lacks its native source gesture')
        input_check(event, platform, {pid}); source_point(transfer, event['from'], file, 'sourceState')
        box, content = transfer['nativeBefore']['bounds'], transfer['contentBounds']
        need(event.get('to') == {'x': N['jsround'](content['x'] + box['x'] + 98), 'y': N['jsround'](content['y'] + box['y'] + 198)}, 'file gesture ended outside the intended receiver')
        received = transfer.get('received', {})
        need(received.get('trusted') is True and 'Files' in received.get('types', []) and len(received.get('files', [])) == 1
             and any(row.get('trusted') is True and finite(row.get('at')) for row in transfer.get('over', [])), 'file transfer was a synthetic or text-only drop')
        received_file = received['files'][0]
        need((received_file.get('name'), received_file.get('type'), received_file.get('size')) == (file['dragName'], file['type'], file['size'])
             and received_file.get('bytes') == list(raw_by_key[file['key']]), 'actual received File bytes/name/MIME differ from the archived original')
        need(transfer.get('nativeFile') == {'name': file['dragName'], 'size': file['size'], 'sha256': file['sha256'], 'hasIcon': True, 'keys': ['file', 'icon']}, 'Electron drag did not use the owned actual file')
        need(re.fullmatch(r'[a-f0-9]{64}', transfer.get('clipboardBefore', '')) and transfer.get('clipboardAfter') == transfer['clipboardBefore']
             and transfer.get('libraryStillOpen') is True, 'file drag changed the clipboard or closed the library')
    need(value.get('restored') == {'archiveEntries': True, 'downloads': True, 'collectorUnchanged': True}, 'library proof did not restore its isolated data')
    return {'witnesses': witnesses, 'inputs': raw_inputs, 'summary': {'bothThemesAndViews': True, 'nativeContextMetadata': True, 'nativeFilesToBothPanes': True, 'clipboardUnchanged': True}}
