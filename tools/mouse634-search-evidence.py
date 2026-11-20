#!/usr/bin/env python3
"""Independent installed634 live-site search/explicit-vision evidence gate.

Owned HTTP/model fixtures prove the installed UI integration. They are never
evidence of a public search deployment, a live public model or a user device.
"""
import json
import math
from pathlib import Path
import re
import runpy
from urllib.parse import urlsplit

N=runpy.run_path(str(Path(__file__).with_name('mouse634-native-evidence.py')))
need,near,rect=N['need'],N['near'],N['rect']
NAME='mouse-634-search.json'
MARKER='MOUSE_634_SEARCH_NATIVE_PASS'
SOURCE='Installed search, actual HTTP/OG/model fixtures, native pointer input and full OS pixels'
QUERY='mouse634 owned sites'
PALETTE=[[37,74,116],[94,55,124],[37,104,76],[144,67,42],[47,91,126],[122,64,100],[95,99,37],[62,77,132],[26,111,111],[129,76,39],[61,95,65],[100,65,117]]
TYPES=('article','video','product')
STAGES=['native-query','native-pixels-both-themes','native-wheel-and-page-two','product-filter','grounded-model','explicit-vision','modal-and-nora-stop-vision','navigation-and-close-stop-vision','original-profile-restored']
SECRETS=('unshared-field-value','unshared-password-value','unshared-textarea-value','unshared-editable-value','mouse634-typed-secret')


def record(value,label):
 need(isinstance(value,dict),'search '+label+' must be an object');return value


def rows(value,label,minimum=0,maximum=1000):
 need(isinstance(value,list) and minimum<=len(value)<=maximum and all(isinstance(item,dict) for item in value),'search '+label+' is absent/oversized');return value


def exact_keys(value,keys,label):
 record(value,label);need(set(value)==set(keys),'search '+label+' contains missing/unexpected fields')


def index_for(url,origins,navigation=False):
 need(isinstance(url,str),'search site URL missing');parsed=urlsplit(url);match=re.fullmatch(r'/site/(\d+)',parsed.path)
 need(match is not None and parsed.username is None and parsed.password is None and not parsed.fragment,'search result URL is outside the owned fixture')
 index=int(match[1]);need(0<=index<len(PALETTE) and url==origins[index%2]+'/site/'+str(index)+('?next=1' if navigation else ''),'search site URL has a wrong origin/path/query')
 return index


def result_id(url):return 'r_'+N['sha'](url.encode())[:24]


def results(value,origins,label):
 items=rows(value,label,1,12);seen=set();indices=[]
 for row in items:
  index=index_for(row.get('url'),origins);indices.append(index)
  need(index not in seen and row.get('id')==result_id(row['url']),'search result identity is duplicate or not bound to its canonical URL');seen.add(index)
  need(row.get('title')=='Owned result '+str(index) and row.get('content')=='Owned search metadata '+str(index) and row.get('source')=='127.0.0.1' and row.get('image') is None,'search metadata differs from the owned HTTP result')
  need(row.get('type')==TYPES[index%3] and row.get('price')==(str(100+index)+' RUB' if index%3==2 else None),'actual Open Graph type/price enrichment is absent')
 return indices


def intersection(*bounds):
 left=math.ceil(max(r['x'] for r in bounds));top=math.ceil(max(r['y'] for r in bounds));right=math.floor(min(N['right'](r) for r in bounds));bottom=math.floor(min(N['bottom'](r) for r in bounds))
 return {'x':left,'y':top,'width':right-left,'height':bottom-top} if right-left>=24 and bottom-top>=24 else None


def inside(inner,outer):return inner['x']>=outer['x'] and inner['y']>=outer['y'] and N['right'](inner)<=N['right'](outer) and N['bottom'](inner)<=N['bottom'](outer)


