#!/usr/bin/env python3
"""Verify installed search absence and actual omnibox navigation witnesses."""
from pathlib import Path
import re
import runpy
from urllib.parse import parse_qs, urlsplit

N = runpy.run_path(str(Path(__file__).with_name('mouse636-native-evidence.py')))
T = runpy.run_path(str(Path(__file__).with_name('mouse636-task-evidence.py')))
need, sha = N['need'], N['sha']
NAME = 'mouse-636-search-removal.json'
MARKER = 'MOUSE_636_SEARCH_REMOVAL_PASS'
REMOVED = ['mouse-tile-search.cjs', 'mouse-search-service.cjs', 'mouse-search-native-source.cjs',
           'mouse-search-native-dom.cjs', 'mouse-search-views.cjs', 'mouse-search-vision.cjs',
           'mouse-search-page-preload.cjs', 'mouse-search-transport.cjs', 'mouse-search-ca.crt',
           'mouse/search.js', 'mouse/search.css']
RETIRED = ['mouse-634-smoke.cjs', 'mouse-634-search-smoke.cjs', 'mouse-635-smoke.cjs',
           'mouse-635-search-smoke.cjs', 'mouse-635-public-search-smoke.cjs']
ENGINES = {'google': ('www.google.com', '/search', 'q'), 'bing': ('www.bing.com', '/search', 'q'),
           'duckduckgo': ('duckduckgo.com', '/', 'q'), 'yandex': ('yandex.ru', '/search/', 'text')}
FOOTER = ['emoji', 'zoom', 'history', 'bookmarks', 'downloads', 'screenshot']


def ui(value):
    need(value.get('ready') is True and N['positive'](value.get('addressInputs'))
         and value.get('footer') == FOOTER and value.get('footerLabel') in
         ('Эмодзи, масштаб, история, закладки, загрузки и скриншот',
          'Emoji, zoom, history, bookmarks, downloads and screenshot'), 'ordinary footer/navigation missing')
    need(all(value.get(key) is False for key in ('searchButton', 'workspace', 'script', 'style', 'api',
         'onSearch', 'globalController', 'testController', 'bodyOpen')), 'tile search remains in the installed UI/preload')


def host(value):
    need(value == {'observableSupported': True, 'method': 'ipcMain._invokeHandlers + listenerCount',
                  'invokeHandler': False, 'commandListeners': 0, 'stateListeners': 0, 'browserController': False},
         'actual Electron IPC/controller absence was not observed')


def inventory(value):
    rows = value.get('rows')
    need(isinstance(rows, list) and rows and value.get('unownedIds') == value.get('searchPreloadIds') == []
         and len({row.get('id') for row in rows}) == len(rows), 'native webContents inventory is missing or duplicated')
    need(all(N['positive'](row.get('id')) and row.get('owner') in ('app-window', 'browser-tab', 'browser-provider')
         and row.get('preload') != 'mouse-search-page-preload.cjs' and type(row.get('sameBrowserSession')) is bool
         for row in rows), 'hidden/unowned tile search view remains')


def packaged(value):
    need(value.get('removedFiles') == [{'path': name, 'exists': False} for name in REMOVED]
         and value.get('retiredSmokes') == [{'path': name, 'exists': False} for name in RETIRED],
         'installed package contains a retired search component')
    wiring = value.get('wiring', [])
    need([row.get('path') for row in wiring] == ['mouse-main.cjs', 'mouse-preload.cjs', 'mouse/browser.js', 'mouse/index.html'],
         'installed search wiring was not read')
    ordinary = value.get('ordinarySearch', {})
    need(ordinary.get('path') == 'mouse-search.cjs' and ordinary.get('exists') is True,
         'ordinary address search implementation is absent')
    for row in [*wiring, ordinary]:
        text = row.get('text')
        need(isinstance(text, str) and 0 < len(text.encode()) <= 4 * 1024**2
             and row.get('bytes') == len(text.encode()) and row.get('sha256') == sha(text.encode()),
             'installed source bytes differ from their raw receipt')
    patterns = {'mouse-main.cjs': r"require\(['\"]\./mouse-tile-search\.cjs['\"]\)|mouse:tile-search|mouse:search-state",
                'mouse-preload.cjs': r'mouse:tile-search|mouse:search-state',
                'mouse/browser.js': r'MouseSearchUI|searchUI|tile-search|onSearch',
                'mouse/index.html': r'''mouse-search-button|data-action="tile-search"|["']search\.(?:js|css)["']'''}
    need(all(not re.search(patterns[row['path']], row['text']) for row in wiring), 'packaged code still connects tile search')


