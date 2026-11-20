#!/usr/bin/env python3
"""Complete synthetic owner633 witnesses; no fixture is native release evidence.

These exercise the actual independent checker and PNG decoder without mocking
verification. Tampered pixels, claims, input, lifecycle and private routes fail.
"""
import copy
import json
from pathlib import Path
import runpy
import struct
import unittest
import zlib

E=runpy.run_path(str(Path(__file__).with_name('mouse633-owner-feedback-evidence.py')))


def png(width,height,color=(238,238,238,255),meter=None):
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 pixels=bytearray(bytes(color)*width*height)
 if meter:
  x,y,w,h=meter
  for row in range(y,y+h):pixels[(row*width+x)*4:(row*width+x+w)*4]=bytes((235,40,155,255))*w
 raw=b''.join(b'\0'+pixels[y*width*4:(y+1)*width*4] for y in range(height))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')


def fixture(platform='win32',available=True):
 arch='arm64' if platform=='darwin' else 'x64';origin='http://127.0.0.1:31337';files={};baseline=[];natives=[]
 for i in (0,1):
  identity='owned-'+str(i)
  baseline.append({'id':'page-'+str(i),'index':i,'desk':'d0','webContentsId':100+i,'url':origin+'/page/'+str(i)+'/',
   'navigationEpoch':1,'identity':identity,'timeOrigin':10000+i,'field':'preserved-'+str(i)+'-данные',
   'cookie':'mouse631_'+str(i)+'='+identity,'scrollX':0,'scrollY':130+i,'ticks':10,'raf':10})
  bounds={'x':i*220,'y':120,'width':200,'height':300}
  natives.append({'tabId':'page-'+str(i),'index':i,'desk':'d0','webContentsId':100+i,'bounds':bounds.copy(),
   'viewBounds':bounds.copy(),'parentBounds':None,'actualBounds':bounds.copy(),'visible':True,'parentVisible':True,'cachedVisible':True,'attached':True})
 def live():return {'before':copy.deepcopy(baseline),'after':[{**row,'raf':11,'ticks':11} for row in baseline],'native':copy.deepcopy(natives)}
 def reload():return {'before':{'processId':11,'routingId':2,'timeOrigin':1000},'after':{'processId':11,'routingId':2,'timeOrigin':2000}}
 sections=[{'name':name,'hidden':False,'title':name} for name in E['SECTIONS']]
 initial={'open':True,'nonmodal':True,'inWorkspace':True,'rightmostGear':True,'gearCount':1,'gearExpanded':'true',
  'panel':{'x':500,'y':100,'width':300,'height':500,'right':800,'bottom':600},'workspace':{'x':0,'y':100,'width':800,'height':500,'right':800,'bottom':600},
  'sections':sections,'toggles':[{'key':key,'checked':False,'disabled':False} for key in E['SETTINGS']],'search':'','theme':'light'}
 facts={'schema':1,'version':'6.0.33','platform':platform,'arch':arch,'pid':123,'budgetMs':240000,'elapsedMs':120000,
  'ok':True,'restored':True,'packaged':True,'profileIsolated':True,'physicalUserDeviceVerified':False,'liveExternalAccountsVerified':False,
  'source':E['SOURCE'],'stage':'complete','fixtureOrigin':origin,'cleanup':{'restored':True,'desktopStateRestored':True},
  'pageRequests':[{'index':i,'at':100+i} for i in (0,1)],'nativeInputSource':{'darwin':'CGEvent','win32':'User32','linux':'XTest'}[platform],
  'nativeInputs':[],'captures':[]}
 facts['settings']={'rightmostGear':True,'nonmodal':True,'initial':initial,'sections':list(E['SECTIONS']),
  'search':{'query':'Загрузки','visibleSections':['downloads'],'input':{'events':[{'type':'input','trusted':True,'matches':True}]},
   'readback':{'sections':[{**row,'hidden':row['name']!='downloads'} for row in sections]}},
  'toggles':[{'key':key,'before':False,'changed':True,'afterReload':True,'restored':False} for key in E['SETTINGS']],
  'persisted':dict.fromkeys(E['SETTINGS'],True),'reload':reload(),
  'afterReload':{'toggles':[{'key':key,'checked':True} for key in E['SETTINGS']]},'livePages':live(),'liveAfterReload':live()}
 facts['agent']={'homeEntry':True,'presetEntry':True,'settingsEntry':True,'openingSources':['home','ai-preset','settings'],
  'enabledBefore':False,'enabledAfter':False,'connectionRestored':False,'connectedClients':0,
  'modelEntry':{'open':True,'visible':True},'permissionsEntry':{'open':True,'visible':True},'ollamaEntry':{'open':True,'visible':True},
  'onboarding':{'downloadButton':True,'checkButton':True,'title':'Агент Маус','officialDownloadURL':'https://ollama.com/download'},
  'closedAndReopened':True,'panelRestoredAfterReload':True,'reload':reload()}
 def screen(name):
  raw=png(800,600);files[name]=raw;display=name[:-4]+'-display.png';files[display]=raw
  row={'filename':name,'source':'globalCapture.acquire(display)','backend':'unit fixture only','bytes':len(raw),'sha256':E['digest'](raw),
   'displayFilename':display,'displaySha256':E['digest'](raw),'screenPixelSize':{'width':800,'height':600},'pixelSize':{'width':800,'height':600},
   'contentBounds':{'x':0,'y':0,'width':800,'height':600},'display':{'id':1,'bounds':{'x':0,'y':0,'width':800,'height':600},'scaleFactor':1},
   'cropPixels':{'x':0,'y':0,'width':800,'height':600},'mapping':{'scaleX':1,'scaleY':1,'originX':0,'originY':0}}
  facts['captures'].append(row);return row
 for name in ['mouse-633-settings-light.png','mouse-633-settings-dark.png','mouse-633-agent-onboarding.png','mouse-633-download-active.png','mouse-633-download-completed.png']:screen(name)
 facts['zoom']={}
 for kind,factor in [('popover',1.1),('settings',1.2)]:
  value={'openAfterChange':True,'gateBlocked':False,'factorBefore':1,'factorAfter':factor,'livePages':live()}
  for phase,zoom in [('before',1),('after',factor)]:
   name='mouse-633-zoom-'+kind+'-'+phase+'.png';screen(name);pages=[]
   for i in (0,1):
    filename='mouse-633-zoom-'+kind+'-'+phase+'-guest-'+str(i)+'.png';x,y=round(24*zoom),round(180*zoom);w,h=round(128*zoom),round(40*zoom)
    raw=png(200,300,meter=(x,y,w,h));files[filename]=raw
    row={'filename':filename,'source':'WebContents.capturePage; excludes shell controls','bytes':len(raw),'sha256':E['digest'](raw),
      'pixelSize':{'width':200,'height':300},'rect':{'x':0,'y':0,'width':200,'height':300},'factor':zoom,'scaleX':1,'scaleY':1,
      'meter':{'x':x,'y':y,'width':w,'height':h,'count':w*h},'expectedMeter':{'width':128*zoom,'height':40*zoom},
      'native':copy.deepcopy(natives[i]),'identity':copy.deepcopy(baseline[i])}
    facts['captures'].append(row);pages.append(row)
   value[phase]={'shell':name,'pages':pages}
  if kind=='settings':value.update(inputSource='native focused range; webContents.sendInputEvent Home then 19 ArrowRight',readback={'open':True,'value':'120','output':'120%'})
  facts['zoom'][kind]=value
 def progress(received):return {'state':{'items':[{'filename':'mouse633-known.bin','received':received,'total':524288}]},
  'button':{'count':1,'indeterminate':False,'bounce':False,'unread':0,'percent':received*100/524288,'ringDisplay':'block'}}
 downloads=[]
 for i,name in enumerate(('known','unknown')):
  size=524288 if i==0 else 393216;checksum=E['digest']((b'A' if i==0 else b'B')*size);total=size if i==0 else 0
  downloads.append({'name':name,'filename':'mouse633-'+name+'.bin','bytes':size,'sha256':checksum,'expectedSha256':checksum,'webContentsId':100+i,
   'saveDecision':'DownloadItem.setSavePath restricted to the owned HTTP fixture',
   'events':[{'type':'will-download','state':'started','at':100+i*50,'received':0,'total':total},
             {'type':'updated','state':'progressing','at':150+i*50,'received':65536,'total':total},
             {'type':'done','state':'completed','at':200+i*100,'received':size,'total':total}]})
 facts['downloads']={'known':{'first':progress(65536),'second':progress(262144)},
  'unknown':{'concurrent':{'button':{'count':2,'indeterminate':True,'unread':0,'bounce':False},'state':{'items':[{'filename':'mouse633-unknown.bin','received':65536,'total':0}]}}},
  'initial':{'state':{'completedSerial':0,'unreadCount':0},'tasks':[]},
  'completed':{'state':{'completedSerial':2},'button':{'unread':2}},
  'expired':{'state':{'completedSerial':2,'items':[]},'tasks':[],'button':{'unread':2,'badgeHidden':False,'badgeText':'2'}},
  'acknowledged':{'button':{'unread':0}},'cancelled':{'state':{'completedSerial':2},'button':{'unread':0,'bounce':False}},
  'transitions':[{'at':210,'serial':1,'unread':1,'bounce':True,'animationName':'mouse-download-complete-bounce'},
                 {'at':310,'serial':2,'unread':2,'bounce':True,'animationName':'mouse-download-complete-bounce'}],
  'files':downloads,'cancel':{'input':'trusted native IPC library cancel for owned DownloadItem','events':[{'type':'done','state':'cancelled'}]},
  'completedSerialBefore':0,'completedSerialAfter':2,'unreadDuringActive':0,'bounceDuringActive':False,'bounceAfterCompletion':True,
  'unreadAfterCompletion':2,'unreadAfterTaskExpiry':2,'unreadAfterOpening':0,'animationPreference':'CI fixture Emulation prefers-reduced-motion:no-preference'}
 passwords={'available':available,'reason':'' if available else 'Без шифрования хранилище недоступно',
  'backend':('gnome_libsecret' if available else 'basic_text') if platform=='linux' else 'Electron safeStorage / '+('Keychain' if platform=='darwin' else 'DPAPI')}
 if available:
  passwords.update(first={'imported':1,'skipped':1},duplicate={'imported':0,'duplicates':1},conflict={'imported':0,'conflicts':1},
   encryption={'cipherBytes':100,'cipherSha256':'e'*64,'plaintextPasswordPresent':False,'plaintextUsernamePresent':False,'mode':0o600,'readbackMatches':True,'metadata':{'total':1,'items':[{'id':'credential-1','username':'owned-unit-fixture'}]}},
   explicitCopy={'result':{'copied':True,'clearAfterSeconds':30},'clipboardMatched':True,'ownedClipboardCleared':True})
 else:passwords.update(unavailableRejected=True,disabledInSettings=True,ciphertextUnchanged=True,rejection='Нет шифрования')
 opens=['bookmarks.html','bookmarks.html']+(['passwords.csv','passwords.csv','password-conflict.csv'] if available else [])
 facts['imports']={'bookmarks':{'first':{'ok':True,'canceled':False,'imported':2,'duplicates':1,'conflicts':0,'skipped':1,'total':4},
   'duplicate':{'ok':True,'canceled':False,'imported':0,'duplicates':3,'conflicts':0,'skipped':1,'total':4},
   'persistedRows':[{'url':'https://mouse633-00000000.test/','title':'Owned first bookmark'},{'url':'https://mouse633-00000000.test/second','title':'Owned second bookmark'}],'originalTitlePreserved':True},
  'passwords':passwords,'sourceFiles':[{'filename':name,'sha256Before':'f'*64,'sha256After':'f'*64,'unchanged':True} for name in ('bookmarks.html','passwords.csv','password-conflict.csv')],
  'dialogCalls':[{'type':'open','filename':name,'selection':'owned exported fixture'} for name in opens]+([{'type':'confirm','response':1} for _ in range(3)] if available else []),
  'privateGuard':{'nativeModeEntered':True,'disabledInSettings':True,'rejections':[{'action':name,'rejected':True,'message':'Эта функция недоступна в инкогнито','nativeRejected':True,'nativeMessage':'Только в обычном окне'} for name in ('state','bookmarks','passwords','credentials/list','credentials/copy','credentials/remove')],'normalPages':live()}}
 selectors=['#settings-button','#settings-search','#global-zoom-button','#global-zoom-panel [data-zoom="plus"]','#settings-scale',
  '.home-agent-open','.ai-preset-card[data-ai-url="mouse://agent"]','#settings-dialog [data-action="assistant"]','#downloads-button','#settings-import-bookmarks','#private-button',
  '#download-known','#download-unknown','#download-cancel']+['[data-setting="'+key+'"]' for key in E['SETTINGS']]
 for selector in selectors:
  row={'selector':selector,'source':facts['nativeInputSource'],'point':{'x':100,'y':200}}
  if selector=='#private-button':row['navigates']=True
  elif selector.startswith('#download-'):row['events']=[{'id':selector[1:],'isTrusted':True,'at':100}]
  else:row['events']=[{'type':'click','trusted':True,'matches':True,'at':100}]
  facts['nativeInputs'].append(row)
 context=runpy.run_path(str(Path(__file__).with_name('test_mouse633_context_evidence.py')))
 context_files,context_facts=context['fixture'](platform,pages=baseline,pid=facts['pid']);files.update(context_files)
 context_raw=json.dumps(context_facts,allow_nan=False).encode();files['mouse-633-context-menu.json']=context_raw
 facts['contextMenu']={'report':'mouse-633-context-menu.json','sha256':E['digest'](context_raw),'marker':'MOUSE_633_NATIVE_CONTEXT_MENU_PASS'}
 return files,facts


class CurrentOwnerEvidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.original_files,cls.original=fixture()
 def setUp(self):self.files=dict(self.original_files);self.facts=copy.deepcopy(self.original)
 def verify(self,platform='win32',arch='x64'):
  files={**self.files,E['NAME']:json.dumps(self.facts,allow_nan=False).encode()}
  return E['verify'](files.__getitem__,expected_platform=platform,expected_arch=arch)
 def reject(self,message=None):
  with self.assertRaisesRegex(ValueError,message) if message else self.assertRaises(ValueError):self.verify()

 def test_complete_actual_checker_runs_all_three_platform_fixture_branches(self):
  for platform,arch,available in [('darwin','arm64',True),('win32','x64',True),('linux','x64',False),('linux','x64',True)]:
   self.files,self.facts=fixture(platform,available);result=self.verify(platform,arch)
   self.assertEqual(result['guestPixelCaptures'],8);self.assertEqual(len(result['nativeCaptures']),9)
   self.assertEqual(result['imports']['passwordImportAvailable'],available)

 def test_wrong_runtime_scope_failed_cleanup_and_physical_claims_fail(self):
  for key,value in [('version','6.0.32'),('packaged',False),('profileIsolated',False),('restored',False),('elapsedMs',240001),('physicalUserDeviceVerified',True),('liveExternalAccountsVerified',True)]:
   self.setUp();self.facts[key]=value
   with self.subTest(key=key):self.reject()
  self.setUp();self.facts['cleanup']['desktopStateRestored']=False;self.reject('cleanup')

 def test_untrusted_shell_or_guest_input_cannot_claim_native_actions(self):
  self.facts['nativeInputs'][0]['events'][0]['trusted']=False;self.reject('trusted native')
  self.setUp();next(row for row in self.facts['nativeInputs'] if row['selector']=='#download-known')['events'][0]['isTrusted']=False;self.reject('trusted native')

 def test_settings_must_be_a_right_nonmodal_sidebar_preserving_live_pages(self):
  self.facts['settings']['initial']['nonmodal']=False;self.reject('opened Settings')
  self.setUp();self.facts['settings']['initial']['panel']['x']=0;self.reject('right sidebar')
  self.setUp();self.facts['settings']['livePages']['native'][0]['visible']=False;self.reject('visibility')

 def test_search_filters_and_every_toggle_persist_and_restore(self):
  self.facts['settings']['search']['visibleSections']=['agent'];self.reject('filter')
  for key in ('changed','afterReload','restored'):
   self.setUp();self.facts['settings']['toggles'][0][key]=not self.facts['settings']['toggles'][0][key]
   with self.subTest(key=key):self.reject('toggle, persist and restore')

 def test_actual_reload_uses_new_document_time_origin_not_a_new_pid_assumption(self):
  self.verify()
  self.facts['settings']['reload']['after']['timeOrigin']=1000;self.reject('did not reload')

 def test_agent_entries_restore_the_panel_without_enabling_connections(self):
  for key,value in [('enabledAfter',True),('connectionRestored',True),('connectedClients',1),('panelRestoredAfterReload',False),('homeEntry',False)]:
   self.setUp();self.facts['agent'][key]=value
   with self.subTest(key=key):self.reject()

 def test_both_live_zoom_choosers_must_remain_open_with_native_pages_visible(self):
  for kind in ('popover','settings'):
   self.setUp();self.facts['zoom'][kind]['openAfterChange']=False
   with self.subTest(kind=kind):self.reject('preview')
  self.setUp();self.facts['zoom']['settings']['gateBlocked']=True;self.reject('preview')

 def test_native_zoom_factor_roundtrip_tolerance_uses_the_actual_factor(self):
  for row in self.facts['zoom']['popover']['after']['pages']:
   row['factor']=1.1000000000000001
   row['expectedMeter']={'width':128*row['factor'],'height':40*row['factor']}
  self.verify()

 def test_a_reloaded_or_frozen_native_page_cannot_pass_live_preview(self):
  for key,value in [('timeOrigin',999999),('raf',10),('field','lost')]:
   self.setUp();self.facts['zoom']['popover']['livePages']['after'][0][key]=value
   with self.subTest(key=key):self.reject()

 def test_native_zoom_requires_real_larger_guest_pixels_even_after_rehash(self):
  row=self.facts['zoom']['settings']['after']['pages'][0];raw=png(200,300,meter=(24,180,128,40));self.files[row['filename']]=raw;row.update(bytes=len(raw),sha256=E['digest'](raw))
  self.reject('decoded live page meter')

 def test_same_crop_and_display_hashes_do_not_excuse_wrong_pixels_or_dpi(self):
  row=next(row for row in self.facts['captures'] if row['filename']=='mouse-633-settings-light.png');raw=png(800,600,color=(0,0,0,255));self.files[row['filename']]=raw;row.update(bytes=len(raw),sha256=E['digest'](raw));self.reject('crop pixels')
  self.setUp();self.facts['captures'][0]['mapping']['scaleX']=2;self.reject('DPI')

 def test_known_and_unknown_native_download_progress_cannot_be_fabricated(self):
  self.facts['downloads']['known']['first']['button']['percent']=99;self.reject('native bytes')
  self.setUp();self.facts['downloads']['unknown']['concurrent']['state']['items'][0]['total']=999;self.reject('unknown-length')

 def test_completion_bounce_must_follow_real_download_done_and_file_hashes(self):
  self.facts['downloads']['transitions'][0]['at']=1;self.reject('before an actual completion')
  self.setUp();self.facts['downloads']['files'][0]['sha256']='0'*64;self.reject('download bytes')

 def test_expired_tasks_do_not_clear_unread_and_cancel_does_not_count_completed(self):
  self.facts['downloads']['expired']['button']['unread']=0;self.reject('unread')
  self.setUp();self.facts['downloads']['cancelled']['state']['completedSerial']=3;self.reject('cancelled')

 def test_bookmark_dedup_original_titles_and_source_files_are_verified(self):
  self.facts['imports']['bookmarks']['duplicate']['imported']=1;self.reject('dedup')
  self.setUp();self.facts['imports']['sourceFiles'][0]['sha256After']='0'*64;self.reject('export files changed')

 def test_password_plaintext_metadata_or_ciphertext_claims_fail(self):
  for key,value in [('plaintextPasswordPresent',True),('plaintextUsernamePresent',True),('readbackMatches',False)]:
   self.setUp();self.facts['imports']['passwords']['encryption'][key]=value
   with self.subTest(key=key):self.reject('encrypted')
  self.setUp();self.facts['imports']['passwords']['encryption']['metadata']['items'][0]['password']='synthetic-forbidden-secret';self.reject('exposed a secret')

 def test_linux_unavailable_storage_must_fail_closed_without_invented_success(self):
  self.files,self.facts=fixture('linux',False);self.facts['imports']['passwords']['ciphertextUnchanged']=False
  with self.assertRaisesRegex(ValueError,'unavailable'):self.verify('linux','x64')
  self.files,self.facts=fixture('linux',True);self.facts['imports']['passwords']['backend']='basic_text'
  with self.assertRaisesRegex(ValueError,'secure OS backend'):self.verify('linux','x64')

 def test_private_native_and_renderer_routes_both_reject(self):
  for key in ('rejected','nativeRejected'):
   self.setUp();self.facts['imports']['privateGuard']['rejections'][0][key]=False
   with self.subTest(key=key):self.reject('private IPC')

 def test_actual_owner_marker_and_raw_report_budget_are_required(self):
  self.files['mouse-633-owner-feedback.log']=b'no actual success\n';self.reject('success marker')
  with self.assertRaisesRegex(ValueError,'oversized'):E['verify'](lambda name:b' '*(4*1024**2+1))

 def test_native_context_is_mandatory_and_bound_to_the_same_owner_process(self):
  del self.facts['contextMenu'];self.reject('context menu report binding')
  self.setUp();self.facts['contextMenu']['sha256']='f'*64;self.reject('raw report binding')
  self.setUp();context=json.loads(self.files['mouse-633-context-menu.json']);context['pid']+=1
  raw=json.dumps(context).encode();self.files['mouse-633-context-menu.json']=raw;self.facts['contextMenu']['sha256']=E['digest'](raw)
  self.reject('native process/runtime')

 def test_full_composition_runs_owner_and_retained_verifiers_without_mocks(self):
  module=runpy.run_path(str(Path(__file__).with_name('test_mouse633_feedback_evidence.py')))
  files,facts=module['fixtures']();owner_files,owner=fixture();files.update(owner_files)
  for name,value in facts.items():files[name]=json.dumps(value).encode()
  files[E['NAME']]=json.dumps(owner).encode()
  result=module['CURRENT'].verify(files.__getitem__,expected_platform='win32',expected_arch='x64')
  self.assertEqual(result['documents']['unchangedOriginalFiles'],9);self.assertTrue(result['owner']['ok'])
  self.assertTrue(result['owner']['contextMenu']['ok']);self.assertEqual(len(result['inputs']),5)


if __name__=='__main__':unittest.main()