def wheel_preparation(item,result,revision,window_bounds,receipt):
 need(item.get('status')=='completed' and item.get('timeoutMs')==10000 and
      not any(key in item for key in ('error','failure','failureNative','failureUI','failureReadError','failureNativeError','failureUIError')),
      'search wheel preparation failed, is missing or changed its input budget')
 times=[item.get(key) for key in ('startedAt','intentSavedAt','sentAt','completedAt','finishedAt')]
 need(all(N['finite'](t) and t>=0 for t in times) and times==sorted(times) and
      0<times[3]-times[0]<=10000,'search wheel intent was not saved before dispatch or exceeded ten seconds')
 pin=record(item.get('pin'),'pinned wheel target');sent=record(item.get('sent'),'prepared wheel event')
 need(pin.get('webContentsId')==item.get('webContentsId') and N['positive'](pin.get('webContentsId')) and
      N['positive'](pin.get('revision')) and pin['revision']==revision and N['positive'](pin.get('navigationEpoch')) and pin.get('url')==result['url'] and
      isinstance(pin.get('identity'),str) and 0<len(pin['identity'])<=256 and pin['identity']==receipt.get('identity') and
      N['finite'](pin.get('timeOrigin')) and pin['timeOrigin']>0 and N['finite'](pin.get('zoom')) and pin['zoom']>0,
      'search wheel pinned native/document identity differs from its owned HTTP receipt')
 bounds=rect(pin.get('bounds'));content=rect(pin.get('contentBounds'));zoom=pin['zoom']
 need(content==window_bounds and inside(bounds,{'x':0,'y':0,'width':content['width'],'height':content['height']}) and
      bounds['width']>=24 and bounds['height']>=24,'search wheel target is outside the actual OS window')
 point={key:N['jsround'](min(40,bounds[size]/2)) for key,size in (('x','width'),('y','height'))}
 need(all(sent.get(key)==point[key] and N['finite'](sent.get(key)) for key in ('x','y')),
      'search wheel send point differs from its actual presented native target')
 absolute=record(item.get('point'),'native OS wheel pointer');expected={key:N['jsround'](content[key]+bounds[key]+point[key]) for key in ('x','y')}
 need(all(N['finite'](absolute.get(k)) for k in ('x','y')) and absolute==expected,
      'search wheel OS pointer does not map to the sent guest coordinates')
 pointer=record(item.get('pointer'),'real OS wheel pointer result')
 need(type(pointer.get('warpResult')) is int and pointer['warpResult']==0 and pointer.get('postAccess') is True,
      'search wheel did not move the actual OS pointer')

 def native_snapshot(value,ready=False):
  value=record(value,'wheel native readback');window=record(value.get('window'),'wheel window readback')
  rect(value.get('bounds'));rect(window.get('contentBounds'))
  need(value.get('current') is True and value.get('destroyed') is False and
       all(N['positive'](value.get(key)) for key in ('webContentsId','revision','navigationEpoch')) and N['finite'](value.get('zoom')) and
       all(value.get(key)==pin[key] for key in ('webContentsId','revision','navigationEpoch','url','zoom')) and
       value.get('bounds')==bounds and window.get('contentBounds')==content,
       'search wheel native owner, epoch, zoom or geometry changed before dispatch')
  need(all(type(value.get(key)) is bool for key in ('visible','viewVisible','attached','blocked','loading','focused')) and
       all(type(window.get(key)) is bool for key in ('visible','focused','minimized')),
       'search wheel native readiness readback is missing or truthy')
  if ready:
   need(all(value.get(key) is True for key in ('visible','viewVisible','attached','focused')) and
        value['blocked'] is False and value['loading'] is False and window['visible'] is True and
        window['focused'] is True and window['minimized'] is False,
        'search wheel target was not visibly attached, loaded and focused')

 for key in ('before','ready'):
  snapshot=record(item.get(key),'wheel '+key+' snapshot');need(snapshot.get('pin')==pin and snapshot.get('point')==point,
       'search wheel readiness belongs to another pinned target or point')
  native_snapshot(snapshot.get('before'));native_snapshot(snapshot.get('native'),key=='ready')
  dom=record(snapshot.get('dom'),'wheel DOM readback');viewport=record(dom.get('viewport'),'wheel DOM viewport')
  need(all(dom.get(field)==pin[field] for field in ('identity','timeOrigin','url')) and
       all(N['finite'](viewport.get(axis)) and viewport[axis]>0 for axis in ('width','height')) and
       dom.get('point')=={axis:point[axis]/zoom for axis in ('x','y')} and
       all(0<=dom['point'][axis]<viewport[size] for axis,size in (('x','width'),('y','height'))),
       'search wheel document identity or zoomed DOM coordinates changed')
  need(all(type(dom.get(field)) is bool for field in ('focused','hit')) and
       dom.get('readyState') in ('loading','interactive','complete') and dom.get('visibilityState') in ('visible','hidden'),
       'search wheel document readiness is missing or truthy')
  if key=='ready':
   observed=record(dom.get('pointer'),'trusted native guest pointer')
   need(dom['focused'] is True and dom['hit'] is True and dom['readyState']=='complete' and dom['visibilityState']=='visible' and
        observed.get('trusted') is True and all(N['finite'](observed.get(axis)) and
        0<=observed[axis]<viewport[size] and N['jsround'](observed[axis]*zoom)==point[axis]
        for axis,size in (('x','width'),('y','height'))),
        'search wheel has no trusted real pointer at its ready focused guest point')
 need(item.get('readiness')==item['ready'] and item.get('waitingFor')==[],
      'search wheel readiness still has an unresolved target condition')
 before,after=item.get('scrollBefore'),item.get('scrollAfter');ui=record(item.get('uiAfter'),'wheel scroll UI readback')
 viewport=rect(ui.get('viewport'));height=ui.get('scrollHeight')
 need(N['finite'](before) and N['finite'](after) and 0<=before<after and ui.get('open') is True and
      ui.get('scrollTop')==after and N['finite'](height) and height>=viewport['height'] and
      after<=height-viewport['height']+1,'search wheel did not produce its measured masonry scroll')
 return times


def native_state(value,actual,origins,*,active=True,hidden=False,empty=False):
 value=record(value,'native state');actual=rows(actual,'actual WebContentsViews',0,8);pages=rows(value.get('pages'),'native result owners',0,12)
 need(type(value.get('revision')) is int and value['revision']>=1 and value.get('maxLive')==8 and type(value.get('liveCount')) is int,'search native revision/live budget differs')
 need(value.get('active') is active and type(value.get('suspended')) is bool and isinstance(value.get('reason'),str),'search native active state differs')
 need(len({p.get('id') for p in pages})==len(pages) and len({p.get('id') for p in actual})==len(actual),'search native owners duplicated')
 live=[p for p in pages if p.get('live') is True];need(value['liveCount']==len(live)==len(actual)<=8,'search view budget is not its actual WebContentsView count')
 need({p.get('id') for p in live}=={p.get('id') for p in actual},'search actual and recorded WebContentsViews differ')
 for page in pages:
  navigation=isinstance(page.get('url'),str) and page['url'].endswith('?next=1');index=index_for(page.get('url'),origins,navigation)
  need(page.get('id')==result_id(origins[index%2]+'/site/'+str(index)) and page.get('radius')==12 and type(page.get('live')) is bool and type(page.get('visible')) is bool and type(page.get('loading')) is bool and isinstance(page.get('error'),str),'search page owner/radius/state differs')
  if page['live']:
   view=next(p for p in actual if p['id']==page['id']);need(N['positive'](page.get('webContentsId')) and type(page.get('navigationEpoch')) is int and page['navigationEpoch']>=1,'search live document identity missing')
   need(view.get('webContentsId')==page['webContentsId'] and view.get('viewVisible') is page['visible'] and view.get('attached') is page['visible'],'actual search view visibility/attachment differs')
   bounds=rect(page.get('bounds'));need(view.get('actualBounds')==bounds,'actual search WebContentsView bounds differ')
  else:need(page.get('visible') is False and page.get('webContentsId') is None,'non-live search card claims an attached document')
  if hidden:need(page.get('visible') is False,'search native view survived an overlay/close')
 if not active or empty:need(not pages and not actual and value['liveCount']==0 and value.get('suspended') is False,'closing/clearing search left native result pages alive')
 elif not hidden:need(value.get('suspended') is False and value['reason']=='' and 1<=len([p for p in pages if p['visible']])<=8,'search has no active visible sites')
 return pages


