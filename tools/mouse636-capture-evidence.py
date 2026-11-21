#!/usr/bin/env python3
"""Reuse immutable635 algorithms with explicit636 runtime/module identities."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name("mouse636-reuse.py")))
_reuse["load"]('mouse635-capture-evidence.py',namespace=globals())
