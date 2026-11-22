#!/usr/bin/env python3
"""Byte-frozen636 gates with scoped637 identities, palette and populated modes.

Old artifacts and validators remain byte-for-byte immutable. Current637 still
emits retained636 owner, Agent, search-removal and desktop-transition reports.
Only new upgrade/performance reports and the current executable identity move.
"""
import ast
import hashlib
from pathlib import Path
import runpy

FROZEN = {'mouse636-633-owner-evidence.py': 'c928466a5b27bc690e98b37561544092b2400ce159bf9db9b6db36784f8c2955',
 'mouse636-agent-inline-evidence.py': '02c3d40f21092d998444693d115b617697a70a9554e415abc92d34dc11587159',
 'mouse636-capture-evidence.py': '2bc823989fcbb494720a1ee52069e0754661c8a25988d7bd27f3e80bc934e43c',
 'mouse636-context-evidence.py': '5bc192e1e3445216a5e2e078ac5dcc3a97bc8041823eadc048d7aad7d7889be6',
 'mouse636-current.py': '2d5e8efaba0a0d86d98ef7d72df29fb4f1e97c49508003dc9011c3583fe393fd',
 'mouse636-download-evidence.py': 'c178a0d8e8c42b61b1352fca4da3c1b6b2baf45076c2bc170ba3897e3ab55644',
 'mouse636-evidence.py': '18f369cdfecd6fda829f91d09e58ab876a1ee705975bd929a7998baf9d25ed6d',
 'mouse636-feedback-evidence.py': '0c866e1a8f363e44f9f0927b7bd0b88d79b0891277d49acc9dd837a0442006f8',
 'mouse636-focused-evidence.py': '0ee66dfeafe9c9d354f9d36cc2c3ce82ea48e11c0be16ed58af8d48c23f4b94f',
 'mouse636-library-evidence.py': '226e939a21ed09cb044da0e5e2ef2d3274264173f23f2d92d28ac9e107d17f8e',
 'mouse636-linux-evidence.py': 'd24b285cd1c079b30aca2d5fae95344099b7b0756dfa0c175f0efab89200fd9b',
 'mouse636-linux-release.py': 'c9ffa6081aadb42b836f73e2caf7e090a133a7ccb7c859c01ae07a436eaf62e6',
 'mouse636-motion-trace.py': 'ea140e6ce40b20cf075a4eb5c36482b5a6a423c127bd81583c84df4c766ebe56',
 'mouse636-native-evidence.py': '157f4bc90b6b7f427dc9f996a92e905adea3a832f7f3ef850b75e586641e878a',
 'mouse636-owner-feedback-evidence.py': '0d64d49172b96d875afd0bf36d0708604b7b74ccfeff4566de91260e712d0d5c',
 'mouse636-pane-layout-evidence.py': '898a8f843a67de4ae3cc090cd2d50588c4efcfd71748d81c91c87189a477aa2a',
 'mouse636-performance-evidence.py': '2548d1fe02bcc9a16816948089ac9773c5bd70a89c3108390a68c84290fe2777',
 'mouse636-publish-plan.py': '387198b46b7038b26286491a08cb13613963ea565e05ae1577db02a9af4a53b8',
 'mouse636-release.py': '84523a1f339f4f1cdd36599a3959e1105f9ee7b4fb78af54370720dc7303dd22',
 'mouse636-retained-native-evidence.py': '0a5f02c62aa5cc66eb1dc487655e74d9a132f2b48a1737c0f17b8818e84ac173',
 'mouse636-retained-owner-evidence.py': 'f7eb49b1e4b67bbe2daf935dec811b3cdba2408eda4029100617dcf3f6930814',
 'mouse636-reuse.py': '1504281765c205013fa952d6d1bc4d84122151d248e3493ce4097638d4f8becc',
 'mouse636-search-removal-evidence.py': '2a5bcf1642350813ab088d85ccd0f29aeb7b2662e410a50954a489b416fd3338',
 'mouse636-task-evidence.py': '14eebe8fbe325068101b22df0c2503e62271028f6b6e955a0b729e9b405ad668',
 'mouse636-ui-evidence.py': 'b955f4b305a6b7fee21c0b6b20ea0662db9f4d39797c863419abc0c8848a7646',
 'mouse636-upgrade-evidence.py': '59fc0d8331e807013c2ce38a6b18f28d718e0b091a2fdc2d247ac6b0e54a2de2',
 'mouse636-windows-release.py': '2c52380413ef25e301ae0c9ec1e6908a5a5bd2bfd0db77e0cafe004c9462c17c',
 'mouse636-workspace-evidence.py': '4fac017354605966af3c8f810106fdc2f46154e5b2dc70bd0eb29ecdf1d17912',
 'test_mouse636_pipeline.py': '3e584150b1de510049311fe85e7656822a7b953e7f9e67602fd086734de422e6'}
