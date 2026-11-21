#!/usr/bin/env python3
"""Synthetic API/parser fixtures only; these tests are not public-search evidence."""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import unittest

C=runpy.run_path(str(Path(__file__).with_name('mouse635-public-search-evidence.py')))
sha=lambda raw:hashlib.sha256(raw).hexdigest()
encode=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n').encode()


def fixture():
 raw={};network=[];cases=[];clock=100.0
 def receipt(endpoint,query,body,offset=None,error=None):
  nonlocal clock
  sequence=len(network)+1;clock+=10
  row={'sequence':sequence,'endpoint':endpoint,'query':query,'offset':offset,'method':'GET','transport':'chromium','startedAt':clock,'finishedAt':clock+1,'ok':error is None}
  if error:row['error']={'code':'ERR_SEARCH_NETWORK','causeCode':error}
  else:
   data=encode(body);filename='mouse-635-public-api-'+str(sequence).zfill(3)+'.json';raw[filename]=data;row.update(filename=filename,bytes=len(data),sha256=sha(data),status=200,contentType='application/json')
  network.append(row);return row
 for index,(name,query,topic,page_count) in enumerate(C['CASES']):
  started=clock;pages=[]
  for page in range(1,page_count+1):
   begin=clock;url='https://www.anthropic.com/news/item-'+str(page) if index==0 else 'https://docs.python.org/3/reference/item-'+str(index)+'-'+str(page)
   title='Anthropic news' if index==0 else 'Python reference';original={'url':url,'title':title,'description':title,'content':title};provider='brave'
   if index==2:
    receipt(C['BRAVE'],query,None,error='ERR_BLOCKED_BY_CLIENT')
    receipt(C['DDG'],query,{'AbstractText':'Python','AbstractURL':'https://www.python.org/','RelatedTopics':[]})
    provider='mwmbl';body={'query':query,'number_of_results':1,'results':[original]}
   else:body={'query':{'more_results_available':page<page_count},'web':{'results':[original]}}
   response=receipt(C['BRAVE'] if provider=='brave' else C['MWMBL'],query,body,str(page-1) if provider=='brave' else None);clock+=10
   row={'id':'r_'+sha(url.encode())[:24],'url':url,'title':title,'content':title,'type':'site'}
   result={'requestId':'public635-'+name+'-'+str(page),'revision':index+1,'query':query,'page':page,'results':[row],'hasMore':page<page_count,'provider':{'id':provider,'kind':'web-search','limited':provider=='mwmbl','pagination':'remote' if provider=='brave' else 'snapshot'}}
   pages.append({'page':page,'requestId':result['requestId'],'startedAt':begin,'completedAt':clock,'result':result,'proof':{'sourceResponseSHA256':[response['sha256']],'topicMatches':[row['id']],'distinct':True,'resultCount':1}})
  clock+=5;cases.append({'name':name,'query':query,'expectedTopic':topic,'pages':pages,'ok':True,'ownerTopicCovered':True,'startedAt':started,'finishedAt':clock,'elapsedMs':clock-started})
 native={'selector':'#mouse-search-button','source':'XTest','point':{'x':12,'y':24},'at':100,'navigates':False,'events':[{'type':'click','trusted':True,'matches':True}]}
 facts={'schema':1,'version':'6.0.35','platform':'linux','arch':'x64','pid':80,'ok':True,'packaged':True,'profileIsolated':True,'fixture':False,'apiOnly':True,'ownerQueryCovered':True,'physicalUserDeviceVerified':False,'source':'installed production preload IPC and Chromium API responses','ipcChannel':'mouse:tile-search','inputMode':'preload-ipc','nativeCaptures':[],'blockers':[],'cleanupErrors':[],'elapsedMs':clock,'production':{'state':{'configured':True,'endpoint':C['DDG'],'providers':['brave','duckduckgo-instant','mwmbl'],'transport':{'kind':'chromium','credentials':'omit','persistent':False}},'providerSettings':{'braveConfigured':True},'endpoints':[C['DDG'],C['MWMBL'],C['BRAVE'],C['TRANSLATION']]},'cases':cases,'network':network,'controlledPrimaryFailure':{'endpoint':C['BRAVE'],'mechanism':'isolated Chromium webRequest cancellation','blocked':[{'endpoint':C['BRAVE'],'query':C['CASES'][2][1],'method':'GET','at':network[4]['startedAt']}],'caseName':C['CASES'][2][0]},'inputs':[native]}
 owner={'platform':'linux','arch':'x64','pid':80,'nativeInputs':[native]};raw['mouse-635-owner-feedback.log']=(C['MARKER']+'\n').encode();return{'facts':facts,'owner':owner,'raw':raw}


