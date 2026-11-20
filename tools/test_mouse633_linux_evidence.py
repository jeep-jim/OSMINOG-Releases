#!/usr/bin/env python3
"""Synthetic Linux installation witnesses. Never native acceptance evidence.

The actual Linux validator/PNG decoder and all provenance/process decisions run.
Only independently-tested task/current-owner/scrollbar downstream algorithms are
replaced at their API boundaries so these tests isolate Linux installation facts.
"""
import copy
import json
from pathlib import Path
import runpy
import struct
import unittest
from unittest.mock import patch, Mock
import zlib

E=runpy.run_path(str(Path(__file__).with_name('mouse633-linux-evidence.py')))


def png(theme):
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    pixel=b'\x20\x40\x80\xff' if theme=='dark' else b'\xc0\xd0\xe0\xff'
    raw=(b'\0'+pixel*800)*600
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',800,600,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')


def fixture():
    files={};native=[]
    p={'source':'a'*40,'run':11,'attempt':1,'packages':{f'Mouse-Browser-6.0.33-Linux-x64.{ext}':{'size':123456789,'sha256':x*64} for ext,x in [('AppImage','c'),('deb','d')]}}
    def process(name,pid,markers):
        files[name]=('\n'.join(markers)+'\nsynthetic fixture only\n').encode()
        return {'exitCode':0,'pid':pid,'elapsedMs':100,'log':Path(name).name,'logSha256':E['sha'](files[name]),'requiredMarkers':list(markers)}
    for index,(mode,package,prefix) in enumerate([('write','deb',''),('read','deb',''),('read','appimage','mouse-linux-appimage/')]):
        pid=10+index*10
        profile={'written':True,'tokenSha256':'1'*64,'pageId':'page-1'} if index==0 else {
            'previousVersion':'6.0.33','currentVersion':'6.0.33','previousPid':10,'currentPid':pid,
            'differentProcess':True,'preferencesPreserved':True,'cookiePreserved':True,'localStoragePreserved':True,
            'bookmarkPreserved':True,'tokenSha256':'1'*64,'pageId':'page-1'}
        rows=[{'pid':100+pid+j,'seccomp':2,'noNewPrivs':1,'uid':1001,'webContentsId':20+j,
               'argv':['/opt/mouse-browser/mouse-browser','--type=renderer'],
               'preferences':{'sandbox':True,'contextIsolation':True,'webSecurity':True,'nodeIntegration':False}} for j in range(2)]
        captures=[]
        for theme in ('light','dark'):
            name=f'mouse-linux-{mode}-{theme}.png';raw=png(theme);files[prefix+name]=raw
            captures.append({'filename':name,'sha256':E['sha'](raw),'theme':theme,'source':'globalCapture.acquire(display)',
                'backend':'desktopCapturer','screenPixelSize':{'width':800,'height':600},
                'display':{'id':1,'scaleFactor':1,'bounds':{'x':0,'y':0,'width':800,'height':600}},
                'window':{'x':10,'y':20,'width':780,'height':570}})
        native.append({'ok':True,'version':'6.0.33','platform':'linux','arch':'x64','pid':pid,'mode':mode,
                       'packageFormat':package,'appImage':None if package=='deb' else '/tmp/owned/Mouse-Browser-6.0.33-Linux-x64.AppImage',
                       'physicalUserDeviceVerified':False,'displayBackend':'X11','asarSha256':'2'*64,
                       'sandbox':{'disabledFlags':[],'renderers':rows},'nativeClose':{'accelerator':'Ctrl+Q','input':'XTest'},'profile':profile,'captures':captures})
    files['mouse-632-documents.json']=b'{"synthetic downstream":"documents"}'
    native[0]['checks']={'nativeInput':{'ctrlASelects':True,'noCaptureFromCtrlA':True,'scrollbarHidden':True,'source':'XTest via xdotool','wheelScrollY':120},
        'private':{'normalWebContentsPreserved':True,'privateWebContentsClosed':True,'privateCookiesCleared':True,'noPrivateProfileMarker':True},
        'nativeRuntime':{'terminalPid':55,'terminalExitCode':0,'terminalOutput':'MOUSE_LINUX_PTY_OK\n','nativeFileRead':True},
        'documents':{'report':'mouse-632-documents.json','sha256':E['sha'](files['mouse-632-documents.json'])}}
    installation={**process('mouse-linux-install.log',4,()),'packageName':'mouse-browser','version':'6.0.33','executable':'/opt/Mouse Browser/mouse-browser',
                  'desktopFile':'/usr/share/applications/mouse-browser.desktop','desktopSha256':'3'*64,'executableSha256':'4'*64}
    reinstallation={**installation,**process('mouse-linux-reinstall.log',5,())}
    report={'ok':True,'version':'6.0.33','platform':'linux','arch':'x64','source':p['source'],'runId':'11','runAttempt':'1',
            'firstLinuxRelease':True,'previousVersion':None,'packages':copy.deepcopy(p['packages']),'ownerDeviceVerified':False,
            'runner':{'system':'Linux','release':'synthetic','uid':1001,'display':':99'},'checks':{'debInstallation':installation,'debReinstallation':reinstallation}}
    report['checks']['profileRestart']={'write':process('mouse-linux-write.log',10,('MOUSE_LINUX_PROFILE_WRITE_PASS','MOUSE_LINUX_X64_SMOKE_PASS')),
        'read':process('mouse-linux-read.log',20,('MOUSE_LINUX_PROFILE_RESTART_PASS','MOUSE_LINUX_X64_SMOKE_PASS')),
        'differentPids':True,'closedProfileUnchanged':True,'closedProfileSha256':'5'*64,'preserved':copy.deepcopy(native[1]['profile'])}
    report['checks']['appImageLaunch']={**process('mouse-linux-appimage/mouse-linux-appimage.log',29,('MOUSE_LINUX_PROFILE_RESTART_PASS','MOUSE_LINUX_X64_SMOKE_PASS')),
        'package':'Mouse-Browser-6.0.33-Linux-x64.AppImage','packageSha256':'c'*64,'report':E['FILES'][2],
        'sameAsar':True,'asarSha256':'2'*64,'preserved':copy.deepcopy(native[2]['profile'])}
    report['checks']['retainedTaskStress']=process('mouse-631-native.log',40,E['TASK_MARKERS'])
    for name,key in [('mouse-631-native.json','reportSha256'),('mouse-631-task.json','taskSha256'),('mouse-631-stress.json','stressSha256'),('mouse-632-media.json','mediaSha256')]:
        files[name]=json.dumps({'syntheticDownstream':name}).encode();report['checks']['retainedTaskStress'][key]=E['sha'](files[name])
    files['mouse-633-owner-feedback.json']=b'{"synthetic downstream":"owner"}'
    report['checks']['ownerFeedback']={**process('mouse-633-owner-feedback.log',50,(E['OWNER_MARKER'],)),
        'reportSha256':E['sha'](files['mouse-633-owner-feedback.json'])}
    files['mouse-629-ui-regressions.json']=json.dumps({'version':'6.0.33','platform':'linux','arch':'x64','restored':True,'scrollbars':{'synthetic':True}}).encode()
    files['mouse-632-footer.json']=b'{"synthetic downstream":"footer"}'
    for kind,name in [('footer','mouse-632-footer.json'),('scrollbars','mouse-629-ui-regressions.json')]:
        native[0]['checks'][kind]={'report':name,'sha256':E['sha'](files[name])}
    def refresh():
        for name,document in zip(E['FILES'],native):files[name]=json.dumps(document).encode()
        report['checks']['profileRestart']['writeSha256']=E['sha'](files[E['FILES'][0]])
        report['checks']['profileRestart']['readSha256']=E['sha'](files[E['FILES'][1]])
        report['checks']['appImageLaunch']['reportSha256']=E['sha'](files[E['FILES'][2]])
        report['sandbox']={'disabledFlags':[],'renderers':copy.deepcopy(native[0]['sandbox']['renderers']+native[2]['sandbox']['renderers'])}
        files['mouse-linux-verification.json']=json.dumps(report).encode()
    refresh()
    return p,report,native,files,refresh


