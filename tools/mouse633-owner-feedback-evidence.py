#!/usr/bin/env python3
"""Independent current633 settings, Agent, live zoom, imports and native menus."""
import hashlib
import json
import math
from pathlib import Path
import re
import runpy

VERSION='6.0.33'
NAME='mouse-633-owner-feedback.json'
SETTINGS=('restoreAgent','showBrandName','showFavicons','desktopGestures','downloadBounce','downloadBadge')
SECTIONS=['appearance','workspace','agent','imports','privacy','capture','downloads','documents','updates','about']
IDENTITY=('id','index','desk','webContentsId','url','navigationEpoch','identity','timeOrigin','field','cookie')
SOURCE='Installed app, native pointer input, owned local HTTP/download/export fixtures'
_tasks=runpy.run_path(str(Path(__file__).with_name('mouse633-task-evidence.py')))
_reuse=runpy.run_path(str(Path(__file__).with_name('mouse633-reuse.py')))
_geometry=_reuse['load']('mouse632-feedback-evidence.py')


def need(value,message):
 if not value:raise ValueError('Mouse633 owner evidence: '+message)


def finite(value):return type(value) in (int,float) and math.isfinite(value)
def positive(value):return type(value) is int and value>0
def digest(raw):return hashlib.sha256(raw).hexdigest()
def hash_value(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value)
def flags(value,keys,label):need(isinstance(value,dict) and all(value.get(key) is True for key in keys),label+' incomplete')
def rect(value,label):return _tasks['rectangle'](value,label)


def reload(value):
 need(isinstance(value,dict),'actual shell reload missing')
 before,after=value.get('before',{}),value.get('after',{})
 need(all(positive(row.get('processId')) and positive(row.get('routingId')) and finite(row.get('timeOrigin')) and row['timeOrigin']>0
          for row in (before,after)) and after['timeOrigin']>before['timeOrigin'],'real renderer document did not reload')


def live(value,baseline,origin,*,scroll=False):
 need(isinstance(value,dict),'live page witness missing')
 before,after=value.get('before'),value.get('after')
 need(isinstance(before,list) and isinstance(after,list) and len(before)==len(after)==2 and
      {row.get('id') for row in before}=={row.get('id') for row in baseline},'both original live pages are required')
 for old,new in zip(before,after):
  initial=next(row for row in baseline if row['id']==old['id'])
  need(all(key in old and key in new and old[key]==new[key]==initial[key] for key in IDENTITY),
       'a live page reloaded, moved or lost its form/cookie identity')
  need(old.get('url')==origin+'/page/'+str(old.get('index'))+'/' and old.get('index') in (0,1) and
       positive(old.get('webContentsId')) and finite(old.get('timeOrigin')) and old['timeOrigin']>0,
       'live page is not the owned native HTTP fixture')
  need(old.get('field')=='preserved-'+str(old['index'])+'-данные' and
       'mouse631_'+str(old['index'])+'='+old['identity'] in old.get('cookie',''),'owned page state is missing')
  need(all(type(row.get('raf')) is int and type(row.get('ticks')) is int and row['raf']>=0 and row['ticks']>=0 for row in (old,new))
       and new['raf']>old['raf'] and new['ticks']>=old['ticks'],'native page stopped animating or its timer restarted')
  if scroll:need(all(new.get(key)==old.get(key) for key in ('scrollX','scrollY')),'settings moved page scroll')
 _geometry['native_views'](value.get('native'),after)
 return value['native']


def raw_png(read,row):
 name=row.get('filename')
 need(isinstance(name,str) and re.fullmatch(r'mouse-633-[a-z0-9-]+\.png',name),'unsafe capture name')
 raw=read(name)
 need(isinstance(raw,bytes) and 0<len(raw)<=16*1024**2 and len(raw)==row.get('bytes') and digest(raw)==row.get('sha256'),
      'capture size/hash differs: '+name)
 image=_tasks['decode_png'](raw,name)
 need(row.get('pixelSize')=={'width':image['width'],'height':image['height']},'PNG dimensions differ: '+name)
 return image


