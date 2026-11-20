#!/usr/bin/env python3
"""Actual per-owner634 download layout, native lifecycle and OS pixel proof."""
import math
from pathlib import Path
import re
import runpy
N=runpy.run_path(str(Path(__file__).with_name('mouse634-native-evidence.py')))
need,near,rect=N['need'],N['near'],N['rect']
TRACK=[83,207,139];FILL=[7,130,60]
ACTIVE=('started','downloading','paused')
STAGES=('before','first-active','both-active','measured-progress','both-other-theme','first-completed','both-completed')


def pane(ui,before,active,owner):
 need(isinstance(ui,dict) and ui.get('placement')=='bottom' and ui.get('topDownloadCount')==0,'download was not moved to its owner bottom')
 slot,base,bounds=rect(ui.get('slot')),rect(before.get('slot')),rect(ui.get('pane'))
 for key in ('x','y','width'): near(slot[key],base[key],'download shifted owning page '+key)
 need(ui.get('pane')==before.get('pane') and ui.get('head')==before.get('head'),'download changed the pane or toolbar')
 footer=ui.get('footer',{});rect(footer.get('bounds'));need(type(footer.get('count')) is int and footer['count']>=0 and type(footer.get('unreadCount')) is int and footer['unreadCount']>=0,'footer counts invalid')
 if active:
  pill=ui.get('pill');need(isinstance(pill,dict) and pill.get('hidden') is False and pill.get('tabId')==owner and ui.get('activeWidgetCount')==1,'active widget belongs to another page or is hidden')
  shape=rect(pill.get('bounds'));rect(ui.get('dock'))
  for actual,expected,label in ((shape['x'],bounds['x'],'full width left'),(shape['width'],bounds['width'],'full width'),(shape['height'],16,'height'),(shape['y']-N['bottom'](slot),6,'gap'),(N['bottom'](shape),N['bottom'](bounds),'pane bottom'),(base['height']-slot['height'],22,'reserved native height')): near(actual,expected,label)
  need(pill.get('text')=='' and pill.get('radius')=='999px' and pill.get('trackColor')=='rgb(83, 207, 139)' and pill.get('fillColor')=='rgb(7, 130, 60)','widget text, green palette or capsule shape differs')
  return shape
 need(ui.get('pill') is None and ui.get('dock') is None and ui.get('activeWidgetCount')==0,'terminal widget remains visible')
 near(slot['height'],base['height'],'terminal viewport was not restored');return None


def current_event(event,phase,expected,case):
 active=phase=='running';ui=event['ui'];before=event.get('before',{});base=before.get('ui',{})
 pane(ui,base,active,event['activity']['tabId'])
 native=event.get('native',{});need(native.get('bounds')==N['endpoints'](ui['slot']),'download native viewport does not follow its real reserved slot')
 baseline=before.get('native',{});need(baseline.get('tabId')==native.get('tabId') and baseline.get('bounds')==N['endpoints'](base['slot']),'pre-download native owner/bounds missing')
 if not active: need(native['bounds']==baseline['bounds'],'terminal native viewport not restored');return
 pill=ui['pill'];need(pill.get('state')==phase and pill.get('tabId')==event['activity']['tabId'] and pill.get('downloadIds')==[event['activity']['id']] and pill.get('count')==1,'rendered download phase or native identity differs')
 if expected is None: need(pill.get('ariaNow') is None and pill.get('value')=='…' and pill.get('indeterminate') is True,'unknown bytes invented a percentage')
 else:
  need(isinstance(pill.get('ariaNow'),str) and re.fullmatch(r'\d+(?:\.\d+)?',pill['ariaNow']) and abs(float(pill['ariaNow'])-expected)<=1e-7 and pill.get('value')==str(math.floor(expected))+'%' and pill.get('indeterminate') is False,'known rendered percentage differs from native bytes')


def download_geometry(ui,native,label):
 # Retained630 screenshot checks use an active widget without a baseline. Every
 # native event additionally passes current_event and its actual before snapshot.
 shape=rect(ui.get('pill',{}).get('bounds'));slot=rect(ui.get('slot'));bounds=rect(ui.get('pane'))
 need(ui.get('placement')=='bottom' and ui.get('topDownloadCount')==0 and ui.get('activeWidgetCount')==1 and ui['pill'].get('hidden') is False and ui['pill'].get('tabId')==native.get('tabId'),label+' active bottom widget missing')
 for a,b in ((shape['x'],bounds['x']),(shape['width'],bounds['width']),(shape['height'],16),(shape['y']-N['bottom'](slot),6),(N['bottom'](shape),N['bottom'](bounds))): near(a,b,label+' bottom geometry')
 need(native.get('bounds')==N['endpoints'](slot),label+' native viewport overlaps widget');rect(ui.get('footer',{}).get('bounds'));return shape


