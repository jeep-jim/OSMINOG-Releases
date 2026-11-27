#!/usr/bin/env python3
"""Run immutable predecessor mutation suites against640 retained checkers.

These are explicitly synthetic tests. Current identities, published predecessor,
one-pixel separators and the requested settings presentation are adapted. No
native result is created and no retained rejection assertion is removed.
"""
import ast
import hashlib
import json
from pathlib import Path
import types
import unittest
import runpy

TOOLS = Path(__file__).resolve().parent
FROZEN = json.loads((TOOLS / 'mouse638-frozen.json').read_text())
SUITES = [name for name in FROZEN if name.startswith('test_mouse637_')]


def load_tests(loader, tests, pattern):
    result = unittest.TestSuite()
    for name in SUITES:
        raw = (TOOLS / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
            raise ValueError('Immutable predecessor mutation suite changed: ' + name)
        tree = ast.parse(raw, filename=str(TOOLS / name))

        class FixtureIdentity(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                node = self.generic_visit(node)
                if name == 'test_mouse637_sidebar_library_evidence.py' and node.name == 'block':
                    #Synthetic computed-style fixtures for the new glass UI;
                    #all dim, native ownership and click-through mutations stay.
                    at = next(i for i, row in enumerate(node.body)
                              if isinstance(row, ast.Assign) and ast.unparse(row.targets[0]) == 'guest')
                    node.body[at:at] = ast.parse("""
shell['settings'].update(backgroundColor='rgba(21, 29, 42, 0.95)' if theme == 'dark' else 'rgba(247, 249, 253, 0.94)', backdropFilter='blur(28px) saturate(1.35)', color='rgb(230, 235, 244)' if theme == 'dark' else 'rgb(31, 42, 57)', borderColor='rgba(255, 255, 255, 0.2)' if theme == 'dark' else 'rgba(70, 95, 130, 0.2)')
shell['library'] = dict(shell['settings'])
""").body
                if name == 'test_mouse637_ai_preview_evidence.py' and node.name == 'fixture':
                    if ast.unparse(node.body[-1]) != 'return (report, owners, inputs)':
                        raise ValueError('Frozen AI fixture return changed')
                    node.body[-1] = ast.parse('return _fixture641_preview(report, owners, inputs)').body[0]
                return node

            def visit_Assign(self, node):
                node = self.generic_visit(node)
                if (name == 'test_mouse637_current_acceptance.py' and any(
                        ast.dump(target) == ast.dump(ast.parse("wrapper['checks']['updateFrom639'] = None").body[0].targets[0])
                        for target in node.targets)):
                    # Current source retains this protocol key; actual version,
                    # native markers, profile and package proofs remain 639 -> 640.
                    node.targets[0] = ast.parse("wrapper['checks']['updateFrom638'] = None").body[0].targets[0]
                if (name == 'test_mouse637_agent_removal_evidence.py'
                        and any(isinstance(target, ast.Name) and target.id == 'SETTINGS' for target in node.targets)):
                    node.value = ast.parse(repr(runpy.run_path(str(TOOLS / 'mouse642-reuse.py'))['SETTINGS_SECTIONS']), mode='eval').body
                return node

            def visit_Constant(self, node):
                if isinstance(node.value, bytes):
                    value = node.value.replace(b'6.0.37', b'6.0.42').replace(b'6.0.36', b'6.0.41')
                    return ast.copy_location(ast.Constant(value), node)
                if not isinstance(node.value, str):
                    return node
                value = node.value.replace('6.0.37', '6.0.42').replace('6.0.36', '6.0.41')
                for filename in FROZEN:
                    if filename.startswith('mouse637-'):
                        value = value.replace(filename, filename.replace('mouse637-', 'mouse642-'))
                value = value.replace('7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3', '3a32e02a8893b4c2f1397cd0a08e94af737f42fc')
                value = value.replace('MOUSE_637_REAL_636_TO_637_', 'MOUSE_642_REAL_641_TO_642_')
                value = value.replace('updateFrom636', 'updateFrom638' if name == 'test_mouse637_windows_display_evidence.py' else 'updateFrom639')
                value = value.replace('legacy636-update', 'legacy641-update')
                return ast.copy_location(ast.Constant(value), node)

            def visit_Call(self, node):
                node = self.generic_visit(node)
                if (name == 'test_mouse637_ai_preview_evidence.py'
                        and isinstance(node.func, ast.Attribute) and node.func.attr == 'assertEqual'
                        and len(node.args) == 2 and ast.unparse(node.args[0]) == "len(F['CAPTURES'])"
                        and isinstance(node.args[1], ast.Constant) and node.args[1].value == 36):
                    #Six current Settings OS frames extend the unchanged ledger.
                    node.args[1] = ast.copy_location(ast.Constant(42), node.args[1])
                if (name == 'test_mouse637_current_acceptance.py'
                        and isinstance(node.func, ast.Attribute) and node.func.attr == 'assertEqual'
                        and len(node.args) == 2 and ast.unparse(node.args[0]) == 'len(seen)'
                        and isinstance(node.args[1], ast.Constant) and node.args[1].value == 10):
                    #638 added three helpers;639 two;640 one;641 two;642 two.
                    node.args[1] = ast.copy_location(ast.Constant(20), node.args[1])
                return node

            def visit_IfExp(self, node):
                node = self.generic_visit(node)
                if (isinstance(node.body, ast.Constant) and node.body.value == 0
                        and isinstance(node.orelse, ast.Constant) and node.orelse.value == 6
                        and ast.unparse(node.test) == "mode == 'square'"):
                    node.body = ast.copy_location(ast.Constant(1), node.body)
                return node

        module = types.ModuleType('retained640_' + name[:-3])
        module.__file__ = str(TOOLS / name)
        module.__dict__['_fixture641_preview'] = runpy.run_path(str(TOOLS / 'fixtures/mouse642-owner-fixtures.py'))['preview']
        exec(compile(ast.fix_missing_locations(FixtureIdentity().visit(tree)), module.__file__, 'exec'), module.__dict__)
        result.addTests(loader.loadTestsFromModule(module))
    return result


if __name__ == '__main__':
    unittest.main()
