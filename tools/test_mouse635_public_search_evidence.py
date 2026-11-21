#!/usr/bin/env python3
"""Synthetic contracts only: these fixtures are never live engine evidence."""
import copy
from datetime import datetime,timezone
from html import escape
import json
from pathlib import Path
import runpy
import unittest
from urllib.parse import quote

HERE=Path(__file__).parent
C=runpy.run_path(str(HERE/'mouse635-public-search-evidence.py'))
L=runpy.run_path(str(HERE/'test_mouse635_library_evidence.py'))
sha=C['sha']
encode=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n').encode()
BASE=1795255200000


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


def fixture(platform='linux',arch='x64',engine='bing'):
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
 for name in C['CAPTURES']:
  capture=copy.deepcopy(template);capture.update(filename=name,displayFilename=name[:-4]+'-display.png')
  raw[name]=library['raw'][template['filename']];raw[capture['displayFilename']]=library['raw'][template['displayFilename']];captures.append(capture)
 first=receipts[0];source={key:first[key] for key in ('requestId','engine','engineName','query','page','filter','project','desk','requestedURL','finalURL','webContentsId','private','preference','navigationEpoch')}
 snapshot=copy.deepcopy(first['snapshot']);snapshot.pop('html');snapshot.pop('htmlLength');snapshot.pop('htmlTruncated');snapshot.update(visibilityState='visible',viewport={'width':2,'height':2})
 state={'source':source,'navigationEpoch':1,'webContentsId':first['webContentsId'],'url':first['finalURL'],'bounds':{'x':0,'y':0,'width':2,'height':2},'zoom':1,'visible':True,'attached':True,'topmost':True,'surfaceHeld':True,'tilesHidden':True,'window':{'visible':True,'focused':True,'minimized':False,'contentBounds':captures[1]['contentBounds']},'snapshot':snapshot,'organicSignature':first['organicSignature']}
 cases[0]['sourceFrame']={'available':True,'requestId':first['requestId'],'sourceFile':sources[0]['filename'],'before':state,'after':copy.deepcopy(state),'restored':{'attached':False,'visible':False,'query':C['CASES'][0][1],'active':True,'surfaceHoldRestored':True}}
 cases[0]['uiAfterSource']=copy.deepcopy(cases[0]['ui'])
 menu_state={'open':True,'modal':True,'bounds':{'x':.1,'y':.1,'width':1.8,'height':1.8},'viewport':{'width':2,'height':2},'options':[{'value':key,'text':value['name'],'role':'option','selected':str(key==original).lower(),'disabled':False,'visible':True,'hit':True,'bounds':{'x':.2,'y':.2+index*.4,'width':1.6,'height':.4}} for index,(key,value) in enumerate(C['ENGINES'].items())]}
 menu={'before':menu_state,'after':copy.deepcopy(menu_state),'gateBlockedBefore':True,'gateBlockedAfter':True,'capture':C['CAPTURES'][0]}
 target=next(item['bounds'] for item in menu_state['options'] if item['value']==engine);origin=captures[0]['contentBounds'];choice['point']={'x':origin['x']+target['x']+target['width']/2,'y':origin['y']+target['y']+target['height']/2}
 production={'configured':True,'engine':engine,'providers':[engine],'endpoint':C['ENGINES'][engine]['base'],'transport':{'kind':'native-serp','session':'browser','private':False}}
 facts={'schema':3,'contract':C['CONTRACT'],'version':'6.0.35','platform':platform,'arch':arch,'pid':80,'packaged':True,'profileIsolated':True,'fixture':False,'physicalUserDeviceVerified':False,'source':'installed selected-engine WebContents navigation and actual organic DOM','ipcChannel':'mouse:tile-search','inputMode':'native engine selection and real search UI','ok':True,'contractVerified':True,'liveTopicalCapabilityVerified':True,'ownerQueryCovered':True,'verifiedEngines':[engine],'elapsedMs':6500,'cases':cases,'sources':sources,'inputs':inputs,'blockers':[],'cleanupErrors':[],'nativeCaptures':captures,'preference':{'before':{'engine':original,'private':False},'selected':setting,'opener':opener,'input':choice,'menu':menu,'closed':{'open':False,'modal':False,'gateBlocked':False},'ui':{'engine':engine,'engineReady':'true','engineDisabled':False}},'preferenceRestored':{'engine':original,'private':False,'exact':True},'production':{'state':production,'selected':copy.deepcopy(production)}}
 raw['mouse-635-owner-feedback.log']=(C['MARKER']+'\n'+C['LIVE_MARKER']+'\n').encode()
 owner={'pid':80,'platform':platform,'arch':arch,'captures':captures,'nativeInputs':inputs}
 return {'raw':raw,'facts':facts,'owner':owner,'receipts':receipts}


def packed(value):
 raw=dict(value['raw']);raw[C['NAME']]=encode(value['facts']);owner=copy.deepcopy(value['owner']);owner['publicSearch']={**value['facts'],'reportFile':C['NAME'],'reportSha256':sha(raw[C['NAME']])};return raw,owner


def replace_receipt(value,index,receipt):
 name=value['facts']['sources'][index]['filename'];raw=encode(receipt);value['raw'][name]=raw;value['facts']['sources'][index].update(bytes=len(raw),sha256=sha(raw))


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


if __name__=='__main__':unittest.main()
