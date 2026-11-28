#!/usr/bin/env python3
"""Mac644 retains earlier gates and binds native website themes and display names."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("mouse644-reuse.py")))["load"]('mouse637-release.py', namespace=globals())
_extra638 = runpy.run_path(str(Path(__file__).with_name('mouse644-extra-evidence.py')))
_original638_import = import_candidate
_original638_publish = publish
_original638_validate_template = validate_template
GATES.append(('x-current638RenderingGate', 'mouse644-rendering-evidence.py'))
GATES.append(('x-current639AdblockGate', 'mouse644-adblock-evidence.py'))
GATES.append(('x-current640SettingsGate', 'mouse644-settings-evidence.py'))
GATES.append(('x-current641WorkspaceGate', 'mouse644-flexible-workspace-evidence.py'))
GATES.append(('x-current643PolishGate', 'mouse644-polish-evidence.py'))
GATES.append(('x-current644SyncGate', 'mouse644-sync-evidence.py'))
GATES.append(('x-current644BrandingGate', 'mouse644-branding-evidence.py'))
FEATURE_TOKENS_632.add('native-adblock-network-ui-restart')
FEATURE_TOKENS_632.add('settings-glass-navigation-search')
FEATURE_TOKENS_632.update(_extra638['WORKSPACE_TOKENS'])
FEATURE_TOKENS_632.update(_extra638['CONTROLS_TOKENS'])
FEATURE_TOKENS_632.update(_extra638['POLISH_TOKENS'])
FEATURE_TOKENS_632.update(_extra638['SYNC_TOKENS'])
FEATURE_TOKENS_632.update(_extra638['BRANDING_TOKENS'])


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
        raise SystemExit('Expected a supported Mac644 publication action')
    if sys.argv[1] not in ('validate-template', 'validate'):
        runpy.run_path(str(Path(__file__).with_name('mouse644-publish-plan.py')))['require_ready']('macos-arm64')
    actions[sys.argv[1]]()
