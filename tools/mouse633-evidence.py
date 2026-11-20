#!/usr/bin/env python3
"""The immutable632 evidence algorithm, rerun against633 runtime facts."""
import runpy
from pathlib import Path
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))
_retained = _reuse['load']('mouse632-evidence.py', namespace=globals())
globals().update({key: value for key, value in _retained.items() if not key.startswith('__')})
