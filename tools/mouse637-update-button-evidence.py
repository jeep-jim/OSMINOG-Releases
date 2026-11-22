#!/usr/bin/env python3
"""Independently validate actual636 UI update, installer, relaunch and profile bytes."""
import math
import ntpath
from pathlib import Path, PurePosixPath, PureWindowsPath
import posixpath
import re
import runpy

U = runpy.run_path(str(Path(__file__).with_name('mouse637-upgrade-evidence.py')))
NAME = 'mouse-637-update-button.json'
MARKER = 'MOUSE_637_REAL_636_TO_637_UPDATE_BUTTON_PASS'
NATIVE = 'mouse-637-update-button-native'
NATIVE_MARKER = 'MOUSE_637_UPDATE_BUTTON_NATIVE_PASS'
SOURCE = '7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3'
UPDATER_BLOB = '91ab363f926774825caf8055b2d3d81bf0d51264'
VERSION, PREVIOUS = '6.0.37', '6.0.36'
CHANNELS = {
    'darwin': 'https://raw.githubusercontent.com/jeep-jim/OSMINOG-Releases/main/channels/mouse/macos-arm64.json',
    'win32': 'https://raw.githubusercontent.com/jeep-jim/OSMINOG-Releases/main/platforms/windows/mouse-x64/latest.json',
    'linux': 'https://raw.githubusercontent.com/jeep-jim/OSMINOG-Releases/main/platforms/linux/mouse-x64/latest.json',
}
TAGS = {'darwin': 'quadro-macos-v6.0.37-arm64', 'win32': 'mouse-windows-v6.0.37-x64', 'linux': 'mouse-linux-v6.0.37-x64'}
BACKENDS = {'darwin': 'CGEvent', 'win32': 'User32', 'linux': 'XTest'}
WINDOWS = {'darwin': 'CGWindowListCopyWindowInfo layer-zero on-screen window',
           'win32': 'User32 EnumWindows top-level visible window', 'linux': 'X11 managed WM_STATE window'}
