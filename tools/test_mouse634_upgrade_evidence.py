#!/usr/bin/env python3
"""Synthetic native-process contracts only; never executes or claims real apps."""
import copy
import json
from pathlib import Path
import runpy
import unittest
E=runpy.run_path(str(Path(__file__).with_name('mouse634-upgrade-evidence.py')))
C=runpy.run_path(str(Path(__file__).with_name('mouse634-current.py')))


def fixture(platform):
 files={};native=[];transitions=[];arch='arm64' if platform=='darwin' else 'x64'
 formats=('deb','appimage') if platform=='linux' else (None,)
 packages={};url='http://127.0.0.1:31337/persisted'
 for number,fmt in enumerate(formats):
  extension=('deb' if fmt=='deb' else 'AppImage') if fmt else 'dmg' if platform=='darwin' else 'exe'
  name='Mouse-Browser-6.0.34-'+('Linux-x64.'+extension if fmt else 'mac-arm64.dmg' if platform=='darwin' else 'Windows-x64.exe')
  package={'name':name,'size':100*1024**2,'sha256':str(number+4)*64};packages[name]={k:v for k,v in package.items() if k!='name'}
  baseline=copy.deepcopy(E['BASELINES'][platform][fmt] if fmt else E['BASELINES'][platform]);baseline['url']='https://github.com/jeep-jim/OSMINOG-Releases/releases/download/'+baseline['tag']+'/'+baseline['name']
  prefix='mouse-634-upgrade'+('-'+fmt if fmt else '')
  facts={'ok':True,'fromVersion':'6.0.33','toVersion':'6.0.34','platform':platform,'method':E['LINUX_METHOD'] if fmt else E['METHOD'],'baseline':baseline,'package':package,'physicalUserDeviceVerified':False,'closedProfileUnchanged':True,'differentProcesses':True,'closedProfileSha256':'b'*64,'reportPrefix':prefix}
  if fmt: facts['format']=fmt
  for mode,version,relative in [('write','6.0.33',1),('read','6.0.34',2)]:
   pid=100+number*10+relative
   report={'ok':True,'mode':mode,'version':version,'platform':platform,'arch':arch,'pid':pid,'launcherPid':pid+1000 if fmt=='appimage' else pid,'reportPrefix':prefix,'source':E['SOURCE'],'physicalUserInputVerified':False,'nativeExit':{'code':0,'signal':None},'identity':{'version':version,'platform':platform,'arch':arch,'test':True},'profile':{'pageId':'page'+str(number),'url':url,'tokenSha256':'c'*64,'preferences':{'theme':'dark','aiWidth':413,'libraryWidth':417},'cookiePreserved':True,'localStoragePreserved':True,'bookmarkPreserved':True,'tabPreserved':True,'preferencesPreserved':True},'pageReadiness':{'ready':True,'attempts':2,'expectedURL':url,'expectedOrigin':'http://127.0.0.1:31337','target':{'id':'target','url':url},'last':{'href':url,'origin':'http://127.0.0.1:31337','readyState':'complete','title':'Mouse634 preserved profile fixture','input':True,'storageAccessible':True,'storageError':None},'evaluationError':None}}
   if fmt:
    report['processIdentity']={'source':'CDP SystemInfo.getProcessInfo and owned /proc','type':'browser','pid':pid,'uid':1001,'executable':'/opt/Mouse Browser/mouse-browser' if fmt=='deb' else '/tmp/.mount_Mouse/mouse-browser','appImage':None if fmt=='deb' else '/tmp/owned/Mouse Browser.AppImage','packageFormat':fmt,'exited':True}
   native.append(report);files[prefix+'-'+mode+'.log']=('MOUSE_634_UPGRADE_PROFILE_'+mode.upper()+'_PASS\nSynthetic unit fixture\n').encode();files[prefix+'-'+mode+'-app.log']=b'MOUSE_EXIT_SAVED\nMOUSE_APP_QUIT\n'
  if platform=='win32':
   for key in ('oldInstallation','replacement'): facts[key]={'exitCode':0,'peMachine':'0x8664','unicodeAndSpaces':True}
  if fmt:
   for key,phase,version,pkg in [('oldInstallation','old','6.0.33',baseline),('replacement','new','6.0.34',package)]:
    if fmt=='deb':
     log=prefix+'-'+phase+'-install.log';files[log]=b'Synthetic dpkg log\n';facts[key]={'exitCode':0,'pid':30,'packageName':'mouse-browser','version':version,'executable':'/opt/Mouse Browser/mouse-browser','log':log,'logSha256':E['sha'](files[log])}
    else: facts[key]={'method':'user-owned AppImage atomic replacement','target':'/tmp/owned/Mouse Browser.AppImage','uid':1001,'size':pkg['size'],'sha256':pkg['sha256'],'executable':True}
  transitions.append(facts)
 outer=transitions[0] if platform!='linux' else {'ok':True,'fromVersion':'6.0.33','toVersion':'6.0.34','platform':'linux','physicalUserDeviceVerified':False,'method':E['LINUX_METHOD'],'firstLinuxRelease':False,'previousVersion':'6.0.33','packages':packages,'formats':dict(zip(formats,transitions))}
 marker='MOUSE_634_REAL_633_TO_634_PROFILE_PASS';files['mouse-634-upgrade.log']=(marker+'\n').encode();files['mouse-633-owner-feedback.json']=b'{"syntheticOwner":true}'
 def refresh():
  for number,transition in enumerate(transitions):
   for i,(mode,key) in enumerate([('write','oldWrite'),('read','newRead')]):
    report=native[number*2+i];prefix=transition['reportPrefix'];name=prefix+'-'+mode+'.json';raw=json.dumps(report).encode();files[name]=raw;log=prefix+'-'+mode+'.log'
    transition[key]={'report':name,'reportSha256':E['sha'](raw),'log':log,'logSha256':E['sha'](files[log]),'result':copy.deepcopy(report)}
  files['mouse-634-upgrade.json']=json.dumps(outer).encode()
  if platform in ('win32','linux'):
   process={'exitCode':0,'pid':51,'elapsedMs':2000,'requiredMarkers':[marker],'reportSha256':E['sha'](files['mouse-634-upgrade.json'])}
   if platform=='linux': process.update(log='mouse-634-upgrade.log',logSha256=E['sha'](files['mouse-634-upgrade.log']))
   wrapper={'checks':{'freshUpgrade':process,'ownerFeedback':{'exitCode':0,'pid':52,'elapsedMs':1000,'requiredMarkers':['MOUSE_633_OWNER_FEEDBACK_PASS'],'reportSha256':E['sha'](files['mouse-633-owner-feedback.json'])}}}
   files['mouse-'+('windows' if platform=='win32' else 'linux')+'-verification.json']=json.dumps(wrapper).encode()
 refresh();return (packages if platform=='linux' else transitions[0]['package']),outer,native,files,refresh


