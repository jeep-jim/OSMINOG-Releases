#!/usr/bin/env python3
"""Recompute634 composed screenshot and before/after native corner pixels."""
from pathlib import Path
import math
import re
import runpy
N=runpy.run_path(str(Path(__file__).with_name('mouse634-native-evidence.py')))
need,near,rect=N['need'],N['near'],N['rect']


def rgb(value):
 if isinstance(value,str) and re.fullmatch(r'#[0-9a-fA-F]{6}',value): return [int(value[i:i+2],16) for i in (1,3,5)]
 match=re.fullmatch(r'rgb\((\d+), (\d+), (\d+)\)',str(value));need(match is not None,'opaque actual theme color missing');return list(map(int,match.groups()))


def geometry(value,native,targets,theme):
 need(value.get('theme')==theme and value.get('padding')=={'top':6,'right':0,'bottom':6,'left':0} and value.get('focusPane')=='' and value.get('focusAI') is False,'capture fixture is not the regular workspace')
 workspace=rect(value.get('workspace'));near(workspace['x'],0,'left outer gutter');near(N['right'](workspace),value.get('viewport',{}).get('width'),'right outer gutter',1/16)
 need(rgb(value.get('line'))==N['LINE'][theme] and rgb(value.get('panel'))==N['PANEL'][theme],'corner palette differs from fixed theme palette')
 rows=value.get('targets',[]);need(len(rows)==len(native)==len(targets)==4 and len({r.get('id') for r in native})==4,'four actual main/chat/preview owners required')
 for target,row in zip(targets,rows):
  need(all(row.get(key)==v for key,v in target.items()) and row.get('hidden') is False and row.get('paneRadii')==[12]*4,'DOM capture target/radius differs')
  pane,slot=rect(row.get('pane')),rect(row.get('slot'));page=next((p for p in native if p.get('id')==target['id']),{})
  N['flags'](page,('visible','viewVisible','parentVisible','attached'),'captured native page hidden/detached')
  need(N['positive'](page.get('webContentsId')) and page.get('bounds')==page.get('actualBounds')==page.get('clip')==N['endpoints'](slot) and page.get('roundBottom')==12,'actual clipped/native capture geometry differs')
  need(page['bounds']['width']>24 and page['bounds']['height']>24 and pane['y']<slot['y'] and pane['y']>=workspace['y']+6-1/16,'pane content lies outside regular workspace')
 chat,preview=rows[2:];near(preview['pane']['y']-N['bottom'](chat['pane']),6,'chat/preview split gap',1/16);near(chat['pane']['x'],preview['pane']['x'],'chat/preview x',1/16);near(N['right'](preview['pane']),value['viewport']['width'],'AI right outer gutter',1/16)
 return rows


def points(value,native):
 result=[];line=N['LINE'][value['theme']];panel=N['PANEL'][value['theme']];workspace=value['workspace']
 def add(kind,x,y,color,**extra): result.append({'kind':kind,**extra,'cssPoint':{'x':x,'y':y},'expectedRGB':color})
 for edge in ('top','bottom'):
  for fraction in (.2,.5,.8): add('workspace-gap',workspace['x']+workspace['width']*fraction,workspace['y']+3 if edge=='top' else N['bottom'](workspace)-3,line,edge=edge)
 for target in value['targets']:
  pane=target['pane'];box=next(p for p in native if p['id']==target['id'])['clip']
  for side in ('left','right'):
   for u in (.65,1.6):
    for v in (.65,1.6):
     add('pane-top-cutout',pane['x']+u if side=='left' else N['right'](pane)-u,pane['y']+v,line,id=target['id'],side=side)
     add('page-bottom-cutout',box['x']+u if side=='left' else N['right'](box)-u,N['bottom'](box)-v,line,id=target['id'],side=side)
   add('pane-top-interior',math.ceil(pane['x']+12)+.5 if side=='left' else math.floor(N['right'](pane)-12)-.5,math.ceil(pane['y'])+.5,panel,id=target['id'],side=side)
   add('page-bottom-interior',box['x']+15.5 if side=='left' else N['right'](box)-15.5,N['bottom'](box)-3.5,target['backgroundRGB'],id=target['id'],side=side)
 chat,preview=value['targets'][2:]
 for fraction in (.2,.5,.8): add('ai-split-gap',chat['pane']['x']+chat['pane']['width']*fraction,N['bottom'](chat['pane'])+3,line)
 return result