MODULES = {name: name.replace('mouse636-', 'mouse637-').replace('test_mouse636_', 'test_mouse637_') for name in FROZEN}
PREVIOUS_LINUX = {'version': '6.0.36', 'source': '7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3',
    'updaterBlobSHA': '91ab363f926774825caf8055b2d3d81bf0d51264', 'packages': {
        'Mouse-Browser-6.0.36-Linux-x64.AppImage': {'size': 135673552, 'sha256': 'e126ee0e50c1bc8e4e1108600e5b2e9e74af609feac0fff8d8de7b3c0b79f090'},
        'Mouse-Browser-6.0.36-Linux-x64.deb': {'size': 105853084, 'sha256': '6de6baf09263ade5ea20fec2984cb183d6909cb7a7646b8c8d917cf33c0d7d7f'}}}


def checked(name):
    if name not in FROZEN:
        raise ValueError('Unreviewed637 dependency: ' + name)
    raw = Path(__file__).with_name(name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
        raise ValueError('Immutable637 dependency changed: ' + name)
    return raw


def legacy():
    checked('mouse636-reuse.py')
    return runpy.run_path(str(Path(__file__).with_name('mouse636-reuse.py')))


def target(name):
    if name in MODULES:
        return MODULES[name]
    previous = legacy()['target'](name)
    if previous not in MODULES:
        raise ValueError('Unreviewed637 dependency: ' + name)
    return MODULES[previous]


def adapted_tree(name, *, current_native=False):
    tree = ast.parse(checked(name), filename=str(Path(__file__).with_name(name))) if name in FROZEN else legacy()['adapted_tree'](name, current_native=current_native)
    preset_adaptations = {'count': 0, 'token': 0}
    zoom_adaptations = {'signature': 0, 'palette': 0, 'call': 0}

    class Identity(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            node = self.generic_visit(node)
            if name == 'mouse633-owner-feedback-evidence.py' and node.name == 'meter':
                expected = ast.parse('def meter(image): pass').body[0].args
                if ast.dump(node.args) != ast.dump(expected):
                    raise ValueError('Frozen zoom meter signature changed')
                node.args.kwonlyargs.append(ast.arg(arg='expected_rgb'))
                node.args.kw_defaults.append(ast.parse('(235, 40, 155)', mode='eval').body)
                zoom_adaptations['signature'] += 1
            return node

        def visit_Tuple(self, node):
            node = self.generic_visit(node)
            if name == 'mouse633-owner-feedback-evidence.py' and ast.dump(node) == ast.dump(ast.parse('(235,40,155)', mode='eval').body):
                zoom_adaptations['palette'] += 1
                return ast.copy_location(ast.Name(id='expected_rgb', ctx=ast.Load()), node)
            return node

        def visit_Call(self, node):
            node = self.generic_visit(node)
            if name == 'mouse633-owner-feedback-evidence.py' and ast.dump(node) == ast.dump(ast.parse('meter(image)', mode='eval').body):
                zoom_adaptations['call'] += 1
                return ast.copy_location(ast.parse('meter(image, expected_rgb=_mouse637_zoom_color(row))', mode='eval').body, node)
            return node

        def visit_Constant(self, node):
            if not isinstance(node.value, str):
                return node
            value = node.value.replace('6.0.36', '6.0.37').replace('MOUSE636_', 'MOUSE637_').replace('publish-mouse636', 'publish-mouse637')
            for old, new in MODULES.items():
                value = value.replace(old, new)
            for old, new in (
                ('mouse636-windows-release', 'mouse637-windows-release'),
                ('mouse636-linux-release', 'mouse637-linux-release'),
                ('mouse636-release', 'mouse637-release'),
                ('mouse-636-upgrade', 'mouse-637-upgrade'),
                ('mouse-636-profile-upgrade', 'mouse-637-profile-upgrade'),
                ('mouse-636-baseline-performance', 'mouse-637-baseline-performance'),
                ('mouse-636-performance', 'mouse-637-performance'),
                ('MOUSE_636_PERFORMANCE_PASS', 'MOUSE_637_PERFORMANCE_PASS'),
                ('MOUSE_636_BASELINE_PERFORMANCE_PASS', 'MOUSE_637_BASELINE_PERFORMANCE_PASS'),
                ('MOUSE_636_REAL_629_TO_636_REPLACE_RELAUNCH_PROFILE_PASS', 'MOUSE_637_REAL_629_TO_637_REPLACE_RELAUNCH_PROFILE_PASS'),
                ('MOUSE_636_WINDOWS_REAL_629_TO_636_PROFILE_PASS', 'MOUSE_637_WINDOWS_REAL_629_TO_637_PROFILE_PASS'),
                ('real-published-predecessor-to-636-profile-preserving-replacement', 'real-published-predecessor-to-637-profile-preserving-replacement'),
                ('real-629-to-636-profile-preserving-install', 'real-629-to-637-profile-preserving-install'),
            ):
                value = value.replace(old, new)
            if name in ('mouse634-linux-release.py', 'mouse633-linux-evidence.py'):
                value = value.replace('6.0.34', '6.0.36').replace('actual634', 'actual636').replace('published634', 'published636').replace('legacy634-update', 'legacy636-update')
            if current_native and node.value == r'mouse-(?:635|636)-[a-z0-9-]+\.png':
                value = r'mouse-(?:635|636|637)-[a-z0-9-]+\.png'
            if name == 'mouse632-release.py' and node.value == 'five-mode-layouts-empty-only-suggestions':
                value = 'five-mode-populated-presets-preserve-live-pages'
                preset_adaptations['token'] += 1
            return ast.copy_location(ast.Constant(value=value), node) if value != node.value else node

        def visit_Compare(self, node):
            node = self.generic_visit(node)
            expected = ast.parse("facts.get('suggestedRequests') != 7", mode='eval').body
            if name == 'mouse632-release.py' and ast.dump(node) == ast.dump(expected):
                # The user explicitly changed preset semantics. Require the
                # full independent637 evidence, including real27 requests,
                # retained page state and both localhost PNGs. Do not edit the
                # emitted count or bypass the other retained622 checks.
                preset_adaptations['count'] += 1
                return ast.copy_location(ast.parse('not _mouse637_verify_mode_requests(facts, OUT)', mode='eval').body, node)
            return node

        def visit_Assign(self, node):
            node = self.generic_visit(node)
            # The requested637 workspace seams darken; old--line control-border
            # colors are not accepted as the new workspace palette. All raw PNG
            # decoding, sampling coordinates and tolerances stay unchanged.
            if any(isinstance(t, ast.Name) and t.id in ('LINE', 'VEINS_627') for t in node.targets):
                class Palette(ast.NodeTransformer):
                    def visit_List(self, value):
                        if all(isinstance(v, ast.Constant) for v in value.elts) and [v.value for v in value.elts] == [67, 83, 107]:
                            return ast.copy_location(ast.parse('[53, 67, 87]', mode='eval').body, value)
                        return self.generic_visit(value)

                    def visit_Constant(self, value):
                        return ast.copy_location(ast.Constant('#354357'), value) if value.value == '#43536b' else value
                node.value = Palette().visit(node.value)
            return node

    tree = Identity().visit(tree)
    if name == 'mouse632-release.py' and preset_adaptations != {'count': 1, 'token': 1}:
        raise ValueError('Frozen preset count/token adaptation target changed')
    if name == 'mouse633-owner-feedback-evidence.py' and zoom_adaptations != {'signature': 1, 'palette': 1, 'call': 1}:
        raise ValueError('Frozen zoom meter adaptation target changed')
    if name == 'mouse634-linux-release.py':
        assignments = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PREVIOUS' for t in n.targets)]
        if len(assignments) != 1:
            raise ValueError('Frozen Linux predecessor assignment changed')
        assignments[0].value = ast.parse(repr(PREVIOUS_LINUX), mode='eval').body
    return ast.fix_missing_locations(tree)


def load(name, *, namespace=None, current_native=False):
    scope = namespace if namespace is not None else {}
    original = scope.get('__name__')
    scope['__file__'] = str(Path(__file__).with_name('mouse637-native-evidence.py' if current_native else target(name)))
    scope['__name__'] = 'retained637_' + name.replace('-', '_')
    if name == 'mouse632-release.py':
        def verify_mode_requests(facts, output):
            checker = runpy.run_path(str(Path(__file__).with_name('mouse637-presets-evidence.py')))
            return checker['verify_legacy_facts'](facts, output)
        scope['_mouse637_verify_mode_requests'] = verify_mode_requests
    if name == 'mouse633-owner-feedback-evidence.py':
        scope['_mouse637_zoom_color'] = runpy.run_path(str(Path(__file__).with_name('mouse637-zoom-evidence.py')))['expected_rgb']
    try:
        exec(compile(adapted_tree(name, current_native=current_native), scope['__file__'], 'exec'), scope)
    finally:
        if original is not None:
            scope['__name__'] = original
    return scope
