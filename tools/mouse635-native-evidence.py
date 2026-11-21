#!/usr/bin/env python3
"""New635 OS-frame primitive, retaining all634 crop and byte predicates."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name("mouse635-reuse.py")))
_reuse["load"]("mouse634-native-evidence.py",namespace=globals(),current_native=True)
