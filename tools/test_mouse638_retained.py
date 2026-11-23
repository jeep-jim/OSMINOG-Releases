#!/usr/bin/env python3
"""Run immutable predecessor mutation suites against638 retained checkers.

These are explicitly synthetic tests. Version/predecessor labels and the new
one-pixel square separator are the only fixture adaptations; no native result
is created by this suite.
"""
import ast
import hashlib
import json
from pathlib import Path
import types
import unittest

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
            def visit_Constant(self, node):
                if isinstance(node.value, bytes):
                    value = node.value.replace(b'6.0.37', b'6.0.38').replace(b'6.0.36', b'6.0.37')
                    return ast.copy_location(ast.Constant(value), node)
                if not isinstance(node.value, str):
                    return node
                value = node.value.replace('6.0.37', '6.0.38').replace('6.0.36', '6.0.37')
                for filename in FROZEN:
                    if filename.startswith('mouse637-'):
                        value = value.replace(filename, filename.replace('mouse637-', 'mouse638-'))
                value = value.replace('7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3', '0021084ccb9537e657d21e6f0c8e812dee6b461f')
                value = value.replace('MOUSE_637_REAL_636_TO_637_', 'MOUSE_638_REAL_637_TO_638_').replace('updateFrom636', 'updateFrom637')
                value = value.replace('legacy636-update', 'legacy637-update')
                return ast.copy_location(ast.Constant(value), node)

            def visit_Call(self, node):
                node = self.generic_visit(node)
                if (name == 'test_mouse637_current_acceptance.py'
                        and isinstance(node.func, ast.Attribute) and node.func.attr == 'assertEqual'
                        and len(node.args) == 2 and ast.unparse(node.args[0]) == 'len(seen)'
                        and isinstance(node.args[1], ast.Constant) and node.args[1].value == 10):
                    #638 adds three source Git-blob checked helpers.
                    node.args[1] = ast.copy_location(ast.Constant(13), node.args[1])
                return node

            def visit_IfExp(self, node):
                node = self.generic_visit(node)
                if (isinstance(node.body, ast.Constant) and node.body.value == 0
                        and isinstance(node.orelse, ast.Constant) and node.orelse.value == 6
                        and ast.unparse(node.test) == "mode == 'square'"):
                    node.body = ast.copy_location(ast.Constant(1), node.body)
                return node

        module = types.ModuleType('retained638_' + name[:-3])
        module.__file__ = str(TOOLS / name)
        exec(compile(ast.fix_missing_locations(FixtureIdentity().visit(tree)), module.__file__, 'exec'), module.__dict__)
        result.addTests(loader.loadTestsFromModule(module))
    return result


if __name__ == '__main__':
    unittest.main()
