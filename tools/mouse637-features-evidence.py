#!/usr/bin/env python3
"""Independent two-process637 features, appearance and actual OS-frame gate."""
import math
from pathlib import Path
import re
import runpy

N = runpy.run_path(str(Path(__file__).with_name('mouse637-native-evidence.py')))
need, finite, positive, sha, rect = (N[k] for k in ('need', 'finite', 'positive', 'sha', 'rect'))
VERSION = '6.0.37'
NAME = 'mouse-637-features.json'
WRITE = 'mouse-637-features-write.json'
MARKER = 'MOUSE_637_FEATURES_NATIVE_PASS'
WRITE_MARKER = 'MOUSE_637_FEATURES_WRITE_PASS'
RANGE = {'min': 0, 'max': 100, 'minimum': '#a0a0a0', 'maximum': '#ffffff', 'default': 55, 'defaultColor': '#d4d4d4'}
INITIAL = {'paneMode': 'rounded', 'whiteTone': 55}
CAPTURES = ['mouse-637-' + part + '.png' for part in (
    'language-ru', 'language-en', 'interface-light', 'interface-dark', 'extensions-installed',
    'extensions-pane', 'media-full', 'media-compact', 'media-replacement',
    'appearance-controls-light', 'appearance-square-light', 'appearance-controls-dark',
    'appearance-square-dark', 'appearance-restored', 'extensions-restore-error')]


def input_event(row, platform, pids):
    need(isinstance(row, dict) and row.get('pid') in pids and row.get('source') == N['source'](platform)
         and isinstance(row.get('selector'), str) and row['selector'], '637 native input source/owner absent')
    events = row.get('events')
    need(isinstance(events, list) and 0 < len(events) <= 100, '637 trusted input events missing')
    if row.get('action') == 'drag':
        need(row['selector'] in ('.divider[data-path=""]', '.divider[data-path=""] > .divider-hit') and all(finite(row.get(p, {}).get(axis)) for p in ('from', 'to') for axis in ('x', 'y'))
             and any(e.get('type') == 'pointerdown' and e.get('trusted') is True and e.get('matches') is True for e in events)
             and any(e.get('type') == 'pointerup' and e.get('trusted') is True for e in events), '637 native divider drag absent')
    else:
        need(finite(row.get('at')) and all(finite(row.get('point', {}).get(axis)) for axis in ('x', 'y'))
             and any(e.get('type') == 'click' and e.get('trusted') is True and e.get('matches') is True for e in events), '637 native target never received a trusted click')


def appearance_state(state, mode, tone, theme, *, settings=False, allow_unstored_default=False):
    model = {'paneMode': mode, 'whiteTone': tone}
    need(isinstance(state, dict) and state.get('model') == model, 'appearance model differs')
    unmodified_default = allow_unstored_default and mode == 'rounded' and tone == 55 and theme == 'light' and 'stored' in state and state['stored'] is None
    need(state.get('stored') == model or unmodified_default, 'appearance model and localStorage differ')
    channel = math.floor(160 + 95 * tone / 100 + .5)
    color = '#' + format(channel, '02x') * 3
    need(state.get('theme') == theme and state.get('primary') == color and state.get('gap') == (0 if mode == 'square' else 6)
         and state.get('radius') == (0 if mode == 'square' else 12), 'appearance color or layout variables differ')
    if theme == 'dark':
        need(state.get('textColor') == 'rgb(%d, %d, %d)' % (channel, channel, channel), 'dark primary text ignores its selected tone')
    if settings:
        controls = state.get('settings', {})
        need(controls.get('open') is True and controls.get('square') is (mode == 'square')
             and controls.get('tone') == tone, 'appearance controls do not reflect the stored state')
    rect(state.get('stage')); rect(state.get('workspace'))
    panes = state.get('panes')
    need(isinstance(panes, list) and 1 <= len(panes) <= 20 and len({p.get('id') for p in panes}) == len(panes), 'appearance pane geometry required')
    for pane in panes:
        rect(pane.get('bounds'))
        need(pane.get('topRadius') == pane.get('bottomRadius') == (0 if mode == 'square' else 12), 'pane radii ignore the chosen mode')
    return state