def translated_fixture():
 data=fixture();facts=data['facts'];entry=facts['cases'][0];query=entry['query'];translated='News about Anthropic';pages=entry['pages']
 rows=[{'url':p['result']['results'][0]['url'],'title':'Anthropic news','content':'Anthropic news'} for p in pages]
 def added(endpoint,search,body,started,**extra):
  content=encode(body);return {'endpoint':endpoint,'query':search,'offset':None,'method':'GET','transport':'chromium','startedAt':started,'finishedAt':started+1,'ok':True,'status':200,'contentType':'application/json','bytes':len(content),'sha256':sha(content),'_body':content,**extra}
 original=added(C['MWMBL'],query,{'query':query,'number_of_results':0,'results':[]},110)
 translation=added(C['TRANSLATION'],query,{'responseStatus':200,'quotaFinished':False,'responseData':{'translatedText':translated}},112,languagePair='ru|en')
 expanded=added(C['MWMBL'],translated,{'query':translated,'number_of_results':2,'results':rows},114)
 previous_raw=data['raw'];raw={k:v for k,v in previous_raw.items() if not k.startswith('mouse-635-public-api-')};network=[original,translation,expanded]+facts['network'][2:]
 for index,receipt in enumerate(network,1):
  body=receipt.pop('_body',previous_raw.get(receipt.get('filename')));receipt['sequence']=index
  if body is not None:receipt['filename']='mouse-635-public-api-'+str(index).zfill(3)+'.json';raw[receipt['filename']]=body
 for page in pages:
  result=page['result'];result['provider']={'id':'mwmbl','kind':'web-search','limited':True,'pagination':'snapshot','total':2};result['translatedQuery']=translated;result['translation']={'provider':'mymemory','originalQuery':query,'translatedQuery':translated,'from':'ru','to':'en'};result['notice']='MyMemory: '+translated
  page['proof']['sourceResponseSHA256']=[expanded['sha256']];page['proof']['translationProof']={'originalQuery':query,'providerQuery':translated,'originalResponseSHA256':[original['sha256']],'translationResponseSHA256':[translation['sha256']]}
 facts['network']=network;data['raw']=raw;return data


def packed(value):
 raw=dict(value['raw']);facts=value['facts'];raw[C['NAME']]=encode(facts);owner=copy.deepcopy(value['owner']);owner['publicSearch']={**facts,'reportFile':C['NAME'],'reportSha256':sha(raw[C['NAME']])};raw['mouse-635-owner-feedback.json']=encode(owner);return raw,owner