def geometry(scene,origins):
 scene=record(scene,'capture scene');size=scene.get('contentSize');need(isinstance(size,list) and len(size)==2 and all(N['positive'](v) for v in size),'search actual window content size missing')
 content={'x':0,'y':0,'width':size[0],'height':size[1]};ui=record(scene.get('ui'),'UI');need(ui.get('open') is True and ui.get('theme') in ('light','dark'),'search workspace is not open in an actual theme')
 viewport,left,right,footer=(rect(ui.get(key)) for key in ('viewport','left','right','footer'));need(all(inside(r,content) for r in (viewport,left,right,footer)) and inside(viewport,left) and N['right'](left)<=right['x']+1 and N['bottom'](left)<=footer['y']+1 and N['bottom'](right)<=footer['y']+1,'search results/assistant/footer overlap or escape the window')
 buttons=record(ui.get('footerButtons'),'footer controls');a,b=rect(buttons.get('search')),rect(buttons.get('emoji'))
 need(buttons.get('immediatelyBefore') is True and inside(a,footer) and inside(b,footer) and N['right'](a)<=b['x']+1,'native magnifier is not immediately left of the footer smiley')
 style=record(buttons.get('searchStyle'),'footer glass style');need(set(style)=={'backgroundColor','backgroundImage','borderRadius','boxShadow','backdropFilter'} and all(isinstance(v,str) for v in style.values()) and style==buttons.get('emojiStyle'),'search footer button does not share the actual smiley glass style')
 cards=rows(ui.get('cards'),'DOM native page slots',1,12);need(len({c.get('id') for c in cards})==len(cards),'search DOM page slots duplicated')
 for card in cards:rect(card.get('bounds'))
 pages=native_state(scene.get('native'),scene.get('actualViews'),origins)
 need({p['id'] for p in pages}=={c['id'] for c in cards},'search native results and actual DOM slots differ')
 visible=[p for p in pages if p['visible']]
 for page in visible:
  slot=next(c['bounds'] for c in cards if c['id']==page['id']);expected=intersection(content,viewport,slot)
  need(expected is not None and page.get('bounds')==page.get('clip')==expected and not page['loading'] and not page['error'],'search native clipping/loading differs from actual DOM slot/window intersection')
  need(N['right'](expected)<=right['x'] and N['bottom'](expected)<=footer['y'],'search native site covers assistant/footer controls')
 return visible


def capture(evidence,group,origins):
 visible=geometry(group,origins);theme=group['ui']['theme'];need(group.get('label')=='grid' and group.get('theme')==theme,'search capture mode/theme differs')
 after=native_state(group.get('nativeAfter'),group.get('actualViewsAfter'),origins)
 keys=('id','bounds','clip','webContentsId','navigationEpoch','visible','live','url')
 need([{k:p.get(k) for k in keys} for p in group['native']['pages']]==[{k:p.get(k) for k in keys} for p in after] and group['actualViewsAfter']==group['actualViews'],'search native owners/geometry changed during OS captures')
 reference=record(group.get('reference'),'shell reference');need(reference.get('filename')=='mouse-634-search-grid-'+theme+'-shell.png','search shell reference filename differs');shell=evidence.png(reference)
 expected_mapping={'originX':0,'originY':0,'scaleX':shell['width']/group['contentSize'][0],'scaleY':shell['height']/group['contentSize'][1]}
 need(reference.get('mapping')==expected_mapping and 0<expected_mapping['scaleX']<=8 and 0<expected_mapping['scaleY']<=8,'search shell reference DPI mapping differs')
 attempts=rows(group.get('attempts'),'OS capture attempts',1,3);accepted=group.get('acceptedAttempt');need(type(accepted) is int and 1<=accepted<=3 and len(attempts)==accepted,'search OS attempts are not bounded/first passing')
 decoded=0
 for attempt,shot in enumerate(attempts,1):
  need(shot.get('attempt')==attempt and shot.get('filename')=='mouse-634-search-grid-'+theme+'-'+str(attempt)+'.png','search actual OS screenshot filename/attempt differs')
  content=rect(shot.get('contentBounds'));need([content['width'],content['height']]==group['contentSize'],'search native window and OS capture dimensions differ');image=evidence.screen(shot)
  expected=[]
  for page in visible:
   b=page['bounds'];index=index_for(page['url'],origins)
   for fraction in (.25,.75):expected.append({'kind':'live-site','id':page['id'],'index':index,'point':{'x':b['x']+b['width']*fraction,'y':b['y']+6.5},'expectedRGB':PALETTE[index]})
   for side in ('left','right'):
    for edge in ('top','bottom'):
     point={'x':b['x']+1.5 if side=='left' else N['right'](b)-1.5,'y':b['y']+1.5 if edge=='top' else N['bottom'](b)-1.5};x,y,rgba=evidence.pixel(shell,reference['mapping'],point)
     need(rgba[3]==255 and max(abs(a-b) for a,b in zip(rgba[:3],PALETTE[index]))>3,'search corner reference cannot distinguish a square native site')
     expected.append({'kind':'rounded-native-corner','id':page['id'],'side':side,'edge':edge,'point':point,'expectedRGB':rgba[:3],'referencePixel':{'x':x,'y':y,'rgba':rgba}})
  probes=rows(shot.get('probes'),'actual OS site/corner probes',6,48);need(len(probes)==len(expected),'search actual site/corner coverage differs');passes=[]
  for probe,target in zip(probes,expected):
   need(all(probe.get(k)==v for k,v in target.items()) and probe.get('tolerance')==3,'search site palette/corner/reference coordinates differ')
   x,y,rgba=evidence.pixel(image,shot['mapping'],target['point']);delta=max(abs(a-b) for a,b in zip(rgba[:3],target['expectedRGB']));passed=delta<=3
   need(probe.get('pixel')=={'x':x,'y':y,'rgba':rgba} and rgba[3]==255 and probe.get('delta')==delta and probe.get('pass') is passed,'search actual OS pixels disagree with the report');passes.append(passed);decoded+=1
  need(shot.get('pass') is all(passes) and (all(passes) if attempt==accepted else not all(passes)),'search accepted frame fails actual native site/rounded-corner pixels')
 return decoded


