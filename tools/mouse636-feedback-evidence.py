#!/usr/bin/env python3
"""Retain every634 gate and require the separate installed635 owner process."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name('mouse636-reuse.py')))
_retained=_reuse['load']('mouse634-feedback-evidence.py',namespace=globals())
globals().update({key:value for key,value in _retained.items() if not key.startswith('__')})
_verify_634=verify


# Owner635 explicitly relocates privacy to the toolbar and theme next to settings.
# Override only that footer contract; all other retained native checks stay exact.
def verify_footer(read, facts, platform, arch):
    need((facts.get('version'), facts.get('platform'), facts.get('arch')) == (VERSION, platform, arch), 'footer runtime differs')
    flags(facts, ('screenshotOrder', 'balancedIconBoxes', 'groupsSeparated', 'narrowWindowFits', 'centerBurrowRetained', 'documentsInMenu'), 'footer layout')
    cases = facts.get('cases', [])
    need(len(cases) == 6 and {(row.get('theme'), row.get('width')) for row in cases} == {(theme, width) for theme in ('light', 'dark') for width in (800, 1100, 1440)}, 'footer width/theme coverage differs')
    captures = []
    for row in cases:
        need(row.get('label') == 'Эмодзи, масштаб, история, закладки, загрузки и скриншот', 'search footer accessible label differs')
        need(row.get('count') == 6 and row.get('actions') == ['emoji', 'zoom', 'history', 'bookmarks', 'downloads', 'screenshot'] and (row.get('duplicate') is False) and (row.get('overflow', 99) <= 1) and (row.get('gap', 0) >= 12) and (row.get('space', -1) >= 0) and (row.get('right', 9999) <= row['width'] + 1), 'footer group overflow/order differs')
        c = row.get('controls', {})
        need(c.get('left') == ['website'] and c.get('right', [])[-2:] == ['theme-button', 'settings-button'] and c.get('themeBeforeSettings') is True and 'language-select' in c['right'] and 'version-button' in c['right'] and (c['right'].index('language-select') > c['right'].index('version-button')), 'requested footer order differs')
        privacy = c.get('privacy', {})
        need(privacy.get('parent') == 'toolbar' and privacy.get('hit') is True and privacy.get('single') is True and privacy.get('appRegion') == 'no-drag', 'privacy toolbar native hit target missing')
        box = T.rectangle(privacy.get('bounds'), 'privacy toolbar button')
        icon = T.rectangle(privacy.get('icon'), 'privacy toolbar icon')
        toolbar = T.rectangle(privacy.get('toolbar'), 'privacy toolbar')
        need(box.get('right') == box['x'] + box['width'] and 0 <= box['x'] < 120 and box['y'] >= toolbar['y'] and box['y'] + box['height'] <= toolbar['y'] + toolbar['height'] and box['x'] >= toolbar['x'] and box['right'] <= toolbar['x'] + toolbar['width'], 'privacy toolbar placement differs')
        need(icon['width'] == 24 and icon['height'] == 14 and icon['x'] >= box['x'] and icon['x'] + icon['width'] <= box['right'] and icon['y'] >= box['y'] and icon['y'] + icon['height'] <= box['y'] + box['height'], 'privacy toolbar glasses geometry differs')
        if platform == 'darwin':
            traffic = T.rectangle(privacy.get('traffic'), 'macOS traffic space')
            need(traffic.get('right') == traffic['x'] + traffic['width'] and box['x'] >= traffic['right'], 'privacy toolbar overlaps macOS window controls')
        need(c.get('brand', {}).get('width') == 19 and c['brand'].get('height') == 17 and (c.get('source') == ('mouse-head-smooth.svg' if platform == 'win32' else 'mouse-head.svg')), 'mascot proportions/source differ')
        need(c.get('footerSettings') == 1 and c.get('footerDocuments') == c.get('footerFullscreen') == 0 and (type(c.get('footerClosePane')) is int) and (c['footerClosePane'] == 0) and (c.get('documentMenu') is True) and (c.get('groupGap', 0) >= 4) and (c.get('groupSpace', 0) >= 6), 'obsolete controls or cramped groups remain')
        need(c['leftBox']['right'] <= c['nora']['x'] and c['nora']['right'] <= c['rightBox']['x'], 'footer covers the central Nora control')
        need(len(c.get('icons', [])) >= 6, 'icon geometry missing')
        for item in c['icons']:
            icon, button = (item['icon'], item['button'])
            need(icon['width'] == icon['height'] == 15 and abs(icon['x'] + icon['width'] / 2 - button['x'] - button['width'] / 2) <= 1 and (abs(icon['y'] + icon['height'] / 2 - button['y'] - button['height'] / 2) <= 1), 'footer icon sizes or centering differ')
        name = 'mouse-632-footer-' + row['theme'] + '-' + str(row['width']) + '.png'
        blob = read(name)
        image = T.decode_png(blob, name)
        need(image['width'] >= row['width'] and image['height'] >= 500, 'footer screenshot is not the actual viewport')
        captures.append({'name': name, 'sha256': sha(blob)})
    website = facts.get('websiteOffer', {})
    flags(website, ('cancelledWithoutNavigation', 'settingsDistinct', 'confirmedAsNewTab', 'existingTabsPreserved'), 'website offer')
    need(website.get('confirmedUrl') == 'https://mouse.black', 'logo destination differs')
    flags(facts.get('agentAvailability'), ('settingsEntry', 'startEntry', 'providerEntry', 'openedExplicitly', 'disabledUntilEnabled', 'closed', 'pagesPreserved', 'layoutPreserved', 'restoredAfterReload'), 'restored Agent')
    return {'widths': [800, 1100, 1440], 'themes': ['light', 'dark'], 'captures': captures, 'website': website['confirmedUrl'], 'agentRestored': True}

def verify(read,*,expected_platform=None,expected_arch=None):
 result=_verify_634(read,expected_platform=expected_platform,expected_arch=expected_arch)
 current=runpy.run_path(str(Path(__file__).with_name('mouse636-owner-feedback-evidence.py')))['verify'](read,expected_platform=result['platform'],expected_arch=result['arch'])
 return{**result,'owner636':current,'inputs':{**result['inputs'],**current['inputs']}}
