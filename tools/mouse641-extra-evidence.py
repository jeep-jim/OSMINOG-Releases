#!/usr/bin/env python3
"""Bind current glass Settings, retained AdBlock and native installation jobs."""
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
VERSION = '6.0.41'
SOURCE_HELPERS = ('mouse-638-feedback-run.py', 'mouse-638-acceptance.py', 'mouse-638-crx-proof.cjs')
ADBLOCK_REQUIRED = ('mouse-639-acceptance.json', 'mouse-639-adblock.json',
    'mouse-639-adblock-write.json', 'mouse-639-adblock-processes.json',
    'mouse-639-adblock-cache.json', 'mouse-639-adblock-cache-easylist.json',
    'mouse-639-adblock-cache-ruadlist.json', 'mouse-639-adblock-http-write.json',
    'mouse-639-adblock-http-read.json', 'mouse-639-adblock-fixture.html',
    'mouse-639-adblock-write.log', 'mouse-639-adblock-read.log')
ADBLOCK_DEPENDENCIES = ('mouse641-task-evidence.py', 'mouse641-extra-evidence.py',
    'mouse641-reuse.py', 'mouse641-frozen.json', 'mouse641-current.py')
SETTINGS_REQUIRED = ('mouse-640-settings-acceptance.json', 'mouse-637-features.json',
    'mouse-637-features-write.json', 'mouse-637-features-processes.json')
SETTINGS_DEPENDENCIES = ('mouse641-task-evidence.py', 'mouse641-extra-evidence.py',
    'mouse641-reuse.py', 'mouse641-frozen.json', 'mouse641-current.py',
    'mouse641-features-evidence.py', 'mouse641-sidebar-focus-evidence.py')
WORKSPACE_REQUIRED = ('mouse-641-workspace-acceptance.json', 'mouse-641-workspace.json',
    'mouse-641-workspace-write.json', 'mouse-641-workspace-processes.json',
    'mouse-641-workspace-write.log', 'mouse-641-workspace-read.log',
    'mouse-641-adblock-cache.json', 'mouse-641-adblock-cache-easylist.json', 'mouse-641-adblock-cache-ruadlist.json',
    'mouse-641-http-write.json', 'mouse-641-http-read.json', 'mouse-637-features.json', 'mouse-637-features-write.json')
WORKSPACE_DEPENDENCIES = ('mouse641-task-evidence.py', 'mouse641-extra-evidence.py',
    'mouse641-reuse.py', 'mouse641-frozen.json', 'mouse641-current.py', 'mouse641-owner-contracts.py',
    'mouse641-features-evidence.py')
WORKSPACE_TOKENS = ('native641-classic-grid-and-workspace-flows', 'native641-site-exclusions-restart',
    'native641-theme-surfaces-and-library', 'native641-headers-always-visible', 'native641-media-player-removed-site-audio-retained')


