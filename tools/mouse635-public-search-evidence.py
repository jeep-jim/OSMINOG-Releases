#!/usr/bin/env python3
"""Independently bind selected-engine native DOM, original order and OS frames."""
import base64
from datetime import datetime
from html.parser import HTMLParser
import ipaddress
import json
import math
from pathlib import Path
import re
import runpy
from urllib.parse import parse_qsl, quote, quote_plus, urljoin, urlsplit, urlunsplit

N=runpy.run_path(str(Path(__file__).with_name('mouse635-native-evidence.py')))
need,finite,positive,sha=N['need'],N['finite'],N['positive'],N['sha']
NAME='mouse-635-public-search.json'
CONTRACT='selected-engine-native-serp-v1'
MARKER='MOUSE_635_PUBLIC_SEARCH_CONTRACT_PASS'
LIVE_MARKER='MOUSE_635_PUBLIC_SEARCH_PASS'
UNVERIFIED_MARKER='MOUSE_635_PUBLIC_SEARCH_LIVE_TOPIC_UNVERIFIED'
CAPTURES=['mouse-635-public-search-engine-menu.png','mouse-635-public-search-source.png','mouse-635-public-search-tiles.png']
CASES=[('owner-russian','новости про антропик',['anthropic','антропик']),('control','Python documentation',['python'])]
ENGINES={
 'google':{'name':'Google','base':'https://www.google.com/search?q=','hosts':['google.com','www.google.com','google.ru','www.google.ru','consent.google.com','accounts.google.com','sorry.google.com']},
 'bing':{'name':'Bing','base':'https://www.bing.com/search?q=','hosts':['bing.com','www.bing.com','cn.bing.com']},
 'duckduckgo':{'name':'DuckDuckGo','base':'https://duckduckgo.com/?q=','hosts':['duckduckgo.com','www.duckduckgo.com','html.duckduckgo.com','lite.duckduckgo.com']},
 'yandex':{'name':'Яндекс','base':'https://yandex.ru/search/?text=','hosts':['yandex.ru','www.yandex.ru','yandex.com','www.yandex.com','ya.ru','yandex.by','yandex.kz','yandex.uz','yandex.com.tr']},
}
ERRORS={'SEARCH_ENGINE_CHALLENGE','SEARCH_ENGINE_LAYOUT','SEARCH_ENGINE_REDIRECT','SEARCH_ENGINE_CLOSED','SEARCH_TIMEOUT','SEARCH_NETWORK','SEARCH_PROXY','SEARCH_DNS','SEARCH_TLS','SEARCH_HTTP','SEARCH_BLOCKED','SEARCH_RATE_LIMIT'}
SELECTORS={'google':'#search h3, #rso h3','bing':'#b_results .b_algo','duckduckgo':'article[data-testid="result"], .result.results_links','yandex':'.serp-item'}
SNIPPETS={'google':['.VwiC3b','.IsZvec','[data-sncf]','.aCOpRe','.yXK7lf'],'bing':['.b_caption p','p.b_lineclamp2','.b_snippet'],'duckduckgo':['[data-testid="result-snippet"]','[data-result="snippet"]','.result__snippet'],'yandex':['.OrganicTextContentSpan','.Organic-Text','.TextContainer','.text-container']}
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
PAINT_SOURCE='same-WebContents readbacks matched to actual native display'
PAINT_POLICY={'stepDIP':4,'insetDIP':16,'tolerance':3,'minimumSamples':256,'minimumStableFraction':.25,'minimumColors':4,'minimumInformative':64,'minimumMatchFraction':.99,'minimumInformativeMatchFraction':.95,'minimumQuadrantSamples':16}
SOURCE_IDENTITY=('source','navigationEpoch','webContentsId','url','bounds','zoom','visible','attached','topmost','surfaceHeld','tilesHidden','window','organicSignature')
TILE_IDENTITY=('id','resultURL','recordURL','url','webContentsId','navigationEpoch','bounds','visible','viewVisible','attached','zoom')


def rgba(image,x,y):
 need(type(x) is int and type(y) is int and 0<=x<image['width'] and 0<=y<image['height'],'paint sample is outside the actual image')
 channels=image['channels'];need(channels in (3,4),'paint reference must decode to RGB or RGBA')
 at=(y*image['width']+x)*channels;value=list(image['pixels'][at:at+channels])
 if channels==3:value.append(255)
 return value


def compare_paint(before,after,candidate,bounds,mapping):
 """Recompute stable, informative native pixels; no image resizing or masking."""
 N['rect'](bounds);need(bounds['width']>0 and bounds['height']>0,'paint view has no native area')
 width,height=before['width'],before['height']
 need(positive(width) and positive(height) and (width,height)==(after['width'],after['height']),'same-WebContents readback dimensions changed')
 need(all(finite(mapping.get(key)) for key in ('originX','originY','scaleX','scaleY')) and 0<mapping['scaleX']<=8 and 0<mapping['scaleY']<=8,'paint native mapping is invalid')
 sx,sy=width/bounds['width'],height/bounds['height'];need(0<sx<=8 and 0<sy<=8,'paint readback scale is invalid')
 trim_x=math.ceil(min(PAINT_POLICY['insetDIP'],bounds['width']/4)*sx);trim_y=math.ceil(min(PAINT_POLICY['insetDIP'],bounds['height']/4)*sy)
 step_x=max(1,math.ceil(PAINT_POLICY['stepDIP']*sx));step_y=max(1,math.ceil(PAINT_POLICY['stepDIP']*sy))
 quadrants=[{'samples':0,'stable':0,'matched':0} for _ in range(4)];histogram={};stable=[];total=matched=0
 close=lambda left,right:all(abs(left[index]-right[index])<=PAINT_POLICY['tolerance'] for index in range(3))
 for y in range(trim_y,height-trim_y,step_y):
  for x in range(trim_x,width-trim_x,step_x):
   total+=1;quadrant=quadrants[(2 if y>=height/2 else 0)+(1 if x>=width/2 else 0)];quadrant['samples']+=1
   first,last=rgba(before,x,y),rgba(after,x,y)
   px=math.floor(mapping['originX']+(bounds['x']+(x+.5)/sx)*mapping['scaleX']);py=math.floor(mapping['originY']+(bounds['y']+(y+.5)/sy)*mapping['scaleY'])
   actual=rgba(candidate,px,py)
   if first[3]!=255 or last[3]!=255 or not close(first,last):continue
   quadrant['stable']+=1;bucket=tuple(channel>>4 for channel in first[:3]);histogram[bucket]=histogram.get(bucket,0)+1
   hit=actual[3]==255 and close(actual,first) and close(actual,last);stable.append((bucket,hit))
   if hit:matched+=1;quadrant['matched']+=1
 count=len(stable);dominant=max(histogram,key=histogram.get) if histogram else None
 informative=sum(bucket!=dominant for bucket,_ in stable);informative_matched=sum(bucket!=dominant and hit for bucket,hit in stable)
 accepted=(count>=PAINT_POLICY['minimumSamples'] and count/total>=PAINT_POLICY['minimumStableFraction'] and len(histogram)>=PAINT_POLICY['minimumColors'] and informative>=PAINT_POLICY['minimumInformative'] and matched/count>=PAINT_POLICY['minimumMatchFraction'] and informative_matched/informative>=PAINT_POLICY['minimumInformativeMatchFraction'] and all(row['stable']>=PAINT_POLICY['minimumQuadrantSamples'] for row in quadrants))
 return {'policy':dict(PAINT_POLICY),'totalSamples':total,'stableSamples':count,'matchedSamples':matched,'mismatchedSamples':count-matched,'informativeSamples':informative,'informativeMatchedSamples':informative_matched,'referenceColors':len(histogram),'quadrants':quadrants,'accepted':accepted}