class PublicAPIProof(unittest.TestCase):
 def verify(self,value):
  raw,owner=packed(value);return C['verify'](raw.__getitem__,expected_platform='linux',expected_arch='x64',owner=owner)
 def test_complete_raw_api_fixture(self):
  result=self.verify(fixture());self.assertTrue(result['ok']);self.assertEqual(result['pageResultCounts'],[1]*5);self.assertEqual(len(result['inputs']),7)
 def test_translated_snapshot_binds_original_translation_and_both_pages(self):
  result=self.verify(translated_fixture());self.assertTrue(result['ok']);self.assertEqual(result['pageResultCounts'],[1]*5)
 def test_translated_snapshot_rejects_hidden_forged_or_reordered_evidence(self):
  mutations=[lambda f:f['cases'][0]['pages'][0]['result'].__setitem__('notice',''),lambda f:f['cases'][0]['pages'][0]['result']['translation'].__setitem__('originalQuery','another query'),lambda f:f['cases'][0]['pages'][1]['result'].__setitem__('translatedQuery','Invented query'),lambda f:f['cases'][0]['pages'][0]['proof']['translationProof'].__setitem__('translationResponseSHA256',['f'*64]),lambda f:f['network'][1].__setitem__('languagePair','en|ru'),lambda f:f['network'][1].__setitem__('endpoint','https://api.mymemory.translated.net/set'),lambda f:f['network'][2].__setitem__('query','unrelated query'),lambda f:f['network'][2].update(startedAt=109,finishedAt=110),lambda f:f['network'][0].update(startedAt=116,finishedAt=117)]
  for mutate in mutations:
   data=translated_fixture();mutate(data['facts'])
   with self.assertRaises(ValueError):self.verify(data)
  for change in [lambda b:b['responseData'].__setitem__('translatedText','Different real text'),lambda b:b.__setitem__('quotaFinished',True),lambda b:b.__setitem__('responseStatus',429)]:
   data=translated_fixture();receipt=data['facts']['network'][1];body=json.loads(data['raw'][receipt['filename']]);change(body);encoded=encode(body);data['raw'][receipt['filename']]=encoded;receipt.update(bytes=len(encoded),sha256=sha(encoded))
   for page in data['facts']['cases'][0]['pages']:page['proof']['translationProof']['translationResponseSHA256']=[receipt['sha256']]
   with self.assertRaises(ValueError):self.verify(data)
 def test_exact_russian_query_and_real_topic_coverage_are_mandatory(self):
  for mutate in [lambda f:f['cases'][0].__setitem__('query','Anthropic'),lambda f:f['cases'][0].__setitem__('ownerTopicCovered',False),lambda f:f['cases'][0]['pages'][0]['result'].__setitem__('results',[]),lambda f:f.__setitem__('ownerQueryCovered',False),lambda f:f['cases'][0]['pages'][0]['proof'].__setitem__('topicMatches',[])]:
   data=fixture();mutate(data['facts'])
   with self.assertRaises(ValueError):self.verify(data)
  data=fixture();entry=data['facts']['network'][0];body=json.loads(data['raw'][entry['filename']]);body['web']['results'][0].update(url='https://unrelated.org/recipe',title='Recipe',content='Cooking',description='Food');data['raw'][entry['filename']]=encode(body);entry.update(bytes=len(data['raw'][entry['filename']]),sha256=sha(data['raw'][entry['filename']]));page=data['facts']['cases'][0]['pages'][0];page['result']['results'][0].update(url='https://unrelated.org/recipe',title='Anthropic claimed by forged result');page['proof']['sourceResponseSHA256']=[entry['sha256']]
  with self.assertRaisesRegex(ValueError,'topic'):self.verify(data)
 def test_html_serp_default_searx_and_reference_cards_are_rejected(self):
  mutations=[lambda f:f['network'][0].__setitem__('contentType','text/html'),lambda f:f['network'][0].__setitem__('endpoint','https://www.google.com/search'),lambda f:f['production']['state']['providers'].append('searx'),lambda f:f['production']['state']['transport'].__setitem__('kind','node-fetch'),lambda f:f['cases'][0]['pages'][0]['result']['provider'].__setitem__('id','duckduckgo-instant')]
  for mutate in mutations:
   data=fixture();mutate(data['facts'])
   with self.assertRaises(ValueError):self.verify(data)
 def test_unique_pages_provider_snapshot_and_raw_body_binding(self):
  mutations=[lambda f:f['cases'][0]['pages'].pop(),lambda f:f['cases'][0]['pages'][1]['result'].__setitem__('revision',999),lambda f:f['cases'][0]['pages'][0]['result'].__setitem__('hasMore',False),lambda f:f['cases'][0]['pages'][1]['result']['results'][0].__setitem__('url',f['cases'][0]['pages'][0]['result']['results'][0]['url']),lambda f:f['cases'][0]['pages'][0]['proof'].__setitem__('sourceResponseSHA256',['f'*64]),lambda f:f['network'][0].__setitem__('offset','10')]
  for mutate in mutations:
   data=fixture();mutate(data['facts'])
   with self.assertRaises(ValueError):self.verify(data)
  data=fixture();data['raw'][data['facts']['network'][0]['filename']]=b'{}'
  with self.assertRaises(ValueError):self.verify(data)
 def test_denial_or_fabricated_failure_cannot_be_hidden_as_fallback(self):
  for status in (401,403,429):
   data=fixture();data['facts']['network'][4]['status']=status
   with self.assertRaises(ValueError):self.verify(data)
  for mutate in [lambda f:f['network'][4]['error'].__setitem__('causeCode','ECONNREFUSED'),lambda f:f['network'][4].__setitem__('filename','invented.json'),lambda f:f['controlledPrimaryFailure'].__setitem__('blocked',[]),lambda f:f['controlledPrimaryFailure'].__setitem__('endpoint',C['DDG']),lambda f:f['cases'][2]['pages'][0]['result']['provider'].__setitem__('id','brave')]:
   data=fixture();mutate(data['facts'])
   with self.assertRaises(ValueError):self.verify(data)
 def test_fresh_process_hash_native_receipt_cleanup_are_required(self):
  for mutate in [lambda d:d['owner'].__setitem__('pid',81),lambda d:d['facts'].__setitem__('fixture',True),lambda d:d['facts'].__setitem__('cleanupErrors',['error']),lambda d:d['facts'].__setitem__('blockers',['no relevant RU result']),lambda d:d['facts']['inputs'][0]['events'][0].__setitem__('trusted',False)]:
   data=fixture();mutate(data)
   with self.assertRaises(ValueError):self.verify(data)
  raw,owner=packed(fixture());owner['publicSearch']['reportSha256']='f'*64
  with self.assertRaises(ValueError):C['verify'](raw.__getitem__,owner=owner)


if __name__=='__main__':unittest.main()
