#!/usr/bin/env python3
"""Reuse byte-frozen633 algorithms with explicit634 runtime/module identities.

Only reviewed code constants are adapted. Evidence bytes, HTTP fixture routes,
owned download filenames and historical native report/marker names stay intact.
The current published633-to634 upgrade is a separate, explicitly named gate.
"""
import ast
import hashlib
from pathlib import Path
import runpy

FROZEN = {
    'mouse633-context-evidence.py': 'd9293accaa4d467e6579dd3096da0b92581705851cef86c13d4ccca43d4e279a',
    'mouse633-current.py': 'f58821bb88ad8a7788c6f4b60b98eb2b65211d1be2de81279dba69df9ebecc42',
    'mouse633-evidence.py': '23a87cdc4429d023f924b7de633ebe58ccde8c20d2022e486c2046881b7cfc4a',
    'mouse633-feedback-evidence.py': '26e96683b0df92e87c42472aff9c444bfd36a324e8c488559e59b2d1486780a1',
    'mouse633-linux-evidence.py': '865952bb80df219bc97348472f8af512e55cb729ff6042d55ac7944ad7ddb09c',
    'mouse633-linux-release.py': '78b26f9736d928bf4ccb69c1f9726b229b5bd40a294b09096a9416ead2d75326',
    'mouse633-owner-feedback-evidence.py': '125dc51e52b0821f9f9eda086d7e2b65c592d01ba09bafc322c1cb2bae2fde32',
    'mouse633-release.py': 'aeadfb7c6b42d923fb2eed48eb0b0c35acf528138e88e601ceea8eb26922bb6e',
    'mouse633-reuse.py': '93ecb85337f02b7668b875a7c3f6b2ec7ef3b6b4849b78f089a762c794d7311e',
    'mouse633-task-evidence.py': 'a7e7ab978cd9dbc4d92c53b5c8e129dc427bb745be95742f8ac1f6e6699aea25',
    'mouse633-ui-evidence.py': 'f5f85beb224a6eabf1a07559641283953562de6abce3a4a6bb3f117be47755bd',
    'mouse633-upgrade-evidence.py': 'ebafc96624d39fd811dd469a226b6c81d0bc82d12c2553459444c2218fb4e975',
    'mouse633-windows-release.py': '8aed5f5beb177e7e81d8002985e2782574d7552353da1db3260766f4c77e3b1f',
    'mouse633-workspace-evidence.py': '17a5ce2b600403e88b64019dbb4f0572989381063ccf94184d59615d96df3d2a',
    'test-mouse633-evidence.py': '40d1bd55ce6b07273ddc224a77ca52f4bd786398821086ab62b449b2e889c733',
    'test-mouse633-ui-evidence.py': '9b1ff1256e1a0b0341cbc18188866cda19a1b349bc4e058e6f99c5c0b7a84347',
    'test_mouse633_context_evidence.py': '5937ee27c6398f9a06cf82aa1859f0a8e74a8f6e268720ac607c560463fcdc57',
    'test_mouse633_feedback_evidence.py': 'a106ee2a3ee7f71b4446688146a705a63312f9df0bfaae8d5441eb0c9af2480d',
    'test_mouse633_linux_evidence.py': '95cf36c19867081405f9a9e0da8e1896469955be38e2ba3c15785312c0fb97ac',
    'test_mouse633_linux_release.py': '381dcf1080c4801c951ebe874cca651a9ff21433facbd1b07e808ff7dbedd01e',
    'test_mouse633_native_report.py': '548779f196365935ff0b152c4cf4de9dd47325896b01305a4c5ee5f146e6add9',
    'test_mouse633_owner_feedback_evidence.py': '8a7037eee323ec3b9cd74a128b5002639e5a2d7601e06932e0cf2ecf6f8f58e3',
    'test_mouse633_release_bytes.py': 'c3f91bd9237decd350da6ad02e4891318a5044171d8555d509893000a85bcbd3',
    'test_mouse633_task_evidence.py': '61e91d2912886b91fe143ecaabd1c05e8c058ac421a3e5fb37855179bbf77b08',
    'test_mouse633_upgrade_evidence.py': '4c0e3cdb54e3d8889f8cf72805e36632fef017d34802f7a221994f243a1300fd',
    'test_mouse633_windows_release.py': 'e57c98d1b1354fdd30be564a87bf81bd577375da31658c589dae51c1ae5c8dc9',
    'test_mouse633_workspace_evidence.py': '37eb1ad34da3cc65264b049f5a6bbc4c3e04e6212f6ff7765a5bc09329fbacc9',
}
MODULES = {name: name.replace('mouse633-', 'mouse634-').replace('test_mouse633_', 'test_mouse634_')
           for name in FROZEN}