def same_fields(before,after,fields,label):
 need(isinstance(before,dict) and isinstance(after,dict) and all(key in before and before[key]==after.get(key) for key in fields),label)


def interval(value,budget,label):
 need(isinstance(value,dict) and value.get('budgetMs')==budget and all(finite(value.get(key)) for key in ('startedAt','finishedAt','elapsedMs')) and 0<=value['startedAt']<=value['finishedAt'] and 0<=value['elapsedMs']<=budget and abs(value['elapsedMs']-value['finishedAt']+value['startedAt'])<=1,label+' timing differs')


def paint_evidence(evidence,frame,kind,validate_state,stable_state,inputs):
 paint=frame.get('paint');interval(paint,4500,kind+' actual paint')
 need(not paint.get('error') and paint.get('source')==PAINT_SOURCE and paint.get('maxFrames')==20 and finite(paint.get('deadline')) and paint['startedAt']<paint['deadline']<=paint['startedAt']+4500 and paint['finishedAt']<=paint['deadline'],'paint acquisition lacks its single bounded deadline')
 attempts=paint.get('attempts');need(isinstance(attempts,list) and 1<=len(attempts)<=20 and type(paint.get('acceptedIndex')) is int and paint['acceptedIndex']==len(attempts)-1,'paint attempts or last accepted frame missing')
 need(frame.get('before')==attempts[-1].get('before') and frame.get('after')==attempts[-1].get('after'),'canonical paint states do not belong to the accepted native frame')
 validate_state(frame.get('before'));validate_state(frame.get('after'));stable_state(frame['before'],frame['after'])
 captures=[];previous=paint['startedAt'];reference_names=set()
 for index,attempt in enumerate(attempts,1):
  need(isinstance(attempt,dict) and not attempt.get('error') and attempt.get('sequence')==index and all(finite(attempt.get(key)) for key in ('startedAt','finishedAt','elapsedMs')) and previous<=attempt['startedAt']<=attempt['finishedAt']<=paint['finishedAt'] and abs(attempt['elapsedMs']-attempt['finishedAt']+attempt['startedAt'])<=1,'paint attempt order or timing differs')
  previous=attempt['finishedAt'];first,last=attempt.get('before'),attempt.get('after');validate_state(first);validate_state(last)
  stable_state(frame['before'],first);stable_state(first,last);stable_state(last,frame['after'])
  subjects=[{'id':'source','webContentsId':first['webContentsId'],'bounds':first['bounds']}] if kind=='source' else first['pages']
  before,after,comparisons=attempt.get('referencesBefore'),attempt.get('referencesAfter'),attempt.get('comparisons')
  need(all(isinstance(rows,list) and len(rows)==len(subjects) for rows in (before,after,comparisons)),'paint references do not cover the exact native subjects')
  capture=attempt.get('capture');need(isinstance(capture,dict),'paint attempt OS receipt missing')
  canonical=CAPTURES[1 if kind=='source' else 2];expected=canonical if index==len(attempts) else canonical[:-4]+'-attempt-'+str(index).zfill(2)+'.png'
  need(capture.get('filename')==expected and capture.get('contentBounds')==first['window']['contentBounds'],'paint attempt native filename/window differs')
  image=evidence.screen(capture);inputs[capture['filename']]=capture['sha256'];inputs[capture['displayFilename']]=capture['displaySha256'];captures.append(capture);accepted=[]
  for subject_index,(subject,left,right,saved) in enumerate(zip(subjects,before,after,comparisons),1):
   decoded=[]
   for suffix,row in (('before',left),('after',right)):
    need(isinstance(row,dict) and all(row.get(key)==subject.get(key) for key in ('id','webContentsId','bounds')),'paint readback belongs to another native view')
    meta=row.get('image');name='mouse-635-public-search-'+kind+'-reference-'+str(index).zfill(2)+'-'+str(subject_index).zfill(2)+'-'+suffix+'.png'
    need(isinstance(meta,dict) and meta.get('source')=='WebContents.capturePage' and meta.get('filename')==name and name not in reference_names,'same-WebContents PNG reference identity differs')
    reference_names.add(name);decoded.append(evidence.png(meta));inputs[name]=meta['sha256']
   actual=compare_paint(*decoded,image,subject['bounds'],capture['mapping'])
   need(isinstance(saved,dict) and saved.get('id')==subject['id'] and saved.get('webContentsId')==subject['webContentsId'] and all(saved.get(key)==value for key,value in actual.items()),'saved paint metrics differ from independently decoded actual pixels')
   accepted.append(actual['accepted'])
  actual_accepted=all(accepted);need(type(attempt.get('accepted')) is bool and attempt['accepted']==actual_accepted and actual_accepted==(index==len(attempts)),'native paint failed or the accepted frame was not the first matching attempt')
 return captures


def jslen(value):
 return len(value.encode('utf-16-le','surrogatepass'))//2


def clean(value,limit):
 value=re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]','',value)
 return re.sub(r'[\t\n\v\f\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]+',' ',value).strip().encode('utf-16-le','surrogatepass')[:limit*2].decode('utf-16-le','surrogatepass')


class Node:
 def __init__(self,tag='',attrs=(),parent=None,start=0):
  self.tag=tag;self.attrs=dict(attrs);self.parent=parent;self.start=start;self.end=None;self.children=[];self.parts=[]
 def text(self):return ''.join(part.text() if isinstance(part,Node) else part for part in self.parts)
 def chain(self):
  value=self
  while value is not None:
   yield value;value=value.parent