class LinuxInstalledEvidence(unittest.TestCase):
    def setUp(self):self.pin,self.report,self.native,self.files,self.refresh=fixture()

    def invoke(self, downstream_error=None):
        task=Mock(return_value={'checked':'task'},side_effect=downstream_error)
        owner=Mock(return_value={'checked':'owner'},side_effect=downstream_error)
        scrollbar=Mock(return_value={'checked':'scrollbar'},side_effect=downstream_error)
        def load(path):
            if str(path).endswith('mouse633-feedback-evidence.py'):return {'verify':owner}
            if str(path).endswith('mouse633-ui-evidence.py'):return {'verify_scrollbars':scrollbar}
            self.fail('unexpected dependency')
        with patch.dict(E['verify'].__globals__,task_gate=task),patch.object(runpy,'run_path',side_effect=load):
            result=E['verify'](self.files.__getitem__,self.pin)
        task.assert_called_once();owner.assert_called_once_with(self.files.__getitem__,expected_platform='linux',expected_arch='x64')
        scrollbar.assert_called_once()
        return result

    def test_complete_synthetic_native_contract_and_appimage_launcher_pid_difference(self):
        result=self.invoke();self.assertEqual(result['sandboxRendererCount'],4);self.assertEqual(len(result['nativeCaptures']),6)
        self.assertIsNone(result['previousVersion'])

    def test_wrong_os_version_or_invented_previous_release_fails(self):
        for key,value in [('platform','win32'),('version','6.0.32'),('previousVersion','6.0.32'),('firstLinuxRelease',False),('ownerDeviceVerified',True)]:
            old=self.report[key];self.report[key]=value;self.refresh()
            with self.subTest(key=key),self.assertRaises(ValueError):self.invoke()
            self.report[key]=old

    def test_missing_or_root_runner_cannot_claim_native_linux(self):
        for key,value in [('uid',0),('system','Windows'),('display','external.example:0')]:
            old=self.report['runner'][key];self.report['runner'][key]=value;self.refresh()
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'runner'):self.invoke()
            self.report['runner'][key]=old

    def test_failed_installer_and_wrong_executable_path_are_rejected(self):
        for name in ('debInstallation','debReinstallation'):
            self.report['checks'][name]['exitCode']=1;self.refresh()
            with self.subTest(name=name),self.assertRaises(ValueError):self.invoke()
            self.report['checks'][name]['exitCode']=0
        self.report['checks']['debInstallation']['executable']='/tmp/extracted/mouse-browser';self.refresh()
        with self.assertRaisesRegex(ValueError,'deb installation'):self.invoke()

    def test_unsafe_renderer_preferences_or_disabled_sandbox_cannot_pass(self):
        for key,value in [('seccomp',0),('noNewPrivs',0),('uid',0),('argv',['browser','--type=renderer','--no-sandbox'])]:
            row=self.native[2]['sandbox']['renderers'][0];old=row[key];row[key]=value;self.refresh()
            with self.subTest(key=key),self.assertRaises(ValueError):self.invoke()
            row[key]=old
        self.native[0]['sandbox']['renderers'][0]['preferences']['nodeIntegration']=True;self.refresh()
        with self.assertRaisesRegex(ValueError,'preferences'):self.invoke()

    def test_actual_appimage_runtime_and_identical_asar_are_required(self):
        for key,value in [('packageFormat','deb'),('appImage',None),('asarSha256','9'*64)]:
            old=self.native[2][key];self.native[2][key]=value;self.refresh()
            with self.subTest(key=key),self.assertRaises(ValueError):self.invoke()
            self.native[2][key]=old

    def test_two_profiles_cannot_be_relabelled_as_one_restart(self):
        self.native[2]['profile']['tokenSha256']='8'*64;self.refresh()
        with self.assertRaisesRegex(ValueError,'another native process'):self.invoke()

    def test_rehashed_wrong_native_pid_still_fails_profile_identity(self):
        self.native[1]['pid']=10;self.refresh()
        with self.assertRaisesRegex(ValueError,'distinct native processes'):self.invoke()

    def test_profile_preservation_flags_and_closed_profile_hash_are_required(self):
        self.report['checks']['profileRestart']['closedProfileSha256']='';self.refresh()
        with self.assertRaisesRegex(ValueError,'byte-bound'):self.invoke()
        self.report['checks']['profileRestart']['closedProfileSha256']='5'*64
        self.native[1]['profile']['bookmarkPreserved']=False;self.refresh()
        with self.assertRaisesRegex(ValueError,'preservation'):self.invoke()

    def test_native_png_hash_and_dpi_are_recomputed(self):
        self.native[2]['captures'][0]['display']['scaleFactor']=2;self.refresh()
        with self.assertRaisesRegex(ValueError,'framebuffer scale'):self.invoke()
        self.native[2]['captures'][0]['display']['scaleFactor']=1;self.refresh()
        self.files['mouse-linux-appimage/mouse-linux-read-light.png']=png('dark')
        with self.assertRaisesRegex(ValueError,'PNG byte'):self.invoke()

    def test_all_theme_captures_and_the_owned_window_are_required(self):
        self.native[0]['captures'][0]['window']['x']=900;self.refresh()
        with self.assertRaisesRegex(ValueError,'outside'):self.invoke()
        self.native[0]['captures'].pop();self.refresh()
        with self.assertRaisesRegex(ValueError,'both Linux themes'):self.invoke()

    def test_real_pty_native_file_and_private_cleanup_are_required(self):
        for group,key in [('nativeRuntime','nativeFileRead'),('private','privateCookiesCleared'),('nativeInput','noCaptureFromCtrlA')]:
            self.native[0]['checks'][group][key]=False;self.refresh()
            with self.subTest(group=group),self.assertRaises(ValueError):self.invoke()
            self.native[0]['checks'][group][key]=True

    def test_log_success_and_raw_owner_task_hashes_cannot_be_fabricated(self):
        self.files['mouse-633-owner-feedback.log']=b'no success marker\n'
        self.report['checks']['ownerFeedback']['logSha256']=E['sha'](self.files['mouse-633-owner-feedback.log']);self.refresh()
        with self.assertRaisesRegex(ValueError,'success marker'):self.invoke()

    def test_downstream_native_evidence_rejection_propagates(self):
        with self.assertRaisesRegex(ValueError,'downstream rejected'):self.invoke(ValueError('downstream rejected'))


if __name__=='__main__':unittest.main()
