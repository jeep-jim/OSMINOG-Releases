#!/usr/bin/env python3
import base64
import copy
import hashlib
import json
from pathlib import Path
import runpy
import struct
import unittest
import zlib

C=runpy.run_path(str(Path(__file__).with_name('mouse635-library-evidence.py')))
sha=lambda raw:hashlib.sha256(raw).hexdigest()
encode=lambda value:(json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n').encode()


def png(width,height,rgb):
 def chunk(kind,raw): return struct.pack('>I',len(raw))+kind+raw+struct.pack('>I',zlib.crc32(kind+raw)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+bytes(rgb)*width)*height))+chunk(b'IEND',b'')


def fixture():
 before=png(160,96,[10,50,90]);after=png(160,96,[90,30,150]);uri=lambda raw:'data:image/png;base64,'+base64.b64encode(raw).decode()
 downloads=['download-'+str(i) for i in range(14)];copies=['copy-'+str(i) for i in range(15)];images={};captures=[];phases=[]
 def start(identifier,order): return{'id':identifier,'kind':'downloads','view':'list','theme':'dark','scrollTop':400,'rowTop':100,'selected':True,'focused':True,'source':uri(before),'imageSize':{'width':160,'height':96},'order':list(order)}
 def sample(old): return{**copy.deepcopy(old),'sameRow':True,'sameImage':True,'sameCheckbox':True,'sameFocus':True,'focusedCheckbox':True,'sameSource':True,'thumbnail':True,'removed':0,'sourceWrites':0,'events':[]}
 for theme in ('light','dark'):
  for kind in ('downloads','captures'):
   for view in ('list','grid'):
    old=start(downloads[5] if kind=='downloads' else copies[8],downloads if kind=='downloads' else copies);old.update(theme=theme,kind=kind,view=view);current=sample(old)
    if kind=='downloads': current['activeProgress']=15
    inserted=sample(old)
    if kind=='captures': inserted['order'].insert(0,'extra-'+theme+'-'+view);inserted['scrollTop']+=40
    name='mouse-635-library-'+kind+'-'+view+'-'+theme+'.png';window=png(2,2,[20,60,100]);display=png(4,4,[20,60,100]);images[name]=window;images[name[:-4]+'-display.png']=display
    capture={'filename':name,'displayFilename':name[:-4]+'-display.png','source':'globalCapture.acquire(display)','backend':'unit-native-frame-fixture','bytes':len(window),'sha256':sha(window),'displaySha256':sha(display),'pixelSize':{'width':2,'height':2},'screenPixelSize':{'width':4,'height':4},'display':{'bounds':{'x':0,'y':0,'width':4,'height':4}},'contentBounds':{'x':1,'y':1,'width':2,'height':2},'cropPixels':{'x':1,'y':1,'width':2,'height':2},'mapping':{'scaleX':1,'scaleY':1,'originX':0,'originY':0}}
    captures.append(capture);phases.append({'theme':theme,'kind':kind,'view':view,'before':old,'after':current,'inserted':inserted,'removed':sample(old),'updates':6,'backgroundArchivePreviewCalls':0,'archivePreviewCalls':0,'capture':capture})
 original=start(downloads[5],downloads);changed=sample(original);changed.update(source=uri(after),sameSource=False,sourceWrites=1,events=[{'type':'src','at':10}]);before_delete={**copy.deepcopy(original),'source':uri(after)};deleted=sample(before_delete);deleted.update(source='data:image/svg+xml,%3Csvg/%3E',sameSource=False,thumbnail=False,sourceWrites=1,events=[{'type':'src','at':20}])
 files={'before':original,'changed':changed,'beforeDelete':before_delete,'deleted':deleted,'replacementSha256':sha(after),'missingOpenError':'Файл перемещён или удалён','missingOnDisk':True,'entryRetained':True}
 for field,suffix,raw in [('originalFile','before',before),('replacementFile','after',after)]:
  name='mouse-635-library-file-'+suffix+'.png';images[name]=raw;files[field]={'filename':name,'source':'fs.readFile of owned installed-app fixture','bytes':len(raw),'sha256':sha(raw),'pixelSize':{'width':160,'height':96}}
 timestamp=1795248000000
 facts={'schema':1,'version':'6.0.35','platform':'linux','arch':'x64','pid':80,'ok':True,'completed':True,'restored':True,'packaged':True,'profileIsolated':True,'fixtureOnly':True,'realTransfer':False,'scenario':'installed-library-stability','startedAt':'2026-11-21T08:00:00.000Z','finishedAt':'2026-11-21T08:00:20.000Z','autoCollection':{'before':False,'after':False,'clipboardReadsBefore':0,'clipboardReadsAfter':0},'owned':{'downloadIds':downloads,'captureIds':copies,'activeId':'active','fileHashes':[{'id':identifier,'filename':'image-'+str(i)+'.png','sha256':sha(before)} for i,identifier in enumerate(downloads)]},'phases':phases,'captures':captures,'files':files,'previews':{'firstPreview':{'title':'Mouse635 image 8','src':uri(before)},'latest':{'title':'Mouse635 image 7','src':uri(after)},'staleClosed':{'open':False,'kind':'downloads'},'realArchiveReads':True},'previewRequests':[{'sequence':i+1,'id':copies[8],'startedAt':timestamp+10+i*100,'finishedAt':timestamp+90+i*100,'controlledDelay':True,'type':'image'} for i in range(3)],'notifications':[]}
 requests=[];facts['placeholderGeometryChecks']=[]
 def held(identifier):
  sequence=len(requests)+1;requests.append({'sequence':sequence,'id':identifier,'startedAt':timestamp+sequence*100,'finishedAt':timestamp+sequence*100+80,'controlledDelay':True,'type':'image'});return sequence
 for phase in phases:
  if phase['kind']!='captures': continue
  height=30 if phase['view']=='list' else 112;width=30 if phase['view']=='list' else 150
  rows=[{'id':identifier,'row':{'x':0,'y':i*200,'width':190,'height':180},'image':{'x':5,'y':i*200+30,'width':width,'height':height},'checkbox':{'x':170,'y':i*200+8,'width':16,'height':16},'thumbnail':False,'decoded':False} for i,identifier in enumerate(copies[:14])]
  old={'kind':'captures','view':phase['view'],'scrollTop':400,'rows':rows};current=copy.deepcopy(old);delayed=[copies[7],copies[8]]
  for row in current['rows']:
   if row['id'] in delayed: row.update(thumbnail=True,decoded=True)
  receipt={'controlledDelay':True,'before':old,'after':current,'delayedIds':delayed,'requestSequences':[held(identifier) for identifier in delayed]};phase['placeholderGeometry']=receipt;facts['placeholderGeometryChecks'].append({'theme':phase['theme'],**receipt})
 for _ in range(3): held(copies[8])
 facts['previewRequests']=requests
 for reason,count in [('other-kind download progress',24),('same-kind download progress',24),('actual owned image bytes replaced',1),('actual owned download file removed',1),('download update while explicit capture preview pending',1)]: facts['notifications'].extend({'reason':reason,'at':timestamp+100+i} for i in range(count))
 native=[]
 for identifier,suffix,count in [(downloads[5],'check',5),(copies[8],'check',4),(copies[8],'name',3),(copies[7],'name',1)]:
  for i in range(count): native.append({'selector':'.library-row[data-id="'+identifier+'"] .library-'+suffix,'source':'XTest','point':{'x':4,'y':5},'at':timestamp+i,'navigates':False,'events':[{'type':'click','trusted':True,'matches':True}]})
 owner={'pid':80,'platform':'linux','arch':'x64','captures':captures,'nativeInputs':native};images['mouse-635-owner-feedback.log']=(C['MARKER']+'\n').encode()
 return{'facts':facts,'owner':owner,'raw':images}