def verify_appearance(value, pid, restart_pid, origin):
    need(value.get('initial') == INITIAL and value.get('range') == RANGE and value.get('writeVerified') is True, 'appearance initial/default/range contract differs')
    pages = value.get('pages', {})
    before, after = pages.get('before', []), pages.get('after', [])
    need(pages.get('identityPreserved') is True and len(before) == len(after) == 2, 'appearance live page witnesses absent')
    for i, (old, new) in enumerate(zip(before, after)):
        need(old.get('index') == i, 'appearance owned page order differs')
        N['identity'](old, new, origin)
    samples = value.get('samples', [])
    need([s.get('theme') for s in samples] == ['light', 'dark'], 'appearance both themes required')
    for sample in samples:
        theme = sample['theme']
        for key, mode, tone, settings in [('initial', 'rounded', 55, True), ('minimum', 'rounded', 0, True),
                ('maximum', 'rounded', 100, True), ('reset', 'rounded', 55, True),
                ('square', 'square', 55, False), ('rounded', 'rounded', 55, False)]:
            appearance_state(sample.get(key, {}), mode, tone, theme, settings=settings,
                             allow_unstored_default=(key == 'initial' and theme == 'light'))
        if theme == 'light':
            need(sample['initial']['textColor'] == sample['minimum']['textColor'] == sample['maximum']['textColor'], 'dark text brightness altered light-theme text')
        square = sample['square']
        need(len(square['panes']) == 2, 'both native square-grid panes required')
        panes = sorted(square['panes'], key=lambda p: p['bounds']['x'])
        left, right = (p['bounds'] for p in panes)
        stage = square['stage']
        workspace = square['workspace']
        N['near'](stage['y'], workspace['y'], 'square workspace top inset', 1.1)
        N['near'](N['bottom'](stage), N['bottom'](workspace), 'square workspace bottom inset', 1.1)
        for actual, expected in [(left['x'], stage['x']), (N['right'](right), N['right'](stage)), (N['right'](left), right['x'])]:
            N['near'](actual, expected, 'square grid has an inset or gap', 1.1)
        for pane in (left, right):
            N['near'](pane['y'], stage['y'], 'square grid top inset', 1.1)
            N['near'](N['bottom'](pane), N['bottom'](stage), 'square grid bottom inset', 1.1)
        native = sample.get('native', [])
        need(len(native) == 2, 'square grid native views missing')
        for row, owner in zip(native, before):
            N['native'](row, owner)
            need(row.get('roundBottom') == 0, 'square mode retained a native corner mask')
        resize = sample.get('resize', {})
        need(resize.get('after') == native and len(resize.get('before', [])) == 2, 'square native resize witnesses absent')
        for row, owner in zip(resize['before'], before):
            N['native'](row, owner)
        drag = resize.get('input', {})
        need(drag.get('selector') == '.divider[data-path=""] > .divider-hit' and drag.get('action') == 'drag'
             and drag.get('to', {}).get('x') == drag.get('from', {}).get('x', 0) + 32
             and drag.get('to', {}).get('y') == drag.get('from', {}).get('y')
             and abs(native[0]['bounds']['width'] - resize['before'][0]['bounds']['width']) >= 16, 'square grid cannot resize through its native header handle')
    appearance_state(value.get('persisted', {}), 'square', 0, 'dark')
    restart = value.get('restart', {})
    need(restart.get('pid') == restart_pid and restart.get('writePid') == pid and restart.get('verified') is True, 'appearance did not survive a distinct process')
    restored = restart.get('restored', {})
    need(restored.get('theme') in ('light', 'dark'), 'restored appearance theme absent')
    appearance_state(restored, 'square', 0, restored['theme'])
    appearance_state(restart.get('settings', {}), 'square', 0, 'dark', settings=True)
    return before


def verify_language(value):
    need(value.get('catalogCount') == 72 and value.get('selectableCodes') == ['ru', 'en'] and value.get('untranslatedSelectable') is False, 'language catalog falsely offers untranslated interfaces')
    catalogs = value.get('catalogs', [])
    need([c.get('locale') for c in catalogs] == ['ru', 'en'], 'both language chooser locales required')
    for catalog in catalogs:
        rows = catalog.get('rows', [])
        need(len(rows) == 72 and len({r.get('code') for r in rows}) == 72
             and [r.get('code') for r in rows if r.get('selectable') is True] == ['ru', 'en']
             and all(isinstance(r.get('label'), str) and r['label'] for r in rows), 'language catalog entries invalid')
    searches = value.get('searches', [])
    need([(s.get('locale'), s.get('query')) for s in searches] == [('ru', 'КИТАЙСКИЙ'), ('ru', 'японский'), ('en', 'КИТАЙСКИЙ'), ('en', 'японский')], 'native Cyrillic language search cases missing')
    for search in searches:
        need([r.get('code') for r in search.get('rows', [])] == (['ja'] if search['query'] == 'японский' else ['zh-Hans', 'zh-Hant'])
             and all(r.get('selectable') is False for r in search['rows']), 'language search returns incorrect or selectable untranslated rows')
    need(value.get('selections') == [{'locale': 'ru', 'actual': 'ru'}, {'locale': 'en', 'actual': 'en'}], 'language selection changed to an unsupported interface')


