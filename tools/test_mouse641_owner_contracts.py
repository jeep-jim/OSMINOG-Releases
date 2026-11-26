"""Synthetic mutations of superseded641 behavior; never native evidence."""
import copy
from pathlib import Path
import runpy
import unittest

TOOLS = Path(__file__).resolve().parent
CONTRACTS = runpy.run_path(str(TOOLS / 'mouse641-owner-contracts.py'))
W = CONTRACTS['reader']()
F = runpy.run_path(str(TOOLS / 'mouse641-features-evidence.py'))
R = runpy.run_path(str(TOOLS / 'mouse641-retained-owner-evidence.py'))
FIXTURE = runpy.run_path(str(TOOLS / 'fixtures/mouse641-owner-fixtures.py'))


def absent():
    return {'widgetCount': 0, 'scripts': [], 'styles': [], 'mediaPlayerAPI': 'undefined', 'onMediaPlayerAPI': 'undefined'}


def input_row(selector):
    return {'selector': selector, 'pid': 11, 'source': 'XTest', 'at': 100, 'point': {'x': 50, 'y': 60},
            'events': [{'type': 'click', 'trusted': True, 'matches': True}]}


def media_fixture():
    sample = lambda time: {'audio': [{'id': 'audio-two', 'paused': False, 'currentTime': time}]}
    play, replace = input_row('#media-play'), input_row('#media-replace')
    mute, unmute = (input_row('.tab-item[data-tab="main"] [data-tab-mute]') for _ in range(2))
    audio = {'owned': True, 'format': 'PCM16 mono WAV', 'files': [
        {'name': name, 'bytes': 100, 'sha256': code * 64} for name, code in [('one', 'a'), ('two', 'b')]],
        'requests': [{'path': '/audio/' + name + '.wav'} for name in ('one', 'two')]}
    owner = {'id': 'main', 'webContentsId': 123}
    value = {'schema': 2, 'ok': True, 'removed': True,
        'source': 'Installed website audio, native tab mute and observed removed-player polling world',
        'pollWorld': 1294, 'pollIntervalWasMs': 1000, 'polls': [], 'initial': absent(), 'other': absent(), 'final': absent(),
        'before': {'playClickTrusted': True, 'current': 'audio-one', 'timeOrigin': 1000},
        'after': {**sample(1), 'replaceClickTrusted': True, 'current': 'audio-two', 'timeOrigin': 1000, 'error': None},
        'observation': {'elapsedMs': 2400, 'startedAt': 1000, 'finishedAt': 3400, 'before': sample(1), 'after': sample(3.4)},
        'samples': [{'at': at, 'shell': absent(), 'audio': sample(time)} for at, time in [(1100, 1.1), (3300, 3.3)]],
        'mute': {'muted': True, 'audio': sample(4), 'input': mute}, 'unmute': {'muted': False, 'audio': sample(5), 'input': unmute},
        'unrelatedPaused': True, 'originDesktop': 'desk-1', 'otherDesktop': 'desk-2',
        'nativeEvents': [{'type': 'media-started-playing', 'at': at} for at in (100, 200)],
        'nativeBefore': {'tabId': 'main', 'webContentsId': 123}, 'nativeAfter': {'tabId': 'main', 'webContentsId': 123},
        'playInput': play, 'replaceInput': replace}
    return value, audio, [owner], [play, replace, mute, unmute]


def retained_fixture():
    old = runpy.run_path(str(TOOLS / 'test_mouse634_owner_feedback_evidence.py'))
    _, facts, _ = old['fixture']('linux')
    ai = facts['aiPreview']; chat = ai['chatBefore']; primary, preview = facts['fixtureOrigins']
    for key in ('chatAfterBlank', 'chatAfterClose', 'chatAfter'):
        ai[key] = copy.deepcopy(chat)
    ai['chatNavigation']['events'] = []
    ai['previewSource'] = 'explicit existing-preview fixture'
    grid = {'classicTabId': '', 'view': 'grid', 'tree': {'type': 'split', 'axis': 'x'}, 'slots': copy.deepcopy(ai['before']['mainSlots']),
            'aiId': chat['id'], 'previewId': '', 'panes': [{'id': 'p1'}, {'id': 'p2'}], 'returnVisible': False}
    ai['linkRouting'] = [FIXTURE['link_route'](chat, selector, preview + '/page/' + str(index) + '/', grid, 'main-link-' + str(index), pid=91)
                         for selector, index in [('#link-blank', 3), ('#link-same', 4)]]
    for index, row in enumerate(ai['linkRouting']):
        row['tab']['webContentsId'] += index
    ai['previewSetup'] = [{'source': 'Explicit fixture setup for retained lower-pane controls; not a native-link outcome',
                          'action': 'browser.command(open)', 'lane': 'side', 'previewOf': chat['id'], 'url': preview + '/page/3/',
                          'id': ai[name]['previewId']} for name in ('first', 'reopened')]
    tabs = [{key: row['tab'][key] for key in ('id', 'lane', 'previewOf', 'url')} for row in ai['linkRouting']]
    for name in ('first', 'closed', 'reopened'):
        ai[name]['tabs'].extend(copy.deepcopy(tabs))
    inputs = [event for row in ai['linkRouting'] for event in (row['input'], row['returnInput'])]
    inputs.append(ai['closeClick'])
    for key in ('second', 'blankClick', 'sameClick', 'previewReused', 'mainAfterSame', 'chatAfterSame'):
        ai.pop(key, None)
    return ai, primary, preview, inputs


