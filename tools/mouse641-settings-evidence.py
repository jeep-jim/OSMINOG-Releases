#!/usr/bin/env python3
"""Independently read installed settings640 controls, native receipts and PNGs."""
import argparse
import importlib.util
import json
import math
import re
from pathlib import Path

_spec = importlib.util.spec_from_file_location('mouse640_pixels', Path(__file__).with_name('mouse641-task-evidence.py'))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)
VERSION = '6.0.41'
PAGES = ['overview', 'appearance', 'surfaces', 'workspace', 'privacy', 'imports', 'capture', 'downloads', 'documents', 'about']
SECTIONS = ['privacy', 'overview-links', 'appearance', 'surface-theme', 'surface-top', 'surface-bottom', 'surface-workspace', 'interface', 'scale', 'workspace', 'imports', 'passwords', 'adblock-exclusions', 'private-browsing', 'capture', 'downloads', 'documents', 'updates', 'about']


def need(condition, message):
    if not condition:
        raise ValueError('Mouse640 settings: ' + message)


def visible(value):
    return [row.get('id') for row in value.get('sections', []) if row.get('hidden') is False]


def rgba(value):
    match = re.fullmatch(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)', value or '')
    need(match, 'missing actual computed color')
    return [int(match[i]) for i in (1, 2, 3)] + [float(match[4]) if match[4] is not None else 1.0]


def base(value, theme):
    need(value.get('open') is True and value.get('theme') == theme, 'settings theme or open state differs')
    panel, main = P.rectangle(value.get('panel'), 'settings'), P.rectangle(value.get('main'), 'settings content')
    need(main['width'] > 180 and value['main']['scrollWidth'] <= value['main']['clientWidth'] + 1,
         'settings content overflows horizontally')
    need(main['x'] >= panel['x'] and main['y'] >= panel['y'] and main['x'] + main['width'] <= panel['x'] + panel['width'] + 1,
         'settings content is outside its panel')
    need([row.get('id') for row in value.get('sections', [])] == SECTIONS, 'actual retained controls differ')
    nav = value.get('navigation', [])
    need([row.get('id') for row in nav] == PAGES and len({row.get('icon', {}).get('tone') for row in nav}) >= 6,
         'ten distinct categorized navigation items and colored icons are required')
    for row in nav:
        icon = row.get('icon', {})
        need(icon.get('viewBox') == '0 0 24 24' and type(icon.get('paths')) is int and icon['paths'] > 0
             and isinstance(row.get('label'), str) and row['label'].strip() and 'gradient' in icon.get('background', ''),
             'a navigation entry lost its labelled vector icon')
    surface = value.get('surface', {})
    match = re.search(r'blur\(([\d.]+)px\)', surface.get('backdropFilter', ''))
    need(match and 16 <= float(match[1]) <= 40, 'actual glass backdrop blur differs')
    color = rgba(surface.get('backgroundColor'))
    need(.65 <= color[3] < 1 and (max(color[:3]) < 100 if theme == 'dark' else min(color[:3]) > 220),
         'the glass base is opaque, illegible or wrong for its theme')
    need(surface.get('backgroundColor') != value.get('toolbar', {}).get('backgroundColor'), 'settings still uses the old solid toolbar surface')


def overview(value, theme):
    base(value, theme)
    need(value.get('selectedPage') == 'overview' and value.get('query') == '' and visible(value) == ['privacy', 'overview-links'],
         'opening settings must expose only its overview groups')
    ad = value.get('adblock', {})
    need(ad.get('visible') is True and ad.get('receivesPoint') is True and isinstance(ad.get('state'), str) and ad['state'].strip()
         and ad.get('fontSize', 0) >= 12, 'AdBlock state/control is not actually exposed')
    b, m = P.rectangle(ad.get('bounds'), 'adblock'), value['main']
    need(b['width'] >= 44 and b['height'] >= 24 and b['x'] >= m['x'] and b['y'] >= m['y']
         and b['x'] + b['width'] <= m['x'] + m['width'] + 1 and b['y'] + b['height'] <= m['y'] + m['height'] + 1
         and m['scrollTop'] == 0, 'large real AdBlock switch is not visible without scrolling')


def native_input(value, selector, facts):
    source = {'darwin': 'CGEvent', 'win32': 'User32', 'linux': 'XTest'}[facts['platform']]
    need(value in facts.get('nativeInputs', []) and value.get('selector') == selector and value.get('pid') == facts['pid']
         and value.get('source') == source, 'input is not bound to the actual native process ledger')
    need(any(e.get('type') == 'click' and e.get('trusted') is True and e.get('matches') is True for e in value.get('events', [])),
         'missing trusted native click on the actual control')


