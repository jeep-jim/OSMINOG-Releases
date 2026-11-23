#!/usr/bin/env python3
"""Retain immutable637 acceptance with reviewed638 and published637 identities.

No archived code, evidence or package is rewritten. The retained source smoke
filenames and markers stay637 where the source intentionally retains them.
Only current product identity and actual predecessor-dependent contracts move.
"""
import ast
import hashlib
import json
from pathlib import Path
import runpy

TOOLS = Path(__file__).resolve().parent
FROZEN = json.loads((TOOLS / 'mouse638-frozen.json').read_text())
MODULES = {name: name.replace('mouse637-', 'mouse638-') for name in FROZEN}
MODULES['mouse637-publish-plan.py'] = 'mouse638-publish-plan.py'
PUBLISHED_SOURCE = '0021084ccb9537e657d21e6f0c8e812dee6b461f'
PUBLISHED_UPDATER = '91ab363f926774825caf8055b2d3d81bf0d51264'


def previous(platform):
    folder = {'darwin': 'arm64', 'linux': 'linux-x64', 'win32': 'windows-x64'}[platform]
    value = json.loads((TOOLS.parent / 'staging/mouse' / ('6.0.37-' + folder) / 'pin.json').read_text())
    if value.get('version') != '6.0.37' or value.get('source') != PUBLISHED_SOURCE or value.get('ready') is not True:
        raise ValueError('Immutable published637 predecessor changed')
    return {'version': '6.0.37', 'source': PUBLISHED_SOURCE, 'updaterBlobSHA': PUBLISHED_UPDATER,
            **{key: value[key] for key in ('packages', 'package') if key in value}}


def baselines():
    def package(platform, name, tag):
        old = previous(platform)
        data = old.get('packages', {}).get(name) or old.get('package')
        return {'name': name, 'tag': tag, 'size': data['size'], 'sha256': data['sha256']}
    return {'darwin': package('darwin', 'Mouse-Browser-6.0.37-mac-arm64.dmg', 'quadro-macos-v6.0.37-arm64'),
            'win32': package('win32', 'Mouse-Browser-6.0.37-Windows-x64.exe', 'mouse-windows-v6.0.37-x64'),
            'linux': {fmt: package('linux', 'Mouse-Browser-6.0.37-Linux-x64.' + suffix, 'mouse-linux-v6.0.37-x64')
                      for fmt, suffix in (('appimage', 'AppImage'), ('deb', 'deb'))}}


