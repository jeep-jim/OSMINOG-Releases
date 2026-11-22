#!/usr/bin/env python3
"""Synthetic geometry mutations; actual OS evidence remains mandatory."""
import ast
import copy
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).parent
L = runpy.run_path(str(ROOT / 'mouse637-library-evidence.py'))


def fixture(view='list', width=360):
    copies = ['owned-copy-' + str(index) for index in range(15)]
    rows = []
    for index, identifier in enumerate(copies[:14]):
        x, y = 100, 200 + index * (126 if view == 'list' else 156)
        grid = view == 'grid'
        row_width = 176 if grid else width
        rows.append({'id': identifier, 'row': {'x': x, 'y': y, 'width': row_width, 'height': 156 if grid else 126},
                     'image': {'x': x + (10 if grid else 6), 'y': y + (34 if grid else 9),
                               'width': row_width - (20 if grid else 37), 'height': 112 if grid else 108},
                     'checkbox': {'x': x + row_width - (26 if grid else 23), 'y': y + (10 if grid else 55),
                                  'width': 16, 'height': 16}, 'thumbnail': False, 'decoded': False})
    before = {'kind': 'captures', 'view': view, 'scrollTop': 200, 'rows': rows}
    after = copy.deepcopy(before)
    delayed = copies[:12 if view == 'grid' else 9]
    for row in after['rows']:
        if row['id'] in delayed: row.update(thumbnail=True, decoded=True)
    return {'controlledDelay': True, 'before': before, 'after': after, 'delayedIds': delayed,
            'requestSequences': list(range(1, len(delayed) + 1))}, copies


class CurrentLibraryGeometry(unittest.TestCase):
    def test_current_list_geometry_follows_actual_row_width(self):
        for width in (280, 360, 420):
            receipt, copies = fixture(width=width)
            with self.subTest(width=width):
                self.assertEqual(L['placeholder_geometry'](receipt, 'list', copies),
                                 list(zip(receipt['requestSequences'], receipt['delayedIds'])))

    def test_grid_retains_its_existing_112_pixel_contract(self):
        receipt, copies = fixture('grid')
        L['placeholder_geometry'](receipt, 'grid', copies)
        for stage in ('before', 'after'): receipt[stage]['rows'][0]['image']['height'] = 110
        with self.assertRaises(ValueError): L['placeholder_geometry'](receipt, 'grid', copies)

    def test_stable_but_wrong_current_list_dimensions_are_rejected(self):
        for box, key in (('image', 'width'), ('image', 'height'), ('image', 'x'), ('image', 'y'), ('row', 'height')):
            receipt, copies = fixture()
            for stage in ('before', 'after'): receipt[stage]['rows'][0][box][key] += 2
            with self.subTest(box=box, key=key), self.assertRaises(ValueError):
                L['placeholder_geometry'](receipt, 'list', copies)
        receipt, copies = fixture()
        for stage in ('before', 'after'): receipt[stage]['rows'][0]['image'].update(width=30, height=30)
        with self.assertRaises(ValueError): L['placeholder_geometry'](receipt, 'list', copies)

    def test_original_identity_delay_decode_scroll_and_stability_checks_remain(self):
        mutations = [lambda r: r.update(controlledDelay=False),
                     lambda r: r['after'].update(view='grid'),
                     lambda r: r['after'].update(scrollTop=r['before']['scrollTop'] + 2),
                     lambda r: r['after']['rows'].pop(), lambda r: r['after']['rows'].reverse(),
                     lambda r: r['after']['rows'][0].update(id='another-file'),
                     lambda r: r['requestSequences'].__setitem__(1, r['requestSequences'][0]),
                     lambda r: r['before']['rows'][8].update(thumbnail=True),
                     lambda r: r['after']['rows'][8].update(decoded=False),
                     lambda r: r['after']['rows'][8]['row'].update(y=r['before']['rows'][8]['row']['y'] + 2),
                     lambda r: r['after']['rows'][8]['image'].update(width=r['before']['rows'][8]['image']['width'] + 2),
                     lambda r: r['after']['rows'][8]['checkbox'].update(x=r['before']['rows'][8]['checkbox']['x'] + 2),
                     lambda r: r['after']['rows'][8]['checkbox'].update(height=0)]
        for number, mutate in enumerate(mutations):
            receipt, copies = fixture(); mutate(receipt)
            with self.subTest(mutation=number), self.assertRaises(ValueError):
                L['placeholder_geometry'](receipt, 'list', copies)
        receipt, copies = fixture()
        receipt['delayedIds'].pop(); receipt['requestSequences'].pop()
        with self.assertRaises(ValueError): L['placeholder_geometry'](receipt, 'list', copies)

    def test_full_retained_gate_uses_override_with_only_geometry_predicate_changed(self):
        self.assertIs(L['verify'].__globals__['placeholder_geometry'], L['placeholder_geometry'])
        functions = []
        for name in ('mouse635-library-evidence.py', 'mouse637-library-evidence.py'):
            tree = ast.parse((ROOT / name).read_text())
            function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'placeholder_geometry')
            calls = [node for node in ast.walk(function) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                     and node.func.id == 'need' and len(node.args) == 2 and isinstance(node.args[1], ast.Constant)
                     and node.args[1].value == 'preview did not reserve its actual list/grid dimensions']
            self.assertEqual(len(calls), 1)
            calls[0].args[0] = ast.Constant(True)
            functions.append(ast.dump(function, include_attributes=False))
        self.assertEqual(*functions)


if __name__ == '__main__':
    unittest.main()
