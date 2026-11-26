#!/usr/bin/env python3
"""Synthetic decoded-PNG Nora contracts; never native publication evidence."""
import copy
from contextlib import redirect_stdout
import io
from pathlib import Path
import runpy
import unittest

TOOLS = Path(__file__).resolve().parent
with redirect_stdout(io.StringIO()):
    CURRENT = runpy.run_path(str(TOOLS / 'mouse640-evidence.py'))
    PREVIOUS = runpy.run_path(str(TOOLS / 'mouse637-evidence.py'))
    FIXTURES = runpy.run_path(str(TOOLS / 'test-mouse632-evidence.py'))

CONTRACT = 'integer-dom-native-endpoints-638'
PHASES = ('before', 'during', 'after')


def integer_slots(facts):
    row = facts['fractionalLayouts'][0]
    for phase in PHASES:
        for page, slot in zip(row[phase]['pages'], row[phase]['slots']):
            slot.update(page['bounds'])


class Nora638(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fractional, cls.blobs = FIXTURES['fractional_fixture']()

    def fixture(self):
        facts = copy.deepcopy(self.fractional)
        facts['version'] = '6.0.40'
        facts['fractionalLayouts'][0]['layoutContract'] = CONTRACT
        integer_slots(facts)
        return facts, self.blobs.copy()

    def check(self, facts, blobs):
        return CURRENT['verify_fractional_layouts'](blobs.__getitem__, facts)

    def test_integer_seven_panes_retain_all_real_png_checks_without_rewriting_bytes(self):
        facts, blobs = self.fixture()
        archived = blobs.copy()
        result = self.check(facts, blobs)
        self.assertEqual(result, {'layouts': 1, 'nativePanes': 7, 'endpointRoundingDifferences': 0,
                                 'frozenNativePngs': 7, 'frozenNativePixels': 21,
                                 'nativeForegroundPixels': 3, 'integerDOMPanes': 7})
        self.assertEqual(blobs, archived)
        self.assertEqual(CURRENT['verify_nora_foreground'](blobs.__getitem__, facts)['displayCaptures'], 7)

    def test_missing_or_wrong_explicit_source_contract_is_rejected(self):
        for receipt in (None, '', 'integer-dom-native-endpoints-637', True):
            facts, blobs = self.fixture()
            facts['fractionalLayouts'][0]['layoutContract'] = receipt
            with self.subTest(receipt=receipt), self.assertRaisesRegex(ValueError, 'contract'):
                self.check(facts, blobs)

    def test_each_dom_component_must_be_integer_even_if_rounded_native_bounds_match(self):
        for key in ('x', 'y', 'width', 'height'):
            facts, blobs = self.fixture()
            for phase in PHASES:
                facts['fractionalLayouts'][0][phase]['slots'][1][key] += .125
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'integers'):
                self.check(facts, blobs)

    def test_legacy_fractional_layout_cannot_pass_by_claiming_the638_contract(self):
        facts = copy.deepcopy(self.fractional)
        facts['version'] = '6.0.40'
        facts['fractionalLayouts'][0]['layoutContract'] = CONTRACT
        with self.assertRaisesRegex(ValueError, 'integers'):
            self.check(facts, self.blobs)

    def test_wrong_version_incomplete_restoration_or_recorded_error_is_rejected(self):
        for key, value in (('version', '6.0.38'), ('version', '6.0.32'), ('restored', False),
                           ('error', {'message': 'native failure'}), ('fractionalPending', {'before': {}})):
            facts, blobs = self.fixture()
            facts[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                self.check(facts, blobs)

    def test_exact971_viewport_and_seven_distinct_owners_are_still_required(self):
        for defect in ('viewport', 'missing-slot', 'duplicate-owner', 'duplicate-webcontents'):
            facts, blobs = self.fixture()
            row = facts['fractionalLayouts'][0]
            if defect == 'viewport':
                row['geometry']['viewport']['width'] = 972
            for phase in PHASES:
                if defect == 'missing-slot': row[phase]['slots'].pop()
                if defect == 'duplicate-owner': row[phase]['slots'][1]['id'] = row[phase]['slots'][0]['id']
                if defect == 'duplicate-webcontents': row[phase]['pages'][1]['webContentsId'] = row[phase]['pages'][0]['webContentsId']
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                self.check(facts, blobs)

    def test_actual_cached_and_child_native_geometry_remain_independent_checks(self):
        for field in ('bounds', 'cachedBounds', 'viewBounds', 'clipBounds'):
            facts, blobs = self.fixture()
            for phase in PHASES:
                facts['fractionalLayouts'][0][phase]['pages'][0][field]['width'] += 1
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.check(facts, blobs)

    def test_page_viewport_scroll_identity_and_root_order_must_be_preserved(self):
        for defect in ('guest-zoom', 'scroll', 'new-document', 'changed-during', 'root-order'):
            facts, blobs = self.fixture()
            row = facts['fractionalLayouts'][0]
            for phase in PHASES:
                page = row[phase]['pages'][0]
                if defect == 'guest-zoom': page['width'] = int(page['width'] / 1.25)
                if defect == 'scroll': page['scrollY'] += 1
                if defect == 'new-document': page['timeOrigin'] += 10
            if defect == 'changed-during': row['during']['pages'][0]['marker'] += .1
            if defect == 'root-order': row['after']['rootOrder'].reverse()
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                self.check(facts, blobs)

    def test_actual_native_visibility_and_foreground_probe_owner_are_still_required(self):
        for defect in ('visible', 'cached-visible', 'detached', 'wrong-probe'):
            facts, blobs = self.fixture()
            row = facts['fractionalLayouts'][0]
            if defect == 'visible': row['native'][1]['view'] = True
            if defect == 'cached-visible': row['native'][1]['cached'] = True
            if defect == 'detached': row['native'][1]['attached'] = False
            if defect == 'wrong-probe': row['samples'][0]['pageId'] = row['before']['pages'][-1]['id']
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                self.check(facts, blobs)

    def test_frozen_snapshot_inventory_hash_owner_and_actual_pixels_still_checked(self):
        for defect in ('missing', 'wrong-hash', 'wrong-owner', 'white-pixels'):
            facts, blobs = self.fixture()
            row = facts['fractionalLayouts'][0]
            snapshot = row['snapshots'][0]
            if defect == 'missing': row['snapshots'].pop()
            if defect == 'wrong-hash': snapshot['sha256'] = '0' * 64
            if defect == 'wrong-owner': snapshot['id'] = row['snapshots'][1]['id']
            if defect == 'white-pixels':
                raw = FIXTURES['png'](snapshot['naturalWidth'], snapshot['naturalHeight'], lambda x, y: (255, 255, 255, 255))
                blobs[snapshot['file']] = raw
                snapshot['sha256'] = FIXTURES['sha'](raw)
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                self.check(facts, blobs)

    def test_display_and_fresh_frame_evidence_are_not_optional(self):
        for defect in ('display-bytes', 'missing-readiness', 'foreign-fill'):
            facts, blobs = self.fixture()
            row = facts['fractionalLayouts'][0]
            if defect == 'display-bytes': blobs[row['capture']['source']] = b'not a PNG'
            if defect == 'missing-readiness': row.pop('readiness')
            if defect == 'foreign-fill': row['expected'] = [227, 31, 173]
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                self.check(facts, blobs)

    def test_frozen632_and637_keep_their_original_fractional_contract(self):
        for version, verify in (('6.0.32', FIXTURES['E'].verify_fractional_layouts),
                                ('6.0.37', PREVIOUS['verify_fractional_layouts'])):
            facts = copy.deepcopy(self.fractional)
            facts['version'] = version
            with self.subTest(version=version):
                self.assertGreater(verify(self.blobs.__getitem__, facts)['endpointRoundingDifferences'], 0)
                integer_slots(facts)
                facts['fractionalLayouts'][0]['layoutContract'] = CONTRACT
                with self.assertRaisesRegex(ValueError, 'independent-span'):
                    verify(self.blobs.__getitem__, facts)


if __name__ == '__main__':
    unittest.main()