def verify_interface(value, owners):
    rows = value.get('themes', [])
    need([r.get('theme') for r in rows] == ['light', 'dark'], 'both637 native interface themes required')
    for row in rows:
        resting, focused, compact, keyboard = (row.get(k, {}) for k in ('resting', 'focused', 'compact', 'keyboard'))
        for state in (resting, focused, compact, keyboard):
            need(state.get('theme') == row['theme'] and len(state.get('panes', [])) == 2, 'native interface state missing')
            for pane in state['panes']:
                rect(pane.get('bounds')); rect(pane.get('header')); rect(pane.get('address'))
        need(all(0 < p['header']['height'] <= 28 for p in resting['panes']) and focused['panes'][0].get('focused') is True, 'slim header or address focus failed')
        if row['theme'] == 'dark':
            need(focused['panes'][0].get('addressColor') != resting['panes'][0].get('addressColor'), 'dark address has no focus contrast')
        need(compact['panes'][0].get('compact') is True and compact['panes'][0]['header']['height'] <= 5.5
             and keyboard['panes'][0].get('focused') is True and keyboard['panes'][0]['header']['height'] >= 28, 'compact header lacks native hover/keyboard restoration')
        normal, small = row.get('native', []), row.get('compactNatives', [])
        need(len(normal) == len(small) == 2 and row.get('compactNative') == small[0], 'compact native owners absent')
        for rows_ in (normal, small):
            for native, owner in zip(rows_, owners):
                N['native'](native, owner)
        N['native'](row.get('expandedNative', {}), owners[0])


def verify_extensions(value, restore, restart):
    installed = value.get('installed', {})
    identifier = installed.get('id')
    need(isinstance(identifier, str) and re.fullmatch(r'[0-9a-f-]{36}', identifier, re.I)
         and installed.get('enabled') is True and value.get('pinned') is True and restore.get('id') == identifier, 'real installed/pinned extension absent')
    dialogs = value.get('dialogs', [])
    need([r.get('kind') for r in dialogs] == ['folder', 'consent'] and dialogs[1].get('response') == 1, 'owned fixture folder/consent binding differs')
    pane = value.get('pane', {})
    before, after = pane.get('beforeResize', {}), pane.get('afterResize', {})
    need(pane.get('identityPreserved') is True and before.get('tabId') == after.get('tabId')
         and before.get('webContentsId') == after.get('webContentsId') and positive(before.get('webContentsId')), 'extension resize replaced its native view')
    for row in (before, after):
        N['flags'](row, ('visible', 'parentVisible', 'cachedVisible', 'attached'), 'extension view not live')
        rect(row.get('bounds')); need(row.get('bounds') == row.get('actualBounds'), 'extension actual bounds mismatch')
    need(abs(before['bounds']['width'] - after['bounds']['width']) >= 20, 'extension native pane was not resized')
    guest = pane.get('guestBefore', {})
    need(guest == pane.get('guestAfter') and guest.get('clicks') == 1 and guest.get('trusted') is True
         and finite(guest.get('timeOrigin')) and guest['timeOrigin'] > 0
         and re.fullmatch(r'chrome-extension://[a-p]{32}/panel\.html', guest.get('url', '')), 'actual extension page/action/identity evidence missing')
    need(restore.get('persistedEnabled') is True and re.fullmatch('[0-9a-f]{64}', restore.get('beforeSha256', ''))
         and re.fullmatch('[0-9a-f]{64}', restore.get('afterSha256', '')) and restore['beforeSha256'] != restore['afterSha256'], 'restart must exercise a real changed managed checksum')
    registry = restore.get('registry', [])
    need(len(registry) == 1 and registry[0].get('id') == identifier and registry[0].get('enabled') is True, 'original enabled registry missing')
    failure = restart.get('restoreError', {})
    entry = failure.get('entry', {})
    need(entry.get('id') == identifier and entry.get('enabled') is False and entry.get('error') == 'load_failed'
         and entry.get('pinned') is True and failure.get('registryPreserved') is True, 'restart error disabled or discarded the wrong record')
    states = failure.get('states', [])
    need([r.get('theme') for r in states] == ['light', 'dark'], 'both restore-error themes missing')
    for state in states:
        need(state.get('state') == 'restore-error' and state.get('pins') == 0
             and re.search(r'Не удалось восстановить.*заново.*папки', state.get('guidance', '')), 'Russian reinstall guidance or failed-pin removal missing')
    need(re.search(r'Could not restore.*reinstall.*folder', failure.get('englishGuidance', ''))
         and restart.get('removed') is True and restart.get('reinstalled', {}).get('id') != identifier
         and restart.get('reinstalled', {}).get('enabled') is True and not restart['reinstalled'].get('error'), 'actual restart cleanup and reinstall incomplete')
    return after


