#!/usr/bin/env python3
"""Run byte-frozen633 algorithms against634 facts; never rewrite evidence."""
import runpy
from pathlib import Path
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse634-reuse.py')))
_retained = _reuse['load']('mouse633-windows-release.py', namespace=globals())
globals().update({key: value for key, value in _retained.items() if not key.startswith('__')})

if __name__ == '__main__':
    commands = {'import': import_candidate, 'verify': verify_installed, 'publish': publish, 'channel': channel}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit('Expected import, verify, publish or channel')
    commands[sys.argv[1]]()
