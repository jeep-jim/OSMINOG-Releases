#!/usr/bin/env python3
"""Synthetic old/new process records; these tests never execute native packages."""
import ast
import copy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

E=runpy.run_path(str(Path(__file__).with_name('mouse633-upgrade-evidence.py')))
C=runpy.run_path(str(Path(__file__).with_name('mouse633-current.py')))


def fixture(platform):
 arch='arm64' if platform=='darwin' else 'x64';files={};native=[]
 package={'name':'Mouse-Browser-6.0.33-'+('mac-arm64.dmg' if platform=='darwin' else 'Windows-x64.exe'),'size':100*1024**2,'sha256':'a'*64}
 baseline=copy.deepcopy(E['BASELINES'][platform]);baseline['url']='https://github.com/jeep-jim/OSMINOG-Releases/releases/download/'+baseline['tag']+'/'+baseline['name']
 facts={'ok':True,'fromVersion':'6.0.32','toVersion':'6.0.33','platform':platform,'method':E['METHOD'],
  'baseline':baseline,'package':package,'physicalUserDeviceVerified':False,'closedProfileUnchanged':True,
  'differentProcesses':True,'closedProfileSha256':'b'*64}
 for mode,version,pid in [('write','6.0.32',101),('read','6.0.33',202)]:
  native.append({'ok':True,'mode':mode,'version':version,'platform':platform,'arch':arch,'pid':pid,'source':E['SOURCE'],
   'physicalUserInputVerified':False,'nativeExit':{'code':0,'signal':None},
   'identity':{'version':version,'platform':platform,'arch':arch,'test':True},
   'profile':{'pageId':'page1','url':'http://127.0.0.1:31337/persisted','tokenSha256':'c'*64,
    'preferences':{'theme':'dark','aiWidth':413,'libraryWidth':417},'cookiePreserved':True,
    'localStoragePreserved':True,'bookmarkPreserved':True,'tabPreserved':True,'preferencesPreserved':True}})
  files['mouse-633-upgrade-'+mode+'.log']=('MOUSE_633_UPGRADE_PROFILE_'+mode.upper()+'_PASS\n').encode()
  files['mouse-633-upgrade-'+mode+'-app.log']=b'MOUSE_EXIT_SAVED\nMOUSE_APP_QUIT\n'
 if platform=='win32':
  facts.update(oldInstallation={'exitCode':0,'peMachine':'0x8664','unicodeAndSpaces':True},replacement={'exitCode':0,'peMachine':'0x8664','unicodeAndSpaces':True})
 files['mouse-633-upgrade.log']=b'MOUSE_633_REAL_632_TO_633_PROFILE_PASS\n'
 files['mouse-633-owner-feedback.json']=b'{"syntheticOwner":true}'
 def refresh():
  for mode,key,report in zip(('write','read'),('oldWrite','newRead'),native):
   raw=json.dumps(report).encode();files['mouse-633-upgrade-'+mode+'.json']=raw
   facts[key]={'reportSha256':E['sha'](raw),'logSha256':E['sha'](files['mouse-633-upgrade-'+mode+'.log']),'result':copy.deepcopy(report)}
  files['mouse-633-upgrade.json']=json.dumps(facts).encode()
  if platform=='win32':
   files['mouse-windows-verification.json']=json.dumps({'checks':{
    'freshUpgrade':{'exitCode':0,'pid':71,'elapsedMs':2000,'requiredMarkers':['MOUSE_633_REAL_632_TO_633_PROFILE_PASS'],'reportSha256':E['sha'](files['mouse-633-upgrade.json'])},
    'ownerFeedback':{'exitCode':0,'pid':72,'elapsedMs':1000,'requiredMarkers':['MOUSE_633_OWNER_FEEDBACK_PASS'],'reportSha256':E['sha'](files['mouse-633-owner-feedback.json'])}}}).encode()
 refresh();return package,facts,native,files,refresh


