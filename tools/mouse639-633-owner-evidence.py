#!/usr/bin/env python3
"""Reuse the immutable predecessor checker for the reviewed638 identity."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("mouse639-reuse.py")))["execute"]('mouse637-633-owner-evidence.py', globals())