def invoke(platform,files,package): return C['verify_upgrade'](files.__getitem__,platform=platform,arch='arm64' if platform=='darwin' else 'x64',**({'packages':package} if platform=='linux' else {'package':package}))


class ActualCurrentUpgrade(unittest.TestCase):
 def test_all_three_targets_require_actual_published633(self):
  for target in ('darwin','win32','linux'):
   package,facts,native,files,refresh=fixture(target);result=invoke(target,files,package);self.assertTrue(result['ok']);self.assertEqual(result['fromVersion'],'6.0.33')
   if target=='linux':self.assertEqual(set(result['formats']),{'deb','appimage'});self.assertNotEqual(native[-1]['pid'],native[-1]['launcherPid'])
 def test_old_package_and_candidate_bytes_cannot_change(self):
  for target in ('darwin','win32','linux'):
   for key in ('baseline','package'):
    package,facts,native,files,refresh=fixture(target);expected=copy.deepcopy(package);transition=facts['formats']['deb'] if target=='linux' else facts;transition[key]['sha256']='0'*64;refresh()
    with self.subTest(target=target,key=key),self.assertRaises(ValueError):invoke(target,files,expected)
 def test_linux_requires_both_actual_formats_and_owned_browser_pid(self):
  for field,value in [('uid',0),('pid',9999),('type','renderer'),('exited',False),('packageFormat','deb'),('appImage',None)]:
   package,facts,native,files,refresh=fixture('linux');native[-1]['processIdentity'][field]=value;refresh()
   with self.subTest(field=field),self.assertRaises(ValueError):invoke('linux',files,package)
  package,facts,native,files,refresh=fixture('linux');facts['formats'].pop('deb');refresh()
  with self.assertRaises(ValueError):invoke('linux',files,package)
 def test_committed_ready_document_is_required_before_profile_proof(self):
  for key,value in [('href','about:blank'),('origin','null'),('readyState','loading'),('input',False),('storageAccessible',False),('storageError','SecurityError')]:
   package,facts,native,files,refresh=fixture('win32');native[0]['pageReadiness']['last'][key]=value;refresh()
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'document was not ready'):invoke('win32',files,package)
 def test_native_identity_profile_and_graceful_exit_remain_mandatory(self):
  for key,value in [('version','6.0.29'),('pid',101),('nativeExit',{'code':1,'signal':None})]:
   package,facts,native,files,refresh=fixture('darwin');native[1][key]=value;refresh()
   with self.subTest(key=key),self.assertRaises(ValueError):invoke('darwin',files,package)
  for key in ('cookiePreserved','localStoragePreserved','bookmarkPreserved','tabPreserved','preferencesPreserved'):
   package,facts,native,files,refresh=fixture('win32');native[1]['profile'][key]=False;refresh()
   with self.subTest(key=key),self.assertRaises(ValueError):invoke('win32',files,package)
 def test_raw_bytes_and_actual_process_wrappers_are_required(self):
  package,facts,native,files,refresh=fixture('linux');files['mouse-634-upgrade-deb-read.json']+=b' '
  with self.assertRaises(ValueError):invoke('linux',files,package)
  for target in ('win32','linux'):
   for key,value in [('exitCode',1),('pid',0),('elapsedMs',999999),('reportSha256','0'*64),('requiredMarkers',[])]:
    package,facts,native,files,refresh=fixture(target);name='mouse-'+('windows' if target=='win32' else 'linux')+'-verification.json';wrapper=json.loads(files[name]);wrapper['checks']['freshUpgrade'][key]=value;files[name]=json.dumps(wrapper).encode()
    with self.subTest(target=target,key=key),self.assertRaises(ValueError):invoke(target,files,package)
 def test_appimage_replaces_the_same_owned_executable(self):
  for key,value in [('target','/tmp/different.AppImage'),('uid',0),('sha256','f'*64),('executable',False)]:
   package,facts,native,files,refresh=fixture('linux');facts['formats']['appimage']['replacement'][key]=value;refresh()
   with self.subTest(key=key),self.assertRaises(ValueError):invoke('linux',files,package)


if __name__=='__main__':unittest.main()
