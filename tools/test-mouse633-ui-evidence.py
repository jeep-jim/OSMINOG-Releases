#!/usr/bin/env python3
"""Run retained rejection fixtures against actual633 functions; no native claims."""
import runpy
from pathlib import Path
import unittest
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))
_tests = _reuse['load']('test-mouse632-ui-evidence.py', namespace=globals())
globals().update({key: value for key, value in _tests.items() if not key.startswith('__')})

def assert_expanded_algorithm_identity(self):
    import ast
    original = ast.parse(Path(__file__).with_name('mouse632-ui-evidence.py').read_text())
    current = _reuse['adapted_tree']('mouse632-ui-evidence.py')
    # All function bodies and control flow must stay identical after restoring
    # explicitly allowed runtime/versioned-module string identities.
    class Restore(ast.NodeTransformer):
        def visit_Constant(self, node):
            if isinstance(node.value, str):
                node.value = node.value.replace('6.0.33', '6.0.32').replace('mouse633-', 'mouse632-')
            return node
    before = {node.name: ast.dump(node) for node in original.body if isinstance(node, ast.FunctionDef)}
    after = {node.name: ast.dump(Restore().visit(node)) for node in current.body if isinstance(node, ast.FunctionDef)}
    self.assertEqual(before, after)

AcceptedAlgorithmMigrationTests.test_all_accepted_algorithms_only_change_runtime_versions_and_label = assert_expanded_algorithm_identity

if __name__ == '__main__':
    unittest.main()
