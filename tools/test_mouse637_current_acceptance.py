#!/usr/bin/env python3
"""Synthetic acceptance contracts only: no installed application is executed."""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import struct
import unittest
from unittest.mock import patch
import zlib
E = runpy.run_path(str(Path(__file__).with_name('mouse637-upgrade-evidence.py')))
B = runpy.run_path(str(Path(__file__).with_name('mouse637-update-button-evidence.py')))
P = runpy.run_path(str(Path(__file__).with_name('mouse637-performance-evidence.py')))
C = runpy.run_path(str(Path(__file__).with_name('mouse637-current.py')))

def fixture(platform):
 files={};native=[];transitions=[];arch='arm64' if platform=='darwin' else 'x64'
 formats=('deb','appimage') if platform=='linux' else (None,)
 packages={};url='http://127.0.0.1:31337/persisted'
 for number,fmt in enumerate(formats):
  extension=('deb' if fmt=='deb' else 'AppImage') if fmt else 'dmg' if platform=='darwin' else 'exe'
  name='Mouse-Browser-6.0.37-'+('Linux-x64.'+extension if fmt else 'mac-arm64.dmg' if platform=='darwin' else 'Windows-x64.exe')
  package={'name':name,'size':100*1024**2,'sha256':str(number+4)*64};packages[name]={k:v for k,v in package.items() if k!='name'}
  baseline=copy.deepcopy(E['BASELINES'][platform][fmt] if fmt else E['BASELINES'][platform]);baseline['url']='https://github.com/jeep-jim/OSMINOG-Releases/releases/download/'+baseline['tag']+'/'+baseline['name']
  prefix='mouse-637-upgrade'+('-'+fmt if fmt else '')
  facts={'ok':True,'fromVersion':'6.0.36','toVersion':'6.0.37','platform':platform,'method':E['LINUX_METHOD'] if fmt else E['METHOD'],'baseline':baseline,'package':package,'physicalUserDeviceVerified':False,'closedProfileUnchanged':True,'differentProcesses':True,'closedProfileSha256':'b'*64,'reportPrefix':prefix}
  if fmt: facts['format']=fmt
  for mode,version,relative in [('write','6.0.36',1),('read','6.0.37',2)]:
   pid=100+number*10+relative
   report={'ok':True,'mode':mode,'version':version,'platform':platform,'arch':arch,'pid':pid,'launcherPid':pid+1000 if fmt=='appimage' else pid,'reportPrefix':prefix,'source':E['SOURCE'],'physicalUserInputVerified':False,'nativeExit':{'code':0,'signal':None},'identity':{'version':version,'platform':platform,'arch':arch,'test':True},'profile':{'pageId':'page'+str(number),'url':url,'tokenSha256':'c'*64,'preferences':{'theme':'dark','aiWidth':413,'libraryWidth':417},'cookiePreserved':True,'localStoragePreserved':True,'bookmarkPreserved':True,'tabPreserved':True,'preferencesPreserved':True},'pageReadiness':{'ready':True,'attempts':2,'expectedURL':url,'expectedOrigin':'http://127.0.0.1:31337','target':{'id':'target','url':url},'last':{'href':url,'origin':'http://127.0.0.1:31337','readyState':'complete','title':'Mouse637 preserved profile fixture','input':True,'storageAccessible':True,'storageError':None},'evaluationError':None}}
   if fmt:
    report['processIdentity']={'source':'CDP SystemInfo.getProcessInfo and owned /proc','type':'browser','pid':pid,'launcherPid':report['launcherPid'],'uid':1001,'executable':'/opt/Mouse Browser/mouse-browser' if fmt=='deb' else '/tmp/.mount_Mouse ABC123/mouse-browser','appImage':None if fmt=='deb' else '/tmp/owned/Mouse Browser.AppImage','environmentAppImage':None,'packageFormat':fmt,'exited':True,
      'launchAncestry':[{'pid':pid,'parentPid':30 if fmt=='deb' else report['launcherPid'],'uid':1001}]+([{'pid':report['launcherPid'],'parentPid':30,'uid':1001}] if fmt=='appimage' else [])}
    if fmt=='appimage':
     expected=baseline if mode=='write' else package
     report['processIdentity'].update(appImageSource='verified launch path and owned browser ancestry',launchedImage={'path':'/tmp/owned/Mouse Browser.AppImage','uid':1001,'device':2049,'inode':12345+relative,'size':expected['size'],'sha256':expected['sha256'],'regularFile':True,'executable':True},
       mount={'raw':'91 37 0:84 / /tmp/.mount_Mouse\\040ABC123 ro,nosuid,nodev,relatime - fuse.Mouse\\040Browser.AppImage Mouse\\040Browser.AppImage ro,user_id=1001,group_id=1001','mountId':91,'parentMountId':37,'device':'0:84','root':'/','mountPoint':'/tmp/.mount_Mouse ABC123','options':['ro','nosuid','nodev','relatime'],'filesystem':'fuse.Mouse\\040Browser.AppImage','source':'Mouse Browser.AppImage','superOptions':['ro','user_id=1001','group_id=1001']})
   native.append(report);files[prefix+'-'+mode+'.log']=('MOUSE_637_UPGRADE_PROFILE_'+mode.upper()+'_PASS\nSynthetic unit fixture\n').encode();files[prefix+'-'+mode+'-app.log']=b'MOUSE_EXIT_SAVED\nMOUSE_APP_QUIT\n'
  if platform=='win32':
   for key in ('oldInstallation','replacement'): facts[key]={'exitCode':0,'peMachine':'0x8664','unicodeAndSpaces':True}
  if fmt:
   for key,phase,version,pkg in [('oldInstallation','old','6.0.36',baseline),('replacement','new','6.0.37',package)]:
    if fmt=='deb':
     log=prefix+'-'+phase+'-install.log';files[log]=b'Synthetic dpkg log\n';facts[key]={'exitCode':0,'pid':30,'packageName':'mouse-browser','version':version,'executable':'/opt/Mouse Browser/mouse-browser','log':log,'logSha256':E['sha'](files[log])}
    else: facts[key]={'method':'user-owned AppImage atomic replacement','target':'/tmp/owned/Mouse Browser.AppImage','uid':1001,'size':pkg['size'],'sha256':pkg['sha256'],'executable':True}
  transitions.append(facts)
 outer=transitions[0] if platform!='linux' else {'ok':True,'fromVersion':'6.0.36','toVersion':'6.0.37','platform':'linux','physicalUserDeviceVerified':False,'method':E['LINUX_METHOD'],'firstLinuxRelease':False,'previousVersion':'6.0.36','packages':packages,'formats':dict(zip(formats,transitions))}
 marker='MOUSE_637_REAL_636_TO_637_PROFILE_PASS';files['mouse-637-upgrade.log']=(marker+'\n').encode();files['mouse-633-owner-feedback.json']=b'{"syntheticOwner":true}'
 def refresh():
  for number,transition in enumerate(transitions):
   for i,(mode,key) in enumerate([('write','oldWrite'),('read','newRead')]):
    report=native[number*2+i];prefix=transition['reportPrefix'];name=prefix+'-'+mode+'.json';raw=json.dumps(report).encode();files[name]=raw;log=prefix+'-'+mode+'.log'
    transition[key]={'report':name,'reportSha256':E['sha'](raw),'log':log,'logSha256':E['sha'](files[log]),'result':copy.deepcopy(report)}
  files['mouse-637-upgrade.json']=json.dumps(outer).encode()
  if platform in ('win32','linux'):
   process={'exitCode':0,'pid':51,'elapsedMs':2000,'requiredMarkers':[marker],'reportSha256':E['sha'](files['mouse-637-upgrade.json'])}
   if platform=='linux': process.update(log='mouse-637-upgrade.log',logSha256=E['sha'](files['mouse-637-upgrade.log']))
   wrapper={'checks':{'freshUpgrade':process,'ownerFeedback':{'exitCode':0,'pid':52,'elapsedMs':1000,'requiredMarkers':['MOUSE_633_OWNER_FEEDBACK_PASS'],'reportSha256':E['sha'](files['mouse-633-owner-feedback.json'])}}}
   files['mouse-'+('windows' if platform=='win32' else 'linux')+'-verification.json']=json.dumps(wrapper).encode()
 refresh();return (packages if platform=='linux' else transitions[0]['package']),outer,native,files,refresh

