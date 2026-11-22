#!/usr/bin/env python3
"""Synthetic AI preview contract mutations; never substitutes native evidence."""
import base64
import copy
from pathlib import Path
import runpy
import struct
import unittest
import zlib

F = runpy.run_path(str(Path(__file__).with_name('mouse637-features-evidence.py')))
CHAT, PREVIEW, MAIN = ('http://127.0.0.1:' + str(n) for n in (12000, 12001, 12002))


def png_url(color=(37, 143, 191, 255)):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 20, 20, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress((b'\0' + bytes(color) * 20) * 20)) + chunk(b'IEND', b'')
    return 'data:image/png;base64,' + base64.b64encode(png).decode()


def identity(index, identifier=None, origin=PREVIEW, ticks=1):
    return {'id': identifier or 'page-' + str(index), 'index': index, 'desk': 'desk-one', 'webContentsId': 100 + index,
            'url': origin + '/page/' + str(index) + '/', 'navigationEpoch': 0, 'identity': 'proof-' + str(index),
            'timeOrigin': 1000 + index, 'field': 'preserved-' + str(index) + '-данные', 'scrollX': 0, 'scrollY': 180,
            'cookie': 'mouse631_' + str(index) + '=proof-' + str(index), 'ticks': ticks}


def native(owner, bounds, mode='square'):
    bounds = F['N']['endpoints'](bounds)
    return {'tabId': owner['id'], 'webContentsId': owner['webContentsId'], 'index': owner['index'], 'desk': owner['desk'],
            'visible': True, 'parentVisible': True, 'cachedVisible': True, 'attached': True,
            'bounds': bounds, 'actualBounds': copy.deepcopy(bounds), 'viewBounds': copy.deepcopy(bounds), 'parentBounds': None,
            'roundBottom': 0 if mode == 'square' else 12}


def geometry(chat, preview, ratio=.5, mode='rounded', theme='dark', page=4):
    gap = 0 if mode == 'square' else 6
    height = (600 - gap) * ratio
    url = PREVIEW + '/page/' + str(page) + '/'
    return {'theme': theme, 'mode': mode, 'ratio': ratio, 'aiId': chat['id'], 'previewId': preview['id'], 'focusAI': False,
            'column': {'x': 600, 'y': 100, 'width': 400, 'height': 600},
            'chat': {'x': 600, 'y': 100, 'width': 400, 'height': height},
            'preview': {'x': 600, 'y': 100 + height + gap, 'width': 400, 'height': 600 - height - gap},
            'chatSlot': {'x': 600, 'y': 128, 'width': 400, 'height': height - 28},
            'previewSlot': {'x': 600, 'y': 128 + height + gap, 'width': 400, 'height': 600 - height - gap - 28},
            'divider': {'x': 600, 'y': 100 + height, 'width': 400, 'height': gap}, 'gap': gap,
            'slots': {'p1': 'main-0', 'p2': 'main-1'}, 'dividerValue': int(ratio * 100 + .5),
            'address': {'value': url, 'readOnly': False, 'disabled': False},
            'icon': {'url': png_url(), 'complete': True, 'width': 20, 'height': 20},
            'tabs': [{'id': preview['id'], 'lane': 'side', 'previewOf': chat['id'], 'url': url, 'favicon': PREVIEW + '/icon.png'}]}


def click(selector, tab_id=None):
    return {'selector': selector, 'pid': 11, 'source': 'XTest', 'tabId': tab_id, 'point': {'x': 4, 'y': 5}, 'at': 100,
            'events': [{'type': 'click', 'trusted': True, 'matches': True}]}


def drag(selector, dy, dx=0):
    return {'selector': selector, 'pid': 11, 'source': 'XTest', 'action': 'drag', 'from': {'x': 600, 'y': 400},
            'to': {'x': 600 + dx, 'y': 400 + dy},
            'events': [{'type': 'pointerdown', 'trusted': True, 'matches': True}, {'type': 'pointerup', 'trusted': True}]}


