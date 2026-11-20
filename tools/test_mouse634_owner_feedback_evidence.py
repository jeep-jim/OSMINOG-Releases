#!/usr/bin/env python3
"""Explicit synthetic parser fixtures. These PNGs are NEVER native evidence."""
import copy
import hashlib
import json
import math
from pathlib import Path
import runpy
import struct
import unittest
import zlib
E=runpy.run_path(str(Path(__file__).with_name('mouse634-owner-feedback-evidence.py')))
SEARCH_FIXTURES=runpy.run_path(str(Path(__file__).with_name('test_mouse634_search_evidence.py')))
LINE={'light':[199,207,223],'dark':[67,83,107]};PANEL={'light':[255,255,255],'dark':[25,33,46]}
TRACK=[83,207,139];FILL=[7,130,60];BODY=[243,240,232]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def box(x,y,w,h):return dict(x=x,y=y,width=w,height=h)
def edges(r):return {**r,'right':r['x']+r['width'],'bottom':r['y']+r['height']}
def color(i):return [40+(i*47)%160,55+(i*71)%150,65+(i*29)%140]
def png(width,height,pixels):
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 data=bytearray(bytes([240,240,240,255])*(width*height))
 for (x,y),rgba in pixels.items():
  if 0<=x<width and 0<=y<height:data[(y*width+x)*4:(y*width+x+1)*4]=bytes(rgba)
 rows=b''.join(b'\0'+data[y*width*4:(y+1)*width*4] for y in range(height))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')


