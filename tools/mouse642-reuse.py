#!/usr/bin/env python3
"""Retain byte-frozen641 gates while advancing current identity to642.

The accepted641 tools, pins and packages remain immutable. This adapter only
advances current/replacement identities. The 642 workspace reader independently
checks the requested same-site navigation and saved-grid restoration evidence.
"""
import ast
import hashlib
import json
from pathlib import Path
import runpy

TOOLS = Path(__file__).resolve().parent
FROZEN = json.loads((TOOLS / 'mouse642-frozen.json').read_text())
MODULES = {name: name.replace('mouse641-', 'mouse642-').replace('test_mouse641_', 'test_mouse642_')
           for name in FROZEN}
PUBLISHED_SOURCE = '3a32e02a8893b4c2f1397cd0a08e94af737f42fc'
PUBLISHED_UPDATER = '91ab363f926774825caf8055b2d3d81bf0d51264'
PUBLISHED_PINS = {
    'arm64': '6835f6ffda369a2ef6c2f1facac41d37aa7e9372023f366f47e3072a2ae9b738',
    'linux-x64': 'c1465c0733d785f7cb614c7102aa9c7cc8d7ad3ddddf5c0bc513cc354a3aa3e1',
    'windows-x64': '4dfd53b78f2ab318cef5f1932ae87bd3ae72b6444103bcfa73688aed3a368c8b',
}


