#!/usr/bin/env python3
"""Retained independent publication gates plus mandatory638 acceptance."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("mouse640-reuse.py")))["load"]('mouse637-windows-release.py', namespace=globals())
_extra638 = runpy.run_path(str(Path(__file__).with_name('mouse640-extra-evidence.py')))
_original638_import = import_candidate
_original638_publish = publish
_original638_pin = pin
_original638_validate_template = validate_template


def pin():
    value = _original638_pin()
    _extra638['validate_pin'](value, 'win32')
    return value


def validate_template():
    value = _original638_validate_template()
    _extra638['validate_pin'](value, 'win32')
    return value


def import_candidate():
    _original638_import()
    _extra638['import_extra'](globals(), 'win32')


def publish():
    _extra638['fresh'](globals(), 'win32')
    _original638_publish()


_original638_verify = verify_installed


def verify_installed():
    _original638_verify()
    _extra638['fresh'](globals(), 'win32')


if __name__ == '__main__':
    actions = {'validate-template': validate_template, 'import': import_candidate,
               'publish': publish, 'channel': channel, 'verify': verify_installed}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        raise SystemExit('Expected a supported638 publication action')
    if sys.argv[1] not in ('validate-template', 'validate'):
        runpy.run_path(str(Path(__file__).with_name('mouse640-publish-plan.py')))['require_ready']('windows-x64')
    actions[sys.argv[1]]()
