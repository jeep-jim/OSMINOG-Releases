#!/usr/bin/env python3
"""Reuse the immutable predecessor checker for the reviewed638 identity."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("mouse642-reuse.py")))["execute"]('mouse637-features-evidence.py', globals())

#The new Settings sequence runs immediately after the retained sidebar proof.
#The final two frames remain the distinct restart-process restoration frames.
_settings_insert = CAPTURES.index('mouse-637-sidebar-restored-dark.png') + 1
CAPTURES[_settings_insert:_settings_insert] = [
    'mouse-637-settings-' + scene + '-' + theme + '.png'
    for theme in ('light', 'dark') for scene in ('overview', 'appearance', 'narrow')
]