def verify_media(value, audio, owners):
    need(audio.get('owned') is True and audio.get('format') == 'PCM16 mono WAV', 'media requires real owned audio')
    files = audio.get('files', [])
    need([f.get('name') for f in files] == ['one', 'two'] and all(f.get('bytes') == 720044 and re.fullmatch('[0-9a-f]{64}', f.get('sha256', '')) for f in files)
         and files[0]['sha256'] != files[1]['sha256'], 'owned PCM files differ from the declared workload')
    need({'/audio/one.wav', '/audio/two.wav'} <= {r.get('path') for r in audio.get('requests', [])}, 'actual audio network requests absent')
    for key, mode, seek in [('full', 'full', False), ('compact', 'compact', True), ('returned', 'full', False)]:
        state = value.get(key, {})
        need(state.get('mode') == mode and state.get('visible') is True and state.get('hidden') is False
             and state.get('seekHidden') is seek, 'media full/compact/return UI failed')
        rect(state.get('bounds')); rect(state.get('returnBounds'))
    need(value.get('originDesktop') != value.get('otherDesktop') and value['full'].get('desktopId') == value['returned'].get('desktopId') == value.get('originDesktop')
         and value['compact'].get('desktopId') == value.get('otherDesktop'), 'media did not return to its source desktop')
    for key in ('nativeBefore', 'nativeAfter'):
        N['native'](value.get(key, {}), owners[0])
    before, after = value.get('before', {}), value.get('after', {})
    need(before.get('id') and after.get('id') and before['id'] != after['id'] and before.get('trackTitle') == 'Owned first track'
         and after.get('trackTitle') == 'Owned replacement track' and after.get('paused') is False, 'pending refresh lost the replacement player')
    replacement = value.get('replacement', {})
    N['flags'](replacement, ('readPending', 'distinctElement', 'distinctPlayerId'), 'real in-flight replacement not exercised')
    guest = replacement.get('guest', {})
    need(guest.get('replaceClickTrusted') is True and guest.get('error') is None and guest.get('current') == 'audio-two'
         and len(guest.get('audio', [])) == 1 and guest['audio'][0].get('id') == 'audio-two' and guest['audio'][0].get('paused') is False, 'replacement actual audio element differs')
    events = value.get('nativeEvents', [])
    need(len(events) >= 2 and all(e.get('type') == 'media-started-playing' and finite(e.get('at')) for e in events)
         and finite(replacement.get('heldAt')) and any(0 <= e['at'] - replacement['heldAt'] < 1700 for e in events), 'actual native replacement event missed the pending read deadline')
    N['flags'](value, ('pauseResumeOriginal', 'unrelatedPaused'), 'widget commands affected an unrelated original element')