class Document(HTMLParser):
 """Parse the browser's serialized DOM without executing its scripts."""
 def __init__(self,source):
  super().__init__(convert_charrefs=True);self.source=source;self.root=Node();self.stack=[self.root];self.lines=[0]
  for match in re.finditer('\n',source):self.lines.append(match.end())
  self.feed(source);self.close()
  roots=[node for node in self.root.children if node.tag=='html'];need(len(roots)==1,'actual DOM must contain one documentElement');self.element=roots[0]
 def position(self):
  line,column=self.getpos();return self.lines[line-1]+column
 def handle_starttag(self,tag,attrs):
  parent=self.stack[-1];node=Node(tag,attrs,parent,self.position());parent.children.append(node);parent.parts.append(node)
  if tag in VOID:node.end=node.start+len(self.get_starttag_text())
  else:self.stack.append(node)
 def handle_startendtag(self,tag,attrs):
  self.handle_starttag(tag,attrs)
  if tag not in VOID:
   node=self.stack.pop();node.end=node.start+len(self.get_starttag_text())
 def handle_endtag(self,tag):
  for index in range(len(self.stack)-1,0,-1):
   if self.stack[index].tag==tag:
    end=self.source.find('>',self.position());need(end>=0,'unfinished DOM close tag')
    for node in self.stack[index:]:node.end=end+1
    self.stack=self.stack[:index];return
 def handle_data(self,data):self.stack[-1].parts.append(data)
 def at(self,path,root=None):
  need(isinstance(path,list) and len(path)<=128 and all(type(value) is int and 0<=value<100000 for value in path),'invalid organic element path')
  node=root or self.element
  for index in path:
   need(index<len(node.children),'organic element path is absent from raw DOM');node=node.children[index]
  return node
 def fragment(self,node):
  need(node.end is not None,'organic element has no complete raw fragment');return self.source[node.start:node.end]


def has_class(node,value):return value in (node.attrs.get('class') or '').split()


def contains(parent,node):return any(item is parent for item in node.chain())


def selector_matches(node,selector,scope):
 # Only the fixed collector selector grammar, not arbitrary CSS evaluation.
 def simple(item,token):
  match=re.fullmatch(r'([a-z][a-z0-9]*)?(?:\.([A-Za-z0-9_-]+)|\[([A-Za-z0-9_-]+)(?:="([^"]*)")?\])?',token)
  need(match is not None,'unreviewed organic selector syntax')
  tag,css,attribute,value=match.groups()
  return (tag is None or item.tag==tag) and (css is None or has_class(item,css)) and (attribute is None or attribute in item.attrs and (value is None or item.attrs[attribute]==value))
 tokens=selector.split();need(tokens and len(tokens)<=3,'unreviewed organic selector depth')
 if not contains(scope,node) or not simple(node,tokens[-1]):return False
 current=node.parent
 for token in reversed(tokens[:-1]):
  while current is not None and contains(scope,current) and not simple(current,token):current=current.parent
  if current is None or not contains(scope,current):return False
  current=current.parent
 return True




def organic(engine,container,title,link):
 need(link.tag=='a' and 'href' in link.attrs and contains(container,link) and contains(container,title),'organic title/link are outside the actual result container')
 for node in container.chain():
  attrs=node.attrs
  need(attrs.get('id') not in ('tads','bottomads') and not any(has_class(node,value) for value in ('uEierd','b_ad','b_adTop','result--ad','serp-item_ad')) and 'data-text-ad' not in attrs and attrs.get('data-testid')!='ad' and attrs.get('data-fast-name')!='adv' and attrs.get('data-is-adv')!='true','advertisement cannot stand in for an organic result')
 if engine!='google':need(title is link,'organic heading does not belong to its actual result anchor')
 if engine=='bing':
  need(has_class(container,'b_algo') and any(node.attrs.get('id')=='b_results' for node in container.chain()) and any(node.tag=='h2' and contains(container,node) for node in title.chain()),'Bing node is outside its organic result list')
 elif engine=='google':
  need(title.tag=='h3' and next((node for node in title.chain() if node.tag=='a'),None) is link and any(node.attrs.get('id') in ('search','rso') for node in title.chain()),'Google node is not a search result heading')
  chosen=next((node for node in title.chain() if has_class(node,'MjjYud') or has_class(node,'g') or 'data-hveid' in node.attrs),None) or (title.parent.parent if title.parent else None)
  need(container is chosen,'Google container differs from the closest actual result scope')
 elif engine=='duckduckgo':
  need(container.tag=='article' and container.attrs.get('data-testid')=='result' or has_class(container,'result') and has_class(container,'results_links'),'DuckDuckGo node is outside its organic result list')
 else:need(has_class(container,'serp-item'),'Yandex node is outside its organic result list')


def web_url(value,base=None):
 need(isinstance(value,str) and 0<len(value)<=8192,'web URL missing')
 parsed=urlsplit(urljoin(base or '',value.strip()))
 need(parsed.scheme in ('http','https') and parsed.hostname and parsed.username is None and parsed.password is None,'unsafe result scheme/credentials')
 host=parsed.hostname.encode('idna').decode().lower()
 need(host!='localhost' and not host.endswith(('.localhost','.local','.internal','.home','.lan','.invalid','.test','.onion')) and ('.' in host or ':' in host),'nonpublic or fixture result host')
 try:address=ipaddress.ip_address(host)
 except ValueError:address=None
 if address is not None:need(address.is_global,'nonpublic result address')
 if ':' in host:host='['+host+']'
 port=parsed.port
 if port is not None and port!={'http':80,'https':443}[parsed.scheme]:host+=':'+str(port)
 return urlunsplit((parsed.scheme,host,quote(parsed.path or '/',safe="/:@-._~!$&'()*+,;=%[]"),quote(parsed.query,safe="/:?@-._~!$&'()*+,;=%[]"),quote(parsed.fragment,safe="/:?@-._~!$&'()*+,;=%[]")))


def source_url(value,engine,query,search=True):
 need(isinstance(value,str) and len(value)<=16384 and engine in ENGINES,'native provider URL missing')
 u=urlsplit(value);need(u.scheme=='https' and u.hostname in ENGINES[engine]['hosts'] and u.username is None and u.password is None,'source navigation left the selected engine')
 if search:
  paths=('/','/html/','/html','/lite/','/lite') if engine=='duckduckgo' else ('/search','/search/')
  key='text' if engine=='yandex' else 'q'
  need(u.path in paths and [value for name,value in parse_qsl(u.query,keep_blank_values=True) if name==key]==[query],'actual source URL changed the original query')
 return value


