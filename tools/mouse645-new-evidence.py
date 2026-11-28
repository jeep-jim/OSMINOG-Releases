#!/usr/bin/env python3
"""Independently verify raw645 UI/account evidence on source and fresh installs."""
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import tempfile

TOOLS = Path(__file__).resolve().parent
SOURCE = runpy.run_path(str(TOOLS / 'mouse645-source.py'))
UI_TOKENS = ('native645-account-sidebar-and-lightweight-sync-disclosure',
             'native645-flash-sidebar-and-overlay-barrier', 'native645-conditional-update-entry',
             'native645-appearance-distinct-process-roundtrip')
ACCOUNT_TOKENS = ('native645-real-account-profile-isolation-and-logout',
                  'native645-cross-device-config-only-sync', 'native645-immediate-logout-final-sync',
                  'native645-missing-credential-prewindow-guard')
DEPENDENCIES = ('mouse645-new-evidence.py', 'mouse645-source.py', 'mouse645-source-files.json',
                'mouse645-identity-evidence.py', 'mouse645-account-evidence.cjs',
                'mouse645-polish-evidence.py', 'mouse645-task-evidence.py', 'mouse645-reuse.py',
                'mouse645-frozen.json')


def need(value, message):
    if not value:
        raise ValueError('Mouse645 native evidence: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def gate_contracts():
    dependencies = {name: sha((TOOLS / name).read_bytes()) for name in DEPENDENCIES}
    common = {'runtimeVersion': '6.0.45', 'platform': 'darwin', 'arch': 'arm64',
              'sourceAndFreshInstalled': True, 'savedReportAcceptedAsInput': False,
              'sourceManifestAttemptBound': True, 'allRawArtifactsHashBound': True,
              'physicalUserDeviceVerified': False, 'dependencies': dependencies}
    return {
        'x-current645IdentityGate': {**common, 'validator': 'tools/mouse645-identity-evidence.py',
            'sha256': sha((TOOLS / 'mouse645-identity-evidence.py').read_bytes()),
            'featureTokens': list(UI_TOKENS), 'actualOSInputAndPixels': True,
            'sandboxedNativeFlashView': True, 'distinctActualProcesses': 2,
            'required': ['mouse-645-acceptance.json', 'mouse-645-ui.json', 'mouse-645-ui-write.json',
                         'mouse-645-processes.json', 'mouse-645-write.log', 'mouse-645-read.log']},
        'x-current645AccountGate': {**common, 'validator': 'tools/mouse645-account-evidence.cjs',
            'sha256': sha((TOOLS / 'mouse645-account-evidence.cjs').read_bytes()),
            'featureTokens': list(ACCOUNT_TOKENS), 'realHTTPAndSQLite': True,
            'osProtectedCredentials': True, 'metadataOnlySync': True,
            'freshGuestEveryLogout': True, 'prewindowMissingCredentialGuard': True,
            'logicalDevices': 2, 'installedProcesses': 14,
            'required': ['mouse-645-account-acceptance.json', 'mouse-645-account-processes.json',
                         'mouse-645-account-server.json']}}


def validate_contract(stage):
    schema = json.loads((Path(stage) / 'evidence.schema.json').read_text())
    for key, expected in gate_contracts().items():
        need(schema.get(key) == expected, 'reviewed native gate contract differs: ' + key)
    SOURCE['validate']()
    raw = SOURCE['checked']('tools/mouse-645-verify.py').replace(
        b'mouse-643-polish-acceptance.py', b'mouse645-polish-evidence.py')
    need(raw == (TOOLS / 'mouse645-identity-evidence.py').read_bytes(), 'independent UI reader differs from the reviewed source')


def inventory(read, receipt, pattern):
    raw = read(receipt)
    need(isinstance(raw, bytes) and 0 < len(raw) <= 1024**2, 'bounded acceptance receipt is missing')
    accepted = json.loads(raw)
    rows = accepted.get('artifacts')
    need(isinstance(rows, list) and 5 <= len(rows) <= 128, 'raw artifact ledger is missing or oversized')
    files, total = {}, 0
    for row in rows:
        need(isinstance(row, dict) and set(row) == {'file', 'bytes', 'sha256'}, 'invalid raw artifact descriptor')
        name = row['file']
        need(isinstance(name, str) and re.fullmatch(pattern, name) and '..' not in name
             and name != receipt and name not in files, 'unsafe or repeated raw artifact filename')
        value = read(name)
        need(isinstance(value, bytes) and 0 < len(value) <= 32 * 1024**2
             and type(row['bytes']) is int and len(value) == row['bytes']
             and sha(value) == row['sha256'], 'raw artifact bytes differ: ' + name)
        total += len(value)
        need(total <= 256 * 1024**2, 'raw artifact ledger exceeds its byte limit')
        files[name] = value
    return raw, accepted, files


def identity(read, build=None):
    receipt = 'mouse-645-acceptance.json'
    raw, accepted, files = inventory(read, receipt, r'mouse-645-[a-z0-9.-]+')
    consumed = set()
    def bound(name):
        need(name in files, 'independent UI reader requested an unbound artifact: ' + name)
        consumed.add(name)
        return files[name]
    verified = runpy.run_path(str(TOOLS / 'mouse645-identity-evidence.py'))['verify'](bound)
    verified['artifacts'] = [{'file': name, 'bytes': len(files[name]), 'sha256': sha(files[name])}
                             for name in sorted(consumed)]
    need(consumed == set(files) and accepted == verified, 'UI acceptance differs from independently read native input/display bytes')
    binding = {'file': receipt, 'sha256': sha(raw),
               'report': {'file': 'mouse-645-ui.json', 'sha256': sha(files['mouse-645-ui.json'])},
               'processes': {'file': 'mouse-645-processes.json', 'sha256': sha(files['mouse-645-processes.json'])}}
    if build is not None:
        need(set(UI_TOKENS) <= set(build.get('tests', [])) and build.get('identity645') == binding,
             'candidate manifest omits or changes native UI645 proof')
    return accepted


def account(read, build=None):
    receipt = 'mouse-645-account-acceptance.json'
    raw, accepted, files = inventory(read, receipt, r'mouse-645-account-[a-z0-9.-]+')
    SOURCE['validate']()
    with tempfile.TemporaryDirectory(prefix='mouse645-account-proof-') as directory:
        target = Path(directory)
        (target / receipt).write_bytes(raw)
        for name, value in files.items():
            (target / name).write_bytes(value)
        env = {key: value for key, value in os.environ.items() if key not in ('GH_TOKEN', 'GITHUB_TOKEN')}
        result = subprocess.run(['node', str(TOOLS / 'mouse645-account-evidence.cjs'), directory],
                                capture_output=True, check=True, timeout=60, env=env)
        need(len(result.stdout) <= 2 * 1024**2, 'oversized account reader result')
        verified = json.loads(result.stdout)
    need(verified.get('accepted') == accepted, 'account acceptance differs from independent raw facts')
    if build is not None:
        need(set(ACCOUNT_TOKENS) <= set(build.get('tests', [])) and build.get('account645') == verified['binding'],
             'candidate manifest omits or changes native account645 proof')
    return accepted


def both(read, build=None):
    return identity(read, build), account(read, build)
