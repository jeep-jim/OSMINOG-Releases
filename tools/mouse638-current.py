#!/usr/bin/env python3
"""Reuse the immutable predecessor checker for the reviewed638 identity."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("mouse638-reuse.py")))["execute"]('mouse637-current.py', globals())

# All helper bytes are fetched from the accepted source commit and Git-blob checked.
HELPERS += ('mouse-638-feedback-run.py', 'mouse-638-acceptance.py', 'mouse-638-crx-proof.cjs')