MODULES['mouse633-owner-feedback-evidence.py'] = 'mouse634-retained-owner-evidence.py'
MODULES['test_mouse633_owner_feedback_evidence.py'] = 'test_mouse634_retained_owner_evidence.py'


def checked(name):
    if name not in FROZEN:
        raise ValueError('Unreviewed634 dependency: ' + name)
    raw = Path(__file__).with_name(name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
        raise ValueError('Immutable634 dependency changed: ' + name)
    return raw


def adapted_tree(name):
    # The existing633 adapter still verifies every frozen632 dependency. Its own
    # source is pinned here before it is used to expand that reviewed algorithm.
    if name.startswith(('mouse632-', 'test_mouse632_', 'test-mouse632-')):
        checked('mouse633-reuse.py')
        legacy = runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))
        tree = legacy['adapted_tree'](name)
    else:
        tree = ast.parse(checked(name), filename=str(Path(__file__).with_name(name)))

    class Identity(ast.NodeTransformer):
        def visit_Constant(self, node):
            if not isinstance(node.value, str):
                return node
            value = node.value.replace('6.0.33', '6.0.34').replace('MOUSE633_', 'MOUSE634_').replace('publish-mouse633', 'publish-mouse634')
            for old, new in MODULES.items():
                value = value.replace(old, new)
            for old, new in (('mouse633-windows-release', 'mouse634-windows-release'),
                             ('mouse633-linux-release', 'mouse634-linux-release'),
                             ('mouse633-release', 'mouse634-release')):
                value = value.replace(old, new)
            for old, new in (
                ('mouse-633-upgrade', 'mouse-634-upgrade'),
                ('MOUSE_633_REAL_632_TO_633_PROFILE_PASS', 'MOUSE_634_REAL_633_TO_634_PROFILE_PASS'),
                ('MOUSE_633_UPGRADE_PROFILE_', 'MOUSE_634_UPGRADE_PROFILE_'),
                ('MOUSE_633_REAL_629_TO_633_REPLACE_RELAUNCH_PROFILE_PASS', 'MOUSE_634_REAL_629_TO_634_REPLACE_RELAUNCH_PROFILE_PASS'),
                ('MOUSE_633_WINDOWS_REAL_629_TO_633_PROFILE_PASS', 'MOUSE_634_WINDOWS_REAL_629_TO_634_PROFILE_PASS'),
                ('real-632-to-633-profile-preserving-replacement', 'real-633-to-634-profile-preserving-replacement'),
                ('real-629-to-633-profile-preserving-install', 'real-629-to-634-profile-preserving-install'),
            ):
                value = value.replace(old, new)
            # These two retained tests reverse module identities when comparing
            # exact function ASTs. Do not rewrite similarly named native files.
            if name in ('test_mouse633_native_report.py', 'test-mouse633-evidence.py') and value == 'mouse633-':
                value = 'mouse634-'
            if name == 'test_mouse632_windows_release.py' and value == 'Immutable633 dependency changed: mouse632-ui-evidence.py':
                value = 'Immutable634 dependency changed: mouse633-ui-evidence.py'
            if value != node.value:
                return ast.copy_location(ast.Constant(value=value), node)
            return node
    tree = Identity().visit(tree)
    if name == 'mouse633-feedback-evidence.py':
        # The native634 footer adds the search control immediately before the
        # smile and names it in the accessible group label. Retain every other
        # order, geometry, icon and PNG requirement.
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'verify_footer')
        replacements = {
            "row.get('count') == 5": "row.get('count') == 6",
            "row.get('actions') == ['emoji', 'zoom', 'history', 'bookmarks', 'downloads']":
                "row.get('actions') == ['tile-search', 'emoji', 'zoom', 'history', 'bookmarks', 'downloads']",
        }
        changed = set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Compare) and ast.unparse(node) in replacements:
                old = ast.unparse(node)
                assert old not in changed, 'Footer634 predicate unexpectedly duplicated'
                node.comparators = ast.parse(replacements[old], mode='eval').body.comparators
                changed.add(old)
        assert changed == set(replacements), 'Only the explicit634 footer count and actions may change'
        loop = next(n for n in fn.body if isinstance(n, ast.For) and isinstance(n.target, ast.Name)
                    and n.target.id == 'row' and isinstance(n.iter, ast.Name) and n.iter.id == 'cases')
        loop.body[:0] = ast.parse("need(row.get('label') == 'Поиск, эмодзи, история, закладки и загрузки', 'search footer accessible label differs')").body
    if name == 'mouse632-evidence.py':
        # Only the explicitly superseded download placement and terminal-widget
        # checks change. Retry/native bytes/private scope/capture stay identical.
        functions = {n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
        fn = functions['verify_feedback']
        loop = next(n for n in fn.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id == 'event' and isinstance(n.iter,ast.Name) and n.iter.id=='events')
        at = next(i for i,n in enumerate(loop.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='pill' for t in n.targets))
        assert isinstance(loop.body[at+1],ast.Expr) and isinstance(loop.body[at+2],ast.If)
        loop.body[at:at+3] = ast.parse('_bottom634["current_event"](event, phase, expected, case)').body
        unknown = next(n for n in loop.body if isinstance(n,ast.If) and ast.unparse(n.test) == "'unknown' in case")
        require_call = unknown.body[0].value
        assert isinstance(require_call.args[0],ast.BoolOp) and len(require_call.args[0].values)==4
        require_call.args[0].values = require_call.args[0].values[:2]
        functions['download_geometry'].body = ast.parse('return _bottom634["download_geometry"](ui, native, label)').body
        tree.body += ast.parse('_bottom634 = runpy.run_path(str(pathlib.Path(__file__).with_name("mouse634-download-evidence.py")))').body
    if name == 'mouse633-linux-evidence.py':
        # Linux now has a real published633 baseline. The separate current gate
        # verifies both actual old packages; native restart/sandbox gates stay.
        fn = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify')
        count = 0
        for node in ast.walk(fn):
            if isinstance(node,ast.Compare) and isinstance(node.left,ast.Call) and isinstance(node.left.func,ast.Attribute) and isinstance(node.left.func.value,ast.Name) and node.left.func.value.id=='report' and node.left.args and isinstance(node.left.args[0],ast.Constant):
                key=node.left.args[0].value
                if key=='firstLinuxRelease': node.comparators=[ast.Constant(False)];count+=1
                if key=='previousVersion': node.ops=[ast.Eq()];node.comparators=[ast.Constant('6.0.33')];count+=1
            if isinstance(node,ast.Return) and isinstance(node.value,ast.Dict):
                for i,key in enumerate(node.value.keys):
                    if isinstance(key,ast.Constant) and key.value=='firstLinuxRelease':node.value.values[i]=ast.Constant(False);count+=1
                    if isinstance(key,ast.Constant) and key.value=='previousVersion':node.value.values[i]=ast.Constant('6.0.33');count+=1
        assert count==4, 'Only the explicit Linux baseline scope may change'
    return ast.fix_missing_locations(tree)


def load(name, *, namespace=None):
    target = MODULES.get(name)
    if target is None and name.startswith(('mouse632-', 'test_mouse632_', 'test-mouse632-')):
        target = name.replace('mouse632-', 'mouse634-').replace('test_mouse632_', 'test_mouse634_')
    if target is None:
        raise ValueError('Unreviewed634 dependency: ' + name)
    scope = namespace if namespace is not None else {}
    original_name = scope.get('__name__')
    scope['__file__'] = str(Path(__file__).with_name(target))
    scope['__name__'] = 'retained634_' + name.replace('-', '_')
    try:
        exec(compile(adapted_tree(name), scope['__file__'], 'exec'), scope)
    finally:
        if original_name is not None:
            scope['__name__'] = original_name
    return scope