def destination(raw_href,engine,base):
 value=web_url(raw_href,base);u=urlsplit(value)
 if u.scheme=='https' and u.hostname in ENGINES[engine]['hosts']:
  query=dict(parse_qsl(u.query,keep_blank_values=True));target=''
  if engine=='google' and u.path=='/url':target=query.get('q') or query.get('url') or ''
  elif engine=='duckduckgo' and u.path=='/l/':target=query.get('uddg') or ''
  elif engine=='bing' and u.path=='/ck/a':
   encoded=query.get('u','')
   if re.fullmatch(r'a1[A-Za-z0-9_-]+={0,2}',encoded):
    data=encoded[2:];target=base64.urlsafe_b64decode(data+'='*((-len(data))%4)).decode('utf-8')
   elif re.match(r'^https?://',encoded,re.I):target=encoded
  elif engine=='yandex' and re.match(r'^/clck/(?:jsredir|redir)',u.path):target=query.get('url') or ''
  if target:value=web_url(target);u=urlsplit(value)
  else:need(u.path not in ('/url','/ck/a','/l/') and not u.path.startswith('/clck/'),'unresolved provider tracking URL')
  need(not(u.hostname in ENGINES[engine]['hosts'] and (any(key in ('q','text') for key,_ in parse_qsl(u.query)) or u.path in ('/search','/search/'))),'search navigation is not an organic target')
 return value


def canonical_id(value):
 u=urlsplit(value);pairs=[(key,value) for key,value in parse_qsl(u.query,keep_blank_values=True) if not re.match(r'^(?:utm_|fbclid$|gclid$|dclid$|msclkid$)',key,re.I)]
 pairs.sort(key=lambda pair:pair[0].encode('utf-16-be','surrogatepass'))
 enc=lambda value:quote_plus(value,safe='*-._').replace('~','%7E')
 canonical=urlunsplit((u.scheme,u.netloc,u.path,'&'.join(enc(key)+'='+enc(value) for key,value in pairs),''))
 return 'r_'+sha(canonical.encode())[:24]


def wall(value):
 need(isinstance(value,str),'native request timestamp missing')
 try:result=datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()*1000
 except (ValueError,TypeError):result=None
 need(finite(result),'invalid native request timestamp');return result


def signature(rows):
 return sha(json.dumps([[row['title'],row['rawHref'],row['content']] for row in rows],ensure_ascii=False,separators=(',',':')).encode())


def dom_rows(receipt):
 snapshot=receipt.get('snapshot');need(isinstance(snapshot,dict),'actual provider DOM missing')
 html=snapshot.get('html');need(isinstance(html,str) and 0<jslen(html)<=4*1024**2 and snapshot.get('htmlLength')==jslen(html) and snapshot.get('htmlTruncated') is False,'actual DOM is missing, oversized or truncated')
 content=html.encode();need(receipt.get('htmlBytes')==len(content) and receipt.get('htmlSha256')==sha(content),'actual serialized DOM bytes/hash differ')
 doc=Document(html);rows=snapshot.get('rows');need(isinstance(rows,list) and len(rows)<=80 and receipt.get('organicSignature')==signature(rows),'organic DOM signature differs')
 base=snapshot['documentURL'];bases=[node for node in doc.element.children if node.tag=='head']
 if bases:
  base_nodes=[node for node in bases[0].children if node.tag=='base' and node.attrs.get('href')]
  if base_nodes:base=urljoin(base,base_nodes[0].attrs['href'])
 derived=[];previous_title=-1
 for index,row in enumerate(rows,1):
  need(row.get('rank')==index and row.get('rendered') is True and type(row.get('inViewport')) is bool and row.get('fragmentTruncated') is False,'organic rank/visibility/fragment missing')
  N['rect'](row.get('bounds'));need(row['bounds']['width']>0 and row['bounds']['height']>0,'organic heading has no actual geometry')
  container=doc.at(row.get('containerPath'));link=doc.at(row.get('linkPath'),container);title=doc.at(row.get('titlePath'),container);snippet=doc.at(row['snippetPath'],container) if row.get('snippetPath') is not None else None
  need(title.start>previous_title,'organic node order differs from actual document order');previous_title=title.start
  need(row.get('rawOuterHTML')==doc.fragment(container),'organic fragment does not equal the element at its raw DOM path')
  need(row.get('selector')==SELECTORS[receipt['engine']] and (row.get('snippetSelector') in SNIPPETS[receipt['engine']] if snippet else row.get('snippetSelector')==''),'organic extractor selector identity differs')
  organic(receipt['engine'],container,title,link)
  if snippet is not None:need(selector_matches(snippet,row['snippetSelector'],container),'snippet path does not match its actual organic selector')
  title_text,content_text=clean(title.text(),300),clean(snippet.text(),1800) if snippet else ''
  need(row.get('title')==title_text and bool(title_text) and row.get('content')==content_text and row.get('rawHref')==link.attrs.get('href'),'title, snippet or raw href differs from actual DOM text')
  try:target=destination(link.attrs['href'],receipt['engine'],base)
  except (ValueError,TypeError,UnicodeError):target=None
  if target is not None:need(row.get('url')==web_url(link.attrs['href'],base),'browser link URL does not resolve from the actual href/base')
  derived.append({'rank':index,'title':title_text,'content':content_text,'url':target,'rawHref':link.attrs['href']})
 next_row=snapshot.get('next')
 if next_row:
  next_node=doc.at(next_row.get('path'));need(next_node.tag=='a' and next_node.attrs.get('href')==next_row.get('rawHref'),'next page is not the raw provider link')
  try:next_url=web_url(next_node.attrs['href'],base)
  except ValueError:next_url=None
  if next_url is not None:need(next_url==next_row.get('url'),'next page does not resolve from its actual href')
 return derived


