#!/usr/bin/env python3
"""Retain byte-frozen638 gates with current639 and published638 identities.

The638 adapter still owns all reviewed layout, rendering and retained feature
predicates. This layer changes only the current identity, exact predecessor
packages and publisher paths. Archived code, pins and evidence are never edited.
"""
import ast
import hashlib
import json
from pathlib import Path
import runpy

TOOLS = Path(__file__).resolve().parent
FROZEN = json.loads((TOOLS / 'mouse639-frozen.json').read_text())
MODULES = {name: name.replace('mouse638-', 'mouse639-').replace('test_mouse638_', 'test_mouse639_')
           for name in FROZEN}
PUBLISHED_SOURCE = 'b9d243dd7507da3c5b5397c62391315c09794db8'
PUBLISHED_UPDATER = '91ab363f926774825caf8055b2d3d81bf0d51264'
PUBLISHED_PINS = {'arm64': '98eae8554a30c09eed95ad71e81a3ee24e6aa6188f984d7251620c21031b6daa', 'linux-x64': 'b4f42cd2d246c93b8ac5f948e88290b95242e02be6e912e0f1ccd5594afdc17d', 'windows-x64': '08512a15c003a5038e2eb1b8ce31290a681f3e9e492e3c9d81acf6b12fb3809e'}


