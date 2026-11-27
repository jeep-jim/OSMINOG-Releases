#!/usr/bin/env python3
"""Bind current controls, glass Settings, AdBlock and native installation jobs."""
from contextlib import contextmanager
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import runpy
import subprocess
import zipfile

TOOLS = Path(__file__).resolve().parent
SOURCE = 'jeep-jim/OSMINOG'
VERSION = '6.0.43'
SOURCE_HELPERS = ('mouse-638-feedback-run.py', 'mouse-638-acceptance.py', 'mouse-638-crx-proof.cjs')
ADBLOCK_REQUIRED = ('mouse-639-acceptance.json', 'mouse-639-adblock.json',
    'mouse-639-adblock-write.json', 'mouse-639-adblock-processes.json',
    'mouse-639-adblock-cache.json', 'mouse-639-adblock-cache-easylist.json',
    'mouse-639-adblock-cache-ruadlist.json', 'mouse-639-adblock-http-write.json',
    'mouse-639-adblock-http-read.json', 'mouse-639-adblock-fixture.html',
    'mouse-639-adblock-write.log', 'mouse-639-adblock-read.log')
ADBLOCK_DEPENDENCIES = ('mouse643-task-evidence.py', 'mouse643-extra-evidence.py',
    'mouse643-reuse.py', 'mouse643-frozen.json', 'mouse643-current.py')
SETTINGS_REQUIRED = ('mouse-640-settings-acceptance.json', 'mouse-637-features.json',
    'mouse-637-features-write.json', 'mouse-637-features-processes.json')
SETTINGS_DEPENDENCIES = ('mouse643-task-evidence.py', 'mouse643-extra-evidence.py',
    'mouse643-reuse.py', 'mouse643-frozen.json', 'mouse643-current.py',
    'mouse643-features-evidence.py', 'mouse643-sidebar-focus-evidence.py')
WORKSPACE_REQUIRED = ('mouse-641-workspace-acceptance.json', 'mouse-641-workspace.json',
    'mouse-641-workspace-write.json', 'mouse-641-workspace-processes.json',
    'mouse-641-workspace-write.log', 'mouse-641-workspace-read.log',
    'mouse-641-adblock-cache.json', 'mouse-641-adblock-cache-easylist.json', 'mouse-641-adblock-cache-ruadlist.json',
    'mouse-641-http-write.json', 'mouse-641-http-read.json', 'mouse-637-features.json', 'mouse-637-features-write.json')
WORKSPACE_DEPENDENCIES = ('mouse643-task-evidence.py', 'mouse643-extra-evidence.py',
    'mouse643-reuse.py', 'mouse643-frozen.json', 'mouse643-current.py', 'mouse643-owner-contracts.py',
    'mouse643-features-evidence.py')
WORKSPACE_TOKENS = ('native641-classic-grid-and-workspace-flows', 'native641-site-exclusions-restart',
    'native641-theme-surfaces-and-library', 'native641-headers-always-visible', 'native641-media-player-removed-site-audio-retained')
CONTROLS_REQUIRED = ('mouse-642-controls-acceptance.json', 'mouse-642-controls.json',
    'mouse-642-controls-write.json', 'mouse-642-controls-processes.json',
    'mouse-642-controls-write.log', 'mouse-642-controls-read.log')
CONTROLS_DEPENDENCIES = ('mouse643-task-evidence.py', 'mouse643-extra-evidence.py',
    'mouse643-reuse.py', 'mouse643-frozen.json', 'mouse643-current.py')
CONTROLS_TOKENS = ('native642-theme-temperature-and-restart', 'native642-real-os-input-language',
    'native642-consent-layout-correction')
POLISH_REQUIRED = ('mouse-643-polish-acceptance.json', 'mouse-643-polish.json',
    'mouse-643-polish-write.json', 'mouse-643-polish-processes.json',
    'mouse-643-polish-write.log', 'mouse-643-polish-read.log')
POLISH_DEPENDENCIES = ('mouse643-task-evidence.py', 'mouse643-extra-evidence.py',
    'mouse643-reuse.py', 'mouse643-frozen.json', 'mouse643-current.py')
POLISH_TOKENS = ('native643-mac-chrome-and-tab-shapes',
    'native643-search-suggestions-and-address-tools', 'native643-real-page-theme-and-restart')


