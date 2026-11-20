#!/usr/bin/env python3
"""Expanded634 bottom geometry and actual header/footer pixels on all3OS."""
from pathlib import Path
import runpy
N=runpy.run_path(str(Path(__file__).with_name('mouse634-native-evidence.py')))
need,near,rect=N['need'],N['near'],N['rect']


def chrome(state):
 header,footer=state.get('header',{}),state.get('footer',{})
 need(isinstance(header.get('backgroundImage'),str) and header['backgroundImage'].startswith('linear-gradient(') and all(footer.get(k)==header.get(k) for k in ('backgroundImage','backgroundColor','backdropFilter')) and header.get('opacity')==footer.get('opacity')=='1','top/footer surfaces do not share their actual opaque background')
 for surface in (header,footer):
  bounds=rect(surface.get('bounds'));points=surface.get('points',[]);need(len(points)==2,'both gradient positions missing')
  for point,fraction in zip(points,(.1,.9)):
   need(point.get('fraction')==fraction and isinstance(point.get('hit'),str) and isinstance(point.get('surfacePath'),list),'unobstructed chrome point missing')
   coords=point.get('point',{});near(coords.get('y'),bounds['y']+bounds['height']*fraction,'chrome relative gradient height',1e-8);need(N['finite'](coords.get('x')) and bounds['x']+100<=coords['x']<N['right'](bounds)-100,'chrome point outside uncovered search region')
 return header,footer


def state_geometry(value,mode,owners,baseline):
 focused=mode!='grid';need(value.get('padding')=={'top':6,'bottom':0 if focused else 6,'left':0,'right':0},'focused workspace padding differs')
 panels=value.get('panels',[]);need(isinstance(panels,list) and len(panels)==(1 if mode=='pane' else 2 if mode=='ai' else 4),'visible native panel count differs')
 need(value.get('window',{}).get('fullscreen') is focused and value.get('mainSlots')==baseline['mainSlots'],'native fullscreen state or main tabs changed')
 rect(value['window'].get('bounds'));rect(value['window'].get('contentBounds'))
 if mode=='pane': need(isinstance(value.get('focusPane'),str) and value['focusPane'] and value.get('focusAI') is False and panels[0].get('key')=='pane:'+value['focusPane'],'expanded main pane identity differs')
 elif mode=='ai': need(value.get('focusPane')=='' and value.get('focusAI') is True and {p.get('tabId') for p in panels}=={value.get('aiId'),value.get('aiPreviewId')},'expanded chat/preview identity differs')
 else: need(value.get('focusPane')=='' and value.get('focusAI') is False,'grid did not restore')
 header,footer=chrome(value);near(min(rect(p['pane'])['y'] for p in panels)-N['bottom'](header['bounds']),6,'top gap changed');near(footer['bounds']['y']-max(N['bottom'](rect(p['slot'])) for p in panels),0 if focused else 6,'expanded bottom gap differs')
 native=value.get('native',[]);need(len(native)==4 and len(value.get('identities',[]))==4,'all original native owners required')
 for old,after in zip(owners,value['identities']): N['identity'](old,after)
 for panel in panels:
  owner=next((o for o in owners if o['id']==panel.get('tabId')),None);need(owner is not None,'foreign focused panel')
  row=next((p for p in native if p.get('tabId')==owner['id']),{});N['native'](row,owner);slot=rect(panel.get('slot'))
  lower=mode=='pane' or mode=='ai' and panel['tabId']==value['aiPreviewId'];radius=0 if lower else 12
  need(panel.get('radius')=={'topLeft':12,'topRight':12,'bottomLeft':radius,'bottomRight':radius} and row.get('roundBottom')==radius and row['bounds']==N['endpoints'](slot),'focused corners or real native viewport differ')
  if lower: near(N['bottom'](panel['pane']),footer['bounds']['y'],'expanded pane does not touch footer');need(N['bottom'](row['bounds'])==N['jsround'](footer['bounds']['y']),'native expanded page leaves a bottom gap')
 visible={r.get('tabId') for r in native if r.get('visible') is True};need(visible=={p['tabId'] for p in panels},'unrelated native page remains over expanded mode')