def validate_receipt(receipt,engine,query,request_id,page=1):
 need(isinstance(receipt,dict) and receipt.get('schema')==1 and receipt.get('kind')=='native-serp' and receipt.get('engine')==engine and receipt.get('engineName')==ENGINES[engine]['name'],'native selected-engine receipt identity differs')
 need((receipt.get('requestId'),receipt.get('query'),receipt.get('page'),receipt.get('filter'))==(request_id,query,page,'all') and receipt.get('private') is False and receipt.get('preference')=={'engine':engine,'name':ENGINES[engine]['name'],'private':False},'request or canonical preference was substituted')
 need(positive(receipt.get('webContentsId')) and type(receipt.get('navigationEpoch')) is int and receipt['navigationEpoch']>=0,'actual native document identity missing')
 source_url(receipt.get('requestedURL'),engine,query)
 if page==1:need(receipt['requestedURL']==ENGINES[engine]['base']+quote(query,safe="~!*'()-._"),'first native URL did not use the selected browser preference')
 begin,end=wall(receipt.get('startedAtISO')),wall(receipt.get('finishedAtISO'))
 need(0<=end-begin<=17000 and finite(receipt.get('elapsedMs')) and 0<=receipt['elapsedMs']<=17000,'native search exceeded its bounded deadline')
 navigation=receipt.get('navigation');need(isinstance(navigation,list) and 0<len(navigation)<=100 and any(row.get('event')=='start' and row.get('url')==receipt['requestedURL'] for row in navigation),'actual source navigation start missing')
 for row in navigation:need(isinstance(row.get('event'),str) and isinstance(row.get('url'),str) and finite(row.get('at')) and type(row.get('epoch')) is int and row['epoch']>=0,'native navigation event malformed')
 snapshot=receipt.get('snapshot')
 if snapshot is None:
  need(receipt.get('ok') is False and 'htmlBytes' not in receipt and 'htmlSha256' not in receipt and receipt.get('organicSignature')=='','failed navigation has invented DOM bytes');return []
 need(snapshot.get('schema')==1 and snapshot.get('engine')==engine and snapshot.get('documentURL')==receipt.get('finalURL') and snapshot.get('documentReadyState') in ('interactive','complete'),'actual provider document changed during extraction')
 need(begin<=wall(snapshot.get('extractedAtISO'))<=end,'DOM snapshot lies outside its actual request')
 viewport=snapshot.get('viewport',{});need(positive(viewport.get('width')) and positive(viewport.get('height')),'actual provider viewport missing')
 return dom_rows(receipt)


def reply_proof(reply,receipt,query,engine,request_id,topic,page=1,previous=()):
 rows=validate_receipt(receipt,engine,query,request_id,page)
 identity={'webContentsId':receipt['webContentsId'],'navigationEpoch':receipt['navigationEpoch'],'htmlSha256':receipt.get('htmlSha256'),'organicSignature':receipt['organicSignature']}
 if reply.get('ok') is False:
  error=reply.get('error',{});need(receipt.get('ok') is False and error.get('code') in ERRORS and receipt.get('error',{}).get('code')==error['code'] and receipt.get('results')==[],'unrelated implementation error or success was relabelled as provider unavailability')
  if error['code']=='SEARCH_ENGINE_CHALLENGE':need(receipt.get('snapshot',{}).get('challenge'),'challenge outcome has no actual provider challenge DOM')
  return {'outcome':receipt['outcome'],'errorCode':error['code'],**identity,'topicMatches':[],'sourceNodeRanks':[],'resultCount':0,'originalQueryPreserved':True}
 snapshot=receipt['snapshot'];need(receipt.get('ok') is True and not snapshot.get('challenge'),'challenged source cannot become successful results');source_url(snapshot['documentURL'],engine,query)
 need((reply.get('requestId'),reply.get('query'),reply.get('page'))==(request_id,query,page) and positive(reply.get('revision')),'actual IPC query/revision differs')
 need(reply.get('provider')=={'id':engine,'name':ENGINES[engine]['name'],'kind':'web-search','transport':'native-serp','pagination':'remote','limited':True} and reply.get('instantAnswer') is None and reply.get('translation') is None and reply.get('translatedQuery')=='','another provider, translation or reference answer replaced native results')
 results=reply.get('results');need(isinstance(results,list) and len(results)<=24 and type(reply.get('hasMore')) is bool,'bounded result page missing')
 expected_outcome='results' if results else 'empty' if snapshot.get('empty') else 'filtered'
 need(reply.get('outcome')==expected_outcome and receipt.get('outcome')==expected_outcome,'empty/filtered/provider outcome is misleading')
 seen={canonical_id(url) for url in previous};expected=[]
 for row in rows:
  if not row['url']:continue
  identifier=canonical_id(row['url'])
  if identifier in seen:continue
  seen.add(identifier);expected.append({**row,'id':identifier,'source':urlsplit(row['url']).hostname})
  if len(expected)==24:break
 need(len(results)==len(expected),'original organic rows were omitted or invented')
 topics=[];ranks=[]
 for result,raw in zip(results,expected):
  need(all(result.get(key)==raw[key] for key in ('id','url','title','content','source')),'result order/title/URL/snippet differs from the actual organic DOM')
  need(result in receipt.get('results',[]),'actual native reply was changed in the IPC controller')
  if any(term in (raw['title']+'\n'+raw['content']+'\n'+raw['url']).lower() for term in topic):topics.append(result['id'])
  ranks.append(raw['rank'])
 if page==1:need(receipt.get('results')==results,'first result page changed after native extraction')
 if reply['hasMore']:
  next_row=snapshot.get('next');need(isinstance(next_row,dict),'invented pagination without raw next link');source_url(next_row.get('url'),engine,query);need(next_row['url']!=snapshot['documentURL'],'next page repeats current source')
 return {'outcome':reply['outcome'],**identity,'topicMatches':topics,'sourceNodeRanks':ranks,'resultCount':len(results),'originalQueryPreserved':True}


def source_state(state,receipt,engine):
 need(isinstance(state,dict),'actual visible source state missing')
 N['flags'](state,('visible','attached','topmost','surfaceHeld','tilesHidden'),'source view was hidden, covered or mixed with live tile views')
 need(state.get('webContentsId')==receipt['webContentsId'] and state.get('navigationEpoch')==receipt['navigationEpoch'] and state.get('url')==receipt['finalURL'] and state.get('organicSignature')==receipt['organicSignature'],'native source frame belongs to another document or organic content')
 expected={key:receipt[key] for key in ('requestId','engine','engineName','query','page','filter','requestedURL','finalURL','webContentsId','private','preference','navigationEpoch')}
 expected.update({key:receipt[key] for key in ('project','desk') if key in receipt})
 need(state.get('source')==expected,'read-only native source handle differs from actual request ownership')
 N['rect'](state.get('bounds'));window=state.get('window',{});N['flags'](window,('visible','focused'),'source window was not foreground');N['rect'](window.get('contentBounds'))
 need(window.get('minimized') is False and state['bounds']=={'x':0,'y':0,'width':window['contentBounds']['width'],'height':window['contentBounds']['height']} and finite(state.get('zoom')) and state['zoom']>0,'actual source bounds/zoom missing')
 snapshot=state.get('snapshot',{});need(snapshot.get('engine')==engine and snapshot.get('documentURL')==receipt['finalURL'] and snapshot.get('documentReadyState') in ('interactive','complete') and snapshot.get('visibilityState')=='visible' and signature(snapshot.get('rows',[]))==receipt['organicSignature'],'visible source DOM does not match extracted organic text')