def need(value, message):
    if not value:
        raise ValueError('638 publication evidence: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_pin(pin, platform):
    need(platform == 'darwin', '643 is authorized for macOS arm64 only')
    validate_contract(TOOLS.parent / 'staging/mouse/6.0.43-arm64')
    previous = runpy.run_path(str(TOOLS / 'mouse643-reuse.py'))['previous']('darwin')
    need(pin.get('currentPrevious') == previous, 'actual published642 Mac predecessor pin differs')


def validate_contract(stage):
    contract = json.loads((stage / 'evidence.schema.json').read_text())['x-current638RenderingGate']
    dependencies = ('mouse643-task-evidence.py', 'mouse-638-crx-proof.cjs',
                    'mouse643-extra-evidence.py', 'mouse643-reuse.py', 'mouse643-frozen.json')
    need(contract.get('dependencies') == {name: sha((TOOLS / name).read_bytes()) for name in dependencies},
         'independent638 checker dependencies changed')
    need(contract.get('required') == ['mouse-638-acceptance.json', 'mouse-638-feedback.json',
         'mouse-638-feedback-processes.json', 'mouse-638-feedback-write.json', 'mouse-638-webstore.crx'],
         'independent638 checker required source/fresh evidence differs')
    validate_adblock_contract(stage)
    validate_settings_contract(stage)
    validate_workspace_contract(stage)
    validate_controls_contract(stage)
    validate_polish_contract(stage)


def validate_adblock_contract(stage):
    contract = json.loads((stage / 'evidence.schema.json').read_text())['x-current639AdblockGate']
    need(contract.get('validator') == 'tools/mouse643-adblock-evidence.py'
         and contract.get('sha256') == sha((TOOLS / 'mouse643-adblock-evidence.py').read_bytes())
         and contract.get('sourceAndFreshInstalled') is True,
         'independent639 AdBlock validator identity changed')
    need(contract.get('dependencies') == {name: sha((TOOLS / name).read_bytes()) for name in ADBLOCK_DEPENDENCIES}
         and contract.get('required') == list(ADBLOCK_REQUIRED),
         'independent639 AdBlock dependency/receipt contract changed')
    runpy.run_path(str(TOOLS / 'mouse643-reuse.py'))['verify_frozen']()


def validate_settings_contract(stage):
    contract = json.loads((stage / 'evidence.schema.json').read_text())['x-current640SettingsGate']
    need(contract.get('validator') == 'tools/mouse643-settings-evidence.py'
         and contract.get('sha256') == sha((TOOLS / 'mouse643-settings-evidence.py').read_bytes())
         and contract.get('sourceAndFreshInstalled') is True
         and contract.get('savedReportAcceptedAsInput') is False,
         'independent640 Settings validator identity changed')
    need(contract.get('dependencies') == {name: sha((TOOLS / name).read_bytes()) for name in SETTINGS_DEPENDENCIES}
         and contract.get('required') == list(SETTINGS_REQUIRED),
         'independent640 Settings dependency/receipt contract changed')


def validate_workspace_contract(stage):
    contract = json.loads((stage / 'evidence.schema.json').read_text())['x-current641WorkspaceGate']
    need(contract.get('validator') == 'tools/mouse643-flexible-workspace-evidence.py'
         and contract.get('sha256') == sha((TOOLS / 'mouse643-flexible-workspace-evidence.py').read_bytes())
         and contract.get('sourceAndFreshInstalled') is True and contract.get('savedReportAcceptedAsInput') is False
         and contract.get('runtimeVersion') == VERSION
         and all(contract.get(key) is True for key in ('sameSiteNavigationKeepsTabAndWebContents',
             'classicCornerMinimizeReturnsSavedGrid', 'classicCornerReturnKeepsWindowVisible')),
         'independent641 workspace validator identity changed')
    need(contract.get('dependencies') == {name: sha((TOOLS / name).read_bytes()) for name in WORKSPACE_DEPENDENCIES}
         and contract.get('required') == list(WORKSPACE_REQUIRED)
         and contract.get('featureTokens') == list(WORKSPACE_TOKENS), 'independent641 workspace dependency/receipt contract changed')


def validate_controls_contract(stage):
    contract = json.loads((stage / 'evidence.schema.json').read_text())['x-current642ControlsGate']
    need(contract.get('validator') == 'tools/mouse643-controls-evidence.py'
         and contract.get('sha256') == sha((TOOLS / 'mouse643-controls-evidence.py').read_bytes())
         and contract.get('runtimeVersion') == VERSION and contract.get('sourceAndFreshInstalled') is True
         and contract.get('savedReportAcceptedAsInput') is False
         and all(contract.get(key) is True for key in ('realOSInputLanguage', 'samePhysicalKeyBothLayouts',
             'explicitConsentBeforeReplacement', 'originalTargetAndRangeBound', 'nativeUndo',
             'plainParagraphCorrection', 'unmodifiedEditorNodesPreserved', 'plainParagraphNativeUndo',
             'settingsOnlyInterfaceLanguage', 'independentToneControls', 'twoProcessTonePersistence')),
         'independent642 controls validator identity or required behavior changed')
    need(contract.get('dependencies') == {name: sha((TOOLS / name).read_bytes()) for name in CONTROLS_DEPENDENCIES}
         and contract.get('required') == list(CONTROLS_REQUIRED)
         and contract.get('featureTokens') == list(CONTROLS_TOKENS), 'independent642 controls dependency/receipt contract changed')


def verify_helper_bytes(output):
    """The fetched source checker/proof must match independent publisher code."""
    source = (output / 'mouse-638-acceptance.py').read_bytes()
    need(source.replace(b'mouse-631-acceptance.py', b'mouse643-task-evidence.py') ==
         (TOOLS / 'mouse643-rendering-evidence.py').read_bytes(), 'source638 checker differs from independent publisher reader')
    need((output / 'mouse-638-crx-proof.cjs').read_bytes() == (TOOLS / 'mouse-638-crx-proof.cjs').read_bytes(),
         'source638 signed CRX proof differs from independent publisher reader')
    source639 = (output / 'mouse-639-acceptance.py').read_bytes()
    need(source639.replace(b'mouse-631-acceptance.py', b'mouse643-task-evidence.py') ==
         (TOOLS / 'mouse643-adblock-evidence.py').read_bytes(),
         'source639 AdBlock checker differs from independent publisher reader')
    source640 = (output / 'mouse-640-settings-acceptance.py').read_bytes()
    need(source640.replace(b'mouse-631-acceptance.py', b'mouse643-task-evidence.py') ==
         (TOOLS / 'mouse643-settings-evidence.py').read_bytes(),
         'source640 Settings checker differs from independent publisher reader')
    source641 = (output / 'mouse-641-workspace-acceptance.py').read_bytes()
    need(source641.replace(b'mouse-631-acceptance.py', b'mouse643-task-evidence.py') ==
         (TOOLS / 'mouse643-flexible-workspace-evidence.py').read_bytes(),
         'source641 workspace checker differs from independent publisher reader')
    source642 = (output / 'mouse-642-controls-acceptance.py').read_bytes()
    need(source642.replace(b'mouse-631-acceptance.py', b'mouse643-task-evidence.py') ==
         (TOOLS / 'mouse643-controls-evidence.py').read_bytes(),
         'source642 controls checker differs from independent publisher reader')
    source643 = (output / 'mouse-643-polish-acceptance.py').read_bytes()
    need(source643.replace(b'mouse-631-acceptance.py', b'mouse643-task-evidence.py') ==
         (TOOLS / 'mouse643-polish-evidence.py').read_bytes(),
         'source643 Mac polish checker differs from independent publisher reader')


def validate_polish_contract(stage):
    contract = json.loads((stage / 'evidence.schema.json').read_text())['x-current643PolishGate']
    need(contract.get('validator') == 'tools/mouse643-polish-evidence.py'
         and contract.get('sha256') == sha((TOOLS / 'mouse643-polish-evidence.py').read_bytes())
         and contract.get('sourceAndFreshInstalled') is True and contract.get('savedReportAcceptedAsInput') is False
         and contract.get('runtimeVersion') == VERSION and contract.get('platform') == 'darwin'
         and contract.get('arch') == 'arm64'
         and all(contract.get(key) is True for key in ('nativeDisplayPixels', 'realNativeClickAndDrag',
             'rootThemeSurfaceActiveTab', 'fixedSquareSeparators', 'realSearchAndAddressActions', 'pageThemeAndRestart',
             'sourceManifestAttemptBound')),
         'independent643 Mac polish validator identity or required behavior changed')
    need(contract.get('dependencies') == {name: sha((TOOLS / name).read_bytes()) for name in POLISH_DEPENDENCIES}
         and contract.get('required') == list(POLISH_REQUIRED)
         and contract.get('featureTokens') == list(POLISH_TOKENS), 'independent643 Mac polish dependency/receipt contract changed')


def polish(read, *, platform, arch, build=None):
    need((platform, arch) == ('darwin', 'arm64'), '643 publication accepts only macOS arm64')
    accepted = runpy.run_path(str(TOOLS / 'mouse643-polish-evidence.py'))['verify'](
        read, expected_platform=platform, expected_arch=arch)
    original = read('mouse-643-polish-acceptance.json')
    need(json.loads(original) == accepted, 'native643 acceptance differs from independently read Mac input, process and display bytes')
    expected = {'file': 'mouse-643-polish-acceptance.json', 'sha256': sha(original),
        'report': {'file': 'mouse-643-polish.json', 'sha256': sha(read('mouse-643-polish.json'))},
        'processes': {'file': 'mouse-643-polish-processes.json', 'sha256': sha(read('mouse-643-polish-processes.json'))}}
    if build is not None:
        need(set(POLISH_TOKENS) <= set(build.get('tests', [])), 'candidate manifest omits mandatory643 native Mac feature gates')
        need(build.get('polish643') == expected, 'candidate manifest does not bind the actual643 process/report/acceptance bytes')
    return accepted


def source_manifest(build, pin):
    need((build.get('version'), build.get('source'), build.get('platform'), build.get('arch')) ==
         (VERSION, pin.get('source'), 'darwin', 'arm64'), '643 source manifest identity differs')
    for field, pin_field in (('runId', 'run'), ('runAttempt', 'sourceAttempt')):
        value, expected = build.get(field), pin.get(pin_field)
        need(type(value) in (str, int) and type(expected) is int and expected > 0
             and str(value) == str(expected), '643 source manifest does not bind exact ' + field)


def controls(read, *, platform, arch, build=None, verification=None):
    accepted = runpy.run_path(str(TOOLS / 'mouse643-controls-evidence.py'))['verify'](
        read, expected_platform=platform, expected_arch=arch)
    original = read('mouse-642-controls-acceptance.json')
    need(json.loads(original) == accepted, 'native642 acceptance differs from independently read controls, native input and display bytes')
    process_raw = read('mouse-642-controls-processes.json'); processes = json.loads(process_raw)
    expected = {'file': 'mouse-642-controls-acceptance.json', 'sha256': sha(original),
        'report': {'file': 'mouse-642-controls.json', 'sha256': sha(read('mouse-642-controls.json'))},
        'processes': {'file': 'mouse-642-controls-processes.json', 'sha256': sha(process_raw)}}
    if build is not None:
        need(set(CONTROLS_TOKENS) <= set(build.get('tests', [])), 'candidate manifest omits mandatory642 native feature gates')
        need(build.get('controls642') == expected, 'candidate manifest does not bind the actual642 process/report/acceptance bytes')
        if platform != 'darwin':
            verification = build.get('verification', {}).get('result')
    if platform != 'darwin':
        need(isinstance(verification, dict), 'installed642 controls lack their actual executable verification')
        checks = verification.get('checks', {})
        need(checks.get('controls642') == {**processes, 'acceptanceSha256': expected['sha256']},
             'installed642 controls wrapper differs from its actual process and independent acceptance bytes')
        key, repeated = {'linux': ('debInstallation', 'debReinstallation'), 'win32': ('installation', 'reinstallation')}[platform]
        installation = checks.get(key, {})
        need(isinstance(installation.get('executable'), str) and installation['executable']
             and re.fullmatch('[0-9a-f]{64}', installation.get('executableSha256', ''))
             and all(processes.get(field) == installation.get(field) for field in ('executable', 'executableSha256')),
             'native642 controls ran another executable than the verified installation')
        if repeated in checks:
            need(all(checks[repeated].get(field) == installation[field] for field in ('executable', 'executableSha256')),
                 'native642 installation and reinstallation differ')
    return accepted


def workspace(read, *, platform, arch, build=None, verification=None):
    accepted = runpy.run_path(str(TOOLS / 'mouse643-flexible-workspace-evidence.py'))['verify'](
        read, expected_platform=platform, expected_arch=arch)
    original = read('mouse-641-workspace-acceptance.json')
    need(json.loads(original) == accepted, 'native641 acceptance differs from independently read user flows and display bytes')
    process_raw = read('mouse-641-workspace-processes.json'); processes = json.loads(process_raw)
    expected = {'file': 'mouse-641-workspace-acceptance.json', 'sha256': sha(original),
        'report': {'file': 'mouse-641-workspace.json', 'sha256': sha(read('mouse-641-workspace.json'))},
        'processes': {'file': 'mouse-641-workspace-processes.json', 'sha256': sha(process_raw)}}
    if build is not None:
        need(set(WORKSPACE_TOKENS) <= set(build.get('tests', [])), 'candidate manifest omits mandatory641 native feature gates')
        need(build.get('workspace641') == expected, 'candidate manifest does not bind the actual641 process/report/acceptance bytes')
        if platform != 'darwin':
            verification = build.get('verification', {}).get('result')
    if platform != 'darwin':
        need(isinstance(verification, dict), 'installed641 evidence lacks its actual executable verification')
        checks = verification.get('checks', {})
        need(checks.get('workspace641') == {**processes, 'acceptanceSha256': expected['sha256']},
             'installed641 wrapper differs from its actual process and independent acceptance bytes')
        key, repeated = {'linux': ('debInstallation', 'debReinstallation'), 'win32': ('installation', 'reinstallation')}[platform]
        installation = checks.get(key, {})
        need(isinstance(installation.get('executable'), str) and installation['executable']
             and re.fullmatch('[0-9a-f]{64}', installation.get('executableSha256', ''))
             and all(processes.get(field) == installation.get(field) for field in ('executable', 'executableSha256')),
             'native641 user flows ran another executable than the verified installation')
        if repeated in checks:
            need(all(checks[repeated].get(field) == installation[field] for field in ('executable', 'executableSha256')),
                 'native641 installation and reinstallation differ')
    return accepted


def settings(read, *, platform, arch, build=None):
    accepted = runpy.run_path(str(TOOLS / 'mouse643-settings-evidence.py'))['verify'](
        read, expected_platform=platform, expected_arch=arch)
    original = read('mouse-640-settings-acceptance.json')
    need(json.loads(original) == accepted,
         'native640 Settings acceptance differs from independently read controls/captures')
    if build is not None:
        need('settings-glass-navigation-search' in build.get('tests', []),
             'candidate manifest omits mandatory Settings640 feature gate')
        need(build.get('settings640') == {'file': 'mouse-640-settings-acceptance.json', 'sha256': sha(original),
             'report': {'file': 'mouse-637-features.json', 'sha256': sha(read('mouse-637-features.json'))}},
             'candidate manifest does not bind actual Settings640 acceptance bytes')
    return accepted


def adblock(read, *, platform, arch, build=None, wrapper=None, verification=None, installation=None):
    accepted = runpy.run_path(str(TOOLS / 'mouse643-adblock-evidence.py'))['verify'](
        read, expected_platform=platform, expected_arch=arch)
    original = read('mouse-639-acceptance.json')
    need(json.loads(original) == accepted,
         'native639 AdBlock acceptance differs from independently recomputed requests/UI/pixels')
    process_raw = read('mouse-639-adblock-processes.json')
    processes = json.loads(process_raw)
    expected = {'file': 'mouse-639-acceptance.json', 'sha256': sha(original),
        'report': {'file': 'mouse-639-adblock.json', 'sha256': sha(read('mouse-639-adblock.json'))},
        'processes': {'file': 'mouse-639-adblock-processes.json', 'sha256': sha(process_raw)},
        'cache': {'file': 'mouse-639-adblock-cache.json', 'sha256': sha(read('mouse-639-adblock-cache.json'))},
        'artifacts': accepted['artifacts']}
    if build is not None:
        need('native-adblock-network-ui-restart' in build.get('tests', []),
             'candidate manifest omits its mandatory AdBlock639 feature gate')
        need(build.get('adblock639') == expected,
             'candidate manifest does not bind the complete independently read AdBlock evidence')
        if platform != 'darwin':
            verification = build.get('verification', {}).get('result')
            need(isinstance(verification, dict), 'candidate installed verification omits AdBlock639')
    if verification is not None:
        checks = verification.get('checks', {})
        actual_wrapper = checks.get('adblock639')
        need(isinstance(actual_wrapper, dict) and (wrapper is None or wrapper == actual_wrapper),
             'installed verification omits or contradicts its AdBlock639 wrapper')
        wrapper = actual_wrapper
        key, repeated = {'linux': ('debInstallation', 'debReinstallation'),
                         'win32': ('installation', 'reinstallation')}[platform]
        installation = checks.get(key)
        need(isinstance(installation, dict), 'AdBlock639 installed executable receipt is missing')
        if repeated in checks:
            reinstall = checks[repeated]
            need(isinstance(reinstall, dict) and all(reinstall.get(field) == installation.get(field)
                 for field in ('executable', 'executableSha256')),
                 'AdBlock639 installation and reinstallation executable identities differ')
    if wrapper is not None:
        need(wrapper == {**processes, 'acceptanceSha256': expected['sha256']},
             'installed AdBlock wrapper differs from exact process/acceptance bytes')
    if platform != 'darwin':
        need(isinstance(installation, dict) and isinstance(installation.get('executable'), str)
             and installation['executable'] and isinstance(installation.get('executableSha256'), str)
             and re.fullmatch('[0-9a-f]{64}', installation['executableSha256'])
             and all(processes.get(field) == installation[field] for field in ('executable', 'executableSha256')),
             'AdBlock639 evidence belongs to a different installed executable or has no installation receipt')
    return accepted


def feedback(read, *, platform, arch, build=None):
    accepted = runpy.run_path(str(TOOLS / 'mouse643-rendering-evidence.py'))['verify'](
        read, expected_platform=platform, expected_arch=arch)
    original = read('mouse-638-acceptance.json')
    need(json.loads(original) == accepted, 'native638 acceptance does not match independently recomputed pixels/runtime')
    if build is not None:
        expected = {'file': 'mouse-638-acceptance.json', 'sha256': sha(original),
            'report': {'file': 'mouse-638-feedback.json', 'sha256': sha(read('mouse-638-feedback.json'))},
            'processes': {'file': 'mouse-638-feedback-processes.json', 'sha256': sha(read('mouse-638-feedback-processes.json'))},
            'webStore': {'id': accepted['webStore']['id'], 'version': accepted['webStore']['version'],
                         'file': 'mouse-638-webstore.crx', 'sha256': sha(read('mouse-638-webstore.crx'))}}
        need(build.get('feedback638') == expected, 'candidate manifest does not bind actual638 evidence and signed Store bytes')
    return accepted


def job(api, pin, key, expected_name, steps):
    attempt = pin.get('sourceAttempt', pin.get('attempt'))
    need(type(pin.get(key)) is int and pin[key] > 0, 'missing exact additional source job: ' + key)
    jobs = api(SOURCE, f'actions/runs/{pin["run"]}/attempts/{attempt}/jobs?per_page=100')['jobs']
    rows = [j for j in jobs if j.get('id') == pin[key] and j.get('name') == expected_name]
    need(len(rows) == 1, 'additional native job is missing: ' + expected_name)
    row = rows[0]
    need((row.get('head_sha'), row.get('run_id'), row.get('run_attempt'), row.get('status'), row.get('conclusion')) ==
         (pin['source'], pin['run'], attempt, 'completed', 'success'), 'additional source job belongs to another run or did not pass')
    actual = {step.get('name') for step in row.get('steps', []) if step.get('status') == 'completed' and step.get('conclusion') == 'success'}
    need(set(steps) <= actual, 'additional native acceptance step did not run')
    return row


@contextmanager
def artifact(api, pin, *, id_key, hash_key, name, output, source_job=None):
    ident, digest = pin.get(id_key), pin.get(hash_key)
    need(type(ident) is int and ident > 0 and isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest),
         'additional artifact identity/hash is not pinned: ' + id_key)
    record = api(SOURCE, f'actions/artifacts/{ident}')
    need(record.get('id') == ident and record.get('name') == name and record.get('expired') is False
         and record.get('workflow_run', {}).get('id') == pin['run']
         and record.get('workflow_run', {}).get('head_sha') == pin['source']
         and type(record.get('size_in_bytes')) is int and 0 < record['size_in_bytes'] <= 768 * 1024**2,
         'additional artifact identity/source/size differs')
    if source_job is not None:
        parse = lambda s: datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
        need(parse(source_job['started_at']) <= parse(record['created_at']) <= parse(source_job['completed_at']),
             'additional artifact was not created by its pinned successful job')
    file = output / (name + '.zip')
    with file.open('wb') as target:
        subprocess.run(['gh', 'api', 'repos/' + SOURCE + f'/actions/artifacts/{ident}/zip'],
                       stdout=target, check=True, timeout=180)
    need(file.stat().st_size <= 768 * 1024**2 and sha(file.read_bytes()) == digest, 'additional artifact ZIP hash differs')
    with zipfile.ZipFile(file) as archive:
        entries = archive.infolist()
        need(len(entries) <= 4096 and len({p.filename for p in entries}) == len(entries)
             and sum(p.file_size for p in entries) <= 1024**3, 'additional evidence archive is oversized or duplicated')
        for item in entries:
            path = PurePosixPath(item.filename)
            need(not path.is_absolute() and '..' not in path.parts and '\\' not in item.filename
                 and (item.external_attr >> 16) & 0o170000 != 0o120000 and item.file_size <= 128 * 1024**2,
                 'unsafe additional evidence archive entry')
        yield archive


