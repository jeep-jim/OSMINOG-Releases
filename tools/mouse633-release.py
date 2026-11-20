#!/usr/bin/env python3
"""Publish633 through immutable632 package, install and public-channel gates."""
import runpy
from pathlib import Path
_reuse = runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))
_retained = _reuse['load']('mouse632-release.py', namespace=globals())
globals().update({key: value for key, value in _retained.items() if not key.startswith('__')})

# The owner now explicitly requests restored Agent entry and Settings. Media,
# readonly documents, native geometry and all package gates remain in force.
FEATURE_TOKENS_632 = FEATURE_TOKENS_632 - {'helper-manual-entry-only'}
FEATURE_TOKENS_633 = {'agent-visible-restore-without-autoenable', 'owner633-feedback-installed',
                      'footer-settings-panel', 'live-page-zoom-preview', 'download-bounce-unread', 'secure-browser-import', 'real-632-to-633-profile-preserving-replacement'}
FEATURE_TOKENS_632 |= FEATURE_TOKENS_633
_retained['FEATURE_TOKENS_632'] = FEATURE_TOKENS_632


def _current_agent_entry(entry):
    return (isinstance(entry, dict) and entry.get('manualOnly') is False and
            all(entry.get(key) is True for key in ('startService', 'aiPreset', 'aiSelect',
                'settingsEntry', 'closeControl', 'disabledUntilEnabled', 'mascotLoaded')))


def _current_agent_reports(read):
    entry = json.loads(read('mouse-623-verification.json')).get('agentEntry', {})
    if not _current_agent_entry(entry):
        raise ValueError('Mouse633 restored Agent entries are incomplete')
    agent = json.loads(read('mouse-624-verification.json')).get('agent', {})
    if agent.get('autoRestoreDisabled') is not False or agent.get('restoredWithoutEnabling') is not True or agent.get('defaultDisabled') is not True:
        raise ValueError('Mouse633 Agent UI restore or opt-in backend contract differs')


def verify_632_feedback(read):
    _current_agent_reports(read)
    _current['verify_upgrade'](read, platform='darwin', arch='arm64',
                               package={'name': DMG, **PIN['packages'][DMG]})
    lines = read('mouse-smoke-write.log').decode('utf-8').splitlines()
    for marker in ('MOUSE_632_WEBSITE_OFFER_NEW_TAB_PASS',
                   'MOUSE_632_FOOTER_LAYOUT_BOTH_THEMES_PASS',
                   'MOUSE_632_DOCUMENTS_VIEW_ONLY_PASS'):
        if marker not in lines:
            raise ValueError('Retained633 native marker missing: ' + marker)
    return _feedback['verify'](read, expected_platform='darwin', expected_arch='arm64')


def validate_template():
    if PIN.get('version') != V or type(PIN.get('ready')) is not bool:
        raise ValueError('Mouse633 pin template version/state invalid')
    if not (STAGE/'RELEASE_NOTES.md').read_text().startswith('# Mouse Browser 6.0.33'):
        raise ValueError('Release notes version mismatch')
    schema = json.loads((STAGE/'evidence.schema.json').read_text())
    required = set(_evidence.JSON_NAMES) | {'mouse-631-native.json', 'mouse-631-task.json',
        'mouse-631-stress.json', 'mouse-632-media.json', 'mouse-632-footer.json',
        'mouse-632-documents.json', 'mouse-633-owner-feedback.json', 'mouse-633-context-menu.json',
        'mouse-633-upgrade.json', 'mouse-633-upgrade-write.json', 'mouse-633-upgrade-read.json'}
    if set(schema['required']) != required or schema['x-motionTraceGate']['algorithm'] != 'mouse628-motion-trace-evidence-v2':
        raise ValueError('Evidence schema mismatch')
    for key, module in [('x-taskStressGate', 'mouse633-task-evidence.py'),
                        ('x-ownerFeedbackGate', 'mouse633-feedback-evidence.py'),
                        ('x-currentOwnerGate', 'mouse633-owner-feedback-evidence.py'),
                        ('x-currentContextGate', 'mouse633-context-evidence.py'),
                        ('x-currentUpgradeGate', 'mouse633-upgrade-evidence.py')]:
        gate = schema[key]
        if gate['validator'] != 'tools/'+module or gate['sha256'] != sha(Path(__file__).with_name(module).read_bytes()) or gate['sourceAndFreshInstalled'] is not True:
            raise ValueError('Independent633 checker contract mismatch: ' + module)
    if PIN['ready'] is False:
        for key in ['source', 'run', 'artifact', 'archiveSHA256', 'verificationArtifact',
                    'verificationSHA256', 'sourcePR', 'sourceMerge', 'sourceAttempt', 'sourceJob']:
            if PIN.get(key) is not None:
                raise ValueError('Unready template contains provenance claims: ' + key)
        if set(PIN.get('packages', {})) != {DMG, ZIP} or any(
                value != {'size': None, 'sha256': None} for value in PIN['packages'].values()):
            raise ValueError('Unready template contains package claims')
        if (STAGE/'PUBLISH_OWNER').exists():
            raise ValueError('Unready template must not have an owner trigger')
    print('MOUSE633_RELEASE_TEMPLATE_CONTRACT_PASS', flush=True)


_retained.update(verify_632_feedback=verify_632_feedback, validate_template=validate_template,
                 _current_agent_entry=_current_agent_entry)
_legacy_publish = publish


def publish():
    verify_package_bytes()
    _current_agent_reports(lambda name: (OUT/name).read_bytes())
    return _legacy_publish()

_current = runpy.run_path(str(Path(__file__).with_name('mouse633-current.py')))
_legacy_import_candidate = import_candidate


def import_candidate():
    _legacy_import_candidate()
    _current['fetch_helpers'](api, SOURCE, HEAD, OUT)


if __name__ == '__main__':
    actions = {'validate-template': validate_template, 'validate': validate,
               'import': import_candidate, 'publish': publish, 'channel': channel}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        raise SystemExit('Expected validate-template, validate, import, publish or channel')
    if sys.argv[1] not in ('validate-template', 'validate'):
        validate()
    actions[sys.argv[1]]()
