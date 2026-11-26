#!/usr/bin/env python3
"""Retain byte-frozen640 gates with current641 and exact640 predecessors.

The accepted640 source and packages remain immutable. This adapter advances
only current identities and the explicitly superseded641 UI contracts. Native
input ownership, profile, update, security and graphics checks are retained.
"""
import ast
import hashlib
import json
from pathlib import Path
import runpy

TOOLS = Path(__file__).resolve().parent
FROZEN = json.loads((TOOLS / 'mouse641-frozen.json').read_text())
MODULES = {name: name.replace('mouse640-', 'mouse641-').replace('test_mouse640_', 'test_mouse641_')
           for name in FROZEN}
PUBLISHED_SOURCE = '7428ecf52698e62468bb7befb9d7d2d06ee7b6d9'
PUBLISHED_UPDATER = '91ab363f926774825caf8055b2d3d81bf0d51264'
PUBLISHED_PINS = {'arm64': 'be5b2efb0ce1279043e99e642299f1a32bb78e979a0759f66e81dc828e500144',
 'linux-x64': 'd9572e122ecd359b1e84274b14383954db1dc3f1956142139c9286a0b8b8b82b',
 'windows-x64': '3411d3d02785638620a176ca114e818197a0c66883c8fbdd9d83f5e800819814'}