def receipt(read, value, expected_name, markers, budget):
    raw = read(expected_name)
    need(isinstance(raw, bytes) and 0 < len(raw) <= 32 * 1024**2 and value.get('log') == expected_name
         and value.get('exitCode') == 0 and type(value.get('pid')) is int and value['pid'] > 0
         and type(value.get('elapsedMs')) in (int, float) and 0 < value['elapsedMs'] <= budget
         and value.get('logSha256') == sha(raw) and value.get('requiredMarkers') == markers
         and all(marker in raw.decode('utf-8', 'replace').splitlines() for marker in markers),
         'actual native process/log receipt failed: ' + expected_name)




def import_extra(module, platform):
    pin = module['PIN']
    validate_pin(pin, platform)
    output, api = module['OUT'], module['api']
    verify_helper_bytes(output)
    build = json.loads((output / 'mouse-build.json').read_text())
    source_manifest(build, pin)
    with artifact(api, pin, id_key='verificationArtifact', hash_key='verificationSHA256', name='mouse-arm64-verification', output=output) as archive:
        accepted = feedback(archive.read, platform='darwin', arch='arm64', build=build)
        accepted_adblock = adblock(archive.read, platform='darwin', arch='arm64', build=build)
        accepted_settings = settings(archive.read, platform='darwin', arch='arm64', build=build)
        accepted_workspace = workspace(archive.read, platform='darwin', arch='arm64', build=build)
        accepted_controls = controls(archive.read, platform='darwin', arch='arm64', build=build)
        accepted_polish = polish(archive.read, platform='darwin', arch='arm64', build=build)
    for name, value in (('source638-feedback-independent.json', accepted),
                        ('source639-adblock-independent.json', accepted_adblock),
                        ('source640-settings-independent.json', accepted_settings),
                        ('source641-workspace-independent.json', accepted_workspace),
                        ('source642-controls-independent.json', accepted_controls),
                        ('source643-polish-independent.json', accepted_polish)):
        (output / name).write_text(json.dumps(value, indent=2) + '\n')
    print('MOUSE_643_SOURCE_MAC_SUPPLEMENTAL_ACCEPTANCE_PASS', flush=True)


def fresh(module, platform):
    need(platform == 'darwin', '643 is authorized for macOS arm64 only')
    output = module['OUT']
    verify_helper_bytes(output)
    read = lambda name: (output / name).read_bytes()
    accepted = feedback(read, platform='darwin', arch='arm64')
    values = (('installed638-feedback-independent.json', accepted),
              ('installed639-adblock-independent.json', adblock(read, platform='darwin', arch='arm64')),
              ('installed640-settings-independent.json', settings(read, platform='darwin', arch='arm64')),
              ('installed641-workspace-independent.json', workspace(read, platform='darwin', arch='arm64')),
              ('installed642-controls-independent.json', controls(read, platform='darwin', arch='arm64')),
              ('installed643-polish-independent.json', polish(read, platform='darwin', arch='arm64')))
    for name, value in values:
        (output / name).write_text(json.dumps(value, indent=2) + '\n')
    return accepted
