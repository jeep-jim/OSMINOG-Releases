#!/usr/bin/env python3
"""Retain byte-frozen639 gates with current640 and exact639 predecessors.

Archived validators, published pins and evidence bytes are immutable. The
current adapter changes identities and only the explicitly revised settings
presentation; all retained native input, profile and package checks remain.
"""
import ast
import hashlib
import json
from pathlib import Path
import runpy

TOOLS = Path(__file__).resolve().parent
FROZEN = json.loads((TOOLS / 'mouse640-frozen.json').read_text())
MODULES = {name: name.replace('mouse639-', 'mouse640-').replace('test_mouse639_', 'test_mouse640_')
           for name in FROZEN}
PUBLISHED_SOURCE = 'eccadb3a37abd00d039616b321292cba57a49941'
PUBLISHED_UPDATER = '91ab363f926774825caf8055b2d3d81bf0d51264'
PUBLISHED_PINS = {
    'arm64': 'be2467138a764a1682acd246c405270de94239e569d1a07dc373a7957577ae95',
    'linux-x64': 'efda4f775444948e1098de4e72a0b217d194dc047936f6c7bc3f091b3087aca5',
    'windows-x64': 'b25c6ac00c2b7ca3ce67e171905ca3e52099bc5e465664995aec51c27887b9de',
}