def process_binding(evidence, facts, raw, written_raw, platform):
    if platform == 'darwin':
        _, processes = evidence.json('mouse-637-features-processes.json')
    else:
        _, wrapper = evidence.json('mouse-' + ('windows' if platform == 'win32' else 'linux') + '-verification.json')
        processes = wrapper.get('checks', {}).get('features637', {})
    need(processes.get('reportSha256') == sha(raw), 'native wrapper binds another637 feature report')
    inputs = {}
    for phase, marker, pid, limit, name, data in [('write', WRITE_MARKER, facts['pid'], 270000, WRITE, written_raw),
            ('read', MARKER, facts['restart']['pid'], 120000, NAME, raw)]:
        process = processes.get(phase, {})
        logfile = 'mouse-637-features-' + phase + '.log'
        log = evidence.read(logfile)
        need(isinstance(log, bytes) and 0 < len(log) <= 16 * 1024**2 and marker in log.decode('utf-8').splitlines(), '637 feature native process success marker absent')
        need(process.get('pid') == pid and process.get('exitCode') == 0 and finite(process.get('elapsedMs'))
             and 0 < process['elapsedMs'] <= limit and process.get('requiredMarkers') == [marker]
             and process.get('log') == logfile and process.get('logSha256') == sha(log)
             and process.get('report') == name and process.get('reportSha256') == sha(data), '637 two-process/raw report/log byte binding differs')
        inputs[logfile] = sha(log)
    return inputs


