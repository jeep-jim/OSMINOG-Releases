#!/usr/bin/env python3
"""Synthetic641 geometry regressions; installed raw evidence stays mandatory."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parent
REUSE = runpy.run_path(str(TOOLS / 'mouse642-reuse.py'))
OLD = runpy.run_path(str(TOOLS / 'mouse637-library-evidence.py'))
CURRENT = runpy.run_path(str(TOOLS / 'mouse642-library-evidence.py'))
OWNER = runpy.run_path(str(TOOLS / 'mouse642-owner-feedback-evidence.py'))


def fixture(view='list', width=348, *, legacy=False):
    copies = ['owned-copy-' + str(index) for index in range(15)]
    rows = []
    grid = view == 'grid'
    height = 156 if grid else (126 if legacy else 130)
    for index, identifier in enumerate(copies[:14]):
        x, y = -17.25, 200.125 + index * height
        row_width = 176 if grid else width
        dx, dy = (10, 34) if grid else ((6, 9) if legacy else (10, 11))
        reduction = 20 if grid else (37 if legacy else 46)
        rows.append({
            'id': identifier,
            'row': {'x': x, 'y': y, 'width': row_width, 'height': height},
            'image': {'x': x + dx, 'y': y + dy, 'width': row_width - reduction,
                      'height': 112 if grid else 108},
            'checkbox': {'x': x + row_width - 28, 'y': y + 55, 'width': 18, 'height': 18},
            'thumbnail': False, 'decoded': False,
        })
    before = {'kind': 'captures', 'view': view, 'scrollTop': 200, 'rows': rows}
    after = copy.deepcopy(before)
    delayed = copies[:9]
    for row in after['rows']:
        if row['id'] in delayed:
            row.update(thumbnail=True, decoded=True)
    return {'controlledDelay': True, 'before': before, 'after': after,
            'delayedIds': delayed, 'requestSequences': list(range(1, len(delayed) + 1))}, copies


def both(receipt, box, key, delta):
    """Wrong reserved geometry must fail even when before/after are identical."""
    for stage in ('before', 'after'):
        receipt[stage]['rows'][0][box][key] += delta


def function(tree, name):
    return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)


class CurrentLibraryGeometry(unittest.TestCase):
    def test_641_list_geometry_tracks_actual_row_width(self):
        for width in (280, 348, 360.5, 420):
            receipt, copies = fixture(width=width)
            with self.subTest(width=width):
                self.assertEqual(CURRENT['placeholder_geometry'](receipt, 'list', copies),
                                 list(zip(receipt['requestSequences'], receipt['delayedIds'])))

    def test_genuine_637_and_641_reject_each_others_list_geometry(self):
        for reader, legacy in ((OLD, True), (CURRENT, False)):
            receipt, copies = fixture(legacy=legacy)
            with self.subTest(reader='637' if legacy else '641'):
                reader['placeholder_geometry'](receipt, 'list', copies)
                wrong, copies = fixture(legacy=not legacy)
                with self.assertRaisesRegex(ValueError, 'preview did not reserve'):
                    reader['placeholder_geometry'](wrong, 'list', copies)

    def test_stable_wrong_current_dimensions_are_rejected(self):
        for box, key in (('image', 'x'), ('image', 'y'), ('image', 'width'),
                         ('image', 'height'), ('row', 'height')):
            for delta in (-1.01, 1.01):
                receipt, copies = fixture()
                both(receipt, box, key, delta)
                with self.subTest(box=box, key=key, delta=delta), \
                        self.assertRaisesRegex(ValueError, 'preview did not reserve'):
                    CURRENT['placeholder_geometry'](receipt, 'list', copies)
        receipt, copies = fixture()
        for stage in ('before', 'after'):
            receipt[stage]['rows'][0]['image'].update(width=30, height=30)
        with self.assertRaisesRegex(ValueError, 'preview did not reserve'):
            CURRENT['placeholder_geometry'](receipt, 'list', copies)

    def test_exact_one_pixel_tolerance_is_retained(self):
        for box, key in (('image', 'x'), ('image', 'y'), ('image', 'width'),
                         ('image', 'height'), ('row', 'height')):
            for delta in (-1, 1):
                receipt, copies = fixture()
                both(receipt, box, key, delta)
                with self.subTest(box=box, key=key, delta=delta):
                    CURRENT['placeholder_geometry'](receipt, 'list', copies)

    def test_grid_retains_112_height_and_one_pixel_tolerance(self):
        for reader in (OLD, CURRENT):
            for delta in (-1, 0, 1, -1.01, 1.01):
                receipt, copies = fixture('grid')
                both(receipt, 'image', 'height', delta)
                with self.subTest(reader=reader['__file__'], delta=delta):
                    if abs(delta) <= 1:
                        reader['placeholder_geometry'](receipt, 'grid', copies)
                    else:
                        with self.assertRaisesRegex(ValueError, 'preview did not reserve'):
                            reader['placeholder_geometry'](receipt, 'grid', copies)
        self.assertFalse(CURRENT['_placeholder_size'](fixture()[0]['before']['rows'][0], 'tiles'))

    def test_row_image_and_checkbox_motion_is_still_rejected(self):
        for box in ('row', 'image', 'checkbox'):
            for key in ('x', 'y', 'width', 'height'):
                receipt, copies = fixture()
                receipt['after']['rows'][0][box][key] += 1
                with self.subTest(box=box, key=key, delta=1):
                    CURRENT['placeholder_geometry'](receipt, 'list', copies)
                receipt['after']['rows'][0][box][key] += .01
                with self.subTest(box=box, key=key, delta=1.01), \
                        self.assertRaisesRegex(ValueError, 'preview completion moved a row, image or checkbox'):
                    CURRENT['placeholder_geometry'](receipt, 'list', copies)

    def test_empty_or_nonfinite_bounds_are_rejected(self):
        for box in ('row', 'image', 'checkbox'):
            for key, value in (('width', 0), ('height', 0), ('x', float('nan')), ('y', float('inf'))):
                receipt, copies = fixture()
                for stage in ('before', 'after'):
                    receipt[stage]['rows'][0][box][key] = value
                with self.subTest(box=box, key=key, value=value), \
                        self.assertRaisesRegex(ValueError, 'placeholder controls have missing or empty bounds'):
                    CURRENT['placeholder_geometry'](receipt, 'list', copies)

    def test_identity_delay_decode_scroll_and_request_guards_are_retained(self):
        mutations = [
            (lambda r: r.update(controlledDelay=False), 'actual delayed preview geometry'),
            (lambda r: r['after'].update(view='grid'), 'another library mode'),
            (lambda r: r['after'].update(scrollTop=201.01), 'moved the list scroll'),
            (lambda r: r['after']['rows'].pop(), 'all fourteen image rows'),
            (lambda r: r['after']['rows'].reverse(), 'replaced, reordered or omitted'),
            (lambda r: r['after']['rows'][0].update(id='another-file'), 'replaced, reordered or omitted'),
            (lambda r: r['requestSequences'].__setitem__(1, 1), 'request sequence binding'),
            (lambda r: r['requestSequences'].__setitem__(1, 0), 'request sequence binding'),
            (lambda r: r['requestSequences'].pop(), 'request sequence binding'),
            (lambda r: r['before']['rows'][8].update(thumbnail=True), 'held placeholder'),
            (lambda r: r['after']['rows'][8].update(decoded=False), 'held placeholder'),
            (lambda r: r['before']['rows'][8].update(decoded=None), 'image state missing'),
            (lambda r: r['delayedIds'].__setitem__(0, 'unowned'), 'viewed owned capture'),
        ]
        for number, (mutate, message) in enumerate(mutations):
            receipt, copies = fixture()
            mutate(receipt)
            with self.subTest(mutation=number), self.assertRaisesRegex(ValueError, message):
                CURRENT['placeholder_geometry'](receipt, 'list', copies)
        receipt, copies = fixture()
        receipt['delayedIds'].pop()
        receipt['requestSequences'].pop()
        with self.assertRaisesRegex(ValueError, 'viewed owned capture'):
            CURRENT['placeholder_geometry'](receipt, 'list', copies)

    def test_full_owner_and_library_callers_bind_the_current_geometry(self):
        library = OWNER['verify'].__globals__['L']
        self.assertEqual(Path(library['__file__']).name, 'mouse642-library-evidence.py')
        for reader in (CURRENT, library):
            geometry = reader['verify'].__globals__['placeholder_geometry']
            self.assertIs(geometry, reader['placeholder_geometry'])
            self.assertIs(geometry.__globals__['_placeholder_size'], reader['_placeholder_size'])
            receipt, copies = fixture()
            geometry(receipt, 'list', copies)
            old, copies = fixture(legacy=True)
            with self.assertRaisesRegex(ValueError, 'preview did not reserve'):
                geometry(old, 'list', copies)

    def test_only_size_helper_changes_in_retained_geometry_predicate(self):
        previous = REUSE['legacy']()['adapted_tree']('mouse637-library-evidence.py')
        current = REUSE['adapted_tree']('mouse637-library-evidence.py')
        self.assertEqual(ast.dump(function(previous, 'placeholder_geometry'), include_attributes=False),
                         ast.dump(function(current, 'placeholder_geometry'), include_attributes=False))

    def test_adaptation_rejects_changed_missing_or_duplicate_frozen_size_helper(self):
        original = REUSE['legacy']()['adapted_tree']('mouse637-library-evidence.py')
        for defect in ('changed', 'missing', 'duplicate'):
            tree = copy.deepcopy(original)
            target = function(tree, '_placeholder_size')
            if defect == 'changed':
                number = next(node for node in ast.walk(target)
                              if isinstance(node, ast.Constant) and node.value == 112)
                number.value = 113
            elif defect == 'missing':
                tree.body.remove(target)
            else:
                tree.body.append(copy.deepcopy(target))
            with self.subTest(defect=defect), \
                    patch.dict(REUSE['adapted_tree'].__globals__, {
                        'legacy': lambda: {'adapted_tree': lambda *args, **kwargs: copy.deepcopy(tree)}}), \
                    self.assertRaisesRegex(ValueError, 'frozen|Frozen'):
                REUSE['adapted_tree']('mouse637-library-evidence.py')

    def test_current_schema_describes_geometry_and_binds_the_adapter(self):
        schema = json.loads((TOOLS.parent / 'staging/mouse/6.0.42-arm64/evidence.schema.json').read_text())
        gate = schema['x-libraryStabilityGate']
        expected = {'placeholderGeometryToleranceCSSPixels': 1,
                    'placeholderListImageHeight': 108, 'placeholderGridImageHeight': 112,
                    'placeholderListImageOffsetX': 10, 'placeholderListImageOffsetY': 11,
                    'placeholderListImageWidthReduction': 46, 'placeholderListRowHeight': 130}
        self.assertEqual({key: gate.get(key) for key in expected}, expected)
        self.assertEqual(gate['sha256'], hashlib.sha256((TOOLS / 'mouse642-library-evidence.py').read_bytes()).hexdigest())
        digest = hashlib.sha256((TOOLS / 'mouse642-reuse.py').read_bytes()).hexdigest()
        references = [value['dependencies']['mouse642-reuse.py'] for value in schema.values()
                      if isinstance(value, dict) and 'mouse642-reuse.py' in value.get('dependencies', {})]
        self.assertEqual(references, [digest] * 7)


if __name__ == '__main__':
    unittest.main()
