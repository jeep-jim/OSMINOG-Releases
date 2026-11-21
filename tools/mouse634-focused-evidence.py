#!/usr/bin/env python3
"""Expanded634 bottom geometry and actual header/footer pixels on all3OS."""
import math
from pathlib import Path
import runpy
N=runpy.run_path(str(Path(__file__).with_name('mouse634-native-evidence.py')))
need,near,rect=N['need'],N['near'],N['rect']


def probe_bounds(original,work_area,minimum,platform):
 original,work_area=rect(original),rect(work_area);need(isinstance(minimum,list) and len(minimum)==2 and all(N['finite'](value) and value>0 for value in minimum),'focused native minimum window size missing')
 expected=dict(original)
 if platform!='darwin':return expected
 bottom=math.floor(N['bottom'](work_area)-32);top=math.ceil(work_area['y']);minimum_height=math.ceil(minimum[1])
 need(bottom-top>=minimum_height and minimum[0]<=original['width']<=work_area['width'],'work area cannot contain the native focused fixture above the Dock shadow')
 expected['x']=min(max(original['x'],work_area['x']),N['right'](work_area)-original['width']);expected['y']=min(max(original['y'],top),bottom-minimum_height);expected['height']=min(original['height'],bottom-expected['y'])
 need(expected['height']>=minimum_height and expected['x']>=work_area['x'] and expected['y']>=work_area['y'] and N['right'](expected)<=N['right'](work_area) and N['bottom'](expected)<=bottom,'focused adjusted native window does not preserve the exact Dock clearance')
 return expected


def probe_window(facts,platform,owners):
 probe=facts.get('probeWindow',{});need(probe.get('minimumBottomClearance')==(32 if platform=='darwin' else 0),'focused native Dock clearance differs')
 expected=probe_bounds(probe.get('originalBounds'),probe.get('workArea'),probe.get('minimumSize'),platform);need(probe.get('adjustedBounds')==expected,'focused adjusted bounds were not independently derived from the actual work area')
 restored=facts.get('windowRestoration',{});original=restored.get('originalNative');need(restored.get('bounds')==probe['originalBounds'] and isinstance(original,list) and len(original)==len(owners) and restored.get('native')==original and not restored.get('error'),'focused caller window/native restoration is not proved by raw before/after geometry')
 for owner,row in zip(owners,original):N['native'](row,owner);need(row.get('roundBottom')==12,'focused caller native bottom corners were not restored')
 return expected


def chrome(state,reference=None):
 header,footer=state.get('header',{}),state.get('footer',{})
 need(isinstance(header.get('backgroundImage'),str) and header['backgroundImage'].startswith('linear-gradient(') and all(footer.get(k)==header.get(k) for k in ('backgroundImage','backgroundColor','backdropFilter')) and header.get('opacity')==footer.get('opacity')=='1','top/footer surfaces do not share their actual opaque background')
 if reference is not None: need(reference.get('name')=='ai-restored-'+state['theme'] and reference.get('theme')==state['theme'] and reference.get('mode')=='grid' and reference.get('nora',{}).get('open') is False,'Nora chrome reference is not the immediately preceding restored grid')
 for name,surface in (('header',header),('footer',footer)):
  bounds=rect(surface.get('bounds'));points=surface.get('points',[]);need(len(points)==2,'both gradient positions missing')
  if reference is None:
   need(surface.get('pointSource')=='live-hit-test' and 'referenceStage' in surface and surface['referenceStage'] is None and all('actualModalHit' not in point for point in points),'closed chrome points are not live hit tests')
  else:
   previous=reference[name];need(surface.get('pointSource')=='pre-modal-layout' and surface.get('referenceStage')==reference['name'] and previous.get('pointSource')=='live-hit-test' and len(previous.get('points',[]))==2,'Nora chrome points lack a measured pre-modal reference')
   need(all(surface.get(key)==previous.get(key) for key in ('bounds','occluders','backgroundImage','backgroundColor','backdropFilter','opacity')),'Nora changed the measured underlying chrome')
   for point,before in zip(points,previous['points']):
    hit=point.get('actualModalHit');need('actualModalHit' in point and (hit is None or isinstance(hit,str) and bool(hit)) and {key:value for key,value in point.items() if key!='actualModalHit'}==before,'Nora point or actual modal hit differs from its measured reference')
  occluders=surface.get('occluders');need(isinstance(occluders,list),'actual chrome vector occluders missing')
  for item in occluders:
   need(isinstance(item,dict) and item.get('selector')=='.mouse-tab-flow','unexpected chrome vector occluder');r=rect(item.get('bounds'))
   near(r.get('right'),N['right'](r),'chrome vector right endpoint differs',1e-8);near(r.get('bottom'),N['bottom'](r),'chrome vector bottom endpoint differs',1e-8)
  for point,fraction in zip(points,(.1,.9)):
   need(point.get('fraction')==fraction and isinstance(point.get('hit'),str) and isinstance(point.get('surfacePath'),list),'unobstructed chrome point missing')
   coords=point.get('point',{});near(coords.get('y'),bounds['y']+bounds['height']*fraction,'chrome relative gradient height',1e-8);need(N['finite'](coords.get('x')) and bounds['x']+100<=coords['x']<N['right'](bounds)-100,'chrome point outside uncovered search region')
   for item in occluders:
    r=item['bounds'];need(not (r['x']-2<=coords['x']<=N['right'](r)+2 and r['y']-2<=coords['y']<=N['bottom'](r)+2),'chrome point intersects pointer-transparent tab-flow vector')
 return header,footer


