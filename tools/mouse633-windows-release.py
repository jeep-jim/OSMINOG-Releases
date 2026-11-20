#!/usr/bin/env python3
"""Publish633 with the immutable632 Windows gates and current owner evidence."""
import runpy
from pathlib import Path
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))
_retained = _reuse['load']('mouse632-windows-release.py', namespace=globals())
globals().update({key: value for key, value in _retained.items() if not key.startswith('__')})

_current = runpy.run_path(str(Path(__file__).with_name('mouse633-current.py')))


def _verify_current_upgrade(read, p):
    return _current['verify_upgrade'](read, platform='win32', arch='x64', package=p['package'])


_legacy_import_candidate = import_candidate


def import_candidate():
    _legacy_import_candidate()
    p = pin()
    _current['fetch_helpers'](api, SOURCE, p['source'], OUT)


if __name__ == '__main__':
    commands = {'import': import_candidate, 'verify': verify_installed,
                'publish': publish, 'channel': channel}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        raise SystemExit('Expected import, verify, publish or channel')
    commands[sys.argv[1]]()