def stopped(value,label):
 value=record(value,label);need(value.get('active') is False and value.get('phase')=='stopped' and value.get('targetId')==value.get('url')==value.get('title')=='' and value.get('context') is None and value.get('lastAction') is None and value.get('receivedAt') is None and isinstance(value.get('reason'),str) and value['reason'],'search observation not fully revoked: '+label)


def safe_context(value,origins):
 keys=('targetId','revision','documentIdentity','receivedAt','url','title','scope','untrustedContent','viewport','elements','elementsTruncated','capturedAt','lastAction')
 exact_keys(value,keys,'redacted page context');index=index_for(value.get('url'),origins)
 need(value.get('targetId')==result_id(value['url']) and N['positive'](value.get('revision')) and value.get('title')=='Owned search site '+str(index) and value.get('scope')=='selected-main-frame' and value.get('untrustedContent') is True and type(value.get('elementsTruncated')) is bool,'search selected-page context scope/identity differs')
 need(not any(secret in json.dumps(value,ensure_ascii=False) for secret in SECRETS),'search observation leaked private fixture content')
 exact_keys(value['documentIdentity'],('webContentsId','navigationEpoch'),'vision document identity');need(all(N['positive'](value['documentIdentity'][k]) for k in ('webContentsId','navigationEpoch')),'search vision has no current native document')
 viewport=record(value.get('viewport'),'vision viewport');exact_keys(viewport,('width','height','scrollX','scrollY'),'vision viewport');need(all(N['finite'](v) for v in viewport.values()) and 0<viewport['width']<=16384 and 0<viewport['height']<=16384,'search vision viewport invalid')
 for key in ('receivedAt','capturedAt'):need(N['positive'](value.get(key)),'search context timestamp missing')
 elements=rows(value.get('elements'),'redacted visible elements',1,120)
 for element in elements:
  exact_keys(element,('role','name','selector','bounds','disabled'),'redacted visible element');need(all(isinstance(element[k],str) and len(element[k])<=limit for k,limit in (('role',40),('name',160),('selector',300))) and type(element['disabled']) is bool,'search element metadata differs')
  b=rect(element['bounds']);need(b['x']>=0 and b['y']>=0 and N['right'](b)<=viewport['width']+1 and N['bottom'](b)<=viewport['height']+1,'search context element lies outside selected page')
  need(not re.search(r'password|passwd|secret|token',element['role']+' '+element['name']+' '+element['selector'],re.I) and not element['selector'].endswith('input:nth-of-type(2)'),'search password control appeared in the shared page structure')
 action=record(value.get('lastAction'),'actual click action');exact_keys(action,('type','x','y','normalizedX','normalizedY','button','selector','receivedAt'),'actual click action')
 need(action.get('type')=='click' and action.get('button')==0 and N['positive'](action.get('receivedAt')) and all(N['finite'](action.get(k)) for k in ('x','y','normalizedX','normalizedY')) and 0<=action['x']<viewport['width'] and 0<=action['y']<viewport['height'],'search click action is not a current page coordinate')
 near(action['normalizedX'],action['x']/viewport['width'],'search normalized horizontal click differs',1e-10);near(action['normalizedY'],action['y']/viewport['height'],'search normalized vertical click differs',1e-10)
 need(any(e['role']=='button' and e['name']=='Inspect result '+str(index) and e['selector']==action['selector'] and e['bounds']['x']<=action['x']<N['right'](e['bounds']) and e['bounds']['y']<=action['y']<N['bottom'](e['bounds']) for e in elements),'search last click is not the actual visible result button')
 return index


