#!/usr/bin/env python3
"""Mac645 retains every Mac gate and requires account/UI and public-service proof."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("mouse645-reuse.py")))["load"]('mouse637-release.py', namespace=globals())
_extra638 = runpy.run_path(str(Path(__file__).with_name('mouse645-extra-evidence.py')))
_new645 = runpy.run_path(str(Path(__file__).with_name('mouse645-new-evidence.py')))
_source645 = runpy.run_path(str(Path(__file__).with_name('mouse645-source.py')))
_services645 = runpy.run_path(str(Path(__file__).with_name('mouse645-readiness.py')))
_rtc645 = runpy.run_path(str(Path(__file__).with_name('mouse645-flash-evidence.py')))
_original638_import = import_candidate
_original638_publish = publish
_original638_validate_template = validate_template
_original645_channel = channel
_original645_validate = validate
GATES.append(('x-current638RenderingGate', 'mouse645-rendering-evidence.py'))
GATES.append(('x-current639AdblockGate', 'mouse645-adblock-evidence.py'))
GATES.append(('x-current640SettingsGate', 'mouse645-settings-evidence.py'))
GATES.append(('x-current641WorkspaceGate', 'mouse645-flexible-workspace-evidence.py'))
GATES.append(('x-current643PolishGate', 'mouse645-polish-evidence.py'))
GATES.append(('x-current644SyncGate', 'mouse645-sync-evidence.py'))
GATES.append(('x-current644BrandingGate', 'mouse645-branding-evidence.py'))
GATES.append(('x-current645IdentityGate', 'mouse645-identity-evidence.py'))
GATES.append(('x-current645AccountGate', 'mouse645-account-evidence.cjs'))
FEATURE_TOKENS_632.add('native-adblock-network-ui-restart')
FEATURE_TOKENS_632.add('settings-glass-navigation-search')
FEATURE_TOKENS_632.update(_extra638['WORKSPACE_TOKENS'])
FEATURE_TOKENS_632.update(_extra638['CONTROLS_TOKENS'])
FEATURE_TOKENS_632.update(_extra638['POLISH_TOKENS'])
FEATURE_TOKENS_632.update(_extra638['SYNC_TOKENS'])
FEATURE_TOKENS_632.update(_extra638['BRANDING_TOKENS'])
FEATURE_TOKENS_632.update(_new645['UI_TOKENS'])
FEATURE_TOKENS_632.update(_new645['ACCOUNT_TOKENS'])


def validate_template():
    _original638_validate_template()
    _extra638['validate_pin'](PIN, 'darwin')
    _extra638['validate_contract'](STAGE)
    _new645['validate_contract'](STAGE)
    _services645['validate_contract'](STAGE)
    _rtc645['validate_contract'](STAGE)
    _rtc645['validate_pin'](PIN)


def validate():
    validate_template()
    _original645_validate()


def import_candidate():
    _original638_import()
    _source645['fetch'](api, SOURCE, HEAD, OUT)
    _extra638['import_extra'](globals(), 'darwin')
    _rtc645['import_source'](globals())


def publish():
    validate_template()
    _source645['verify'](OUT)
    _extra638['fresh'](globals(), 'darwin')
    _rtc645['before_publication'](globals())
    _services645['require_ready'](OUT, stage=STAGE, phase='publish')
    _original638_publish()


def channel():
    validate_template()
    _source645['verify'](OUT)
    _rtc645['before_publication'](globals())
    _services645['require_ready'](OUT, stage=STAGE, phase='channel')
    _original645_channel()


if __name__ == '__main__':
    actions = {'validate-template': validate_template, 'import': import_candidate,
               'publish': publish, 'channel': channel, 'validate': validate}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        raise SystemExit('Expected a supported Mac645 publication action')
    if sys.argv[1] not in ('validate-template', 'validate'):
        runpy.run_path(str(Path(__file__).with_name('mouse645-publish-plan.py')))['require_ready']('macos-arm64')
    actions[sys.argv[1]]()
