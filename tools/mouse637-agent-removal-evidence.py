#!/usr/bin/env python3
"""Independently verify installed637 Agent absence and retained browser pages."""
from pathlib import Path
import re
import runpy
from urllib.parse import urlsplit

N = runpy.run_path(str(Path(__file__).with_name('mouse637-native-evidence.py')))
need, sha = N['need'], N['sha']
NAME = 'mouse-637-agent-removal.json'
MARKER = 'MOUSE_637_AGENT_REMOVAL_PASS'
CONTRACT = 'mouse637-agent-removal-v1'
SOURCE = 'Installed package paths and executable bytes, actual shell/preload readbacks and retained owned native pages'
CAPTURES = ['mouse-637-agent-removed-light.png', 'mouse-637-agent-removed-dark.png']
SELECTORS = ['#agent-panel', '#agent-settings-page', '#agent-local-workspace', '.home-agent-open',
             '[data-action="assistant"]', '[data-agent-settings]', '[data-mode="agents"]',
             '[data-ai-url="mouse://agent"]', '#ai-select option[value="mouse://agent"]', '.localhost-start']
APP_PATHS = ['mouse-agent', 'mouse/agent-ui.js', 'mouse/agent-chat.css', 'mouse/agent-onboarding.js',
             'mouse/agent-onboarding.css', 'mouse/agent-brand.js', 'mouse/agent-brand.css',
             'mouse/local-workspace.js', 'mouse/local-workspace.css', 'mouse/agent-vendor',
             'mouse/vendor/xterm', 'mouse/vendor/xterm.js', 'mouse/vendor/xterm.css'] + [
             'mouse/agent-mouse-' + color + '.svg' for color in ('orange', 'cyan', 'green', 'violet', 'coral')]
RESOURCE_PATHS = ['mouse-agent-node_modules']
CODE_PATHS = ['mouse-main.cjs', 'mouse-preload.cjs', 'page-pointer-preload.cjs']
CODE_EVIDENCE = ['mouse-637-agent-code-main.cjs', 'mouse-637-agent-code-preload.cjs',
                 'mouse-637-agent-code-page-pointer-preload.cjs']
FORBIDDEN_CODE = ['mouse-agent/', 'mouse:agent', 'MouseAgent', 'node-pty', '@modelcontextprotocol/sdk', '@xterm/']
AI_CATALOG = ['https://chatgpt.com/', 'https://claude.ai/', 'https://gemini.google.com/', 'https://chat.deepseek.com/']
MODES = ['content', 'design', 'support', 'trader']
SECTIONS = ['appearance', 'workspace', 'imports', 'privacy', 'capture', 'downloads', 'documents', 'updates', 'about']


def website(value):
    if not isinstance(value, str) or not re.match(r'^https?://', value):
        return False
    authority = re.split(r'[/?#]', value.split('://', 1)[1], maxsplit=1)[0]
    if any(character.isspace() for character in authority):
        return False
    try:
        parsed = urlsplit(value)
        hostname, port = parsed.hostname, parsed.port
        return bool(hostname) and not any(character.isspace() for character in hostname) and (
            port is None or 0 <= port <= 65535)
    except ValueError:
        return False


def package(read, value):
    need(isinstance(value, dict) and isinstance(value.get('appPath'), str) and value['appPath'].endswith('app.asar')
         and isinstance(value.get('resourcesPath'), str) and value['resourcesPath'], 'actual installed ASAR/resources paths missing')
    paths = value.get('paths', [])
    expected = [('app', path) for path in APP_PATHS] + [('resources', path) for path in RESOURCE_PATHS]
    need(isinstance(paths, list) and [(row.get('root'), row.get('path')) for row in paths] == expected
         and all(row.get('exists') is False for row in paths), 'removed Agent remains in installed application/resources')
    code = value.get('code', [])
    need(isinstance(code, list) and [row.get('path') for row in code] == CODE_PATHS
         and [row.get('evidenceFile') for row in code] == CODE_EVIDENCE, 'actual executable evidence ledger differs')
    inputs = {}
    for row in code:
        raw = read(row['evidenceFile'])
        need(isinstance(raw, bytes) and 0 < len(raw) <= 2 * 1024**2 and row.get('bytes') == len(raw)
             and row.get('sha256') == sha(raw) and row.get('forbidden') == [], 'packaged executable bytes/hash differ')
        text = raw.decode('utf-8')
        need(all(token not in text for token in FORBIDDEN_CODE), 'packaged executable still contains an Agent dependency/API')
        inputs[row['evidenceFile']] = sha(raw)
    return inputs