def screen_capture(read,row):
 image=raw_png(read,row)
 need(row.get('source')=='globalCapture.acquire(display)' and isinstance(row.get('backend'),str) and row['backend'],
      'shell capture is not an actual OS display')
 name=row['filename']
 need(row.get('displayFilename')==name[:-4]+'-display.png','full OS display capture missing')
 raw=read(row['displayFilename'])
 need(isinstance(raw,bytes) and 0<len(raw)<=16*1024**2 and digest(raw)==row.get('displaySha256'),'full display PNG hash differs')
 full=_tasks['decode_png'](raw,row['displayFilename'])
 need(row.get('screenPixelSize')=={'width':full['width'],'height':full['height']},'full display dimensions differ')
 bounds=rect(row.get('display',{}).get('bounds'),'display');content=rect(row.get('contentBounds'),'window')
 sx,sy=full['width']/bounds['width'],full['height']/bounds['height']
 left,top=(content['x']-bounds['x'])*sx,(content['y']-bounds['y'])*sy
 crop={'x':math.floor(left),'y':math.floor(top),'width':math.ceil(left+content['width']*sx)-math.floor(left),
       'height':math.ceil(top+content['height']*sy)-math.floor(top)}
 need(row.get('cropPixels')==crop and (image['width'],image['height'])==(crop['width'],crop['height']),
      'OS crop does not follow the actual window')
 mapping={'scaleX':sx,'scaleY':sy,'originX':left-crop['x'],'originY':top-crop['y']}
 need(all(finite(row.get('mapping',{}).get(key)) and abs(row['mapping'][key]-value)<1e-8 for key,value in mapping.items()),
      'OS display DPI mapping differs')
 need(crop['x']>=0 and crop['y']>=0 and crop['x']+crop['width']<=full['width'] and crop['y']+crop['height']<=full['height'],
      'captured window is outside its display')
 need(image['channels']==full['channels'],'crop PNG channel representation differs')
 channels=image['channels']
 for y in range(crop['height']):
  offset=((y+crop['y'])*full['width']+crop['x'])*channels
  need(image['pixels'][y*image['width']*channels:(y+1)*image['width']*channels]==full['pixels'][offset:offset+image['width']*channels],
       'window crop pixels differ from the archived display')
 return {'filename':name,'sha256':row['sha256'],'displaySha256':row['displaySha256']}


def meter(image):
 width,height,channels=image['width'],image['height'],image['channels'];pixels=image['pixels'];xs=[];ys=[];count=0
 left,top,right,bottom=width,height,-1,-1
 for y in range(height):
  for x in range(width):
   at=(y*width+x)*channels
   if (channels==4 and pixels[at+3]<250) or any(abs(pixels[at+i]-value)>2 for i,value in enumerate((235,40,155))):continue
   left=min(left,x);right=max(right,x);top=min(top,y);bottom=max(bottom,y);count+=1
 return {'x':left,'y':top,'width':right-left+1,'height':bottom-top+1,'count':count} if count else None


def guest_capture(read,row,owner,factor):
 image=raw_png(read,row)
 need(row.get('source')=='WebContents.capturePage; excludes shell controls' and finite(row.get('factor')) and abs(row['factor']-factor)<1e-8,
      'actual native guest zoom differs')
 bounds=rect(row.get('rect'),'guest capture')
 need(bounds['x']==bounds['y']==0 and bounds['width']<=420 and bounds['height']<=360,'guest capture rectangle differs')
 sx,sy=image['width']/bounds['width'],image['height']/bounds['height']
 need(finite(row.get('scaleX')) and finite(row.get('scaleY')) and abs(row['scaleX']-sx)<1e-8 and abs(row['scaleY']-sy)<1e-8,
      'guest capture DPI differs')
 actual=meter(image);expected={'width':128*row['factor']*sx,'height':40*row['factor']*sy}
 need(actual is not None and row.get('meter')==actual and row.get('expectedMeter')==expected and
      abs(actual['width']-expected['width'])<=3 and abs(actual['height']-expected['height'])<=3 and
      actual['count']>=(actual['width']-2)*(actual['height']-2), 'decoded live page meter does not match WebContents zoom')
 identity=row.get('identity',{})
 need(all(identity.get(key)==owner[key] for key in IDENTITY),'guest screenshot belongs to another page')
 _geometry['native_views']([row.get('native')],[identity])
 native=row['native']['bounds']
 need(bounds['width']==min(420,native['width']) and bounds['height']==min(360,native['height']), 'guest capture was not taken from its actual native pane')
 return actual