def verify(read, *, owner):
    evidence = N['Evidence'](read)
    raw, facts = evidence.json(NAME)
    platform, arch = owner.get('platform'), owner.get('arch')
    need(owner.get('searchRemoval') == facts and facts.get('pid') == owner.get('pid')
         and facts.get('platform') == platform and facts.get('arch') == arch
         and facts.get('version') == '6.0.36' and facts.get('schema') == 1
         and facts.get('contract') == 'mouse636-search-removal-v1', 'search removal belongs to another process')
    N['flags'](facts, ('ok', 'restored', 'packaged', 'profileIsolated'), 'installed search removal did not complete')
    need(not facts.get('error') and facts.get('cleanupErrors') == [], 'search removal hid a fixture/cleanup failure')
    packaged(facts.get('packagedFiles', {}))
    host(facts.get('host', {})); host(facts.get('hostAfter', {}))
    inventory(facts.get('native', {}).get('before', {})); inventory(facts.get('native', {}).get('after', {}))
    need(len(facts.get('ui', [])) == 2, 'search absence before and after navigation is required')
    for value in facts['ui']:
        ui(value)
    navigation = facts.get('normalNavigation', {})
    need(navigation.get('navigationMode') == 'owned-request-substitution'
         and navigation.get('externalEngineVerified') is False, 'ordinary navigation overstates external search verification')
    origin = navigation.get('fixtureOrigin', '')
    need(re.fullmatch(r'http://127\.0\.0\.1:\d+', origin), 'ordinary navigation did not use its owned HTTP fixture')
    rows = navigation.get('cases', [])
    need([row.get('engine') for row in rows] == list(ENGINES), 'all four ordinary address engines must be exercised')
    for row in rows:
        hostname, path, parameter = ENGINES[row['engine']]
        url = urlsplit(row.get('requestedURL', ''))
        need(url.scheme == 'https' and url.netloc == hostname and url.path == path and not url.fragment
             and parse_qs(url.query, keep_blank_values=True) == {parameter: [row.get('query')]}
             and row.get('capturedResolvedURL') == row['requestedURL'], 'selected ordinary engine resolved another request')
        need(row.get('navigationMode') == 'owned-request-substitution' and row.get('externalEngineVerified') is False
             and row.get('actualURL') == origin + '/page/60/captured?engine=' + row['engine'], 'owned navigation substitution differs')
        loads = row.get('loads', [])
        need(len(loads) == 1 and loads[0].get('requestedURL') == row['requestedURL']
             and loads[0].get('actualURL') == row['actualURL'], 'actual ordinary guest load was not recorded once')
        N['input_event'](row.get('click'), platform, '.pane[data-pane="p1"] .pane-address input')
        need(row['click'] in owner.get('nativeInputs', []) and row.get('nativeKey', {}).get('accepted') is True
             and row['nativeKey'].get('method') == 'nativeInput.testKey'
             and row['nativeKey'].get('key') == ('Return' if platform == 'linux' else 'ENTER'), 'ordinary native address click/key missing')
        events = row.get('keyboard', [])
        submits = [event for event in events if event.get('type') == 'submit']
        need(any(event.get('type') == 'keydown' and event.get('key') == 'Enter' and event.get('isTrusted') is True for event in events)
             and len(submits) == 1 and submits[0].get('isTrusted') is True and submits[0].get('value') == row['query'],
             'native Enter did not submit the actual address input')
        before, after = row.get('before', {}), row.get('after', {})
        need(row.get('samePageObject') is True and row.get('sameWebContents') is True
             and all(before.get(key) == after.get(key) for key in ('id', 'webContentsId'))
             and after.get('url') == row['actualURL']
             and any(event.get('type') == 'did-navigate' and event.get('url') == row['actualURL'] for event in row.get('navigation', [])),
             'ordinary native tab did not commit its navigation')
        N['identity'](row.get('otherBefore'), row.get('otherAfter'))
        need(len(row.get('native', [])) == 2, 'ordinary navigation lost another page')
        for native, page in zip(row['native'], (after, row['otherAfter'])):
            N['native'](native, page)
    captures = facts.get('captures', [])
    need(len(captures) == 1 and captures[0] in owner.get('captures', []), 'ordinary navigation OS frame missing')
    T['verify_capture'](read, captures[0], 'mouse-636-search-removal.png', [rows[-1]['after'], rows[-1]['otherAfter']])
    names = [NAME, captures[0]['filename'], captures[0]['displayFilename']]
    return {'ok': True, 'reportSha256': sha(raw), 'externalEngineVerified': False,
            'ordinaryEngines': list(ENGINES), 'tileSearchRemoved': True,
            'nativeCaptures': [captures[0]], 'canonicalCaptures': [captures[0]['filename']],
            'inputs': {name: sha(read(name)) for name in names}}
