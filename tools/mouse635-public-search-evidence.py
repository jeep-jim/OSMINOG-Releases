#!/usr/bin/env python3
"""Require actual Chromium JSON API bytes for the exact public owner query."""
import ipaddress
import json
from pathlib import Path
import re
import runpy
from urllib.parse import quote, urlsplit, urlunsplit

N=runpy.run_path(str(Path(__file__).with_name('mouse635-native-evidence.py')))
need,finite,positive,sha=N['need'],N['finite'],N['positive'],N['sha']
NAME='mouse-635-public-search.json'
MARKER='MOUSE_635_PUBLIC_SEARCH_PASS'
DDG='https://api.duckduckgo.com/'
MWMBL='https://api.mwmbl.org/api/v2/search/'
BRAVE='https://api.search.brave.com/res/v1/web/search'
TRANSLATION='https://api.mymemory.translated.net/get'
CASES=[('owner-russian','новости про антропик',['anthropic','антропик'],2),('control','Python documentation',['python'],2),('forced-primary-failure','Python programming language reference',['python'],1)]


def web_url(value):
 need(isinstance(value,str) and 0<len(value)<=8192,'web URL missing')
 parsed=urlsplit(value.strip());need(parsed.scheme in ('http','https') and parsed.hostname and parsed.username is None and parsed.password is None,'unsafe web result URL')
 host=parsed.hostname.encode('idna').decode().lower();need(host!='localhost' and not host.endswith(('.localhost','.local','.invalid','.test','.example')),'fixture/private result URL')
 try: address=ipaddress.ip_address(host)
 except ValueError: address=None
 if address is not None: need(address.is_global,'non-public result address')
 if ':' in host: host='['+host+']'
 port=parsed.port
 if port is not None and port!=({'http':80,'https':443}[parsed.scheme]): host+=':'+str(port)
 return urlunsplit((parsed.scheme,host,quote(parsed.path or '/',safe="/:@-._~!$&'()*+,;=%[]"),quote(parsed.query,safe="/:?@-._~!$&'()*+,;=%[]"),quote(parsed.fragment,safe="/:?@-._~!$&'()*+,;=%[]")))


