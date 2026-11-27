#!/usr/bin/env python3
"""Mac643 identity over byte-frozen642 acceptance; no new platform publisher."""
import ast
import hashlib
import json
from pathlib import Path
import runpy

TOOLS = Path(__file__).resolve().parent
FROZEN = json.loads((TOOLS / 'mouse643-frozen.json').read_text())
RETAINED_PLATFORM_MODULES = {'mouse642-linux-release.py', 'mouse642-linux-evidence.py',
                             'mouse642-windows-release.py', 'mouse642-windows-display-evidence.py'}
MODULES = {name: name if name in RETAINED_PLATFORM_MODULES else
           name.replace('mouse642-', 'mouse643-').replace('test_mouse642_', 'test_mouse643_')
           for name in FROZEN}
PUBLISHED_SOURCE = 'ac51d80d4190bce54d8cc5f7017359dcb8fa838c'
PUBLISHED_UPDATER = '91ab363f926774825caf8055b2d3d81bf0d51264'
PUBLISHED_PIN_SHA256 = '35f7d8b77f576be3145df43898de28ad4d5c6f75daf37d2687b4c37cafa62668'


def checked(name):
    if name not in FROZEN:
        raise ValueError('Unreviewed643 predecessor dependency: ' + name)
    raw = (TOOLS / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
        raise ValueError('Immutable642 predecessor dependency changed: ' + name)
    return raw


def legacy():
    checked('mouse642-reuse.py')
    checked('mouse642-frozen.json')
    return runpy.run_path(str(TOOLS / 'mouse642-reuse.py'))


def verify_frozen():
    for name in FROZEN:
        checked(name)
    legacy()['verify_frozen']()


def previous(platform):
    if platform != 'darwin':
        raise ValueError('Mouse643 is authorized for macOS arm64 only')
    raw = (TOOLS.parent / 'staging/mouse/6.0.42-arm64/pin.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != PUBLISHED_PIN_SHA256:
        raise ValueError('Immutable642 Mac predecessor pin bytes changed')
    value = json.loads(raw)
    if value.get('version') != '6.0.42' or value.get('source') != PUBLISHED_SOURCE or value.get('ready') is not True:
        raise ValueError('Immutable642 Mac predecessor identity changed')
    return {'version': '6.0.42', 'source': PUBLISHED_SOURCE, 'updaterBlobSHA': PUBLISHED_UPDATER,
            'packages': value['packages']}


def baselines():
    name = 'Mouse-Browser-6.0.42-mac-arm64.dmg'
    package = previous('darwin')['packages'][name]
    return {'darwin': {'name': name, 'tag': 'quadro-macos-v6.0.42-arm64', **package}}


def target(name):
    if name in MODULES:
        return MODULES[name]
    old = legacy()['target'](name)
    if old not in MODULES:
        raise ValueError('Unreviewed643 legacy target: ' + name)
    return MODULES[old]


PREDECESSOR_MODULES = {'mouse637-current.py', 'mouse637-upgrade-evidence.py',
    'mouse637-update-button-evidence.py', 'mouse637-performance-evidence.py', 'mouse637-public-channel.py'}
SETTINGS_SECTIONS = legacy()['SETTINGS_SECTIONS']
SETTINGS_PAGES = legacy()['SETTINGS_PAGES']


def contracts():
    return runpy.run_path(str(TOOLS / 'mouse643-owner-contracts.py'))


def adapted_tree(name, *, current_native=False):
    tree = ast.parse(checked(name), filename=str(TOOLS / name)) if name in FROZEN else legacy()['adapted_tree'](name, current_native=current_native)

    class Identity(ast.NodeTransformer):
        def visit_Constant(self, node):
            if not isinstance(node.value, str):
                return node
            value = node.value.replace('6.0.42', '6.0.43')
            for old, new in MODULES.items():
                value = value.replace(old, new)
            value = value.replace('mouse642-release', 'mouse643-release').replace('publish-mouse642', 'publish-mouse643').replace('MOUSE642_', 'MOUSE643_')
            for old, new in (
                ('MOUSE_642_REAL_641_TO_642_', 'MOUSE_643_REAL_642_TO_643_'),
                ('MOUSE_642_REAL_629_TO_642_', 'MOUSE_643_REAL_629_TO_643_'),
                ('real-641-to-642-', 'real-642-to-643-'),
                ('real-629-to-642-', 'real-629-to-643-'),
                ('real-published-predecessor-to-642-', 'real-published-predecessor-to-643-'),
                ('MOUSE_628_ACTIVE_TAB_FLOW_BORDERLESS_BOTH_THEMES_PASS', 'MOUSE_643_ACTIVE_TAB_BOX_BOTH_THEMES_PASS'),
                ('active-tab-flow-borderless-both-themes', 'active-tab-box-both-themes'),
            ):
                value = value.replace(old, new)
            if name in PREDECESSOR_MODULES:
                value = value.replace('6.0.41', '6.0.42').replace('legacy641-update', 'legacy642-update')
                value = value.replace('3a32e02a8893b4c2f1397cd0a08e94af737f42fc', PUBLISHED_SOURCE)
                value = value.replace('MOUSE_642_ACTUAL_641_UPDATER_', 'MOUSE_643_ACTUAL_642_UPDATER_')
                if value == '641':
                    value = '642'
            if name == 'mouse637-performance-evidence.py' and node.value == 'mouse641-task-evidence.py':
                value = 'mouse642-task-evidence.py'
            if name == 'mouse637-current.py':
                if value == 'MOUSE_642_REAL_':
                    value = 'MOUSE_643_REAL_'
                elif value == '_TO_642_PROFILE_PASS':
                    value = '_TO_643_PROFILE_PASS'
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


def load(name, *, namespace=None, current_native=False):
    scope = namespace if namespace is not None else {}
    original = scope.get('__name__')
    scope['__file__'] = str(TOOLS / ('mouse643-native-evidence.py' if current_native else target(name)))
    scope['__name__'] = 'retained643_' + name.replace('-', '_')
    prepare_scope(scope)
    if name == 'mouse632-release.py':
        def verify_mode_requests(facts, output):
            return runpy.run_path(str(TOOLS / 'mouse643-presets-evidence.py'))['verify_legacy_facts'](facts, output)
        scope['_mouse637_verify_mode_requests'] = verify_mode_requests
    if name == 'mouse633-owner-feedback-evidence.py':
        scope['_mouse637_zoom_color'] = runpy.run_path(str(TOOLS / 'mouse643-zoom-evidence.py'))['expected_rgb']
    try:
        exec(compile(adapted_tree(name, current_native=current_native), scope['__file__'], 'exec'), scope)
    finally:
        if original is not None:
            scope['__name__'] = original
    return scope


def execute(name, scope):
    prepare_scope(scope)
    exec(compile(adapted_tree(name), scope['__file__'], 'exec'), scope)
