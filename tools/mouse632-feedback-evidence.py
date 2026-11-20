#!/usr/bin/env python3
"""Independent632 media, view-only documents and footer acceptance.

The immutable631 page/pixel algorithms are reused with a bounded632 PNG name
namespace. This does not change the retained task/stress checker on disk.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re

VERSION = '6.0.32'
JSON_NAMES = ('mouse-632-media.json', 'mouse-632-documents.json', 'mouse-632-footer.json')
_spec = importlib.util.spec_from_file_location('mouse632_feedback_pixels', Path(__file__).with_name('mouse632-task-evidence.py'))
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)


def need(value, message):
    if not value:
        raise ValueError('Mouse632 feedback: ' + message)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def read_png(read, name, claimed_digest, claimed_size):
    need(isinstance(name, str) and re.fullmatch(r'mouse-632-[a-z0-9-]+\.png', name), 'unsafe632 screenshot name')
    value = read(name)
    need(sha(value) == claimed_digest, name + ' checksum differs')
    image = T.decode_png(value, name)
    expected = T.size(claimed_size, name)
    need(all(image[key] == expected[key] for key in ('width', 'height')), name + ' pixel dimensions differ')
    return image


# The imported function's globals belong to this private module instance.
# All native mapping, ownership and decoded pixel comparisons stay unchanged.
T.read_png = read_png


def flags(value, names, label):
    need(isinstance(value, dict) and all(value.get(name) is True for name in names), label + ' incomplete')


def identity_pairs(before, after, count):
    need(isinstance(before, list) and isinstance(after, list) and len(before) == len(after) == count,
         'missing live page identities')
    need(len({row.get('id') for row in before}) == count, 'duplicate live page identity')
    for a, b in zip(before, after):
        T.verify_identity(a, b)


def native_views(states, pages):
    owners = {page['id']: page for page in pages}
    need(isinstance(states, list) and len(states) == len(owners)
         and all(isinstance(state, dict) for state in states)
         and {state.get('tabId') for state in states} == set(owners),
         'stationary native view owners are incomplete')
    for state in states:
        owner = owners[state['tabId']]
        need(all(state.get(key) == owner[key] for key in ('index', 'desk', 'webContentsId')),
             'stationary native view belongs to a different page')
        flags(state, ('visible', 'parentVisible', 'cachedVisible', 'attached'), 'stationary native view visibility')
        bounds = T.rectangle(state.get('bounds'), 'stationary page')
        view = T.rectangle(state.get('viewBounds'), 'stationary view')
        parent = state.get('parentBounds')
        if parent is not None:
            T.rectangle(parent, 'stationary parent')
        actual = {'x': view['x'] + (parent['x'] if parent else 0),
                  'y': view['y'] + (parent['y'] if parent else 0),
                  'width': view['width'], 'height': view['height']}
        need(actual == bounds == state.get('actualBounds'), 'stationary native view hierarchy differs from page bounds')


def report_scope(facts, platform, arch):
    need(facts.get('version') == VERSION and facts.get('platform') == platform and facts.get('arch') == arch,
         'wrong runtime or platform')
    need(facts.get('ok') is True and facts.get('restored') is True and not facts.get('error') and not facts.get('cleanupError'),
         'native fixture did not complete and restore state')
    flags(facts.get('cleanup'), ('restored', 'desktopStateRestored'), 'fixture cleanup')


def verify_media(read, facts, platform, arch):
    report_scope(facts, platform, arch)
    need(facts.get('physicalMediaKeysVerified') is False and facts.get('externalMusicAccountVerified') is False,
         'local fixture makes an unsupported owner-device or live-account claim')
    need(facts.get('budgetMs') == 55000 and T.finite(facts.get('elapsedMs')) and 0 < facts['elapsedMs'] <= 55000,
         'media fixture exceeded its budget')
    expected = [('native site next-button', 'site-button'), ('automatic audio ended', 'automatic-ended'),
                ('registered MediaSession nexttrack callback', 'media-session-handler'),
                ('repeated title and media metadata burst', 'metadata-burst')]
    rows = facts.get('scenarios')
    need(isinstance(rows, list) and [(row.get('name'), row.get('source')) for row in rows] == expected,
         'missing media input paths')
    pages = None
    for index, row in enumerate(rows):
        before, after = row.get('mediaBefore', {}), row.get('mediaAfter', {})
        need(T.integer(before.get('track')) and T.integer(after.get('track')) and after['track'] > before['track'],
             'track did not advance')
        need(after.get('paused') is False and T.integer(row.get('titleEvents'), 1), 'real playback/title event missing')
        need(row.get('operations') == [], 'media metadata touched native view geometry, visibility or capture')
        identity_pairs(row.get('identitiesBefore'), row.get('identitiesAfter'), 4)
        native_views(row.get('nativeBefore'), row['identitiesBefore'])
        native_views(row.get('nativeAfter'), row['identitiesAfter'])
        need(row.get('nativeBefore') == row.get('nativeAfter') and len(row.get('nativeBefore', [])) == 4,
             'native views changed during stationary media')
        changes = row.get('mutations')
        need(isinstance(changes, list) and len(changes) > 0 and len({change.get('pane') for change in changes}) == 1
             and all(isinstance(change.get('pane'), str) and change['pane'] for change in changes),
             'title changes mutated unrelated pane subtrees or never reached the shell')
        need(row.get('typingFocused') is (None if index == 0 else True), 'another pane lost input focus')
        if pages is not None:
            identity_pairs(pages, row['identitiesBefore'], 4)
        pages = row['identitiesAfter']
    need(facts.get('requests', {}).get('pages') == 4 and T.integer(facts.get('requests', {}).get('media'), 4),
         'fixture reloaded a document or did not load real audio')
    captures = facts.get('captures', [])
    need(len(captures) == 2 and {item.get('theme') for item in captures} == {'light', 'dark'}, 'both media themes missing')
    for item in captures:
        T.verify_capture(read, item, 'mouse-632-media-' + item['theme'] + '.png', pages)
    return {'scenarios': len(rows), 'nativePageCount': len(pages), 'osDisplayCaptures': len(captures),
            'physicalMediaKeysVerified': False, 'externalMusicAccountVerified': False}


def typing(value):
    need(isinstance(value, dict) and isinstance(value.get('before'), str) and value['before']
         and value.get('after') == value['before'] and value.get('nativeInputSource') == 'native pointer click + webContents.insertText',
         'read-only native text insertion was not observed unchanged')


def verify_documents(read, facts, platform, arch):
    report_scope(facts, platform, arch)
    need(facts.get('physicalUserDeviceVerified') is False and facts.get('budgetMs') == 120000
         and T.finite(facts.get('elapsedMs')) and 0 < facts['elapsedMs'] <= 120000, 'document scope or time budget differs')
    flags(facts.get('entry'), ('nora', 'settings', 'nativePicker', 'cancelPreserved'), 'document entry/cancel')
    need(facts['entry'].get('pickerSelection') == 'owned test dialog response', 'unverified system chooser claim')
    need(facts.get('formats') == ['pdf', 'docx', 'xlsx', 'txt', 'md', 'csv', 'tsv', 'json'], 'supported formats were not all viewed')
    pdf = facts.get('pdf', {})
    flags(pdf, ('workerOffMainThread', 'canvasPainted', 'textSelected', 'pageNavigation', 'zoom', 'viewRotation', 'readOnly'), 'PDF viewing')
    need('Mouse632 PDF page' in pdf.get('selection', ''), 'native PDF text selection missing')
    for key in ('first', 'second', 'zoomed', 'rotated'):
        row = pdf.get(key, {})
        need(row.get('workerOffMainThread') is True and T.integer(row.get('dark'), 51)
             and T.integer(row.get('width'), 1) and T.integer(row.get('height'), 1), 'PDF canvas/worker witness missing')
    need('page one' in pdf['first'].get('text', '') and 'page two' in pdf['second'].get('text', '')
         and pdf['first'].get('view', {}).get('page') == 1 and pdf['second'].get('view', {}).get('page') == 2,
         'PDF next/previous page content differs')
    need(pdf['zoomed']['width'] > pdf['first']['width'] and pdf['rotated']['height'] > pdf['rotated']['width']
         and pdf['rotated'].get('view', {}).get('rotation') == 90, 'PDF view zoom/rotation missing')
    flags(facts.get('docx'), ('text', 'table', 'image', 'readOnly', 'typingBlocked'), 'Word view')
    flags(facts.get('xlsx'), ('cells', 'formulaVisible', 'sheetNavigation', 'readOnly', 'typingBlocked'), 'Excel view')
    typing(facts['docx'].get('typing')); typing(facts['xlsx'].get('typing'))
    need(facts['xlsx']['typing']['before'] == '=SUM(A1,A2)' and facts['xlsx'].get('secondSheet') == 'Second sheet retained',
         'spreadsheet formula and second sheet are not the owned original values')
    text = facts.get('text')
    need(isinstance(text, list) and [row.get('extension') for row in text] == ['txt', 'md', 'csv', 'tsv', 'json'], 'text format coverage differs')
    for row in text:
        flags(row, ('readOnly', 'typingBlocked'), 'text view'); typing(row.get('typing'))
    panes = facts.get('twoPanes', {})
    flags(panes, ('ordinaryTabs', 'noExtraWebContents', 'simultaneous', 'resizePreserved'), 'document pane lifecycle')
    need(panes.get('nodeCount') == 2 and len(set(panes.get('documentIds', []))) == 2
         and T.integer(panes.get('webContentsCountBefore'), 1)
         and panes.get('webContentsCountBefore') == panes.get('webContentsCountAfter')
         and panes.get('webContentsIdsBefore') == panes.get('webContentsIdsAfter')
         and len(panes.get('webContentsIdsBefore', [])) == panes['webContentsCountBefore'], 'viewers created native page processes')
    before, after = panes.get('beforeBounds', []), panes.get('afterBounds', [])
    need(len(before) == len(after) == 2 and {item.get('id') for item in before} == set(panes['documentIds'])
         and {item.get('id') for item in after} == set(panes['documentIds']), 'two pane geometry missing')
    for item in before + after:
        T.rectangle(item, 'document pane')
    need(any(abs(item['width'] - next(row['width'] for row in before if row['id'] == item['id'])) > 20 for item in after),
         'native document divider did not move')
    guards = facts.get('guards', {})
    flags(guards, ('draftRejected', 'saveRejected', 'noSaveDialogs', 'noUnsavedPrompts', 'originalHashesUnchanged'), 'write guards')
    need(guards.get('dialogCalls', {}).get('save') == guards.get('dialogCalls', {}).get('message') == 0, 'viewer offered saving')
    rejections = guards.get('rejections', [])
    need(isinstance(rejections, list) and len(rejections) == 18
         and all(isinstance(row, dict) for row in rejections)
         and {row.get('action') for row in rejections} == {'draft', 'save'}
         and {row.get('kind') for row in rejections} == {'pdf', 'docx', 'xlsx', 'text'}, 'native/IPC write rejection coverage missing')
    guarded = {}
    for row in rejections:
        need(isinstance(row.get('id'), str) and row['id'], 'guarded document identity missing')
        guarded.setdefault(row['id'], []).append(row)
        need(row.get('native', {}).get('rejected') is True and row['native'].get('code') == 'MOUSE_DOCUMENT_READ_ONLY'
             and row.get('ipc', {}).get('rejected') is True and 'только для просмотра' in row['ipc'].get('message', ''),
             'document write was accepted by the host')
    need(len(guarded) == 9 and all(len(rows) == 2
         and {row['action'] for row in rows} == {'draft', 'save'}
         and len({row['kind'] for row in rows}) == 1 for rows in guarded.values()),
         'every guarded document requires distinct native/IPC draft and save rejection pairs')
    originals = guards.get('originalFiles', [])
    need(len(originals) == 9 and len({row.get('name') for row in originals}) == 9, 'original document byte witnesses missing')
    for row in originals:
        need(re.fullmatch('[0-9a-f]{64}', row.get('beforeSHA256', '')) is not None
             and row.get('afterSHA256') == row['beforeSHA256'], 'original file was changed')
    privacy = facts.get('privacy', {})
    flags(privacy, ('normalIdsCleared', 'privateIdCleared', 'privateTextAbsentFromProfile'), 'document privacy')
    need(privacy.get('documentsAfter') == 0 and privacy.get('normalProfileContainsPrivateText') is False
         and privacy.get('normalProfileContainsPrivateId') is False, 'private document persisted')
    flags(facts.get('browser'), ('layoutPreserved', 'pageIdentityPreserved'), 'surrounding browser')
    identity_pairs(facts['browser'].get('before'), facts['browser'].get('after'), 2)
    captures = facts.get('captures', [])
    expected = {(kind, theme) for kind in ('pdf', 'docx', 'xlsx', 'text') for theme in ('light', 'dark')} | {('two-panes', 'dark')}
    need(len(captures) == len(expected) and {(row.get('kind'), row.get('theme')) for row in captures} == expected, 'viewer theme captures missing')
    for item in captures:
        name = 'mouse-632-documents-' + item['kind'] + '-' + item['theme'] + '.png'
        need(item.get('filename') == name and item.get('source') == 'BrowserWindow.capturePage (shell document viewer)', 'viewer capture identity differs')
        T.rectangle(item.get('bounds'), 'captured viewer pane')
        read_png(read, name, item.get('sha256'), item.get('pixelSize'))
    return {'formats': facts['formats'], 'unchangedOriginalFiles': len(originals), 'writeRejections': len(rejections), 'captures': len(captures)}


def verify_footer(read, facts, platform, arch):
    need((facts.get('version'), facts.get('platform'), facts.get('arch')) == (VERSION, platform, arch), 'footer runtime differs')
    flags(facts, ('screenshotOrder', 'balancedIconBoxes', 'groupsSeparated', 'narrowWindowFits', 'centerBurrowRetained', 'documentsInMenu'), 'footer layout')
    cases = facts.get('cases', [])
    need(len(cases) == 6 and {(row.get('theme'), row.get('width')) for row in cases} == {(theme, width) for theme in ('light', 'dark') for width in (800, 1100, 1440)}, 'footer width/theme coverage differs')
    captures = []
    for row in cases:
        need(row.get('count') == 5 and row.get('actions') == ['emoji', 'zoom', 'history', 'bookmarks', 'downloads']
             and row.get('duplicate') is False and row.get('overflow', 99) <= 1 and row.get('gap', 0) >= 12
             and row.get('space', -1) >= 0 and row.get('right', 9999) <= row['width'] + 1, 'footer group overflow/order differs')
        c = row.get('controls', {})
        need(c.get('left') == ['website', 'theme', 'privacy', 'screenshot'] and c.get('right', [])[-1:] == ['quit']
             and c['right'].index('language-select') > c['right'].index('version-button'), 'requested footer order differs')
        need(c.get('brand', {}).get('width') == 19 and c['brand'].get('height') == 17
             and c.get('source') == ('mouse-head-smooth.svg' if platform == 'win32' else 'mouse-head.svg'), 'mascot proportions/source differ')
        need(c.get('footerSettings') == c.get('footerDocuments') == c.get('footerFullscreen') == 0
             and c.get('documentMenu') is True and c.get('groupGap', 0) >= 4 and c.get('groupSpace', 0) >= 6,
             'obsolete controls or cramped groups remain')
        need(c['leftBox']['right'] <= c['nora']['x'] and c['nora']['right'] <= c['rightBox']['x'], 'footer covers the central Nora control')
        need(len(c.get('icons', [])) >= 6, 'icon geometry missing')
        for item in c['icons']:
            icon, button = item['icon'], item['button']
            need(icon['width'] == icon['height'] == 15
                 and abs(icon['x'] + icon['width']/2 - button['x'] - button['width']/2) <= 1
                 and abs(icon['y'] + icon['height']/2 - button['y'] - button['height']/2) <= 1, 'footer icon sizes or centering differ')
        name = 'mouse-632-footer-' + row['theme'] + '-' + str(row['width']) + '.png'
        blob = read(name); image = T.decode_png(blob, name)
        need(image['width'] >= row['width'] and image['height'] >= 500, 'footer screenshot is not the actual viewport')
        captures.append({'name': name, 'sha256': sha(blob)})
    website = facts.get('websiteOffer', {})
    flags(website, ('cancelledWithoutNavigation', 'settingsDistinct', 'confirmedAsNewTab', 'existingTabsPreserved'), 'website offer')
    need(website.get('confirmedUrl') == 'https://mouse.black', 'logo destination differs')
    flags(facts.get('manualHelper'), ('singleEntry', 'noStartPromo', 'noProviderPromotion', 'openedExplicitly',
          'disabledUntilEnabled', 'closed', 'pagesPreserved', 'layoutPreserved', 'autoRestoreDisabled'), 'optional helper')
    return {'widths': [800, 1100, 1440], 'themes': ['light', 'dark'], 'captures': captures, 'website': website['confirmedUrl'], 'helperManualOnly': True}


def verify(read, *, expected_platform=None, expected_arch=None):
    files = {name: read(name) for name in JSON_NAMES}
    need(all(isinstance(blob, bytes) and 0 < len(blob) <= 4 * 1024**2 for blob in files.values()), 'new feedback report missing or oversized')
    facts = {name: json.loads(blob) for name, blob in files.items()}
    media = facts[JSON_NAMES[0]]
    platform, arch = media.get('platform'), media.get('arch')
    need((platform, arch) in (('darwin', 'arm64'), ('win32', 'x64')), 'unsupported target')
    need((expected_platform is None or platform == expected_platform) and (expected_arch is None or arch == expected_arch), 'requested target differs')
    return {'ok': True, 'version': VERSION, 'platform': platform, 'arch': arch,
            'inputs': {name: sha(blob) for name, blob in files.items()},
            'media': verify_media(read, media, platform, arch),
            'documents': verify_documents(read, facts[JSON_NAMES[1]], platform, arch),
            'footer': verify_footer(read, facts[JSON_NAMES[2]], platform, arch)}
