#!/usr/bin/env python3
"""Synthetic contracts only: these fixtures are never live engine evidence."""
import copy
from datetime import datetime,timezone
from html import escape
import json
from functools import lru_cache
from pathlib import Path
import runpy
import struct
import unittest
from urllib.parse import quote
import zlib

HERE=Path(__file__).parent
C=runpy.run_path(str(HERE/'mouse635-public-search-evidence.py'))
L=runpy.run_path(str(HERE/'test_mouse635_library_evidence.py'))
sha=C['sha']
encode=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n').encode()
BASE=1795255200000


def png_image(image):
 def chunk(kind,raw):return struct.pack('>I',len(raw))+kind+raw+struct.pack('>I',zlib.crc32(kind+raw)&0xffffffff)
 width,height,channels=image['width'],image['height'],image['channels'];stride=width*channels
 data=b''.join(b'\0'+image['pixels'][y*stride:(y+1)*stride] for y in range(height))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6 if channels==4 else 2,0,0,0))+chunk(b'IDAT',zlib.compress(data))+chunk(b'IEND',b'')


def bitmap(width,height,color):
 return {'width':width,'height':height,'channels':4,'pixels':bytes(channel for y in range(height) for x in range(width) for channel in color(x,y))}


def pattern(x,y):
 return ([24,48,96],[180,72,40],[64,164,88],[208,184,64],[120,64,176])[(x//12+y//12)%5]+[255]


@lru_cache(maxsize=32)
def scene(x=0,y=0,width=256,height=192):
 image=bitmap(width,height,lambda px,py:pattern(x+px,y+py));return image,png_image(image)


def native_capture(raw,name,blank=False):
 window=bitmap(256,192,lambda x,y:[255,255,255,255]) if blank else scene()[0]
 display=bitmap(258,194,lambda x,y:(list(window['pixels'][((y-1)*256+x-1)*4:((y-1)*256+x-1)*4+4]) if 1<=x<257 and 1<=y<193 else [12,18,24,255]))
 a,b=png_image(window),png_image(display);raw[name]=a;raw[name[:-4]+'-display.png']=b
 return {'filename':name,'displayFilename':name[:-4]+'-display.png','source':'globalCapture.acquire(display)','backend':'unit-native-frame-fixture','bytes':len(a),'sha256':sha(a),'displaySha256':sha(b),'pixelSize':{'width':256,'height':192},'screenPixelSize':{'width':258,'height':194},'display':{'bounds':{'x':0,'y':0,'width':258,'height':194}},'contentBounds':{'x':1,'y':1,'width':256,'height':192},'cropPixels':{'x':1,'y':1,'width':256,'height':192},'mapping':{'scaleX':1,'scaleY':1,'originX':0,'originY':0}}


def paint_fixture(raw,frame,kind,capture,start):
 before=frame['before'];subjects=[{'id':'source','webContentsId':before['webContentsId'],'bounds':before['bounds']}] if kind=='source' else before['pages'];left=[];right=[];comparisons=[]
 for index,page in enumerate(subjects,1):
  bounds=page['bounds'];decoded=[]
  for suffix,rows in [('before',left),('after',right)]:
   image,data=scene(bounds['x'],bounds['y'],bounds['width'],bounds['height']);filename='mouse-635-public-search-'+kind+'-reference-01-'+str(index).zfill(2)+'-'+suffix+'.png';raw[filename]=data;decoded.append(image)
   rows.append({key:copy.deepcopy(page[key]) for key in ('id','webContentsId','bounds')}|{'image':{'source':'WebContents.capturePage','filename':filename,'bytes':len(data),'sha256':sha(data),'pixelSize':{'width':image['width'],'height':image['height']}}})
  comparisons.append({'id':page['id'],'webContentsId':page['webContentsId'],**C['compare_paint'](*decoded,scene()[0],bounds,capture['mapping'])})
 attempt={'sequence':1,'startedAt':start+1,'finishedAt':start+90,'elapsedMs':89,'before':before,'referencesBefore':left,'capture':capture,'referencesAfter':right,'after':frame['after'],'comparisons':comparisons,'accepted':True}
 frame['paint']={'source':C['PAINT_SOURCE'],'budgetMs':4500,'maxFrames':20,'startedAt':start,'deadline':start+4500,'finishedAt':start+100,'elapsedMs':100,'acceptedIndex':0,'attempts':[attempt]}


def document(engine,query,values):
 rows=[];fragments=[]
 for index,value in enumerate(values):
  title,content,url=value['title'],value['content'],value['url'];href=escape(url,quote=True);t=escape(title);c=escape(content)
  if engine=='bing':
   fragment='<li class="b_algo"><h2><a href="'+href+'">'+t+'</a></h2><div class="b_caption"><p>'+c+'</p></div></li>'
   link_path=title_path=[0,0];snippet_path=[1,0];snippet='.b_caption p';wrapper='ol id="b_results"'
  elif engine=='google':
   fragment='<div class="g"><a href="'+href+'"><h3>'+t+'</h3></a><div class="VwiC3b">'+c+'</div></div>'
   link_path=[0];title_path=[0,0];snippet_path=[1];snippet='.VwiC3b';wrapper='div id="search"'
  elif engine=='duckduckgo':
   fragment='<article data-testid="result"><h2><a data-testid="result-title-a" href="'+href+'">'+t+'</a></h2><div data-testid="result-snippet">'+c+'</div></article>'
   link_path=title_path=[0,0];snippet_path=[1];snippet='[data-testid="result-snippet"]';wrapper='div id="links"'
  else:
   fragment='<li class="serp-item"><h2><a class="OrganicTitle-Link" href="'+href+'">'+t+'</a></h2><div class="OrganicTextContentSpan">'+c+'</div></li>'
   link_path=title_path=[0,0];snippet_path=[1];snippet='.OrganicTextContentSpan';wrapper='ul id="search-results"'
  fragments.append(fragment)
  rows.append({'rank':index+1,'title':title,'url':url,'rawHref':url,'content':content,'selector':C['SELECTORS'][engine],'snippetSelector':snippet,'containerPath':[1,0,index],'linkPath':link_path,'titlePath':title_path,'snippetPath':snippet_path,'bounds':{'x':20,'y':50+index*120,'width':500,'height':24},'rendered':True,'inViewport':True,'rawOuterHTML':fragment,'fragmentTruncated':False})
 if not values:wrapper='div id="empty"'
 html='<html><head><title>'+escape(query)+'</title></head><body><'+wrapper+'>'+''.join(fragments)+'</'+wrapper.split(' ')[0]+'></body></html>'
 return html,rows


def fixture(platform='linux',arch='x64',engine='bing',owner_results=2):
 raw={};sources=[];receipts=[];inputs=[]
 def native(selector,at):
  events=[{'type':'click','trusted':True,'matches':True}]
  item={'selector':selector,'source':{'darwin':'CGEvent','win32':'User32','linux':'XTest'}[platform],'point':{'x':1,'y':1},'at':BASE+at,'navigates':False,'events':events};inputs.append(item);return item
 native('#mouse-search-button',1);opener=native('.mouse-search-engine',2);choice=native('#choice-dialog button[data-value="'+engine+'"]',3)
 registry=[{'id':key,'name':value['name']} for key,value in C['ENGINES'].items()]
 original='google' if engine!='google' else 'bing';setting={'engine':engine,'name':C['ENGINES'][engine]['name'],'private':False,'engines':registry}
 cases=[]
 for index,(name,query,topic) in enumerate(C['CASES']):
  start=100+index*3000;request='ui-'+name
  values=[{'url':'https://www.anthropic.com/news','title':'Anthropic news','content':'Actual Anthropic source text'},{'url':'https://www.anthropic.com/claude','title':'Claude from Anthropic','content':'A second original organic result'}] if index==0 else [{'url':'https://docs.python.org/3/','title':'Python documentation','content':'The Python language reference'},{'url':'https://pypi.org/','title':'Python Package Index','content':'Python packages'}]
  if index==0:values=values[:owner_results]
  html,rows=document(engine,query,values);url=C['ENGINES'][engine]['base']+quote(query,safe="~!*'()-._")
  results=[{'id':C['canonical_id'](row['url']),'url':row['url'],'title':row['title'],'content':row['content'],'image':None,'type':'article','price':None,'source':__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(row['url']).hostname} for row in rows]
  iso=lambda at:datetime.fromtimestamp((BASE+at)/1000,timezone.utc).isoformat()
  receipt={'schema':1,'kind':'native-serp','requestId':request,'engine':engine,'engineName':setting['name'],'private':False,'query':query,'page':1,'filter':'all','project':'normal','desk':'d1','requestedURL':url,'finalURL':url,'webContentsId':100+index,'navigationEpoch':1,'preference':{key:setting[key] for key in ('engine','name','private')},'startedAtISO':iso(start+10),'finishedAtISO':iso(start+1010),'elapsedMs':1000,'navigation':[{'event':'start','url':url,'at':start+20,'epoch':1},{'event':'commit','url':url,'at':start+100,'epoch':1},{'event':'dom-ready','url':url,'at':start+110,'epoch':1}],
   'snapshot':{'schema':1,'engine':engine,'documentURL':url,'documentTitle':query,'documentReadyState':'complete','visibilityState':'hidden','viewport':{'width':1100,'height':800},'extractedAtISO':iso(start+1000),'rows':rows,'next':None,'challenge':'','empty':False,'bodyExcerpt':'','html':html,'htmlLength':C['jslen'](html),'htmlTruncated':False},'htmlBytes':len(html.encode()),'htmlSha256':sha(html.encode()),'organicSignature':C['signature'](rows),'results':results,'ok':True,'outcome':'results'}
  filename='mouse-635-serp-'+str(index+1).zfill(3)+'.json';raw[filename]=encode(receipt);receipts.append(receipt);sources.append({'sequence':index+1,'filename':filename,'bytes':len(raw[filename]),'sha256':sha(raw[filename]),'requestId':request,'engine':engine,'query':query,'page':1,'outcome':'results'})
  reply={'query':query,'page':1,'requestId':request,'revision':index+4,'provider':{'id':engine,'name':setting['name'],'kind':'web-search','transport':'native-serp','pagination':'remote','limited':True},'results':copy.deepcopy(results),'hasMore':False,'translation':None,'translatedQuery':'','instantAnswer':None,'outcome':'results'}
  proof=C['reply_proof'](reply,receipt,query,engine,request,topic)
  entry={'name':name,'query':query,'expectedTopic':topic,'engine':engine,'startedAt':start,'finishedAt':start+2000,'elapsedMs':2000,'ok':True,'ownerTopicCovered':True,'outcome':'results','input':native('#mouse-search-query',start+5),'typing':{'method':'WebContents.insertText','text':query,'events':[{'type':'input','trusted':True,'matches':True}]},'pages':[{'args':{'query':query,'page':1,'filter':'all','requestId':request},'requestId':request,'page':1,'startedAt':start+9,'completedAt':start+1011,'result':reply,'proof':proof}],'cleanupStartedAt':start+1500,'additionalQueries':[],
   'ui':{'open':True,'query':query,'state':'results','busy':'false','engineReady':'true','engine':engine,'engineDisabled':False,'provider':engine,'errorVisible':False,'errorText':'','cards':[{'id':row['id'],'title':row['title'],'source':__import__('re').sub(r'^www\.','',row['source']),'bounds':{'x':0,'y':0,'width':1,'height':1}} for row in results]},'hostResults':[{key:row[key] for key in ('id','url','title','source','content')} for row in results]}
  cases.append(entry)
 library=L['fixture']();template=library['facts']['captures'][0];captures=[]
 for index,name in enumerate(C['CAPTURES']):
  if index:
   captures.append(native_capture(raw,name));continue
  capture=copy.deepcopy(template);capture.update(filename=name,displayFilename=name[:-4]+'-display.png')
  raw[name]=library['raw'][template['filename']];raw[capture['displayFilename']]=library['raw'][template['displayFilename']];captures.append(capture)
 first=receipts[0];source={key:first[key] for key in ('requestId','engine','engineName','query','page','filter','project','desk','requestedURL','finalURL','webContentsId','private','preference','navigationEpoch')}
 snapshot=copy.deepcopy(first['snapshot']);snapshot.pop('html');snapshot.pop('htmlLength');snapshot.pop('htmlTruncated');snapshot.update(visibilityState='visible',viewport={'width':256,'height':192})
 state={'source':source,'navigationEpoch':1,'webContentsId':first['webContentsId'],'url':first['finalURL'],'bounds':{'x':0,'y':0,'width':256,'height':192},'zoom':1,'visible':True,'attached':True,'topmost':True,'surfaceHeld':True,'tilesHidden':True,'window':{'visible':True,'focused':True,'minimized':False,'contentBounds':captures[1]['contentBounds']},'snapshot':snapshot,'organicSignature':first['organicSignature']}
 cases[0]['sourceFrame']={'available':True,'requestId':first['requestId'],'sourceFile':sources[0]['filename'],'before':state,'after':copy.deepcopy(state),'restored':{'attached':False,'visible':False,'query':C['CASES'][0][1],'active':True,'surfaceHoldRestored':True}}
 paint_fixture(raw,cases[0]['sourceFrame'],'source',captures[1],1200)
 pages=[];registry=[]
 for index,result in enumerate(first['results']):
  bounds={'x':8+128*index,'y':8,'width':112,'height':176};url=result['url'];body='Anthropic actual site text. '*8
  page={'id':result['id'],'resultURL':url,'recordURL':url,'url':url,'webContentsId':200+index,'navigationEpoch':1,'bounds':bounds,'visible':True,'viewVisible':True,'attached':True,'loading':False,'error':'','zoom':1,'document':{'url':url,'title':result['title'],'readyState':'complete','visibilityState':'visible','timeOrigin':BASE+120,'viewport':{key:bounds[key] for key in ('width','height')},'bodyText':body,'bodyTextLength':len(body)},'navigation':[{'event':'start','url':url,'at':1120},{'event':'commit','url':url,'at':1121},{'event':'dom-ready','url':url,'at':1122}]};pages.append(page)
  registry.append({key:copy.deepcopy(page[key]) for key in ('id','url','webContentsId','navigationEpoch','bounds','visible','loading','error')}|{'live':True,'title':result['title'],'clip':copy.deepcopy(bounds),'radius':12})
 tiles={'query':cases[0]['query'],'revision':4,'active':True,'blocked':False,'window':copy.deepcopy(state['window']),'registry':{'active':True,'suspended':False,'reason':'','revision':4,'maxLive':6,'liveCount':len(pages),'pages':registry},'pages':pages}
 cases[0]['tileFrame']={'selectedIds':[row['id'] for row in pages],'readiness':{'budgetMs':15000,'startedAt':1301,'finishedAt':1360,'elapsedMs':59,'lastState':copy.deepcopy(tiles)},'before':tiles,'after':copy.deepcopy(tiles)}
 paint_fixture(raw,cases[0]['tileFrame'],'tiles',captures[2],1370)
 cases[0]['uiAfterSource']=copy.deepcopy(cases[0]['ui'])
 menu_state={'open':True,'modal':True,'bounds':{'x':.1,'y':.1,'width':1.8,'height':1.8},'viewport':{'width':2,'height':2},'options':[{'value':key,'text':value['name'],'role':'option','selected':str(key==original).lower(),'disabled':False,'visible':True,'hit':True,'bounds':{'x':.2,'y':.2+index*.4,'width':1.6,'height':.4}} for index,(key,value) in enumerate(C['ENGINES'].items())]}
 menu={'before':menu_state,'after':copy.deepcopy(menu_state),'gateBlockedBefore':True,'gateBlockedAfter':True,'capture':C['CAPTURES'][0]}
 target=next(item['bounds'] for item in menu_state['options'] if item['value']==engine);origin=captures[0]['contentBounds'];choice['point']={'x':origin['x']+target['x']+target['width']/2,'y':origin['y']+target['y']+target['height']/2}
 production={'configured':True,'engine':engine,'providers':[engine],'endpoint':C['ENGINES'][engine]['base'],'transport':{'kind':'native-serp','session':'browser','private':False}}
 facts={'schema':3,'contract':C['CONTRACT'],'version':'6.0.35','platform':platform,'arch':arch,'pid':80,'packaged':True,'profileIsolated':True,'fixture':False,'physicalUserDeviceVerified':False,'source':'installed selected-engine WebContents navigation and actual organic DOM','ipcChannel':'mouse:tile-search','inputMode':'native engine selection and real search UI','ok':True,'contractVerified':True,'liveTopicalCapabilityVerified':True,'ownerQueryCovered':True,'verifiedEngines':[engine],'elapsedMs':6500,'cases':cases,'sources':sources,'inputs':inputs,'blockers':[],'cleanupErrors':[],'nativeCaptures':captures,'canonicalCaptures':list(C['CAPTURES']),'preference':{'before':{'engine':original,'private':False},'selected':setting,'opener':opener,'input':choice,'menu':menu,'closed':{'open':False,'modal':False,'gateBlocked':False},'ui':{'engine':engine,'engineReady':'true','engineDisabled':False}},'preferenceRestored':{'engine':original,'private':False,'exact':True},'production':{'state':production,'selected':copy.deepcopy(production)}}
 raw['mouse-635-owner-feedback.log']=(C['MARKER']+'\n'+C['LIVE_MARKER']+'\n').encode()
 owner={'pid':80,'platform':platform,'arch':arch,'captures':captures,'nativeInputs':inputs}
 return {'raw':raw,'facts':facts,'owner':owner,'receipts':receipts}


def packed(value):
 raw=dict(value['raw']);raw[C['NAME']]=encode(value['facts']);owner=copy.deepcopy(value['owner']);owner['publicSearch']={**value['facts'],'reportFile':C['NAME'],'reportSha256':sha(raw[C['NAME']])};return raw,owner


def replace_receipt(value,index,receipt):
 name=value['facts']['sources'][index]['filename'];raw=encode(receipt);value['raw'][name]=raw;value['facts']['sources'][index].update(bytes=len(raw),sha256=sha(raw))


def reject_then_accept(value,kind='source'):
 """Keep a real synthetic rejected OS frame, then a correctly matched frame."""
 frame=value['facts']['cases'][0]['sourceFrame' if kind=='source' else 'tileFrame'];paint=frame['paint'];good=paint['attempts'][0];bad=copy.deepcopy(good);start=paint['startedAt']
 bad['finishedAt']=start+30;bad['elapsedMs']=29;good.update(sequence=2,startedAt=start+40,finishedAt=start+90,elapsedMs=50)
 for direction in ('Before','After'):
  for row in good['references'+direction]:
   meta=row['image'];old=meta['filename'];meta['filename']=old.replace('-reference-01-','-reference-02-');value['raw'][meta['filename']]=value['raw'][old]
 name=good['capture']['filename'][:-4]+'-attempt-01.png';bad['capture']=native_capture(value['raw'],name,blank=True);candidate=C['N']['T']['decode_png'](value['raw'][name],name)
 for saved,left,right in zip(bad['comparisons'],bad['referencesBefore'],bad['referencesAfter']):
  decoded=[C['N']['T']['decode_png'](value['raw'][row['image']['filename']],row['image']['filename']) for row in (left,right)]
  saved.update(C['compare_paint'](*decoded,candidate,left['bounds'],bad['capture']['mapping']))
 bad['accepted']=False;paint.update(attempts=[bad,good],acceptedIndex=1)
 index=value['facts']['nativeCaptures'].index(good['capture']);value['facts']['nativeCaptures'].insert(index,bad['capture']);return value


def tile_states(value):
 frame=value['facts']['cases'][0]['tileFrame'];return [frame['readiness']['lastState'],frame['before'],frame['after']]


class PaintPixels(unittest.TestCase):
 def image(self,width=128,height=128):
  return bitmap(width,height,lambda x,y:([32,48,64],[96,112,128],[144,160,176],[208,224,240])[(2 if y>=height/2 else 0)+(1 if x>=width/2 else 0)]+[255])
 def compare(self,before,after=None,candidate=None,**kwargs):
  return C['compare_paint'](before,after or before,candidate or before,kwargs.get('bounds',{'x':0,'y':0,'width':before['width'],'height':before['height']}),kwargs.get('mapping',{'originX':0,'originY':0,'scaleX':1,'scaleY':1}))
 def test_exact_grid_counts_and_quadrants_are_hand_derived(self):
  result=self.compare(self.image());self.assertEqual(result,{'policy':C['PAINT_POLICY'],'totalSamples':576,'stableSamples':576,'matchedSamples':576,'mismatchedSamples':0,'informativeSamples':432,'informativeMatchedSamples':432,'referenceColors':4,'quadrants':[{'samples':144,'stable':144,'matched':144} for _ in range(4)],'accepted':True})
  self.assertTrue(self.compare(self.image(96,96))['accepted']);self.assertFalse(self.compare(self.image(92,96))['accepted'])
 def test_white_background_cannot_replace_small_but_informative_content(self):
  points={(x,y):i for i,(y,x) in enumerate((y,x) for y in range(16,496,4) for x in range(16,496,4))}
  reference=bitmap(512,512,lambda x,y:([32,64,96],[96,128,160],[160,192,224])[points[(x,y)]//24]+[255] if (x,y) in points and points[(x,y)]<72 else [255,255,255,255]);blank=bitmap(512,512,lambda x,y:[255,255,255,255])
  result=self.compare(reference,candidate=blank);self.assertEqual((result['totalSamples'],result['informativeSamples'],result['informativeMatchedSamples']),(14400,72,0));self.assertGreater(result['matchedSamples']/result['stableSamples'],.99);self.assertFalse(result['accepted']);self.assertFalse(self.compare(blank)['accepted'])
  for lost,accepted in [(3,True),(4,False)]:
   changed=bitmap(512,512,lambda x,y:[255,255,255,255] if (x,y) in points and points[(x,y)]<lost else list(reference['pixels'][(y*512+x)*4:(y*512+x)*4+4]));self.assertEqual(self.compare(reference,candidate=changed)['accepted'],accepted)
 def test_actual_pixels_must_match_both_opaque_readbacks(self):
  first=self.image();last=bitmap(128,128,lambda x,y:[v+3 for v in rgba_at(first,x,y)[:3]]+[255]);outside=bitmap(128,128,lambda x,y:[v-3 for v in rgba_at(first,x,y)[:3]]+[255])
  result=self.compare(first,last,outside);self.assertEqual((result['stableSamples'],result['matchedSamples']),(576,0));self.assertFalse(result['accepted'])
  transparent=bitmap(128,128,lambda x,y:rgba_at(first,x,y)[:3]+[254]);self.assertFalse(self.compare(first,candidate=transparent)['accepted']);self.assertEqual(self.compare(first,transparent)['stableSamples'],0)
 def test_one_unpainted_quadrant_and_a_broad_instability_fail(self):
  first=self.image();points=[(x,y) for y in range(16,64,4) for x in range(16,64,4)];keep=set(points[:15]);last=bitmap(128,128,lambda x,y:rgba_at(first,x,y)[:3]+[0 if x<64 and y<64 and (x,y) not in keep else 255])
  result=self.compare(first,last);self.assertEqual([q['stable'] for q in result['quadrants']],[15,144,144,144]);self.assertEqual(result['matchedSamples'],447);self.assertFalse(result['accepted'])
  unstable=bitmap(128,128,lambda x,y:rgba_at(first,x,y)[:3]+[255 if (x+y)%20==0 else 0]);self.assertFalse(self.compare(first,unstable)['accepted'])
 def test_global_match_fraction_remains_strict(self):
  first=self.image();points=[(x,y) for y in range(16,112,4) for x in range(16,112,4)]
  for count,accepted in [(5,True),(6,False)]:
   missed=set(points[:count]);actual=bitmap(128,128,lambda x,y:[0,0,0,255] if (x,y) in missed else rgba_at(first,x,y));result=self.compare(first,candidate=actual);self.assertEqual(result['mismatchedSamples'],count);self.assertEqual(result['accepted'],accepted)
 def test_fractional_native_mapping_samples_without_resizing(self):
  retina=self.compare(self.image(256,256),candidate=self.image(),bounds={'x':0,'y':0,'width':128,'height':128});self.assertTrue(retina['accepted']);self.assertEqual(retina['totalSamples'],576)
  first=self.image();bounds={'x':5.25,'y':7.5,'width':128,'height':128};mapping={'originX':.25,'originY':.5,'scaleX':1.25,'scaleY':1.5};pixels=bytearray(bytes([0,0,0,255])*180*210)
  for y in range(16,112,4):
   for x in range(16,112,4):
    px=int(mapping['originX']+(bounds['x']+x+.5)*mapping['scaleX']);py=int(mapping['originY']+(bounds['y']+y+.5)*mapping['scaleY']);at=(py*180+px)*4;pixels[at:at+4]=bytes(rgba_at(first,x,y))
  actual={'width':180,'height':210,'channels':4,'pixels':bytes(pixels)};self.assertTrue(self.compare(first,candidate=actual,bounds=bounds,mapping=mapping)['accepted'])
  self.assertFalse(self.compare(first,candidate=actual,bounds=bounds,mapping={**mapping,'originX':1.25})['accepted'])
  with self.assertRaisesRegex(ValueError,'outside'):self.compare(first,candidate=actual,bounds={**bounds,'x':1000},mapping=mapping)
  with self.assertRaisesRegex(ValueError,'dimensions'):self.compare(first,self.image(120,128))


def rgba_at(image,x,y):
 at=(y*image['width']+x)*image['channels'];return list(image['pixels'][at:at+4])


class NativeSearchEvidence(unittest.TestCase):
 def verify(self,value):
  raw,owner=packed(value);return C['verify'](raw.__getitem__,owner=owner)
 def test_actual_native_contract_shapes_and_all_selected_engine_dom_structures(self):
  for platform,arch in [('darwin','arm64'),('win32','x64'),('linux','x64')]:
   with self.subTest(platform=platform):
    result=self.verify(fixture(platform,arch));self.assertTrue(result['originalResultOrderPreserved']);self.assertEqual(result['resultCounts'],[2,2]);self.assertEqual(result['verifiedEngines'],['bing'])
  for engine in C['ENGINES']:
   with self.subTest(engine=engine):self.assertEqual(self.verify(fixture(engine=engine))['verifiedEngines'],[engine])
 def test_parser_reads_actual_dom_text_paths_and_entity_escaping_once(self):
  value=fixture();receipt=value['receipts'][0];html,rows=document('bing',C['CASES'][0][1],[{'url':'https://example.org/a?x=1&y=2','title':'Literal <b> &amp; 😀','content':'Plain <script> text & entity'}])
  receipt['snapshot'].update(html=html,htmlLength=C['jslen'](html),rows=rows);receipt.update(htmlBytes=len(html.encode()),htmlSha256=sha(html.encode()),organicSignature=C['signature'](rows))
  actual=C['dom_rows'](receipt);self.assertEqual(actual[0]['title'],'Literal <b> &amp; 😀');self.assertEqual(actual[0]['content'],'Plain <script> text & entity')
 def test_changed_dom_path_href_title_snippet_and_forged_fragment_fail(self):
  mutations=[lambda r:r['snapshot']['rows'][0].update(title='Forged title'),lambda r:r['snapshot']['rows'][0].update(content='Invented snippet'),lambda r:r['snapshot']['rows'][0].update(rawHref='https://other.org/'),lambda r:r['snapshot']['rows'][0].update(containerPath=[1,0,1]),lambda r:r['snapshot']['rows'][0].update(rawOuterHTML='<li>invented</li>'),lambda r:r.update(htmlSha256='f'*64),lambda r:r['snapshot'].update(htmlTruncated=True)]
  for mutate in mutations:
   value=fixture();receipt=copy.deepcopy(value['receipts'][0]);mutate(receipt);receipt['organicSignature']=C['signature'](receipt['snapshot']['rows']);replace_receipt(value,0,receipt)
   with self.assertRaises(ValueError):self.verify(value)
 def test_snippet_path_must_match_the_declared_provider_selector(self):
  value=fixture();receipt=copy.deepcopy(value['receipts'][0]);original=receipt['snapshot']['rows'][0]['rawOuterHTML'];replacement=original.replace('</li>','<span class="other-text">Forged but real nearby text</span></li>')
  receipt['snapshot']['html']=receipt['snapshot']['html'].replace(original,replacement);row=receipt['snapshot']['rows'][0];row.update(rawOuterHTML=replacement,snippetPath=[2],content='Forged but real nearby text');html=receipt['snapshot']['html'];receipt['snapshot']['htmlLength']=C['jslen'](html);receipt.update(htmlBytes=len(html.encode()),htmlSha256=sha(html.encode()),organicSignature=C['signature'](receipt['snapshot']['rows']))
  with self.assertRaisesRegex(ValueError,'snippet path'):C['dom_rows'](receipt)
 def test_navigation_exact_query_engine_and_preference_are_not_interchangeable(self):
  for mutate in [lambda r:r['preference'].update(engine='google'),lambda r:r.update(requestedURL=C['ENGINES']['google']['base']+'other'),lambda r:r['snapshot'].update(documentURL=r['finalURL']+'&q=other'),lambda r:r.update(query='news about anthropic'),lambda r:r.update(kind='public-api'),lambda r:r.update(navigation=[])]:
   value=fixture();receipt=copy.deepcopy(value['receipts'][0]);mutate(receipt);replace_receipt(value,0,receipt)
   with self.assertRaises(ValueError):self.verify(value)
 def test_provider_ads_and_nonorganic_containers_cannot_supply_results(self):
  value=fixture();receipt=copy.deepcopy(value['receipts'][0]);html=receipt['snapshot']['html'].replace('class="b_algo"','class="b_algo b_ad"',1);receipt['snapshot']['html']=html;receipt['snapshot']['htmlLength']=C['jslen'](html);receipt['snapshot']['rows'][0]['rawOuterHTML']=receipt['snapshot']['rows'][0]['rawOuterHTML'].replace('class="b_algo"','class="b_algo b_ad"');receipt.update(htmlBytes=len(html.encode()),htmlSha256=sha(html.encode()));replace_receipt(value,0,receipt)
  with self.assertRaisesRegex(ValueError,'advertisement'):self.verify(value)
 def test_raw_receipt_cannot_reorder_the_actual_dom_nodes(self):
  value=fixture();receipt=copy.deepcopy(value['receipts'][0]);receipt['snapshot']['rows'].reverse()
  for rank,row in enumerate(receipt['snapshot']['rows'],1):row['rank']=rank
  receipt['organicSignature']=C['signature'](receipt['snapshot']['rows']);receipt['results'].reverse()
  with self.assertRaisesRegex(ValueError,'document order'):C['dom_rows'](receipt)
 def test_original_organic_order_must_survive_reply_and_actual_tile_dom(self):
  for mutate in [lambda v:v['facts']['cases'][0]['pages'][0]['result']['results'].reverse(),lambda v:v['facts']['cases'][0]['ui']['cards'].reverse(),lambda v:v['facts']['cases'][0]['hostResults'].reverse(),lambda v:v['facts']['cases'][0]['pages'][0]['result']['results'].pop()]:
   value=fixture();mutate(value)
   with self.assertRaises(ValueError):self.verify(value)
 def test_duplicate_canonical_results_are_the_only_removed_duplicate_rows(self):
  value=fixture();receipt=value['receipts'][0];query=C['CASES'][0][1];row={'url':'https://www.anthropic.com/news?utm_source=test','title':'Duplicate tracking link','content':'Anthropic repeated'};base=[{'url':r['url'],'title':r['title'],'content':r['content']} for r in receipt['snapshot']['rows']];html,rows=document('bing',query,[base[0],row,base[1]]);receipt['snapshot'].update(html=html,htmlLength=C['jslen'](html),rows=rows);receipt.update(htmlBytes=len(html.encode()),htmlSha256=sha(html.encode()),organicSignature=C['signature'](rows));reply=value['facts']['cases'][0]['pages'][0]['result']
  proof=C['reply_proof'](reply,receipt,query,'bing',receipt['requestId'],['anthropic']);self.assertEqual(proof['sourceNodeRanks'],[1,3])
 def test_unsafe_organic_links_are_excluded_without_reranking_safe_rows(self):
  for unsafe in ('http://127.0.0.1/','javascript:alert(1)'):
   value=fixture();receipt=value['receipts'][0];query=C['CASES'][0][1];base=[{key:r[key] for key in ('url','title','content')} for r in receipt['snapshot']['rows']];html,rows=document('bing',query,[base[0],{'url':unsafe,'title':'Unsafe link','content':'Excluded original node'},base[1]])
   receipt['snapshot'].update(html=html,htmlLength=C['jslen'](html),rows=rows);receipt.update(htmlBytes=len(html.encode()),htmlSha256=sha(html.encode()),organicSignature=C['signature'](rows));proof=C['reply_proof'](value['facts']['cases'][0]['pages'][0]['result'],receipt,query,'bing',receipt['requestId'],['anthropic']);self.assertEqual(proof['sourceNodeRanks'],[1,3])
  self.assertEqual(C['clean']('\ufeff A\u0085B\ufeff',300),'A\u0085B')
 def test_actual_bytes_and_same_source_native_frames_are_mandatory(self):
  for mutate in [lambda v:v['raw'].__setitem__(C['CAPTURES'][0],b'fake'),lambda v:v['facts']['cases'][0]['sourceFrame']['after'].update(webContentsId=999),lambda v:v['facts']['cases'][0]['sourceFrame']['after'].update(navigationEpoch=2),lambda v:v['facts']['cases'][0]['sourceFrame']['after'].update(topmost=False),lambda v:v['facts']['cases'][0]['sourceFrame']['after'].update(tilesHidden=False),lambda v:v['facts']['cases'][0]['sourceFrame']['after'].update(zoom=2),lambda v:v['facts']['cases'][0]['sourceFrame']['restored'].update(surfaceHoldRestored=False)]:
   value=fixture();mutate(value)
   with self.assertRaises(ValueError):self.verify(value)
 def test_a_new_tab_screenshot_cannot_substitute_for_the_extracted_source_view(self):
  value=fixture();frame=value['facts']['cases'][0]['sourceFrame'];frame['before']['webContentsId']=frame['after']['webContentsId']=200
  with self.assertRaisesRegex(ValueError,'another document'):self.verify(value)
 def test_engine_choice_requires_both_real_clicks_and_preference_restore(self):
  for mutate in [lambda v:v['facts']['preference']['opener']['events'].pop(),lambda v:v['facts']['preference']['opener']['events'][-1].update(trusted=False),lambda v:v['facts']['preference']['input']['events'].pop(),lambda v:v['facts']['preference']['input']['events'][-1].update(trusted=False),lambda v:v['facts']['preference']['input'].update(selector='.mouse-search-engine'),lambda v:v['facts']['preferenceRestored'].update(engine='duckduckgo'),lambda v:v['facts']['production']['state']['transport'].update(kind='fixture')]:
   value=fixture();mutate(value)
   with self.assertRaises(ValueError):self.verify(value)
 def test_chooser_application_change_is_not_a_native_input_witness(self):
  value=fixture();value['facts']['preference']['input']['events'].append({'type':'change','trusted':False,'matches':False});self.verify(value)
  value['facts']['preference']['input']['events']=value['facts']['preference']['input']['events'][1:]
  with self.assertRaises(ValueError):self.verify(value)
 def test_captured_chooser_options_selection_barrier_and_hit_are_bound(self):
  for mutate in [lambda v:v['facts']['preference']['menu'].update(gateBlockedBefore=False),lambda v:v['facts']['preference']['menu'].update(capture=C['CAPTURES'][1]),lambda v:v['facts']['preference']['menu']['before'].update(modal=False),lambda v:v['facts']['preference']['menu']['after']['options'][1].update(text='Another search'),lambda v:v['facts']['preference']['menu']['after']['options'][1].update(hit=False),lambda v:v['facts']['preference']['closed'].update(gateBlocked=True),lambda v:v['facts']['preference']['input']['point'].update(x=99)]:
   value=fixture();mutate(value)
   with self.assertRaises(ValueError):self.verify(value)
  for mutate in [lambda v:v['options'][0].update(selected='false'),lambda v:v['options'].pop(),lambda v:v['options'][1].update(value='google'),lambda v:v['options'][1].update(disabled=True),lambda v:v['viewport'].update(width=3),lambda v:v['options'][1]['bounds'].update(y=99)]:
   value=fixture();menu=value['facts']['preference']['menu'];mutate(menu['before']);menu['after']=copy.deepcopy(menu['before'])
   with self.assertRaises(ValueError):self.verify(value)
 def test_live_capability_cannot_be_replaced_by_contract_pass_or_hidden_blocker(self):
  for mutate in [lambda v:v['facts'].update(liveTopicalCapabilityVerified=False),lambda v:v['facts'].update(blockers=[{'code':'CAPTCHA'}]),lambda v:v['raw'].__setitem__('mouse-635-owner-feedback.log',(C['MARKER']+'\n'+C['UNVERIFIED_MARKER']+'\n').encode()),lambda v:v['facts'].update(verifiedEngines=['bing','google'])]:
   value=fixture();mutate(value)
   with self.assertRaises(ValueError):self.verify(value)
 def test_visible_domain_omits_www_without_changing_host_or_url(self):
  value=fixture();case=value['facts']['cases'][0];self.assertEqual(case['ui']['cards'][0]['source'],'anthropic.com');self.assertEqual(case['hostResults'][0]['source'],'www.anthropic.com');self.verify(value)
  case['ui']['cards'][0]['source']='www.anthropic.com'
  with self.assertRaisesRegex(ValueError,'rendered title/domain'):self.verify(value)
 def test_provider_tracking_decoding_and_exact_query_rules(self):
  target='https://www.anthropic.com/news?x=1&y=2'
  self.assertEqual(C['destination']('/url?q='+quote(target,safe=''),'google',C['ENGINES']['google']['base']),target)
  self.assertEqual(C['destination']('/l/?uddg='+quote(target,safe=''),'duckduckgo',C['ENGINES']['duckduckgo']['base']),target)
  with self.assertRaises(ValueError):C['destination']('/url?q=http%3A%2F%2F127.0.0.1%2F','google',C['ENGINES']['google']['base'])
  with self.assertRaises(ValueError):C['source_url']('https://www.bing.com/search?q=C%2B%2B&q=other','bing','C++')
  self.assertEqual(C['canonical_id']('https://example.org/a?utm_source=x&b=2&a=1#part'),C['canonical_id']('https://example.org/a?a=1&b=2'))
 def test_dom_only_old_artifacts_cannot_authorize_source_or_live_site_pixels(self):
  for field in ('sourceFrame','tileFrame'):
   value=fixture();value['facts']['cases'][0][field].pop('paint')
   with self.assertRaisesRegex(ValueError,'actual paint'):self.verify(value)
  value=fixture();value['facts']['cases'][0].pop('tileFrame')
  with self.assertRaisesRegex(ValueError,'live sites'):self.verify(value)
 def test_real_native_wrong_shell_bytes_fail_even_with_refreshed_hashes(self):
  for kind,index in [('source',1),('tiles',2)]:
   value=fixture();frame=value['facts']['cases'][0]['sourceFrame' if kind=='source' else 'tileFrame'];wrong=native_capture(value['raw'],C['CAPTURES'][index],blank=True);value['facts']['nativeCaptures'][index]=wrong;frame['paint']['attempts'][0]['capture']=wrong
   with self.assertRaisesRegex(ValueError,'metrics differ'):self.verify(value)
 def test_reference_png_identity_hash_dimensions_and_metrics_are_recomputed(self):
  mutations=[lambda a:a['referencesBefore'][0].update(webContentsId=999),lambda a:a['referencesAfter'][0]['image'].update(sha256='f'*64),lambda a:a['referencesBefore'][0]['image'].update(source='shell.capturePage'),lambda a:a['referencesBefore'][0]['image']['pixelSize'].update(width=300),lambda a:a['referencesBefore'][0]['bounds'].update(x=4),lambda a:a['comparisons'][0].update(matchedSamples=1),lambda a:a['comparisons'][0]['policy'].update(tolerance=99),lambda a:a['capture']['mapping'].update(originX=20)]
  for change in mutations:
   value=fixture();change(value['facts']['cases'][0]['sourceFrame']['paint']['attempts'][0])
   with self.assertRaises(ValueError):self.verify(value)
 def test_rejected_os_frames_and_reference_pngs_are_retained_in_exact_order(self):
  value=reject_then_accept(reject_then_accept(fixture()),'tiles');result=self.verify(value)
  self.assertEqual(result['canonicalCaptures'],C['CAPTURES']);self.assertEqual(len(result['nativeCaptures']),5);self.assertEqual(len([name for name in result['inputs'] if '-reference-' in name]),12);self.assertTrue(result['sourcePaintVerified']);self.assertTrue(result['liveTilePaintVerified'])
  value['facts']['nativeCaptures'][1:3]=reversed(value['facts']['nativeCaptures'][1:3])
  with self.assertRaisesRegex(ValueError,'ledger'):self.verify(value)
 def test_retry_deadline_acceptance_and_canonical_states_cannot_be_forged(self):
  changes=[lambda p:p.update(deadline=p['startedAt']+4501),lambda p:p.update(finishedAt=p['deadline']+1,elapsedMs=4501),lambda p:p.update(acceptedIndex=0),lambda p:p['attempts'][0].update(accepted=True),lambda p:p['attempts'][0].update(sequence=2),lambda p:p['attempts'][0].update(error='document changed'),lambda p:p['attempts'][1].update(startedAt=p['attempts'][0]['finishedAt']-1),lambda p:p['attempts'][0]['after'].update(zoom=2),lambda p:p.update(attempts=p['attempts']*11,acceptedIndex=21)]
  for change in changes:
   value=reject_then_accept(fixture());change(value['facts']['cases'][0]['sourceFrame']['paint'])
   with self.assertRaises(ValueError):self.verify(value)
  value=fixture();value['facts']['cases'][0]['sourceFrame']['before']=copy.deepcopy(value['facts']['cases'][0]['sourceFrame']['before']);value['facts']['cases'][0]['sourceFrame']['before']['snapshot']['documentTitle']='Unrelated outer snapshot'
  with self.assertRaisesRegex(ValueError,'canonical paint states'):self.verify(value)
 def test_reference_bytes_are_read_and_bound_even_for_rejected_attempts(self):
  value=reject_then_accept(fixture());name=value['facts']['cases'][0]['sourceFrame']['paint']['attempts'][0]['referencesBefore'][0]['image']['filename'];value['raw'][name]=b'not a PNG'
  with self.assertRaisesRegex(ValueError,'size/hash'):self.verify(value)
 def test_loading_can_remain_true_only_with_visible_substantive_actual_site_pixels(self):
  value=fixture()
  for state in tile_states(value):
   for page in state['pages']+state['registry']['pages']:page['loading']=True
  self.assertTrue(self.verify(value)['liveTilePaintVerified'])
  for change in [lambda p:p.update(attached=False),lambda p:p.update(error='network failed'),lambda p:p['document'].update(readyState='loading'),lambda p:p['document'].update(visibilityState='hidden'),lambda p:p['document'].update(bodyText='Загрузка…'),lambda p:p['document'].update(bodyText='Unrelated page content. '*10),lambda p:p['document'].update(timeOrigin=0)]:
   value=fixture();change(value['facts']['cases'][0]['tileFrame']['before']['pages'][0])
   with self.assertRaises(ValueError):self.verify(value)
 def test_actual_redirect_keeps_original_result_and_document_navigation_binding(self):
  value=fixture();target='https://www.anthropic.com/news/redirected'
  for state in tile_states(value):
   page=state['pages'][0];page.update(url=target,recordURL=target);page['document']['url']=target;page['navigation'].extend([{'event':'redirect','url':target,'at':1200},{'event':'commit','url':target,'at':1201}]);state['registry']['pages'][0]['url']=target
  self.verify(value)
  for state in tile_states(value):state['pages'][0]['navigation']=[row for row in state['pages'][0]['navigation'] if row['url']!=target]
  with self.assertRaisesRegex(ValueError,'navigation'):self.verify(value)
 def test_original_first_two_sites_cannot_be_replaced_by_faster_or_other_pages(self):
  for change in [lambda f:f['selectedIds'].reverse(),lambda f:f['before']['pages'].reverse(),lambda f:f['before']['registry']['pages'].reverse(),lambda f:f['before'].update(query='other'),lambda f:f['before'].update(revision=88),lambda f:f['before'].update(blocked=True),lambda f:f['before']['registry'].update(suspended=True),lambda f:f['before']['pages'][0].update(resultURL='https://example.org/'),lambda f:f['after']['pages'][0]['document'].update(timeOrigin=BASE+999)]:
   value=fixture();change(value['facts']['cases'][0]['tileFrame'])
   with self.assertRaises(ValueError):self.verify(value)
 def test_one_painted_site_only_when_actual_provider_returns_one_result(self):
  value=fixture(owner_results=1);result=self.verify(value);self.assertEqual(result['resultCounts'],[1,2]);self.assertEqual(len(result['liveTileIds']),1)
  value=fixture();frame=value['facts']['cases'][0]['tileFrame'];frame['selectedIds'].pop()
  for state in tile_states(value):state['pages'].pop()
  with self.assertRaises(ValueError):self.verify(value)
 def test_live_tile_readiness_and_paint_must_precede_query_cleanup(self):
  for change in [lambda f:f['readiness'].update(budgetMs=60000),lambda f:f['readiness'].update(elapsedMs=16000),lambda f:f['readiness'].update(finishedAt=f['paint']['startedAt']+1),lambda f:f['readiness']['lastState']['pages'][0].update(url='https://other.org/')]:
   value=fixture();change(value['facts']['cases'][0]['tileFrame'])
   with self.assertRaises(ValueError):self.verify(value)
  value=fixture();case=value['facts']['cases'][0];case['cleanupStartedAt']=case['tileFrame']['paint']['finishedAt']-1
  with self.assertRaisesRegex(ValueError,'lifetime'):self.verify(value)


if __name__=='__main__':unittest.main()