def checked(name):
    if name not in FROZEN:
        raise ValueError('Unreviewed638 predecessor dependency: ' + name)
    raw = (TOOLS / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
        raise ValueError('Immutable638 predecessor dependency changed: ' + name)
    return raw


def legacy():
    checked('mouse637-reuse.py')
    return runpy.run_path(str(TOOLS / 'mouse637-reuse.py'))


def target(name):
    if name in MODULES:
        return MODULES[name]
    old = legacy()['target'](name)
    if old not in MODULES:
        raise ValueError('Unreviewed638 legacy target: ' + name)
    return MODULES[old]


PREDECESSOR_MODULES = {'mouse637-current.py', 'mouse637-upgrade-evidence.py',
    'mouse637-update-button-evidence.py', 'mouse637-performance-evidence.py',
    'mouse637-public-channel.py', 'mouse637-windows-display-evidence.py',
    'mouse634-linux-release.py', 'mouse633-linux-evidence.py'}


def adapted_tree(name, *, current_native=False):
    tree = ast.parse(checked(name), filename=str(TOOLS / name)) if name in FROZEN else legacy()['adapted_tree'](name, current_native=current_native)

    class Identity(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            node = self.generic_visit(node)
            if name != 'mouse632-evidence.py' or node.name != 'verify_fractional_layouts':
                return node
            #638 deliberately partitions DOM panes on the native integer-DIP
            #grid. Keep the complete seven-page Nora proof, but require this
            #new source contract instead of the superseded fractional defect.
            row = next(n for n in node.body if isinstance(n, ast.Assign)
                       and ast.unparse(n.targets[0]) == 'row')
            node.body[node.body.index(row) + 1:node.body.index(row) + 1] = ast.parse(
                "require(row.get('layoutContract') == 'integer-dom-native-endpoints-638', "
                "'seven-pane638 integer layout contract is missing')").body
            loop = next(n for n in node.body if isinstance(n, ast.For)
                        and ast.unparse(n.target) == '(identity, page)')
            slot = next(n for n in loop.body if isinstance(n, ast.Assign)
                        and ast.unparse(n.targets[0]) == 'slot')
            loop.body[loop.body.index(slot) + 1:loop.body.index(slot) + 1] = ast.parse(
                "require(all(nonnegative_integer(slot[key]) for key in ('x', 'y', 'width', 'height')), "
                "'seven-pane638 DOM bounds are not integers')").body
            comparisons = [n for n in ast.walk(node) if isinstance(n, ast.Compare)
                           and ast.unparse(n) == 'differences >= 1']
            assert len(comparisons) == 1, 'Reviewed Nora endpoint predicate changed'
            comparisons[0].ops = [ast.Eq()]
            comparisons[0].comparators = [ast.Constant(0)]
            messages = [n for n in ast.walk(node) if isinstance(n, ast.Constant)
                        and n.value == 'seven-pane fixture did not reproduce independent-span versus endpoint rounding']
            assert len(messages) == 1, 'Reviewed Nora endpoint diagnostic changed'
            messages[0].value = 'seven-pane638 integer DOM differs from rounded native endpoints'
            result = next(n for n in node.body if isinstance(n, ast.Return))
            assert isinstance(result.value, ast.Dict) and 'integerDOMPanes' not in [
                key.value for key in result.value.keys], 'Reviewed Nora result changed'
            result.value.keys.append(ast.Constant('integerDOMPanes'))
            result.value.values.append(ast.parse('len(slots)', mode='eval').body)
            return node

        def visit_IfExp(self, node):
            node = self.generic_visit(node)
            # Explicit owner638 change: rectangular grid and AI preview now
            # have one CSS-pixel separators. Radius0 remains unchanged.
            if (name == 'mouse637-features-evidence.py' and isinstance(node.body, ast.Constant)
                    and node.body.value == 0 and isinstance(node.orelse, ast.Constant) and node.orelse.value == 6
                    and ast.unparse(node.test) in ("mode == 'square'", "value['mode'] == 'square'")):
                node.body = ast.copy_location(ast.Constant(1), node.body)
            return node

        def visit_Constant(self, node):
            if not isinstance(node.value, str):
                return node
            value = node.value.replace('6.0.37', '6.0.38')
            for old, new in MODULES.items():
                value = value.replace(old, new)
            # Publisher folders/statuses; never rename retained source smoke files.
            value = value.replace('mouse637-release', 'mouse638-release').replace('mouse637-linux-release', 'mouse638-linux-release').replace('mouse637-windows-release', 'mouse638-windows-release')
            value = value.replace('publish-mouse637', 'publish-mouse638').replace('MOUSE637_', 'MOUSE638_')
            for old, new in (
                ('MOUSE_637_REAL_636_TO_637_', 'MOUSE_638_REAL_637_TO_638_'),
                ('MOUSE_637_REAL_629_TO_637_', 'MOUSE_638_REAL_629_TO_638_'),
                ('MOUSE_637_WINDOWS_REAL_629_TO_637_', 'MOUSE_638_WINDOWS_REAL_629_TO_638_'),
                ('real-636-to-637-', 'real-637-to-638-'),
                ('real-629-to-637-', 'real-629-to-638-'),
                ('real-published-predecessor-to-637-', 'real-published-predecessor-to-638-'),
            ):
                value = value.replace(old, new)
            if name in PREDECESSOR_MODULES:
                value = value.replace('6.0.36', '6.0.37').replace('legacy636-update', 'legacy637-update').replace('updateFrom636', 'updateFrom637')
                value = value.replace('7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3', PUBLISHED_SOURCE)
                value = value.replace('MOUSE_637_ACTUAL_636_UPDATER_', 'MOUSE_638_ACTUAL_637_UPDATER_')
                if value == '636':
                    value = '637'
            # Baseline acceptance must remain the actual published637 checker.
            if name == 'mouse637-performance-evidence.py' and node.value == 'mouse636-task-evidence.py':
                value = 'mouse637-task-evidence.py'
            if name == 'mouse637-features-evidence.py' and value == 'gapFreeNativeViews':
                value = 'onePixelSeparatedNativeViews'
            if current_native and value == r'mouse-(?:635|636|637)-[a-z0-9-]+\.png':
                value = r'mouse-(?:635|636|637|638)-[a-z0-9-]+\.png'
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

    tree = Identity().visit(tree)
    # The source keeps current helper filenames637 but moves the actual
    # predecessor from636 to637. Marker concatenation must match its new638 ID.
    if name == 'mouse637-current.py':
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == 'MOUSE_637_REAL_':
                node.value = 'MOUSE_638_REAL_'
            elif isinstance(node, ast.Constant) and node.value == '_TO_637_PROFILE_PASS':
                node.value = '_TO_638_PROFILE_PASS'
    return ast.fix_missing_locations(tree)


def load(name, *, namespace=None, current_native=False):
    scope = namespace if namespace is not None else {}
    original = scope.get('__name__')
    scope['__file__'] = str(TOOLS / ('mouse638-native-evidence.py' if current_native else target(name)))
    scope['__name__'] = 'retained638_' + name.replace('-', '_')
    if name == 'mouse632-release.py':
        def verify_mode_requests(facts, output):
            return runpy.run_path(str(TOOLS / 'mouse638-presets-evidence.py'))['verify_legacy_facts'](facts, output)
        scope['_mouse637_verify_mode_requests'] = verify_mode_requests
    if name == 'mouse633-owner-feedback-evidence.py':
        scope['_mouse637_zoom_color'] = runpy.run_path(str(TOOLS / 'mouse638-zoom-evidence.py'))['expected_rgb']
    try:
        exec(compile(adapted_tree(name, current_native=current_native), scope['__file__'], 'exec'), scope)
    finally:
        if original is not None:
            scope['__name__'] = original
    return scope


def execute(name, scope):
    """Execute one immutable top-level637 module with the actual caller mode."""
    tree = adapted_tree(name)
    exec(compile(tree, scope['__file__'], 'exec'), scope)