def need(value, message):
    if not value:
        raise ValueError('638 publication evidence: ' + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_pin(pin, platform):
    """Additional successful jobs must be named before a ready pin can run."""
    validate_adblock_contract(TOOLS.parent / 'staging/mouse/6.0.41-arm64')
    validate_settings_contract(TOOLS.parent / 'staging/mouse/6.0.41-arm64')
    validate_workspace_contract(TOOLS.parent / 'staging/mouse/6.0.41-arm64')
    previous = runpy.run_path(str(TOOLS / 'mouse641-reuse.py'))['previous'](platform)
    need(pin.get('currentPrevious') == previous, 'actual published638 predecessor pin differs')
    prefix = {'linux': 'noble', 'win32': 'modern'}.get(platform)
    if prefix is None:
        return
    keys = (prefix + 'Job', prefix + 'Artifact', prefix + 'SHA256')
    if pin.get('ready') is False:
        need(all(pin.get(key) is None for key in keys), 'unready candidate claims additional native acceptance')
    else:
        need(pin.get('ready') is True and all(type(pin.get(key)) is int and pin[key] > 0 for key in keys[:2])
             and isinstance(pin.get(keys[2]), str) and re.fullmatch('[0-9a-f]{64}', pin[keys[2]]),
             'ready candidate lacks its exact additional native job/artifact/hash: ' + prefix)


def validate_contract(stage):
    contract = json.loads((stage / 'evidence.schema.json').read_text())['x-current638RenderingGate']
    dependencies = ('mouse641-task-evidence.py', 'mouse-638-crx-proof.cjs',
                    'mouse641-extra-evidence.py', 'mouse641-reuse.py', 'mouse641-frozen.json')
    need(contract.get('dependencies') == {name: sha((TOOLS / name).read_bytes()) for name in dependencies},
         'independent638 checker dependencies changed')
    need(contract.get('required') == ['mouse-638-acceptance.json', 'mouse-638-feedback.json',
         'mouse-638-feedback-processes.json', 'mouse-638-feedback-write.json', 'mouse-638-webstore.crx'],
         'independent638 checker required source/fresh evidence differs')
    validate_adblock_contract(stage)
    validate_settings_contract(stage)
    validate_workspace_contract(stage)


def validate_adblock_contract(stage):
    contract = json.loads((stage / 'evidence.schema.json').read_text())['x-current639AdblockGate']
    need(contract.get('validator') == 'tools/mouse641-adblock-evidence.py'
         and contract.get('sha256') == sha((TOOLS / 'mouse641-adblock-evidence.py').read_bytes())
         and contract.get('sourceAndFreshInstalled') is True,
         'independent639 AdBlock validator identity changed')
    need(contract.get('dependencies') == {name: sha((TOOLS / name).read_bytes()) for name in ADBLOCK_DEPENDENCIES}
         and contract.get('required') == list(ADBLOCK_REQUIRED),
         'independent639 AdBlock dependency/receipt contract changed')
    runpy.run_path(str(TOOLS / 'mouse641-reuse.py'))['verify_frozen']()


def validate_settings_contract(stage):
    contract = json.loads((stage / 'evidence.schema.json').read_text())['x-current640SettingsGate']
    need(contract.get('validator') == 'tools/mouse641-settings-evidence.py'
         and contract.get('sha256') == sha((TOOLS / 'mouse641-settings-evidence.py').read_bytes())
         and contract.get('sourceAndFreshInstalled') is True
         and contract.get('savedReportAcceptedAsInput') is False,
         'independent640 Settings validator identity changed')
    need(contract.get('dependencies') == {name: sha((TOOLS / name).read_bytes()) for name in SETTINGS_DEPENDENCIES}
         and contract.get('required') == list(SETTINGS_REQUIRED),
         'independent640 Settings dependency/receipt contract changed')


def validate_workspace_contract(stage):
    contract = json.loads((stage / 'evidence.schema.json').read_text())['x-current641WorkspaceGate']
    need(contract.get('validator') == 'tools/mouse641-flexible-workspace-evidence.py'
         and contract.get('sha256') == sha((TOOLS / 'mouse641-flexible-workspace-evidence.py').read_bytes())
         and contract.get('sourceAndFreshInstalled') is True and contract.get('savedReportAcceptedAsInput') is False,
         'independent641 workspace validator identity changed')
    need(contract.get('dependencies') == {name: sha((TOOLS / name).read_bytes()) for name in WORKSPACE_DEPENDENCIES}
         and contract.get('required') == list(WORKSPACE_REQUIRED)
         and contract.get('featureTokens') == list(WORKSPACE_TOKENS), 'independent641 workspace dependency/receipt contract changed')


def verify_helper_bytes(output):
    """The fetched source checker/proof must match independent publisher code."""
    source = (output / 'mouse-638-acceptance.py').read_bytes()
    need(source.replace(b'mouse-631-acceptance.py', b'mouse641-task-evidence.py') ==
         (TOOLS / 'mouse641-rendering-evidence.py').read_bytes(), 'source638 checker differs from independent publisher reader')
    need((output / 'mouse-638-crx-proof.cjs').read_bytes() == (TOOLS / 'mouse-638-crx-proof.cjs').read_bytes(),
         'source638 signed CRX proof differs from independent publisher reader')
    source639 = (output / 'mouse-639-acceptance.py').read_bytes()
    need(source639.replace(b'mouse-631-acceptance.py', b'mouse641-task-evidence.py') ==
         (TOOLS / 'mouse641-adblock-evidence.py').read_bytes(),
         'source639 AdBlock checker differs from independent publisher reader')
    source640 = (output / 'mouse-640-settings-acceptance.py').read_bytes()
    need(source640.replace(b'mouse-631-acceptance.py', b'mouse641-task-evidence.py') ==
         (TOOLS / 'mouse641-settings-evidence.py').read_bytes(),
         'source640 Settings checker differs from independent publisher reader')
    source641 = (output / 'mouse-641-workspace-acceptance.py').read_bytes()
    need(source641.replace(b'mouse-631-acceptance.py', b'mouse641-task-evidence.py') ==
         (TOOLS / 'mouse641-flexible-workspace-evidence.py').read_bytes(),
         'source641 workspace checker differs from independent publisher reader')


def workspace(read, *, platform, arch, build=None, verification=None):
    accepted = runpy.run_path(str(TOOLS / 'mouse641-flexible-workspace-evidence.py'))['verify'](
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
    accepted = runpy.run_path(str(TOOLS / 'mouse641-settings-evidence.py'))['verify'](
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
    accepted = runpy.run_path(str(TOOLS / 'mouse641-adblock-evidence.py'))['verify'](
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
    accepted = runpy.run_path(str(TOOLS / 'mouse641-rendering-evidence.py'))['verify'](
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


def noble(read, pin, *, expected_asar):
    facts = json.loads(read('mouse-linux-install-noble.json'))
    package_name = 'Mouse-Browser-6.0.41-Linux-x64.deb'
    need(facts.get('ok') is True and not facts.get('error') and facts.get('source') == pin['source']
         and (facts.get('version'), facts.get('platform'), facts.get('arch')) == (VERSION, 'linux', 'x64')
         and str(facts.get('runId')) == str(pin['run']) and str(facts.get('runAttempt')) == str(pin['attempt'])
         and facts.get('package') == {'name': package_name, **pin['packages'][package_name]}, 'Ubuntu24 candidate provenance differs')
    need(re.search(r'^ID=ubuntu$', facts.get('osRelease', ''), re.M)
         and re.search(r'^VERSION_ID="24\.04"$', facts['osRelease'], re.M)
         and facts.get('ownerDeviceVerified') is False, 'missing actual Ubuntu24 host identity')
    need(isinstance(facts.get('policyBefore'), dict) and facts.get('policyAfter') == facts['policyBefore'],
         'Ubuntu24 check changed user-namespace policy')
    receipt(read, facts.get('cleanDependencies', {}), 'mouse-linux-clean-dependencies.log',
            ['MOUSE_LINUX_CLEAN_DEB_DEPENDENCIES_PASS'], 480000)
    need(isinstance(facts.get('containerImage'), list) and facts['containerImage']
         and all(re.fullmatch(r'ubuntu@sha256:[0-9a-f]{64}', item) for item in facts['containerImage']), 'clean dependency container is not digest-bound')
    install = facts.get('installation', {})
    receipt(read, install, 'mouse-linux-noble-install.log', [], 180000)
    need(install.get('packageName') == 'mouse-browser' and install.get('version') == VERSION
         and str(install.get('executable', '')).startswith('/opt/') and install['executable'].endswith('/mouse-browser'),
         'APT did not install the expected executable')
    need(install.get('desktopFile') == '/usr/share/applications/mouse-browser.desktop'
         and all(re.fullmatch('[0-9a-f]{64}', install.get(key, '')) for key in ('desktopSha256', 'executableSha256')),
         'APT installation lacks desktop/executable byte identity')
    if facts['policyBefore'].get('apparmor_restrict_unprivileged_userns') == '1':
        need(facts.get('apparmorProfile', {}).get('path') == '/etc/apparmor.d/mouse-browser'
             and re.fullmatch('[0-9a-f]{64}', facts['apparmorProfile'].get('sha256', '')), 'restricted user namespaces lack package AppArmor evidence')
    native, processes = {}, facts.get('nativeProcesses', {})
    pixels = runpy.run_path(str(TOOLS / 'mouse641-task-evidence.py'))
    for phase, budget, marker in [('write', 300000, 'MOUSE_LINUX_PROFILE_WRITE_PASS'), ('read', 100000, 'MOUSE_LINUX_PROFILE_RESTART_PASS')]:
        row = processes.get(phase, {})
        receipt(read, row, 'mouse-linux-noble-' + phase + '.log', [marker, 'MOUSE_LINUX_X64_SMOKE_PASS'], budget)
        name = 'mouse-linux-smoke-' + phase + '.json'
        raw = read(name)
        need(row.get('report') == name and row.get('reportSha256') == sha(raw), 'Ubuntu24 native report bytes differ')
        report = json.loads(raw)
        need(report.get('ok') is True and not report.get('error') and report.get('version') == VERSION
             and (report.get('platform'), report.get('arch')) == ('linux', 'x64')
             and report.get('pid') == row['pid'] and report.get('packageFormat') == 'deb'
             and report.get('executable') == install['executable']
             and report.get('physicalUserDeviceVerified') is False, 'Ubuntu24 native report identity differs')
        sandbox = report.get('sandbox', {})
        renderers = sandbox.get('renderers', [])
        need(sandbox.get('disabledFlags') == [] and len(renderers) >= 2
             and all(r.get('seccomp') == 2 and r.get('noNewPrivs') == 1 and type(r.get('uid')) is int and r['uid'] > 0
                     and r.get('preferences') == {'sandbox': True, 'contextIsolation': True, 'nodeIntegration': False, 'webSecurity': True}
                     for r in renderers), 'Ubuntu24 renderer sandbox evidence missing')
        need(re.fullmatch('[0-9a-f]{64}', report.get('asarSha256', '')), 'installed Ubuntu24 ASAR bytes missing')
        need(report['asarSha256'] == expected_asar, 'Ubuntu24 ASAR differs from the accepted source packages')
        captures = report.get('captures', [])
        need(len(captures) == 2 and {c.get('theme') for c in captures} == {'dark', 'light'}, 'both Ubuntu24 themes are required')
        for capture in captures:
            filename = 'mouse-linux-' + phase + '-' + capture['theme'] + '.png'
            image = read(filename)
            need(capture.get('filename') == filename and capture.get('sha256') == sha(image)
                 and capture.get('source') == 'globalCapture.acquire(display)' and capture.get('backend') == 'desktopCapturer', 'Ubuntu24 native screen capture differs')
            decoded = pixels['decode_png'](image, filename)
            need(capture.get('screenPixelSize') == {k: decoded[k] for k in ('width', 'height')}, 'Ubuntu24 capture dimensions differ')
        native[phase] = report
    need(processes['write']['pid'] != processes['read']['pid'] and native['write']['asarSha256'] == native['read']['asarSha256'],
         'Ubuntu24 restart did not use distinct processes with the same installed bytes')
    need(native['write'].get('profile', {}).get('written') is True, 'Ubuntu24 profile was not written')
    profile = native['read'].get('profile', {})
    need(all(profile.get(k) is True for k in ('differentProcess', 'preferencesPreserved', 'cookiePreserved', 'localStoragePreserved', 'bookmarkPreserved'))
         and profile.get('previousPid') == processes['write']['pid'] and profile.get('currentPid') == processes['read']['pid']
         and re.fullmatch('[0-9a-f]{64}', profile.get('tokenSha256', ''))
         and profile.get('tokenSha256') == native['write']['profile'].get('tokenSha256')
         and profile.get('pageId') and profile['pageId'] == native['write']['profile'].get('pageId'), 'Ubuntu24 native profile restart failed')
    need(isinstance(facts.get('adblock639'), dict), 'Ubuntu24 installed verification omits AdBlock639')
    adblock_result = adblock(read, platform='linux', arch='x64', wrapper=facts['adblock639'], installation=install)
    adblock_processes = json.loads(read('mouse-639-adblock-processes.json'))
    need(adblock_processes.get('executable') == install['executable']
         and adblock_processes.get('executableSha256') == install['executableSha256'],
         'Ubuntu24 AdBlock evidence belongs to a different installed executable')
    return {'ok': True, 'source': pin['source'], 'package': facts['package'], 'os': 'Ubuntu24.04', 'ownerDeviceVerified': False,
            'reportSha256': sha(read('mouse-linux-install-noble.json')), 'nativePids': [processes[p]['pid'] for p in ('write', 'read')],
            'adblock639': adblock_result}


def import_extra(module, platform):
    pin = module['PIN'] if platform == 'darwin' else module['pin']()
    validate_pin(pin, platform)
    output, api = module['OUT'], module['api']
    verify_helper_bytes(output)
    stem, artifact_name, arch = ('mouse-build', 'mouse-arm64-verification', 'arm64') if platform == 'darwin' else (
        ('mouse-linux-build', 'mouse-linux-x64-verification', 'x64') if platform == 'linux' else
        ('mouse-windows-build', 'mouse-windows-x64-verification', 'x64'))
    build = json.loads((output / (stem + '.json')).read_text())
    with artifact(api, pin, id_key='verificationArtifact', hash_key='verificationSHA256', name=artifact_name, output=output) as archive:
        accepted = feedback(archive.read, platform=platform, arch=arch, build=build)
        accepted_adblock = adblock(archive.read, platform=platform, arch=arch, build=build)
        accepted_settings = settings(archive.read, platform=platform, arch=arch, build=build)
        accepted_workspace = workspace(archive.read, platform=platform, arch=arch, build=build)
    (output / 'source638-feedback-independent.json').write_text(json.dumps(accepted, indent=2) + '\n')
    (output / 'source639-adblock-independent.json').write_text(json.dumps(accepted_adblock, indent=2) + '\n')
    (output / 'source640-settings-independent.json').write_text(json.dumps(accepted_settings, indent=2) + '\n')
    (output / 'source641-workspace-independent.json').write_text(json.dumps(accepted_workspace, indent=2) + '\n')
    if platform == 'linux':
        source_job = job(api, pin, 'nobleJob', 'mouse-linux-install-noble', ['Check clean package dependencies and native Ubuntu 24.04 launch'])
        with artifact(api, pin, id_key='nobleArtifact', hash_key='nobleSHA256', name='mouse-linux-install-noble-verification', output=output, source_job=source_job) as archive:
            accepted = noble(archive.read, pin, expected_asar=build['verification']['result']['checks']['appImageLaunch']['asarSha256'])
        (output / 'source638-noble-independent.json').write_text(json.dumps(accepted, indent=2) + '\n')
    elif platform == 'win32':
        source_job = job(api, pin, 'modernJob', 'mouse-windows-x64-modern', ['Verify immutable installer and source evidence', 'Verify same installed app on modern Windows'])
        with artifact(api, pin, id_key='modernArtifact', hash_key='modernSHA256', name='mouse-windows-x64-modern-verification', output=output, source_job=source_job) as archive:
            modern = json.loads(archive.read('mouse-windows-modern-input.json'))
            need(modern.get('ok') is True and modern.get('source') == pin['source'] and modern.get('package') == pin['package']
                 and str(modern.get('runId')) == str(pin['run']) and str(modern.get('sourceRunAttempt')) == str(pin['attempt'])
                 and modern.get('sourceVerificationSha256') == build['verification']['sha256'], 'modern Windows reused another installer/source')
            verification = json.loads(archive.read('mouse-windows-verification.json'))
            module['verification'](verification)
            module['verify_task_evidence'](archive.read, verification)
            module['verify_feedback_evidence'](archive.read)
            module['_verify_current_upgrade'](archive.read, pin)
            accepted = feedback(archive.read, platform='win32', arch='x64')
            accepted_adblock = adblock(archive.read, platform='win32', arch='x64', verification=verification)
            accepted_settings = settings(archive.read, platform='win32', arch='x64')
            accepted_workspace = workspace(archive.read, platform='win32', arch='x64', verification=verification)
        (output / 'source638-modern-independent.json').write_text(json.dumps(accepted, indent=2) + '\n')
        (output / 'source639-modern-adblock-independent.json').write_text(json.dumps(accepted_adblock, indent=2) + '\n')
        (output / 'source640-modern-settings-independent.json').write_text(json.dumps(accepted_settings, indent=2) + '\n')
        (output / 'source641-modern-workspace-independent.json').write_text(json.dumps(accepted_workspace, indent=2) + '\n')
    print('MOUSE_639_SOURCE_SUPPLEMENTAL_ACCEPTANCE_PASS', flush=True)


def fresh(module, platform):
    output = module['OUT']
    read = lambda name: (output / name).read_bytes()
    arch = 'arm64' if platform == 'darwin' else 'x64'
    accepted = feedback(read, platform=platform, arch=arch)
    (output / 'installed638-feedback-independent.json').write_text(json.dumps(accepted, indent=2) + '\n')
    verification = None
    if platform != 'darwin':
        name = 'mouse-linux-verification.json' if platform == 'linux' else 'mouse-windows-verification.json'
        verification = json.loads(read(name))
    accepted_adblock = adblock(read, platform=platform, arch=arch, verification=verification)
    (output / 'installed639-adblock-independent.json').write_text(json.dumps(accepted_adblock, indent=2) + '\n')
    accepted_settings = settings(read, platform=platform, arch=arch)
    (output / 'installed640-settings-independent.json').write_text(json.dumps(accepted_settings, indent=2) + '\n')
    accepted_workspace = workspace(read, platform=platform, arch=arch, verification=verification)
    (output / 'installed641-workspace-independent.json').write_text(json.dumps(accepted_workspace, indent=2) + '\n')
    return accepted