def stable_source(before,after):
 same_fields(before,after,SOURCE_IDENTITY,'native source changed during actual paint')
 same_fields(before['snapshot'],after['snapshot'],('viewport',),'native source viewport changed during actual paint')


def tile_state(state,entry,selected_ids):
 need(isinstance(state,dict) and state.get('query')==entry['query'] and state.get('revision')==entry['pages'][0]['result']['revision'] and state.get('active') is True and state.get('blocked') is False,'live tile query/revision or foreground surface differs')
 window=state.get('window',{});N['flags'](window,('visible','focused'),'tile window was not foreground');content=N['rect'](window.get('contentBounds'));need(window.get('minimized') is False,'tile window was minimized')
 registry=state.get('registry',{});need(registry.get('active') is True and registry.get('suspended') is False and registry.get('reason')=='' and registry.get('revision')==state['revision'],'actual live tile registry was blocked or stale')
 results=entry['pages'][0]['result']['results'];registered=registry.get('pages');pages=state.get('pages')
 count=min(2,len(results));need(count>0 and isinstance(registered,list) and [row.get('id') for row in registered]==[row['id'] for row in results] and isinstance(pages,list) and len(pages)==count,'actual first result registry or live tile subjects missing')
 visible=[row for row in registered if row.get('visible') is True][:count]
 need(len(visible)==count and [row.get('id') for row in pages]==selected_ids==[row.get('id') for row in visible],'live tile proof skipped or replaced the first visible results')
 result_by_id={row['id']:row for row in results}
 for page,record in zip(pages,visible):
  N['flags'](page,('visible','viewVisible','attached'),'a selected live site was hidden or detached')
  need(record.get('live') is True and record.get('error')=='' and page.get('error')=='' and type(page.get('loading')) is bool and type(record.get('loading')) is bool,'actual live site has an error or missing load state')
  need(page.get('resultURL')==result_by_id[page['id']]['url'] and page.get('recordURL')==page.get('url')==page.get('document',{}).get('url'),'tile URL lost its original organic result or actual redirect ownership')
  web_url(page.get('url'));need(positive(page.get('webContentsId')) and type(page.get('navigationEpoch')) is int and page['navigationEpoch']>=0 and finite(page.get('zoom')) and page['zoom']>0,'actual site WebContents identity/zoom missing')
  need(all(page.get(key)==record.get(key) for key in ('id','url','webContentsId','navigationEpoch','bounds')),'live site differs from its native registry')
  bounds=N['rect'](page.get('bounds'));need(bounds['width']>0 and bounds['height']>0 and bounds['x']>=0 and bounds['y']>=0 and bounds['x']+bounds['width']<=content['width'] and bounds['y']+bounds['height']<=content['height'],'live tile bounds leave the visible native window')
  doc=page.get('document');need(isinstance(doc,dict) and doc.get('readyState') in ('interactive','complete') and doc.get('visibilityState')=='visible' and finite(doc.get('timeOrigin')) and doc['timeOrigin']>0,'live site document has not become visible/interactive')
  text=doc.get('bodyText');need(isinstance(doc.get('title'),str) and isinstance(text,str) and 80<=jslen(text)<=2000 and type(doc.get('bodyTextLength')) is int and doc['bodyTextLength']>=jslen(text),'live site document has no substantive actual body text')
  viewport=doc.get('viewport',{});need(positive(viewport.get('width')) and positive(viewport.get('height')),'live site viewport missing')
  need(any(term in (doc['title']+'\n'+text).lower() for term in entry['expectedTopic']),'actual visible tile document does not cover the owner topic')
  navigation=page.get('navigation');need(isinstance(navigation,list) and 2<=len(navigation)<=100 and any(row.get('event')=='start' and row.get('url')==page['resultURL'] for row in navigation) and any(row.get('event')=='commit' and row.get('url')==page['url'] for row in navigation),'actual tile navigation does not bind the organic URL to the current document')
  need(all(row.get('event') in ('start','redirect','commit','dom-ready','failed') and isinstance(row.get('url'),str) and finite(row.get('at')) for row in navigation),'actual tile navigation ledger malformed')


def stable_tiles(before,after):
 same_fields(before,after,('query','revision','active','blocked','window'),'tile query/window changed during actual paint')
 need(1<=len(before['pages'])==len(after['pages'])<=2,'tile subjects changed during actual paint')
 for first,last in zip(before['pages'],after['pages']):
  same_fields(first,last,TILE_IDENTITY,'live tile identity, navigation or bounds changed during actual paint')
  same_fields(first['document'],last['document'],('url','timeOrigin','viewport'),'live tile document changed during actual paint')