def fixture(platform='win32'):
 files={};arch='arm64' if platform=='darwin' else 'x64';source={'win32':'User32','darwin':'CGEvent','linux':'XTest'}[platform];origin='http://127.0.0.1:31337';cross='http://127.0.0.1:31338'
 facts={'schema':1,'version':'6.0.34','platform':platform,'arch':arch,'pid':91,'budgetMs':240000,'elapsedMs':10000,'packaged':True,'profileIsolated':True,'physicalUserDeviceVerified':False,'liveExternalAccountsVerified':False,'source':'Installed app, native pointer input, owned HTTP/download fixtures and actual composed/OS pixels','stage':'complete','ok':True,'restored':True,'nativeInputSource':source,'nativeInputs':[],'captures':[],'fixtureOrigins':[origin,cross],'requests':[{'index':i,'at':j+1} for j,i in enumerate([0,1,2,3,4,3])],'cleanup':{'restored':True,'ownedPagesClosed':5,'originalPagesPreserved':1,'desktopStateRestored':True}}
 def owner(i):return {'id':'page'+str(i),'index':i,'desk':'desk','webContentsId':100+i,'url':(cross if i==3 else origin)+'/page/'+str(i)+'/','navigationEpoch':1,'identity':'owned-'+str(i),'timeOrigin':1000+i,'field':'preserved-'+str(i)+'-данные','scrollX':0,'scrollY':0,'cookie':'mouse631_'+str(i)+'=owned-'+str(i),'ticks':10,'raf':20}
 owners=[owner(i) for i in range(4)]
 def live(rows,ticks):return [{**row,'ticks':ticks,'raf':ticks*2} for row in rows]
 def native(row,r,visible=True,radius=None):
  value={'tabId':row['id'],'index':row['index'],'desk':row['desk'],'webContentsId':row['webContentsId'],'bounds':copy.deepcopy(r),'viewBounds':copy.deepcopy(r),'parentBounds':None,'actualBounds':copy.deepcopy(r),'visible':visible,'parentVisible':True,'cachedVisible':visible,'attached':visible}
  if radius is not None:value['roundBottom']=radius
  return value
 def click(selector,row=None):
  value={'selector':selector,'source':source,'point':{'x':100,'y':100}}
  if row:value.update(tabId=row['id'],webContentsId=row['webContentsId'],events=[{'id':selector[1:],'trusted':True,'isTrusted':True,'at':1}])
  else:value.update(at=1,navigates=False,events=[{'type':'click','trusted':True,'matches':True}])
  facts['nativeInputs'].append(value);return value
 def capture(name,points=(),kind='synthetic fixture',width=640,height=600,extra_pixels=None):
  pixels={(math.floor(p['point']['x']),math.floor(p['point']['y'])):p['expectedRGB']+[255] for p in points}
  pixels.update(extra_pixels or {});raw=png(width,height,pixels);files[name]=raw;display=name[:-4]+'-display.png';files[display]=raw
  value={'filename':name,'displayFilename':display,'displaySha256':sha(raw),'screenPixelSize':{'width':width,'height':height},'kind':kind,'source':'globalCapture.acquire(display)','backend':'synthetic-unit-test-only','sha256':sha(raw),'bytes':len(raw),'pixelSize':{'width':width,'height':height},'contentBounds':box(0,0,width,height),'display':{'id':1,'bounds':box(0,0,width,height),'workArea':box(0,0,width,height),'scaleFactor':1},'cropPixels':box(0,0,width,height),'mapping':{'scaleX':1,'scaleY':1,'originX':0,'originY':0}}
  facts['captures'].append(copy.deepcopy(value));return value
 def sampled(points):return [{**p,'pixel':{'x':math.floor(p['point']['x']),'y':math.floor(p['point']['y']),'rgba':p['expectedRGB']+[255]},'maxChannelDelta':0,'pass':True} for p in points]
 def ui(row,pane,slot,active,download=None,received=0,unread=0):
  footer={'state':'downloading' if active else 'completed','count':1 if active else 0,'bounds':box(520,572,24,28),'unreadCount':unread,'badgeColor':'rgb(7, 130, 60)','badgeHidden':unread==0}
  result={'placement':'bottom','viewport':{'width':640,'height':600},'footer':footer,'pane':pane,'head':box(pane['x'],pane['y'],pane['width'],32),'slot':{**slot,'height':slot['height']-(22 if active else 0)},'dock':None,'pill':None,'activeWidgetCount':int(active),'topDownloadCount':0}
  if active:
   bounds=box(pane['x'],pane['y']+pane['height']-16,pane['width'],16);percent=received/524288*100
   result['dock']=box(bounds['x'],bounds['y']-6,bounds['width'],22);result['pill']={'bounds':bounds,'hidden':False,'ariaNow':str(percent).removesuffix('.0'),'value':str(math.floor(percent))+'%','state':'running','tabId':row['id'],'downloadIds':[download],'count':1,'downloadState':'downloading','indeterminate':False,'text':'','trackColor':'rgb(83, 207, 139)','fillColor':'rgb(7, 130, 60)','radius':'999px'}
  return result
 mainpanes=[box(0,46,317,520),box(323,46,317,520)];mainslots=[box(p['x'],78,p['width'],488) for p in mainpanes]
 gridpanes=[box(0,46,197,520),box(203,46,197,520),box(406,46,234,257),box(406,309,234,257)];gridslots=[box(p['x'],p['y']+32,p['width'],p['height']-32) for p in gridpanes]
 def download(rows,names,panes,slots,unread,download_origins):
  prefix='mouse-634-'+('ai-' if names[0]=='chat' else '')+'download-widget';report=prefix+'.json'
  value={'schema':1,'version':'6.0.34','platform':platform,'arch':arch,'pid':91,'source':'Actual DownloadItems, trusted native guest clicks and full OS display pixels','physicalUserDeviceVerified':False,'placement':'bottom','pillHeight':16,'gap':6,'reservedHeight':22,'palette':{'track':TRACK,'fill':FILL},'pixelTolerance':12,'names':names,'tabIds':[r['id'] for r in rows],'nativeInputs':[click('#download-'+name,row) for name,row in zip(names,rows)],'stages':[],'captures':[],'files':[],'ok':True,'unreadBefore':unread,'unreadAfter':unread+2,'reportFile':report}
  for number,(label,active) in enumerate(zip(['before','first-active','both-active','measured-progress','both-other-theme','first-completed','both-completed'],[[],[names[0]],names,names,names,[names[1]],[]])):
   count=unread+(1 if number==5 else 2 if number==6 else 0);stage={'name':label,'activeNames':active,'at':number+1,'theme':'dark' if number==4 else 'light','activity':{'unreadCount':count},'panels':[],'native':[],'identities':live(rows,10+number),'runningTransitions':[]}
   for index,(row,name,pane_,slot_) in enumerate(zip(rows,names,panes,slots)):
    enabled=name in active;received=65536 if number<3 else 262144 if index==0 else 131072;did='download-'+name
    view=ui(row,pane_,slot_,enabled,did,received,count);panel={'tabId':row['id'],'activeIds':[did] if enabled else [],'ui':view}
    if enabled:panel.update(activity={'id':did,'tabId':row['id'],'state':'downloading','received':received,'total':524288},task={'source':'download','kind':'download','tabId':row['id'],'taskId':did,'phase':'running','estimated':False,'percent':received/524288*100})
    stage['panels'].append(panel);stage['native'].append(native(row,view['slot']))
   value['stages'].append(stage)
  badge={'hidden':False,'display':'block','color':'rgb(7, 130, 60)','text':str(unread+2),'bounds':box(550,578,20,16)};value['badge']=badge
  for label,number in [('first',1),('both',2),('both',4),('first-completed',5),('completed',6)]:
   stage=value['stages'][number];points=[]
   for panel,page,row in zip(stage['panels'],stage['native'],rows):
    pill=panel['ui']['pill']
    if pill:
     r=pill['bounds'];ratio=float(pill['ariaNow'])/100
     for kind,x,rgb in [('fill',r['x']+r['width']*ratio/2,FILL),('track',r['x']+r['width']*(1+ratio)/2,TRACK)]:
      for dy in (-2,0,2):points.append({'kind':kind,'tabId':row['id'],'point':{'x':x,'y':r['y']+8+dy},'expectedRGB':rgb})
     points.append({'kind':'gap','tabId':row['id'],'point':{'x':r['x']+r['width']/2,'y':r['y']-3},'expectedRGB':LINE[stage['theme']]})
    r=page['bounds']
    for dx,dy in ((0,0),(-4,0),(4,0),(0,-4),(0,4)):points.append({'kind':'native-page','tabId':row['id'],'point':{'x':r['x']+.26*r['width']+dx,'y':r['y']+95+dy},'expectedRGB':color(row['index'])})
   if number in (5,6):
    for dy in (-1,0,1):points.append({'kind':'unread-badge','point':{'x':552.5,'y':586+dy},'expectedRGB':FILL})
   shot=capture(prefix+'-'+label+'-'+stage['theme']+'-1.png',points);shot.update(attempt=1,pass_=True,probes=sampled(points));shot['pass']=shot.pop('pass_');value['captures'].append({'label':label,'theme':stage['theme'],'attempts':[shot],'acceptedAttempt':1})
  for index,(name,row) in enumerate(zip(names,rows)):
   events=[{'event':kind,'type':kind,'state':'completed' if kind=='done' else 'progressing','received':received,'total':524288,'at':i+1} for i,(kind,received) in enumerate([('start',0),('updated',65536),('updated',262144 if index==0 else 131072),('done',524288)])];digest=sha(bytes([65+['a','b','chat','preview'].index(name)])*524288)
   value['files'].append({'name':name,'id':'download-'+name,'tabId':row['id'],'webContentsId':row['webContentsId'],'url':download_origins[index]+'/download/'+name,'filename':'mouse634-'+name+'.bin','bytes':524288,'sha256':digest,'expectedBytes':524288,'expectedSha256':digest,'requests':1,'events':events,'saveDecision':'DownloadItem.setSavePath only for this owned HTTP fixture'})
  return value
 facts['downloads']=download(owners[:2],['a','b'],mainpanes,mainslots,0,[origin,origin])
 slots={'p1':'page0','p2':'page1'};oldtabs=[{'id':row['id'],'url':row['url'],'lane':'side' if i==2 else 'main','previewOf':''} for i,row in enumerate(owners[:3])]
 def ai_state(preview='',url='',split=False):
  chat=gridpanes[2] if split else box(406,46,234,520);previewbox=gridpanes[3] if split else box(0,0,0,0)
  return {'aiId':'page2','previewId':preview,'aiOpen':True,'mainSlots':slots,'gap':6,'chat':{**edges(chat),'hidden':False},'preview':{**edges(previewbox),'hidden':not split},'chatSlot':{**edges(box(chat['x'],chat['y']+32,chat['width'],chat['height']-32)),'hidden':False},'previewSlot':{**edges(gridslots[3]),'hidden':not split},'column':edges(box(406,46,234,520)),'workspace':edges(box(0,40,640,532)),'tabs':copy.deepcopy(oldtabs)+([{'id':preview,'url':url,'lane':'side','previewOf':'page2'}] if preview else [])}
 before=ai_state();first=ai_state('firstPreview',cross+'/page/3/',True);second=ai_state('firstPreview',cross+'/page/4/',True);reopened=ai_state('page3',cross+'/page/3/',True);firstowner={**owners[3],'id':'firstPreview','webContentsId':150}
 ai={'ok':True,'before':before,'first':first,'second':second,'closed':copy.deepcopy(before),'reopened':reopened,'native':[native(owners[2],gridslots[2]),native(firstowner,gridslots[3])],'blankClick':click('#link-blank',owners[2]),'sameClick':click('#link-same',owners[2]),'closeClick':click('[data-action="close-ai-preview"]'),'chatBefore':owners[2],'chatAfter':copy.deepcopy(owners[2]),'mainBefore':owners[:2],'mainAfter':copy.deepcopy(owners[:2]),'mainTabsUnchanged':True,'previewReused':True,'chatRestored':True}
 ai['chatAfterBlank']=copy.deepcopy(owners[2]);owners[2]={**owners[2],'navigationEpoch':2};ai['chatAfterSame']=copy.deepcopy(owners[2]);ai['chatAfterClose']=copy.deepcopy(owners[2]);ai['chatAfter']=copy.deepcopy(owners[2]);ai['mainAfterSame']=copy.deepcopy(owners[:2])
 ai['chatNavigation']={'source':'WebContents navigation events for one native same-window link click','tabId':owners[2]['id'],'webContentsId':owners[2]['webContentsId'],'targetURL':cross+'/page/4/','events':[
  {'type':'did-start-navigation','url':cross+'/page/4/','mainFrame':True,'sameDocument':False,'navigationEpoch':2,'at':1000},
  {'type':'will-navigate','url':cross+'/page/4/','mainFrame':True,'sameDocument':False,'navigationEpoch':2,'at':1001,'prevented':True}]}
 click('#link-blank',owners[2]);capture('mouse-634-ai-preview-new-window.png');ai['downloads']=download(owners[2:],['chat','preview'],gridpanes[2:],gridslots[2:],2,[origin,cross]);facts['aiPreview']=ai
 targets=[]
 for i,row in enumerate(owners):
  role='main' if i<2 else 'ai-chat' if i==2 else 'ai-preview';pane='.pane[data-pane="p'+str(i+1)+'"]' if i<2 else '#'+role+'-pane';targets.append({'id':row['id'],'role':role,'slotSelector':pane+' .page-slot' if i<2 else '#ai-slot' if i==2 else '#ai-preview-slot','paneSelector':pane,'backgroundRGB':BODY})
 corners={'schema':1,'ok':True,'source':'Native screenshot-button input, actual composed editor canvas and OS before/after captures','physicalUserDeviceVerified':False,'radius':12,'gap':6,'targets':targets,'scenes':[],'captures':[],'identityRestored':True}
 for theme in ('light','dark'):
  geometry={'theme':theme,'viewport':{'width':640,'height':600},'workspace':box(0,40,640,532),'padding':{'top':6,'right':0,'bottom':6,'left':0},'line':'rgb('+', '.join(map(str,LINE[theme]))+')','panel':'#ffffff' if theme=='light' else '#19212e','focusPane':'','focusAI':False,'targets':[{**t,'pane':p,'slot':s,'paneRadii':[12]*4,'slotRadii':[0,0,12,12],'hidden':False} for t,p,s in zip(targets,gridpanes,gridslots)]}
  nativepages=[{'id':r['id'],'webContentsId':r['webContentsId'],'bounds':s,'actualBounds':s,'clip':s,'roundBottom':12,'visible':True,'viewVisible':True,'parentVisible':True,'attached':True} for r,s in zip(owners,gridslots)]
  points=[]
  def add(kind,x,y,rgb,**extra):points.append({'kind':kind,**extra,'cssPoint':{'x':x,'y':y},'expectedRGB':rgb})
  for edge,y in [('top',43),('bottom',569)]:
   for fraction in (.2,.5,.8):add('workspace-gap',640*fraction,y,LINE[theme],edge=edge)
  for t,p,s in zip(targets,gridpanes,gridslots):
   for side in ('left','right'):
    for u in (.65,1.6):
     for v in (.65,1.6):add('pane-top-cutout',p['x']+u if side=='left' else p['x']+p['width']-u,p['y']+v,LINE[theme],id=t['id'],side=side);add('page-bottom-cutout',s['x']+u if side=='left' else s['x']+s['width']-u,s['y']+s['height']-v,LINE[theme],id=t['id'],side=side)
    add('pane-top-interior',math.ceil(p['x']+12)+.5 if side=='left' else math.floor(p['x']+p['width']-12)-.5,math.ceil(p['y'])+.5,PANEL[theme],id=t['id'],side=side)
    add('page-bottom-interior',s['x']+15.5 if side=='left' else s['x']+s['width']-15.5,s['y']+s['height']-3.5,BODY,id=t['id'],side=side)
  for fraction in (.2,.5,.8):add('ai-split-gap',406+234*fraction,306,LINE[theme])
  scene={'theme':theme,'stage':'complete','preserved':True,'before':{'geometry':geometry,'native':nativepages,'identities':live(owners,20)},'after':{'geometry':copy.deepcopy(geometry),'native':copy.deepcopy(nativepages),'identities':live(owners,30)},'openInput':click('#screenshot-button'),'closeInput':click('#capture-close'),'during':{'overlayBlocked':True,'native':[{**p,'visible':False,'viewVisible':False,'attached':False} for p in nativepages]}}
  for phase in ('before','composed','after'):
   name='mouse-634-capture-corners-'+theme+'-'+phase+'.png';mapped=[{**p,'point':p['cssPoint']} for p in points];shot=capture(name,mapped)
   if phase=='composed':
    facts['captures'].pop();shot={k:v for k,v in shot.items() if k in ('filename','sha256','bytes','pixelSize','mapping')};shot.update(source='capture-dialog #capture-canvas.toDataURL after native screenshot-button click',viewport={'width':640,'height':600});scene['composed']=name
   else:scene[phase]['capture']=name
   shot.update(phase=phase,theme=theme,probes=[{**p,'pixel':{'x':math.floor(p['cssPoint']['x']),'y':math.floor(p['cssPoint']['y'])},'actualRGBA':p['expectedRGB']+[255],'tolerance':3} for p in points]);corners['captures'].append(shot)
  corners['scenes'].append(scene)
 facts['captureCorners']=corners
 def chrome_surface(r,theme):return {'bounds':edges(r),'backgroundImage':'linear-gradient(rgb(240, 240, 240), rgb(230, 230, 230))' if theme=='light' else 'linear-gradient(rgb(40, 40, 40), rgb(30, 30, 30))','backgroundColor':'rgb(240, 240, 240)' if theme=='light' else 'rgb(35, 35, 35)','backdropFilter':'none','opacity':'1','occluders':[],'pointSource':'live-hit-test','referenceStage':None,'points':[{'fraction':fraction,'point':{'x':100,'y':r['y']+r['height']*fraction},'hit':'toolbar','surfacePath':[]} for fraction in (.1,.9)]}
 def focused_state(name,theme,mode):
  w,h=(800,700) if mode in ('pane','ai') else (640,600);footer=box(0,h-28,w,28);header=box(0,0,w,40)
  if mode=='pane':panes=[box(0,46,w,h-28-46)];indices=[0]
  elif mode=='ai':panes=[box(0,46,w,310),box(0,362,w,310)];indices=[2,3]
  else:panes=gridpanes;indices=list(range(4))
  panels=[];nativepages=[]
  for i,p in zip(indices,panes):
   radius=0 if mode=='pane' or mode=='ai' and i==3 else 12;s=box(p['x'],p['y']+32,p['width'],p['height']-32);panels.append({'key':'pane:p'+str(i+1) if i<2 else 'ai' if i==2 else 'ai-preview','tabId':owners[i]['id'],'pane':edges(p),'slot':edges(s),'radius':{'topLeft':12,'topRight':12,'bottomLeft':radius,'bottomRight':radius}})
  for i,row in enumerate(owners):
   panel=next((p for p in panels if p['tabId']==row['id']),None);r={k:v for k,v in panel['slot'].items() if k in ('x','y','width','height')} if panel else gridslots[i];nativepages.append(native(row,r,visible=panel is not None and mode!='nora',radius=panel['radius']['bottomLeft'] if panel else 12))
  nora={'open':mode=='nora','motion':'open' if mode=='nora' else 'closed','settingsButtonPresent':False,'scrim':{'hidden':mode!='nora','opacity':.24 if mode=='nora' else 0,'backgroundColor':'rgb(0, 0, 0)','bounds':edges(box(0,0,w,h-28) if mode=='nora' else box(0,0,0,0))}}
  return {'name':name,'mode':mode,'theme':theme,'focusPane':'p1' if mode=='pane' else '','focusAI':mode=='ai','aiId':'page2','aiPreviewId':'page3','mainSlots':slots,'workspace':edges(box(0,40,w,h-68)),'padding':{'top':6,'bottom':0 if mode in ('pane','ai') else 6,'left':0,'right':0},'header':chrome_surface(header,theme),'footer':chrome_surface(footer,theme),'nora':nora,'panels':panels,'window':{'bounds':box(0,0,w,h),'contentBounds':box(0,0,w,h),'fullscreen':mode in ('pane','ai')},'native':nativepages,'identities':copy.deepcopy(owners)}
 focused={'schema':1,'version':'6.0.34','platform':platform,'arch':arch,'pid':91,'physicalUserDeviceVerified':False,'source':'Native pane fullscreen controls, actual native bounds and full OS display pixels','stages':[focused_state('before','light','grid')],'nativeInputs':[],'captures':[],'ok':True,'restored':True,'reportFile':'mouse-634-focused-chrome.json'}
 original_bounds=box(0,32 if platform=='darwin' else 0,640,600);original_native=copy.deepcopy(focused['stages'][0]['native'])
 focused['probeWindow']={'originalBounds':original_bounds,'workArea':box(0,0,640,632),'minimumSize':[600,600],'minimumBottomClearance':32 if platform=='darwin' else 0,'adjustedBounds':box(0,0,640,600)}
 focused['windowRestoration']={'bounds':copy.deepcopy(original_bounds),'native':copy.deepcopy(original_native),'originalNative':original_native}
 for theme in ('light','dark'):
  for label,mode in [('grid','grid'),('pane-expanded','pane'),('pane-restored','grid'),('ai-expanded','ai'),('ai-restored','grid'),('nora-open','nora'),('nora-restored','grid')]:
   stage=focused_state(label+'-'+theme,theme,mode)
   if mode=='nora':
    previous=focused['stages'][-1]
    for surface in ('header','footer'):stage[surface].update(pointSource='pre-modal-layout',referenceStage=previous['name'],points=[{**copy.deepcopy(point),'actualModalHit':'synthetic-modal-hit'} for point in previous[surface]['points']])
   focused['stages'].append(stage)
   if label not in ('grid','pane-expanded','ai-expanded','nora-open'):continue
   points=[]
   if mode!='nora':
    for panel in stage['panels']:
     row=next(p for p in stage['native'] if p['tabId']==panel['tabId']);r=row['bounds'];radius=row['roundBottom']
     for side in ('left','right'):points.append({'kind':'native-bottom-corner','tabId':row['tabId'],'side':side,'roundBottom':radius,'point':{'x':r['x']+1.5 if side=='left' else r['x']+r['width']-1.5,'y':r['y']+r['height']-1.5},'expectedRGB':BODY if radius==0 else LINE[theme]})
     points.append({'kind':'native-bottom-interior','tabId':row['tabId'],'point':{'x':r['x']+r['width']-24.5,'y':r['y']+r['height']-1.5},'expectedRGB':BODY})
   pixel=[240,240,240,255] if theme=='light' else [35,35,35,255];shade=.24 if mode=='nora' else 0;header_rgb=[math.floor(v*(1-shade)+.5) for v in pixel[:3]];pairs=[];extra={}
   for a,b in zip(stage['header']['points'],stage['footer']['points']):
    ap={'x':math.floor(a['point']['x']),'y':math.floor(a['point']['y']),'rgba':header_rgb+[255]};bp={'x':math.floor(b['point']['x']),'y':math.floor(b['point']['y']),'rgba':pixel};extra[(ap['x'],ap['y'])]=ap['rgba'];extra[(bp['x'],bp['y'])]=pixel;pairs.append({'fraction':a['fraction'],'header':a,'footer':b,'headerPixel':ap,'footerPixel':bp,'shadeOpacity':shade,'expectedHeaderRGB':header_rgb,'maxChannelDelta':0,'pass':True})
   r=stage['window']['contentBounds'];shot=capture('mouse-634-focused-chrome-'+label+'-'+theme+'-1.png',points,width=r['width'],height=r['height'],extra_pixels=extra);shot.update(attempt=1,probes=sampled(points),chromePairs=pairs);shot['pass']=True;focused['captures'].append({'label':label,'theme':theme,'attempts':[shot],'acceptedAttempt':1})
  for selector in ['.pane[data-pane="p1"] [data-pane-action="fullscreen"]']*2+['[data-action="ai-fullscreen"]']*2+['#desktops-button','#desks-close']:focused['nativeInputs'].append(click(selector))
 focused['stages'].append(focused_state('restored','light','grid'));facts['focusedChrome']=focused
 search_files,search,_=SEARCH_FIXTURES['fixture'](platform,owners,focused['stages'][-1]['native']);files.update(search_files);facts['search']=search
 facts['nativeInputs'].extend(copy.deepcopy(row) for row in search['inputs'] if 'id' not in row)
 facts['captures'].extend(copy.deepcopy(shot) for group in search['captures'] for shot in group['attempts'])
 facts['captures'].extend(copy.deepcopy(shot) for shot in (search['nora']['capture'],search['captureModal']['capture'],search['restoredCapture']))
 files['mouse-634-owner-feedback.log']=b'MOUSE_634_OWNER_FEEDBACK_PASS\nMOUSE_634_SEARCH_NATIVE_PASS\nSynthetic parser fixture only\n'
 def refresh():
  for report in (facts['downloads'],facts['aiPreview']['downloads'],facts['focusedChrome'],facts.get('search')):
   if report is None:continue
   raw=json.dumps({k:v for k,v in report.items() if k not in ('reportFile','reportSha256')}).encode();files[report['reportFile']]=raw;report['reportSha256']=sha(raw)
  raw=json.dumps(facts).encode();files[E['NAME']]=raw
  if platform in ('win32','linux'):
   wrapper={'checks':{'ownerFeedback634':{'exitCode':0,'pid':91,'elapsedMs':10000,'requiredMarkers':['MOUSE_634_OWNER_FEEDBACK_PASS'],'reportSha256':sha(raw)}}}
   if platform=='linux':wrapper['checks']['ownerFeedback634'].update(log='mouse-634-owner-feedback.log',logSha256=sha(files['mouse-634-owner-feedback.log']))
   files['mouse-'+('windows' if platform=='win32' else 'linux')+'-verification.json']=json.dumps(wrapper).encode()
 refresh();return files,facts,refresh


