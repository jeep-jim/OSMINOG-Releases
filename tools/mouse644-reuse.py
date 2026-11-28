#!/usr/bin/env python3
"""Mac644 identity over byte-frozen643 acceptance; no new platform publisher."""
import ast
import hashlib
import json
from pathlib import Path
import runpy

TOOLS = Path(__file__).resolve().parent
FROZEN = json.loads((TOOLS / 'mouse644-frozen.json').read_text())
RETAINED_PLATFORM_MODULES = {'mouse642-linux-release.py', 'mouse642-linux-evidence.py',
                             'mouse642-windows-release.py', 'mouse642-windows-display-evidence.py'}
MODULES = {name: name if name in RETAINED_PLATFORM_MODULES else
           name.replace('mouse643-', 'mouse644-').replace('test_mouse643_', 'test_mouse644_')
           for name in FROZEN}
PUBLISHED_SOURCE = '926ad99ffa36e15068b713d110c127e1fa22565e'
PUBLISHED_UPDATER = '91ab363f926774825caf8055b2d3d81bf0d51264'
PUBLISHED_PIN_SHA256 = 'f9658021e1cbb437ae53e4e3a0bbcbf72436da750be05ec6d6e62e4e08515a75'


def checked(name):
    if name not in FROZEN:
        raise ValueError('Unreviewed644 predecessor dependency: ' + name)
    raw = (TOOLS / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
        raise ValueError('Immutable643 predecessor dependency changed: ' + name)
    return raw


def legacy():
    checked('mouse643-reuse.py')
    checked('mouse643-frozen.json')
    return runpy.run_path(str(TOOLS / 'mouse643-reuse.py'))


def verify_frozen():
    for name in FROZEN:
        checked(name)
    legacy()['verify_frozen']()


def previous(platform):
    if platform != 'darwin':
        raise ValueError('Mouse644 is authorized for macOS arm64 only')
    raw = (TOOLS.parent / 'staging/mouse/6.0.43-arm64/pin.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != PUBLISHED_PIN_SHA256:
        raise ValueError('Immutable643 Mac predecessor pin bytes changed')
    value = json.loads(raw)
    if value.get('version') != '6.0.43' or value.get('source') != PUBLISHED_SOURCE or value.get('ready') is not True:
        raise ValueError('Immutable643 Mac predecessor identity changed')
    return {'version': '6.0.43', 'source': PUBLISHED_SOURCE, 'updaterBlobSHA': PUBLISHED_UPDATER,
            'packages': value['packages']}


def baselines():
    name = 'Mouse-Browser-6.0.43-mac-arm64.dmg'
    package = previous('darwin')['packages'][name]
    return {'darwin': {'name': name, 'tag': 'quadro-macos-v6.0.43-arm64', **package}}


def target(name):
    if name in MODULES:
        return MODULES[name]
    old = legacy()['target'](name)
    if old not in MODULES:
        raise ValueError('Unreviewed644 legacy target: ' + name)
    return MODULES[old]


PREDECESSOR_MODULES = {'mouse637-current.py', 'mouse637-upgrade-evidence.py',
    'mouse637-update-button-evidence.py', 'mouse637-performance-evidence.py', 'mouse637-public-channel.py'}
SETTINGS_SECTIONS = legacy()['SETTINGS_SECTIONS']
SETTINGS_PAGES = legacy()['SETTINGS_PAGES']


def contracts():
    return runpy.run_path(str(TOOLS / 'mouse644-owner-contracts.py'))


def adapted_tree(name, *, current_native=False):
    tree = ast.parse(checked(name), filename=str(TOOLS / name)) if name in FROZEN else legacy()['adapted_tree'](name, current_native=current_native)

    class Identity(ast.NodeTransformer):
        def visit_Constant(self, node):
            if not isinstance(node.value, str):
                return node
            value = node.value.replace('6.0.43', '6.0.44')
            for old, new in MODULES.items():
                value = value.replace(old, new)
            value = value.replace('mouse643-release', 'mouse644-release').replace('publish-mouse643', 'publish-mouse644').replace('MOUSE643_', 'MOUSE644_')
            for old, new in (
                ('MOUSE_643_REAL_642_TO_643_', 'MOUSE_644_REAL_643_TO_644_'),
                ('MOUSE_643_REAL_629_TO_643_', 'MOUSE_644_REAL_629_TO_644_'),
                ('real-642-to-643-', 'real-643-to-644-'),
                ('real-629-to-643-', 'real-629-to-644-'),
                ('real-published-predecessor-to-643-', 'real-published-predecessor-to-644-'),
            ):
                value = value.replace(old, new)
            if name in PREDECESSOR_MODULES:
                value = value.replace('6.0.42', '6.0.43').replace('legacy642-update', 'legacy643-update')
                value = value.replace('ac51d80d4190bce54d8cc5f7017359dcb8fa838c', PUBLISHED_SOURCE)
                value = value.replace('MOUSE_643_ACTUAL_642_UPDATER_', 'MOUSE_644_ACTUAL_643_UPDATER_')
                if value == '642':
                    value = '643'
            if name == 'mouse637-performance-evidence.py' and node.value == 'mouse642-task-evidence.py':
                value = 'mouse643-task-evidence.py'
            if name == 'mouse637-current.py':
                if value == 'MOUSE_643_REAL_':
                    value = 'MOUSE_644_REAL_'
                elif value == '_TO_643_PROFILE_PASS':
                    value = '_TO_644_PROFILE_PASS'
            return ast.copy_location(ast.Constant(value=value), node) if value != node.value else node

        def visit_Assign(self, node):
            node = self.generic_visit(node)
            names = [item.id for item in node.targets if isinstance(item, ast.Name)]
            if name == 'mouse637-upgrade-evidence.py' and 'BASELINES' in names:
                node.value = ast.parse(repr(baselines()), mode='eval').body
            return node

    return ast.fix_missing_locations(Identity().visit(tree))


def prepare_scope(scope):
    scope['_mouse641_contracts'] = contracts
    scope['_mouse642_contracts'] = contracts
    scope['_mouse643_contracts'] = contracts
    scope['_mouse644_contracts'] = contracts


def load(name, *, namespace=None, current_native=False):
    scope = namespace if namespace is not None else {}
    original = scope.get('__name__')
    scope['__file__'] = str(TOOLS / ('mouse644-native-evidence.py' if current_native else target(name)))
    scope['__name__'] = 'retained644_' + name.replace('-', '_')
    prepare_scope(scope)
    if name == 'mouse632-release.py':
        def verify_mode_requests(facts, output):
            return runpy.run_path(str(TOOLS / 'mouse644-presets-evidence.py'))['verify_legacy_facts'](facts, output)
        scope['_mouse637_verify_mode_requests'] = verify_mode_requests
    if name == 'mouse633-owner-feedback-evidence.py':
        scope['_mouse637_zoom_color'] = runpy.run_path(str(TOOLS / 'mouse644-zoom-evidence.py'))['expected_rgb']
    try:
        exec(compile(adapted_tree(name, current_native=current_native), scope['__file__'], 'exec'), scope)
    finally:
        if original is not None:
            scope['__name__'] = original
    return scope


def execute(name, scope):
    prepare_scope(scope)
    exec(compile(adapted_tree(name), scope['__file__'], 'exec'), scope)
