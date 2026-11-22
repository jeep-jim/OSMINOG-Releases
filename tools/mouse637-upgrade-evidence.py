#!/usr/bin/env python3
def old_version(platform):
    return '6.0.36'
"""Independently bind published636-to637 package and native profile replacement."""
import hashlib
import json
from pathlib import PurePosixPath
import posixpath
import re
BASELINES = {'darwin': {'name': 'Mouse-Browser-6.0.36-mac-arm64.dmg', 'tag': 'quadro-macos-v6.0.36-arm64', 'size': 137981934, 'sha256': '8688b4db4bd8d9541d93508ecdb3260727d9c6a975f336cfcd2b086caae704fb'}, 'win32': {'name': 'Mouse-Browser-6.0.36-Windows-x64.exe', 'tag': 'mouse-windows-v6.0.36-x64', 'size': 125834363, 'sha256': '443496508013d5734e8a81c7eb0ddb33cedad4149440da3c04ff891486c6cf61'}, 'linux': {'appimage': {'name': 'Mouse-Browser-6.0.36-Linux-x64.AppImage', 'tag': 'mouse-linux-v6.0.36-x64', 'size': 135673552, 'sha256': 'e126ee0e50c1bc8e4e1108600e5b2e9e74af609feac0fff8d8de7b3c0b79f090'}, 'deb': {'name': 'Mouse-Browser-6.0.36-Linux-x64.deb', 'tag': 'mouse-linux-v6.0.36-x64', 'size': 105853084, 'sha256': '6de6baf09263ade5ea20fec2984cb183d6909cb7a7646b8c8d917cf33c0d7d7f'}}}
NAME = 'mouse-637-upgrade.json'
MARKER = 'MOUSE_637_REAL_636_TO_637_PROFILE_PASS'
SOURCE = 'real installed executable and owned loopback CDP fixture'
METHOD = 'verified package replacement and actual old/new profile processes; retained629 gate tests updater'
LINUX_METHOD = 'verified deb and AppImage replacement with actual old/new profile processes'

