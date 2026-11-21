#!/usr/bin/env python3
"""All retained633 owner/media/document/workspace gates plus mandatory634 gate."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name('mouse634-reuse.py')))
_retained=_reuse['load']('mouse633-feedback-evidence.py',namespace=globals())
globals().update({key:value for key,value in _retained.items() if not key.startswith('__')})
_verify_preserved=verify

def verify(read,*,expected_platform=None,expected_arch=None):
 result=_verify_preserved(read,expected_platform=expected_platform,expected_arch=expected_arch)
 current=runpy.run_path(str(Path(__file__).with_name('mouse634-owner-feedback-evidence.py')))['verify'](read,expected_platform=result['platform'],expected_arch=result['arch'])
 return {**result,'owner634':current,'inputs':{**result['inputs'],'mouse-634-owner-feedback.json':current['reportSha256']}}