def checked(name):
    if name not in FROZEN:
        raise ValueError('Unreviewed642 predecessor dependency: ' + name)
    raw = (TOOLS / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
        raise ValueError('Immutable642 predecessor dependency changed: ' + name)
    return raw


def legacy():
    checked('mouse641-reuse.py')
    checked('mouse641-frozen.json')
    return runpy.run_path(str(TOOLS / 'mouse641-reuse.py'))


def verify_frozen():
    for name in FROZEN:
        checked(name)
    legacy()['verify_frozen']()


def previous(platform):
    folder = {'darwin': 'arm64', 'linux': 'linux-x64', 'win32': 'windows-x64'}[platform]
    raw = (TOOLS.parent / 'staging/mouse' / ('6.0.41-' + folder) / 'pin.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != PUBLISHED_PINS[folder]:
        raise ValueError('Immutable641 predecessor pin bytes changed: ' + folder)
    value = json.loads(raw)
    if value.get('version') != '6.0.41' or value.get('source') != PUBLISHED_SOURCE or value.get('ready') is not True:
        raise ValueError('Immutable641 predecessor identity changed')
    return {'version': '6.0.41', 'source': PUBLISHED_SOURCE, 'updaterBlobSHA': PUBLISHED_UPDATER,
            **{key: value[key] for key in ('packages', 'package') if key in value}}


def baselines():
    def package(platform, name, tag):
        old = previous(platform)
        data = old.get('packages', {}).get(name) or old.get('package')
        return {'name': name, 'tag': tag, 'size': data['size'], 'sha256': data['sha256']}
    return {
        'darwin': package('darwin', 'Mouse-Browser-6.0.41-mac-arm64.dmg', 'quadro-macos-v6.0.41-arm64'),
        'win32': package('win32', 'Mouse-Browser-6.0.41-Windows-x64.exe', 'mouse-windows-v6.0.41-x64'),
        'linux': {fmt: package('linux', 'Mouse-Browser-6.0.41-Linux-x64.' + suffix, 'mouse-linux-v6.0.41-x64')
                  for fmt, suffix in (('appimage', 'AppImage'), ('deb', 'deb'))},
    }


def target(name):
    if name in MODULES:
        return MODULES[name]
    old = legacy()['target'](name)
    if old not in MODULES:
        raise ValueError('Unreviewed642 legacy target: ' + name)
    return MODULES[old]


PREDECESSOR_MODULES = {'mouse637-current.py', 'mouse637-upgrade-evidence.py',
    'mouse637-update-button-evidence.py', 'mouse637-performance-evidence.py',
    'mouse637-public-channel.py', 'mouse637-windows-display-evidence.py',
    'mouse634-linux-release.py', 'mouse633-linux-evidence.py'}
SETTINGS_SECTIONS = legacy()['SETTINGS_SECTIONS']
SETTINGS_PAGES = legacy()['SETTINGS_PAGES']


def contracts():
    return runpy.run_path(str(TOOLS / 'mouse642-owner-contracts.py'))


def adapted_tree(name, *, current_native=False):
    tree = ast.parse(checked(name), filename=str(TOOLS / name)) if name in FROZEN else legacy()['adapted_tree'](name, current_native=current_native)
    origin_changes = 0
    if name == 'mouse637-library-evidence.py':
        # 642 preserves the accepted641 geometry exactly, including its 1px
        # tolerance in the unchanged caller. Bind the inherited AST as well as
        # the byte-frozen dependency so a missing/duplicate adapter cannot pass.
        expected = ast.parse("""
def _placeholder_size(row, view):
    image, box = row['image'], row['row']
    if view == 'grid': return abs(image['height'] - 112) <= 1
    if view != 'list': return False
    return all(abs(actual - expected) <= 1 for actual, expected in (
        (image['x'], box['x'] + 10), (image['y'], box['y'] + 11),
        (image['width'], box['width'] - 46), (image['height'], 108), (box['height'], 130)))
""").body[0]
        actual = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_placeholder_size']
        if len(actual) != 1 or ast.dump(actual[0], include_attributes=False) != ast.dump(expected, include_attributes=False):
            raise ValueError('Frozen641 library geometry predicate changed')

    class Identity(ast.NodeTransformer):
        def visit_Call(self, node):
            nonlocal origin_changes
            node = self.generic_visit(node)
            replacements = {
                ('mouse637-features-evidence.py', 'AI preview needs two distinct owned origins'):
                    "isinstance(chat_origin, str) and isinstance(preview_origin, str) and re.fullmatch(r'http://127\\.0\\.0\\.1:\\d+', chat_origin) and re.fullmatch(r'http://localhost:\\d+', preview_origin)",
                ('mouse636-retained-owner-evidence.py', 'two owned cross-origin fixtures required'):
                    "isinstance(origins, list) and len(origins) == 2 and all(isinstance(o, str) for o in origins) and re.fullmatch(r'http://127\\.0\\.0\\.1:\\d+', origins[0]) and re.fullmatch(r'http://localhost:\\d+', origins[1])",
                ('mouse634-download-evidence.py', 'both caller-bound download origins required'):
                    "isinstance(origins, (list, tuple)) and len(origins) == 2 and all(isinstance(o, str) and re.fullmatch(r'http://(?:127\\.0\\.0\\.1|localhost):\\d+', o) for o in origins)",
            }
            if len(node.args) == 2 and isinstance(node.args[1], ast.Constant):
                replacement = replacements.get((name, node.args[1].value))
                if replacement is not None:
                    if not any(isinstance(part, ast.Constant) and part.value == r'http://127\.0\.0\.1:\d+' for part in ast.walk(node.args[0])):
                        raise ValueError('Frozen loopback origin predicate changed: ' + name)
                    node.args[0] = ast.parse(replacement, mode='eval').body
                    origin_changes += 1
            return node

        def visit_Constant(self, node):
            if not isinstance(node.value, str):
                return node
            value = node.value.replace('6.0.41', '6.0.42')
            for old, new in MODULES.items():
                value = value.replace(old, new)
            value = value.replace('mouse641-release', 'mouse642-release').replace('mouse641-linux-release', 'mouse642-linux-release').replace('mouse641-windows-release', 'mouse642-windows-release')
            value = value.replace('publish-mouse641', 'publish-mouse642').replace('MOUSE641_', 'MOUSE642_')
            for old, new in (
                ('MOUSE_641_REAL_640_TO_641_', 'MOUSE_642_REAL_641_TO_642_'),
                ('MOUSE_641_REAL_629_TO_641_', 'MOUSE_642_REAL_629_TO_642_'),
                ('MOUSE_641_WINDOWS_REAL_629_TO_641_', 'MOUSE_642_WINDOWS_REAL_629_TO_642_'),
                ('real-640-to-641-', 'real-641-to-642-'),
                ('real-629-to-641-', 'real-629-to-642-'),
                ('real-published-predecessor-to-641-', 'real-published-predecessor-to-642-'),
            ):
                value = value.replace(old, new)
            if name in PREDECESSOR_MODULES:
                value = value.replace('6.0.40', '6.0.41').replace('legacy640-update', 'legacy641-update')
                value = value.replace('7428ecf52698e62468bb7befb9d7d2d06ee7b6d9', PUBLISHED_SOURCE)
                value = value.replace('MOUSE_641_ACTUAL_640_UPDATER_', 'MOUSE_642_ACTUAL_641_UPDATER_')
                if value == '640':
                    value = '641'
            if name == 'mouse637-performance-evidence.py' and node.value == 'mouse640-task-evidence.py':
                value = 'mouse641-task-evidence.py'
            if name == 'mouse637-current.py':
                if value == 'MOUSE_641_REAL_':
                    value = 'MOUSE_642_REAL_'
                elif value == '_TO_641_PROFILE_PASS':
                    value = '_TO_642_PROFILE_PASS'
            return ast.copy_location(ast.Constant(value=value), node) if value != node.value else node

        def visit_Assign(self, node):
            node = self.generic_visit(node)
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if name == 'mouse637-upgrade-evidence.py' and 'BASELINES' in names:
                node.value = ast.parse(repr(baselines()), mode='eval').body
            if name == 'mouse634-linux-release.py' and 'PREVIOUS' in names:
                node.value = ast.parse(repr(previous('linux')), mode='eval').body
            return node

    tree = Identity().visit(tree)
    expected = int(name in {'mouse637-features-evidence.py', 'mouse636-retained-owner-evidence.py', 'mouse634-download-evidence.py'})
    if origin_changes != expected:
        raise ValueError('642 owned fixture adaptation did not bind its exact frozen predicate: ' + name)
    return ast.fix_missing_locations(tree)


def prepare_scope(scope):
    # The retained641 AST calls this historical hook; it must read642 receipts.
    scope['_mouse641_contracts'] = contracts
    scope['_mouse642_contracts'] = contracts


def load(name, *, namespace=None, current_native=False):
    scope = namespace if namespace is not None else {}
    original = scope.get('__name__')
    scope['__file__'] = str(TOOLS / ('mouse642-native-evidence.py' if current_native else target(name)))
    scope['__name__'] = 'retained642_' + name.replace('-', '_')
    prepare_scope(scope)
    if name == 'mouse632-release.py':
        def verify_mode_requests(facts, output):
            return runpy.run_path(str(TOOLS / 'mouse642-presets-evidence.py'))['verify_legacy_facts'](facts, output)
        scope['_mouse637_verify_mode_requests'] = verify_mode_requests
    if name == 'mouse633-owner-feedback-evidence.py':
        scope['_mouse637_zoom_color'] = runpy.run_path(str(TOOLS / 'mouse642-zoom-evidence.py'))['expected_rgb']
    try:
        exec(compile(adapted_tree(name, current_native=current_native), scope['__file__'], 'exec'), scope)
    finally:
        if original is not None:
            scope['__name__'] = original
    return scope


def execute(name, scope):
    prepare_scope(scope)
    exec(compile(adapted_tree(name), scope['__file__'], 'exec'), scope)
