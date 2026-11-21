#!/usr/bin/env python3
"""Mandatory installed635 process: actual selected-engine pages and stable owned files."""
from pathlib import Path
import re
import runpy

N=runpy.run_path(str(Path(__file__).with_name('mouse635-native-evidence.py')))
L=runpy.run_path(str(Path(__file__).with_name('mouse635-library-evidence.py')))
P=runpy.run_path(str(Path(__file__).with_name('mouse635-public-search-evidence.py')))
A=runpy.run_path(str(Path(__file__).with_name('mouse635-agent-chat-evidence.py')))
D=runpy.run_path(str(Path(__file__).with_name('mouse635-pane-layout-evidence.py')))
need=N['need']
NAME='mouse-635-owner-feedback.json'
MARKERS=[P['MARKER'],L['MARKER'],A['MARKER'],D['MARKER'],'MOUSE_635_OWNER_FEEDBACK_PASS']


def verify(read,*,expected_platform=None,expected_arch=None):
 evidence=N['Evidence'](read);raw,facts=evidence.json(NAME)
 platform,arch,pid=facts.get('platform'),facts.get('arch'),facts.get('pid')
 need((platform,arch) in (('darwin','arm64'),('win32','x64'),('linux','x64')) and (expected_platform is None or platform==expected_platform) and (expected_arch is None or arch==expected_arch),'owner635 installed target differs')
 need(facts.get('schema')==1 and facts.get('version')=='6.0.35' and N['positive'](pid) and facts.get('budgetMs')==240000 and N['finite'](facts.get('elapsedMs')) and 0<facts['elapsedMs']<=240000,'owner635 actual process identity/budget missing')
 N['flags'](facts,('ok','packaged','profileIsolated','restored'),'owner635 failed or did not restore its isolated installed profile')
 need(facts.get('stage')=='complete' and facts.get('source')=='Installed Electron production public-search IPC and owned local file updates with actual native input' and facts.get('physicalUserDeviceVerified') is False and not facts.get('error') and not facts.get('cleanupErrors') and not facts.get('failureCaptureError'),'owner635 failed, overstated scope or hid cleanup errors')
 log=read('mouse-635-owner-feedback.log');need(isinstance(log,bytes) and 0<len(log)<=16*1024**2,'owner635 actual process log missing');lines=log.decode('utf-8').splitlines()
 need(all(marker in lines for marker in MARKERS),'owner635 native search, library or process marker missing')
 if platform in ('win32','linux'):
  _,wrapper=evidence.json('mouse-'+('windows' if platform=='win32' else 'linux')+'-verification.json');process=wrapper.get('checks',{}).get('ownerFeedback635',{})
  need(process.get('exitCode')==0 and process.get('pid')==pid and N['finite'](process.get('elapsedMs')) and 0<process['elapsedMs']<=270000 and process.get('requiredMarkers')==MARKERS and process.get('reportSha256')==N['sha'](raw),'owner635 wrapper/process/report byte binding differs')
  if platform=='linux':need(process.get('log')=='mouse-635-owner-feedback.log' and process.get('logSha256')==N['sha'](log),'owner635 actual Linux log byte binding differs')
 else:
  returned=[re.fullmatch(r'MOUSE_NATIVE_PROCESS_RETURN pid=(\d+) code=(\d+) elapsedMs=(\d+)',line) for line in lines];returned=[row for row in returned if row]
  need(len(returned)==1 and int(returned[0][1])==pid and int(returned[0][2])==0 and 0<int(returned[0][3])<=270000,'owner635 actual macOS child PID/exit/budget receipt missing')
 cleanup=facts.get('cleanup',{});N['flags'](cleanup,('restored','desktopStateRestored'),'owner635 original desktop did not restore')
 need(all(type(cleanup.get(key)) is int and cleanup[key]>=0 for key in ('ownedPagesClosed','originalPagesPreserved')),'owner635 original and owned page accounting missing')
 native=facts.get('nativeInputs');need(isinstance(native,list) and 20<=len(native)<=100,'owner635 actual native input ledger missing')
 for row in native:N['input_event'](row,platform,row.get('selector'))
 library=L['verify'](read,expected_platform=platform,expected_arch=arch,owner=facts)
 public=P['verify'](read,expected_platform=platform,expected_arch=arch,owner=facts)
 agent=A['verify'](read,owner=facts)
 panes=D['verify'](read,owner=facts)
 need(isinstance(facts.get('captures'),list) and 17<=len(facts['captures'])<=55 and len({row.get('filename') for row in facts['captures']})==len(facts['captures']) and facts['captures'][:8]==facts['library']['captures'] and [row.get('filename') for row in facts['captures'][8:]]==A['CAPTURES']+D['CAPTURES']+public['nativeCaptures'],'owner635 frame ledger differs from actual library, Agent, layout and all selected-engine paint attempts')
 inputs={NAME:N['sha'](raw),'mouse-635-owner-feedback.log':N['sha'](log),**library['inputs'],**public['inputs'],**agent['inputs'],**panes['inputs']}
 return{'ok':True,'version':'6.0.35','platform':platform,'arch':arch,'pid':pid,'reportSha256':N['sha'](raw),'nativeInputSource':N['source'](platform),'publicSearch':public,'library':library,'agentChat':agent,'paneLayout':panes,'inputs':inputs,'nativeCaptures':library['nativeCaptures']+agent['nativeCaptures']+panes['nativeCaptures']+public['nativeCaptures'],'canonicalCaptures':[row['filename'] for row in facts['captures'][:14]]+public['canonicalCaptures'],'physicalUserDeviceVerified':False}