def checked(name):
    if name not in FROZEN:
        raise ValueError('Unreviewed639 predecessor dependency: ' + name)
    raw = (TOOLS / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
        raise ValueError('Immutable639 predecessor dependency changed: ' + name)
    return raw


def verify_frozen():
    for name in FROZEN:
        checked(name)


def previous(platform):
    folder = {'darwin': 'arm64', 'linux': 'linux-x64', 'win32': 'windows-x64'}[platform]
    raw = (TOOLS.parent / 'staging/mouse' / ('6.0.38-' + folder) / 'pin.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != PUBLISHED_PINS[folder]:
        raise ValueError('Immutable published638 pin bytes changed: ' + folder)
    value = json.loads(raw)
    if value.get('version') != '6.0.38' or value.get('source') != PUBLISHED_SOURCE or value.get('ready') is not True:
        raise ValueError('Immutable published638 predecessor changed')
    return {'version': '6.0.38', 'source': PUBLISHED_SOURCE, 'updaterBlobSHA': PUBLISHED_UPDATER,
            **{key: value[key] for key in ('packages', 'package') if key in value}}


def baselines():
    def package(platform, name, tag):
        old = previous(platform)
        data = old.get('packages', {}).get(name) or old.get('package')
        return {'name': name, 'tag': tag, 'size': data['size'], 'sha256': data['sha256']}
    return {'darwin': package('darwin', 'Mouse-Browser-6.0.38-mac-arm64.dmg', 'quadro-macos-v6.0.38-arm64'),
            'win32': package('win32', 'Mouse-Browser-6.0.38-Windows-x64.exe', 'mouse-windows-v6.0.38-x64'),
            'linux': {fmt: package('linux', 'Mouse-Browser-6.0.38-Linux-x64.' + suffix, 'mouse-linux-v6.0.38-x64')
                      for fmt, suffix in (('appimage', 'AppImage'), ('deb', 'deb'))}}


def legacy():
    checked('mouse638-reuse.py')
    checked('mouse638-frozen.json')
    checked('mouse638-task-evidence.py')
    return runpy.run_path(str(TOOLS / 'mouse638-reuse.py'))


def target(name):
    if name in MODULES:
        return MODULES[name]
    old = legacy()['target'](name)
    if old not in MODULES:
        raise ValueError('Unreviewed639 legacy target: ' + name)
    return MODULES[old]


PREDECESSOR_MODULES = {'mouse637-current.py', 'mouse637-upgrade-evidence.py',
    'mouse637-update-button-evidence.py', 'mouse637-performance-evidence.py',
    'mouse637-public-channel.py', 'mouse637-windows-display-evidence.py',
    'mouse634-linux-release.py', 'mouse633-linux-evidence.py'}


def adapted_tree(name, *, current_native=False):
    tree = ast.parse(checked(name), filename=str(TOOLS / name)) if name in FROZEN else legacy()['adapted_tree'](name, current_native=current_native)

    class Identity(ast.NodeTransformer):
        def visit_Constant(self, node):
            if not isinstance(node.value, str):
                return node
            value = node.value.replace('6.0.38', '6.0.39')
            for old, new in MODULES.items():
                value = value.replace(old, new)
            value = value.replace('mouse638-release', 'mouse639-release').replace('mouse638-linux-release', 'mouse639-linux-release').replace('mouse638-windows-release', 'mouse639-windows-release')
            value = value.replace('publish-mouse638', 'publish-mouse639').replace('MOUSE638_', 'MOUSE639_')
            for old, new in (
                ('MOUSE_638_REAL_637_TO_638_', 'MOUSE_639_REAL_638_TO_639_'),
                ('MOUSE_638_REAL_629_TO_638_', 'MOUSE_639_REAL_629_TO_639_'),
                ('MOUSE_638_WINDOWS_REAL_629_TO_638_', 'MOUSE_639_WINDOWS_REAL_629_TO_639_'),
                ('real-637-to-638-', 'real-638-to-639-'),
                ('real-629-to-638-', 'real-629-to-639-'),
                ('real-published-predecessor-to-638-', 'real-published-predecessor-to-639-'),
            ):
                value = value.replace(old, new)
            if name in PREDECESSOR_MODULES:
                value = value.replace('6.0.37', '6.0.38').replace('legacy637-update', 'legacy638-update').replace('updateFrom637', 'updateFrom638')
                value = value.replace('0021084ccb9537e657d21e6f0c8e812dee6b461f', PUBLISHED_SOURCE)
                value = value.replace('MOUSE_638_ACTUAL_637_UPDATER_', 'MOUSE_639_ACTUAL_638_UPDATER_')
                if value == '637':
                    value = '638'
            # Compare against the exact public638 raw task reader, not a639 copy.
            if name == 'mouse637-performance-evidence.py' and node.value == 'mouse637-task-evidence.py':
                value = 'mouse638-task-evidence.py'
            if name == 'mouse637-current.py':
                if value == 'MOUSE_638_REAL_':
                    value = 'MOUSE_639_REAL_'
                elif value == '_TO_638_PROFILE_PASS':
                    value = '_TO_639_PROFILE_PASS'
            return ast.copy_location(ast.Constant(value=value), node) if value != node.value else node

        def visit_Assign(self, node):
            node = self.generic_visit(node)
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            replacement = None
            if name == 'mouse637-upgrade-evidence.py' and 'BASELINES' in names:
                replacement = baselines()
            if name == 'mouse634-linux-release.py' and 'PREVIOUS' in names:
                replacement = previous('linux')
            if replacement is not None:
                node.value = ast.parse(repr(replacement), mode='eval').body
            return node

    return ast.fix_missing_locations(Identity().visit(tree))


def load(name, *, namespace=None, current_native=False):
    scope = namespace if namespace is not None else {}
    original = scope.get('__name__')
    scope['__file__'] = str(TOOLS / ('mouse639-native-evidence.py' if current_native else target(name)))
    scope['__name__'] = 'retained639_' + name.replace('-', '_')
    if name == 'mouse632-release.py':
        def verify_mode_requests(facts, output):
            return runpy.run_path(str(TOOLS / 'mouse639-presets-evidence.py'))['verify_legacy_facts'](facts, output)
        scope['_mouse637_verify_mode_requests'] = verify_mode_requests
    if name == 'mouse633-owner-feedback-evidence.py':
        scope['_mouse637_zoom_color'] = runpy.run_path(str(TOOLS / 'mouse639-zoom-evidence.py'))['expected_rgb']
    try:
        exec(compile(adapted_tree(name, current_native=current_native), scope['__file__'], 'exec'), scope)
    finally:
        if original is not None:
            scope['__name__'] = original
    return scope


def execute(name, scope):
    tree = adapted_tree(name)
    exec(compile(tree, scope['__file__'], 'exec'), scope)