def settings_contract(facts,baseline,origin):
 value=facts.get('settings',{});flags(value,('rightmostGear','nonmodal'),'Settings sidebar')
 initial=value.get('initial',{})
 flags(initial,('open','nonmodal','inWorkspace','rightmostGear'),'opened Settings')
 need(initial.get('gearCount')==1 and initial.get('gearExpanded')=='true' and value.get('sections')==SECTIONS and
      [row.get('name') for row in initial.get('sections',[])]==SECTIONS and
      all(row.get('hidden') is False for row in initial['sections']),'Settings sections or unique gear differ')
 panel,workspace=rect(initial.get('panel'),'sidebar'),rect(initial.get('workspace'),'workspace')
 need(abs(panel['x']+panel['width']-workspace['x']-workspace['width'])<=2,'Settings is not the right sidebar')
 native=live(value.get('livePages'),baseline,origin,scroll=True)
 need(all(row['bounds']['x']+row['bounds']['width']<=panel['x']+2 for row in native),'Settings covers native pages')
 live(value.get('liveAfterReload'),baseline,origin,scroll=True);reload(value.get('reload'))
 search=value.get('search',{})
 need(search.get('query')=='Загрузки' and search.get('visibleSections')==['downloads'] and
      [row.get('name') for row in search.get('readback',{}).get('sections',[]) if row.get('hidden') is False]==['downloads'],
      'Settings search did not filter its actual sections')
 events=search.get('input',{}).get('events',[])
 need(any(row.get('trusted') is True and row.get('matches') is True and row.get('type') in ('input','keydown') for row in events),
      'Settings search lacks real focused keyboard input')
 toggles=value.get('toggles',[])
 need(len(toggles)==len(SETTINGS) and {row.get('key') for row in toggles}==set(SETTINGS),'Settings toggles missing')
 current={row.get('key'):row for row in value.get('afterReload',{}).get('toggles',[])}
 for row in toggles:
  key=row['key'];need(type(row.get('before')) is bool and row.get('changed') is (not row['before']) and
       row.get('afterReload') is row['changed'] and row.get('restored') is row['before'] and
       value.get('persisted',{}).get(key) is row['changed'] and current.get(key,{}).get('checked') is row['changed'],
       'actual setting did not toggle, persist and restore: '+key)
 return {'sections':SECTIONS,'toggles':list(SETTINGS),'nonmodal':True}


def agent_contract(facts):
 value=facts.get('agent',{});flags(value,('homeEntry','presetEntry','settingsEntry','closedAndReopened','panelRestoredAfterReload'),'Agent entry/restoration')
 need(value.get('openingSources')==['home','ai-preset','settings'] and value.get('enabledBefore') is False and
      value.get('enabledAfter') is False and value.get('connectionRestored') is False and value.get('connectedClients')==0,
      'Agent UI restoration enabled or connected the backend')
 for key in ('modelEntry','permissionsEntry','ollamaEntry'):flags(value.get(key),('open','visible'),key)
 onboarding=value.get('onboarding',{});flags(onboarding,('downloadButton','checkButton'),'Ollama onboarding')
 need(onboarding.get('title')=='Агент Маус' and onboarding.get('officialDownloadURL')=='https://ollama.com/download','Agent onboarding identity differs')
 reload(value.get('reload'));return {'restored':True,'backendEnabled':False,'openingSources':value['openingSources']}


