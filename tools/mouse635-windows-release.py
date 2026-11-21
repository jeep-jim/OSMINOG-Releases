#!/usr/bin/env python3
"""Retain byte-frozen634 algorithms with explicit635 identities."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name("mouse635-reuse.py")))
_reuse["load"]('mouse634-windows-release.py',namespace=globals())

if __name__=="__main__":
 commands={"import":import_candidate,"verify":verify_installed,"publish":publish,"channel":channel}
 if len(sys.argv)!=2 or sys.argv[1] not in commands: raise SystemExit("Expected import, verify, publish or channel")
 commands[sys.argv[1]]()