def nora_surface(state,opened):
 nora=state.get('nora',{});need(nora.get('open') is opened and nora.get('motion')==('open' if opened else 'closed') and nora.get('settingsButtonPresent') is False,'Nora open/closed state or removed settings control differs')
 scrim=nora.get('scrim',{});need(scrim.get('hidden') is (not opened) and N['finite'](scrim.get('opacity')) and scrim['opacity']==(.24 if opened else 0),'Nora shade visibility or exact opacity differs')
 need(scrim.get('backgroundColor')=='rgb(0, 0, 0)','Nora shade is not black')
 if not opened: return
 bounds=rect(scrim.get('bounds'));header=rect(state['header'].get('bounds'));footer=rect(state['footer'].get('bounds'))
 for actual,expected in ((bounds['x'],0),(bounds['y'],0),(bounds['width'],header['width']),(N['bottom'](bounds),footer['y']),(bounds.get('right'),N['right'](bounds)),(bounds.get('bottom'),N['bottom'](bounds))): near(actual,expected,'Nora shade bounds differ',1e-8)
 need(bounds['x']<=header['x'] and N['right'](bounds)>=N['right'](header) and bounds['y']<=header['y'] and N['bottom'](bounds)>=N['bottom'](header),'Nora shade does not cover the complete header')
 for surface,inside in ((state['header'],True),(state['footer'],False)):
  for row in surface['points']:
   point=row['point'];covered=bounds['x']<=point['x']<N['right'](bounds) and bounds['y']<=point['y']<N['bottom'](bounds)
   need(covered is inside,'Nora shade covers the footer or misses a header pixel')


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
 probe=probe_window(facts,platform,owners)
 names=['before']+[phase+'-'+theme for theme in ('light','dark') for phase in ('grid','pane-expanded','pane-restored','ai-expanded','ai-restored','nora-open','nora-restored')]+['restored']
 stages=facts.get('stages',[]);need([s.get('name') for s in stages]==names,'focused/native restore/theme sequence differs');baseline=stages[0];need(baseline.get('window',{}).get('bounds')==probe,'focused baseline is not the measured temporary native window')
 for index,value in enumerate(stages):
  mode='pane' if value['name'].startswith('pane-expanded') else 'ai' if value['name'].startswith('ai-expanded') else 'nora' if value['name'].startswith('nora-open') else 'grid'
  need(value.get('mode')==mode,'focused mode differs')
  if mode=='nora':
   chrome(value,stages[index-1]);need(value.get('nora',{}).get('open') is True and value['nora'].get('motion')=='open' and value.get('window',{}).get('fullscreen') is False,'Nora surface not actually open')
  else: state_geometry(value,mode,owners,baseline)
  nora_surface(value,mode=='nora')
  if value['name'] not in ('before','restored'): need(value['theme']==value['name'].rsplit('-',1)[-1],'focused theme differs')
  if mode in ('grid','nora'): need(value['window']['bounds']==baseline['window']['bounds'],'regular native window was not restored')
 need(stages[-1]['theme']==baseline['theme'] and stages[-1]['native']==baseline['native'],'focused modes changed original theme/native geometry')
 inputs=facts.get('nativeInputs',[]);need(len(inputs)==12,'native fullscreen and Nora controls not exercised')
 pane=next(p for p in baseline['panels'] if p['key'].startswith('pane:'));selector='.pane[data-pane="'+pane['key'][5:]+'"] [data-pane-action="fullscreen"]'
 for event,expected in zip(inputs,[selector,selector,'[data-action="ai-fullscreen"]','[data-action="ai-fullscreen"]','#desktops-button','#desks-close']*2): N['input_event'](event,platform,expected)
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
    a=evidence.pixel(image,shot['mapping'],header['point']);b=evidence.pixel(image,shot['mapping'],footer['point']);shade=.24 if state['nora']['open'] else 0;expected_rgb=[N['jsround'](v*(1-shade)) for v in b[2][:3]];delta=max(abs(x-y) for x,y in zip(a[2][:3],expected_rgb));visible=all(v>=180 for v in b[2][:3]) if state['theme']=='light' else sum(b[2][:3])>30;success=delta<=6 and visible
    need(pair.get('headerPixel')=={'x':a[0],'y':a[1],'rgba':a[2]} and pair.get('footerPixel')=={'x':b[0],'y':b[1],'rgba':b[2]} and a[2][3]==b[2][3]==255 and N['finite'](pair.get('shadeOpacity')) and pair['shadeOpacity']==shade and pair.get('expectedHeaderRGB')==expected_rgb and pair.get('maxChannelDelta')==delta and pair.get('pass') is success,'actual top/footer shade pixels differ');passed.append(success);count+=2
   need(shot.get('pass') is all(passed) and (all(passed) if number==accepted else not all(passed)),'focused accepted frame does not pass actual pixels')
 return {'report':filename,'reportSha256':N['sha'](raw),'stages':16,'captureGroups':8,'decodedProbes':count,'focusedBottomRadius':0,'focusedBottomGap':0,'regularRadius':12,'regularGap':6,'chromePixelsMatch':True,'minimumSystemOverlayClearance':32 if platform=='darwin' else 0,'callerWindowAndNativeRestored':True}