def checked(name):
    if name not in FROZEN:
        raise ValueError('Unreviewed641 predecessor dependency: ' + name)
    raw = (TOOLS / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
        raise ValueError('Immutable641 predecessor dependency changed: ' + name)
    return raw


def verify_frozen():
    for name in FROZEN:
        checked(name)
    legacy()['verify_frozen']()


def previous(platform):
    folder = {'darwin': 'arm64', 'linux': 'linux-x64', 'win32': 'windows-x64'}[platform]
    raw = (TOOLS.parent / 'staging/mouse' / ('6.0.40-' + folder) / 'pin.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != PUBLISHED_PINS[folder]:
        raise ValueError('Immutable640 predecessor pin bytes changed: ' + folder)
    value = json.loads(raw)
    if value.get('version') != '6.0.40' or value.get('source') != PUBLISHED_SOURCE or value.get('ready') is not True:
        raise ValueError('Immutable640 predecessor identity changed')
    return {'version': '6.0.40', 'source': PUBLISHED_SOURCE, 'updaterBlobSHA': PUBLISHED_UPDATER,
            **{key: value[key] for key in ('packages', 'package') if key in value}}


def baselines():
    def package(platform, name, tag):
        old = previous(platform)
        data = old.get('packages', {}).get(name) or old.get('package')
        return {'name': name, 'tag': tag, 'size': data['size'], 'sha256': data['sha256']}
    return {'darwin': package('darwin', 'Mouse-Browser-6.0.40-mac-arm64.dmg', 'quadro-macos-v6.0.40-arm64'),
            'win32': package('win32', 'Mouse-Browser-6.0.40-Windows-x64.exe', 'mouse-windows-v6.0.40-x64'),
            'linux': {fmt: package('linux', 'Mouse-Browser-6.0.40-Linux-x64.' + suffix, 'mouse-linux-v6.0.40-x64')
                      for fmt, suffix in (('appimage', 'AppImage'), ('deb', 'deb'))}}


def legacy():
    checked('mouse640-reuse.py')
    checked('mouse640-frozen.json')
    return runpy.run_path(str(TOOLS / 'mouse640-reuse.py'))


def target(name):
    if name in MODULES:
        return MODULES[name]
    old = legacy()['target'](name)
    if old not in MODULES:
        raise ValueError('Unreviewed641 legacy target: ' + name)
    return MODULES[old]


PREDECESSOR_MODULES = {'mouse637-current.py', 'mouse637-upgrade-evidence.py',
    'mouse637-update-button-evidence.py', 'mouse637-performance-evidence.py',
    'mouse637-public-channel.py', 'mouse637-windows-display-evidence.py',
    'mouse634-linux-release.py', 'mouse633-linux-evidence.py'}
SETTINGS_SECTIONS = ['privacy', 'overview-links', 'appearance', 'surface-theme',
    'surface-top', 'surface-bottom', 'surface-workspace', 'interface', 'scale',
    'workspace', 'imports', 'passwords', 'adblock-exclusions', 'private-browsing',
    'capture', 'downloads', 'documents', 'updates', 'about']
SETTINGS_PAGES = ['overview', 'appearance', 'surfaces', 'workspace', 'privacy',
    'imports', 'capture', 'downloads', 'documents', 'about']


def contracts():
    # Lazy loading avoids cycles through retained task/native primitive readers.
    return runpy.run_path(str(TOOLS / 'mouse641-owner-contracts.py'))


def adapted_tree(name, *, current_native=False):
    tree = ast.parse(checked(name), filename=str(TOOLS / name)) if name in FROZEN else legacy()['adapted_tree'](name, current_native=current_native)
    changed = {}
    def mark(key):
        changed[key] = changed.get(key, 0) + 1

    class Identity(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            node = self.generic_visit(node)
            if name == 'mouse633-owner-feedback-evidence.py' and node.name == 'settings_contract':
                if ast.unparse(node.body[0]) != "value = facts.get('settings', {})":
                    raise ValueError('Frozen Settings readback binding changed')
                mark('settings_branding')
                node.body[1:1] = ast.parse("_mouse641_contracts()['settings_branding'](value)").body
            if name == 'mouse637-features-evidence.py':
                if node.name == 'input_event':
                    mark('link_input')
                    node.body[:0] = ast.parse("""
if isinstance(row, dict) and row.get('action') == 'intercepted-link':
    return _mouse641_contracts()['link_input'](row, platform, pids)
""").body
                elif node.name == 'verify_media':
                    mark('media_removed')
                    node.body = ast.parse("return _mouse641_contracts()['reader']()['verify_media_removal'](value, audio, owners)").body
                elif node.name == 'verify_interface':
                    for row in ast.walk(node):
                        if isinstance(row, ast.Expr) and isinstance(row.value, ast.Call) and any(
                                isinstance(arg, ast.Constant) and arg.value == 'compact header lacks native hover/keyboard restoration' for arg in row.value.args):
                            mark('always_header')
                            row.value = ast.parse("_mouse641_contracts()['compact_headers'](compact, keyboard)", mode='eval').body
                elif node.name == 'verify_ai_preview':
                    for index, row in enumerate(node.body):
                        if isinstance(row, ast.Expr) and isinstance(row.value, ast.Call) and any(
                                isinstance(arg, ast.Constant) and arg.value == 'AI link was not clicked by native input' for arg in row.value.args):
                            mark('ai_routes')
                            node.body[index] = ast.parse("_mouse641_contracts()['preview_routes'](value, platform, pid, inputs)").body[0]
                        if isinstance(row, ast.For) and ast.unparse(row.iter) == "(opened.get('input', {}), header.get('open', {}))":
                            mark('explicit_preview')
                            node.body[index:index + 1] = ast.parse("""
_mouse641_contracts()['preview_setup'](opened.get('input', {}), chat['id'], preview_id, preview_origin + '/page/3/', 'Explicit fixture setup for existing lower-pane resize and transfer controls; not a native-link outcome')
_mouse641_contracts()['preview_setup'](header.get('open', {}), chat['id'], header['before']['id'], preview_origin + '/page/3/', 'Explicit fixture setup for existing lower-pane resize and transfer controls; not a native-link outcome')
""").body
                            break
            if name == 'mouse636-retained-owner-evidence.py':
                if node.name == 'canceled_chat_navigation':
                    mark('chat_interception')
                    node.body = ast.parse("return _mouse641_contracts()['retained_chat'](ai, platform, origin, preview_origin, N)").body
                elif node.name == 'verify':
                    start = next(i for i, row in enumerate(node.body) if isinstance(row, ast.Assign) and ast.unparse(row.targets[0]) == 'ai')
                    end = next(i for i, row in enumerate(node.body) if isinstance(row, ast.Assign) and ast.unparse(row.targets[0]) == 'main_downloads')
                    mark('retained_ai')
                    node.body[start:end] = ast.parse("""
ai = facts.get('aiPreview', {})
chat, main_before, reopened_id = _mouse641_contracts()['retained_ai'](ai, platform, pid, primary, preview_origin, facts.get('nativeInputs', []), N, ai_split)
""").body
            if name == 'mouse632-feedback-evidence.py' and node.name == 'verify_media':
                mark('stationary_removed')
                node.body[1:1] = ast.parse("_mouse641_contracts()['reader']()['verify_stationary_removal'](facts.get('mediaPlayerRemoved', {}))").body
            return node

        def visit_If(self, node):
            node = self.generic_visit(node)
            if name == 'mouse637-sidebar-focus-evidence.py' and ast.unparse(node.test) == "kind == 'settings'":
                mark('library_glass')
                return ast.parse("""
if kind in ('settings', 'library'):
    _mouse640_settings_surface(shell.get(kind, {}), shell.get('toolbar', {}), theme)
    if kind == 'library':
        need(all(shell.get('library', {}).get(key) == shell.get('settings', {}).get(key) for key in ('backgroundColor', 'backgroundImage', 'backdropFilter', 'borderColor')), 'library does not share the actual Settings glass material')
""").body[0]
            return node

        def visit_Subscript(self, node):
            node = self.generic_visit(node)
            if name == 'mouse636-retained-owner-evidence.py' and ast.unparse(node) in ("ai['blankClick']", "ai['sameClick']"):
                index = 0 if ast.unparse(node) == "ai['blankClick']" else 1
                return ast.parse("ai['linkRouting'][" + str(index) + "]['input']", mode='eval').body
            return node

        def visit_Compare(self, node):
            node = self.generic_visit(node)
            if name == 'mouse636-retained-owner-evidence.py':
                if ast.unparse(node) == 'len(requests) == 6':
                    mark('request_count'); return ast.parse('len(requests) == 7', mode='eval').body
                if ast.unparse(node) == "cleanup['ownedPagesClosed'] >= 5":
                    mark('owned_count'); return ast.parse("cleanup['ownedPagesClosed'] >= 7", mode='eval').body
            return node

        def visit_List(self, node):
            node = self.generic_visit(node)
            if name == 'mouse636-retained-owner-evidence.py' and ast.unparse(node) == '[0, 1, 2, 3, 4, 3]':
                return ast.parse('[0, 1, 2, 3, 4, 3, 3]', mode='eval').body
            if (name == 'mouse633-owner-feedback-evidence.py' and all(isinstance(item, ast.Constant) for item in node.elts)
                    and ast.literal_eval(node) == SETTINGS_PAGES[:2] + SETTINGS_PAGES[3:]):
                return ast.parse(repr(SETTINGS_PAGES), mode='eval').body
            return node

        def visit_Constant(self, node):
            if not isinstance(node.value, str):
                return node
            value = node.value.replace('6.0.40', '6.0.41')
            for old, new in MODULES.items():
                value = value.replace(old, new)
            value = value.replace('mouse640-release', 'mouse641-release').replace('mouse640-linux-release', 'mouse641-linux-release').replace('mouse640-windows-release', 'mouse641-windows-release')
            value = value.replace('publish-mouse640', 'publish-mouse641').replace('MOUSE640_', 'MOUSE641_')
            for old, new in (
                ('MOUSE_640_REAL_639_TO_640_', 'MOUSE_641_REAL_640_TO_641_'),
                ('MOUSE_640_REAL_629_TO_640_', 'MOUSE_641_REAL_629_TO_641_'),
                ('MOUSE_640_WINDOWS_REAL_629_TO_640_', 'MOUSE_641_WINDOWS_REAL_629_TO_641_'),
                ('real-639-to-640-', 'real-640-to-641-'),
                ('real-629-to-640-', 'real-629-to-641-'),
                ('real-published-predecessor-to-640-', 'real-published-predecessor-to-641-'),
            ):
                value = value.replace(old, new)
            if name in PREDECESSOR_MODULES:
                value = value.replace('6.0.39', '6.0.40').replace('legacy639-update', 'legacy640-update')
                # Installed wrappers deliberately retain updateFrom638. No
                # predecessor evidence or native update assertion is renamed.
                value = value.replace('eccadb3a37abd00d039616b321292cba57a49941', PUBLISHED_SOURCE)
                value = value.replace('MOUSE_640_ACTUAL_639_UPDATER_', 'MOUSE_641_ACTUAL_640_UPDATER_')
                if value == '639':
                    value = '640'
            if name == 'mouse637-performance-evidence.py' and node.value == 'mouse639-task-evidence.py':
                value = 'mouse640-task-evidence.py'
            if name == 'mouse637-current.py':
                if value == 'MOUSE_640_REAL_':
                    value = 'MOUSE_641_REAL_'
                elif value == '_TO_640_PROFILE_PASS':
                    value = '_TO_641_PROFILE_PASS'
            if name == 'mouse637-features-evidence.py' and value == 'Owned cross-origin AI source, native resize and native chooser/header transfers':
                value = 'Native cross-origin link routing, explicit existing-preview fixture, native resize and native chooser/header transfers'
            if name == 'mouse637-sidebar-focus-evidence.py' and value == 'darkLibraryToolbarSurface':
                value = 'librarySettingsGlassBothThemes'
            if value == 'right-ai-links-lower-preview':
                value = 'right-ai-links-classic-existing-preview-retained'
            return ast.copy_location(ast.Constant(value=value), node) if value != node.value else node

        def visit_Assign(self, node):
            node = self.generic_visit(node)
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            replacement = None
            if name == 'mouse637-upgrade-evidence.py' and 'BASELINES' in names:
                replacement = baselines()
            if name == 'mouse634-linux-release.py' and 'PREVIOUS' in names:
                replacement = previous('linux')
            if name in ('mouse633-owner-feedback-evidence.py', 'mouse637-agent-removal-evidence.py') and 'SECTIONS' in names:
                replacement = SETTINGS_SECTIONS
            if name == 'mouse633-owner-feedback-evidence.py' and 'SETTINGS' in names:
                original = ('showBrandName', 'showFavicons', 'desktopGestures', 'downloadBounce', 'downloadBadge')
                if ast.literal_eval(node.value) != original:
                    raise ValueError('Frozen Settings toggle contract changed')
                mark('settings_toggles')
                replacement = original[1:]
            if name == 'mouse637-features-evidence.py' and 'expected_selectors' in names:
                mark('removed_controls')
                need_removed = {'#mouse-media-widget [data-media=return]', '#mouse-media-widget [data-media=toggle]'}
                values = ast.literal_eval(node.value)
                if not need_removed <= values:
                    raise ValueError('Frozen media control predicates changed')
                node.value = ast.parse(repr(values - need_removed), mode='eval').body
            if replacement is not None:
                node.value = ast.parse(repr(replacement), mode='eval').body
            return node

    tree = Identity().visit(tree)
    required = {'mouse637-features-evidence.py': ('link_input', 'media_removed', 'always_header', 'ai_routes', 'explicit_preview', 'removed_controls'),
                'mouse636-retained-owner-evidence.py': ('chat_interception', 'retained_ai', 'request_count', 'owned_count'),
                'mouse637-sidebar-focus-evidence.py': ('library_glass',),
                'mouse632-feedback-evidence.py': ('stationary_removed',),
                'mouse633-owner-feedback-evidence.py': ('settings_branding', 'settings_toggles')}.get(name, ())
    if any(changed.get(key) != 1 for key in required):
        raise ValueError('Current641 adaptation did not bind its frozen predicate: ' + repr(changed))
    return ast.fix_missing_locations(tree)


def load(name, *, namespace=None, current_native=False):
    scope = namespace if namespace is not None else {}
    original = scope.get('__name__')
    scope['__file__'] = str(TOOLS / ('mouse641-native-evidence.py' if current_native else target(name)))
    scope['__name__'] = 'retained641_' + name.replace('-', '_')
    scope['_mouse641_contracts'] = contracts
    if name == 'mouse632-release.py':
        def verify_mode_requests(facts, output):
            return runpy.run_path(str(TOOLS / 'mouse641-presets-evidence.py'))['verify_legacy_facts'](facts, output)
        scope['_mouse637_verify_mode_requests'] = verify_mode_requests
    if name == 'mouse633-owner-feedback-evidence.py':
        scope['_mouse637_zoom_color'] = runpy.run_path(str(TOOLS / 'mouse641-zoom-evidence.py'))['expected_rgb']
    try:
        exec(compile(adapted_tree(name, current_native=current_native), scope['__file__'], 'exec'), scope)
    finally:
        if original is not None:
            scope['__name__'] = original
    return scope


def execute(name, scope):
    scope['_mouse641_contracts'] = contracts
    tree = adapted_tree(name)
    exec(compile(tree, scope['__file__'], 'exec'), scope)
