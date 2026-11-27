"""Synthetic settings fixtures and adversarial mutations, never native proof."""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import struct
import unittest
import zlib

TOOLS = Path(__file__).resolve().parent
V = runpy.run_path(str(TOOLS / 'mouse642-settings-evidence.py'))
EXTRA = runpy.run_path(str(TOOLS / 'mouse642-extra-evidence.py'))
PAGES = ['overview', 'appearance', 'surfaces', 'workspace', 'privacy', 'imports', 'capture', 'downloads', 'documents', 'about']
GROUPS = [('privacy', 'overview privacy'), ('overview-links', 'overview'),
          ('appearance', 'appearance'), ('surface-theme', 'surfaces'), ('surface-top', 'surfaces'),
          ('surface-bottom', 'surfaces'), ('surface-workspace', 'surfaces'), ('interface', 'appearance'), ('scale', 'appearance'),
          ('workspace', 'workspace'), ('imports', 'imports'), ('passwords', 'imports'),
          ('adblock-exclusions', 'privacy'),
          ('private-browsing', 'privacy'), ('capture', 'capture'), ('downloads', 'downloads'),
          ('documents', 'documents'), ('updates', 'about'), ('about', 'about')]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def png(*, blank=False):
    width, height = 320, 300
    data = bytearray([45, 53, 65] * width * height)
    if not blank:
        for x, y, w, h, color in [(12, 12, 24, 24, [30, 130, 240]),
                                  (240, 80, 22, 24, [90, 110, 140]),
                                  (262, 80, 22, 24, [245, 245, 245])]:
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    offset = (yy * width + xx) * 3
                    data[offset:offset + 3] = bytes(color)
    def chunk(kind, value):
        return struct.pack('>I', len(value)) + kind + value + struct.pack('>I', zlib.crc32(kind + value) & 0xffffffff)
    rows = b''.join(b'\0' + data[y * width * 3:(y + 1) * width * 3] for y in range(height))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b'')


def fixture(platform='linux'):
    """Small synthetic receipts; no installed process or native input occurs."""
    files, inputs, samples, captures = {}, [], [], []
    source = {'darwin': 'CGEvent', 'linux': 'XTest', 'win32': 'User32'}[platform]
    def click(selector):
        value = {'pid': 101, 'source': source, 'selector': selector, 'at': len(inputs) + 1,
                 'point': {'x': 24, 'y': 24}, 'events': [{'type': 'click', 'trusted': True, 'matches': True}]}
        inputs.append(value)
        return value
    def state(theme, page='overview'):
        return {'open': True, 'theme': theme, 'selectedPage': page, 'query': '', 'focused': '',
            'panel': {'x': 0, 'y': 0, 'width': 320, 'height': 300},
            'main': {'x': 90, 'y': 30, 'width': 230, 'height': 270, 'clientWidth': 230, 'scrollWidth': 230, 'scrollTop': 0},
            'sidebar': {'x': 0, 'y': 0, 'width': 90, 'height': 300},
            'surface': {'backdropFilter': 'blur(28px) saturate(1.35)',
                        'backgroundColor': 'rgba(21, 29, 42, 0.95)' if theme == 'dark' else 'rgba(247, 249, 253, 0.94)'},
            'toolbar': {'backgroundColor': 'rgb(15, 20, 28)'},
            'sections': [{'id': name, 'pages': pages, 'hidden': page not in pages.split()} for name, pages in GROUPS],
            'navigation': [{'id': name, 'label': 'Synthetic ' + name, 'icon': {'tone': 'tone-' + str(i), 'viewBox': '0 0 24 24',
                             'paths': 1, 'background': 'linear-gradient(synthetic-only)', 'bounds': {'x': 12, 'y': 12, 'width': 24, 'height': 24}}}
                           for i, name in enumerate(PAGES)],
            'adblock': {'visible': True, 'receivesPoint': True, 'state': 'Synthetic off', 'fontSize': 14,
                        'bounds': {'x': 240, 'y': 80, 'width': 44, 'height': 24}},
            'clearVisible': False, 'emptyVisible': False}
    def selection(theme, page):
        return {'page': page, 'input': click('#settings-dialog .settings-nav-item[data-settings-page="' + page + '"]'), 'readback': state(theme, page)}
    def search(theme, query, visible):
        value = state(theme, 'appearance')
        value.update(query=query, clearVisible=True, emptyVisible=not visible)
        for row in value['sections']:
            row['hidden'] = row['id'] not in visible
        return {'query': query, 'readback': value, 'input': {'selector': '#settings-search', 'value': query,
            'source': 'webContents.sendInputEvent and insertText after native focus',
            'events': [{'type': kind, 'trusted': True, 'matches': True} for kind in ('click', 'input')]}}
    for theme in ('light', 'dark'):
        sample = {'theme': theme, 'openInput': click('#settings-button'), 'overview': state(theme),
                  'navigation': [selection(theme, page) for page in PAGES[1:]], 'appearance': selection(theme, 'appearance'),
                  'search': [search(theme, 'AdBlock', ['privacy', 'adblock-exclusions'])],
                  'empty': search(theme, 'mouse-no-such-setting-640', []), 'clearInput': click('#settings-search-clear'),
                  'cleared': state(theme, 'appearance'), 'narrowSelection': selection(theme, 'overview'),
                  'wide': state(theme), 'closeInput': click('#settings-dialog [data-close-dialog]'),
                  'closed': {'open': False, 'focused': 'settings-button'}, 'captures': {}}
        sample['cleared']['focused'] = 'settings-search'
        sample['narrow'] = sample['narrowSelection']['readback']
        for kind in ('overview', 'appearance', 'narrow'):
            name = 'mouse-637-settings-' + kind + '-' + theme + '.png'
            blob = png(); files[name] = files[name[:-4] + '-display.png'] = blob
            sample['captures'][kind] = name
            dimensions = {'width': 320, 'height': 300}
            bounds = {'x': 0, 'y': 0, **dimensions}
            captures.append({'filename': name, 'displayFilename': name[:-4] + '-display.png', 'sha256': digest(blob),
                'displaySha256': digest(blob), 'source': 'globalCapture.acquire(display)', 'kind': 'screen',
                'backend': 'synthetic-unit-only', 'pixelSize': dimensions, 'screenPixelSize': dimensions,
                'display': {'bounds': bounds}, 'contentBounds': bounds, 'cropPixels': bounds,
                'mapping': {'originX': 0, 'originY': 0, 'scaleX': 1, 'scaleY': 1}})
        samples.append(sample)
    facts = {'version': '6.0.42', 'ok': True, 'restored': True, 'packaged': True, 'profileIsolated': True,
             'platform': platform, 'arch': 'arm64' if platform == 'darwin' else 'x64', 'pid': 101,
             'restart': {'pid': 102}, 'nativeInputs': inputs, 'captures': captures,
             'settings640': {'schema': 1, 'version': '6.0.42', 'ok': True,
                             'source': 'Installed app, trusted native controls and actual OS captures', 'samples': samples}}
    def refresh():
        files['mouse-637-features.json'] = json.dumps(facts).encode()
        written = copy.deepcopy(facts)
        written.update(ok=False, restored=False, awaitingRestart=True)
        written.pop('restart')
        files['mouse-637-features-write.json'] = json.dumps(written).encode()
    refresh()
    return files, facts, refresh