def checked(name):
    if name not in FROZEN:
        raise ValueError('Unreviewed640 predecessor dependency: ' + name)
    raw = (TOOLS / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
        raise ValueError('Immutable640 predecessor dependency changed: ' + name)
    return raw


def verify_frozen():
    for name in FROZEN:
        checked(name)


def previous(platform):
    folder = {'darwin': 'arm64', 'linux': 'linux-x64', 'win32': 'windows-x64'}[platform]
    raw = (TOOLS.parent / 'staging/mouse' / ('6.0.39-' + folder) / 'pin.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != PUBLISHED_PINS[folder]:
        raise ValueError('Immutable639 predecessor pin bytes changed: ' + folder)
    value = json.loads(raw)
    if value.get('version') != '6.0.39' or value.get('source') != PUBLISHED_SOURCE or value.get('ready') is not True:
        raise ValueError('Immutable639 predecessor identity changed')
    return {'version': '6.0.39', 'source': PUBLISHED_SOURCE, 'updaterBlobSHA': PUBLISHED_UPDATER,
            **{key: value[key] for key in ('packages', 'package') if key in value}}


def baselines():
    def package(platform, name, tag):
        old = previous(platform)
        data = old.get('packages', {}).get(name) or old.get('package')
        return {'name': name, 'tag': tag, 'size': data['size'], 'sha256': data['sha256']}
    return {'darwin': package('darwin', 'Mouse-Browser-6.0.39-mac-arm64.dmg', 'quadro-macos-v6.0.39-arm64'),
            'win32': package('win32', 'Mouse-Browser-6.0.39-Windows-x64.exe', 'mouse-windows-v6.0.39-x64'),
            'linux': {fmt: package('linux', 'Mouse-Browser-6.0.39-Linux-x64.' + suffix, 'mouse-linux-v6.0.39-x64')
                      for fmt, suffix in (('appimage', 'AppImage'), ('deb', 'deb'))}}


def legacy():
    checked('mouse639-reuse.py')
    checked('mouse639-frozen.json')
    checked('mouse639-task-evidence.py')
    return runpy.run_path(str(TOOLS / 'mouse639-reuse.py'))


def target(name):
    if name in MODULES:
        return MODULES[name]
    old = legacy()['target'](name)
    if old not in MODULES:
        raise ValueError('Unreviewed640 legacy target: ' + name)
    return MODULES[old]


PREDECESSOR_MODULES = {'mouse637-current.py', 'mouse637-upgrade-evidence.py',
    'mouse637-update-button-evidence.py', 'mouse637-performance-evidence.py',
    'mouse637-public-channel.py', 'mouse637-windows-display-evidence.py',
    'mouse634-linux-release.py', 'mouse633-linux-evidence.py'}
SETTINGS_SECTIONS = ['privacy', 'overview-links', 'appearance', 'interface', 'scale',
    'workspace', 'imports', 'passwords', 'private-browsing', 'capture', 'downloads',
    'documents', 'updates', 'about']


def adapted_tree(name, *, current_native=False):
    tree = ast.parse(checked(name), filename=str(TOOLS / name)) if name in FROZEN else legacy()['adapted_tree'](name, current_native=current_native)

    changed = {'input_budget': 0, 'settings_overview': 0}

    class Identity(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            node = self.generic_visit(node)
            if name == 'mouse633-owner-feedback-evidence.py' and node.name == 'settings_contract':
                #Category receipts are additional proof; all legacy control,
                #search, persistence, workspace and native-page checks remain.
                extra = ast.parse("""
categories = value.get('categoryInputs', [])
need(isinstance(categories, list) and {'appearance', 'workspace', 'downloads', 'imports'} <= {row.get('page') for row in categories}, 'Settings category navigation missing')
for row in categories:
    event = row.get('input', {})
    need(event in facts.get('nativeInputs', []) and event.get('selector') == '#settings-dialog .settings-nav-item[data-settings-page="' + row.get('page', '') + '"]' and any(e.get('type') == 'click' and e.get('trusted') is True and e.get('matches') is True for e in event.get('events', [])), 'Settings category was not selected with its trusted native control')
""").body
                #The first statement assigns value; no predicate is removed.
                node.body[1:1] = extra
            return node

        def visit_If(self, node):
            node = self.generic_visit(node)
            if (name == 'mouse637-sidebar-focus-evidence.py'
                    and ast.unparse(node.test) == "theme == 'dark' and kind"):
                #640 deliberately gives Settings its own glass material. The
                #unchanged library still has the actual dark toolbar surface.
                original = node
                original.test = ast.parse("theme == 'dark' and kind == 'library'", mode='eval').body
                return ast.If(test=ast.parse("kind == 'settings'", mode='eval').body,
                    body=ast.parse("_mouse640_settings_surface(shell.get('settings', {}), shell.get('toolbar', {}), theme)").body,
                    orelse=[original])
            return node

        def visit_Compare(self, node):
            node = self.generic_visit(node)
            if (name == 'mouse637-features-evidence.py'
                    and ast.unparse(node) == '50 <= len(native) <= 200'):
                # The independently validated Settings640 route adds exactly 15
                # native clicks per theme: open, 8 categories, appearance, 2 search
                # focuses, clear, narrow overview, close. Keep the old 200 budget
                # plus those 30 real controls; every ledger row still validates.
                changed['input_budget'] += 1
                return ast.parse('50 <= len(native) <= 230', mode='eval').body
            if (name == 'mouse637-sidebar-focus-evidence.py'
                    and ast.unparse(node) == 'shell.get(kind) == toolbar'):
                return ast.parse("all(shell.get(kind, {}).get(key) == toolbar.get(key) for key in ('backgroundColor', 'backgroundImage'))", mode='eval').body
            return node

        def visit_Call(self, node):
            node = self.generic_visit(node)
            if (name == 'mouse633-owner-feedback-evidence.py'
                    and ast.dump(node) == ast.dump(ast.parse("all(row.get('hidden') is False for row in initial['sections'])", mode='eval').body)):
                changed['settings_overview'] += 1
                return ast.parse("initial.get('selectedPage') == 'overview' and [row.get('name') for row in initial['sections'] if row.get('hidden') is False] == ['privacy', 'overview-links'] and initial.get('navigation') == ['overview', 'appearance', 'workspace', 'privacy', 'imports', 'capture', 'downloads', 'documents', 'about']", mode='eval').body
            return node

        def visit_Constant(self, node):
            if not isinstance(node.value, str):
                return node
            value = node.value.replace('6.0.39', '6.0.40')
            for old, new in MODULES.items():
                value = value.replace(old, new)
            value = value.replace('mouse639-release', 'mouse640-release').replace('mouse639-linux-release', 'mouse640-linux-release').replace('mouse639-windows-release', 'mouse640-windows-release')
            value = value.replace('publish-mouse639', 'publish-mouse640').replace('MOUSE639_', 'MOUSE640_')
            for old, new in (
                ('MOUSE_639_REAL_638_TO_639_', 'MOUSE_640_REAL_639_TO_640_'),
                ('MOUSE_639_REAL_629_TO_639_', 'MOUSE_640_REAL_629_TO_640_'),
                ('MOUSE_639_WINDOWS_REAL_629_TO_639_', 'MOUSE_640_WINDOWS_REAL_629_TO_640_'),
                ('real-638-to-639-', 'real-639-to-640-'),
                ('real-629-to-639-', 'real-629-to-640-'),
                ('real-published-predecessor-to-639-', 'real-published-predecessor-to-640-'),
            ):
                value = value.replace(old, new)
            if name in PREDECESSOR_MODULES:
                value = value.replace('6.0.38', '6.0.39').replace('legacy638-update', 'legacy639-update').replace('updateFrom638', 'updateFrom639')
                value = value.replace('b9d243dd7507da3c5b5397c62391315c09794db8', PUBLISHED_SOURCE)
                value = value.replace('MOUSE_639_ACTUAL_638_UPDATER_', 'MOUSE_640_ACTUAL_639_UPDATER_')
                if value == '638':
                    value = '639'
            # The baseline is read with the actual published639 task reader.
            if name == 'mouse637-performance-evidence.py' and node.value == 'mouse638-task-evidence.py':
                value = 'mouse639-task-evidence.py'
            if name == 'mouse637-current.py':
                if value == 'MOUSE_639_REAL_':
                    value = 'MOUSE_640_REAL_'
                elif value == '_TO_639_PROFILE_PASS':
                    value = '_TO_640_PROFILE_PASS'
            if name == 'mouse637-sidebar-focus-evidence.py' and value == 'darkToolbarSurface':
                value = 'darkLibraryToolbarSurface'
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
            if replacement is not None:
                node.value = ast.parse(repr(replacement), mode='eval').body
            return node

    tree = Identity().visit(tree)
    required = {'mouse637-features-evidence.py': 'input_budget',
                'mouse633-owner-feedback-evidence.py': 'settings_overview'}.get(name)
    if required is not None and changed[required] != 1:
        raise ValueError('Current640 Settings adaptation did not bind its frozen predicate: ' + required)
    return ast.fix_missing_locations(tree)


def load(name, *, namespace=None, current_native=False):
    scope = namespace if namespace is not None else {}
    original = scope.get('__name__')
    scope['__file__'] = str(TOOLS / ('mouse640-native-evidence.py' if current_native else target(name)))
    scope['__name__'] = 'retained640_' + name.replace('-', '_')
    if name == 'mouse632-release.py':
        def verify_mode_requests(facts, output):
            return runpy.run_path(str(TOOLS / 'mouse640-presets-evidence.py'))['verify_legacy_facts'](facts, output)
        scope['_mouse637_verify_mode_requests'] = verify_mode_requests
    if name == 'mouse633-owner-feedback-evidence.py':
        scope['_mouse637_zoom_color'] = runpy.run_path(str(TOOLS / 'mouse640-zoom-evidence.py'))['expected_rgb']
    try:
        exec(compile(adapted_tree(name, current_native=current_native), scope['__file__'], 'exec'), scope)
    finally:
        if original is not None:
            scope['__name__'] = original
    return scope


def execute(name, scope):
    tree = adapted_tree(name)
    exec(compile(tree, scope['__file__'], 'exec'), scope)