def verify(read, *, expected_platform=None, expected_arch=None):
    evidence = N['Evidence'](read)
    raw, facts = evidence.json(NAME)
    written_raw, written = evidence.json(WRITE)
    platform, arch, pid = (facts.get(k) for k in ('platform', 'arch', 'pid'))
    need((platform, arch) in (('darwin', 'arm64'), ('win32', 'x64'), ('linux', 'x64'))
         and (expected_platform is None or platform == expected_platform) and (expected_arch is None or arch == expected_arch), '637 features belong to another platform')
    need(facts.get('schema') == 1 and facts.get('version') == VERSION and facts.get('budgetMs') == 240000 and positive(pid)
         and facts.get('writePid') == pid and facts.get('phase') == 'complete' and facts.get('stage') == 'complete'
         and facts.get('source') == 'Installed app, native input, owned loopback audio, real persistent-session extension and separate-process restoration', '637 installed native identity incomplete')
    N['flags'](facts, ('ok', 'restored', 'packaged', 'profileIsolated', 'writeComplete'), '637 features did not complete')
    need(all(facts.get(k) is False for k in ('physicalUserDeviceVerified', 'chromeWebStoreVerified', 'vkVerified', 'awaitingRestart'))
         and not facts.get('error') and not facts.get('cleanupErrors') and not facts.get('failureCaptureError'), '637 feature scope overstated or cleanup failed')
    restart = facts.get('restart', {})
    restart_pid = restart.get('pid')
    need(positive(restart_pid) and restart_pid != pid and restart.get('writePid') == pid and restart.get('processChanged') is True
         and restart.get('budgetMs') == 90000 and finite(restart.get('elapsedMs')) and 0 < restart['elapsedMs'] <= 90000
         and finite(facts.get('writeElapsedMs')) and 0 < facts['writeElapsedMs'] <= 240000
         and facts.get('elapsedMs') == facts['writeElapsedMs'] + restart['elapsedMs'], '637 restart process/budget absent')
    need(written.get('writeComplete') is True and written.get('awaitingRestart') is True and written.get('ok') is False
         and written.get('restored') is False and written.get('phase') == 'write' and written.get('stage') == 'awaiting-restart', '637 original write-phase receipt was not retained')
    for key in ('schema', 'version', 'platform', 'arch', 'pid', 'writePid', 'profile', 'profileIsolated', 'packaged', 'source',
                'budgetMs', 'writeElapsedMs', 'writeCleanup', 'language', 'interface', 'extensions', 'media', 'audio', 'restoreFixture', 'fixtureOrigin'):
        need(key in written and written[key] == facts.get(key), '637 restart rewrote the original ' + key + ' evidence')
    need(written.get('appearance') == {k: v for k, v in facts.get('appearance', {}).items() if k != 'restart'}, 'appearance write receipt changed after restart')
    need(facts.get('nativeInputs', [])[:len(written.get('nativeInputs', []))] == written.get('nativeInputs')
         and facts.get('captures', [])[:len(written.get('captures', []))] == written.get('captures'), '637 restart rewrote its native input/frame ledger')
    for cleanup in (facts.get('writeCleanup', {}), restart.get('cleanup', {})):
        N['flags'](cleanup, ('restored', 'desktopStateRestored'), '637 workspace cleanup incomplete')
    origin = facts.get('fixtureOrigin')
    need(isinstance(origin, str) and re.fullmatch(r'http://127\.0\.0\.1:\d+', origin), '637 audio fixture is not owned loopback')
    owners = verify_appearance(facts.get('appearance', {}), pid, restart_pid, origin)
    verify_language(facts.get('language', {}))
    verify_interface(facts.get('interface', {}), owners)
    extension_native = verify_extensions(facts.get('extensions', {}), facts.get('restoreFixture', {}), restart)
    verify_media(facts.get('media', {}), facts.get('audio', {}), owners)
    native = facts.get('nativeInputs', [])
    need(isinstance(native, list) and 50 <= len(native) <= 200, '637 actual input ledger missing')
    for row in native:
        input_event(row, platform, {pid, restart_pid})
    need(all(s['resize']['input'] in native for s in facts['appearance']['samples']), 'square resize inputs absent from actual process ledger')
    expected_selectors = {'#language-select', '.language-chooser-search', '#media-play', '#media-replace', '#extension-action', '#mouse-extensions-install',
                          '#settings-square-grid', '#settings-white-tone', '#settings-white-tone-reset', '#mouse-media-widget [data-media=return]',
                          '#mouse-media-widget [data-media=toggle]', '.divider[data-path=""]', '.divider[data-path=""] > .divider-hit'}
    need(expected_selectors <= {r['selector'] for r in native}, '637 mandatory native control was never exercised')
    captures = facts.get('captures', [])
    need([c.get('filename') for c in captures] == CAPTURES and len(written.get('captures', [])) == 13, '637 exact native frame ledger differs')
    witness_specs = {
        'interface-light': [(facts['interface']['themes'][0]['compactNatives'][1], [43, 164, 99], (58, 245))],
        'interface-dark': [(facts['interface']['themes'][1]['compactNatives'][1], [43, 164, 99], (58, 245))],
        'extensions-pane': [(extension_native, [37, 143, 191], (69, 182))],
        'media-full': [(facts['media']['nativeBefore'], [43, 164, 99], (58, 245))],
        'media-replacement': [(facts['media']['nativeAfter'], [153, 69, 193], (58, 245))],
    }
    for sample in facts['appearance']['samples']:
        witness_specs['appearance-square-' + sample['theme']] = [(row, [153, 69, 193] if i == 0 else [43, 164, 99], (58, 245)) for i, row in enumerate(sample['native'])]
    for i, row in enumerate(captures):
        need(row.get('pid') == (pid if i < 13 else restart_pid) and row.get('kind') == 'screen', '637 OS frame belongs to another process')
        image = evidence.screen(row)
        specs = witness_specs.get(row['filename'][10:-4], [])
        probes = row.get('probes', [])
        need(len(probes) == len(specs), '637 native guest pixels absent')
        for probe, (native_view, color, offset) in zip(probes, specs):
            point = {'x': native_view['bounds']['x'] + offset[0], 'y': native_view['bounds']['y'] + offset[1]}
            need(probe.get('name') == 'owned native guest' and probe.get('tabId') == native_view['tabId'] and probe.get('webContentsId') == native_view['webContentsId']
                 and probe.get('point') == point and probe.get('expectedRGB') == color and probe.get('tolerance') == 3, '637 native guest probe placement/identity/color differs')
            x, y, rgba = evidence.pixel(image, row['mapping'], point)
            need(probe.get('x') == x and probe.get('y') == y and probe.get('actualRGBA') == rgba and rgba[3] == 255
                 and all(abs(rgba[j] - color[j]) <= 3 for j in range(3)) and probe.get('accepted') is True, '637 native guest probe disagrees with actual OS bytes')
        attempts = row.get('attempts', [])
        need(1 <= len(attempts) <= 6 and [a.get('attempt') for a in attempts] == list(range(1, len(attempts) + 1))
             and attempts[-1].get('accepted') is True, '637 bounded OS presentation acquisition incomplete')
    inputs = {NAME: sha(raw), WRITE: sha(written_raw), **process_binding(evidence, facts, raw, written_raw, platform)}
    return {'ok': True, 'version': VERSION, 'platform': platform, 'arch': arch, 'pid': pid, 'restartPid': restart_pid,
            'marker': MARKER, 'inputs': inputs, 'nativeCaptures': list(evidence.receipts.values()),
            'appearance': {'bothThemes': True, 'gapFreeNativeViews': True, 'defaultColor': '#d4d4d4', 'twoProcessPersistence': True}}