class ActualCurrentUpgrade(unittest.TestCase):
 def invoke(self,platform,files,package):
  return C['verify_upgrade'](files.__getitem__,platform=platform,arch='arm64' if platform=='darwin' else 'x64',package=package)

 def test_complete_synthetic_old_and_new_process_contracts(self):
  for platform in ('darwin','win32'):
   package,facts,native,files,refresh=fixture(platform)
   result=self.invoke(platform,files,package)
   self.assertEqual(result['fromVersion'],'6.0.32');self.assertEqual(result['newPid'],202)

 def test_629_evidence_cannot_be_relabelled_as_current632_upgrade(self):
  for platform in ('darwin','win32'):
   package,facts,native,files,refresh=fixture(platform);native[0]['version']='6.0.29';refresh()
   with self.subTest(platform=platform),self.assertRaises(ValueError):self.invoke(platform,files,package)

 def test_old_package_bytes_and_new_candidate_must_match_exact_pins(self):
  for target in ('baseline','package'):
   package,facts,native,files,refresh=fixture('darwin');expected=copy.deepcopy(package);facts[target]['sha256']='0'*64;refresh()
   with self.subTest(target=target),self.assertRaisesRegex(ValueError,'immutable package'):self.invoke('darwin',files,expected)

 def test_same_process_or_rehashed_different_profile_cannot_pass(self):
  for field,value in [('pid',101),('profile',{'invented':'profile'})]:
   package,facts,native,files,refresh=fixture('darwin');native[1][field]=value;refresh()
   with self.subTest(field=field),self.assertRaises(ValueError):self.invoke('darwin',files,package)

 def test_cookie_bookmark_storage_tab_and_preferences_are_independent(self):
  for key in ('cookiePreserved','localStoragePreserved','bookmarkPreserved','tabPreserved','preferencesPreserved'):
   package,facts,native,files,refresh=fixture('win32');native[1]['profile'][key]=False;refresh()
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'profile values'):self.invoke('win32',files,package)

 def test_actual_runtime_identity_and_graceful_exit_are_required(self):
  for key,value in [('identity',{}),('nativeExit',{'code':1,'signal':None}),('physicalUserInputVerified',True)]:
   package,facts,native,files,refresh=fixture('darwin');native[0][key]=value;refresh()
   with self.subTest(key=key),self.assertRaises(ValueError):self.invoke('darwin',files,package)

 def test_native_report_and_probe_log_raw_hashes_are_required(self):
  package,facts,native,files,refresh=fixture('darwin');files['mouse-633-upgrade-read.json']+=b' '
  with self.assertRaisesRegex(ValueError,'raw native'):self.invoke('darwin',files,package)
  refresh();files['mouse-633-upgrade-read.log']+=b'changed\n'
  with self.assertRaisesRegex(ValueError,'probe log'):self.invoke('darwin',files,package)

 def test_production_lifecycle_saved_and_quit_markers_are_required(self):
  package,facts,native,files,refresh=fixture('darwin');files['mouse-633-upgrade-write-app.log']=b'synthetic unrelated process\n'
  with self.assertRaisesRegex(ValueError,'save and quit'):self.invoke('darwin',files,package)

 def test_windows_wrapper_binds_both_actual_current_processes(self):
  for stage in ('freshUpgrade','ownerFeedback'):
   for key,value in [('exitCode',1),('pid',0),('elapsedMs',999999),('reportSha256','0'*64),('requiredMarkers',[])]:
    package,facts,native,files,refresh=fixture('win32');wrapper=json.loads(files['mouse-windows-verification.json']);wrapper['checks'][stage][key]=value
    files['mouse-windows-verification.json']=json.dumps(wrapper).encode()
    with self.subTest(stage=stage,key=key),self.assertRaisesRegex(ValueError,'byte binding'):self.invoke('win32',files,package)

 def test_linux_first_release_cannot_claim_a_current632_baseline(self):
  package,facts,native,files,refresh=fixture('darwin')
  with self.assertRaisesRegex(ValueError,'unsupported target'):E['verify'](files.__getitem__,expected_platform='linux',expected_arch='x64',expected_package=package)

 def test_every_windows_import_install_and_publish_path_calls_the_current_upgrade_gate(self):
  reuse=runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))
  tree=reuse['adapted_tree']('mouse632-windows-release.py')
  functions={node.name:node for node in tree.body if isinstance(node,ast.FunctionDef)}
  for name in ('import_candidate','verify_installed','publish'):
   calls=[node for node in ast.walk(functions[name]) if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='_verify_current_upgrade']
   self.assertEqual(len(calls),1,name)

 def test_source_helper_download_rejects_wrong_git_blob(self):
  import base64,tempfile
  with tempfile.TemporaryDirectory() as folder:
   with self.assertRaisesRegex(ValueError,'Git blob'):
    C['fetch_helpers'](lambda *a:{'content':base64.b64encode(b'not reviewed').decode(),'sha':'0'*40},'repo','a'*40,Path(folder))
   self.assertEqual(list(Path(folder).iterdir()),[])


if __name__=='__main__':unittest.main()
