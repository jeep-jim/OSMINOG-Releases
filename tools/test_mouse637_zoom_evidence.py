#!/usr/bin/env python3
"""Synthetic pixel contracts for the scoped637 dim; never native completion."""
import ast
import copy
import hashlib
from pathlib import Path
import runpy
import struct
import unittest
import zlib

TOOLS = Path(__file__).resolve().parent
REUSE = runpy.run_path(str(TOOLS / 'mouse637-reuse.py'))
CURRENT = runpy.run_path(str(TOOLS / 'mouse637-633-owner-evidence.py'))
FROZEN = runpy.run_path(str(TOOLS / 'mouse633-owner-feedback-evidence.py'))
FIXTURE = runpy.run_path(str(TOOLS / 'test_mouse633_owner_feedback_evidence.py'))
ZOOM = runpy.run_path(str(TOOLS / 'mouse637-zoom-evidence.py'))


def png(width, height, marker, color, holes=False):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    pixels = bytearray(bytes((238, 238, 238, 255)) * width * height)
    left, top, w, h = (marker[key] for key in ('x', 'y', 'width', 'height'))
    for y in range(top, top + h):
        for x in range(left, left + w):
            if holes and (x + y) % 2:
                continue
            pixels[(y * width + x) * 4:(y * width + x + 1) * 4] = bytes((*color, 255))
    raw = b''.join(b'\0' + pixels[y * width * 4:(y + 1) * width * 4] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


class RetainedZoomPresentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.original = FIXTURE['fixture']()

    def case(self, kind, phase='before', *, color=None, width_delta=0, holes=False):
        row = copy.deepcopy(self.original['zoom'][kind][phase]['pages'][0])
        owner = copy.deepcopy(self.original['settings']['livePages']['before'][0])
        expected = ZOOM['DIMMED'] if kind == 'settings' else ZOOM['ORIGINAL']
        row['presentation'] = {'kind': kind, 'dimmed': kind == 'settings', 'expectedRGB': list(expected)}
        row['meter']['width'] += width_delta
        row['meter']['count'] = row['meter']['width'] * row['meter']['height']
        if holes:
            row['meter']['count'] //= 2
        raw = png(200, 300, row['meter'], expected if color is None else color, holes)
        row.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        return raw, row, owner

    def check(self, case, *, frozen=False):
        raw, row, owner = case
        validator = FROZEN if frozen else CURRENT
        return validator['guest_capture']({row['filename']: raw}.__getitem__, row, owner, row['factor'])

    def test_both_zoom_controls_and_phases_use_their_own_exact_pixels(self):
        self.assertEqual(ZOOM['DIMMED'], (202, 34, 133))
        for kind in ('popover', 'settings'):
            for phase in ('before', 'after'):
                with self.subTest(kind=kind, phase=phase):
                    case = self.case(kind, phase)
                    self.assertEqual(self.check(case), case[1]['meter'])
        self.assertEqual(self.check(self.case('popover'), frozen=True), self.case('popover')[1]['meter'])
        with self.assertRaisesRegex(ValueError, 'decoded live page meter'):
            self.check(self.case('settings'), frozen=True)

    def test_old_settings_pixels_or_dimmed_popover_cannot_be_accepted(self):
        for kind, wrong in [('settings', ZOOM['ORIGINAL']), ('popover', ZOOM['DIMMED'])]:
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'decoded live page meter'):
                self.check(self.case(kind, color=wrong))

    def test_color_is_derived_from_bound_filename_not_report_choice(self):
        for mutate in [lambda r: r['presentation'].update(expectedRGB=list(ZOOM['ORIGINAL'])),
                       lambda r: r['presentation'].update(dimmed=False),
                       lambda r: r['presentation'].update(dimmed=1),
                       lambda r: r['presentation'].update(kind='popover'),
                       lambda r: r.update(filename='mouse-633-zoom-settings-before-guest-2.png'),
                       lambda r: r.pop('presentation')]:
            case = self.case('settings')
            mutate(case[1])
            with self.assertRaisesRegex(ValueError, 'Mouse637 zoom presentation'):
                self.check(case)

    def test_rgb_tolerance_geometry_density_and_owner_remain_strict(self):
        near = tuple(channel + 2 for channel in ZOOM['DIMMED'])
        far = tuple(channel + 3 for channel in ZOOM['DIMMED'])
        self.check(self.case('settings', color=near))
        for case in (self.case('settings', color=far), self.case('settings', width_delta=-5), self.case('settings', holes=True)):
            with self.assertRaisesRegex(ValueError, 'decoded live page meter'):
                self.check(case)
        case = self.case('settings')
        case[1]['native']['webContentsId'] += 1
        with self.assertRaises(ValueError):
            self.check(case)

    def test_scoped_ast_keeps_entire_frozen_meter_and_guest_algorithm(self):
        old = ast.parse((TOOLS / 'mouse633-owner-feedback-evidence.py').read_bytes())
        current = REUSE['adapted_tree']('mouse633-owner-feedback-evidence.py')
        functions = lambda tree: {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        expected, actual = functions(old), functions(current)
        meter = copy.deepcopy(actual['meter'])
        self.assertEqual([arg.arg for arg in meter.args.kwonlyargs], ['expected_rgb'])
        meter.args.kwonlyargs.clear()
        meter.args.kw_defaults.clear()

        class RestorePalette(ast.NodeTransformer):
            def visit_Name(self, node):
                return ast.parse('(235,40,155)', mode='eval').body if node.id == 'expected_rgb' else node

        self.assertEqual(ast.dump(RestorePalette().visit(meter)), ast.dump(expected['meter']))
        guest = copy.deepcopy(actual['guest_capture'])

        class RestoreCall(ast.NodeTransformer):
            def visit_Call(self, node):
                node = self.generic_visit(node)
                if isinstance(node.func, ast.Name) and node.func.id == 'meter':
                    node.keywords.clear()
                return node

        self.assertEqual(ast.dump(RestoreCall().visit(guest)), ast.dump(expected['guest_capture']))
        for name in REUSE['FROZEN']:
            REUSE['checked'](name)


if __name__ == '__main__':
    unittest.main()