def verify(evidence,facts,platform,owners):
 need(facts.get('schema')==1 and facts.get('ok') is True and facts.get('identityRestored') is True and not facts.get('error') and facts.get('physicalUserDeviceVerified') is False and facts.get('radius')==12 and facts.get('gap')==6 and facts.get('source')=='Native screenshot-button input, actual composed editor canvas and OS before/after captures','capture corner scope incomplete')
 expected=[]
 for i,owner in enumerate(owners):
  role='main' if i<2 else 'ai-chat' if i==2 else 'ai-preview';pane='.pane[data-pane="p'+str(i+1)+'"]' if i<2 else '#'+role+'-pane'
  expected.append({'id':owner['id'],'role':role,'slotSelector':pane+' .page-slot' if i<2 else '#ai-slot' if i==2 else '#ai-preview-slot','paneSelector':pane,'backgroundRGB':[243,240,232]})
 need(facts.get('targets')==expected,'capture target pane/owner matrix differs')
 scenes=facts.get('scenes',[]);captures=facts.get('captures',[])
 need([s.get('theme') for s in scenes]==['light','dark'] and len(captures)==6,'both themes and six actual captures required')
 count=0
 for scene in scenes:
  theme=scene['theme'];need(scene.get('stage')=='complete' and scene.get('preserved') is True,'capture scene not completed')
  before,after=scene.get('before',{}),scene.get('after',{})
  geometry(before.get('geometry',{}),before.get('native',[]),expected,theme);geometry(after.get('geometry',{}),after.get('native',[]),expected,theme)
  need(before['geometry']==after['geometry'] and before['native']==after['native'],'screenshot changed native owners or workspace geometry')
  need(len(before.get('identities',[]))==len(after.get('identities',[]))==4,'all screenshot page identities required')
  for owner,old,new in zip(owners,before['identities'],after['identities']):
   N['identity'](owner,old);N['identity'](old,new);need(type(old.get('raf')) is int and type(new.get('raf')) is int and new['raf']>old['raf'],'page animation did not resume after capture')
   page=next(p for p in before['native'] if p['id']==owner['id']);need(page['webContentsId']==owner['webContentsId'],'screenshot native owner changed')
  N['input_event'](scene.get('openInput'),platform,'#screenshot-button');N['input_event'](scene.get('closeInput'),platform,'#capture-close')
  if 'themeInput' in scene: N['input_event'](scene['themeInput'],platform,'#statusbar [data-action="theme"]')
  during=scene.get('during',{});need(during.get('overlayBlocked') is True and len(during.get('native',[]))==4,'real screenshot overlay did not hold native pages')
  for row,old in zip(during['native'],before['native']): need(row.get('id')==old['id'] and row.get('webContentsId')==old['webContentsId'] and all(row.get(k) is False for k in ('visible','viewVisible','attached')),'modal capture held a different page or did not hide actual native views')
  wanted=points(before['geometry'],before['native']);need(len(wanted)==89,'corner probe coverage changed')
  for phase in ('before','composed','after'):
   name='mouse-634-capture-corners-'+theme+'-'+phase+'.png';row=next((r for r in captures if r.get('filename')==name),{})
   need(row.get('phase')==phase and row.get('theme')==theme and (scene.get('composed') if phase=='composed' else scene[phase].get('capture'))==name,'capture phase binding differs')
   if phase=='composed':
    image=evidence.png(row);viewport=before['geometry']['viewport'];need(row.get('source')=='capture-dialog #capture-canvas.toDataURL after native screenshot-button click' and row.get('viewport')==viewport and row.get('mapping')=={'scaleX':image['width']/viewport['width'],'scaleY':image['height']/viewport['height'],'originX':0,'originY':0},'composed image is not the actual editor canvas/viewport')
   else: image=evidence.screen(row)
   probes=row.get('probes',[]);need(len(probes)==89,'all actual screenshot corner probes required')
   for probe,target in zip(probes,wanted):
    need(all(probe.get(k)==v for k,v in target.items()) and probe.get('tolerance')==3,'screenshot probe point, owner, palette or tolerance differs')
    x,y,rgba=evidence.pixel(image,row['mapping'],target['cssPoint']);need(probe.get('pixel')=={'x':x,'y':y} and probe.get('actualRGBA')==rgba and rgba[3]==255 and max(abs(a-b) for a,b in zip(rgba[:3],target['expectedRGB']))<=3,'raw composed/native corner pixel failed');count+=1
 return {'themes':['light','dark'],'targets':[o['id'] for o in owners],'captures':6,'decodedProbes':count,'radius':12,'gap':6,'nativeInputVerified':True}