def zoom_contract(read,facts,baseline,origin,captures):
 result={}
 for kind,factor in [('popover',1.1),('settings',1.2)]:
  value=facts.get('zoom',{}).get(kind,{})
  need(value.get('openAfterChange') is True and value.get('gateBlocked') is False and
       value.get('factorBefore')==1 and value.get('factorAfter')==factor,'zoom chooser hides live pages or closes before preview')
  live(value.get('livePages'),baseline,origin)
  phases={}
  for phase,expected in [('before',1),('after',factor)]:
   data=value.get(phase,{})
   shell='mouse-633-zoom-'+kind+'-'+phase+'.png'
   need(data.get('shell')==shell and shell in captures,'zoom preview shell capture missing')
   pages=data.get('pages',[])
   need(len(pages)==2 and {row.get('identity',{}).get('id') for row in pages}=={row['id'] for row in baseline},'both actual zoomed pages required')
   phases[phase]={}
   for row in pages:
    owner=next(item for item in baseline if item['id']==row['identity']['id']);name='mouse-633-zoom-'+kind+'-'+phase+'-guest-'+str(owner['index'])+'.png'
    need(row.get('filename')==name and captures.get(name)==row,'zoom capture is not bound to the top-level native frame')
    phases[phase][owner['id']]={'meter':guest_capture(read,row,owner,expected),'native':row['native']}
  for page in baseline:
   before,after=phases['before'][page['id']],phases['after'][page['id']]
   need(before['native']==after['native'],'native pane geometry changed while changing zoom')
   need(after['meter']['width']>before['meter']['width'] and after['meter']['height']>before['meter']['height'],'actual page pixels did not enlarge')
  if kind=='settings':
   need(value.get('inputSource')=='native focused range; webContents.sendInputEvent Home then 19 ArrowRight' and
        value.get('readback',{}).get('open') is True and str(value['readback'].get('value'))=='120' and value['readback'].get('output')=='120%',
        'Settings range does not show the applied live value')
  result[kind]={'factor':factor,'livePages':2,'nativeGuestPixels':True}
 return result


def download_contract(facts,baseline):
 value=facts.get('downloads',{});need(value.get('completedSerialBefore')==0 and value.get('completedSerialAfter')==2 and
      value.get('unreadDuringActive')==0 and value.get('bounceDuringActive') is False and value.get('bounceAfterCompletion') is True and
      value.get('unreadAfterCompletion')==value.get('unreadAfterTaskExpiry')==2 and value.get('unreadAfterOpening')==0,
      'download completion/unread semantics differ')
 need(value.get('animationPreference')=='CI fixture Emulation prefers-reduced-motion:no-preference','animation fixture scope differs')
 initial=value.get('initial',{});need(initial.get('state',{}).get('completedSerial')==initial.get('state',{}).get('unreadCount')==0 and initial.get('tasks')==[], 'downloads were not initially clean')
 first,second=value.get('known',{}).get('first',{}),value.get('known',{}).get('second',{})
 progress=[]
 for row in (first,second):
  button=row.get('button',{});items=[item for item in row.get('state',{}).get('items',[]) if item.get('filename')=='mouse633-known.bin']
  need(len(items)==1 and items[0].get('total')==524288 and finite(items[0].get('received')) and 0<items[0]['received']<524288,
       'actual known-length byte progress missing')
  percent=100*items[0]['received']/524288
  need(button.get('count')==1 and button.get('indeterminate') is False and button.get('bounce') is False and button.get('unread')==0 and
       button.get('ringDisplay') not in (None,'none') and finite(button.get('percent')) and abs(button['percent']-percent)<.01,
       'visible progress ring does not match native bytes')
  progress.append(percent)
 need(progress[1]>progress[0] and progress[1]>=50,'native known download progress did not advance')
 concurrent=value.get('unknown',{}).get('concurrent',{});button=concurrent.get('button',{})
 need(button.get('count')==2 and button.get('indeterminate') is True and button.get('unread')==0 and button.get('bounce') is False and
      any(item.get('filename')=='mouse633-unknown.bin' and item.get('received',0)>0 and item.get('total')==0 for item in concurrent.get('state',{}).get('items',[])),
      'unknown-length native transfer was fabricated as a percentage')
 files=value.get('files',[]);need(len(files)==2 and {row.get('name') for row in files}=={'known','unknown'},'both completed file witnesses required')
 done=[]
 for row in files:
  known=row['name']=='known';size=524288 if known else 393216;expected=digest((b'A' if known else b'B')*size)
  need(row.get('filename')=='mouse633-'+row['name']+'.bin' and row.get('bytes')==size and row.get('sha256')==row.get('expectedSha256')==expected and
       row.get('webContentsId')==baseline[0 if known else 1]['webContentsId'] and
       row.get('saveDecision')=='DownloadItem.setSavePath restricted to the owned HTTP fixture','saved native download bytes/owner differ')
  events=row.get('events',[]);need(events and events[0].get('type')=='will-download' and
       len([event for event in events if event.get('type')=='done'])==1 and events[-1].get('type')=='done' and
       events[-1].get('state')=='completed' and events[-1].get('received')==size,'DownloadItem completion lifecycle missing')
  need(any(event.get('type')=='updated' and event.get('received',0)>0 for event in events),'native updated-byte events absent')
  for index,event in enumerate(events):
   need(finite(event.get('at')) and finite(event.get('received')) and 0<=event['received']<=size and event.get('total') in (0,size), 'invalid native transfer measurements')
   if index:need(event['at']>=events[index-1]['at'] and event['received']>=events[index-1]['received'],'native transfer chronology reversed')
  done.append(events[-1]['at'])
 transitions=value.get('transitions',[]);need(isinstance(transitions,list) and 0<len(transitions)<=600,'download animation observations missing')
 bounces=[row for row in transitions if row.get('bounce') is True]
 need(bounces and all(row.get('serial') in (1,2) and row.get('unread') in (1,2) and finite(row.get('at')) and min(done)<=row['at'] for row in bounces),
      'download bounced before an actual completion')
 need(any(row.get('animationName')=='mouse-download-complete-bounce' or any(animation.get('name')=='mouse-download-complete-bounce'
      for animation in row.get('animations',[])) for row in bounces),'actual CSS completion animation missing')
 for key in ('completed','expired'):
  state=value.get(key,{});need(state.get('state',{}).get('completedSerial')==2 and state.get('button',{}).get('unread')==2,'unread files vanished before opening downloads')
 expired=value['expired'];need(expired.get('tasks')==[] and expired.get('state',{}).get('items')==[] and
      expired['button'].get('badgeHidden') is False and expired['button'].get('badgeText')=='2','task expiry erased unread completion badge')
 need(value.get('acknowledged',{}).get('button',{}).get('unread')==0,'opening Downloads did not acknowledge unread files')
 cancelled=value.get('cancelled',{});need(cancelled.get('state',{}).get('completedSerial')==2 and cancelled.get('button',{}).get('unread')==0 and
      cancelled.get('button',{}).get('bounce') is False,'cancelled transfer counted as a new completed file')
 need(value.get('cancel',{}).get('input')=='trusted native IPC library cancel for owned DownloadItem' and
      any(event.get('type')=='done' and event.get('state')=='cancelled' for event in value['cancel'].get('events',[])), 'actual cancellation missing')
 return {'completedFiles':2,'knownByteProgress':True,'unknownIndeterminate':True,'unreadUntilOpened':True,'completionBounce':True}