def verify(read,*,expected_platform=None,expected_arch=None,owner=None):
 evidence=N['Evidence'](read);raw,facts=evidence.json(NAME)
 if owner is None:_,owner=evidence.json('mouse-635-owner-feedback.json')
 platform,arch,pid=facts.get('platform'),facts.get('arch'),facts.get('pid')
 need((platform,arch) in (('darwin','arm64'),('win32','x64'),('linux','x64')) and (expected_platform is None or expected_platform==platform) and (expected_arch is None or expected_arch==arch) and (owner.get('platform'),owner.get('arch'),owner.get('pid'))==(platform,arch,pid),'search report belongs to another installed native process')
 need(facts.get('schema')==3 and facts.get('contract')==CONTRACT and facts.get('version')=='6.0.35' and positive(pid),'selected-engine evidence version differs')
 N['flags'](facts,('ok','packaged','profileIsolated','contractVerified'),'native selected-engine contract did not pass')
 need(facts.get('fixture') is False and facts.get('physicalUserDeviceVerified') is False and facts.get('source')=='installed selected-engine WebContents navigation and actual organic DOM' and facts.get('ipcChannel')=='mouse:tile-search' and facts.get('inputMode')=='native engine selection and real search UI','live provider evidence was replaced with a fixture or overstated')
 need(not facts.get('error') and facts.get('cleanupErrors')==[] and finite(facts.get('elapsedMs')) and 0<facts['elapsedMs']<=240000,'native search failed or did not restore within its owner budget')
 need(owner.get('publicSearch')=={**facts,'reportFile':NAME,'reportSha256':sha(raw)},'search raw/owner summary byte binding differs')
 log=read('mouse-635-owner-feedback.log');need(isinstance(log,bytes) and 0<len(log)<=16*1024**2 and MARKER in log.decode().splitlines(),'actual search contract marker missing')
 preference=facts.get('preference',{});selected=preference.get('selected',{});engine=selected.get('engine')
 need(engine in ENGINES and selected.get('name')==ENGINES[engine]['name'] and selected.get('private') is False and preference.get('before',{}).get('engine') in ENGINES and preference['before']['engine']!=engine,'native choice did not change the actual shared preference')
 need(selected.get('engines')==[{'id':key,'name':value['name']} for key,value in ENGINES.items()],'browser engine registry differs')
 for state in (facts.get('production',{}).get('state',{}),facts.get('production',{}).get('selected',{})):
  need(state.get('configured') is True and state.get('engine')==engine and state.get('providers')==[engine] and state.get('endpoint')==ENGINES[engine]['base'] and state.get('transport')=={'kind':'native-serp','session':'browser','private':False},'production query uses another provider or API transport')
 need(facts.get('preferenceRestored')=={'engine':preference['before']['engine'],'private':False,'exact':True},'common search preference was not restored')
 input_rows=facts.get('inputs');need(isinstance(input_rows,list) and 4<=len(input_rows)<=30,'native engine/search input ledger missing')
 for row in input_rows:
  N['input_event'](row,platform,row.get('selector'));need(row in owner.get('nativeInputs',[]),'search input missing from actual process ledger')
 opener,choice=preference.get('opener'),preference.get('input')
 need(opener in input_rows and opener.get('selector')=='.mouse-search-engine' and choice in input_rows and choice.get('selector')=='#choice-dialog button[data-value="'+engine+'"]' and choice['at']>=opener['at'],'engine was assigned programmatically instead of chosen through both actual chooser clicks')
 need(preference.get('closed')=={'open':False,'modal':False,'gateBlocked':False},'engine chooser did not release its actual modal barrier')
 chosen_ui=preference.get('ui',{});need(chosen_ui.get('engine')==engine and chosen_ui.get('engineReady')=='true' and chosen_ui.get('engineDisabled') is False,'canonical selected engine was not visible in the real UI')
 sources=facts.get('sources');need(isinstance(sources,list) and 2<=len(sources)<=12,'actual DOM source ledger missing or unbounded')
 receipts={};inputs={NAME:sha(raw)};used=set()
 for sequence,row in enumerate(sources,1):
  need(row.get('sequence')==sequence and row.get('filename')=='mouse-635-serp-'+str(sequence).zfill(3)+'.json','raw SERP filename/sequence differs')
  data,value=evidence.json(row['filename'],16*1024**2);need(row.get('bytes')==len(data) and row.get('sha256')==sha(data),'raw SERP receipt bytes/hash differ')
  for key in ('requestId','engine','query','page','outcome'):need(row.get(key)==value.get(key),'raw SERP metadata differs: '+key)
  request=value.get('requestId');need(isinstance(request,str) and re.fullmatch(r'[A-Za-z0-9_:.\-]{1,128}',request) and request not in receipts,'duplicate/unrelated native request receipt')
  need(value.get('engine')==engine and value.get('query') in [case[1] for case in CASES],'query or selected engine changed silently')
  receipts[request]=value;inputs[row['filename']]=sha(data)
 cases=facts.get('cases');need(isinstance(cases,list) and len(cases)==2,'exact owner and ordinary control cases are required')
 counts=[]
 for index,(entry,(name,query,topic)) in enumerate(zip(cases,CASES)):
  need((entry.get('name'),entry.get('query'),entry.get('expectedTopic'),entry.get('engine'))==(name,query,topic,engine) and entry.get('ok') is True and not entry.get('error'),'native case identity differs')
  need(finite(entry.get('startedAt')) and finite(entry.get('finishedAt')) and entry['startedAt']<entry['finishedAt'] and finite(entry.get('elapsedMs')) and abs(entry['elapsedMs']-entry['finishedAt']+entry['startedAt'])<=1,'actual case timing missing')
  typing=entry.get('typing',{});need(typing.get('method')=='WebContents.insertText' and typing.get('text')==query and any(row.get('type')=='input' and row.get('trusted') is True and row.get('matches') is True for row in typing.get('events',[])) and entry.get('input') in input_rows,'exact query did not reach the actual renderer input')
  pages=entry.get('pages');need(isinstance(pages,list) and len(pages)==1,'primary live native page missing')
  primary=pages[0];request=primary.get('requestId');receipt=receipts.get(request);need(receipt is not None,'primary query has no actual DOM receipt');used.add(request)
  need(primary.get('page')==1 and primary.get('args',{}).get('query')==query and primary['args'].get('page')==1 and primary['args'].get('filter')=='all' and primary['args'].get('requestId')==request and 'engine' not in primary['args'],'renderer chose another provider or query')
  need(finite(primary.get('startedAt')) and finite(primary.get('completedAt')) and entry['startedAt']<=primary['startedAt']<=primary['completedAt']<=entry['finishedAt'],'IPC timing outside the actual case')
  proof=reply_proof(primary.get('result',{}),receipt,query,engine,request,topic)
  need(primary.get('proof')==proof and entry.get('ownerTopicCovered') is bool(proof['topicMatches']) and entry.get('outcome')==proof['outcome'],'saved proof differs from actual native source')
  counts.append(proof['resultCount']);ui=entry.get('ui',{});results=primary['result'].get('results',[])
  need(ui.get('open') is True and ui.get('query')==query and ui.get('engine')==engine and ui.get('engineReady')=='true' and ui.get('busy')=='false','actual UI differs from the chosen query/engine')
  cards=ui.get('cards');host=entry.get('hostResults');need(isinstance(cards,list) and isinstance(host,list),'actual tile DOM/host registry missing')
  need([row.get('id') for row in cards]==[row.get('id') for row in results]==[row.get('id') for row in host],'tile DOM or host changed original result order')
  for card,owned,result in zip(cards,host,results):
   need(card.get('title')==result.get('title') and card.get('source')==re.sub(r'^www\.','',urlsplit(result['url']).hostname) and owned=={key:result[key] for key in ('id','url','title','source','content')},'rendered title/domain or actual host URL differs from DOM source')
   N['rect'](card.get('bounds'));need(card['bounds']['width']>0 and card['bounds']['height']>0,'actual card is not visible')
  if primary['result'].get('ok') is False:need(ui.get('errorVisible') is True and isinstance(ui.get('errorText'),str) and ui['errorText'] and not cards,'provider refusal was hidden behind fabricated results')
  extras=entry.get('additionalQueries');need(isinstance(extras,list) and len(extras)<=4 and finite(entry.get('cleanupStartedAt')) and primary['completedAt']<=entry['cleanupStartedAt']<=entry['finishedAt'],'ordinary pagination/cleanup boundary missing')
  previous=[row['url'] for row in results]
  for extra in extras:
   need(extra.get('args',{}).get('query')==query and type(extra.get('page')) is int and extra['page']>1 and extra.get('requestId')==extra['args'].get('requestId'),'unrelated additional request')
   if extra.get('cancelledByCleanup') is True:
    need(extra.get('result',{}).get('ok') is False and extra['result'].get('error',{}).get('code')=='SEARCH_CANCELLED' and extra.get('completedAt',0)>=entry['cleanupStartedAt'],'early provider failure relabelled as cleanup cancellation')
    if extra['requestId'] in receipts:used.add(extra['requestId']);validate_receipt(receipts[extra['requestId']],engine,query,extra['requestId'],extra['page'])
   else:
    need(extra['requestId'] in receipts,'additional actual provider receipt missing');used.add(extra['requestId'])
    actual=reply_proof(extra.get('result',{}),receipts[extra['requestId']],query,engine,extra['requestId'],topic,extra['page'],previous)
    need(extra.get('proof')==actual,'additional page proof differs');previous.extend(row['url'] for row in extra['result'].get('results',[]))
 need(used==set(receipts),'unclaimed or unrelated native source receipt')
 captures=facts.get('nativeCaptures');need(isinstance(captures,list) and 3<=len(captures)<=41 and facts.get('canonicalCaptures')==CAPTURES and captures[0].get('filename')==CAPTURES[0] and len({row.get('filename') for row in captures})==len(captures),'real engine chooser, source and tile OS frames missing')
 for frame in captures:
  need(frame in owner.get('captures',[]),'actual search frame missing from owner ledger');evidence.screen(frame);inputs[frame['filename']]=frame['sha256'];inputs[frame['displayFilename']]=frame['displaySha256']
 menu=preference.get('menu',{});before_menu,after_menu=menu.get('before',{}),menu.get('after',{})
 need(menu.get('capture')==CAPTURES[0] and menu.get('gateBlockedBefore') is True and menu.get('gateBlockedAfter') is True and before_menu==after_menu,'actual chooser frame or modal barrier differs')
 need(before_menu.get('open') is True and before_menu.get('modal') is True,'engine chooser was not an actual open modal')
 viewport=before_menu.get('viewport',{});content=captures[0]['contentBounds']
 need(viewport=={key:content[key] for key in ('width','height')},'engine chooser viewport differs from the actual OS frame')
 options=before_menu.get('options');need(isinstance(options,list) and len(options)==len(ENGINES),'actual engine choices are missing')
 for item in [before_menu,*options]:
  bounds=N['rect'](item.get('bounds'));need(bounds['x']>=0 and bounds['y']>=0 and bounds['width']>0 and bounds['height']>0 and bounds['x']+bounds['width']<=viewport['width']+1 and bounds['y']+bounds['height']<=viewport['height']+1,'actual chooser option was outside the visible window')
 for item,(key,value) in zip(options,ENGINES.items()):
  need(item.get('value')==key and item.get('text')==value['name'] and item.get('role')=='option' and item.get('selected')==str(key==preference['before']['engine']).lower() and item.get('disabled') is False and item.get('visible') is True and item.get('hit') is True,'actual chooser labels, current selection or hit target differs')
 chosen_bounds=next(item['bounds'] for item in options if item['value']==engine);point=choice['point']
 need(chosen_bounds['x']-1<=point['x']-content['x']<=chosen_bounds['x']+chosen_bounds['width']+1 and chosen_bounds['y']-1<=point['y']-content['y']<=chosen_bounds['y']+chosen_bounds['height']+1,'actual engine click did not hit the captured chosen option')
 # Honest unavailability may pass the source contract so other UI checks run.
 # It is never enough to publish: both real topical cases and source frame bind.
 need(facts.get('liveTopicalCapabilityVerified') is True and facts.get('ownerQueryCovered') is True and facts.get('verifiedEngines')==[engine] and facts.get('blockers')==[] and all(entry['ownerTopicCovered'] for entry in cases) and LIVE_MARKER in log.decode().splitlines() and UNVERIFIED_MARKER not in log.decode().splitlines(),'live selected-engine topical capability is unverified; publication remains blocked')
 owner_case=cases[0];frame=owner_case.get('sourceFrame',{});request=owner_case['pages'][0]['requestId'];receipt=receipts[request]
 need(frame.get('available') is True and frame.get('requestId')==request and frame.get('sourceFile')==next(row['filename'] for row in sources if row['requestId']==request),'OS source frame is not the queried native document')
 source_captures=paint_evidence(evidence,frame,'source',lambda state:source_state(state,receipt,engine),stable_source,inputs)
 need(frame.get('restored')=={'attached':False,'visible':False,'query':CASES[0][1],'active':True,'surfaceHoldRestored':True},'native source proof did not restore ordinary tile presentation')
 restored_ui=owner_case.get('uiAfterSource',{});need(restored_ui.get('query')==CASES[0][1] and [(row.get('id'),row.get('title'),row.get('source')) for row in restored_ui.get('cards',[])]==[(row['id'],row['title'],row['source']) for row in owner_case['ui']['cards']],'restored tile feed changed its original organic order')
 tile=owner_case.get('tileFrame');need(isinstance(tile,dict) and isinstance(tile.get('selectedIds'),list) and len(tile['selectedIds'])==len(set(tile['selectedIds']))==min(2,len(owner_case['pages'][0]['result']['results'])),'actual live sites paint receipt missing')
 ready=tile.get('readiness');interval(ready,15000,'live site readiness');tile_state(ready.get('lastState'),owner_case,tile['selectedIds'])
 tile_captures=paint_evidence(evidence,tile,'tiles',lambda state:tile_state(state,owner_case,tile['selectedIds']),stable_tiles,inputs);stable_tiles(ready['lastState'],tile['before'])
 need(owner_case['pages'][0]['completedAt']<=frame['paint']['startedAt']<=frame['paint']['finishedAt']<=ready['startedAt']<=ready['finishedAt']<=tile['paint']['startedAt']<=tile['paint']['finishedAt']<=owner_case['cleanupStartedAt'],'source/tile readback occurred outside the actual live query lifetime')
 need(captures==[captures[0],*source_captures,*tile_captures],'actual OS attempt ledger was reordered, omitted or substituted')
 return {'ok':True,'version':'6.0.35','platform':platform,'arch':arch,'pid':pid,'reportSha256':sha(raw),'contract':CONTRACT,'ownerTopicCovered':True,'liveTopicalCapabilityVerified':True,'verifiedEngines':[engine],'resultCounts':counts,'originalResultOrderPreserved':True,'sourcePaintVerified':True,'liveTilePaintVerified':True,'liveTileIds':tile['selectedIds'],'nativeCaptures':[row['filename'] for row in captures],'canonicalCaptures':list(CAPTURES),'inputs':inputs,'physicalUserDeviceVerified':False}
