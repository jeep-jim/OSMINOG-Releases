#!/usr/bin/env python3
"""Retain the immutable acceptance lineage for current Mac 6.0.43."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("mouse643-reuse.py")))["execute"]('mouse637-update-button-evidence.py', globals())