def ui(value):
    need(isinstance(value, dict) and isinstance(value.get('selectors'), dict)
         and list(value['selectors']) == SELECTORS
         and all(type(count) is int and count == 0 for count in value['selectors'].values()), 'removed Agent UI control remains')
    need(all(value.get(key) == [] for key in ('preloadKeys', 'globals', 'modelKeys')),
         'removed Agent API, renderer or active model remains')
    modes, presets = value.get('modes'), value.get('presetKeys')
    need(isinstance(modes, list) and sorted(modes) == MODES and isinstance(presets, list)
         and all(key in MODES for key in presets) and len(set(presets)) == len(presets), 'removed Agent mode/preset remains')
    options = value.get('aiOptions')
    need(isinstance(options, list) and options[:4] == AI_CATALOG and len(options) <= 100
         and options.count('custom') == 1 and all(url == 'custom' or website(url) for url in options),
         'ordinary AI website chooser was removed or retains an Agent service')
    need(value.get('settingsSections') == SECTIONS, 'browser settings sections differ or retain Agent settings')


def verify(read, *, owner=None):
    evidence = N['Evidence'](read)
    raw, facts = evidence.json(NAME)
    if owner is None:
        _, owner = evidence.json('mouse-636-owner-feedback.json')
    need(isinstance(owner, dict) and owner.get('agentRemoval') == {
        **facts, 'reportFile': NAME, 'reportSha256': sha(raw)}, 'removal owner/report bytes differ')
    platform, arch, pid = facts.get('platform'), facts.get('arch'), facts.get('pid')
    need((platform, arch) in (('darwin', 'arm64'), ('win32', 'x64'), ('linux', 'x64'))
         and all(owner.get(key) == facts.get(key) for key in ('version', 'platform', 'arch', 'pid'))
         and facts.get('version') == '6.0.37' and N['positive'](pid)
         and facts.get('schema') == 1 and facts.get('contract') == CONTRACT and facts.get('source') == SOURCE,
         'removal installed process/contract differs')
    N['flags'](facts, ('ok', 'restored', 'packaged'), 'Agent removal check did not finish and restore')
    need(owner.get('packaged') is True and owner.get('profileIsolated') is True and owner.get('budgetMs') == 240000
         and N['finite'](facts.get('elapsedMs')) and 0 < facts['elapsedMs'] <= owner['budgetMs']
         and facts.get('physicalUserDeviceVerified') is False and not facts.get('error') and not facts.get('cleanupError'),
         'removal check failed or overstated its scope/budget')
    need(facts.get('runtime') == {'contextHasAgentHost': False, 'contextAgentHostType': 'undefined'},
         'installed application still creates an Agent host')
    inputs = {NAME: sha(raw), **package(read, facts.get('package'))}
    origin = facts.get('fixtureOrigin', '')
    need(isinstance(origin, str) and re.fullmatch(r'http://127\.0\.0\.1:[0-9]+', origin), 'removal page fixture origin differs')
    before, after = facts.get('pages', {}).get('before'), facts.get('pages', {}).get('after')
    need(isinstance(before, list) and isinstance(after, list) and len(before) == len(after) == 2
         and [row.get('index') for row in before] == [201, 202], 'retained page pair missing')
    for old, new in zip(before, after):
        N['identity'](old, new, origin)
    need(len({row['id'] for row in before}) == len({row['webContentsId'] for row in before}) == 2,
         'retained page pair does not contain two distinct native pages')
    apis = facts.get('pageAPIs', [])
    need(isinstance(apis, list) and [row.get('tabId') for row in apis] == [row['id'] for row in before]
         and all(row.get('mouseAgentType') == 'undefined' and row.get('progressType') == 'function' for row in apis),
         'page bridge still exposes Agent or lost ordinary progress')
    themes = facts.get('themes', [])
    need(isinstance(themes, list) and [row.get('theme') for row in themes] == ['light', 'dark']
         and facts.get('captures') == CAPTURES and [row.get('capture') for row in themes] == CAPTURES,
         'both-theme removal scenes missing')
    captures = {row.get('filename'): row for row in owner.get('captures', [])}
    native_inputs = owner.get('nativeInputs', [])
    for selector in ('#settings-button', '#settings-dialog [data-close-dialog]'):
        matches = [row for row in native_inputs if row.get('selector') == selector]
        need(len(matches) >= 2, 'native browser settings round trips missing')
        for row in matches:
            N['input_event'](row, platform, selector)
    for scene in themes:
        ui(scene)
        native = scene.get('native', [])
        need(isinstance(native, list) and len(native) == 2, 'removal scene native pages missing')
        for row, page in zip(native, before):
            N['native'](row, page)
        name = scene['capture']
        need(name in captures, 'removal frame absent from actual owner capture ledger')
        evidence.screen(captures[name])
        for key in ('filename', 'displayFilename'):
            filename = captures[name][key]; inputs[filename] = sha(read(filename))
    return {'ok': True, 'version': '6.0.37', 'platform': platform, 'arch': arch, 'pid': pid,
            'reportSha256': sha(raw), 'inputs': inputs, 'nativeCaptures': CAPTURES,
            'canonicalCaptures': CAPTURES, 'physicalUserDeviceVerified': False}