def need(value, message):
    if not value:
        raise ValueError('Mouse637 actual636 upgrade: ' + message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def read_json(read, name):
    raw = read(name)
    need(isinstance(raw, bytes) and 0 < len(raw) <= 2 * 1024 ** 2, 'missing or oversized ' + name)
    value = json.loads(raw)
    need(isinstance(value, dict), 'non-object ' + name)
    return (raw, value)

def positive(value):
    return type(value) is int and value > 0

def linux_process_binding(native, report, expected_image):
    chain = native.get('launchAncestry')
    need(native.get('launcherPid') == report['launcherPid'] and isinstance(chain, list) and (1 <= len(chain) <= 16) and all((isinstance(row, dict) and positive(row.get('pid')) and positive(row.get('parentPid')) and (row.get('uid') == native['uid']) for row in chain)) and (len({row['pid'] for row in chain}) == len(chain)) and (chain[0]['pid'] == report['pid']) and (chain[-1]['pid'] == report['launcherPid']) and all((chain[i]['parentPid'] == chain[i + 1]['pid'] for i in range(len(chain) - 1))), 'actual browser is not bound to its owned launcher')
    need('environmentAppImage' in native, 'initial environment diagnostic is absent')
    if native['packageFormat'] == 'deb':
        need(native['environmentAppImage'] is None, 'deb has an AppImage environment')
        return
    target = native.get('appImage')
    need(native.get('appImageSource') == 'verified launch path and owned browser ancestry' and native['environmentAppImage'] in (None, target), 'AppImage environment conflicts with the verified launch')
    image = native.get('launchedImage', {})
    need(image.get('path') == target and image.get('uid') == native['uid'] and (image.get('regularFile') is True) and (image.get('executable') is True) and positive(image.get('size')) and (image.get('size') == expected_image['size']) and (image.get('sha256') == expected_image['sha256']) and (type(image.get('device')) is int) and (image['device'] >= 0) and positive(image.get('inode')), 'launched AppImage does not match the immutable package bytes')
    mount = native.get('mount', {})
    raw = mount.get('raw')
    need(isinstance(raw, str) and 0 < len(raw) <= 16384 and (not any((value in raw for value in ('\x00', '\n', '\r')))), 'raw native mountinfo is absent')
    fields = raw.split(' ')
    separator = fields.index('-') if '-' in fields else -1
    need(separator >= 6 and len(fields) == separator + 4 and all(fields) and re.fullmatch('[1-9]\\d*', fields[0]) and re.fullmatch('[1-9]\\d*', fields[1]) and re.fullmatch('\\d+:\\d+', fields[2]), 'raw native mountinfo is malformed')
    decode = lambda value: re.sub('\\\\(040|011|012|134)', lambda match: chr(int(match[1], 8)), value)
    decoded = {'raw': raw, 'mountId': int(fields[0]), 'parentMountId': int(fields[1]), 'device': fields[2], 'root': decode(fields[3]), 'mountPoint': decode(fields[4]), 'options': fields[5].split(','), 'filesystem': fields[separator + 1], 'source': decode(fields[separator + 2]), 'superOptions': fields[separator + 3].split(',')}
    need(mount == decoded and mount['root'] == '/' and PurePosixPath(mount['mountPoint']).is_absolute() and (mount['mountPoint'] not in ('/', '')) and (not mount['mountPoint'].startswith('//')) and (posixpath.normpath(mount['mountPoint']) == mount['mountPoint']) and re.fullmatch('fuse(?:\\.(?:[^\\s/\\\\\\0]|\\\\040)+)?', mount['filesystem']) and ('ro' in mount['options']) and ('rw' not in mount['options']) and (native['executable'] == mount['mountPoint'] + '/mouse-browser'), 'AppImage browser is not on its exact read-only FUSE mount')

def profile_pair(read, facts, platform, arch, package, baseline, prefix, format_=None):
    reports, inputs = ([], {})
    for mode, version, key in [('write', old_version(platform), 'oldWrite'), ('read', '6.0.37', 'newRead')]:
        name = prefix + '-' + mode + '.json'
        data, report = read_json(read, name)
        bound = facts.get(key, {})
        need(bound.get('report') == name and bound.get('reportSha256') == sha(data) and (bound.get('result') == report), 'raw native profile report differs')
        inputs[name] = sha(data)
        need(report.get('ok') is True and (not report.get('error')) and ((report.get('version'), report.get('platform'), report.get('arch'), report.get('mode'), report.get('reportPrefix')) == (version, platform, arch, mode, prefix)) and positive(report.get('pid')) and positive(report.get('launcherPid')), 'native old/new runtime identity differs')
        need(report.get('source') == SOURCE and report.get('physicalUserInputVerified') is False and (report.get('nativeExit') == {'code': 0, 'signal': None}), 'actual process lifecycle or input scope differs')
        identity = report.get('identity', {})
        need(identity.get('version') == version and identity.get('platform') == platform and (identity.get('arch') == arch) and (identity.get('test') is True), 'installed runtime identity absent')
        logname = prefix + '-' + mode + '.log'
        log = read(logname)
        need(bound.get('log') == logname and isinstance(log, bytes) and (0 < len(log) <= 8 * 1024 ** 2) and (sha(log) == bound.get('logSha256')) and ('MOUSE_637_UPGRADE_PROFILE_' + mode.upper() + '_PASS' in log.decode('utf-8').splitlines()), 'native probe log differs')
        app = read(prefix + '-' + mode + '-app.log')
        need(isinstance(app, bytes) and 0 < len(app) <= 16 * 1024 ** 2 and all((marker in app.decode('utf-8') for marker in ('MOUSE_EXIT_SAVED', 'MOUSE_APP_QUIT'))), 'old/new app did not save and quit')
        profile = report.get('profile', {})
        need(all((profile.get(flag) is True for flag in ('cookiePreserved', 'localStoragePreserved', 'bookmarkPreserved', 'tabPreserved', 'preferencesPreserved'))) and profile.get('preferences') == {'theme': 'dark', 'aiWidth': 413, 'libraryWidth': 417}, 'profile values were not preserved')
        need(isinstance(profile.get('pageId'), str) and bool(profile['pageId']) and isinstance(profile.get('url'), str) and re.fullmatch('http://127\\.0\\.0\\.1:\\d+/persisted', profile['url']) and isinstance(profile.get('tokenSha256'), str) and re.fullmatch('[0-9a-f]{64}', profile['tokenSha256']), 'owned profile identity missing')
        ready = report.get('pageReadiness', {})
        last = ready.get('last', {})
        origin = profile['url'].removesuffix('/persisted')
        need(ready.get('ready') is True and positive(ready.get('attempts')) and (ready['attempts'] <= 200) and (ready.get('expectedURL') == ready.get('target', {}).get('url') == last.get('href') == profile['url']) and (ready.get('expectedOrigin') == last.get('origin') == origin) and (last.get('readyState') == 'complete') and (last.get('title') == 'Mouse637 preserved profile fixture') and (last.get('input') is True) and (last.get('storageAccessible') is True) and (last.get('storageError') is None) and (ready.get('evaluationError') is None), 'committed native profile document was not ready')
        if platform == 'linux':
            native = report.get('processIdentity', {})
            need(native.get('source') == 'CDP SystemInfo.getProcessInfo and owned /proc' and native.get('type') == 'browser' and (native.get('pid') == report['pid']) and positive(native.get('uid')) and (native.get('exited') is True) and (native.get('packageFormat') == format_) and isinstance(native.get('executable'), str) and (PurePosixPath(native['executable']).name == 'mouse-browser'), 'actual Linux browser process identity missing')
            if format_ == 'deb':
                need(native.get('appImage') is None and native['executable'].startswith('/opt/'), 'deb was replaced with a portable launch')
            else:
                need(isinstance(native.get('appImage'), str) and PurePosixPath(native['appImage']).is_absolute(), 'real mounted AppImage missing')
            linux_process_binding(native, report, baseline if mode == 'write' else package)
        reports.append(report)
    need(reports[0]['pid'] != reports[1]['pid'] and reports[0]['profile'] == reports[1]['profile'], 'same process or different profile cannot prove upgrade')
    return reports, inputs

def transition(read, facts, platform, arch, package, baseline, prefix, format_=None):
    expected_baseline = {**baseline, 'url': 'https://github.com/jeep-jim/OSMINOG-Releases/releases/download/' + baseline['tag'] + '/' + baseline['name']}
    method = LINUX_METHOD if platform == 'linux' else METHOD
    need(facts.get('ok') is True and (not facts.get('error')) and (facts.get('fromVersion') == old_version(platform)) and (facts.get('toVersion') == '6.0.37') and (facts.get('platform') == platform) and (facts.get('baseline') == expected_baseline) and (facts.get('package') == package) and (facts.get('reportPrefix') == prefix), 'wrong versions or immutable package bytes')
    need(facts.get('method') == method and facts.get('physicalUserDeviceVerified') is False, 'package replacement method or physical scope misrepresented')
    need(facts.get('closedProfileUnchanged') is True and facts.get('differentProcesses') is True and isinstance(facts.get('closedProfileSha256'), str) and re.fullmatch('[0-9a-f]{64}', facts['closedProfileSha256']), 'closed profile preservation is not bound')
    reports, inputs = profile_pair(read, facts, platform, arch, package, baseline, prefix, format_)
    if platform == 'win32':
        for key in ('oldInstallation', 'replacement'):
            value = facts.get(key, {})
            need(value.get('exitCode') == 0 and value.get('peMachine') == '0x8664' and (value.get('unicodeAndSpaces') is True), 'Windows installation failed')
    if platform == 'linux':
        need(facts.get('format') == format_, 'Linux format scope differs')
        for key, version, expected, native, phase in [('oldInstallation', old_version(platform), baseline, reports[0], 'old'), ('replacement', '6.0.37', package, reports[1], 'new')]:
            value = facts.get(key, {})
            if format_ == 'deb':
                name = prefix + '-' + phase + '-install.log'
                raw = read(name)
                need(value.get('exitCode') == 0 and positive(value.get('pid')) and (value.get('packageName') == 'mouse-browser') and (value.get('version') == version) and (value.get('executable') == native['processIdentity']['executable']) and (value.get('log') == name) and isinstance(raw, bytes) and (0 < len(raw) <= 16 * 1024 ** 2) and (sha(raw) == value.get('logSha256')), 'actual old/new deb installation failed or its log differs')
            else:
                need(value.get('method') == 'user-owned AppImage atomic replacement' and value.get('uid') == native['processIdentity']['uid'] and (value.get('target') == native['processIdentity']['appImage']) and (value.get('executable') is True) and (value.get('size') == expected['size']) and (value.get('sha256') == expected['sha256']), 'actual AppImage replacement differs')
        if format_ == 'appimage':
            need(facts['oldInstallation']['target'] == facts['replacement']['target'], 'AppImage replacement changed the owned installed path')
    return {'ok': True, 'fromVersion': old_version(platform), 'toVersion': '6.0.37', 'platform': platform, 'arch': arch, 'method': method, 'inputs': inputs, 'baseline': expected_baseline, 'package': package, 'oldPid': reports[0]['pid'], 'newPid': reports[1]['pid'], 'closedProfileSha256': facts['closedProfileSha256']}

def verify(read, *, expected_platform, expected_arch, expected_package=None, expected_packages=None):
    need((expected_platform, expected_arch) in (('darwin', 'arm64'), ('win32', 'x64'), ('linux', 'x64')), 'unsupported target')
    raw, facts = read_json(read, 'mouse-637-upgrade.json')
    if expected_platform != 'linux':
        result = transition(read, facts, expected_platform, expected_arch, expected_package, BASELINES[expected_platform], 'mouse-637-upgrade')
        result['inputs']['mouse-637-upgrade.json'] = sha(raw)
        return result
    need(facts.get('ok') is True and (not facts.get('error')) and (facts.get('fromVersion') == old_version(expected_platform)) and (facts.get('toVersion') == '6.0.37') and (facts.get('platform') == 'linux') and (facts.get('physicalUserDeviceVerified') is False) and (facts.get('firstLinuxRelease') is False) and (facts.get('previousVersion') == old_version(expected_platform)) and (facts.get('method') == LINUX_METHOD) and (facts.get('packages') == expected_packages) and (set(facts.get('formats', {})) == {'deb', 'appimage'}), 'Linux636 baseline or both actual package formats missing')
    results = {}
    for format_, extension in [('deb', 'deb'), ('appimage', 'AppImage')]:
        name = 'Mouse-Browser-6.0.37-Linux-x64.' + extension
        need(isinstance(expected_packages, dict) and name in expected_packages, 'Linux candidate package missing')
        results[format_] = transition(read, facts['formats'][format_], 'linux', 'x64', {'name': name, **expected_packages[name]}, BASELINES['linux'][format_], 'mouse-637-upgrade-' + format_, format_)
    return {'ok': True, 'fromVersion': old_version(expected_platform), 'toVersion': '6.0.37', 'platform': 'linux', 'arch': 'x64', 'firstLinuxRelease': False, 'inputs': {'mouse-637-upgrade.json': sha(raw)}, 'formats': results}