def imports_contract(facts,baseline,origin,platform):
 value=facts.get('imports',{});bookmarks=value.get('bookmarks',{})
 need(bookmarks.get('first')=={'ok':True,'canceled':False,'imported':2,'duplicates':1,'conflicts':0,'skipped':1,'total':4} and
      bookmarks.get('duplicate')=={'ok':True,'canceled':False,'imported':0,'duplicates':3,'conflicts':0,'skipped':1,'total':4}, 'bookmark parser/dedup results differ')
 rows=bookmarks.get('persistedRows',[])
 need(len(rows)==2 and len({row.get('url') for row in rows})==2 and
      {row.get('title') for row in rows}=={'Owned first bookmark','Owned second bookmark'} and
      all(isinstance(row.get('url'),str) and re.fullmatch(r'https://mouse633-[0-9a-f-]+\.test/(?:second)?',row['url']) for row in rows) and
      bookmarks.get('originalTitlePreserved') is True,'actual persisted imported bookmarks differ')
 sources=value.get('sourceFiles',[])
 need(len(sources)==3 and {row.get('filename') for row in sources}=={'bookmarks.html','passwords.csv','password-conflict.csv'} and
      all(row.get('unchanged') is True and hash_value(row.get('sha256Before')) and row['sha256Before']==row.get('sha256After') for row in sources), 'selected export files changed')
 passwords=value.get('passwords',{});need(type(passwords.get('available')) is bool and isinstance(passwords.get('backend'),str),'OS credential storage scope missing')
 if passwords['available']:
  need(passwords.get('reason')=='' and (platform!='linux' or passwords['backend'] in ('gnome_libsecret','kwallet','kwallet5','kwallet6')),
       'password storage claims encryption without a secure OS backend')
  for key,expected in [('first',{'imported':1,'skipped':1}),('duplicate',{'imported':0,'duplicates':1}),('conflict',{'imported':0,'conflicts':1})]:
   need(all(passwords.get(key,{}).get(field)==number for field,number in expected.items()),'password import '+key+' differs')
  encryption=passwords.get('encryption',{})
  need(positive(encryption.get('cipherBytes')) and hash_value(encryption.get('cipherSha256')) and
       encryption.get('plaintextPasswordPresent') is False and encryption.get('plaintextUsernamePresent') is False and
       encryption.get('readbackMatches') is True and (platform=='win32' or encryption.get('mode')==0o600),'actual encrypted credential storage failed')
  metadata=encryption.get('metadata',{})
  need(metadata.get('total')==1 and len(metadata.get('items',[]))==1 and all('password' not in row for row in metadata['items']), 'credential metadata exposed a secret')
  copied=passwords.get('explicitCopy',{});need(copied.get('result')=={'copied':True,'clearAfterSeconds':30} and copied.get('clipboardMatched') is True and
       copied.get('ownedClipboardCleared') is True,'explicit password copy/owned clipboard cleanup missing')
 else:
  flags(passwords,('unavailableRejected','disabledInSettings','ciphertextUnchanged'),'unavailable OS storage')
  need(isinstance(passwords.get('reason'),str) and passwords['reason'] and isinstance(passwords.get('rejection'),str) and
       re.search('шифрования|хранилище|расшифровать',passwords['rejection']),'unavailable storage must fail closed with its real reason')
  need(not any(key in passwords for key in ('encryption','explicitCopy','first','duplicate','conflict')),'unavailable storage claims a successful password import')
 dialogs=value.get('dialogCalls',[])
 opens=[row for row in dialogs if row.get('type')=='open'];confirms=[row for row in dialogs if row.get('type')=='confirm']
 need(len(opens)==(5 if passwords['available'] else 2) and all(row.get('selection')=='owned exported fixture' and row.get('filename') in
      ('bookmarks.html','passwords.csv','password-conflict.csv') for row in opens) and len(confirms)==(3 if passwords['available'] else 0) and all(row.get('response')==1 for row in confirms),'native selected-file/confirmation path missing')
 private=value.get('privateGuard',{});flags(private,('nativeModeEntered','disabledInSettings'),'private import guard')
 rejections=private.get('rejections',[])
 need(len(rejections)==6 and {row.get('action') for row in rejections}=={'state','bookmarks','passwords','credentials/list','credentials/copy','credentials/remove'} and
      all(row.get('rejected') is True and isinstance(row.get('message'),str) and re.search('обычном окне|отменено|инкогнито',row['message']) and row.get('nativeRejected') is True and
          isinstance(row.get('nativeMessage'),str) and re.search('обычном окне|отменено|инкогнито',row['nativeMessage']) for row in rejections),'private IPC imports or credential access were accepted')
 live(private.get('normalPages'),baseline,origin)
 return {'persistedBookmarks':2,'sourceFilesUnchanged':3,'privateRoutesRejected':6,'passwordImportAvailable':passwords['available'],
         'unavailableReason':passwords.get('reason') if not passwords['available'] else None}


