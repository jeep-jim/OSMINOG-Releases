#!/usr/bin/env python3
"""Run retained rejection fixtures against actual633 functions; no native claims."""
import runpy
from pathlib import Path
import unittest
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))
_tests = _reuse['load']('test_mouse632_windows_release.py', namespace=globals())
globals().update({key: value for key, value in _tests.items() if not key.startswith('__')})
# Inherited draft/package tests already replace downstream owner/task facts.
# The added actual632 upgrade gate is independently exercised by its own suite.
_original_publication_setup = WindowsPublisherDraftPublication.setUp

def current_publication_setup(self):
    _original_publication_setup(self)
    gate = patch.dict(PUBLISHER['publish'].__globals__, _verify_current_upgrade=lambda read, p: {'unitOnly': True})
    gate.start()
    self.addCleanup(gate.stop)

WindowsPublisherDraftPublication.setUp = current_publication_setup

if __name__ == '__main__':
    unittest.main()
