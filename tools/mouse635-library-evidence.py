#!/usr/bin/env python3
"""Independent raw DOM, native capture and owned-file stability acceptance."""
import datetime
from pathlib import Path
import re
import runpy

N=runpy.run_path(str(Path(__file__).with_name('mouse635-native-evidence.py')))
need,finite,positive,sha=N['need'],N['finite'],N['positive'],N['sha']
NAME='mouse-635-library.json'
MARKER='MOUSE_635_LIBRARY_STABLE_PASS'


def ordered_ids(value,label):
 need(isinstance(value,list) and 0<len(value)<=1000 and all(isinstance(v,str) and 0<len(v)<=100 for v in value) and len(set(value))==len(value),label)
 return value


def source_image(value):
 need(isinstance(value,str) and 0<len(value)<=2*1024**2 and value.startswith('data:image/'),'loaded image source missing')


def start(row,identifier):
 need(isinstance(row,dict) and row.get('id')==identifier and row.get('selected') is True and row.get('focused') is True,'owned checkbox was not selected and focused')
 need(row.get('kind') in ('downloads','captures') and row.get('view') in ('list','grid') and row.get('theme') in ('light','dark'),'observed library section, view or theme missing')
 need(finite(row.get('scrollTop')) and row['scrollTop']>0 and finite(row.get('rowTop')),'actual scrolled file position missing')
 source_image(row.get('source'));size=row.get('imageSize',{})
 need(positive(size.get('width')) and positive(size.get('height')),'original thumbnail was not decoded')
 need(identifier in ordered_ids(row.get('order'),'original file order missing'),'target absent from its original list')


def stable(before,after,*,source=True,scroll=True,order=True):
 need(isinstance(after,dict) and after.get('id')==before['id'],'sample belongs to another row')
 need(all(after.get(key)==before[key] for key in ('kind','view','theme')),'observed library section, view or theme changed')
 N['flags'](after,('sameRow','sameImage','sameCheckbox','sameFocus','focusedCheckbox','selected'),'file DOM, focus or selection was recreated')
 need(after.get('removed')==0 and type(after.get('sourceWrites')) is int and after['sourceWrites']>=0,'row/image detach or missing mutation count')
 events=after.get('events');need(isinstance(events,list) and len(events)==after['sourceWrites'] and all(isinstance(e,dict) and e.get('type')=='src' and finite(e.get('at')) for e in events),'mutation ledger differs from the source-write count')
 source_image(after.get('source'));ordered_ids(after.get('order'),'updated file order missing')
 need(after['id'] in after['order'] and finite(after.get('scrollTop')) and finite(after.get('rowTop')),'updated viewed file missing')
 if source:
  need(after.get('sameSource') is True and after['source']==before['source'] and after['sourceWrites']==0 and after.get('thumbnail') is True,'unchanged file preview was reset or reloaded')
  need(positive(after.get('imageSize',{}).get('width')) and positive(after.get('imageSize',{}).get('height')),'unchanged thumbnail no longer decodes')
 if scroll: need(abs(after['scrollTop']-before['scrollTop'])<=1,'unchanged list scroll moved')
 need(abs(after['rowTop']-before['rowTop'])<=1,'viewed file moved on screen')
 if order: need(after['order']==before['order'],'unchanged file order shifted')