class Current634Evidence(unittest.TestCase):
 def setUp(self):self.files,self.facts,self.refresh=fixture()
 def verify(self):self.refresh();return E['verify'](self.files.__getitem__,expected_platform=self.facts['platform'],expected_arch=self.facts['arch'])
 def reject(self):
  with self.assertRaises((ValueError,KeyError,TypeError)):self.verify()
 def focused_pixels(self,index,header_rgba,footer_rgba,shade):
  # Rewrite both actual PNGs and every size/hash receipt, leaving a deliberately
  # self-consistent claimed pass for the independent pixel gate to assess.
  shot=self.facts['focusedChrome']['captures'][index]['attempts'][0];pixels={(p['pixel']['x'],p['pixel']['y']):p['pixel']['rgba'] for p in shot['probes']}
  for pair in shot['chromePairs']:
   for key,rgba in (('headerPixel',header_rgba),('footerPixel',footer_rgba)):
    pair[key]['rgba']=list(rgba);pixels[(pair[key]['x'],pair[key]['y'])]=list(rgba)
   pair.update(shadeOpacity=shade,expectedHeaderRGB=list(header_rgba[:3]),maxChannelDelta=0,pass_=True);pair['pass']=pair.pop('pass_')
  raw=png(shot['pixelSize']['width'],shot['pixelSize']['height'],pixels);self.files[shot['filename']]=raw;self.files[shot['displayFilename']]=raw
  for row in [shot]+[r for r in self.facts['captures'] if r['filename']==shot['filename']]:row.update(sha256=sha(raw),displaySha256=sha(raw),bytes=len(raw))
 def test_all_three_actual_schemas_accept_explicit_synthetic_fixtures(self):
  for platform in ('win32','darwin','linux'):
   self.files,self.facts,self.refresh=fixture(platform);result=self.verify();self.assertEqual(result['captureCorners']['decodedProbes'],534);self.assertEqual(result['focusedChrome']['captureGroups'],8);self.assertEqual(result['search']['captureGroups'],2);self.assertEqual(len(result['nativeCaptures']),28)
 def test_native_search_is_required_and_bound_to_its_raw_report_and_owner_ledgers(self):
  self.facts.pop('search');self.reject()
  self.setUp();self.facts['search']['reportFile']='mouse-634-optional-search.json';self.reject()
  self.setUp();name=self.facts['search']['captures'][0]['attempts'][0]['filename'];self.facts['captures']=[shot for shot in self.facts['captures'] if shot['filename']!=name];self.reject()
  self.setUp();event=next(row for row in self.facts['search']['inputs'] if row['selector']=='#mouse-search-button');self.facts['nativeInputs']=[row for row in self.facts['nativeInputs'] if row!=event];self.reject()
 def test_focused_probe_window_is_derived_and_only_mac_can_adjust_it(self):
  self.facts['focusedChrome']['probeWindow']['adjustedBounds']['y']=1;self.reject()
  self.setUp();self.facts['focusedChrome']['probeWindow']['minimumBottomClearance']=32;self.reject()
  self.files,self.facts,self.refresh=fixture('darwin');self.facts['focusedChrome']['probeWindow']['minimumBottomClearance']=0;self.reject()
  self.files,self.facts,self.refresh=fixture('darwin');self.facts['focusedChrome']['probeWindow']['workArea']['height']=620;self.reject()
 def test_focused_mac_adjustment_keeps_native_minimum_size_and_exact_clearance(self):
  adjusted=E['F']['probe_bounds'](box(20,32,800,632),box(0,0,900,650),[800,600],'darwin');self.assertEqual(adjusted,box(20,18,800,600))
  unchanged=E['F']['probe_bounds'](box(20,32,800,632),box(0,0,900,650),[800,600],'win32');self.assertEqual(unchanged,box(20,32,800,632))
  for area,minimum in [(box(0,0,900,620),[800,600]),(box(0,0,799,900),[800,600]),(box(0,0,900,900),[900,600])]:
   with self.assertRaises(ValueError):E['F']['probe_bounds'](box(20,32,800,632),area,minimum,'darwin')
 def test_focused_caller_window_native_hierarchy_and_corner_restore_require_raw_data(self):
  self.facts['focusedChrome'].pop('windowRestoration');self.reject()
  self.setUp();self.facts['focusedChrome']['windowRestoration']['bounds']['height']-=1;self.reject()
  self.setUp();self.facts['focusedChrome']['windowRestoration']['native'][0]['actualBounds']['height']+=1;self.reject()
  self.setUp()
  for key in ('native','originalNative'):self.facts['focusedChrome']['windowRestoration'][key][0]['roundBottom']=0
  self.reject()
 def test_download_owners_and_exact_reservation_are_required(self):
  for branch in ('downloads','ai'):
   self.setUp();value=self.facts['downloads'] if branch=='downloads' else self.facts['aiPreview']['downloads'];value['stages'][2]['native'][0]['bounds']['height']+=1;self.reject()
   self.setUp();value=self.facts['downloads'] if branch=='downloads' else self.facts['aiPreview']['downloads'];value['files'][0]['webContentsId']+=1;self.reject()
 def test_terminal_restoration_and_persistent_unread_cannot_be_flags_only(self):
  self.facts['downloads']['stages'][-1]['panels'][0]['ui']['pill']={'invented':'terminal'};self.reject()
  self.setUp();self.facts['downloads']['stages'][2]['activity']['unreadCount']=1;self.reject()
 def test_native_file_bytes_and_known_meter_are_independent(self):
  self.facts['downloads']['files'][0]['sha256']='0'*64;self.reject()
  self.setUp();self.facts['downloads']['stages'][3]['panels'][0]['ui']['pill']['ariaNow']='49';self.reject()
 def test_download_urls_are_bound_to_each_validated_document_origin(self):
  primary,preview=self.facts['fixtureOrigins']
  self.assertEqual([row['url'] for row in self.facts['downloads']['files']],[primary+'/download/a',primary+'/download/b'])
  self.assertEqual([row['url'] for row in self.facts['aiPreview']['downloads']['files']],[primary+'/download/chat',preview+'/download/preview'])
  self.assertTrue(self.verify()['ok'])
 def test_swapped_and_foreign_download_origins_are_rejected(self):
  primary,preview=self.facts['fixtureOrigins']
  for branch,index,wrong in [('main',0,preview),('main',1,preview),('ai',0,preview),('ai',1,primary),('ai',1,'http://127.0.0.1:31339')]:
   self.setUp();value=self.facts['downloads'] if branch=='main' else self.facts['aiPreview']['downloads'];entry=value['files'][index];entry['url']=wrong+'/download/'+entry['name']
   with self.subTest(branch=branch,index=index,origin=wrong),self.assertRaisesRegex(ValueError,'native downloaded bytes/owner'):self.verify()
 def test_downloads_do_not_revoke_or_replace_either_owning_document(self):
  for branch,index in [('main',0),('main',1),('ai',0),('ai',1)]:
   for field in ('navigationEpoch','timeOrigin'):
    self.setUp();value=self.facts['downloads'] if branch=='main' else self.facts['aiPreview']['downloads'];value['stages'][1]['identities'][index][field]+=1
    with self.subTest(branch=branch,index=index,field=field),self.assertRaisesRegex(ValueError,'identity'):self.verify()
 def test_ai_links_must_target_the_right_preview_without_background_tab(self):
  self.facts['aiPreview']['first']['tabs'][-1]['lane']='main';self.reject()
  self.setUp();self.facts['aiPreview']['second']['previewId']='different';self.reject()
  self.setUp();self.facts['aiPreview']['closed']['chatSlot']['height']-=22;self.reject()
 def test_untrusted_input_reloaded_chat_or_extra_request_are_rejected(self):
  self.facts['aiPreview']['blankClick']['events'][0].update(trusted=False,isTrusted=False);self.reject()
  self.setUp();self.facts['aiPreview']['chatAfter']['timeOrigin']+=1;self.reject()
  self.setUp();self.facts['requests'].append({'index':2,'at':10});self.reject()
 def test_only_exact_observed_canceled_chat_attempt_may_advance_its_epoch(self):
  ai=self.facts['aiPreview'];args=('win32',*self.facts['fixtureOrigins']);self.assertEqual(E['canceled_chat_navigation'](ai,*args)['navigationEpoch'],2)
  with self.assertRaisesRegex(ValueError,'identity'):E['N']['identity'](ai['chatBefore'],ai['chatAfter'],self.facts['fixtureOrigins'][0])
  mutations=[lambda a:a.pop('chatNavigation'),lambda a:a['chatAfterBlank'].update(navigationEpoch=2),lambda a:a['chatAfterSame'].update(navigationEpoch=3),lambda a:a['chatAfterClose'].update(navigationEpoch=1),lambda a:a['chatAfter'].update(navigationEpoch=3),
   lambda a:a['chatNavigation'].update(tabId='other'),lambda a:a['chatNavigation'].update(webContentsId=999),lambda a:a['chatNavigation'].update(targetURL='https://external.example/'),
   lambda a:a['chatNavigation']['events'][0].update(navigationEpoch=1),lambda a:a['chatNavigation']['events'][0].update(mainFrame=False),lambda a:a['chatNavigation']['events'][0].update(sameDocument=True),
   lambda a:a['chatNavigation']['events'][1].update(prevented=False),lambda a:a['chatNavigation']['events'][1].update(at=999),lambda a:a['chatNavigation']['events'][1].update(url='http://127.0.0.1:31338/page/3/')]
  for number,mutate in enumerate(mutations):
   value=copy.deepcopy(ai);mutate(value)
   with self.subTest(number=number),self.assertRaises((ValueError,KeyError,TypeError)):E['canceled_chat_navigation'](value,*args)
 def test_navigation_commit_finish_or_reloaded_chat_cannot_hide_behind_cancellation(self):
  ai=self.facts['aiPreview'];args=('win32',*self.facts['fixtureOrigins'])
  for event in ('did-frame-navigate','did-navigate','did-navigate-in-page','did-finish-load','did-start-navigation'):
   value=copy.deepcopy(ai);value['chatNavigation']['events'].append({**value['chatNavigation']['events'][0],'type':event})
   with self.subTest(event=event),self.assertRaisesRegex(ValueError,'canceled navigation witness'):E['canceled_chat_navigation'](value,*args)
  for field,value in [('timeOrigin',9999),('identity','new-document'),('webContentsId',999),('url','http://127.0.0.1:31338/page/4/'),('field','changed'),('cookie','changed'),('scrollY',1)]:
   changed=copy.deepcopy(ai);changed['chatAfterSame'][field]=value
   with self.subTest(field=field),self.assertRaisesRegex(ValueError,'identity'):E['canceled_chat_navigation'](changed,*args)
 def test_post_cancellation_native_helpers_must_keep_the_actual_new_epoch(self):
  self.facts['aiPreview']['downloads']['stages'][0]['identities'][0]['navigationEpoch']=1;self.reject()
 def test_composed_corner_pixels_and_fixed_radius_are_recomputed(self):
  self.facts['captureCorners']['scenes'][0]['before']['native'][0]['roundBottom']=0;self.reject()
  self.setUp();row=self.facts['captureCorners']['captures'][1];row['probes'][0]['actualRGBA']=[0,0,0,255];self.reject()
 def test_full_display_bytes_cannot_disagree_with_the_window_crop(self):
  row=self.facts['downloads']['captures'][0]['attempts'][0];raw=png(640,600,{});self.files[row['displayFilename']]=raw;row['displaySha256']=sha(raw);self.reject()
 def test_focus_bottom_zero_preserves_regular_and_top_radius(self):
  for stage,radius in [(2,12),(1,0)]:
   self.setUp();self.facts['focusedChrome']['stages'][stage]['panels'][0]['radius']['bottomLeft']=radius;self.reject()
  self.setUp();self.facts['focusedChrome']['stages'][2]['padding']['bottom']=6;self.reject()
 def test_footer_requires_actual_shaded_header_pixels_in_nora(self):
  row=self.facts['focusedChrome']['captures'][3]['attempts'][0];row['chromePairs'][0]['footerPixel']['rgba']=[0,0,0,255];self.reject()
  self.setUp();self.facts['focusedChrome']['stages'][6]['footer']['backgroundImage']='none';self.reject()
 def test_chrome_excludes_pointer_transparent_tab_flow_bounds(self):
  state=copy.deepcopy(self.facts['focusedChrome']['stages'][1]);header=state['header'];header['occluders']=[{'selector':'.mouse-tab-flow','bounds':edges(box(90,32,400,8))}]
  for x in (100,490,492):
   header['points'][1]['point']['x']=x
   with self.subTest(x=x),self.assertRaisesRegex(ValueError,'pointer-transparent tab-flow'):E['F']['chrome'](state)
  header['points'][1]['point']['x']=494;E['F']['chrome'](state)
  header['occluders'][0]['bounds']['right']+=1
  with self.assertRaisesRegex(ValueError,'vector right endpoint'):E['F']['chrome'](state)
  header['occluders'][0]['bounds']['right']-=1;header['occluders'][0]['selector']='unmeasured'
  with self.assertRaisesRegex(ValueError,'unexpected chrome vector'):E['F']['chrome'](state)
  header.pop('occluders')
  with self.assertRaisesRegex(ValueError,'vector occluders missing'):E['F']['chrome'](state)
 def test_nora_uses_exact_prior_points_and_records_the_actual_modal_hit(self):
  previous=self.facts['focusedChrome']['stages'][5];original=self.facts['focusedChrome']['stages'][6];state=copy.deepcopy(original)
  for surface in ('header','footer'):
   for point in state[surface]['points']:point['actualModalHit']=None
  E['F']['chrome'](state,previous)
  for change in (lambda p:p.pop('actualModalHit'),lambda p:p.update(actualModalHit=''),lambda p:p.update(actualModalHit=42),lambda p:p.update(hit='invented'),lambda p:p['point'].update(x=102),lambda p:p.update(surfacePath=['invented'])):
   state=copy.deepcopy(original);change(state['header']['points'][0])
   with self.assertRaisesRegex(ValueError,'modal hit differs'):E['F']['chrome'](state,previous)
  self.facts['focusedChrome']['stages'][6]['header']['referenceStage']='grid-light';self.reject()
 def test_nora_rejects_changed_chrome_or_an_unrelated_reference(self):
  previous=self.facts['focusedChrome']['stages'][5];original=self.facts['focusedChrome']['stages'][6]
  for reference in (self.facts['focusedChrome']['stages'][1],self.facts['focusedChrome']['stages'][12]):
   with self.assertRaisesRegex(ValueError,'immediately preceding restored grid'):E['F']['chrome'](original,reference)
  for key,value in [('bounds',edges(box(1,0,640,40))),('occluders',[{'selector':'.mouse-tab-flow','bounds':edges(box(300,32,80,8))}]),('backgroundImage','linear-gradient(rgb(250, 250, 250), rgb(230, 230, 230))'),('backgroundColor','rgb(239, 239, 239)'),('backdropFilter','blur(1px)'),('opacity','.99')]:
   state=copy.deepcopy(original)
   for surface in ('header','footer'):state[surface][key]=copy.deepcopy(value)
   with self.subTest(field=key),self.assertRaises(ValueError):E['F']['chrome'](state,previous)
  state=copy.deepcopy(original);state['header']['pointSource']='live-hit-test'
  with self.assertRaisesRegex(ValueError,'measured pre-modal reference'):E['F']['chrome'](state,previous)
 def test_closed_chrome_cannot_claim_pre_modal_or_modal_hits(self):
  original=self.facts['focusedChrome']['stages'][1]
  for change in (lambda s:s.update(pointSource='pre-modal-layout'),lambda s:s.update(referenceStage='ai-restored-light'),lambda s:s.pop('referenceStage'),lambda s:s['points'][0].update(actualModalHit=None)):
   state=copy.deepcopy(original);change(state['header'])
   with self.assertRaisesRegex(ValueError,'not live hit tests'):E['F']['chrome'](state)
 def test_nora_has_no_settings_gear_in_any_stage(self):
  for original in self.facts['focusedChrome']['stages']:
   state=copy.deepcopy(original);state['nora']['settingsButtonPresent']=True
   with self.subTest(stage=state['name']),self.assertRaisesRegex(ValueError,'removed settings control'):E['F']['nora_surface'](state,state['mode']=='nora')
  self.facts['focusedChrome']['stages'][-1]['nora'].pop('settingsButtonPresent');self.reject()
 def test_nora_shade_requires_exact_visibility_opacity_and_black(self):
  for stage,changes in [(6,{'hidden':True}),(6,{'opacity':.12}),(6,{'opacity':.240001}),(6,{'opacity':'0.24'}),(6,{'backgroundColor':'rgb(1, 1, 1)'}),(0,{'hidden':False}),(0,{'opacity':.24}),(0,{'opacity':False}),(0,{'backgroundColor':'transparent'})]:
   state=copy.deepcopy(self.facts['focusedChrome']['stages'][stage]);state['nora']['scrim'].update(changes)
   with self.subTest(stage=stage,changes=changes),self.assertRaisesRegex(ValueError,'Nora shade'):E['F']['nora_surface'](state,state['mode']=='nora')
 def test_nora_shade_bounds_cover_header_and_stop_before_footer(self):
  original=self.facts['focusedChrome']['stages'][6]
  for key,delta in [('x',1),('y',1),('width',-1),('height',-1),('height',1)]:
   state=copy.deepcopy(original);bounds=state['nora']['scrim']['bounds'];bounds[key]+=delta;bounds.update(edges(bounds))
   with self.subTest(key=key,delta=delta),self.assertRaisesRegex(ValueError,'Nora shade bounds'):E['F']['nora_surface'](state,True)
  state=copy.deepcopy(original);state['nora']['scrim']['bounds']['bottom']+=1
  with self.assertRaisesRegex(ValueError,'Nora shade bounds'):E['F']['nora_surface'](state,True)
  state=copy.deepcopy(original);state['header']['bounds']['y']=-1
  with self.assertRaisesRegex(ValueError,'complete header'):E['F']['nora_surface'](state,True)
  state=copy.deepcopy(original);state['footer']['points'][0]['point']['y']=10
  with self.assertRaisesRegex(ValueError,'covers the footer'):E['F']['nora_surface'](state,True)
 def test_nora_visibility_is_measured_on_the_undimmed_footer(self):
  self.focused_pixels(3,[152,156,160,255],[200,205,210,255],.24)
  self.focused_pixels(7,[9,9,9,255],[12,12,12,255],.24)
  self.assertTrue(self.verify()['ok'])
 def test_independent_pngs_reject_missing_half_or_footer_shade(self):
  cases=[(3,[240,240,240,255],[240,240,240,255],.24),(7,[35,35,35,255],[35,35,35,255],.24),(3,[211,211,211,255],[240,240,240,255],.24),(3,[182,182,182,255],[182,182,182,255],.24),(0,[182,182,182,255],[240,240,240,255],0)]
  for index,header,footer,shade in cases:
   self.setUp();self.focused_pixels(index,header,footer,shade)
   with self.subTest(index=index,header=header,footer=footer),self.assertRaisesRegex(ValueError,'actual top/footer shade pixels'):self.verify()
 def test_shade_metadata_and_alpha_cannot_override_actual_pixels(self):
  for changes in ({'shadeOpacity':.12},{'shadeOpacity':True},{'expectedHeaderRGB':[240,240,240]}):
   self.setUp();self.facts['focusedChrome']['captures'][3]['attempts'][0]['chromePairs'][0].update(changes)
   with self.subTest(changes=changes),self.assertRaisesRegex(ValueError,'actual top/footer shade pixels'):self.verify()
  for header,footer in [([182,182,182,254],[240,240,240,255]),([182,182,182,255],[240,240,240,254])]:
   self.setUp();self.focused_pixels(3,header,footer,.24)
   with self.subTest(header=header,footer=footer),self.assertRaisesRegex(ValueError,'actual top/footer shade pixels'):self.verify()
 def test_raw_report_bytes_and_installed_process_must_match(self):
  self.files['mouse-634-download-widget.json']+=b' '
  with self.assertRaises(ValueError):E['verify'](self.files.__getitem__)
  self.refresh();wrapper=json.loads(self.files['mouse-windows-verification.json']);wrapper['checks']['ownerFeedback634']['pid']=999;self.files['mouse-windows-verification.json']=json.dumps(wrapper).encode()
  with self.assertRaisesRegex(ValueError,'process/report'):E['verify'](self.files.__getitem__)


def load_tests(loader,tests,pattern):
 # Existing required platform workflows run this entrypoint. Keep the new
 # search adversaries in that mandatory suite, not just a local-only script.
 tests.addTests(loader.loadTestsFromTestCase(SEARCH_FIXTURES['SearchEvidence']))
 return tests


if __name__=='__main__':unittest.main()
