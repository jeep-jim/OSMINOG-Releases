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

class RetainedNativeScrollbarRouteTests(unittest.TestCase):
    """Synthetic input with literal producer routes, outside the AST adapter."""

    def setUp(self):
        self.rows = encapsulated_fixture()
        self.fixture = {'url': 'http://127.0.0.1:58856/mouse629-scrollbars', 'desktop': 'desk-a'}
        for row in self.rows:
            # These exact route names are emitted by the retained native smoke.
            # Do not derive them from transformed fixtures or checker constants.
            row['pageURL'] = 'http://127.0.0.1:58856/mouse632-encapsulated'
            row['frameURL'] = (
                'http://127.0.0.1:58856/mouse632-frame' if row['kind'] == 'same-frame' else
                'http://127.0.0.1:58855/mouse632-cross-frame' if row['kind'] == 'cross-frame' else None)

    def verify(self):
        return evidence.verify_encapsulated_scrollbars(self.rows, self.fixture)

    def test_literal_retained_producer_routes_pass_current_runtime_checker(self):
        self.assertEqual(self.verify(), 8)

    def test_different_guest_origin_is_still_rejected(self):
        self.rows[0]['pageURL'] = 'http://127.0.0.1:58857/mouse632-encapsulated'
        with self.assertRaisesRegex(ValueError, 'different guest'):
            self.verify()

    def test_same_frame_requires_the_exact_guest_origin(self):
        self.rows[2]['frameURL'] = 'http://127.0.0.1:58857/mouse632-frame'
        with self.assertRaisesRegex(ValueError, 'same-origin frame'):
            self.verify()

    def test_cross_frame_cannot_use_the_guest_origin(self):
        self.rows[3]['frameURL'] = 'http://127.0.0.1:58856/mouse632-cross-frame'
        with self.assertRaisesRegex(ValueError, 'cross-origin frame'):
            self.verify()

    def test_invented_633_routes_are_rejected_for_all_three_identities(self):
        cases = (
            (0, 'pageURL', 'http://127.0.0.1:58856/mouse633-encapsulated', 'different guest'),
            (2, 'frameURL', 'http://127.0.0.1:58856/mouse633-frame', 'same-origin frame'),
            (3, 'frameURL', 'http://127.0.0.1:58855/mouse633-cross-frame', 'cross-origin frame'))
        for index, key, value, message in cases:
            original = self.rows[index][key]
            self.rows[index][key] = value
            with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, message):
                self.verify()
            self.rows[index][key] = original


if __name__ == '__main__':
    unittest.main()