def verify(evidence,value,platform,arch,pid,names,owners,origin):
 filename='mouse-634-'+('ai-' if names==['chat','preview'] else '')+'download-widget.json'
 raw,facts=evidence.json(filename)
 need(value.get('reportFile')==filename and value.get('reportSha256')==N['sha'](raw) and {k:v for k,v in value.items() if k not in ('reportFile','reportSha256')}==facts,'download embedded/raw reports differ')
 need(facts.get('schema')==1 and facts.get('ok') is True and not facts.get('error') and (facts.get('version'),facts.get('platform'),facts.get('arch'),facts.get('pid'))==(N['VERSION'],platform,arch,pid),'download native runtime differs')
 need(facts.get('source')=='Actual DownloadItems, trusted native guest clicks and full OS display pixels' and facts.get('physicalUserDeviceVerified') is False and facts.get('placement')=='bottom' and (facts.get('pillHeight'),facts.get('gap'),facts.get('reservedHeight'))==(16,6,22) and facts.get('palette')=={'track':TRACK,'fill':FILL} and facts.get('pixelTolerance')==12,'download geometry/pixel contract differs')
 tabids=[o['id'] for o in owners];need(facts.get('names')==names and facts.get('tabIds')==tabids and len(set(tabids))==2,'independent originating pages missing')
 inputs=facts.get('nativeInputs',[]);need(len(inputs)==2,'both native downloads need trusted clicks')
 for value,name,owner in zip(inputs,names,owners): N['input_event'](value,platform,'#download-'+name,owner)
 stages=facts.get('stages',[]);need([r.get('name') for r in stages]==list(STAGES),'concurrent lifecycle coverage differs')
 themes={r.get('theme') for r in stages};need(themes=={'light','dark'},'both download themes missing')
 before=stages[0];need(len(before.get('panels',[]))==len(before.get('native',[]))==len(before.get('identities',[]))==2,'both initial native owners missing')
 expected_active=[[],[names[0]],names,names,names,[names[1]],[]]
 for number,(stage,active_names) in enumerate(zip(stages,expected_active)):
  need(stage.get('activeNames')==active_names and stage.get('runningTransitions')==[] and N['finite'](stage.get('at')),'unsettled or differently owned stage')
  need(len(stage.get('panels',[]))==len(stage.get('native',[]))==len(stage.get('identities',[]))==2,'stage lost an owner')
  need(stage['theme']==(next(t for t in themes if t!=before['theme']) if number==4 else before['theme']),'theme was not restored')
  for index,(row,native,ident) in enumerate(zip(stage['panels'],stage['native'],stage['identities'])):
   owner=owners[index];N['identity'](owner,ident);N['native'](native,owner);active=names[index] in active_names
   need(row.get('tabId')==owner['id'],'panel owner differs');pane(row['ui'],before['panels'][index]['ui'],active,owner['id'])
   need(native['bounds']==N['endpoints'](row['ui']['slot']),'actual native viewport misses reserved slot')
   for key in ('x','y','width'): need(native['bounds'][key]==before['native'][index]['bounds'][key],'another native coordinate changed')
   need(native['bounds']['height']==before['native'][index]['bounds']['height']-(22 if active else 0),'native reservation differs')
   if active:
    item=row.get('activity',{});task=row.get('task',{});pill=row['ui']['pill'];expected_received=65536 if number<3 else (262144 if index==0 else 131072)
    need(item.get('tabId')==owner['id'] and item.get('state') in ACTIVE and item.get('received')==expected_received and item.get('total')==524288 and row.get('activeIds')==[item.get('id')],'active native item/counters/URL differ')
    need(task.get('source')==task.get('kind')=='download' and task.get('tabId')==owner['id'] and task.get('taskId')==item['id'] and task.get('phase')=='running' and task.get('estimated') is False and task.get('percent')==expected_received/524288*100,'download task does not follow actual byte counts')
    need(pill.get('downloadIds')==[item['id']] and pill.get('count')==1 and pill.get('state')=='running' and pill.get('downloadState')==item['state'] and pill.get('indeterminate') is False and float(pill.get('ariaNow','nan'))==expected_received/524288*100,'widget meter/native item differs')
   else: need(row.get('activeIds')==[],'terminal/unrelated pane has active download IDs')
  unread=stage.get('activity',{}).get('unreadCount');need(type(unread) is int and unread==facts.get('unreadBefore')+(1 if number==5 else 2 if number==6 else 0),'unread count increments before completion or loses a completed item')
 need(facts.get('unreadAfter')==facts['unreadBefore']+2,'both completed files did not persist unread')
 for old,new in zip(before['identities'],stages[-1]['identities']): need(new['ticks']>old['ticks'],'native pages stopped running throughout transfer')
 files=facts.get('files',[]);need(len(files)==2,'both completed native files required')
 for index,(entry,name,owner) in enumerate(zip(files,names,owners)):
  expected=N['sha'](bytes([65+['a','b','chat','preview'].index(name)])*524288)
  need(entry.get('name')==name and entry.get('url')==origin+'/download/'+name and entry.get('filename')=='mouse634-'+name+'.bin' and entry.get('tabId')==owner['id'] and entry.get('webContentsId')==owner['webContentsId'] and entry.get('id')==stages[2]['panels'][index]['activity']['id'] and entry.get('bytes')==entry.get('expectedBytes')==524288 and entry.get('sha256')==entry.get('expectedSha256')==expected and entry.get('requests')==1 and entry.get('saveDecision')=='DownloadItem.setSavePath only for this owned HTTP fixture','native downloaded bytes/owner or exact single request differ')
  events=entry.get('events',[]);need(3<=len(events)<=2048 and events[0].get('event')=='start' and events[-1].get('event')=='done' and events[-1].get('state')=='completed','actual DownloadItem lifecycle incomplete')
  for event in events: need(event.get('event')==event.get('type') and event['event'] in ('start','updated','done') and event.get('total')==524288 and type(event.get('received')) is int and 0<=event['received']<=524288 and N['finite'](event.get('at')),'invalid DownloadItem observation')
  need(all(a['at']<=b['at'] and a['received']<=b['received'] for a,b in zip(events,events[1:])) and events[-1]['received']==524288,'native bytes/time regress or completion is early')
  need({65536,262144 if index==0 else 131072,524288}<={e['received'] for e in events},'rendered byte milestones did not occur natively')
 groups=facts.get('captures',[]);need(len(groups)==5 and [(g.get('label'),g.get('theme')) for g in groups]==[(label,stages[idx]['theme']) for label,idx in [('first',1),('both',2),('both',4),('first-completed',5),('completed',6)]],'download native screenshot matrix differs')
 total=0
 for group,stage in zip(groups,[stages[i] for i in (1,2,4,5,6)]):
  attempts=group.get('attempts',[]);accepted=group.get('acceptedAttempt');need(type(accepted) is int and 1<=accepted<=4 and len(attempts)==accepted,'bounded native capture attempts differ')
  expected=[]
  for row,native,owner in zip(stage['panels'],stage['native'],owners):
   pill=row['ui']['pill']
   if pill:
    r=pill['bounds'];p=float(pill['ariaNow'])/100
    for kind,x,rgb in [('fill',r['x']+r['width']*p/2,FILL),('track',r['x']+r['width']*(1+p)/2,TRACK)]:
     for dy in (-2,0,2): expected.append((kind,owner['id'],{'x':x,'y':r['y']+8+dy},rgb))
    expected.append(('gap',owner['id'],{'x':r['x']+r['width']/2,'y':r['y']-3},N['LINE'][stage['theme']]))
   for dx,dy in ((0,0),(-4,0),(4,0),(0,-4),(0,4)): expected.append(('native-page',owner['id'],{'x':native['bounds']['x']+.26*native['bounds']['width']+dx,'y':native['bounds']['y']+95+dy},N['color'](owner['index'])))
  badge=group['label'] in ('first-completed','completed')
  if badge:
   b=facts.get('badge',{});need(b.get('hidden') is False and b.get('display')!='none' and b.get('color')=='rgb(7, 130, 60)' and str(b.get('text','')).isdigit() and int(b['text'])>=1,'persistent green unread badge absent');r=rect(b.get('bounds'))
   for dy in (-1,0,1): expected.append(('unread-badge',None,{'x':r['x']+2.5,'y':r['y']+r['height']/2+dy},FILL))
  for number,attempt in enumerate(attempts,1):
   need(attempt.get('attempt')==number and attempt.get('filename')==filename[:-5]+'-'+group['label']+'-'+group['theme']+'-'+str(number)+'.png','capture attempt identity differs')
   image=evidence.screen(attempt);probes=attempt.get('probes',[]);need(len(probes)==len(expected),'actual green widget/gap/live page probes missing');passes=[]
   for probe,(kind,tabid,point,rgb) in zip(probes,expected):
    need(probe.get('kind')==kind and probe.get('tabId')==tabid and probe.get('expectedRGB')==rgb,'pixel ownership or fixed palette differs')
    for key in ('x','y'): near(probe.get('point',{}).get(key),point[key],'pixel point geometry differs',1/32 if kind=='native-page' else 1e-8)
    x,y,rgba=evidence.pixel(image,attempt['mapping'],probe['point']);delta=max(abs(a-b) for a,b in zip(rgba[:3],rgb));passed=delta<=12
    need(probe.get('pixel')=={'x':x,'y':y,'rgba':rgba} and probe.get('maxChannelDelta')==delta and probe.get('pass') is passed,'raw native pixel does not match recorded probe');need(rgba[3]==255,'native download pixel not opaque');passes.append(passed);total+=1
   need(attempt.get('pass') is all(passes) and (all(passes) if number==accepted else not all(passes)),'accepted native frame is stale or incomplete')
 return {'report':filename,'reportSha256':N['sha'](raw),'nativePages':tabids,'stages':7,'captureGroups':5,'decodedProbes':total,'completedFiles':[{'filename':f['filename'],'sha256':f['sha256']} for f in files]}