def encoded(value):
    return json.dumps(value, sort_keys=True).encode()


def png_fixture():
    width, height = 160, 120
    def chunk(kind, raw):
        return struct.pack('>I', len(raw)) + kind + raw + struct.pack('>I', zlib.crc32(kind + raw) & 0xffffffff)
    data = b''.join(b'\0' + bytes((x * 17 + y * 31 + (x * y) % 251) % 256 for x in range(width * 3)) for y in range(height))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(data)) + chunk(b'IEND', b'')


def button_fixture(platform):
    expected, upgrade, profiles, files, _refresh = fixture(platform)
    selected = upgrade['formats']['appimage'] if platform == 'linux' else upgrade
    package = selected['package']; profiles = profiles[-2:] if platform == 'linux' else profiles
    baseline = {**selected['baseline'], 'source': B['SOURCE'], 'updaterBlobSHA': B['UPDATER_BLOB']}
    old_prefix = selected['reportPrefix']; prefix = 'mouse-637-update-button-profile' + ('-appimage' if platform == 'linux' else '')
    for key, data in list(files.items()):
        if key.startswith(old_prefix + '-'):
            files[prefix + key[len(old_prefix):]] = data
    profile = r'C:\Owned\profile' if platform == 'win32' else '/Users/runner/Library/Application Support/Trader OS' if platform == 'darwin' else '/tmp/owned/profile'
    executable = r'C:\Owned\Mouse Browser.exe' if platform == 'win32' else '/tmp/Applications/Mouse Browser.app/Contents/MacOS/Mouse Browser' if platform == 'darwin' else '/tmp/owned/Mouse Browser.AppImage'
    browser = profiles[0]['processIdentity']['executable'] if platform == 'linux' else executable
    stage = r'C:\Temp\mouse-update-install-unit' if platform == 'win32' else '/tmp/owned/.mouse-update-unit'
    candidate_path = ('C:\\Packages\\' if platform == 'win32' else '/tmp/packages/') + package['name']
    url = 'https://github.com/jeep-jim/OSMINOG-Releases/releases/download/' + B['TAGS'][platform] + '/' + package['name']
    sentinel = {'name': 'mouse637-update-owner.txt', 'sha256': 'c' * 64, 'preserved': True}
    facts = {'schema': 1, 'version': '6.0.37', 'fromVersion': '6.0.36', 'toVersion': '6.0.37', 'platform': platform,
             'arch': 'arm64' if platform == 'darwin' else 'x64', 'ok': True,
             'method': 'actual published636 native update buttons and actual637 profile restart', 'physicalUserDeviceVerified': False,
             'publicChannelDownloadVerified': False, 'baseline': baseline, 'package': package,
             'ownerSentinel': sentinel, 'differentProcesses': True}
    if platform == 'linux':
        facts.update(oldInstallation=selected['oldInstallation'], packageFormat='appimage',
                     debInstallation='manual package-manager path independently verified by mouse-637-upgrade.json')
    elif platform == 'win32':
        facts['oldInstallation'] = selected['oldInstallation']
    else:
        facts.update(oldInstallation={'version': '6.0.36', 'target': '/tmp/Applications/Mouse Browser.app', 'codesignVerified': True},
                     ownedDefaultProfileRemovedAfterVerification=True)
    def driver(pid, action):
        process = {'pid': pid, 'executable': browser, 'sameUser': True, 'identity': {'pid': pid}}
        if platform == 'win32':
            process.update(userSID='S-1-5-21-42'); process['identity'].update(userSID=process['userSID'], creationTime100ns=str(123456789 + pid))
        else:
            process['uid'] = 1001; process['identity']['uid'] = 1001
            if platform == 'darwin':
                process['identity']['started'] = 'Sun Nov 22 12:00:00 2026'
            else:
                process['identity']['startTicks'] = 1234 + pid
                process.update(expectedExecutable=executable, environmentAppImage=executable, environmentProfile=None,
                               mount=copy.deepcopy(profiles[0]['processIdentity']['mount']),
                               launchAncestry=[{'pid': pid, 'parentPid': 1, 'uid': 1001, 'state': 'S'}],
                               imageBinding={'kind': 'observed initial APPIMAGE environment and read-only FUSE executable', 'pid': pid, 'path': executable})
        result = {'schema': 1, 'ok': True, 'action': action, 'platform': platform, 'profile': profile,
                  'expectedExecutable': executable, 'sentinelSha256': sentinel['sha256'], 'terminationUsed': False,
                  'elapsedMs': 123, 'process': process, 'window': {'handle': pid + 100, 'pid': pid, 'visible': True,
                  'bounds': {'x': 0, 'y': 0, 'width': 640, 'height': 480}, 'source': B['WINDOWS'][platform]},
                  'nativeInput': {'backend': B['BACKENDS'][platform], 'action': action, 'foregroundVerified': True,
                  'coordinateSpace': 'quartz-screen-points' if platform == 'darwin' else 'physical-screen-pixels'}}
        if action == 'click':
            result['nativeInput'].update(x=50, y=50)
        else:
            result['nativeInput']['accelerator'] = 'Cmd+Q' if platform == 'darwin' else 'Ctrl+Q'
            result['exit'] = {'observed': True, 'graceful': True, 'terminationUsed': False,
                              'method': 'production native quit accelerator', 'exitCode': 0 if platform == 'win32' else None}
        return result
    clicks = []
    for selector in ('#version-button', '#update-download', '#update-install'):
        event = {'selector': selector, 'trusted': True, 'type': 'click', 'button': 0, 'x': 50, 'y': 50, 'at': 1}
        clicks.append({'selector': selector, 'point': {'x': 50, 'y': 50}, 'source': B['BACKENDS'][platform], 'at': 2,
                       'driver': driver(301, 'click'), 'event': event})
    native = {'schema': 1, 'ok': True, 'fromVersion': '6.0.36', 'toVersion': '6.0.37', 'platform': platform,
              'arch': facts['arch'], 'budgetMs': 300000, 'elapsedMs': 12000, 'stage': 'complete',
              'method': 'unchanged installed predecessor with CI-only fetch transport; native UI and stock installer',
              'physicalUserDeviceVerified': False, 'publicChannelDownloadVerified': False,
              'baseline': baseline, 'package': {**package, 'version': '6.0.37', 'path': candidate_path, 'url': url},
              'inspectorClosedBeforeInstall': True, 'previousWriterPid': profiles[0]['pid'], 'launcherPid': 301,
              'oldProcess': {'pid': 301, 'version': '6.0.36', 'platform': platform, 'arch': facts['arch'], 'packaged': True,
              'executable': browser, 'profile': profile, 'appPath': (r'C:\Owned\resources\app.asar' if platform == 'win32' else '/owned/app.asar'),
              'updaterBlobSHA': B['UPDATER_BLOB'], 'installerSha256': 'd' * 64, 'transportOnly': True,
              'selectionUnchanged': True, 'verificationUnchanged': True, 'installerUnchanged': True},
              'nativeInputs': clicks, 'oldExit': {'code': 0, 'signal': None},
              'available': {'phase': 'available', 'currentVersion': '6.0.36', 'availableVersion': '6.0.37', 'channel': 'static'},
              'downloaded': {'phase': 'ready', 'currentVersion': '6.0.36', 'availableVersion': '6.0.37', 'channel': 'static', 'percent': 100, 'canInstall': True},
              'download': {'candidate': {'version': '6.0.37', 'name': package['name'], 'url': url, 'size': package['size'], 'hash': package['sha256']},
              'file': candidate_path, 'requests': [{'url': B['CHANNELS'][platform], 'fixtureURL': 'http://127.0.0.1:32323/channel', 'at': 1},
                                                  {'url': url, 'fixtureURL': 'http://127.0.0.1:32323/package', 'at': 2}]},
              'fixtureRequests': [{'path': '/channel', 'method': 'GET', 'at': 1, 'bytes': 300, 'complete': True},
                                  {'path': '/package', 'method': 'GET', 'at': 2, 'bytes': package['size'], 'complete': True}],
              'installerReceipt': {'version': '6.0.37', 'target': '/tmp/Applications/Mouse Browser.app' if platform == 'darwin' else executable, 'stage': stage},
              'newProcess': driver(302, 'witness-quit')}
    if platform == 'linux':
        native['oldProcess']['linuxInstallerSha256'] = 'e' * 64
        native['installerReceipt'].update(hash=package['sha256'], previousHash=baseline['sha256'])
    def save(name, raw):
        files[name] = raw
        return {'filename': name, 'bytes': len(raw), 'sha256': E['sha'](raw)}
    old_log = ('\n'.join('MOUSE_637_BUTTON_CLICK ' + json.dumps(click['event']) for click in clicks) + '\nMOUSE_EXIT_SAVED\nMOUSE_APP_QUIT\n').encode()
    native['oldLifecycle'] = {'exitSaved': True, 'quit': True, 'appLog': save(B['NATIVE'] + '-app.log', old_log)}
    ready = save(B['NATIVE'] + '-ready.log', b'6.0.37')
    startup = save(B['NATIVE'] + '-startup-ready.log', b'Synthetic unit lifecycle\nMOUSE_READY 6.0.37\n')
    native['acknowledgement'] = {'version': '6.0.37', 'readyPath': stage + ('\\READY' if platform == 'win32' else '/READY'),
                                 'readySha256': ready['sha256'], 'receiptRemoved': True, 'startupReady': True,
                                 'startupLogSha256': startup['sha256'], 'evidence': {'ready': ready, 'startup': startup}}
    quit_ = save(B['NATIVE'] + '-startup-quit.log', files[startup['filename']] + b'MOUSE_EXIT_SAVED\nMOUSE_APP_QUIT\n')
    native['newLifecycle'] = {'ready': True, 'exitSaved': True, 'quit': True, 'startupLogSha256': quit_['sha256'], 'evidence': quit_}
    native['captures'] = [{**save('mouse-637-update-button-' + label + '.png', png_fixture()), 'source': 'installed shell compositor', 'width': 160, 'height': 120} for label in ('available', 'ready')]
    files['mouse-637-update-button.log'] = (B['MARKER'] + '\n').encode()
    files[B['NATIVE'] + '.log'] = (B['NATIVE_MARKER'] + '\n').encode()
    def refresh():
        for report, mode, key in zip(profiles, ('write', 'read'), ('oldWrite', 'newRead')):
            report['reportPrefix'] = prefix
            raw = encoded(report); name = prefix + '-' + mode + '.json'; files[name] = raw
            logname = prefix + '-' + mode + '.log'
            facts[key] = {'report': name, 'reportSha256': E['sha'](raw), 'result': copy.deepcopy(report),
                          'log': logname, 'logSha256': E['sha'](files[logname])}
        native_raw = encoded(native); files[B['NATIVE'] + '.json'] = native_raw
        facts['native'] = {'pid': 500, 'exitCode': 0, 'elapsedMs': 15000, 'requiredMarkers': [B['NATIVE_MARKER']],
                           'log': B['NATIVE'] + '.log', 'logSha256': E['sha'](files[B['NATIVE'] + '.log']),
                           'report': B['NATIVE'] + '.json', 'reportSha256': E['sha'](native_raw), 'result': copy.deepcopy(native)}
        files[B['NAME']] = encoded(facts)
    refresh()
    return expected, facts, native, files, refresh