class SettingsAcceptance(unittest.TestCase):
    def test_all_platforms_recompute_six_crops_and_bind_fourteen_raw_artifacts(self):
        for platform in ('darwin', 'linux', 'win32'):
            files, _, _ = fixture(platform)
            before = copy.deepcopy(files)
            result = V['verify'](files.__getitem__, expected_platform=platform)
            self.assertEqual(len(result['nativeCaptures']), 6)
            self.assertEqual(len(result['artifacts']), 14)
            self.assertEqual(files, before)

    def test_invisible_adblock_wrong_category_search_focus_and_untrusted_click_are_rejected(self):
        changes = [lambda f: f['settings640']['samples'][0]['overview']['adblock'].update(visible=False),
                   lambda f: f['settings640']['samples'][0]['overview']['adblock'].update(receivesPoint=False),
                   lambda f: f['settings640']['samples'][0]['overview']['main'].update(scrollTop=100),
                   lambda f: f['settings640']['samples'][0]['overview']['navigation'][0]['icon'].update(paths=0),
                   lambda f: f['settings640']['samples'][0]['navigation'].pop(),
                   lambda f: f['settings640']['samples'][0]['search'][0]['input']['events'][1].update(trusted=False),
                   lambda f: f['settings640']['samples'][0]['cleared'].update(focused=''),
                   lambda f: f['settings640']['samples'][0]['closeInput']['events'][0].update(trusted=False),
                   lambda f: f['restart'].update(pid=101)]
        for index, mutate in enumerate(changes):
            files, facts, refresh = fixture()
            mutate(facts); refresh()
            with self.subTest(index=index), self.assertRaises(ValueError):
                V['verify'](files.__getitem__)

    def test_coherently_rehashed_blank_native_image_and_wrong_dpi_are_rejected(self):
        for defect in ('blank-image', 'wrong-dpi'):
            files, facts, refresh = fixture()
            record = facts['captures'][0]
            if defect == 'blank-image':
                blob = png(blank=True)
                for key, sha_key in (('filename', 'sha256'), ('displayFilename', 'displaySha256')):
                    files[record[key]] = blob; record[sha_key] = digest(blob)
            else:
                record['mapping']['scaleX'] = .8
            refresh()
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                V['verify'](files.__getitem__)

    def test_source_manifest_and_saved_summary_cannot_substitute_for_raw_acceptance(self):
        files, _, _ = fixture()
        result = V['verify'](files.__getitem__)
        acceptance = json.dumps(result).encode(); files['mouse-640-settings-acceptance.json'] = acceptance
        build = {'tests': ['settings-glass-navigation-search'], 'settings640': {
            'file': 'mouse-640-settings-acceptance.json', 'sha256': digest(acceptance),
            'report': {'file': 'mouse-637-features.json', 'sha256': digest(files['mouse-637-features.json'])}}}
        self.assertEqual(EXTRA['settings'](files.__getitem__, platform='linux', arch='x64', build=build), result)
        for field in ('sha256', 'report'):
            wrong = copy.deepcopy(build); wrong['settings640'][field] = 'wrong'
            with self.subTest(field=field), self.assertRaises(ValueError):
                EXTRA['settings'](files.__getitem__, platform='linux', arch='x64', build=wrong)
        files['mouse-640-settings-acceptance.json'] = json.dumps({**result, 'ok': False}).encode()
        with self.assertRaises(ValueError):
            EXTRA['settings'](files.__getitem__, platform='linux', arch='x64')


if __name__ == '__main__':
    unittest.main()
