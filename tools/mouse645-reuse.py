#!/usr/bin/env python3
"""Mac645 identity over byte-frozen644 acceptance; no new platform publisher."""
import ast
import hashlib
import json
from pathlib import Path
import runpy

TOOLS = Path(__file__).resolve().parent
FROZEN = json.loads((TOOLS / 'mouse645-frozen.json').read_text())
RETAINED_PLATFORM_MODULES = {'mouse642-linux-release.py', 'mouse642-linux-evidence.py',
                             'mouse642-windows-release.py', 'mouse642-windows-display-evidence.py'}
MODULES = {name: name if name in RETAINED_PLATFORM_MODULES else
           name.replace('mouse644-', 'mouse645-').replace('test_mouse644_', 'test_mouse645_')
           for name in FROZEN}
PUBLISHED_SOURCE = 'ad9b8c217da8917f95a2d672e62790f474daef4b'
PUBLISHED_UPDATER = '91ab363f926774825caf8055b2d3d81bf0d51264'
PUBLISHED_PIN_SHA256 = '95b24108aff260f781284b82db4b34900f63b26c705de6d3807389a4bb4aabbb'


def checked(name):
    if name not in FROZEN:
        raise ValueError('Unreviewed645 predecessor dependency: ' + name)
    raw = (TOOLS / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
        raise ValueError('Immutable644 predecessor dependency changed: ' + name)
    return raw


def legacy():
    checked('mouse644-reuse.py')
    checked('mouse644-frozen.json')
    return runpy.run_path(str(TOOLS / 'mouse644-reuse.py'))


def verify_frozen():
    for name in FROZEN:
        checked(name)
    legacy()['verify_frozen']()


def previous(platform):
    if platform != 'darwin':
        raise ValueError('Mouse645 is authorized for macOS arm64 only')
    raw = (TOOLS.parent / 'staging/mouse/6.0.44-arm64/pin.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != PUBLISHED_PIN_SHA256:
        raise ValueError('Immutable644 Mac predecessor pin bytes changed')
    value = json.loads(raw)
    if value.get('version') != '6.0.44' or value.get('source') != PUBLISHED_SOURCE or value.get('ready') is not True:
        raise ValueError('Immutable644 Mac predecessor identity changed')
    return {'version': '6.0.44', 'source': PUBLISHED_SOURCE, 'updaterBlobSHA': PUBLISHED_UPDATER,
            'packages': value['packages']}


def baselines():
    name = 'Mouse-Browser-6.0.44-mac-arm64.dmg'
    package = previous('darwin')['packages'][name]
    return {'darwin': {'name': name, 'tag': 'quadro-macos-v6.0.44-arm64', **package}}


def target(name):
    if name in MODULES:
        return MODULES[name]
    old = legacy()['target'](name)
    if old not in MODULES:
        raise ValueError('Unreviewed645 legacy target: ' + name)
    return MODULES[old]


PREDECESSOR_MODULES = {'mouse637-current.py', 'mouse637-upgrade-evidence.py',
    'mouse637-update-button-evidence.py', 'mouse637-performance-evidence.py', 'mouse637-public-channel.py'}
SETTINGS_SECTIONS = legacy()['SETTINGS_SECTIONS']
SETTINGS_TOGGLES = legacy()['SETTINGS_TOGGLES']
SETTINGS_PAGES = legacy()['SETTINGS_PAGES']


def contracts():
    return runpy.run_path(str(TOOLS / 'mouse645-owner-contracts.py'))


def adapted_tree(name, *, current_native=False):
    tree = ast.parse(checked(name), filename=str(TOOLS / name)) if name in FROZEN else legacy()['adapted_tree'](name, current_native=current_native)
    footer_changes = set()
    search_footer_changes = {}
    class Identity(ast.NodeTransformer):
        def visit_Compare(self, node):
            node = self.generic_visit(node)
            if name == 'mouse636-feedback-evidence.py':
                old = ast.parse("row.get('count') == 6", mode='eval').body
                if ast.dump(node) == ast.dump(old):
                    footer_changes.add('count')
                    return ast.copy_location(ast.parse("row.get('count') == 7", mode='eval').body, node)
            return node

        def visit_List(self, node):
            node = self.generic_visit(node)
            if name == 'mouse636-feedback-evidence.py':
                old = ast.parse("['emoji', 'zoom', 'history', 'bookmarks', 'downloads', 'screenshot']", mode='eval').body
                if ast.dump(node) == ast.dump(old):
                    footer_changes.add('actions')
                    return ast.copy_location(ast.parse("['emoji', 'zoom', 'history', 'bookmarks', 'downloads', 'flash', 'screenshot']", mode='eval').body, node)
            return node

        def visit_Constant(self, node):
            if not isinstance(node.value, str):
                return node
            value = node.value.replace('6.0.44', '6.0.45')
            if name == 'mouse636-feedback-evidence.py' and value == 'Эмодзи, масштаб, история, закладки, загрузки и скриншот':
                footer_changes.add('label')
                value = 'Эмодзи, масштаб, история, закладки, загрузки, Флэш и скриншот'
            if name == 'mouse636-search-removal-evidence.py':
                labels = {
                    'Эмодзи, масштаб, история, закладки, загрузки и скриншот':
                        ('ru', 'Эмодзи, масштаб, история, закладки, загрузки, Флэш и скриншот'),
                    'Emoji, zoom, history, bookmarks, downloads and screenshot':
                        ('en', 'Emoji, zoom, history, bookmarks, downloads, Flash and screenshot')}
                if value in labels:
                    key, value = labels[value]
                    search_footer_changes[key] = search_footer_changes.get(key, 0) + 1
            for old, new in MODULES.items():
                value = value.replace(old, new)
            value = value.replace('mouse644-release', 'mouse645-release').replace('publish-mouse644', 'publish-mouse645').replace('MOUSE644_', 'MOUSE645_')
            for old, new in (
                ('MOUSE_644_REAL_643_TO_644_', 'MOUSE_645_REAL_644_TO_645_'),
                ('MOUSE_644_REAL_629_TO_644_', 'MOUSE_645_REAL_629_TO_645_'),
                ('real-643-to-644-', 'real-644-to-645-'),
                ('real-629-to-644-', 'real-629-to-645-'),
                ('real-published-predecessor-to-644-', 'real-published-predecessor-to-645-'),
            ):
                value = value.replace(old, new)
            if name in PREDECESSOR_MODULES:
                value = value.replace('6.0.43', '6.0.44').replace('legacy643-update', 'legacy644-update')
                value = value.replace('926ad99ffa36e15068b713d110c127e1fa22565e', PUBLISHED_SOURCE)
                value = value.replace('MOUSE_644_ACTUAL_643_UPDATER_', 'MOUSE_645_ACTUAL_644_UPDATER_')
                if value == '643':
                    value = '644'
            if name == 'mouse637-performance-evidence.py' and node.value == 'mouse643-task-evidence.py':
                value = 'mouse644-task-evidence.py'
            if name == 'mouse637-current.py':
                if value == 'MOUSE_644_REAL_':
                    value = 'MOUSE_645_REAL_'
                elif value == '_TO_644_PROFILE_PASS':
                    value = '_TO_645_PROFILE_PASS'
            return ast.copy_location(ast.Constant(value=value), node) if value != node.value else node

        def visit_Assign(self, node):
            node = self.generic_visit(node)
            names = [item.id for item in node.targets if isinstance(item, ast.Name)]
            if name == 'mouse637-upgrade-evidence.py' and 'BASELINES' in names:
                node.value = ast.parse(repr(baselines()), mode='eval').body
            if name == 'mouse636-search-removal-evidence.py' and 'FOOTER' in names:
                if ast.literal_eval(node.value) != ['emoji', 'zoom', 'history', 'bookmarks', 'downloads', 'screenshot']:
                    raise ValueError('Frozen636 search-removal footer inventory changed')
                search_footer_changes['actions'] = search_footer_changes.get('actions', 0) + 1
                node.value = ast.parse("['emoji', 'zoom', 'history', 'bookmarks', 'downloads', 'flash', 'screenshot']", mode='eval').body
            return node

    tree = Identity().visit(tree)
    if name == 'mouse636-feedback-evidence.py' and footer_changes != {'count', 'actions', 'label'}:
        raise ValueError('The645 Flash footer adaptation did not bind the exact frozen controls')
    if name == 'mouse636-search-removal-evidence.py' and search_footer_changes != {'actions': 1, 'ru': 1, 'en': 1}:
        raise ValueError('The645 search-removal adapter did not bind the exact frozen footer and both labels')
    return ast.fix_missing_locations(tree)


def prepare_scope(scope):
    scope['_mouse641_contracts'] = contracts
    scope['_mouse642_contracts'] = contracts
    scope['_mouse643_contracts'] = contracts
    scope['_mouse644_contracts'] = contracts
    scope['_mouse645_contracts'] = contracts


def load(name, *, namespace=None, current_native=False):
    scope = namespace if namespace is not None else {}
    original = scope.get('__name__')
    scope['__file__'] = str(TOOLS / ('mouse645-native-evidence.py' if current_native else target(name)))
    scope['__name__'] = 'retained645_' + name.replace('-', '_')
    prepare_scope(scope)
    if name == 'mouse632-release.py':
        def verify_mode_requests(facts, output):
            return runpy.run_path(str(TOOLS / 'mouse645-presets-evidence.py'))['verify_legacy_facts'](facts, output)
        scope['_mouse637_verify_mode_requests'] = verify_mode_requests
    if name == 'mouse633-owner-feedback-evidence.py':
        scope['_mouse637_zoom_color'] = runpy.run_path(str(TOOLS / 'mouse645-zoom-evidence.py'))['expected_rgb']
    try:
        exec(compile(adapted_tree(name, current_native=current_native), scope['__file__'], 'exec'), scope)
    finally:
        if original is not None:
            scope['__name__'] = original
    return scope


def execute(name, scope):
    prepare_scope(scope)
    exec(compile(adapted_tree(name), scope['__file__'], 'exec'), scope)