need, sha, positive = U['need'], U['sha'], U['positive']


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def digest(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def absolute(value, platform):
    return isinstance(value, str) and 0 < len(value) <= 32768 and '\0' not in value and (
        PureWindowsPath(value).is_absolute() if platform == 'win32' else PurePosixPath(value).is_absolute())


def same_path(a, b, platform):
    if not absolute(a, platform) or not absolute(b, platform):
        return False
    return ntpath.normcase(ntpath.normpath(a)) == ntpath.normcase(ntpath.normpath(b)) if platform == 'win32' else posixpath.normpath(a) == posixpath.normpath(b)


def raw_file(read, name, *, limit=16 * 1024**2):
    raw = read(name)
    need(isinstance(raw, bytes) and 0 < len(raw) <= limit, 'missing or oversized button evidence: ' + name)
    return raw


def receipt(read, row, name, *, limit=16 * 1024**2):
    raw = raw_file(read, name, limit=limit)
    need(row == {'filename': name, 'bytes': len(raw), 'sha256': sha(raw)}, 'button raw-byte receipt differs: ' + name)
    return raw


def linux_binding(process, target):
    identity = process.get('identity', {})
    uid = process.get('uid')
    need(positive(uid) and identity.get('uid') == uid and positive(identity.get('startTicks'))
         and same_path(process.get('expectedExecutable'), target, 'linux'), 'Linux native process identity missing')
    chain = process.get('launchAncestry')
    need(isinstance(chain, list) and 0 < len(chain) <= 16 and chain[0].get('pid') == process['pid']
         and all(isinstance(row, dict) and positive(row.get('pid')) and type(row.get('parentPid')) is int
                 and row['parentPid'] >= 0 and row.get('uid') == uid and row.get('state') != 'Z' for row in chain)
         and len({row['pid'] for row in chain}) == len(chain)
         and all(chain[i]['parentPid'] == chain[i + 1]['pid'] for i in range(len(chain) - 1)),
         'native Linux window has a broken process ancestry')
    # Reuse immutable raw mount decoding and boundary validation, but this
    # daemon-aware witness has its own identity, not a fabricated launch receipt.
    mount = process.get('mount', {})
    raw = mount.get('raw')
    need(isinstance(raw, str) and 0 < len(raw) <= 16384 and not any(c in raw for c in '\0\r\n'), 'native mountinfo absent')
    fields = raw.split(' '); separator = fields.index('-') if '-' in fields else -1
    need(separator >= 6 and len(fields) == separator + 4 and all(fields)
         and re.fullmatch('[1-9]\\d*', fields[0]) and re.fullmatch('[1-9]\\d*', fields[1])
         and re.fullmatch('\\d+:\\d+', fields[2]), 'native mountinfo malformed')
    decode = lambda value: re.sub(r'\\(040|011|012|134)', lambda match: chr(int(match[1], 8)), value)
    decoded = {'raw': raw, 'mountId': int(fields[0]), 'parentMountId': int(fields[1]), 'device': fields[2],
               'root': decode(fields[3]), 'mountPoint': decode(fields[4]), 'options': fields[5].split(','),
               'filesystem': fields[separator + 1], 'source': decode(fields[separator + 2]), 'superOptions': fields[separator + 3].split(',')}
    need(mount == decoded and mount['root'] == '/' and mount['mountPoint'] not in ('', '/')
         and absolute(mount['mountPoint'], 'linux') and not mount['mountPoint'].startswith('//')
         and posixpath.normpath(mount['mountPoint']) == mount['mountPoint']
         and re.fullmatch(r'fuse(?:\.(?:[^\s/\\\0]|\\040)+)?', mount['filesystem'])
         and 'ro' in mount['options'] and 'rw' not in mount['options']
         and process.get('executable') == mount['mountPoint'] + '/mouse-browser', 'native window lacks exact read-only FUSE mount')
    need('environmentAppImage' in process and process['environmentAppImage'] in (None, target)
         and 'environmentProfile' in process, 'native environment diagnostic conflicts or is missing')
    binding = process.get('imageBinding', {})
    need(binding.get('path') == target and positive(binding.get('pid')), 'actual AppImage binding missing')
    if binding.get('kind') == 'exact AppImage runtime and inherited FUSE keepalive pipe':
        backing, pipes = binding.get('backingImage', {}), binding.get('pipes')
        need(binding.get('pid') != process['pid'] and positive(binding.get('startTicks'))
             and binding.get('mountId') == mount['mountId'] and backing.get('pid') == binding['pid']
             and backing.get('path') == target and positive(backing.get('inode'))
             and backing.get('kind') in ('ancestor executable', 'ancestor mapped backing image', 'ancestor open backing image')
             and isinstance(pipes, list) and 0 < len(pipes) <= 4096
             and all(isinstance(row, dict) and type(row.get('device')) is int and row['device'] >= 0
                     and positive(row.get('inode')) and type(row.get('browserReadFD')) is int and row['browserReadFD'] >= 0
                     and type(row.get('runtimeWriteFD')) is int and row['runtimeWriteFD'] >= 0 for row in pipes)
             and len({(row['device'], row['inode']) for row in pipes}) == len(pipes),
             'daemonized runtime is not bound by actual read/write kernel pipe ends')
    elif binding.get('kind') == 'observed initial APPIMAGE environment and read-only FUSE executable':
        need(binding['pid'] == process['pid'] and process['environmentAppImage'] == target,
             'claimed initial APPIMAGE was not observed')
    else:
        need(binding.get('kind') in ('ancestor executable', 'ancestor mapped backing image', 'ancestor open backing image')
             and binding['pid'] in {row['pid'] for row in chain} and positive(binding.get('inode')),
             'AppImage is not bound to its actual native ancestor')


def native_driver(row, *, platform, profile, executable, sentinel, action, pid=None):
    need(isinstance(row, dict) and row.get('schema') == 1 and row.get('ok') is True and not row.get('error')
         and row.get('platform') == platform and row.get('action') == action
         and row.get('terminationUsed') is False and row.get('sentinelSha256') == sentinel
         and same_path(row.get('profile'), profile, platform) and same_path(row.get('expectedExecutable'), executable, platform)
         and finite(row.get('elapsedMs')) and 0 <= row['elapsedMs'] <= 45000,
         'native window helper identity, ownership or bounded action differs')
    process, window, input_ = row.get('process', {}), row.get('window', {}), row.get('nativeInput', {})
    need(positive(process.get('pid')) and process.get('sameUser') is True
         and process.get('identity', {}).get('pid') == process['pid']
         and (pid is None or process['pid'] == pid) and window.get('pid') == process['pid']
         and positive(window.get('handle')) and window.get('visible') is True,
         'native input was not tied to one visible owned process')
    need(window.get('source') == WINDOWS[platform], 'window was not observed through the platform native API')
    bounds = window.get('bounds', {})
    need(all(finite(bounds.get(key)) for key in ('x', 'y', 'width', 'height'))
         and 100 <= bounds['width'] <= 32768 and 100 <= bounds['height'] <= 32768, 'native window bounds are invalid')
    need(input_.get('backend') == BACKENDS[platform] and input_.get('foregroundVerified') is True
         and input_.get('action') == action
         and input_.get('coordinateSpace') == ('quartz-screen-points' if platform == 'darwin' else 'physical-screen-pixels'),
         'native input backend or verified foreground missing')
    identity = process['identity']
    if platform == 'linux':
        linux_binding(process, executable)
        need(process['environmentProfile'] in (None, profile), 'observed Linux profile differs')
    else:
        need(same_path(process.get('executable'), executable, platform), 'native window belongs to another executable')
        if platform == 'darwin':
            need(positive(process.get('uid')) and identity.get('uid') == process['uid']
                 and isinstance(identity.get('started'), str) and bool(identity['started']), 'macOS native birth identity absent')
        else:
            need(isinstance(identity.get('creationTime100ns'), str) and re.fullmatch('[1-9]\\d*', identity['creationTime100ns'])
                 and isinstance(process.get('userSID'), str) and re.fullmatch(r'S-1-\d+(?:-\d+)+', process['userSID'])
                 and identity.get('userSID') == process['userSID'], 'Windows native birth/owner identity absent')
    if action == 'click':
        need(all(finite(input_.get(key)) for key in ('x', 'y'))
             and bounds['x'] <= input_['x'] < bounds['x'] + bounds['width']
             and bounds['y'] <= input_['y'] < bounds['y'] + bounds['height'], 'native click is outside the verified window')
    else:
        exit_ = row.get('exit', {})
        need(input_.get('accelerator') == ('Cmd+Q' if platform == 'darwin' else 'Ctrl+Q')
             and exit_.get('observed') is True and exit_.get('graceful') is True and exit_.get('terminationUsed') is False
             and exit_.get('method') == 'production native quit accelerator'
             and exit_.get('exitCode') == (0 if platform == 'win32' else None), 'automatic relaunch did not quit through production native lifecycle')
    return process


def verify(read, *, expected_platform, expected_arch, expected_package=None, expected_packages=None):
    platform, arch = expected_platform, expected_arch
    need((platform, arch) in (('darwin', 'arm64'), ('win32', 'x64'), ('linux', 'x64')), 'unsupported native button target')
    raw, facts = U['read_json'](read, NAME)
    baseline = U['BASELINES'][platform]['appimage'] if platform == 'linux' else U['BASELINES'][platform]
    baseline = {**baseline, 'url': 'https://github.com/jeep-jim/OSMINOG-Releases/releases/download/' + baseline['tag'] + '/' + baseline['name'],
                'source': SOURCE, 'updaterBlobSHA': UPDATER_BLOB}
    if platform == 'linux':
        name = 'Mouse-Browser-6.0.37-Linux-x64.AppImage'
        need(isinstance(expected_packages, dict) and name in expected_packages, 'actual AppImage candidate missing')
        package = {'name': name, **expected_packages[name]}
    else:
        package = expected_package
    need(isinstance(package, dict) and set(package) == {'name', 'size', 'sha256'} and positive(package['size'])
         and package['size'] <= 512 * 1024**2 and digest(package['sha256']), 'immutable native candidate identity missing')
    need(facts.get('schema') == 1 and facts.get('ok') is True and not facts.get('error')
         and (facts.get('version'), facts.get('fromVersion'), facts.get('toVersion'), facts.get('platform'), facts.get('arch'))
         == (VERSION, PREVIOUS, VERSION, platform, arch) and facts.get('baseline') == baseline and facts.get('package') == package
         and facts.get('method') == 'actual published636 native update buttons and actual637 profile restart'
         and facts.get('physicalUserDeviceVerified') is False and facts.get('publicChannelDownloadVerified') is False
         and facts.get('differentProcesses') is True, 'actual button scope, package or predecessor differs')
    sentinel = facts.get('ownerSentinel', {})
    need(sentinel.get('name') == 'mouse637-update-owner.txt' and digest(sentinel.get('sha256')) and sentinel.get('preserved') is True,
         'owned updater profile sentinel was not retained')
    outer_log = raw_file(read, 'mouse-637-update-button.log')
    need(MARKER in outer_log.decode('utf-8').splitlines(), 'real update button marker missing')
    inputs = {NAME: sha(raw), 'mouse-637-update-button.log': sha(outer_log)}
    native_raw, native = U['read_json'](read, NATIVE + '.json')
    bound = facts.get('native', {})
    need(bound.get('report') == NATIVE + '.json' and bound.get('reportSha256') == sha(native_raw)
         and bound.get('result') == native and positive(bound.get('pid')) and bound.get('exitCode') == 0
         and finite(bound.get('elapsedMs')) and 0 < bound['elapsedMs'] <= 360000
         and bound.get('requiredMarkers') == [NATIVE_MARKER], 'native button process/report binding differs')
    log = raw_file(read, NATIVE + '.log')
    need(bound.get('log') == NATIVE + '.log' and bound.get('logSha256') == sha(log)
         and NATIVE_MARKER in log.decode('utf-8').splitlines(), 'native button process log differs')
    inputs.update({NATIVE + '.json': sha(native_raw), NATIVE + '.log': sha(log)})
    candidate = native.get('package', {})
    url = 'https://github.com/jeep-jim/OSMINOG-Releases/releases/download/' + TAGS[platform] + '/' + package['name']
    need(candidate == {**package, 'version': VERSION, 'path': candidate.get('path'), 'url': url}
         and absolute(candidate.get('path'), platform)
         and (PureWindowsPath(candidate['path']).name if platform == 'win32' else PurePosixPath(candidate['path']).name) == package['name'],
         'native transport candidate differs from immutable package')
    need(native.get('schema') == 1 and native.get('ok') is True and not native.get('error')
         and native.get('stage') == 'complete' and native.get('budgetMs') == 300000
         and finite(native.get('elapsedMs')) and 0 < native['elapsedMs'] < 300000
         and (native.get('fromVersion'), native.get('toVersion'), native.get('platform'), native.get('arch')) == (PREVIOUS, VERSION, platform, arch)
         and native.get('method') == 'unchanged installed predecessor with CI-only fetch transport; native UI and stock installer'
         and native.get('baseline') == baseline and native.get('physicalUserDeviceVerified') is False
         and native.get('publicChannelDownloadVerified') is False and native.get('inspectorClosedBeforeInstall') is True,
         'native button method, budget or unchanged installer scope differs')
    prefix = 'mouse-637-update-button-profile' + ('-appimage' if platform == 'linux' else '')
    reports, profile_inputs = U['profile_pair'](read, facts, platform, arch, package, baseline, prefix, 'appimage' if platform == 'linux' else None)
    inputs.update(profile_inputs)
    before, after = reports
    old = native.get('oldProcess', {})
    need(old.get('version') == PREVIOUS and old.get('platform') == platform and old.get('arch') == arch
         and old.get('packaged') is True and positive(old.get('pid')) and positive(native.get('launcherPid'))
         and native.get('previousWriterPid') == before['pid'] and old.get('pid') != before['pid']
         and old.get('updaterBlobSHA') == UPDATER_BLOB and digest(old.get('installerSha256'))
         and all(old.get(key) is True for key in ('transportOnly', 'selectionUnchanged', 'verificationUnchanged', 'installerUnchanged'))
         and absolute(old.get('profile'), platform) and absolute(old.get('executable'), platform) and absolute(old.get('appPath'), platform),
         'published636 updater was not an unchanged distinct installed process')
    if platform == 'linux':
        need(digest(old.get('linuxInstallerSha256')) and facts.get('packageFormat') == 'appimage'
             and facts.get('debInstallation') == 'manual package-manager path independently verified by mouse-637-upgrade.json',
             'Linux automatic updater must retain its actual AppImage scope')
    old_log_receipt = native.get('oldLifecycle', {})
    need(old_log_receipt.get('exitSaved') is True and old_log_receipt.get('quit') is True
         and native.get('oldExit') == {'code': 0, 'signal': None}, 'predecessor did not save and quit')
    old_log = receipt(read, old_log_receipt.get('appLog'), NATIVE + '-app.log')
    inputs[NATIVE + '-app.log'] = sha(old_log)
    old_text = old_log.decode('utf-8')
    need(all(marker in old_text for marker in ('MOUSE_EXIT_SAVED', 'MOUSE_APP_QUIT')), 'predecessor lifecycle raw log missing')
    clicks = native.get('nativeInputs')
    need(isinstance(clicks, list) and [row.get('selector') for row in clicks] == ['#version-button', '#update-download', '#update-install'],
         'all three actual update controls must receive native clicks')
    driver_target = clicks[0].get('driver', {}).get('expectedExecutable')
    need(absolute(driver_target, platform), 'exact installed native target absent')
    events = []
    for line in old_text.splitlines():
        if line.startswith('MOUSE_637_BUTTON_CLICK '):
            import json
            events.append(json.loads(line[len('MOUSE_637_BUTTON_CLICK '):]))
    for click in clicks:
        process = native_driver(click.get('driver'), platform=platform, profile=old['profile'], executable=driver_target,
                                sentinel=sentinel['sha256'], action='click', pid=old['pid'])
        point, event = click.get('point', {}), click.get('event', {})
        need(click.get('source') == BACKENDS[platform] and finite(click.get('at'))
             and all(point.get(key) == click['driver']['nativeInput'][key] for key in ('x', 'y'))
             and event.get('selector') == click['selector'] and event.get('trusted') is True and event.get('type') == 'click'
             and event.get('button') == 0 and all(finite(event.get(key)) for key in ('x', 'y', 'at'))
             and event in events, 'update control lacks trusted OS-input event in actual app log')
        need(same_path(process['executable'], old['executable'], platform), 'clicked process differs from observed predecessor')
        need(process['identity'] == clicks[0]['driver']['process']['identity'], 'predecessor birth identity changed between native clicks')
    available, downloaded = native.get('available', {}), native.get('downloaded', {})
    for state, phase in ((available, 'available'), (downloaded, 'ready')):
        need(state.get('phase') == phase and state.get('currentVersion') == PREVIOUS and state.get('availableVersion') == VERSION
             and state.get('channel') == 'static' and not state.get('error'), 'production updater state differs')
    need(downloaded.get('canInstall') is True and downloaded.get('percent') == 100, 'production candidate was not fully downloaded/verified')
    download = native.get('download', {})
    need(download.get('candidate') == {'version': VERSION, 'name': package['name'], 'url': url, 'size': package['size'], 'hash': package['sha256']}
         and absolute(download.get('file'), platform), 'production-selected candidate bytes differ')
    requests = download.get('requests', [])
    need(isinstance(requests, list) and [row.get('url') for row in requests] == [CHANNELS[platform], url]
         and all(finite(row.get('at')) and re.fullmatch(r'http://127\.0\.0\.1:[1-9]\d*/(?:channel|package)', row.get('fixtureURL', '')) for row in requests)
         and requests[0]['fixtureURL'].removesuffix('/channel') == requests[1]['fixtureURL'].removesuffix('/package'),
         'transport must be the owned loopback channel and exact package only')
    transport = native.get('fixtureRequests', [])
    need(isinstance(transport, list) and [row.get('path') for row in transport] == ['/channel', '/package']
         and all(row.get('method') == 'GET' and row.get('complete') is True and positive(row.get('bytes')) and finite(row.get('at')) for row in transport)
         and transport[1]['bytes'] == package['size'], 'fixture did not serve complete immutable candidate bytes')
    captures = native.get('captures', [])
    need(isinstance(captures, list) and [row.get('filename') for row in captures] == ['mouse-637-update-button-available.png', 'mouse-637-update-button-ready.png'],
         'both real update UI captures are required')
    decode_png = runpy.run_path(str(Path(__file__).with_name('mouse637-task-evidence.py')))['decode_png']
    for capture in captures:
        data = receipt(read, {k: capture.get(k) for k in ('filename', 'bytes', 'sha256')}, capture['filename'])
        image = decode_png(data, capture['filename'])
        need(len(data) > 1000 and capture.get('source') == 'installed shell compositor'
             and (capture.get('width'), capture.get('height')) == (image['width'], image['height']), 'button capture pixels/dimensions differ')
        inputs[capture['filename']] = sha(data)
    installed, ack = native.get('installerReceipt', {}), native.get('acknowledgement', {})
    path_module = ntpath if platform == 'win32' else posixpath
    need(installed.get('version') == VERSION and absolute(installed.get('stage'), platform)
         and same_path(installed.get('target'), str(PurePosixPath(driver_target).parents[2]) if platform == 'darwin' else driver_target, platform)
         and ack.get('version') == VERSION and same_path(ack.get('readyPath'), path_module.join(installed['stage'], 'READY'), platform)
         and ack.get('receiptRemoved') is True and ack.get('startupReady') is True, 'production installer/relaunch acknowledgement differs')
    if platform == 'linux':
        need(installed.get('hash') == package['sha256'] and installed.get('previousHash') == baseline['sha256'], 'Linux actual replacement hashes differ')
    ready = receipt(read, ack.get('evidence', {}).get('ready'), NATIVE + '-ready.log', limit=32)
    startup = receipt(read, ack.get('evidence', {}).get('startup'), NATIVE + '-startup-ready.log')
    need(ready == VERSION.encode() and ack.get('readySha256') == sha(ready)
         and ack.get('startupLogSha256') == sha(startup) and ('MOUSE_READY ' + VERSION) in startup.decode('utf-8'),
         'automatic637 READY file/startup bytes differ')
    new_process = native_driver(native.get('newProcess'), platform=platform, profile=old['profile'], executable=driver_target,
                                sentinel=sentinel['sha256'], action='witness-quit')
    need(len({before['pid'], old['pid'], new_process['pid'], after['pid']}) == 4,
         'writer, updating predecessor, automatic relaunch and independent read must be four distinct actual processes')
    lifecycle = native.get('newLifecycle', {})
    quit_log = receipt(read, lifecycle.get('evidence'), NATIVE + '-startup-quit.log')
    need(all(lifecycle.get(key) is True for key in ('ready', 'exitSaved', 'quit'))
         and lifecycle.get('startupLogSha256') == sha(quit_log) and quit_log.startswith(startup), 'automatic relaunch lifecycle bytes differ')
    lifecycle_text = quit_log.decode('utf-8').rsplit('MOUSE_READY ' + VERSION, 1)
    need(len(lifecycle_text) == 2 and 'MOUSE_EXIT_SAVED' in lifecycle_text[1] and 'MOUSE_APP_QUIT' in lifecycle_text[1]
         and lifecycle_text[1].index('MOUSE_EXIT_SAVED') < lifecycle_text[1].index('MOUSE_APP_QUIT'), 'updated app did not save then quit after READY')
    for name, data in ((NATIVE + '-ready.log', ready), (NATIVE + '-startup-ready.log', startup), (NATIVE + '-startup-quit.log', quit_log)):
        inputs[name] = sha(data)
    installation = facts.get('oldInstallation', {})
    if platform == 'darwin':
        need(installation.get('version') == PREVIOUS and installation.get('codesignVerified') is True
             and same_path(installation.get('target'), str(PurePosixPath(driver_target).parents[2]), platform)
             and facts.get('ownedDefaultProfileRemovedAfterVerification') is True, 'published macOS bundle or owned default-profile cleanup differs')
    elif platform == 'win32':
        need(installation.get('exitCode') == 0 and installation.get('peMachine') == '0x8664'
             and installation.get('unicodeAndSpaces') is True, 'published Windows installer did not install')
    else:
        need(installation.get('method') == 'user-owned AppImage atomic replacement' and installation.get('uid') == before['processIdentity']['uid']
             and same_path(installation.get('target'), driver_target, 'linux') and installation.get('size') == baseline['size']
             and installation.get('sha256') == baseline['sha256'] and installation.get('executable') is True,
             'published Linux AppImage installation differs')
    return {'ok': True, 'fromVersion': PREVIOUS, 'toVersion': VERSION, 'platform': platform, 'arch': arch,
            'baseline': baseline, 'package': package, 'inputs': inputs, 'oldPid': old['pid'], 'relaunchedPid': new_process['pid'],
            'writerPid': before['pid'], 'readerPid': after['pid'], 'physicalUserDeviceVerified': False,
            'publicChannelDownloadVerified': False}
