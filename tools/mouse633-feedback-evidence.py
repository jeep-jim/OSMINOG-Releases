#!/usr/bin/env python3
"""Current633 owner contract plus unchanged media and document algorithms.

No facts are relabeled: historical632 report filenames contain runtime633 facts.
The former manual-only helper and Quit button contract is explicitly superseded
by the separately verified633 owner report and current footer controls.
"""
import json
import runpy
from pathlib import Path
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))
R = _reuse['load']('mouse632-feedback-evidence.py')
VERSION = '6.0.33'
JSON_NAMES = ('mouse-632-media.json', 'mouse-632-documents.json',
              'mouse-632-footer.json', 'mouse-633-owner-feedback.json', 'mouse-633-context-menu.json',
              'mouse-629-ui-regressions.json')
need, sha = R['need'], R['sha']
verify_media, verify_documents = R['verify_media'], R['verify_documents']
flags, T = R['flags'], R['T']


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
        need(c.get('left') == ['website', 'theme', 'privacy', 'screenshot'] and c.get('right', [])[-1:] == ['settings-button']
             and c['right'].index('language-select') > c['right'].index('version-button'), 'requested footer order differs')
        need(c.get('brand', {}).get('width') == 19 and c['brand'].get('height') == 17
             and c.get('source') == ('mouse-head-smooth.svg' if platform == 'win32' else 'mouse-head.svg'), 'mascot proportions/source differ')
        need(c.get('footerSettings') == 1 and c.get('footerDocuments') == c.get('footerFullscreen') == 0
             and type(c.get('footerClosePane')) is int and c['footerClosePane'] == 0
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
    flags(facts.get('agentAvailability'), ('settingsEntry', 'startEntry', 'providerEntry', 'openedExplicitly',
          'disabledUntilEnabled', 'closed', 'pagesPreserved', 'layoutPreserved', 'restoredAfterReload'), 'restored Agent')
    return {'widths': [800, 1100, 1440], 'themes': ['light', 'dark'], 'captures': captures, 'website': website['confirmedUrl'], 'agentRestored': True}



CORE_JSON_NAMES = JSON_NAMES[:3]


def verify_retained(read, *, expected_platform=None, expected_arch=None):
    files = {name: read(name) for name in CORE_JSON_NAMES}
    need(all(isinstance(raw, bytes) and 0 < len(raw) <= 4*1024**2
             for raw in files.values()), 'current633 reports missing or oversized')
    facts = {name: json.loads(raw) for name, raw in files.items()}
    media = facts[CORE_JSON_NAMES[0]]
    platform, arch = media.get('platform'), media.get('arch')
    need((platform, arch) in (('darwin', 'arm64'), ('win32', 'x64'), ('linux', 'x64')),
         'unsupported633 target')
    need((expected_platform is None or platform == expected_platform) and
         (expected_arch is None or arch == expected_arch), 'requested target differs')
    return {'ok': True, 'version': VERSION, 'platform': platform, 'arch': arch,
            'inputs': {name: sha(raw) for name, raw in files.items()},
            'media': verify_media(read, media, platform, arch),
            'documents': verify_documents(read, facts[CORE_JSON_NAMES[1]], platform, arch),
            'footer': verify_footer(read, facts[CORE_JSON_NAMES[2]], platform, arch)}


def verify(read, *, expected_platform=None, expected_arch=None):
    result = verify_retained(read, expected_platform=expected_platform, expected_arch=expected_arch)
    raw = read('mouse-633-owner-feedback.json')
    need(isinstance(raw, bytes) and 0 < len(raw) <= 4*1024**2, 'owner633 report missing or oversized')
    owner = runpy.run_path(str(Path(__file__).with_name('mouse633-owner-feedback-evidence.py')))
    current = owner['verify'](read, expected_platform=result['platform'], expected_arch=result['arch'])
    geometry = runpy.run_path(str(Path(__file__).with_name('mouse633-workspace-evidence.py')))
    workspace = geometry['verify'](read, expected_platform=result['platform'], expected_arch=result['arch'])
    return {**result, 'inputs': {**result['inputs'], 'mouse-633-owner-feedback.json': sha(raw),
                              'mouse-633-context-menu.json': current['contextMenu']['reportSha256'],
                              'mouse-629-ui-regressions.json': workspace['reportSha256']},
            'owner': current, 'workspaceGeometry': workspace}
