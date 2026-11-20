#!/usr/bin/env python3
"""Run retained rejection fixtures against actual633 functions; no native claims."""
import runpy
from pathlib import Path
import unittest
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))
_tests = _reuse['load']('test_mouse632_task_evidence.py', namespace=globals())
globals().update({key: value for key, value in _tests.items() if not key.startswith('__')})
if __name__ == '__main__':
    unittest.main()