def verify(read,*,expected_platform=None,expected_arch=None,owner=None):
 evidence=N['Evidence'](read);raw,facts=evidence.json(NAME)
 if owner is None: _,owner=evidence.json('mouse-635-owner-feedback.json')
 platform,arch,pid=facts.get('platform'),facts.get('arch'),facts.get('pid')
 need((platform,arch) in (('darwin','arm64'),('win32','x64'),('linux','x64')) and (expected_platform is None or platform==expected_platform) and (expected_arch is None or arch==expected_arch),'library native platform/architecture differs')
 need(facts.get('schema')==1 and facts.get('version')=='6.0.35' and positive(pid) and owner.get('pid')==pid and owner.get('platform')==platform and owner.get('arch')==arch,'library report belongs to another installed process')
 N['flags'](facts,('ok','completed','restored','packaged','profileIsolated','fixtureOnly'),'library did not finish or restore its isolated packaged profile')
 need(facts.get('realTransfer') is False and facts.get('scenario')=='installed-library-stability' and not facts.get('error') and not facts.get('cleanupErrors'),'library fixture scope overstated or cleanup failed')
 need(owner.get('library')=={**facts,'reportFile':NAME,'reportSha256':sha(raw)},'owner635 library raw bytes/summary differ')
 log=read('mouse-635-owner-feedback.log');need(isinstance(log,bytes) and 0<len(log)<=16*1024**2 and MARKER in log.decode('utf-8').splitlines(),'native library marker missing')
 times=[]
 for key in ('startedAt','finishedAt'):
  text=facts.get(key);need(isinstance(text,str) and text.endswith('Z'),'library UTC timestamp missing');times.append(datetime.datetime.fromisoformat(text.replace('Z','+00:00')).timestamp()*1000)
 need(0<times[1]-times[0]<=240000,'library exceeded the unchanged owner process budget')
 auto=facts.get('autoCollection',{});need(auto.get('before') is False and auto.get('after') is False and type(auto.get('clipboardReadsBefore')) is int and auto['clipboardReadsBefore']>=0 and auto.get('clipboardReadsAfter')==auto['clipboardReadsBefore'],'default collection or clipboard privacy changed')
 owned=facts.get('owned',{});downloads=ordered_ids(owned.get('downloadIds'),'owned downloads missing');copies=ordered_ids(owned.get('captureIds'),'owned copies missing')
 need(len(downloads)==14 and len(copies)==15 and owned.get('activeId') not in downloads and isinstance(owned.get('activeId'),str),'owned fixture identities differ')
 hashes=owned.get('fileHashes');need(isinstance(hashes,list) and len(hashes)==14 and [row.get('id') for row in hashes]==downloads and all(row.get('filename')=='image-'+str(i)+'.png' and re.fullmatch('[0-9a-f]{64}',row.get('sha256','')) for i,row in enumerate(hashes)),'actual initial file byte identities missing')
 phases=facts.get('phases');need(isinstance(phases,list) and len(phases)==8,'both themes, both libraries and both views are mandatory')
 combinations={(theme,kind,view) for theme in ('light','dark') for kind in ('downloads','captures') for view in ('list','grid')}
 need({(p.get('theme'),p.get('kind'),p.get('view')) for p in phases}==combinations,'duplicate or missing native library scene')
 captures=facts.get('captures');need(isinstance(captures,list) and len(captures)==8,'canonical library native frames missing')
 for phase in phases:
  theme,kind,view=(phase[key] for key in ('theme','kind','view'));identifier=downloads[5] if kind=='downloads' else copies[8]
  before=phase.get('before',{});start(before,identifier)
  need((before['theme'],before['kind'],before['view'])==(theme,kind,view),'declared library scene differs from actual renderer state')
  for name in ('after','removed'): stable(before,phase.get(name))
  stable(before,phase.get('inserted'),scroll=kind!='captures',order=kind!='captures')
  need(phase.get('updates')==6 and type(phase.get('backgroundArchivePreviewCalls')) is int and phase['backgroundArchivePreviewCalls']>=0 and type(phase.get('archivePreviewCalls')) is int and phase['archivePreviewCalls']>=phase['backgroundArchivePreviewCalls'],'background update witnesses missing')
  if kind=='downloads': need(phase['after'].get('activeProgress')==15,'real progress node did not receive the final model update')
  else:
   need(phase['backgroundArchivePreviewCalls']==0,'other-kind updates re-decoded capture thumbnails')
   added=set(phase['inserted']['order'])-set(before['order']);need(len(added)==1 and not added.intersection(phase['removed']['order']),'actual added/deleted archive entry did not reconcile')
  capture=phase.get('capture',{});need(capture.get('filename')=='mouse-635-library-'+kind+'-'+view+'-'+theme+'.png' and capture in captures and capture in owner.get('captures',[]),'native phase frame is absent from the owner ledger');evidence.screen(capture)
 need(len(evidence.receipts)==8 and {row.get('filename') for row in captures}==set(evidence.receipts),'duplicate or unbound native library frame')
 files=facts.get('files',{});before=files.get('before',{});start(before,downloads[5]);changed=files.get('changed',{});stable(before,changed,source=False)
 need(changed.get('sameSource') is False and changed['source']!=before['source'] and changed['sourceWrites']==1 and changed.get('thumbnail') is True,'changed actual file did not update the existing thumbnail once')
 before_delete=files.get('beforeDelete',{});start(before_delete,downloads[5]);need(before_delete['source']==changed['source'],'deletion started from another preview');deleted=files.get('deleted',{});stable(before_delete,deleted,source=False)
 need(deleted.get('thumbnail') is False and deleted.get('sameSource') is False and deleted['source']!=before_delete['source'] and files.get('missingOnDisk') is True and files.get('entryRetained') is True and isinstance(files.get('missingOpenError'),str) and 'перемещён или удалён' in files['missingOpenError'],'removed file retained stale pixels or opened as a real file')
 inputs={NAME:sha(raw)}
 for key,suffix in [('originalFile','before'),('replacementFile','after')]:
  row=files.get(key,{});need(row.get('filename')=='mouse-635-library-file-'+suffix+'.png' and row.get('source')=='fs.readFile of owned installed-app fixture' and row.get('pixelSize')=={'width':160,'height':96},'owned before/after file receipt missing');evidence.png(row);inputs[row['filename']]=row['sha256']
 need(files['originalFile']['sha256']==hashes[5]['sha256'] and files['replacementFile']['sha256']==files.get('replacementSha256') and files['originalFile']['sha256']!=files['replacementFile']['sha256'],'replacement bytes do not match the original/replacement receipts')
 previews=facts.get('previews',{});first,latest=previews.get('firstPreview',{}),previews.get('latest',{});source_image(first.get('src'));source_image(latest.get('src'))
 need(first.get('title')=='Mouse635 image 8' and latest.get('title')=='Mouse635 image 7' and latest['src']!=first['src'] and previews.get('realArchiveReads') is True and previews.get('staleClosed')=={'open':False,'kind':'downloads'},'pending, latest-click or closed-section preview ordering failed')
 requests=facts.get('previewRequests');need(isinstance(requests,list) and 3<=len(requests)<=1000 and [row.get('sequence') for row in requests]==list(range(1,len(requests)+1)),'actual archive request ledger missing')
 for row in requests: need(row.get('id') in copies and finite(row.get('startedAt')) and finite(row.get('finishedAt')) and times[0]<=row['startedAt']<=row['finishedAt']<=times[1] and row.get('type')=='image' and not row.get('error'),'archive request did not finish against an owned image')
 held=[row for row in requests if row.get('controlledDelay') is True];need(len(held)==3 and all(row['id']==copies[8] for row in held),'actual deferred archive reads are incomplete')
 notifications=facts.get('notifications');need(isinstance(notifications,list) and len(notifications)==51 and all(finite(row.get('at')) and times[0]<=row['at']<=times[1] for row in notifications),'background model/file notification ledger differs')
 for reason,count in [('other-kind download progress',24),('same-kind download progress',24),('actual owned image bytes replaced',1),('actual owned download file removed',1),('download update while explicit capture preview pending',1)]: need(sum(row.get('reason')==reason for row in notifications)==count,'missing actual notification: '+reason)
 native=owner.get('nativeInputs',[])
 for identifier,count in [(downloads[5],5),(copies[8],4)]:
  selector='.library-row[data-id="'+identifier+'"] .library-check';receipts=[row for row in native if row.get('selector')==selector];need(len(receipts)==count,'native checkbox inputs missing')
  for row in receipts: N['input_event'](row,platform,selector)
 for identifier,count in [(copies[8],3),(copies[7],1)]:
  selector='.library-row[data-id="'+identifier+'"] .library-name';receipts=[row for row in native if row.get('selector')==selector];need(len(receipts)==count,'native explicit preview inputs missing')
  for row in receipts: N['input_event'](row,platform,selector)
 return{'ok':True,'version':'6.0.35','platform':platform,'arch':arch,'pid':pid,'reportSha256':sha(raw),'phases':8,'stableDOM':True,'actualFileReplacement':True,'missingFileHonest':True,'previewOrdering':True,'defaultCollectionOff':True,'inputs':inputs,'nativeCaptures':list(evidence.receipts.values())}