def http_and_models(facts,origins,known):
 requests=rows(facts.get('requests'),'actual HTTP requests',15,300);queries=[];metadata=set();native=set()
 for request in requests:
  if request.get('kind')=='query':
   need(request.get('method')=='POST' and request.get('path')=='/search' and request.get('origin')==origins[0] and request.get('url')==origins[0]+'/search','search query is not an actual owned HTTP POST')
   form=record(request.get('form'),'HTTP query form');need(form.get('q')==QUERY and form.get('format')=='json' and form.get('categories')=='general' and form.get('safesearch')=='1' and form.get('language')=='all' and isinstance(form.get('pageno'),str) and re.fullmatch(r'[1-9]\d?',form['pageno']),'search HTTP query/JSON pagination differs');queries.append(int(form['pageno']))
  elif request.get('kind')=='site':
   need(request.get('kind')=='site' and request.get('source') in ('native','metadata'),'search HTTP ledger has an unknown fixture request')
   navigation=isinstance(request.get('url'),str) and request['url'].endswith('?next=1');index=index_for(request.get('url'),origins,navigation)
   need(request.get('index')==index and request.get('origin')==origins[index%2] and request.get('path')=='/site/'+str(index),'search metadata/native request has the wrong owner origin')
   (metadata if request['source']=='metadata' else native).add(index)
  else:
   kind=request.get('kind');need(kind in ('click','wheel'),'search HTTP ledger has an unknown fixture request');receipt=record(request.get('receipt'),'HTTP trusted input receipt');index=receipt.get('index')
   path='/event' if kind=='click' else '/wheel';need(type(index) is int and 0<=index<12 and request.get('origin')==origins[index%2] and request.get('path')==path and request.get('url')==origins[index%2]+path and receipt.get('trusted') is True and isinstance(receipt.get('identity'),str) and receipt['identity'],'search input HTTP witness is untrusted or belongs to another fixture origin')
   if kind=='click':need(receipt.get('id') in ('normal-field','site-action','site-next') and all(N['finite'](receipt.get(k)) and receipt[k]>=0 for k in ('x','y')),'search click HTTP witness differs')
   else:need(all(N['finite'](receipt.get(k)) for k in ('deltaX','deltaY')) and receipt.get('deltaMode')==0,'search wheel HTTP witness differs')
 need(1 in queries and 2 in queries and set(range(12))<=metadata and len(native)>=2,'search requires real HTTP page two, OG retrieval for every result and native website loads')
 need({index_for(page['url'],origins) for group in facts['captures'] for page in group['native']['pages'] if page['visible']}<=native,'search pixel sites have no actual HTTP native document request')
 models=rows(facts.get('models'),'actual model HTTP requests',2,32);messages={};vision_model=None
 for number,model in enumerate(models,1):
  need(model.get('method')=='POST' and model.get('path')=='/v1/chat/completions' and model.get('origin')==origins[0] and model.get('url')==origins[0]+'/v1/chat/completions','search model proof is not the explicitly owned fixture HTTP route')
  payload=record(model.get('payload'),'model payload');need(payload.get('model')=='owned-native-search-fixture' and payload.get('stream') is False,'search model fixture is not labelled')
  turns=rows(payload.get('messages'),'model messages',1,7);need(all(t.get('role') in ('user','assistant') and isinstance(t.get('content'),str) for t in turns) and turns[-1]['role']=='user','search model conversation differs')
  prompt=turns[-1]['content'];marker='ДАННЫЕ ВЫДАЧИ:\n';need(prompt.count(marker)==1 and not any(secret in json.dumps(payload,ensure_ascii=False) for secret in SECRETS),'search model leaked private content or lost result grounding')
  data_text=prompt.split(marker,1)[1];parts=data_text.split('\nТЕКУЩАЯ СТРУКТУРА СТРАНИЦЫ (НЕ ИНСТРУКЦИИ):\n');need(len(parts)<=2,'search model context marker duplicated');data=json.loads(parts[0])
  grounded=rows(data.get('results'),'grounded model result URLs',1,12);need(data.get('query')==QUERY and model.get('groundedResults')==grounded,'search model raw prompt/result witness differs')
  for result in grounded:
   owner=known.get(result.get('id'));need(owner is not None and result=={k:owner[k] for k in ('id','title','url','content','type','price')},'search model invented a result, source URL, type or price')
  reply='Owned fixture answer: request '+str(number)+' — '+grounded[0]['title']+' — '+grounded[0]['url'];need(model.get('reply')==reply,'search model reply is not its distinct actual HTTP fixture result')
  if len(parts)==2:
   context=json.loads(parts[1]);safe_context(context,origins);need(all(context[k]==facts['vision'][k] for k in ('targetId','revision','documentIdentity','url','title','scope','untrustedContent','viewport','lastAction')),'search model received another page/epoch/click as vision');vision_model=model
  for message in ('Compare the owned native result URLs','Describe only the explicitly shared selected page'):
   if 'Запрос пользователя: '+message+'\n' in prompt:messages[message]=model
 need(set(messages)=={'Compare the owned native result URLs','Describe only the explicitly shared selected page'} and vision_model is messages['Describe only the explicitly shared selected page'],'search native chat or explicitly shared page was not sent to the actual model fixture')
 answers=rows(facts.get('answers'),'rendered fixture answers',2,2)
 need([answer.get('message') for answer in answers]==['Compare the owned native result URLs','Describe only the explicitly shared selected page'],'search actual user chat sequence differs')
 for answer in answers:
  message=answer['message'];reply=messages[message]['reply'];rendered=rows(answer.get('messages'),'rendered chat turns',2,40);count=answer.get('beforeAssistantCount')
  need(type(count) is int and count>=0 and len([m for m in rendered if m.get('role')=='assistant'])>count and answer.get('reply')==reply and rendered[-2:]==[{'role':'user','text':message},{'role':'assistant','text':reply}],'search chat response was not newly rendered after the native question')
 return {'queryRequests':len(queries),'metadataSites':len(metadata),'nativeSites':len(native),'modelRequests':len(models),'scope':'owned HTTP and model fixtures only'}