def verify(read,*,expected_platform=None,expected_arch=None,owner=None):
 evidence=N['Evidence'](read);raw,facts=evidence.json(NAME)
 if owner is None: _,owner=evidence.json('mouse-635-owner-feedback.json')
 platform,arch,pid=facts.get('platform'),facts.get('arch'),facts.get('pid')
 need((platform,arch) in (('darwin','arm64'),('win32','x64'),('linux','x64')) and (expected_platform is None or expected_platform==platform) and (expected_arch is None or expected_arch==arch),'public search native target differs')
 need(facts.get('schema')==1 and facts.get('version')=='6.0.35' and positive(pid) and (owner.get('platform'),owner.get('arch'),owner.get('pid'))==(platform,arch,pid),'public report belongs to another installed process')
 N['flags'](facts,('ok','packaged','profileIsolated','apiOnly','ownerQueryCovered'),'public API owner query did not pass in the installed profile')
 need(facts.get('fixture') is False and facts.get('physicalUserDeviceVerified') is False and facts.get('source')=='installed production preload IPC and Chromium API responses' and facts.get('ipcChannel')=='mouse:tile-search' and facts.get('inputMode')=='preload-ipc' and facts.get('nativeCaptures')==[],'public API test scope was overstated or replaced by a fixture')
 need(not facts.get('error') and facts.get('blockers')==[] and facts.get('cleanupErrors')==[] and finite(facts.get('elapsedMs')) and 0<facts['elapsedMs']<=240000,'public API acceptance failed, exceeded its owner budget or did not restore')
 need(owner.get('publicSearch')=={**facts,'reportFile':NAME,'reportSha256':sha(raw)},'public API raw/owner summary byte binding differs')
 log=read('mouse-635-owner-feedback.log');need(isinstance(log,bytes) and 0<len(log)<=16*1024**2 and MARKER in log.decode('utf-8').splitlines(),'actual public-search process marker missing')
 production=facts.get('production',{});state=production.get('state',{});transport=state.get('transport',{});providers=state.get('providers')
 need(state.get('configured') is True and state.get('endpoint')==DDG and production.get('endpoints')==[DDG,MWMBL,BRAVE,TRANSLATION] and isinstance(providers,list) and {'duckduckgo-instant','mwmbl'}<=set(providers)<= {'duckduckgo-instant','mwmbl','brave'},'default public search endpoint/providers differ or SearX is enabled')
 need(transport.get('kind')=='chromium' and transport.get('credentials')=='omit' and transport.get('persistent') is False,'real private Chromium API transport missing')
 configured=production.get('providerSettings',{}).get('braveConfigured');need(type(configured) is bool,'configured provider key state missing')
 network=facts.get('network');need(isinstance(network,list) and 4<=len(network)<=40 and len({r.get('sequence') for r in network})==len(network),'actual API response ledger missing/duplicated')
 bodies={};inputs={NAME:sha(raw)}
 for receipt in network:
  need(isinstance(receipt,dict) and positive(receipt.get('sequence')) and receipt.get('endpoint') in (DDG,MWMBL,BRAVE,TRANSLATION) and isinstance(receipt.get('query'),str) and 0<len(receipt['query'])<=512 and receipt.get('method')=='GET' and receipt.get('transport')=='chromium' and type(receipt.get('ok')) is bool,'response came from another transport, query, HTML SERP or endpoint')
  need(finite(receipt.get('startedAt')) and finite(receipt.get('finishedAt')) and receipt['startedAt']<=receipt['finishedAt'],'actual Chromium response timing absent')
  need(receipt.get('status') not in (401,403,429),'a denied/rate-limited provider cannot be retried as successful acceptance')
  if receipt['ok']:
   filename=receipt.get('filename');need(filename=='mouse-635-public-api-'+str(receipt['sequence']).zfill(3)+'.json','raw API filename differs')
   body=read(filename);need(isinstance(body,bytes) and 0<len(body)<=2*1024**2 and receipt.get('bytes')==len(body) and receipt.get('sha256')==sha(body) and receipt.get('status')==200,'actual API body bytes/hash/status differ')
   mime=receipt.get('contentType');need(isinstance(mime,str) and (re.search(r'\bjson\b',mime,re.I) or receipt['endpoint']==DDG and re.match(r'^application/(?:x-)?javascript(?:;|$)',mime,re.I)),'API returned HTML or another unsupported format')
   value=json.loads(body);need(isinstance(value,dict),'raw API response is not a JSON object');bodies[receipt['sequence']]=value;inputs[filename]=sha(body)
   if receipt['endpoint']==DDG: need(isinstance(value.get('AbstractText'),str) and isinstance(value.get('AbstractURL'),str) and isinstance(value.get('RelatedTopics'),list),'DDG result is not an Instant Answer response')
   elif receipt['endpoint']==MWMBL: need(value.get('query')==receipt['query'] and isinstance(value.get('results'),list) and type(value.get('number_of_results')) is int and value['number_of_results']==len(value['results'])<=1000,'Mwmbl raw API query/count differs')
   elif receipt['endpoint']==BRAVE: need(isinstance(value.get('query'),dict) and isinstance(value.get('web',{}).get('results'),list) and len(value['web']['results'])<=1000,'Brave raw web-search rows missing')
   else:
    text=value.get('responseData',{}).get('translatedText')
    need(receipt['query'] in {row[1] for row in CASES} and re.search(r'[а-яё]',receipt['query'],re.I) and len(receipt['query'].encode('utf-8'))<=500 and receipt.get('languagePair')=='ru|en','translation did not use the bounded original Russian query')
    need(str(value.get('responseStatus'))=='200' and value.get('quotaFinished') is not True and isinstance(text,str) and 0<len(text.strip())<=512 and not re.search(r'[\x00-\x1f\x7f<>]',text) and re.search(r'[a-z]',text,re.I),'actual translation response is invalid or quota limited')
  else:
   need('filename' not in receipt and 'sha256' not in receipt and 'bytes' not in receipt and isinstance(receipt.get('error',{}).get('code'),str),'failed Chromium receipt contains invented response bytes')
 # A provider query may differ only when the actual fixed translation API
 # supplied those exact bytes. Arbitrary extra queries cannot join the ledger.
 original_queries={row[1] for row in CASES}
 translated_queries={bodies[row['sequence']]['responseData']['translatedText'].strip() for row in network if row['ok'] and row['endpoint']==TRANSLATION}
 for receipt in network:
  need(receipt['query'] in original_queries or receipt['endpoint']==MWMBL and receipt['query'] in translated_queries,'unrelated query was mixed into the public response ledger')
 cases=facts.get('cases');need(isinstance(cases,list) and len(cases)==3,'all real public cases are mandatory')
 result_counts=[]
 for entry,(name,query,topic,page_count) in zip(cases,CASES):
  need((entry.get('name'),entry.get('query'),entry.get('expectedTopic'))==(name,query,topic) and entry.get('ok') is True and entry.get('ownerTopicCovered') is True and not entry.get('error') and not entry.get('relevanceFailure') and not entry.get('stopAfterDenial'),'exact owner/control query is missing, irrelevant or denied')
  need(finite(entry.get('startedAt')) and finite(entry.get('finishedAt')) and entry['startedAt']<entry['finishedAt'] and finite(entry.get('elapsedMs')) and abs(entry['elapsedMs']-(entry['finishedAt']-entry['startedAt']))<=1,'case timing differs')
  pages=entry.get('pages');need(isinstance(pages,list) and len(pages)==page_count,'actual requested public pages missing');seen=set();revision=None;provider_id=None;first_hashes=None;first_translation=None
  for index,page in enumerate(pages,1):
   request='public635-'+name+'-'+str(index);result=page.get('result',{});proof=page.get('proof',{});provider=result.get('provider',{})
   need(page.get('page')==index and page.get('requestId')==request and finite(page.get('startedAt')) and finite(page.get('completedAt')) and entry['startedAt']<=page['startedAt']<=page['completedAt']<=entry['finishedAt'],'actual IPC page timing/request binding differs')
   need(result.get('query')==query and result.get('page')==index and result.get('requestId')==request and positive(result.get('revision')) and result.get('ok') is not False,'public query, page or revision was rewritten')
   current=provider.get('id');need(current in ('brave','mwmbl') and provider.get('kind')=='web-search' and provider.get('limited') is (current=='mwmbl') and provider.get('pagination')==('remote' if current=='brave' else 'snapshot'),'reference answers/fixtures cannot stand in for API web-search cards')
   if index==1: revision=result['revision'];provider_id=current
   else: need(revision==result['revision'] and provider_id==current,'pagination changed provider or query revision')
   endpoint=BRAVE if current=='brave' else MWMBL
   provider_query=query;translation_proof=None;originals=[];translations=[]
   translated=result.get('translatedQuery')
   if translated:
    need(current=='mwmbl' and isinstance(translated,str) and translated!=query and result.get('translation')=={'provider':'mymemory','originalQuery':query,'translatedQuery':translated,'from':'ru','to':'en'},'query expansion metadata differs from the original user query')
    need(isinstance(result.get('notice'),str) and 'MyMemory' in result['notice'] and translated in result['notice'],'translated provider query was hidden from the user')
    originals=[row for row in network if row['ok'] and row['endpoint']==MWMBL and row['query']==query]
    translations=[row for row in network if row['ok'] and row['endpoint']==TRANSLATION and row['query']==query and row.get('languagePair')=='ru|en' and bodies[row['sequence']]['responseData']['translatedText'].strip()==translated]
    need(originals and translations,'expanded page lacks actual original-query or translation response bytes')
    need(any(original['finishedAt']<=translation['startedAt'] for original in originals for translation in translations),'query expansion happened before the original API request')
    provider_query=translated;translation_proof={'originalQuery':query,'providerQuery':translated,'originalResponseSHA256':[row['sha256'] for row in originals],'translationResponseSHA256':[row['sha256'] for row in translations]}
   else:need(not result.get('translation'),'query expansion metadata exists without a translated query')
   need(proof.get('translationProof')==translation_proof,'query expansion proof differs from actual original and translated response bytes')
   if index==1:first_translation=translation_proof
   else:need(translation_proof==first_translation,'snapshot query expansion changed between pages')
   receipts=[row for row in network if row['ok'] and row['endpoint']==endpoint and row['query']==provider_query and (current!='brave' or row.get('offset')==str(index-1))]
   need(receipts,'returned page has no actual provider body');sources={}
   if translations:need(any(translation['finishedAt']<=receipt['startedAt'] for translation in translations for receipt in receipts),'translated provider search preceded the real translation response')
   need(all(entry['startedAt']<=row['startedAt']<=row['finishedAt']<=entry['finishedAt'] for row in originals+translations+receipts),'provider/translation bytes belong to another public case')
   for receipt in receipts:
    value=bodies[receipt['sequence']];rows=value['web']['results'] if current=='brave' else value['results']
    for row in rows:
     need(isinstance(row,dict) and isinstance(row.get('url'),str) and isinstance(row.get('title'),str),'raw provider web row is malformed')
     try: sources[web_url(row['url'])]=row
     except (ValueError,UnicodeError): continue
   hashes=list(dict.fromkeys(row['sha256'] for row in receipts));need(proof.get('sourceResponseSHA256')==hashes,'page proof is not bound to the actual raw provider body')
   if index==1:first_hashes=hashes
   elif current=='mwmbl':need(hashes==first_hashes,'snapshot pagination was replaced by a second unrelated query')
   rows=result.get('results');need(isinstance(rows,list) and 0<len(rows)<=24 and proof.get('resultCount')==len(rows) and proof.get('distinct') is True,'empty or unbounded public page')
   topics=[];ids=set()
   for row in rows:
    need(isinstance(row,dict) and isinstance(row.get('id'),str) and re.fullmatch(r'r_[0-9a-f]{24}',row['id']) and row['id'] not in ids and isinstance(row.get('title'),str) and row['title'].strip(),'public result identity/title absent')
    url=web_url(row.get('url'));need(url==row['url'] and url not in seen and url in sources,'invented or duplicate URL outside actual API response');seen.add(url);ids.add(row['id']);original=sources[url]
    text='\n'.join(original.get(key,'') for key in ('url','title','content','description') if isinstance(original.get(key,''),str)).lower()
    if any(term in text for term in topic):topics.append(row['id'])
   need(proof.get('topicMatches')==topics,'topic coverage was fabricated from unrelated raw rows')
   if index==1: need(topics,'the real first API page does not cover the exact requested topic')
   if index<page_count: need(result.get('hasMore') is True,'no real next API/snapshot page was available')
   if name=='forced-primary-failure':need(current=='mwmbl','controlled primary failure did not reach the real API fallback')
   result_counts.append(len(rows))
 fault=facts.get('controlledPrimaryFailure',{});primary=BRAVE if configured else DDG;blocked=fault.get('blocked')
 need(fault.get('endpoint')==primary and fault.get('mechanism')=='isolated Chromium webRequest cancellation' and fault.get('caseName')==CASES[2][0] and isinstance(blocked,list) and 0<len(blocked)<=4 and all(row.get('endpoint')==primary and row.get('query')==CASES[2][1] and row.get('method')=='GET' and finite(row.get('at')) for row in blocked),'actual controlled primary cancellation receipt missing')
 need(any(row['query']==CASES[2][1] and row['endpoint']==primary and not row['ok'] and row.get('error',{}).get('causeCode')=='ERR_BLOCKED_BY_CLIENT' for row in network),'Chromium did not observe the cancelled primary request')
 native=facts.get('inputs');need(isinstance(native,list) and len(native)==1 and native[0] in owner.get('nativeInputs',[]),'public native footer input missing from owner ledger');N['input_event'](native[0],platform,'#mouse-search-button')
 return{'ok':True,'version':'6.0.35','platform':platform,'arch':arch,'pid':pid,'reportSha256':sha(raw),'apiOnly':True,'ownerQuery':CASES[0][1],'ownerTopicCovered':True,'cases':3,'pageResultCounts':result_counts,'controlledPrimaryFailure':True,'inputs':inputs,'nativeCaptures':[]}
