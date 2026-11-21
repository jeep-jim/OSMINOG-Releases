#!/usr/bin/env python3
"""Retained Linux native/sandbox gates plus both actual633 package upgrades."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name('mouse634-reuse.py')))
_retained=_reuse['load']('mouse633-linux-evidence.py',namespace=globals())
globals().update({key:value for key,value in _retained.items() if not key.startswith('__')})
verify_preserved=verify
_current634=runpy.run_path(str(Path(__file__).with_name('mouse634-current.py')))

def verify(read,p):
 result=verify_preserved(read,p)
 transition=_current634['verify_upgrade'](read,platform='linux',arch='x64',packages=p['packages'])
 return {**result,'current633Upgrade':transition}
