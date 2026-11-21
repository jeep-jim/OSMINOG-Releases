#!/usr/bin/env python3
"""Small independent primitives for current634 raw native evidence."""
import hashlib
import json
import math
from pathlib import Path
import re
import runpy

T = runpy.run_path(str(Path(__file__).with_name('mouse634-task-evidence.py')))
VERSION='6.0.34'
LINE={'light':[199,207,223],'dark':[67,83,107]}
PANEL={'light':[255,255,255],'dark':[25,33,46]}
IDENTITY=('id','index','desk','webContentsId','url','navigationEpoch','identity','timeOrigin','field','scrollX','scrollY','cookie')


def need(value,message):
 if not value: raise ValueError('Mouse634 native evidence: '+message)


def finite(value): return type(value) in (int,float) and math.isfinite(value)
def positive(value): return type(value) is int and value>0
def sha(raw): return hashlib.sha256(raw).hexdigest()
def rect(value): return T['rectangle'](value,'actual native/DOM')
def right(value): return value['x']+value['width']
def bottom(value): return value['y']+value['height']
def jsround(value): return math.floor(value+.5)
def endpoints(value): return {'x':jsround(value['x']),'y':jsround(value['y']),'width':jsround(right(value))-jsround(value['x']),'height':jsround(bottom(value))-jsround(value['y'])}
def near(actual,expected,what,tolerance=1/64): need(finite(actual) and abs(actual-expected)<=tolerance,what)
def flags(value,names,label): need(isinstance(value,dict) and all(value.get(name) is True for name in names),label)
def source(platform): return {'darwin':'CGEvent','win32':'User32','linux':'XTest'}[platform]
def color(index): return [40+(index*47)%160,55+(index*71)%150,65+(index*29)%140]


def identity(before,after,origin=None):
 need(isinstance(before,dict) and isinstance(after,dict) and all(key in before and before[key]==after.get(key) for key in IDENTITY),'live page identity, state or scroll changed')
 need(positive(before.get('webContentsId')) and finite(before.get('timeOrigin')) and before['timeOrigin']>0 and isinstance(before.get('id'),str) and before['id'],'native page identity absent')
 need(type(before.get('index')) is int and before['index']>=0 and before.get('field')=='preserved-'+str(before['index'])+'-данные' and 'mouse631_'+str(before['index'])+'='+before['identity'] in before['cookie'],'owned fixture state missing')
 need(type(before.get('ticks')) is int and type(after.get('ticks')) is int and after['ticks']>=before['ticks'],'page clock restarted')
 if origin is not None: need(before['url']==origin+'/page/'+str(before['index'])+'/','page belongs to another origin')
 return after


def native(row,owner):
 need(row.get('tabId')==owner['id'] and row.get('webContentsId')==owner['webContentsId'] and row.get('index')==owner['index'] and row.get('desk')==owner['desk'],'native view belongs to another page')
 flags(row,('visible','parentVisible','cachedVisible','attached'),'native page is hidden or detached')
 rect(row.get('bounds')); need(row.get('actualBounds')==row['bounds'],'recorded bounds do not match actual native bounds')
 child=rect(row.get('viewBounds'));parent=row.get('parentBounds')
 if parent is not None: rect(parent)
 need({'x':child['x']+(parent['x'] if parent else 0),'y':child['y']+(parent['y'] if parent else 0),'width':child['width'],'height':child['height']}==row['bounds'],'native parent/child hierarchy differs')
 return row


def input_event(value,platform,selector,owner=None):
 need(isinstance(value,dict) and value.get('selector')==selector and value.get('source')==source(platform),'native input source or target differs')
 point=value.get('point',{});need(all(finite(point.get(key)) for key in ('x','y')),'native input point absent')
 events=value.get('events',[]);need(isinstance(events,list) and 0<len(events)<=100,'trusted native input witness absent')
 if owner is None:
  need(value.get('navigates') is False and finite(value.get('at')) and any(e.get('type')=='click' and e.get('trusted') is True and e.get('matches') is True for e in events),'native shell click was not received by the target')
 else:
  need(value.get('tabId')==owner['id'] and value.get('webContentsId')==owner['webContentsId'] and any(e.get('id')==selector.removeprefix('#') and (e.get('trusted') is True or e.get('isTrusted') is True) for e in events),'native guest click was not received by the owning page')
 return value