def verify_upgrade(platform, files, package):
    return E['verify'](files.__getitem__, expected_platform=platform, expected_arch='arm64' if platform == 'darwin' else 'x64',
                       **({'expected_packages': package} if platform == 'linux' else {'expected_package': package}))


def verify_button(platform, files, package):
    return B['verify'](files.__getitem__, expected_platform=platform, expected_arch='arm64' if platform == 'darwin' else 'x64',
                       **({'expected_packages': package} if platform == 'linux' else {'expected_package': package}))


class CurrentAcceptance(unittest.TestCase):
    def test_published636_upgrade_all_three_platforms_and_two_linux_formats(self):
        for platform in ('darwin', 'win32', 'linux'):
            package, facts, native, files, refresh = fixture(platform)
            with self.subTest(platform=platform):
                result = verify_upgrade(platform, files, package)
                self.assertTrue(result['ok']); self.assertEqual(result['fromVersion'], '6.0.36')
                if platform == 'linux': self.assertEqual(set(result['formats']), {'deb', 'appimage'})

    def test_actual_upgrade_rejects_package_profile_lifecycle_and_mount_changes(self):
        changes = [lambda f, r: f['baseline'].update(sha256='0' * 64), lambda f, r: r.update(pid=111),
                   lambda f, r: r['profile'].update(cookiePreserved=False), lambda f, r: r.update(nativeExit={'code': 1, 'signal': None}),
                   lambda f, r: r['pageReadiness']['last'].update(href='about:blank'),
                   lambda f, r: r['processIdentity']['mount'].update(filesystem='ext4'),
                   lambda f, r: r['processIdentity']['launchAncestry'][0].update(parentPid=9999)]
        for index, change in enumerate(changes):
            package, facts, native, files, refresh = fixture('linux')
            change(facts['formats']['appimage'], native[-1]); refresh()
            with self.subTest(change=index), self.assertRaises(ValueError): verify_upgrade('linux', files, package)

    def test_actual_button_all_three_platforms_requires_four_processes(self):
        for platform in ('darwin', 'win32', 'linux'):
            package, facts, native, files, refresh = button_fixture(platform)
            with self.subTest(platform=platform):
                result = verify_button(platform, files, package)
                self.assertTrue(result['ok'])
                self.assertEqual(len({result[k] for k in ('oldPid', 'relaunchedPid', 'writerPid', 'readerPid')}), 4)
                self.assertFalse(result['publicChannelDownloadVerified'])

    def test_button_rejects_relabelled_or_modified_updater_and_unsafe_native_input(self):
        changes = [lambda f, n: n['oldProcess'].update(version='6.0.37'),
                   lambda f, n: n['oldProcess'].update(updaterBlobSHA='0' * 40),
                   lambda f, n: n['oldProcess'].update(installerUnchanged=False),
                   lambda f, n: n.update(inspectorClosedBeforeInstall=False),
                   lambda f, n: n['nativeInputs'][0]['event'].update(trusted=False),
                   lambda f, n: n['nativeInputs'][0]['driver'].update(terminationUsed=True),
                   lambda f, n: n['nativeInputs'][0]['driver']['process'].update(sameUser=False),
                   lambda f, n: n['nativeInputs'][0]['driver']['window'].update(pid=9999),
                   lambda f, n: n['nativeInputs'][0]['driver']['nativeInput'].update(x=9999),
                   lambda f, n: n.update(elapsedMs=300001),
                   lambda f, n: f.update(publicChannelDownloadVerified=True),
                   lambda f, n: f['baseline'].update(sha256='0' * 64)]
        for index, change in enumerate(changes):
            package, facts, native, files, refresh = button_fixture('win32'); change(facts, native); refresh()
            with self.subTest(change=index), self.assertRaises(ValueError): verify_button('win32', files, package)

    def test_button_rejects_fake_relaunch_missing_graceful_exit_or_different_profile(self):
        changes = [lambda f, n: n['newProcess']['process'].update(pid=n['oldProcess']['pid']),
                   lambda f, n: n['newProcess'].update(profile=r'C:\Other'),
                   lambda f, n: n['newProcess']['exit'].update(graceful=False),
                   lambda f, n: n['newProcess']['exit'].update(terminationUsed=True),
                   lambda f, n: n['newProcess']['window'].update(visible=False),
                   lambda f, n: n['acknowledgement'].update(receiptRemoved=False),
                   lambda f, n: n['acknowledgement'].update(readySha256='0' * 64),
                   lambda f, n: n['newLifecycle'].update(quit=False),
                   lambda f, n: f['ownerSentinel'].update(preserved=False)]
        for index, change in enumerate(changes):
            package, facts, native, files, refresh = button_fixture('win32'); change(facts, native); refresh()
            with self.subTest(change=index), self.assertRaises(ValueError): verify_button('win32', files, package)

    def test_button_checks_archived_startup_and_png_bytes_independently(self):
        for name in (B['NATIVE'] + '-ready.log', B['NATIVE'] + '-startup-ready.log', B['NATIVE'] + '-startup-quit.log',
                     B['NATIVE'] + '-app.log', 'mouse-637-update-button-available.png', B['NATIVE'] + '.json'):
            package, facts, native, files, refresh = button_fixture('darwin'); files[name] += b'changed'
            with self.subTest(name=name), self.assertRaises(ValueError): verify_button('darwin', files, package)

    def test_daemon_keepalive_binding_requires_exact_image_pipe_and_birth_identity(self):
        package, facts, native, files, refresh = button_fixture('linux')
        for witness in [click['driver'] for click in native['nativeInputs']] + [native['newProcess']]:
            process = witness['process']; process['environmentAppImage'] = None
            process['imageBinding'] = {'kind': 'exact AppImage runtime and inherited FUSE keepalive pipe', 'pid': 401,
                                      'path': witness['expectedExecutable'], 'startTicks': 9999, 'mountId': process['mount']['mountId'],
                                      'backingImage': {'kind': 'ancestor executable', 'pid': 401, 'path': witness['expectedExecutable'], 'inode': 12345},
                                      'pipes': [{'device': 15, 'inode': 3456, 'browserReadFD': 3, 'runtimeWriteFD': 4}]}
        refresh(); self.assertTrue(verify_button('linux', files, package)['ok'])
        for key, value in [('pipes', []), ('startTicks', 0), ('mountId', 999), ('path', '/tmp/other.AppImage')]:
            saved = copy.deepcopy(native['newProcess']['process']['imageBinding'])
            native['newProcess']['process']['imageBinding'][key] = value; refresh()
            with self.subTest(key=key), self.assertRaises(ValueError): verify_button('linux', files, package)
            native['newProcess']['process']['imageBinding'] = saved

    def test_current_fetches_exact_new_native_helpers_and_rejects_changed_git_blob(self):
        with __import__('tempfile').TemporaryDirectory() as temporary:
            seen = []
            def api(_repo, path):
                seen.append(path); raw = b'unit synthetic helper\n'
                return {'content': __import__('base64').b64encode(raw).decode(), 'sha': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}
            raw = b'unit synthetic helper\n'
            unit_blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            self.assertEqual(C['PUBLISHED_UPDATER_BLOB'], '91ab363f926774825caf8055b2d3d81bf0d51264')
            with patch.dict(C['fetch_helpers'].__globals__, PUBLISHED_UPDATER_BLOB=unit_blob):
                C['fetch_helpers'](api, 'owner/repository', 'a' * 40, Path(temporary))
            self.assertEqual(len(seen), 8)
            self.assertIn('contents/desktop/mouse-smoke-hit-target.cjs?ref=' + 'a' * 40, seen)
            self.assertTrue((Path(temporary) / 'mouse-637-update-window.py').is_file())
            self.assertTrue((Path(temporary) / 'legacy636-update.cjs').is_file())
            self.assertEqual(seen[-1], 'contents/desktop/mouse-update.cjs?ref=7c09b6cb9885ce72be41e8f16a35d4c55c9ecde3')
            with self.assertRaisesRegex(ValueError, 'published636 updater'):
                C['fetch_helpers'](api, 'owner/repository', 'a' * 40, Path(temporary))
            with self.assertRaises(ValueError):
                C['fetch_helpers'](lambda *_: {'content': 'eA==', 'sha': '0' * 40}, 'owner/repo', 'a' * 40, Path(temporary))

    def test_current_requires_actual_button_then_feature_gate_on_each_platform(self):
        original = runpy.run_path
        for platform in ('darwin', 'win32', 'linux'):
            package, facts, native, files, refresh = button_fixture(platform)
            if platform != 'darwin':
                name = 'mouse-' + ('windows' if platform == 'win32' else 'linux') + '-verification.json'
                wrapper = json.loads(files[name])
                wrapper['checks']['updateFrom636'] = {'exitCode': 0, 'pid': 501, 'elapsedMs': 20000,
                    'requiredMarkers': [B['MARKER']], 'reportSha256': E['sha'](files[B['NAME']]),
                    'log': 'mouse-637-update-button.log', 'logSha256': E['sha'](files['mouse-637-update-button.log'])}
                files[name] = encoded(wrapper)
            observed = []
            def feature_gate(read, **arguments):
                observed.append(arguments)
                return {'ok': True, 'syntheticFeatureWiringOnly': True}
            def dispatch(path, *args, **kwargs):
                if Path(path).name == 'mouse637-features-evidence.py':
                    return {'verify': feature_gate}
                return original(path, *args, **kwargs)
            arguments = {'platform': platform, 'arch': 'arm64' if platform == 'darwin' else 'x64',
                         **({'packages': package} if platform == 'linux' else {'package': package})}
            with self.subTest(platform=platform), patch.object(runpy, 'run_path', side_effect=dispatch):
                result = C['verify_upgrade'](files.__getitem__, **arguments)
                self.assertTrue(result['updateFrom636']['ok'])
                self.assertEqual(observed, [{'expected_platform': platform, 'expected_arch': arguments['arch']}])
                self.assertTrue(result['features']['ok'])
                files[B['NAME']] += b'changed'
                observed.clear()
                with self.assertRaises((ValueError, KeyError)):
                    C['verify_upgrade'](files.__getitem__, **arguments)
                self.assertEqual(observed, [])