def keyboard(value, query):
    need(value.get('selector') == '#settings-search' and value.get('value') == query
         and value.get('source') == 'webContents.sendInputEvent and insertText after native focus', 'search input source or value differs')
    events = value.get('events', [])
    need(any(e.get('type') == 'click' and e.get('trusted') is True and e.get('matches') is True for e in events)
         and any(e.get('type') == 'input' and e.get('trusted') is True and e.get('matches') is True for e in events),
         'search lacks real focus and trusted text input')


def capture(read, record, expected_name, state, *, with_switch):
    need(record.get('filename') == expected_name and record.get('source') == 'globalCapture.acquire(display)'
         and record.get('kind') == 'screen' and record.get('backend'), 'not an actual OS display capture')
    blob, full_blob = read(expected_name), read(expected_name[:-4] + '-display.png')
    need(P.digest(blob) == record.get('sha256') and P.digest(full_blob) == record.get('displaySha256')
         and record.get('displayFilename') == expected_name[:-4] + '-display.png', 'capture bytes differ from native receipt')
    image, full = P.decode_png(blob, expected_name), P.decode_png(full_blob, record['displayFilename'])
    need(all(image[k] == record.get('pixelSize', {}).get(k) for k in ('width', 'height'))
         and all(full[k] == record.get('screenPixelSize', {}).get(k) for k in ('width', 'height')), 'native dimensions differ')
    display = P.rectangle(record.get('display', {}).get('bounds'), 'display')
    bounds = P.rectangle(record.get('contentBounds'), 'window content')
    sx, sy = full['width'] / display['width'], full['height'] / display['height']
    left, top = (bounds['x'] - display['x']) * sx, (bounds['y'] - display['y']) * sy
    crop = {'x': math.floor(left), 'y': math.floor(top), 'width': math.ceil(left + bounds['width'] * sx) - math.floor(left),
            'height': math.ceil(top + bounds['height'] * sy) - math.floor(top)}
    need(record.get('cropPixels') == crop and image['width'] == crop['width'] and image['height'] == crop['height'], 'native window crop geometry differs')
    need(crop['x'] >= 0 and crop['y'] >= 0 and crop['x'] + crop['width'] <= full['width'] and crop['y'] + crop['height'] <= full['height'], 'native crop lies outside full display')
    mapping = {'originX': left - crop['x'], 'originY': top - crop['y'], 'scaleX': sx, 'scaleY': sy}
    need(all(P.finite(record.get('mapping', {}).get(k)) and abs(record['mapping'][k] - v) < 1e-8 for k, v in mapping.items()), 'native DPI mapping differs')
    for x in range(0, image['width'], max(1, image['width'] // 37)):
        for y in range(0, image['height'], max(1, image['height'] // 31)):
            need(P.pixel(image, x, y) == P.pixel(full, crop['x'] + x, crop['y'] + y), 'window PNG is not the recorded full-display region')
    def pixels(region):
        rect = P.rectangle(region, 'visible control')
        result = []
        for fx in (.2, .4, .6, .8):
            for fy in (.2, .4, .6, .8):
                x = math.floor(mapping['originX'] + (rect['x'] + rect['width'] * fx) * sx)
                y = math.floor(mapping['originY'] + (rect['y'] + rect['height'] * fy) * sy)
                need(0 <= x < image['width'] and 0 <= y < image['height'], 'control pixel outside native capture')
                result.append(P.pixel(image, x, y))
        need(all(p[3] == 255 for p in result), 'native control pixels are not opaque screen pixels')
        return result
    active = next(row for row in state['navigation'] if row['id'] == state['selectedPage'])
    icon = pixels(active['icon']['bounds'])
    need(sum(max(p[:3]) - min(p[:3]) >= 30 for p in icon) >= 3, 'native capture does not show the colored navigation icon')
    if with_switch:
        shades = [sum(p[:3]) for p in pixels(state['adblock']['bounds'])]
        need(max(shades) - min(shades) >= 30, 'native capture does not show a contrasted visible switch')


def verify(read, expected_platform=None, expected_arch=None):
    artifacts = {}
    def bound(name):
        need(re.fullmatch(r'mouse-(?:637|640)-[a-z0-9.-]+', name) and '..' not in name, 'unsafe artifact name')
        data = read(name)
        artifacts[name] = {'file': name, 'sha256': P.digest(data), 'bytes': len(data)}
        return data
    facts = json.loads(bound('mouse-637-features.json'))
    write = json.loads(bound('mouse-637-features-write.json'))
    need(facts.get('version') == VERSION and facts.get('ok') is True and facts.get('restored') is True
         and facts.get('packaged') is True and facts.get('profileIsolated') is True, 'not a completed installed feature report')
    platform, arch = facts.get('platform'), facts.get('arch')
    need((platform, arch) in [('darwin', 'arm64'), ('linux', 'x64'), ('win32', 'x64')]
         and (expected_platform is None or platform == expected_platform) and (expected_arch is None or arch == expected_arch), 'native platform differs')
    need(type(facts.get('pid')) is int and type(facts.get('restart', {}).get('pid')) is int
         and facts['pid'] != facts['restart']['pid'] and write.get('pid') == facts['pid'], 'distinct installed processes are required')
    report = facts.get('settings640', {})
    need(report == write.get('settings640') and report.get('schema') == 1 and report.get('version') == VERSION and report.get('ok') is True
         and report.get('source') == 'Installed app, trusted native controls and actual OS captures', 'settings raw evidence changed during restart')
    samples = report.get('samples', [])
    need([s.get('theme') for s in samples] == ['light', 'dark'], 'both settings themes are required')
    captures = {c['filename']: c for c in facts.get('captures', [])}
    checked = []
    for sample in samples:
        theme = sample['theme']
        native_input(sample['openInput'], '#settings-button', facts)
        overview(sample['overview'], theme)
        need([row.get('page') for row in sample.get('navigation', [])] == PAGES[1:], 'every category must receive a native click')
        for row in [*sample['navigation'], sample['appearance']]:
            page, state = row['page'], row['readback']
            native_input(row['input'], '#settings-dialog .settings-nav-item[data-settings-page="' + page + '"]', facts)
            base(state, theme)
            need(state.get('query') == '' and state.get('selectedPage') == page and visible(state)
                 and all(section['hidden'] is (page not in section['pages'].split()) for section in state['sections']), 'category reveals the wrong controls')
        need(sample['appearance']['page'] == 'appearance', 'appearance capture belongs to another category')
        need(len(sample.get('search', [])) == 1, 'required AdBlock search is missing')
        for row, query, expected in [(sample['search'][0], 'AdBlock', ['privacy', 'adblock-exclusions']), (sample['empty'], 'mouse-no-such-setting-640', [])]:
            keyboard(row['input'], query)
            state = row['readback']; base(state, theme)
            need(row.get('query') == query and state.get('query') == query and visible(state) == expected
                 and state.get('clearVisible') is True and state.get('emptyVisible') is (not expected), 'search or empty state differs')
        need(sample['search'][0]['readback']['adblock']['receivesPoint'] is True, 'search did not reveal the actual actionable AdBlock control')
        native_input(sample['clearInput'], '#settings-search-clear', facts)
        clear = sample['cleared']; base(clear, theme)
        need(clear.get('query') == '' and clear.get('selectedPage') == 'appearance' and clear.get('focused') == 'settings-search'
             and clear.get('emptyVisible') is False, 'clearing search lost its category or keyboard focus')
        native_input(sample['narrowSelection']['input'], '#settings-dialog .settings-nav-item[data-settings-page="overview"]', facts)
        need(sample['narrowSelection']['readback'] == sample['narrow'], 'narrow selection receipt differs')
        overview(sample['narrow'], theme); overview(sample['wide'], theme)
        need(sample['narrow']['panel']['width'] <= 421 and sample['narrow']['sidebar']['y'] < sample['narrow']['main']['y'], 'narrow layout did not move navigation above content')
        native_input(sample['closeInput'], '#settings-dialog [data-close-dialog]', facts)
        need(sample.get('closed') == {'open': False, 'focused': 'settings-button'}, 'closing settings lost focus restoration')
        for kind, state in [('overview', sample['overview']), ('appearance', sample['appearance']['readback']), ('narrow', sample['narrow'])]:
            name = 'mouse-637-settings-' + kind + '-' + theme + '.png'
            need(sample.get('captures', {}).get(kind) == name and name in captures, 'required native settings capture is missing')
            capture(bound, captures[name], name, state, with_switch=kind != 'appearance')
            checked.append(name)
    return {'schema': 1, 'version': VERSION, 'platform': platform, 'arch': arch, 'ok': True,
            'processes': {'writePid': facts['pid'], 'readPid': facts['restart']['pid']},
            'themes': ['light', 'dark'], 'categories': PAGES, 'nativeCaptures': checked,
            'artifacts': list(artifacts.values())}


def run(directory, *, platform=None, arch=None):
    directory = Path(directory)
    result = verify(lambda name: (directory / name).read_bytes(), platform, arch)
    (directory / 'mouse-640-settings-acceptance.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--platform', choices=['darwin', 'win32', 'linux'])
    parser.add_argument('--arch', choices=['arm64', 'x64'])
    args = parser.parse_args()
    run(args.directory, platform=args.platform, arch=args.arch)
    print('MOUSE_640_SETTINGS_ACCEPTANCE_PASS')