def fixture():
    owners = [identity(i, 'main-' + str(i), MAIN, 100) for i in range(2)]
    chat, preview = identity(2, 'chat', CHAT), identity(4, 'preview')
    opened = click('#ai-preview-link', chat['id'])
    inputs = [opened]
    initial = geometry(chat, preview, page=3)
    nav = geometry(chat, preview)
    report = {'schema': 1, 'ok': True, 'source': 'Owned cross-origin AI source, native resize and native chooser/header transfers',
              'origins': {'chat': CHAT, 'preview': PREVIEW}, 'chatBefore': chat, 'chatAfter': {**chat, 'ticks': 20},
              'open': {'input': opened, 'chatClick': {'trusted': True, 'at': 100}}, 'initial': initial,
              'favicon': {'source': PREVIEW + '/icon.png', 'pngDataURL': png_url(), 'pixelSize': {'width': 20, 'height': 20}, 'expectedRGBA': [37, 143, 191, 255]},
              'navigation': {'id': preview['id'], 'webContentsId': preview['webContentsId'], 'from': PREVIEW + '/page/3/', 'to': PREVIEW + '/page/4/',
                             'beforeNative': native({**preview, 'index': 3}, initial['previewSlot'], 'rounded'),
                             'afterNative': native(preview, nav['previewSlot'], 'rounded'), 'state': nav}, 'samples': []}
    report['navigation'].update(
        beforeInput={'aiId': chat['id'], 'previewId': preview['id'], 'url': PREVIEW + '/page/3/', 'value': PREVIEW + '/page/4/',
                     'focused': True, 'formId': 'ai-preview-address', 'hasSubmitHandler': True, 'readOnly': False, 'disabled': False},
        nativeKey={'method': 'nativeInput.testKey', 'key': 'Return', 'source': 'XTest', 'pid': 11, 'at': 200, 'accepted': True},
        keyboard=[{'type': kind, 'key': None if kind == 'submit' else 'Enter', 'code': None if kind == 'submit' else 'Enter',
                   'isTrusted': True, 'value': PREVIEW + '/page/4/', 'at': 100 + index}
                  for index, kind in enumerate(('keydown', 'keypress', 'submit', 'keyup'))])
    ratio = .5
    for i, (mode, theme, dy) in enumerate([('rounded', 'light', -40), ('rounded', 'dark', 40), ('square', 'light', -40), ('square', 'dark', -24)]):
        before = geometry(chat, preview, ratio, mode, theme)
        ratio += dy / (600 - before['gap'])
        after = geometry(chat, preview, ratio, mode, theme)
        movement = drag('#ai-preview-divider' + (' > .divider-hit' if mode == 'square' else ''), dy)
        inputs.append(movement)
        report['samples'].append({'mode': mode, 'theme': theme, 'dy': dy, 'before': before, 'after': after,
                                 'beforeNative': [native(chat, before['chatSlot'], mode), native(preview, before['previewSlot'], mode)],
                                 'afterNative': [native(chat, after['chatSlot'], mode), native(preview, after['previewSlot'], mode)],
                                 'identityBefore': {**preview, 'ticks': i * 2 + 1}, 'identityAfter': {**preview, 'ticks': i * 2 + 2}, 'input': movement})
    report['persistence'] = {'desk': 'desk-one', 'other': 'desk-two', 'savedRatio': ratio, 'restored': copy.deepcopy(after)}
    second = identity(3, 'second-preview')
    main_bounds = [{'x': 0, 'y': 100, 'width': 400, 'height': 600}, {'x': 400, 'y': 100, 'width': 400, 'height': 600}]
    fullscreen = {**copy.deepcopy(after), 'focusAI': True}
    chooser = {'target': 'p2', 'before': {**preview, 'ticks': 9}, 'after': {**preview, 'ticks': 10},
               'beforeNative': native(preview, after['previewSlot']), 'afterNative': native(preview, main_bounds[1]),
               'fullscreen': fullscreen, 'displacedBefore': {**owners[1], 'ticks': 1}, 'displacedAfter': {**owners[1], 'ticks': 2},
               'lane': 'main', 'previewOf': '', 'state': {'slots': {'p1': 'main-0', 'p2': preview['id']}, 'previewId': '', 'focusAI': False},
               'captureNative': [native(preview, main_bounds[1])]}
    header_drag, second_open = drag('#ai-preview-icon', -50, -300), click('#ai-preview-link', chat['id'])
    inputs.extend([second_open, header_drag])
    header = {'target': 'p1', 'open': second_open, 'input': header_drag, 'before': second, 'after': {**second, 'ticks': 2},
              'afterNative': native(second, main_bounds[0]), 'displacedBefore': {**owners[0], 'ticks': 1}, 'displacedAfter': {**owners[0], 'ticks': 2},
              'lane': 'main', 'previewOf': '', 'state': {'slots': {'p1': second['id'], 'p2': preview['id']}, 'previewId': '', 'focusAI': False},
              'captureNative': [native(second, main_bounds[0]), native(preview, main_bounds[1])]}
    report.update(chooserMove=chooser, headerMove=header,
                  parentClosed={'id': chat['id'], 'closed': True, 'retained': [{**preview, 'ticks': 11}, {**second, 'ticks': 3}],
                                'retainedNative': [native(preview, main_bounds[1]), native(second, main_bounds[0])]})
    inputs.extend(click(s) for s in ['#ai-preview-address-input', '[data-action=ai-fullscreen]', '#ai-preview-target', '#choice-dialog button[data-value="p2"]', '[data-action=close-ai]'])
    return report, owners, inputs


