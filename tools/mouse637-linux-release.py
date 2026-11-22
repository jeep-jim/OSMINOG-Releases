#!/usr/bin/env python3
"""Reuse immutable635 algorithms with explicit636 runtime/module identities."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name("mouse637-reuse.py")))
_reuse["load"]('mouse635-linux-release.py',namespace=globals())

if __name__=="__main__":
 commands={"validate-template":validate_template,"import":import_candidate,"verify":verify_installed,"publish":publish,"channel":channel}
 if len(sys.argv)!=2 or sys.argv[1] not in commands: raise SystemExit("Expected a supported publisher action")
 if sys.argv[1] != 'validate-template':
  runpy.run_path(str(Path(__file__).with_name('mouse637-publish-plan.py')))['require_ready']('linux-x64')
 commands[sys.argv[1]]()
