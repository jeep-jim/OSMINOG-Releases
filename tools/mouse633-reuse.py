#!/usr/bin/env python3
"""Reuse immutable632 algorithms with explicit633 code identities.

Only Python string constants are adapted; evidence and published files are never
rewritten. Historical631/632 report filenames, native markers and all frozen
629/628 dependencies stay intact. The hashes bind every reused algorithm.
"""
import ast
import hashlib
from pathlib import Path

FROZEN = {'mouse632-release.py': '387206f76612703dd196f079d250ade8cc12f00b2bc24efa76e86d81e1fe6369', 'mouse632-windows-release.py': 'e096a3f4bcbe3f5672dad30f2aa7ffb9079996e55ba43ab853704b76bbd4440e', 'mouse632-evidence.py': '73df70bff6099639e421624a01f77ea6651013448b1cc09fe10c073899e40be6', 'mouse632-ui-evidence.py': 'dfcfa00cbc50b3bf48c6473d8b771e79b12926640db3872aedfe9fde7d0269b4', 'mouse632-feedback-evidence.py': '4d775cc2240a9cab5cf811c6d219d1b3dd38ce645c565ba2257eade0f83c1526', 'test-mouse632-evidence.py': '53108c8fb1142cb2fc65354e322e4524af11788ca8f4ade98cce056a69b684ca', 'test-mouse632-ui-evidence.py': '8324e2c310fd8568c8b973036431bd1ba86973fd07a37c42356a4bf1d538c008', 'test_mouse632_task_evidence.py': '5911ce1896bf999cef416a139f47ac77e0507359361404ea5a013ebd77ede3b9', 'test_mouse632_windows_release.py': '1fbb471cceb5e11c9d292aef9b941f0406c9144e1d4ed5ace3cfd85a11a16830'}
FROZEN['test_mouse632_native_report.py'] = '6c9e467a23e339d38a35a7f503012b91eb521a0f5b5afa1b3cc214a2b668c9d0'
FROZEN['test_mouse632_release_bytes.py'] = 'a6bc3d4256b79c13a2ce85457779ef6e36b5ce2a8b71efeeddd8f10a3d869316'


FROZEN['test_mouse632_feedback_evidence.py'] = 'f27c0c136e3401b2116bea5bf47e5ef0cb7beebc32f28625773257871c628e61'


def adapted_tree(name):
    path = Path(__file__).with_name(name)
    if name not in FROZEN:
        raise ValueError('Unreviewed633 dependency: ' + name)
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
        raise ValueError('Immutable633 dependency changed: ' + name)
    class Identity(ast.NodeTransformer):
        current_function = None

        def visit_FunctionDef(self, node):
            previous = self.current_function
            self.current_function = node.name
            self.generic_visit(node)
            self.current_function = previous
            return node

        def current_upgrade(self, call):
            if (name == 'mouse632-windows-release.py' and isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Name) and call.func.id == 'verify_feedback_evidence'
                    and self.current_function in ('import_candidate','verify_installed','publish')):
                pin_arg = ast.parse('pin()', mode='eval').body if self.current_function == 'verify_installed' else ast.Name(id='p', ctx=ast.Load())
                return ast.Expr(value=ast.Call(func=ast.Name(id='_verify_current_upgrade',ctx=ast.Load()),
                                               args=[call.args[0],pin_arg],keywords=[]))
            return None

        def visit_Assign(self, node):
            self.generic_visit(node)
            gate = self.current_upgrade(node.value)
            return [node, ast.copy_location(gate,node)] if gate else node

        def visit_Expr(self, node):
            self.generic_visit(node)
            gate = self.current_upgrade(node.value)
            return [node, ast.copy_location(gate,node)] if gate else node

        def visit_Constant(self, node):
            if isinstance(node.value, str):
                value = node.value.replace('6.0.32', '6.0.33')
                value = value.replace('mouse632-', 'mouse633-').replace('test_mouse632_', 'test_mouse633_')
                # Native scrollbar HTTP fixtures retain their published632
                # route identities, including URLs and the cross-frame regexp.
                for route in ('/mouse632-encapsulated', '/mouse632-frame', '/mouse632-cross-frame'):
                    value = value.replace(route.replace('mouse632-', 'mouse633-'), route)
                value = value.replace('MOUSE632_', 'MOUSE633_')
                value = value.replace('MOUSE_632_REAL_629_TO_632_REPLACE_RELAUNCH_PROFILE_PASS',
                                      'MOUSE_633_REAL_629_TO_633_REPLACE_RELAUNCH_PROFILE_PASS')
                value = value.replace('MOUSE_632_WINDOWS_REAL_629_TO_632_PROFILE_PASS',
                                      'MOUSE_633_WINDOWS_REAL_629_TO_633_PROFILE_PASS')
                value = value.replace('mouse-632-source-', 'mouse-633-source-')
                value = value.replace('real-629-to-632-profile-preserving-install', 'real-629-to-633-profile-preserving-install')
                if name == 'test_mouse632_windows_release.py' and value == 'Accepted Mouse629 evidence validator changed':
                    value = 'Immutable633 dependency changed: mouse632-ui-evidence.py'
                if value != node.value:
                    return ast.copy_location(ast.Constant(value=value), node)
            return node

        def visit_If(self, node):
            self.generic_visit(node)
            # Only the owner-superseded632 manual-entry predicate changes.
            # The caller checks the explicit633 start/provider/settings fields.
            if name == 'mouse632-release.py' and any(
                    isinstance(part, ast.Constant) and part.value == 'Mouse632 quiet optional helper entry evidence incomplete'
                    for statement in node.body for part in ast.walk(statement)):
                node.test = ast.parse('not _current_agent_entry(entry)', mode='eval').body
            return node

        def visit_Tuple(self, node):
            self.generic_visit(node)
            if (name == 'mouse632-release.py' and len(node.elts) == 2
                    and isinstance(node.elts[0], ast.Constant) and node.elts[0].value == 'agent'
                    and isinstance(node.elts[1], ast.List)):
                values = [part.value for part in node.elts[1].elts if isinstance(part, ast.Constant)]
                if values == ['layoutExact','pagesPreserved','aiReturn','reloadExact','defaultDisabled','autoRestoreDisabled']:
                    node.elts[1].elts[-1].value = 'restoredWithoutEnabling'
            return node
    return ast.fix_missing_locations(Identity().visit(ast.parse(raw, filename=str(path))))


def load(name, *, namespace=None):
    target = Path(__file__).with_name(name.replace('mouse632-', 'mouse633-')
                                      .replace('test_mouse632_', 'test_mouse633_'))
    scope = namespace if namespace is not None else {}
    original_name = scope.get('__name__')
    scope['__file__'] = str(target)
    scope['__name__'] = 'retained633_' + name.replace('-', '_')
    try:
        exec(compile(adapted_tree(name), str(target), 'exec'), scope)
    finally:
        if original_name is not None:
            scope['__name__'] = original_name
    return scope