def verify(evidence,value,platform,arch,pid,owners):
 filename='mouse-634-focused-chrome.json';raw,facts=evidence.json(filename)
 need(value.get('reportFile')==filename and value.get('reportSha256')==N['sha'](raw) and {k:v for k,v in value.items() if k not in ('reportFile','reportSha256')}==facts,'focused embedded/raw report differs')
 need(facts.get('schema')==1 and facts.get('ok') is True and facts.get('restored') is True and not facts.get('error') and facts.get('physicalUserDeviceVerified') is False and (facts.get('version'),facts.get('platform'),facts.get('arch'),facts.get('pid'))==(N['VERSION'],platform,arch,pid) and facts.get('source')=='Native pane fullscreen controls, actual native bounds and full OS display pixels','focused native scope incomplete')
 names=['before']+[phase+'-'+theme for theme in ('light','dark') for phase in ('grid','pane-expanded','pane-restored','ai-expanded','ai-restored','nora-open','nora-restored')]+['restored']
 stages=facts.get('stages',[]);need([s.get('name') for s in stages]==names,'focused/native restore/theme sequence differs');baseline=stages[0]
 for value in stages:
  mode='pane' if value['name'].startswith('pane-expanded') else 'ai' if value['name'].startswith('ai-expanded') else 'nora' if value['name'].startswith('nora-open') else 'grid'
  need(value.get('mode')==mode,'focused mode differs')
  if mode=='nora':
   chrome(value);need(value.get('nora',{}).get('open') is True and value['nora'].get('motion')=='open' and value.get('window',{}).get('fullscreen') is False,'Nora surface not actually open')
  else: state_geometry(value,mode,owners,baseline)
  if value['name'] not in ('before','restored'): need(value['theme']==value['name'].rsplit('-',1)[-1],'focused theme differs')
  if mode in ('grid','nora'): need(value['window']['bounds']==baseline['window']['bounds'],'regular native window was not restored')
 need(stages[-1]['theme']==baseline['theme'] and stages[-1]['native']==baseline['native'],'focused modes changed original theme/native geometry')
 inputs=facts.get('nativeInputs',[]);need(len(inputs)==12,'native fullscreen and Nora controls not exercised')
 pane=next(p for p in baseline['panels'] if p['key'].startswith('pane:'));selector='.pane[data-pane="'+pane['key'][5:]+'"] [data-pane-action="fullscreen"]'
 for event,expected in zip(inputs,[selector,selector,'[data-action="ai-fullscreen"]','[data-action="ai-fullscreen"]','#desktops-button','#desktops-button']*2): N['input_event'](event,platform,expected)
 groups=facts.get('captures',[]);wanted=[(label,theme) for theme in ('light','dark') for label in ('grid','pane-expanded','ai-expanded','nora-open')];need([(g.get('label'),g.get('theme')) for g in groups]==wanted,'focused pixel theme/mode coverage differs')
 count=0
 for group in groups:
  state=next(s for s in stages if s['name']==group['label']+'-'+group['theme']);expected=[]
  if group['label']!='nora-open':
   for panel in state['panels']:
    row=next(p for p in state['native'] if p['tabId']==panel['tabId']);r=row['bounds'];radius=row['roundBottom']
    for side in ('left','right'): expected.append({'kind':'native-bottom-corner','tabId':panel['tabId'],'side':side,'roundBottom':radius,'point':{'x':r['x']+1.5 if side=='left' else N['right'](r)-1.5,'y':N['bottom'](r)-1.5},'expectedRGB':[243,240,232] if radius==0 else N['LINE'][state['theme']]})
    expected.append({'kind':'native-bottom-interior','tabId':panel['tabId'],'point':{'x':N['right'](r)-24.5,'y':N['bottom'](r)-1.5},'expectedRGB':[243,240,232]})
  attempts=group.get('attempts',[]);accepted=group.get('acceptedAttempt');need(type(accepted) is int and 1<=accepted<=4 and len(attempts)==accepted,'focused OS attempts not bounded')
  for number,shot in enumerate(attempts,1):
   need(shot.get('attempt')==number and shot.get('filename')=='mouse-634-focused-chrome-'+group['label']+'-'+group['theme']+'-'+str(number)+'.png' and shot.get('contentBounds')==state['window']['contentBounds'],'focused image is not from the measured native window')
   image=evidence.screen(shot);probes=shot.get('probes',[]);need(len(probes)==len(expected),'focused corner pixel coverage missing');passed=[]
   for probe,target in zip(probes,expected):
    need(all(probe.get(k)==v for k,v in target.items()),'focused corner point/radius/palette differs');x,y,rgba=evidence.pixel(image,shot['mapping'],target['point']);delta=max(abs(a-b) for a,b in zip(rgba[:3],target['expectedRGB']));success=delta<=12
    need(probe.get('pixel')=={'x':x,'y':y,'rgba':rgba} and rgba[3]==255 and probe.get('maxChannelDelta')==delta and probe.get('pass') is success,'actual focused corner pixel differs');passed.append(success);count+=1
   pairs=shot.get('chromePairs',[]);need(len(pairs)==2,'both actual chrome pixel pairs missing')
   for i,pair in enumerate(pairs):
    header,footer=state['header']['points'][i],state['footer']['points'][i];need(pair.get('fraction')==header['fraction']==footer['fraction'] and pair.get('header')==header and pair.get('footer')==footer,'chrome points do not share gradient position')
    a=evidence.pixel(image,shot['mapping'],header['point']);b=evidence.pixel(image,shot['mapping'],footer['point']);delta=max(abs(x-y) for x,y in zip(a[2][:3],b[2][:3]));visible=all(v>=180 for v in a[2][:3]) if state['theme']=='light' else sum(a[2][:3])>30;success=delta<=6 and visible
    need(pair.get('headerPixel')=={'x':a[0],'y':a[1],'rgba':a[2]} and pair.get('footerPixel')=={'x':b[0],'y':b[1],'rgba':b[2]} and a[2][3]==b[2][3]==255 and pair.get('maxChannelDelta')==delta and pair.get('pass') is success,'actual top/footer pixel equality differs');passed.append(success);count+=2
   need(shot.get('pass') is all(passed) and (all(passed) if number==accepted else not all(passed)),'focused accepted frame does not pass actual pixels')
 return {'report':filename,'reportSha256':N['sha'](raw),'stages':16,'captureGroups':8,'decodedProbes':count,'focusedBottomRadius':0,'focusedBottomGap':0,'regularRadius':12,'regularGap':6,'chromePixelsMatch':True}