def packed(fixture):
 raw=dict(fixture['raw']);facts=fixture['facts'];raw[C['NAME']]=encode(facts);owner=copy.deepcopy(fixture['owner']);owner['library']={**facts,'reportFile':C['NAME'],'reportSha256':sha(raw[C['NAME']])};raw['mouse-635-owner-feedback.json']=encode(owner);return raw,owner


class LibraryEvidence(unittest.TestCase):
 def verify(self,value):
  raw,owner=packed(value);return C['verify'](raw.__getitem__,expected_platform='linux',expected_arch='x64',owner=owner)
 def test_complete_byte_bound_library_fixture(self):
  result=self.verify(fixture());self.assertTrue(result['ok']);self.assertEqual(result['phases'],8);self.assertEqual(result['placeholderGeometryScenes'],4);self.assertEqual(len(result['nativeCaptures']),8)
 def test_rejects_recreated_nodes_focus_selection_and_thumbnail(self):
  for field,value in [('sameRow',False),('sameImage',False),('sameCheckbox',False),('sameFocus',False),('focusedCheckbox',False),('selected',False),('sameSource',False),('thumbnail',False),('removed',1),('sourceWrites',1),('scrollTop',404),('rowTop',104),('order',['foreign']),('kind','captures'),('view','grid'),('theme','dark')]:
   with self.subTest(field=field):
    data=fixture();data['facts']['phases'][0]['after'][field]=value
    with self.assertRaises(ValueError): self.verify(data)
 def test_all_themes_views_sections_and_real_progress_are_required(self):
  mutations=[lambda f:f['phases'].pop(),lambda f:f['phases'].__setitem__(1,copy.deepcopy(f['phases'][0])),lambda f:f['phases'][0]['after'].__setitem__('activeProgress',14),lambda f:f['phases'][2].__setitem__('backgroundArchivePreviewCalls',1),lambda f:f['phases'][2]['inserted'].__setitem__('order',f['phases'][2]['before']['order'])]
  for index,mutate in enumerate(mutations):
   with self.subTest(index=index):
    data=fixture();mutate(data['facts'])
    with self.assertRaises(ValueError): self.verify(data)
 def test_real_preview_completion_cannot_move_controls_or_use_file_icons(self):
  for box in ('row','image','checkbox'):
   for axis in ('x','y','width','height'):
    with self.subTest(box=box,axis=axis):
     data=fixture();receipt=data['facts']['phases'][2]['placeholderGeometry'];receipt['after']['rows'][7][box][axis]+=2
     with self.assertRaisesRegex(ValueError,'moved a row, image or checkbox'): self.verify(data)
  changes=[lambda r:r['after'].__setitem__('scrollTop',402),lambda r:r['before']['rows'][7].__setitem__('thumbnail',True),lambda r:r['after']['rows'][7].__setitem__('decoded',False),lambda r:r['after']['rows'][7].__setitem__('thumbnail',False),lambda r:r['before']['rows'][0]['image'].__setitem__('width',0),lambda r:r['before']['rows'][0]['row'].__setitem__('x',float('nan'))]
  for change in changes:
   data=fixture();change(data['facts']['phases'][2]['placeholderGeometry'])
   with self.assertRaises(ValueError): self.verify(data)
  data=fixture();receipt=data['facts']['phases'][3]['placeholderGeometry']
  for sample in ('before','after'):
   for row in receipt[sample]['rows']: row['image']['height']=36
  with self.assertRaisesRegex(ValueError,'reserve its actual'): self.verify(data)
 def test_placeholder_proof_requires_every_scene_and_the_actual_held_reads(self):
  mutations=[lambda f:f['phases'][2].pop('placeholderGeometry'),lambda f:f['placeholderGeometryChecks'].pop(),lambda f:f['phases'][2]['placeholderGeometry'].__setitem__('delayedIds',[]),lambda f:f['phases'][2]['placeholderGeometry']['requestSequences'].__setitem__(0,1000),lambda f:f['phases'][2]['placeholderGeometry']['after']['rows'].reverse(),lambda f:f['previewRequests'][0].__setitem__('controlledDelay',False),lambda f:f['previewRequests'][0].__setitem__('id','copy-6'),lambda f:f['previewRequests'][-1].__setitem__('id','copy-7')]
  for index,mutate in enumerate(mutations):
   with self.subTest(index=index):
    data=fixture();mutate(data['facts'])
    with self.assertRaises(ValueError): self.verify(data)
  data=fixture();earlier=data['facts']['phases'][2]['placeholderGeometry'];later=data['facts']['phases'][3]['placeholderGeometry'];later['requestSequences'][:]=earlier['requestSequences']
  with self.assertRaisesRegex(ValueError,'reused'): self.verify(data)
 def test_real_changed_and_deleted_files_cannot_be_replaced_by_boolean_claims(self):
  for key,value in [('replacementSha256','f'*64),('missingOnDisk',False),('entryRetained',False),('missingOpenError','Opened successfully')]:
   with self.subTest(field=key):
    data=fixture();data['facts']['files'][key]=value
    with self.assertRaises(ValueError): self.verify(data)
  data=fixture();data['facts']['files']['deleted']['thumbnail']=True
  with self.assertRaises(ValueError): self.verify(data)
  data=fixture();data['raw']['mouse-635-library-file-after.png']=data['raw']['mouse-635-library-file-before.png']
  with self.assertRaises(ValueError): self.verify(data)
 def test_wrong_process_native_input_and_cleanup_fail_closed(self):
  for mutate in [lambda d:d['owner'].__setitem__('pid',81),lambda d:d['owner']['nativeInputs'][0]['events'][0].__setitem__('trusted',False),lambda d:d['facts'].__setitem__('restored',False),lambda d:d['facts']['autoCollection'].__setitem__('clipboardReadsAfter',1),lambda d:d['facts']['previews']['latest'].__setitem__('title','stale'),lambda d:d['facts']['previewRequests'].pop(),lambda d:d['facts']['notifications'].pop()]:
   data=fixture();mutate(data)
   with self.assertRaises(ValueError): self.verify(data)
 def test_native_png_bytes_crop_and_owner_hash_cannot_be_substituted(self):
  data=fixture();name=data['facts']['captures'][0]['filename'];data['raw'][name]=png(2,2,[1,2,3]);data['facts']['captures'][0]['sha256']=sha(data['raw'][name]);data['facts']['captures'][0]['bytes']=len(data['raw'][name])
  with self.assertRaises(ValueError): self.verify(data)
  raw,owner=packed(fixture());owner['library']['reportSha256']='f'*64
  with self.assertRaises(ValueError): C['verify'](raw.__getitem__,owner=owner)
  data=fixture();data['raw']['mouse-635-owner-feedback.log']=b'not a native library pass\n'
  with self.assertRaises(ValueError): self.verify(data)


if __name__=='__main__': unittest.main()