class Owner641Contracts(unittest.TestCase):
    def test_ordinary_site_audio_retains_native_mute_and_replacement_with_no_player_or_polling(self):
        value, audio, owners, inputs = media_fixture()
        result = W['verify_media_removal'](value, audio, owners, platform='linux', pid=11, inputs=inputs)
        self.assertEqual(result['observedNoPollingMs'], 2400)
        self.assertTrue(F['verify_media'](value, audio, owners)['removed'])

    def test_old_widget_polling_short_observation_stopped_audio_and_foreign_tab_are_rejected(self):
        value, audio, owners, inputs = media_fixture()
        changes = [lambda v: v['initial'].update(widgetCount=1), lambda v: v['final'].update(mediaPlayerAPI='function'),
            lambda v: v['other'].update(styles=['media-widget.css']), lambda v: v.update(polls=[{'world': 1294}]),
            lambda v: v['observation'].update(elapsedMs=1000), lambda v: v['observation']['after']['audio'][0].update(currentTime=1),
            lambda v: v['mute']['audio']['audio'][0].update(paused=True), lambda v: v['unmute'].update(muted=True),
            lambda v: v['nativeAfter'].update(webContentsId=999), lambda v: v['after'].update(timeOrigin=2000),
            lambda v: v['playInput']['events'][0].update(trusted=False)]
        for change in changes:
            bad = copy.deepcopy(value); change(bad)
            with self.assertRaises(ValueError): W['verify_media_removal'](bad, audio, owners, platform='linux', pid=11, inputs=inputs)

    def test_media_ordinary_mute_input_is_mandatory_and_must_belong_to_same_process(self):
        value, audio, owners, inputs = media_fixture()
        with self.assertRaises(ValueError): W['verify_media_removal'](value, audio, owners, platform='linux', pid=11, inputs=inputs[:2])
        for key in ('mute', 'unmute'):
            bad = copy.deepcopy(value); bad[key]['input']['pid'] = 12
            with self.assertRaises(ValueError): W['verify_media_removal'](bad, audio, owners, platform='linux', pid=11, inputs=inputs)

    def test_tiny_headers_are_always_visible_instead_of_hover_revealed(self):
        pane = {'bounds': {'x': 1, 'y': 2, 'width': 120, 'height': 90}, 'header': {'x': 1, 'y': 2, 'width': 120, 'height': 28}, 'focused': True}
        compact = {'panes': [pane, copy.deepcopy(pane)]}; keyboard = copy.deepcopy(compact)
        CONTRACTS['compact_headers'](compact, keyboard)
        for change in [lambda c: c['panes'][0]['header'].update(height=5), lambda c: c['panes'][1]['header'].update(y=100),
                       lambda c: c['panes'][0]['bounds'].update(height=350)]:
            bad = copy.deepcopy(compact); change(bad)
            with self.assertRaises(ValueError): CONTRACTS['compact_headers'](bad, keyboard)

    def test_new_ai_links_and_explicit_existing_preview_retain_all_original_native_owners(self):
        ai, primary, preview, inputs = retained_fixture()
        chat, mains, reopened = CONTRACTS['retained_ai'](ai, 'linux', 91, primary, preview, inputs, R['N'], R['ai_split'])
        self.assertEqual(chat['id'], ai['chatBefore']['id']); self.assertEqual(len(mains), 2); self.assertEqual(reopened, ai['reopened']['previewId'])
        self.assertEqual(R['canceled_chat_navigation'](ai, 'linux', primary, preview)['navigationEpoch'], ai['chatBefore']['navigationEpoch'])

    def test_ai_classic_grid_chat_epoch_explicit_setup_and_original_native_geometry_are_required(self):
        ai, primary, preview, inputs = retained_fixture()
        changes = [lambda v: v['linkRouting'][0]['tab'].update(lane='side', previewOf='page2'),
            lambda v: v['linkRouting'][1]['state']['slots'].update(p1='main-link-4'),
            lambda v: v['linkRouting'][0]['input']['events'][0].update(href=primary + '/wrong'),
            lambda v: v['chatNavigation']['events'].append({'type': 'will-navigate'}),
            lambda v: v['chatAfter'].update(navigationEpoch=2), lambda v: v['previewSetup'][0].update(action='native-click'),
            lambda v: v['first']['tabs'][0].update(url='https://replaced.example/'),
            lambda v: v['closed']['chatSlot'].update(height=10), lambda v: v['native'][1].update(attached=False)]
        for change in changes:
            bad = copy.deepcopy(ai); change(bad)
            with self.assertRaises(ValueError): CONTRACTS['retained_ai'](bad, 'linux', 91, primary, preview, inputs, R['N'], R['ai_split'])
        without_return = [row for row in inputs if row.get('selector') != '#return-to-grid']
        with self.assertRaises(ValueError): CONTRACTS['retained_ai'](ai, 'linux', 91, primary, preview, without_return, R['N'], R['ai_split'])

    def test_intercepted_link_receipts_are_a_narrow_new_native_action(self):
        ai, _, _, _ = retained_fixture(); event = ai['linkRouting'][0]['input']
        F['input_event'](event, 'linux', {91})
        for key, value in [('pid', 1), ('source', 'script'), ('selector', '#settings-button'), ('webContentsId', 0)]:
            with self.assertRaises(ValueError): F['input_event']({**event, key: value}, 'linux', {91})
        wrong = copy.deepcopy(event); wrong['events'][0]['type'] = 'click'
        with self.assertRaises(ValueError): F['input_event'](wrong, 'linux', {91})


if __name__ == '__main__':
    unittest.main()