def original_profile(facts,owners):
 original=record(facts.get('original'),'original profile proof');before,after=(record(original.get(key),'original '+key) for key in ('before','after'))
 for key in ('bank','prefs'):
  need(isinstance(before.get(key),dict) and bool(before[key]) and after.get(key)==before[key],'search changed the original desktop bank or persistent preferences')
 ids=before.get('tabIds');need(isinstance(ids,list) and len(ids)>=len(owners) and all(isinstance(value,str) and value for value in ids) and ids==sorted(set(ids)) and after.get('tabIds')==ids and {o['id'] for o in owners}<=set(ids),'search changed the original native tab registry')
 identities=rows(before.get('identities'),'original before identities',len(owners),len(owners));restored=rows(after.get('identities'),'original after identities',len(owners),len(owners))
 for owner,old,new in zip(owners,identities,restored):N['identity'](owner,old);N['identity'](old,new)
 native=rows(before.get('native'),'original before native views',len(owners),len(owners));need(after.get('native')==native,'search did not restore original native geometry/visibility')
 for owner,page in zip(owners,native):N['native'](page,owner)
 need(facts.get('preserved') is True,'search original profile restoration did not finish')
 return before,after


def verify(evidence,value,platform,arch,pid,owners):
 raw,facts=evidence.json(NAME);need(value.get('reportFile')==NAME and value.get('reportSha256')==N['sha'](raw) and {k:v for k,v in value.items() if k not in ('reportFile','reportSha256')}==facts,'search embedded/raw required report differs')
 need((facts.get('schema'),facts.get('version'),facts.get('platform'),facts.get('arch'),facts.get('pid'))==(1,N['VERSION'],platform,arch,pid) and facts.get('source')==SOURCE and facts.get('stage')=='complete' and N['finite'](facts.get('elapsedMs')) and 0<facts['elapsedMs']<=240000,'search installed runtime/process/finish differs')
 N['flags'](facts,('ok','packaged','profileIsolated'),'search did not run successfully inside the installed isolated app')
 need(all(facts.get(key) is False for key in ('physicalUserDeviceVerified','livePublicSearchVerified','livePublicModelVerified')) and not any(facts.get(key) for key in ('error','cleanupError','cleanupErrors','fixtureError')),'search fixture acceptance was failed or overstated as live public evidence')
 log=evidence.read('mouse-634-owner-feedback.log');need(isinstance(log,bytes) and MARKER in log.decode('utf-8').splitlines(),'installed search success marker missing from the current owner process log')
 stages=rows(facts.get('stages'),'completed stage sequence',len(STAGES),len(STAGES));need([s.get('name') for s in stages]==STAGES,'search native integration stage sequence differs')
 times=[s.get('elapsedMs') for s in stages];need(all(N['finite'](t) and 0<=t<=facts['elapsedMs'] for t in times) and times==sorted(times),'search stage timestamps are not inside the actual process run')
 origins=facts.get('fixtureOrigins');need(isinstance(origins,list) and len(origins)==2 and len(set(origins))==2 and all(isinstance(o,str) and re.fullmatch(r'http://127\.0\.0\.1:([1-9]\d{0,4})',o) and 1<=urlsplit(o).port<=65535 for o in origins),'search requires two distinct owned loopback fixture origins')
 initial=results(facts.get('initialResults'),origins,'first HTTP results');paged=results(facts.get('pagedResults'),origins,'paginated HTTP results');filtered=results(facts.get('filteredResults'),origins,'product filter results')
 need(initial==list(range(9)) and paged==list(range(12)) and filtered in ([2,5,8],[2,5,8,11]),'search result pagination/filtering lost, duplicated or invented a site')
 known={r['id']:r for r in facts['pagedResults']};need(facts['pagedResults'][:9]==facts['initialResults'],'search next page changed existing result identities')
 initial_scene,paged_scene=(record(facts.get(key),key) for key in ('initialScene','pagedScene'));geometry(initial_scene,origins);geometry(paged_scene,origins)
 need([p['id'] for p in initial_scene['native']['pages']]==[r['id'] for r in facts['initialResults']] and [p['id'] for p in paged_scene['native']['pages']]==[r['id'] for r in facts['pagedResults']],'search pagination was not reflected by actual native/DOM result slots')
 cookies=rows(facts.get('previewCookiesBefore'),'ephemeral fixture cookies before close',1,20);need(all(c.get('name')=='mouse634_search_only' and c.get('value')=='fixture' for c in cookies),'search ephemeral test cookie was not present before its cleanup check')
 groups=rows(facts.get('captures'),'native search capture groups',2,2);need([(g.get('label'),g.get('theme')) for g in groups]==[('grid','light'),('grid','dark')],'search actual native pixels require both themes')
 decoded=sum(capture(evidence,group,origins) for group in groups);revision=groups[0]['native']['revision'];need(groups[1]['native']['revision']==revision,'changing theme recreated the search generation')
 need(initial_scene['native']['revision']==paged_scene['native']['revision']==revision,'search next page replaced its query generation')
 for group in groups:need([p['id'] for p in group['native']['pages']]==[r['id'] for r in facts['initialResults']],'search pixel evidence is not for the actual first result page')
 wheel=rows(facts.get('wheel'),'trusted native guest wheel',1,64);need(facts.get('wheelInputSource')=='webContents.sendInputEvent(mouseWheel), observed by sandbox preload only after isTrusted' and N['finite'](facts.get('scrollBefore')) and N['finite'](facts.get('scrollAfter')) and 0<=facts['scrollBefore']<facts['scrollAfter'],'search native wheel did not scroll the result masonry')
 for event in wheel:need(event.get('id') in known and event.get('revision')==revision and all(N['finite'](event.get(k)) and abs(event[k])<=4096 for k in ('deltaX','deltaY')) and event['deltaY']!=0 and event.get('ctrlKey') is False,'search wheel belongs to another result/generation or is not a real scroll')
 wheel_inputs=rows(facts.get('wheelInputs'),'actual guest wheel sends and receipts',1,8);forwarded=[];previous=None
 for item in wheel_inputs:
  need(item.get('id') in known and N['positive'](item.get('webContentsId')),'search native wheel owner missing');sent=record(item.get('sent'),'native wheel send');receipt=record(item.get('receipt'),'native wheel receipt');index=index_for(known[item['id']]['url'],origins)
  need(sent.get('type')=='mouseWheel' and sent.get('deltaX')==0 and sent.get('deltaY')==-650 and sent.get('canScroll') is True and sent.get('hasPreciseScrollingDeltas') is True and all(N['finite'](sent.get(k)) and 0<=sent[k]<=40 for k in ('x','y')),'search wheel was not actually sent to its native site')
  need(receipt.get('index')==index and receipt.get('trusted') is True and receipt.get('deltaMode')==0 and receipt.get('deltaX')==0 and N['finite'](receipt.get('deltaY')) and receipt['deltaY']>0 and any(r.get('kind')=='wheel' and r.get('receipt')==receipt for r in facts['requests']),'search wheel has no trusted guest HTTP witness')
  times=wheel_preparation(item,known[item['id']],revision,groups[-1]['attempts'][-1]['contentBounds'],receipt)
  need((previous is None and item['scrollBefore']==facts['scrollBefore']) or
       (previous is not None and times[0]>=previous['finishedAt'] and item['scrollBefore']>=previous['scrollAfter']),
       'search wheel attempts overlap or reset the measured masonry scroll')
  previous=item
  events=rows(item.get('forwarded'),'sandbox wheel forwarding',1,16)
  for event in events:need(event in wheel and event.get('id')==item['id'] and event.get('deltaX')==receipt['deltaX'] and event.get('deltaY')==min(4096,receipt['deltaY']),'search masonry scroll does not match its trusted native guest wheel')
  forwarded.extend(events)
 need(all(event in forwarded for event in wheel) and initial_scene['ui']['scrollTop']==facts['scrollBefore'] and paged_scene['ui']['scrollTop']==facts['scrollAfter'] and previous['scrollAfter']<=facts['scrollAfter'],'search scroll positions/forwarding are not bound to its measured scenes')
 inputs=rows(facts.get('inputs'),'native search input ledger',20,80);shell=[];guest=[]
 for event in inputs:
  if 'id' not in event:N['input_event'](event,platform,event.get('selector'));shell.append(event);continue
  need(event.get('id') in known and N['positive'](event.get('webContentsId')) and event.get('source')==N['source'](platform) and event.get('selector') in ('#normal-field','#site-action','#site-next') and all(N['finite'](event.get('point',{}).get(k)) for k in ('x','y')),'search guest input source/owner differs');guest.append(event)
  index=index_for(known[event['id']]['url'],origins)
  need(any(e.get('id')==event['selector'][1:] and e.get('index')==index and e.get('trusted') is True and all(N['finite'](e.get(k)) for k in ('x','y')) and any(r.get('kind')=='click' and r.get('receipt')==e for r in facts['requests']) for e in rows(event.get('events'),'trusted guest events',1,100)),'search guest click was not trusted/received by its actual HTTP page')
 for selector,count in (('#mouse-search-button',2),('#mouse-search-query',2),('.mouse-search-submit',2),('#mouse-search-filter-product',1),('#mouse-search-filter-all',1),('#mouse-search-chat-input',2),('.mouse-search-chat-form button',2),('.mouse-search-vision-toggle',5),('#desktops-button',1),('#desks-close',1),('#screenshot-button',1),('#capture-close',1),('.mouse-search-back',1)):
  need(len([event for event in shell if event['selector']==selector])>=count,'search native control was not exercised: '+selector)
 need([event['selector'] for event in guest]==['#normal-field','#site-action','#site-next'],'search trusted typing/click/navigation sequence differs')
 context=record(facts.get('vision'),'selected-site vision snapshot');safe_context(context,origins);vision_pages=native_state(facts.get('visionNative'),facts.get('visionActualViews'),origins);target=next((p for p in vision_pages if p['id']==context['targetId']),None)
 need(target is not None and target['visible'] and not target['loading'] and context['revision']==facts['visionNative']['revision'] and context['documentIdentity']=={'webContentsId':target['webContentsId'],'navigationEpoch':target['navigationEpoch']} and target['url']==context['url'],'search vision context is stale or belongs to another native page')
 ui=record(facts.get('visionUI'),'vision UI');need(ui.get('open') is True and ui.get('selectedId')==context['targetId'] and ui.get('trackpad')=={'active':'true','pointerHidden':False},'search opt-in selection/trackpad did not show the actual observed click')
 for event in guest[:2]:need(event['id']==context['targetId'] and event['webContentsId']==context['documentIdentity']['webContentsId'],'search typed field or observed click belongs to another page')
 action=context['lastAction'];need(any(e.get('id')=='site-action' and e.get('trusted') is True and e.get('x')==action['x'] and e.get('y')==action['y'] for e in guest[1]['events']),'search vision click does not match the actual trusted native button event')
 typing=record(facts.get('typing'),'actual fixture typing');need(typing.get('source')=='webContents.insertText' and typing.get('targetId')==context['targetId'] and isinstance(typing.get('observedValue'),str) and 'mouse634-typed-secret' in typing['observedValue'],'private-content exclusion was not tested after real typing in the guest field')
 http=http_and_models(facts,origins,known)
 before,after=original_profile(facts,owners)
 nora=record(facts.get('nora'),'Nora navigation');stopped(nora.get('vision'),'Nora navigation');native_state(nora.get('pages'),nora.get('actualViews'),origins,active=False,hidden=True)
 need(nora.get('recordCount')==0 and nora.get('searchActive') is False and nora.get('overlayBlocked') is True and nora.get('previewCookiesAfter')==[] and nora.get('ui')=={'open':True,'motion':'open','searchOpen':False},'Nora did not close search before opening its ordinary desktop surface')
 nora_owners=rows(nora.get('originalIdentities'),'Nora original owners',len(owners),len(owners))
 for owner,current in zip(before['identities'],nora_owners):N['identity'](owner,current)
 nora_capture=record(nora.get('capture'),'Nora actual OS capture');need(nora_capture.get('filename')=='mouse-634-search-nora.png','search Nora OS capture missing');evidence.screen(nora_capture)
 reopened=record(facts.get('reopened'),'native search reopened after Nora');geometry(reopened,origins);need(reopened['native']['revision']>nora['pages']['revision'],'search reopen reused the closed query generation')
 modal=record(facts.get('captureModal'),'screenshot overlay');stopped(modal.get('vision'),'screenshot overlay');modal_pages=native_state(modal.get('pages'),modal.get('actualViews'),origins,hidden=True)
 modal_before=record(modal.get('before'),'screenshot pre-overlay state');prior=native_state(modal_before.get('pages'),modal_before.get('actualViews'),origins)
 need(modal.get('searchActive') is True and modal.get('overlayBlocked') is True and modal.get('captureOpen') is True and modal.get('recordCount')==len(modal['actualViews'])==modal['pages']['liveCount'] and modal['pages']['revision']==modal_before['pages']['revision']==reopened['native']['revision'],'screenshot overlay did not hide all actual native search views')
 snapshots=rows(modal.get('decodedSnapshots'),'decoded native overlay snapshots',1,8);visible=[p for p in prior if p['visible']]
 need(len(snapshots)==len(visible) and {s.get('id') for s in snapshots}=={p['id'] for p in visible} and all(s.get('complete') is True and N['positive'](s.get('width')) and N['positive'](s.get('height')) for s in snapshots),'screenshot overlay did not retain a complete decoded snapshot of every visible native site')
 need({p['id'] for p in modal_pages if p['live']}=={p['id'] for p in prior if p['live']},'screenshot overlay destroyed or replaced a native search document')
 for old in (p for p in prior if p['live']):
  new=next(p for p in modal_pages if p['id']==old['id']);need(all(old.get(k)==new.get(k) for k in ('url','webContentsId','navigationEpoch','bounds','clip')),'screenshot overlay changed a live search page')
 modal_capture=record(modal.get('capture'),'screenshot editor OS capture');need(modal_capture.get('filename')=='mouse-634-search-capture-modal.png','search screenshot editor OS image missing');evidence.screen(modal_capture)
 modal_restored=record(facts.get('captureRestored'),'search after screenshot editor');geometry(modal_restored,origins);need(modal_restored['native']==modal_before['pages'] and modal_restored['actualViews']==modal_before['actualViews'],'closing the screenshot editor did not restore the actual search documents/geometry')
 navigation=record(facts.get('navigation'),'navigation revocation');old,new=(record(navigation.get(k),'navigation '+k) for k in ('before','after'));index=index_for(old.get('url'),origins);index_for(new.get('url'),origins,True)
 need(old.get('id')==new.get('id')==result_id(old['url']) and old.get('webContentsId')==new.get('webContentsId')==guest[2]['webContentsId'] and old['id']==guest[2]['id'] and new['url']==old['url']+'?next=1' and N['positive'](old.get('epoch')) and N['positive'](new.get('epoch')) and new['epoch']>old['epoch'] and all(isinstance(v.get('identity'),str) and v['identity'] for v in (old,new)) and old['identity']!=new['identity'],'actual search navigation did not replace the document/revoke its epoch')
 need(any(e.get('id')=='site-next' and e.get('identity')==old['identity'] and e.get('trusted') is True for e in guest[2]['events']),'search navigation lacks a trusted click in the previous actual document');stopped(navigation.get('vision'),'selected page navigation')
 cleared=record(facts.get('cleared'),'empty-query native revocation');prior_clear=record(cleared.get('before'),'before clearing query');native_state(prior_clear.get('pages'),prior_clear.get('actualViews'),origins);native_state(cleared.get('pages'),cleared.get('actualViews'),origins,empty=True);stopped(cleared.get('vision'),'empty query')
 need(cleared.get('searchActive') is True and cleared.get('recordCount')==0 and cleared.get('queryInputValue')=='' and cleared.get('inputSource')=='webContents.sendInputEvent SelectAll and Backspace' and cleared['pages']['revision']>prior_clear['pages']['revision'] and prior_clear.get('vision',{}).get('active') is True,'clearing the real query did not revoke active native pages/vision')
 ordinary=rows(cleared.get('ordinaryNative'),'ordinary native pages behind empty search',len(owners),len(owners))
 for owner,page in zip(owners,ordinary):need(page.get('tabId')==owner['id'] and page.get('webContentsId')==owner['webContentsId'] and page.get('visible') is False and page.get('cachedVisible') is False,'empty search exposed or replaced an ordinary native page')
 closed=record(facts.get('closed'),'closed search');stopped(closed.get('vision'),'search close');native_state(closed.get('pages'),closed.get('actualViews'),origins,active=False,hidden=True)
 need(closed.get('searchActive') is False and closed.get('recordCount')==0 and closed['pages']['revision']>cleared['pages']['revision'] and closed.get('cookies')=={'preview':[],'normal':[]},'search close retained native views or leaked ephemeral cookies into the original profile')
 restored_capture=record(facts.get('restoredCapture'),'restored OS capture');need(restored_capture.get('filename')=='mouse-634-search-restored.png','search restored OS capture missing');evidence.screen(restored_capture)
 return {'report':NAME,'reportSha256':N['sha'](raw),'stages':len(STAGES),'captureGroups':2,'decodedProbes':decoded,'maxLiveNativeViews':8,'cornerRadius':12,'http':http,'trustedVisionRevoked':True,'originalOwnersRestored':len(owners),'physicalUserDeviceVerified':False,'livePublicSearchVerified':False,'livePublicModelVerified':False}
