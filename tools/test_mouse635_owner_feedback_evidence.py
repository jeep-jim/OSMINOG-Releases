#!/usr/bin/env python3
"""Exercise complete synthetic child reports and the real composition boundary."""
import copy
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

HERE=Path(__file__).parent
C=runpy.run_path(str(HERE/'mouse635-owner-feedback-evidence.py'))
L=runpy.run_path(str(HERE/'test_mouse635_library_evidence.py'))
P=runpy.run_path(str(HERE/'test_mouse635_public_search_evidence.py'))
A=runpy.run_path(str(HERE/'test_mouse635_agent_chat_evidence.py'))
D=runpy.run_path(str(HERE/'test_mouse635_pane_layout_evidence.py'))
encode=L['encode'];sha=L['sha']


def fixture(platform='linux',arch='x64'):
 library=L['fixture']();public=P['fixture'](platform,arch);agent=A['fixture'](platform,arch);panes=D['fixture'](platform,arch);native=library['owner']['nativeInputs']+public['owner']['nativeInputs']+agent['owner']['nativeInputs']+panes['owner']['nativeInputs']
 for i in range(9):native.append({'selector':'#library-'+('list' if i%2 else 'grid'),'source':'XTest','point':{'x':12,'y':24},'at':i+1,'navigates':False,'events':[{'type':'click','trusted':True,'matches':True}]})
 for row in native:row['source']={'linux':'XTest','win32':'User32','darwin':'CGEvent'}[platform]
 facts={'schema':1,'version':'6.0.35','platform':platform,'arch':arch,'pid':80,'budgetMs':240000,'elapsedMs':30000,'ok':True,'packaged':True,'profileIsolated':True,'restored':True,'stage':'complete','source':'Installed Electron production public-search IPC and owned local file updates with actual native input','physicalUserDeviceVerified':False,'cleanup':{'restored':True,'desktopStateRestored':True,'ownedPagesClosed':0,'originalPagesPreserved':1},'nativeInputs':native,'captures':library['facts']['captures']}
 facts['agentChat']=agent['owner']['agentChat'];facts['panes']=panes['owner']['panes'];facts['captures']=library['facts']['captures']+agent['owner']['captures']+panes['owner']['captures']+public['owner']['captures']
 raw={**library['raw'],**public['raw'],**agent['raw'],**panes['raw']}
 for name,value in [(L['C']['NAME'],library['facts']),(P['C']['NAME'],public['facts'])]:
  value.update(platform=platform,arch=arch);raw[name]=encode(value);facts['library' if 'library' in name else 'publicSearch']={**value,'reportFile':name,'reportSha256':sha(raw[name])}
 log=('\n'.join([*C['MARKERS'],P['C']['LIVE_MARKER'],'MOUSE_NATIVE_PROCESS_RETURN pid=80 code=0 elapsedMs=30100'])+'\n').encode();raw['mouse-635-owner-feedback.log']=log
 raw[C['NAME']]=encode(facts);wrapper={'checks':{'ownerFeedback635':{'exitCode':0,'pid':80,'elapsedMs':30100,'requiredMarkers':C['MARKERS'],'reportSha256':sha(raw[C['NAME']]),'log':'mouse-635-owner-feedback.log','logSha256':sha(log)}}}
 if platform!='darwin':raw['mouse-'+('linux' if platform=='linux' else 'windows')+'-verification.json']=encode(wrapper)
 return raw,facts,wrapper


def repack(raw,facts,wrapper):
 raw=dict(raw);raw[C['NAME']]=encode(facts);wrapper=copy.deepcopy(wrapper);wrapper['checks']['ownerFeedback635']['reportSha256']=sha(raw[C['NAME']])
 platform=facts['platform']
 if platform!='darwin':raw['mouse-'+('linux' if platform=='linux' else 'windows')+'-verification.json']=encode(wrapper)
 return raw


class Owner635(unittest.TestCase):
 def test_all_three_actual_process_contract_shapes(self):
  for platform,arch in [('linux','x64'),('win32','x64'),('darwin','arm64')]:
   with self.subTest(platform=platform):
    raw,_,_=fixture(platform,arch);result=C['verify'](raw.__getitem__);self.assertTrue(result['ok']);self.assertTrue(result['library']['stableDOM']);self.assertTrue(result['publicSearch']['ownerTopicCovered']);self.assertEqual(len(result['nativeCaptures']),17)
 def test_child_report_cannot_be_omitted_or_substituted(self):
  for name in (L['C']['NAME'],P['C']['NAME']):
   raw,_,_=fixture();raw.pop(name)
   with self.assertRaises((KeyError,ValueError)):C['verify'](raw.__getitem__)
  for field in ('library','publicSearch'):
   raw,facts,wrapper=fixture();facts[field]['reportSha256']='f'*64
   with self.assertRaises(ValueError):C['verify'](repack(raw,facts,wrapper).__getitem__)
 def test_process_exit_hash_markers_and_log_must_bind(self):
  for key,value in [('exitCode',1),('pid',81),('elapsedMs',270001),('requiredMarkers',[C['MARKERS'][-1]]),('reportSha256','f'*64),('logSha256','f'*64)]:
   raw,facts,wrapper=fixture();wrapper['checks']['ownerFeedback635'][key]=value;raw['mouse-linux-verification.json']=encode(wrapper)
   with self.assertRaises(ValueError):C['verify'](raw.__getitem__)
  raw,_,_=fixture('darwin','arm64');raw['mouse-635-owner-feedback.log']=raw['mouse-635-owner-feedback.log'].replace(b'pid=80',b'pid=81')
  with self.assertRaises(ValueError):C['verify'](raw.__getitem__)
 def test_success_cannot_hide_timeout_cleanup_or_extra_frame(self):
  for mutate in [lambda f:f.__setitem__('elapsedMs',240001),lambda f:f.__setitem__('cleanupErrors',['error']),lambda f:f['cleanup'].__setitem__('restored',False),lambda f:f['captures'].append({'filename':'unexpected.png'}),lambda f:f.__setitem__('physicalUserDeviceVerified',True)]:
   raw,facts,wrapper=fixture();mutate(facts)
   with self.assertRaises(ValueError):C['verify'](repack(raw,facts,wrapper).__getitem__)
 def test_composition_requires_retained_and_current_process(self):
  module=runpy.run_path(str(HERE/'mouse635-feedback-evidence.py'));calls=[];scope=module['verify'].__globals__
  def retained(read,**kwargs):calls.append('retained');return{'platform':'linux','arch':'x64','inputs':{'old.json':'a'}}
  def current(read,**kwargs):calls.append('current');return{'inputs':{'new.json':'b'},'ok':True}
  original=scope['_verify_634'];scope['_verify_634']=retained
  try:
   with patch.object(scope['runpy'],'run_path',return_value={'verify':current}):
    result=module['verify'](lambda name:b'');self.assertEqual(calls,['retained','current']);self.assertEqual(result['inputs'],{'old.json':'a','new.json':'b'})
   calls.clear()
   def failed(*args,**kwargs):raise ValueError('public RU query failed')
   with patch.object(scope['runpy'],'run_path',return_value={'verify':failed}):
    with self.assertRaisesRegex(ValueError,'RU'):module['verify'](lambda name:b'')
  finally:scope['_verify_634']=original


if __name__=='__main__':unittest.main()
