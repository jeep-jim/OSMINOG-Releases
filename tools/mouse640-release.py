#!/usr/bin/env python3
"""Retained independent publication gates plus mandatory638 acceptance."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("mouse640-reuse.py")))["load"]('mouse637-release.py', namespace=globals())
_extra638 = runpy.run_path(str(Path(__file__).with_name('mouse640-extra-evidence.py')))
_original638_import = import_candidate
_original638_publish = publish
_original638_validate_template = validate_template
GATES.append(('x-current638RenderingGate', 'mouse640-rendering-evidence.py'))
GATES.append(('x-current639AdblockGate', 'mouse640-adblock-evidence.py'))
GATES.append(('x-current640SettingsGate', 'mouse640-settings-evidence.py'))
FEATURE_TOKENS_632.add('native-adblock-network-ui-restart')
FEATURE_TOKENS_632.add('settings-glass-navigation-search')


def validate_template():
    _original638_validate_template()
    _extra638['validate_pin'](PIN, 'darwin')
    _extra638['validate_contract'](STAGE)


def import_candidate():
    _original638_import()
    _extra638['import_extra'](globals(), 'darwin')


def publish():
    _extra638['fresh'](globals(), 'darwin')
    _original638_publish()


if __name__ == '__main__':
    actions = {'validate-template': validate_template, 'import': import_candidate,
               'publish': publish, 'channel': channel, 'validate': validate}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        raise SystemExit('Expected a supported638 publication action')
    if sys.argv[1] not in ('validate-template', 'validate'):
        runpy.run_path(str(Path(__file__).with_name('mouse640-publish-plan.py')))['require_ready']('macos-arm64')
    actions[sys.argv[1]]()
