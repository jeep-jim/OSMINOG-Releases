#!/usr/bin/env python3
"""Retain byte-frozen634 algorithms with explicit635 identities."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name("mouse635-reuse.py")))
_reuse["load"]('test_mouse634_release_bytes.py',namespace=globals())

if __name__=="__main__":
 import unittest
 unittest.main()