class AIPreviewAcceptance(unittest.TestCase):
    def check(self, report, owners, inputs):
        return F['verify_ai_preview'](report, owners, 11, 'linux', inputs)

    def test_all_modes_themes_navigation_transfers_and_parent_close(self):
        witnesses = self.check(*fixture())
        self.assertEqual(len(witnesses), 6)
        self.assertEqual(len(F['CAPTURES']), 38)
        self.assertEqual([name for name in F['CAPTURES'] if name.startswith('mouse-637-ai-preview-')], [
            'mouse-637-ai-preview-rounded-light.png', 'mouse-637-ai-preview-rounded-dark.png',
            'mouse-637-ai-preview-square-light.png', 'mouse-637-ai-preview-square-dark.png',
            'mouse-637-ai-preview-moved.png', 'mouse-637-ai-preview-dragged.png'])
        self.assertEqual(len(witnesses['ai-preview-dragged']), 2)
        self.assertEqual(witnesses['ai-preview-moved'][0][1:], ([37, 143, 191], (54, 100)))

    def test_wrong_bounds_masks_ratios_and_hidden_native_views_fail(self):
        mutations = [lambda r: r['samples'][0]['after']['preview'].update(height=300),
                     lambda r: r['samples'][2]['afterNative'][1].update(roundBottom=12),
                     lambda r: r['samples'][1]['afterNative'][0].update(visible=False),
                     lambda r: r['persistence'].update(savedRatio=.5),
                     lambda r: r['navigation']['beforeNative'].update(webContentsId=999),
                     lambda r: r['samples'][3]['after'].update(dividerValue=99)]
        for mutation in mutations:
            r, owners, inputs = fixture(); mutation(r)
            with self.assertRaises(ValueError): self.check(r, owners, inputs)

    def test_address_and_normalized_favicon_are_real_owned_content(self):
        r, owners, inputs = fixture(); r['navigation']['state']['address']['readOnly'] = True
        with self.assertRaises(ValueError): self.check(r, owners, inputs)
        r, owners, inputs = fixture(); r['favicon']['pngDataURL'] = png_url((38, 143, 191, 255))
        with self.assertRaises(ValueError): self.check(r, owners, inputs)
        r, owners, inputs = fixture(); r['favicon']['pngDataURL'] = 'data:image/png;base64,not-a-PNG'
        with self.assertRaises(ValueError): self.check(r, owners, inputs)
        r, owners, inputs = fixture(); r['samples'][0]['after']['tabs'][0]['favicon'] = CHAT + '/icon.png'
        with self.assertRaises(ValueError): self.check(r, owners, inputs)

    def test_moves_cannot_replace_documents_displaced_tabs_or_detached_children(self):
        mutations = [lambda r: r['chooserMove']['after'].update(webContentsId=999),
                     lambda r: r['chooserMove']['displacedAfter'].update(field='lost'),
                     lambda r: r['chooserMove']['state'].update(focusAI=True),
                     lambda r: r['headerMove']['state']['slots'].update(p1='main-0'),
                     lambda r: r['headerMove'].update(previewOf='chat'),
                     lambda r: r['parentClosed']['retained'].pop(),
                     lambda r: r['parentClosed']['retainedNative'][0].update(attached=False),
                     lambda r: r['headerMove']['captureNative'][1].update(webContentsId=999)]
        for mutation in mutations:
            r, owners, inputs = fixture(); mutation(r)
            with self.assertRaises(ValueError): self.check(r, owners, inputs)

    def test_address_requires_complete_trusted_submit_and_exact_preview_owner(self):
        mutations = [lambda n: n['beforeInput'].update(aiId='foreign-chat'),
                     lambda n: n['beforeInput'].update(previewId='foreign-preview'),
                     lambda n: n['beforeInput'].update(focused=False),
                     lambda n: n['beforeInput'].update(formId='address-form'),
                     lambda n: n['beforeInput'].update(hasSubmitHandler=False),
                     lambda n: n['beforeInput'].update(readOnly=True),
                     lambda n: n['beforeInput'].update(value=n['from']),
                     lambda n: n['nativeKey'].update(method='sendInputEvent'),
                     lambda n: n['nativeKey'].update(key='Enter'),
                     lambda n: n['nativeKey'].update(source='User32'),
                     lambda n: n['nativeKey'].update(pid=12),
                     lambda n: n['nativeKey'].update(accepted=False),
                     lambda n: n['keyboard'].pop(1),
                     lambda n: n['keyboard'][1].update(isTrusted=False),
                     lambda n: n['keyboard'][2].update(isTrusted=False),
                     lambda n: n['keyboard'][2].update(value=n['from']),
                     lambda n: n['keyboard'].append(copy.deepcopy(n['keyboard'][2])),
                     lambda n: n['keyboard'].reverse()]
        for mutation in mutations:
            report, owners, inputs = fixture(); mutation(report['navigation'])
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.check(report, owners, inputs)

    def test_address_native_key_receipts_are_bound_on_all_three_platforms(self):
        for platform, key, source in [('linux', 'Return', 'XTest'), ('darwin', 'ENTER', 'CGEvent'), ('win32', 'ENTER', 'User32')]:
            report, _, _ = fixture(); navigation = report['navigation']
            navigation['nativeKey'].update(key=key, source=source)
            F['verify_ai_address'](navigation, report['chatBefore']['id'], navigation['id'], 11, platform)
            navigation['nativeKey']['source'] = 'foreign input'
            with self.assertRaises(ValueError):
                F['verify_ai_address'](navigation, report['chatBefore']['id'], navigation['id'], 11, platform)

    def test_trusted_pointer_and_full_control_ledger_are_mandatory(self):
        r, owners, inputs = fixture(); r['samples'][0]['input']['events'][0]['trusted'] = False
        with self.assertRaises(ValueError): self.check(r, owners, inputs)
        r, owners, inputs = fixture(); inputs[:] = [i for i in inputs if i['selector'] != '#ai-preview-icon']
        with self.assertRaises(ValueError): self.check(r, owners, inputs)
        r, owners, inputs = fixture(); inputs[:] = [i for i in inputs if i['selector'] != '#ai-preview-target']
        with self.assertRaises(ValueError): self.check(r, owners, inputs)


if __name__ == '__main__':
    unittest.main()