class PerformanceAcceptance(unittest.TestCase):
    def report(self, median, *, capture=0):
        rows = []
        for pages, count in ((20, 5), (50, 10)):
            timings = [median] * count
            rows.append({'ownedPageCount': pages, 'deskCount': 5, 'switchCount': count,
                         'switches': [{'elapsedMs': value, 'counts': {'capturePage': capture}} for value in timings],
                         'switchLatencyMs': P['distribution'](timings), 'mainEventLoopSamplesMs': [1, 2, 3],
                         'mainEventLoop': P['distribution']([1, 2, 3]),
                         'renderer': {'gaps': [4, 5, 6], 'gapDistribution': P['distribution']([4, 5, 6])}})
        return {'stages': rows}

    def test_fixed_one_frame_boundary_and_zero_snapshots_for_both_runs(self):
        allowed = P['CRITERIA']['medianAllowanceMs']
        self.assertEqual(allowed, 1000 / 60)
        result = P['compare'](self.report(100), self.report(100 + allowed))
        self.assertAlmostEqual(result[0]['medianDeltaMs'], allowed)
        for before, after in ((100, 100 + allowed + .01), (0, 1), (100, 0)):
            with self.subTest(before=before, after=after), self.assertRaises(ValueError): P['compare'](self.report(before), self.report(after))
        for baseline in (False, True):
            with self.subTest(baseline=baseline), self.assertRaises(ValueError):
                P['compare'](self.report(100, capture=1 if baseline else 0), self.report(100, capture=0 if baseline else 1))

    def test_baseline_and_candidate_must_both_retain_fixed_250_600ms_tail_budget(self):
        for target in (0, 1):
            for values in ([300] * 10, [100] * 9 + [601]):
                reports = [self.report(100), self.report(100)]
                row = reports[target]['stages'][1]
                row['switches'] = [{'elapsedMs': v, 'counts': {'capturePage': 0}} for v in values]
                row['switchLatencyMs'] = P['distribution'](values)
                with self.subTest(target=target, values=values), self.assertRaises(ValueError): P['compare'](*reports)

    def test_raw_percentiles_loop_samples_and_renderer_gaps_are_recomputed(self):
        for target in (0, 1):
            for key in ('switchLatencyMs', 'mainEventLoop'):
                reports = [self.report(100), self.report(100)]; reports[target]['stages'][0][key]['p95'] = 0
                with self.subTest(target=target, key=key), self.assertRaises(ValueError): P['compare'](*reports)
            reports = [self.report(100), self.report(100)]; reports[target]['stages'][0]['renderer']['gaps'].append(50)
            with self.subTest(target=target), self.assertRaises(ValueError): P['compare'](*reports)


if __name__ == '__main__':
    unittest.main()