class Evidence:
 def __init__(self,read): self.read=read;self.images={};self.receipts={}
 def json(self,name,limit=8*1024**2):
  raw=self.read(name);need(isinstance(raw,bytes) and 0<len(raw)<=limit,'missing/oversized report: '+name)
  value=json.loads(raw);need(isinstance(value,dict),'report is not an object');return raw,value
 def png(self,row):
  name=row.get('filename');need(isinstance(name,str) and re.fullmatch(r'mouse-634-[a-z0-9-]+\.png',name),'unsafe634 capture name')
  raw=self.read(name);need(isinstance(raw,bytes) and 0<len(raw)<=16*1024**2 and len(raw)==row.get('bytes') and sha(raw)==row.get('sha256'),'raw634 capture size/hash differs: '+name)
  key=(name,sha(raw));image=self.images.get(key)
  if image is None: image=T['decode_png'](raw,name);self.images[key]=image
  need(row.get('pixelSize')=={'width':image['width'],'height':image['height']},'PNG dimensions differ: '+name)
  return image
 def screen(self,row):
  image=self.png(row);name=row['filename']
  need(row.get('source')=='globalCapture.acquire(display)' and isinstance(row.get('backend'),str) and row['backend'],'capture is not a native display frame')
  need(row.get('displayFilename')==name[:-4]+'-display.png','full native display missing')
  raw=self.read(row['displayFilename']);need(isinstance(raw,bytes) and 0<len(raw)<=16*1024**2 and sha(raw)==row.get('displaySha256'),'display raw hash differs')
  key=(row['displayFilename'],sha(raw));full=self.images.get(key)
  if full is None: full=T['decode_png'](raw,row['displayFilename']);self.images[key]=full
  need(row.get('screenPixelSize')=={'width':full['width'],'height':full['height']},'display dimensions differ')
  bounds=rect(row.get('display',{}).get('bounds'));content=rect(row.get('contentBounds'))
  sx,sy=full['width']/bounds['width'],full['height']/bounds['height'];need(0<sx<=8 and 0<sy<=8,'invalid native display scale')
  left,top=(content['x']-bounds['x'])*sx,(content['y']-bounds['y'])*sy
  crop={'x':math.floor(left),'y':math.floor(top),'width':math.ceil(left+content['width']*sx)-math.floor(left),'height':math.ceil(top+content['height']*sy)-math.floor(top)}
  mapping={'scaleX':sx,'scaleY':sy,'originX':left-crop['x'],'originY':top-crop['y']}
  need(row.get('cropPixels')==crop and (image['width'],image['height'])==(crop['width'],crop['height']),'native window crop differs')
  need(all(finite(row.get('mapping',{}).get(k)) and abs(row['mapping'][k]-v)<=1e-8 for k,v in mapping.items()),'native DPI mapping differs')
  need(crop['x']>=0 and crop['y']>=0 and crop['x']+crop['width']<=full['width'] and crop['y']+crop['height']<=full['height'],'window lies outside native display')
  need(image['channels']==full['channels'],'raw crop channel representation differs')
  channels=image['channels'];stride=image['width']*channels
  for y in range(crop['height']):
   offset=((y+crop['y'])*full['width']+crop['x'])*channels
   need(image['pixels'][y*stride:(y+1)*stride]==full['pixels'][offset:offset+stride],'window pixels differ from the full native display')
  self.receipts[name]={'filename':name,'sha256':row['sha256'],'displaySha256':row['displaySha256']}
  return image
 def pixel(self,image,mapping,point):
  need(all(finite(mapping.get(k)) for k in ('scaleX','scaleY','originX','originY')) and mapping['scaleX']>0 and mapping['scaleY']>0,'pixel mapping invalid')
  need(all(finite(point.get(k)) for k in ('x','y')),'pixel point invalid')
  x,y=math.floor(mapping['originX']+point['x']*mapping['scaleX']),math.floor(mapping['originY']+point['y']*mapping['scaleY'])
  need(0<=x<image['width'] and 0<=y<image['height'],'pixel probe outside raw frame')
  at=(y*image['width']+x)*image['channels'];rgba=list(image['pixels'][at:at+image['channels']])
  if image['channels']==3: rgba.append(255)
  return x,y,rgba
