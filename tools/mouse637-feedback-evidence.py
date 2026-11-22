#!/usr/bin/env python3
"""Retain byte-frozen636 gates with explicit637 runtime identities."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name("mouse637-reuse.py")))
_reuse["load"]('mouse636-feedback-evidence.py',namespace=globals())