def verify(read, *, expected_platform=None, expected_arch=None):
 raw=read(NAME);need(isinstance(raw,bytes) and 0<len(raw)<=4*1024**2,'missing or oversized owner report')
 facts=json.loads(raw);need(isinstance(facts,dict),'owner report must be an object')
 platform,arch=facts.get('platform'),facts.get('arch')
 need(facts.get('schema')==1 and facts.get('version')==VERSION and (platform,arch) in (('darwin','arm64'),('win32','x64'),('linux','x64')) and
      (expected_platform is None or platform==expected_platform) and (expected_arch is None or arch==expected_arch),'wrong current runtime or target')
 flags(facts,('ok','restored','packaged','profileIsolated'),'installed owner scope')
 need(not facts.get('error') and not facts.get('cleanupError') and facts.get('stage')=='complete' and positive(facts.get('pid')) and
      facts.get('budgetMs')==240000 and finite(facts.get('elapsedMs')) and 0<facts['elapsedMs']<=240000 and
      facts.get('physicalUserDeviceVerified') is False and facts.get('liveExternalAccountsVerified') is False and facts.get('source')==SOURCE,
      'owner process failed, exceeded budget or overstated physical scope')
 flags(facts.get('cleanup'),('restored','desktopStateRestored'),'owner cleanup')
 origin=facts.get('fixtureOrigin');need(isinstance(origin,str) and re.fullmatch(r'http://127\.0\.0\.1:\d+',origin),'fixture must be owned loopback HTTP')
 requests=facts.get('pageRequests',[]);need(len(requests)==2 and {row.get('index') for row in requests}=={0,1},'settings or private transition reloaded an owned page')
 baseline=facts.get('settings',{}).get('livePages',{}).get('before',[])
 need(len(baseline)==2 and {row.get('index') for row in baseline}=={0,1},'initial native page pair missing')
 expected_source={'darwin':'CGEvent','win32':'User32','linux':'XTest'}[platform]
 need(facts.get('nativeInputSource')==expected_source,'native input backend differs')
 inputs=facts.get('nativeInputs',[]);need(isinstance(inputs,list) and 16<=len(inputs)<=300,'native interaction witnesses missing')
 for row in inputs:
  need(row.get('source')==expected_source and isinstance(row.get('selector'),str) and
       all(finite(row.get('point',{}).get(key)) for key in ('x','y')),'native pointer source/point missing')
  if row.get('navigates') is True:
   need(row['selector']=='#private-button','unsupported navigation without a trusted input witness')
  elif row['selector'].startswith('#download-'):
   need(any(event.get('id')==row['selector'][1:] and event.get('isTrusted') is True for event in row.get('events',[])), 'guest download lacked trusted native input')
  else:
   need(any(event.get('type')=='click' and event.get('trusted') is True and event.get('matches') is True for event in row.get('events',[])), 'shell control lacked trusted native input')
 required={'#settings-button','#settings-search','#global-zoom-button','#global-zoom-panel [data-zoom="plus"]','#settings-scale',
           '.home-agent-open','.ai-preset-card[data-ai-url="mouse://agent"]','#settings-dialog [data-action="assistant"]',
           '#downloads-button','#settings-import-bookmarks','#private-button','#download-known','#download-unknown','#download-cancel'}
 need(required<={row['selector'] for row in inputs},'one or more requested native control routes were skipped')
 rows=facts.get('captures',[]);need(isinstance(rows,list) and len(rows)==17 and len({row.get('filename') for row in rows})==17,'all current native captures are required')
 captures={row['filename']:row for row in rows};shell_names={'mouse-633-settings-'+theme+'.png' for theme in ('light','dark')}|{'mouse-633-agent-onboarding.png','mouse-633-download-active.png','mouse-633-download-completed.png'}
 shell_names|={'mouse-633-zoom-'+kind+'-'+phase+'.png' for kind in ('popover','settings') for phase in ('before','after')}
 guest_names={'mouse-633-zoom-'+kind+'-'+phase+'-guest-'+str(i)+'.png' for kind in ('popover','settings') for phase in ('before','after') for i in (0,1)}
 need(set(captures)==shell_names|guest_names,'native capture names/scenes differ')
 checked=[screen_capture(read,captures[name]) for name in sorted(shell_names)]
 settings=settings_contract(facts,baseline,origin);agent=agent_contract(facts)
 zoom=zoom_contract(read,facts,baseline,origin,captures);downloads=download_contract(facts,baseline)
 imports=imports_contract(facts,baseline,origin,platform)
 need(isinstance(facts.get('contextMenu'),dict),'native context menu report binding missing')
 context=runpy.run_path(str(Path(__file__).with_name('mouse633-context-evidence.py')))['verify'](
  read,expected_platform=platform,expected_arch=arch,expected_pid=facts['pid'],expected_pages=baseline,binding=facts['contextMenu'])
 log=read('mouse-633-owner-feedback.log')
 need(isinstance(log,bytes) and 0<len(log)<=32*1024**2 and 'MOUSE_633_OWNER_FEEDBACK_PASS' in log.decode('utf-8').splitlines(),'actual owner process success marker missing')
 return {'ok':True,'version':VERSION,'platform':platform,'arch':arch,'reportSha256':digest(raw),'logSha256':digest(log),
         'settings':settings,'agent':agent,'zoom':zoom,'downloads':downloads,'imports':imports,'contextMenu':context,'nativeCaptures':checked,'guestPixelCaptures':8,
         'physicalUserDeviceVerified':False,'liveExternalAccountsVerified':False}
