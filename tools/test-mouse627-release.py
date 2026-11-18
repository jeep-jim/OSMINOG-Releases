#!/usr/bin/env python3
"""Offline publisher contract tests. All positive facts below are synthetic."""
import ast,contextlib,copy,hashlib,io,json,os,pathlib,runpy,struct,sys,tempfile,types,unittest,zipfile,zlib
from unittest.mock import Mock,patch

ROOT=pathlib.Path(__file__).resolve().parents[1]
with patch.object(sys,'argv',['mouse627-release.py','validate-template']),contextlib.redirect_stdout(io.StringIO()):
 P=runpy.run_path(str(ROOT/'tools/mouse627-release.py'))

def window():
 before={'x':40,'y':40,'width':1200,'height':800};after={**before,'x':76,'y':64}
 return{'version':'6.0.27','restored':True,'gestures':[{'label':theme+' '+region,'point':{'x':120,'y':780},'before':dict(before),'after':dict(after),'requested':{'dx':36,'dy':24}} for theme in ['light','dark'] for region in ['footer left','footer right','top grip']],'controls':[theme+' '+control for theme in ['light','dark'] for control in ['theme','Nora']]}
def documents():return{'version':'6.0.27',**dict.fromkeys(P['DOCUMENT_FACTS'],True)}
def presentation(metadata):
 return{'source':'beginFrameSubscription','sequence':3,'elapsedMs':80,'dirtyRect':{'x':0,'y':0,'width':1200,'height':900},'scaleFactor':1,'pixelSize':{'width':1200,'height':900},'metadata':metadata}
def pdf():
 samples=[{'x':100+i*12,'y':400,'sourceRGBA':[0,0,0,255],'pixelX':100+i*12,'pixelY':400,'rgba':[3,7,4,255],'dark':7} for i in range(12)]
 proof=presentation({'text':'Mouse627 исправлен','mode':'edit','viewport':{'width':1200,'height':900},'beforeStyle':{'backdropFilter':'none','webkitBackdropFilter':'none','appearance':'none','background':'rgba(0, 0, 0, 0)'},'minimum':12,'samples':samples})
 return{'version':'6.0.27',**dict.fromkeys(P['PDF_FACTS'],True),'readability':{**proof,'filename':'mouse-627-pdf-existing-text.png'}}
def performance():
 result={'version':'6.0.27','platform':'darwin','arch':'arm64','panes':8,'stateRestored':True,'livePagesPreserved':True,'measurements':{}}
 for name in ['controlled-immediate','controlled-batched','unchanged-metadata','renderer-immediate','renderer-batched']:
  memory={'rss':1000,'heapTotal':500,'heapUsed':300,'external':20,'arrayBuffers':10}
  row={'label':name,'stateBuilds':1,'stateBuildMs':1,'layoutCalls':1,'elapsedMs':120,'frames':{'count':5,'p95Ms':17,'maxMs':18},'mainMemoryBefore':dict(memory),'mainMemoryAfter':dict(memory)}
  if name=='controlled-immediate':row.update(events=64,synchronousBuilds=64,stateBuilds=64)
  elif name=='controlled-batched':row.update(events=64,synchronousBuilds=0)
  elif name=='unchanged-metadata':row.update(events=320,synchronousBuilds=0,stateBuilds=0)
  else:row.update(requestedTitleChanges=96,titleEvents=96)
  result['measurements'][name]=row
 return result
def palette():return{'version':'6.0.26','stateRestored':True,'palette':dict.fromkeys(P['PALETTE_FACTS'],True),'supersededForNora':dict(P['SUPERSEDED_NORA_METADATA'])}
def retained623():return{'version':'6.0.23','geometryVersion':'6.0.27',**dict.fromkeys(['fixedTopCurves','outlineMatchesFooter','fixedViewport','scrollableContent','footerStationary','supersededOldGeometry'],True),'themes':['light','dark'],'states':['compact','modes','preview'],'frames':[{'theme':theme,'state':state} for theme in ['light','dark'] for state in ['compact','modes','preview']],'tabLifecycle':dict.fromkeys(P['LIFECYCLE_FACTS_623'],True),'agentEntry':{**dict.fromkeys(P['AGENT_ENTRY_FACTS_623'],True),'color':'orange'}}
def frame(progress,phase,time):
 return{'time':time,'phase':phase,'progress':progress,'open':phase!='closed','hidden':phase=='closed','height':440,'targetHeight':440,'width':1000,'left':100,'baseline':800,'inert':phase!='open','opacity':1,'font':'12px','measurements':1,'geometryWrites':1,'paths':{'outline':'M0 440Q500 0 1000 440','fill':'M0 440Q500 0 1000 440Z','viewBox':'0 0 1000 440'},'matrix':{'a':1,'b':0,'c':0,'d':1,'e':0,'f':440*(1-progress)}}
def motion():
 value={'version':'6.0.27','themes':['light','dark'],**dict.fromkeys(P['MOTION_FACTS'],True),'frames':{},'geometry':{},'captures':{},'captureStates':{},'footer':{}}
 for theme in ['light','dark']:
  value['frames'][theme+'Opening']=[frame(p,phase,i*10) for i,(p,phase) in enumerate([(0,'opening'),(.2,'opening'),(.5,'opening'),(.8,'opening'),(1,'open')])]
  value['frames'][theme+'Closing']=[frame(p,phase,i*10) for i,(p,phase) in enumerate([(1,'closing'),(.8,'closing'),(.5,'closing'),(.2,'closing'),(0,'closed')])]
  value['captures'][theme]={phase:f'mouse-627-panel-{theme}-{phase}.png' for phase in ['opening','open','closing']}
  value['captureStates'][theme]={'open':{'before':frame(1,'open',20)}}
  for phase in ['opening','closing']:
   before=None if phase=='opening' else frame(1,'open',20);fill=[255,255,255] if theme=='light' else [25,33,46];line=[199,207,223] if theme=='light' else [67,83,107]
   geometry={'viewport':{'width':1200,'height':900},'width':1000,'height':440,'left':100,'baseline':800,'fill':fill,'line':line,'before':copy.deepcopy(before)}
   probes=[{'x':x,'y':580,'above':[10,20,30,255],'edge':line+[255],'inside':fill+[255],'lower':fill+[255]} for x in [300,600,900]]
   value['captureStates'][theme][phase]={'before':before,'after':None,'painted':presentation({'theme':theme,'state':phase,'geometry':geometry,'top':580,'translateY':220,'progress':.5,'probes':probes})}
  value['geometry'][theme+'Controls']=[{'name':name,'height':440,'width':1000,'paths':{key:frame(1,'open',0)['paths'][key] for key in ['outline','fill']},'geometryWrites':1,'scrollTop':10,'scrollHeight':600,'clientHeight':440,'overflow':'auto','accessible':True,'visibleHeight':25} for name in ['preview','modes','history']]
  footer={'x':0,'y':800,'width':1200,'height':28,'pixels':[{'x':x,'y':800.25,'rgb':[20,30,40]} for x in [180,360,840,1020]]}
  value['footer'][theme]={'before':copy.deepcopy(footer),'after':copy.deepcopy(footer)}
 value['frames']['interrupted']=[frame(p,phase,i*10) for i,(p,phase) in enumerate([(.2,'opening'),(.7,'opening'),(.6,'closing'),(.5,'closing'),(.6,'opening'),(1,'open')])]
 value['frames']['reduced']=[frame(1,'open',0),frame(0,'closed',20)]
 value['interruption']={'before':frame(.5,'closing',30),'after':frame(.5,'opening',31),'closingFrames':[frame(.6,'closing',20),frame(.5,'closing',30)],'open':True}
 for name in value['frames']:
  initial={key:{'width':width,'height':height} for key,width,height in [('tray',1000,440),('panel',1000,440),('content',920,440),('button',30,28)]}
  value['geometry'][name]={'initial':initial,'sizes':[{'target':key,**box} for key,box in initial.items()],'mutations':[]}
 bounds={'x':100,'y':60,'width':900,'height':600};page={'id':'retained-page','webContentsId':11,'url':'http://127.0.0.1:1/synthetic-fixture','epoch':1,'bounds':bounds,'clip':None,'timeOrigin':123,'width':900,'height':600,'scrollX':10,'scrollY':20,'resizeEvents':[],'visible':True,'surfaceBounds':bounds}
 image={'id':page['id'],'complete':True,'png':True,'naturalWidth':900,'naturalHeight':600,'bounds':bounds,'transform':'none'}
 value['background']={'before':[copy.deepcopy(page)],'after':[copy.deepcopy(page)],'nativeBoundsCalls':0,'resizeEvents':0,'snapshots':[{'theme':theme,'images':[copy.deepcopy(image)]} for theme in ['light','dark']]}
 return value
def desktop_transition():
 value={'version':'6.0.27',**dict.fromkeys(P['DESKTOP_TRANSITION_FACTS'],True),'transitions':[]}
 page={'id':'retained-page','webContentsId':11,'navigationEpoch':1,'url':'http://127.0.0.1:1/synthetic-fixture','width':900,'height':600,'scrollX':10,'scrollY':20,'marker':'synthetic-unit-marker'}
 pages=[page,{**page,'id':'second-retained-page','webContentsId':12,'marker':.12345}]
 snapshots=[{'id':pin['id'],'frame':frame,'png':True,'decoded':True,'pixelWidth':900,'pixelHeight':600,'width':900,'height':600} for pin,frame in zip(pages,['outgoing','incoming'])]
 captures=[{'prepared':bool(index),'complete':True,'ids':[pin['id']],'rows':[{'id':pin['id'],'epoch':pin['navigationEpoch'],'webContentsId':pin['webContentsId'],'pixelWidth':900,'pixelHeight':600,'width':900,'height':600,'sample':{'x':450,'y':300,'pixelX':450,'pixelY':300,'viewportWidth':900,'viewportHeight':600,'rgba':[240,240,240,255],'domTag':'BODY','background':'rgb(240, 240, 240)'}}]} for index,pin in enumerate(pages)]
 for theme in ['light','dark']:
  for direction in [-1,1]:
   row={'theme':theme,'direction':direction,'ackDelayMs':250 if not value['transitions'] else 0,'nativeLayoutCalls':4,'animationDurationMs':330,'totalDurationMs':650,'pageBefore':copy.deepcopy(pages),'pageAfter':copy.deepcopy(pages),'frames':[{'at':i*165,'outgoingX':-direction*i*600,'incomingX':direction*(1200-i*600),'width':1200} for i in range(3)],'snapshots':copy.deepcopy(snapshots),'allSnapshots':copy.deepcopy(snapshots),'captures':copy.deepcopy(captures)}
   if direction==1:row['paintedFrame']={**presentation({'bothDesktopsPainted':True,'colors':[[199,37,77],[29,125,220]],'counts':[32,32],'minimum':16,'rows':[90],'viewport':{'width':1200,'height':900,'rows':[90,90]},'pixelSize':{'width':1200,'height':900},'scaleFactor':1}),'filename':f'mouse-627-desktop-transition-{theme}.png'}
   value['transitions'].append(row)
 return value
def png_bytes(width=1200,height=900,points=None,channels=4):
 pixels=bytearray([255])*(width*height*channels)
 for (x,y),value in (points or {}).items():pixels[(y*width+x)*channels:(y*width+x+1)*channels]=bytes(value[:channels])
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 stride=width*channels;raw=b''.join(b'\0'+pixels[y*stride:(y+1)*stride] for y in range(height))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6 if channels==4 else 2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
def evidence():
 facts=dict(zip(P['JSON_FILES_627'],[window(),documents(),pdf(),performance(),motion(),desktop_transition()]));data={name:json.dumps(value).encode() for name,value in facts.items()}
 data['mouse-623-verification.json']=json.dumps(retained623()).encode()
 for name in P['PNG_FILES_627']:data[name]=png_bytes(1,1)
 for theme in ['light','dark']:
  for phase in ['opening','closing']:
   points={}
   for probe in facts['mouse-627-motion.json']['captureStates'][theme][phase]['painted']['metadata']['probes']:
    for key,dy in [('above',-2),('edge',0),('inside',2),('lower',6)]:points[(probe['x'],probe['y']+dy)]=probe[key]
   data[f'mouse-627-panel-{theme}-{phase}.png']=png_bytes(points=points)
  points={(x,90):color+[255] for start,color in [(100,[199,37,77]),(600,[29,125,220])] for x in range(start,start+32)}
  data[f'mouse-627-desktop-transition-{theme}.png']=png_bytes(points=points)
 data['mouse-627-pdf-existing-text.png']=png_bytes(points={(s['pixelX'],s['pixelY']):s['rgba'] for s in facts['mouse-627-pdf-text.json']['readability']['metadata']['samples']})
 return data

class PublisherContract(unittest.TestCase):
 def test_all_new_evidence_is_required(self):
  files=evidence();P['verify_627_evidence'](files.__getitem__)
  for name in files:
   with self.subTest(missing=name),self.assertRaises((KeyError,ValueError)):
    incomplete=dict(files);del incomplete[name];P['verify_627_evidence'](incomplete.__getitem__)
  files[P['PNG_FILES_627'][0]]=b'not a PNG'
  with self.assertRaisesRegex(ValueError,'not PNG'):P['verify_627_evidence'](files.__getitem__)

 def test_native_drag_proves_both_axes_and_unchanged_size(self):
  P['verify_627_window'](window())
  for field,value in [('x',79),('y',67),('width',1201),('height',801)]:
   with self.subTest(field=field),self.assertRaises(ValueError):
    facts=window();facts['gestures'][0]['after'][field]=value;P['verify_627_window'](facts)
  for mutate in [lambda f:f['gestures'].pop(),lambda f:f['controls'].pop(),lambda f:f['gestures'][0].update(label='dark footer left'),lambda f:f.update(restored=False),lambda f:f.update(version='6.0.26')]:
   with self.assertRaises(ValueError):facts=window();mutate(facts);P['verify_627_window'](facts)

 def test_required_facts_cannot_be_omitted_or_truthy_strings(self):
  for factory,validator,keys in [(documents,P['verify_627_documents'],P['DOCUMENT_FACTS']),(pdf,P['verify_627_pdf'],P['PDF_FACTS']),(motion,P['verify_627_motion'],P['MOTION_FACTS']),(desktop_transition,P['verify_627_desktop_transition'],P['DESKTOP_TRANSITION_FACTS'])]:
   validator(factory())
   for key in keys:
    for value in [False,'true',1,None]:
     with self.subTest(key=key,value=value),self.assertRaises(ValueError):facts=factory();facts[key]=value;validator(facts)
    with self.subTest(missing=key),self.assertRaises(ValueError):facts=factory();del facts[key];validator(facts)

 def test_pdf_readability_requires_glyphs_in_edit_mode_without_blur(self):
  validate=P['verify_627_pdf'];validate(pdf())
  for mutate in [lambda f:f.pop('readability'),lambda f:f['readability'].update(source='capturePage'),lambda f:f['readability'].update(filename='unrelated.png'),lambda f:f['readability']['metadata'].update(mode='view'),lambda f:f['readability']['metadata']['beforeStyle'].update(backdropFilter='blur(14px)'),lambda f:f['readability']['metadata']['samples'].pop(),lambda f:f['readability']['metadata']['samples'][0].update(pixelX=500),lambda f:f['readability']['metadata']['samples'][0].update(sourceRGBA=[100,100,100,255]),lambda f:f['readability']['metadata']['samples'][0].update(rgba=[190,190,190,255],dark=190),lambda f:f['readability']['metadata']['samples'][1].update(f['readability']['metadata']['samples'][0])]:
   with self.assertRaises(ValueError):facts=pdf();mutate(facts);validate(facts)

 def test_motion_presentation_requires_natural_intermediate_edges_and_both_desktops(self):
  # Opening starts from a truthful null/closed DOM sample. Only delivered
  # presentation pixels establish that the selected PNG is intermediate.
  P['verify_627_motion'](motion())
  for mutate in [lambda p:p.update(source='capturePage'),lambda p:p.update(sequence=0),lambda p:p.update(elapsedMs=float('nan')),lambda p:p['metadata'].update(top=360,translateY=0,progress=1),lambda p:p['metadata'].update(top=800,translateY=440,progress=0),lambda p:p['metadata']['probes'][0].update(x=301),lambda p:p['metadata']['probes'][0].update(inside=[0,0,0,255]),lambda p:p['metadata']['probes'][0].update(edge=[199,207,223,0])]:
   with self.assertRaises(ValueError):facts=motion();mutate(facts['captureStates']['light']['opening']['painted']);P['verify_627_motion'](facts)
  for theme in ['light','dark']:
   with self.assertRaises(ValueError):facts=motion();del facts['captureStates'][theme]['closing']['painted'];P['verify_627_motion'](facts)
  for mutate in [lambda r:r.pop('paintedFrame'),lambda r:r['paintedFrame'].update(source='capturePage'),lambda r:r['paintedFrame']['metadata'].update(counts=[32,0]),lambda r:r['paintedFrame']['metadata'].update(rows=[91]),lambda r:r['paintedFrame']['metadata'].update(colors=[[0,0,0],[29,125,220]]),lambda r:r['paintedFrame']['metadata'].update(bothDesktopsPainted=False)]:
   with self.assertRaises(ValueError):facts=desktop_transition();mutate(facts['transitions'][1]);P['verify_627_desktop_transition'](facts)

 def test_presented_png_bytes_must_match_claimed_edge_bands_and_glyphs(self):
  files=evidence();P['verify_627_evidence'](files.__getitem__);blank=png_bytes()
  moving=[f'mouse-627-panel-{theme}-{phase}.png' for theme in ['light','dark'] for phase in ['opening','closing']]+[f'mouse-627-desktop-transition-{theme}.png' for theme in ['light','dark']]+['mouse-627-pdf-existing-text.png']
  for name in moving:
   with self.subTest(blank=name),self.assertRaises(ValueError):changed=dict(files);changed[name]=blank;P['verify_627_evidence'](changed.__getitem__)
  with self.assertRaisesRegex(ValueError,'dimensions'):changed=dict(files);changed[moving[0]]=png_bytes(1,1);P['verify_627_evidence'](changed.__getitem__)
  # A different valid bitmap cannot be accepted on the strength of JSON alone.
  changed=dict(files);changed[moving[0]]=files['mouse-627-panel-dark-opening.png']
  with self.assertRaisesRegex(ValueError,'pixel evidence'):P['verify_627_evidence'](changed.__getitem__)
  for channels in [3,4]:
   image=P['decode_png'](png_bytes(2,2,{(1,1):[12,34,56,255]},channels),'synthetic test');self.assertEqual(P['png_pixel'](image,1,1),[12,34,56,255])
  corrupt=bytearray(files[moving[0]]);corrupt[-1]^=1
  for blob in [bytes(corrupt),files[moving[0]][:-1],files[moving[0]]+b'trailing']:
   with self.assertRaises(ValueError):P['decode_png'](blob,'corrupt synthetic fixture')

 def test_performance_requires_actual_pages_counts_and_valid_measurements(self):
  P['verify_627_performance'](performance())
  for key,value in [('stateRestored',False),('livePagesPreserved',False),('panes',7),('platform','linux'),('arch','x64')]:
   with self.subTest(key=key),self.assertRaises(ValueError):facts=performance();facts[key]=value;P['verify_627_performance'](facts)
  for name,key,value in [('controlled-immediate','synchronousBuilds',63),('controlled-batched','synchronousBuilds',1),('controlled-batched','stateBuilds',64),('unchanged-metadata','synchronousBuilds',1),('renderer-batched','titleEvents',0),('renderer-batched','elapsedMs',float('nan')),('renderer-immediate','stateBuildMs',-1)]:
   with self.subTest(name=name,key=key),self.assertRaises(ValueError):facts=performance();facts['measurements'][name][key]=value;P['verify_627_performance'](facts)
  with self.assertRaises(ValueError):facts=performance();facts['measurements']['renderer-batched']['frames']['count']=0;P['verify_627_performance'](facts)

 def test_fixed_panel_requires_real_translation_without_geometry_or_background_changes(self):
  validate=P['verify_627_motion'];validate(motion())
  mutations=[
   lambda f:f['frames']['lightOpening'][2].update(height=445),
   lambda f:f['frames']['lightOpening'][2]['matrix'].update(a=.8),
   lambda f:f['frames']['lightOpening'][2]['paths'].update(outline='changed shape'),
   lambda f:f['frames']['darkClosing'][2].update(geometryWrites=2),
   lambda f:f['frames']['darkClosing'][2].update(measurements=20),
   lambda f:f['frames']['lightOpening'].__setitem__(slice(None),[frame(.5,'opening',0)]),
   lambda f:f['geometry']['darkOpening']['mutations'].append({'time':15,'attribute':'d'}),
   lambda f:f['geometry']['lightClosing']['sizes'].append({'target':'panel','width':1000,'height':500}),
   lambda f:f['geometry']['darkControls'][0].update(accessible=False),
   lambda f:f['footer']['light']['after'].update(y=801),
   lambda f:f['background'].update(nativeBoundsCalls=1),
   lambda f:f['background'].update(resizeEvents=1),
   lambda f:f['background']['after'][0].update(width=899),
   lambda f:f['background']['after'][0].update(webContentsId=12),
   lambda f:f['background']['after'][0].update(epoch=2),
   lambda f:f['background']['after'][0].update(scrollY=21),
   lambda f:f['background']['snapshots'][0]['images'][0].update(png=False),
   lambda f:f['background']['snapshots'][0]['images'][0]['bounds'].update(x=101),
   lambda f:f['interruption']['after']['matrix'].update(f=0),
   lambda f:f['interruption'].update(closingFrames=[frame(.5,'closing',20),frame(.5,'closing',30)]),
   lambda f:f['frames']['reduced'].append(frame(.5,'opening',30)),
   lambda f:f['captureStates']['dark']['closing'].update(before=frame(0,'closed',20)),
   lambda f:f['captures']['light'].pop('closing'),
  ]
  for index,mutate in enumerate(mutations):
   with self.subTest(mutation=index),self.assertRaises(ValueError):facts=motion();mutate(facts);validate(facts)

 def test_desktop_requires_four_simultaneous_slides_bounded_native_work_and_page_pins(self):
  validate=P['verify_627_desktop_transition'];validate(desktop_transition())
  # A user's pre-existing page is also painted; it does not become a third
  # tracked test fixture or force the test to alter their desktop layout.
  extra=desktop_transition();row=extra['transitions'][0];row['allSnapshots'].append({**row['snapshots'][0],'id':'existing-page'});row['captures'][0]['ids'].append('existing-page');validate(extra)
  for mutate in [lambda r:r['captures'][0]['ids'].pop(),lambda r:r['allSnapshots'][-1].update(decoded=False),lambda r:r['allSnapshots'].pop()]:
   with self.assertRaises(ValueError):changed=copy.deepcopy(extra);mutate(changed['transitions'][0]);validate(changed)
  for mutate in [lambda f:f['transitions'].pop(),lambda f:f['transitions'][0].update(ackDelayMs=0),lambda f:f['transitions'][1].update(ackDelayMs=250),lambda f:f['transitions'][0].update(nativeLayoutCalls=0),lambda f:f['transitions'][0].update(nativeLayoutCalls=9),lambda f:f['transitions'][0].update(animationDurationMs=911,totalDurationMs=1200),lambda f:f['transitions'][0]['frames'][1].update(outgoingX=0),lambda f:f['transitions'][0]['frames'][1].update(width=900),lambda f:f['transitions'][0]['frames'].pop(),lambda f:f['transitions'][0]['snapshots'][0].update(decoded=False),lambda f:f['transitions'][0]['captures'][1].update(prepared=False),lambda f:f['transitions'][0]['captures'][0]['rows'][0].update(epoch=2),lambda f:f['transitions'][0]['pageBefore'].pop()]:
   with self.assertRaises(ValueError):facts=desktop_transition();mutate(facts);validate(facts)
  for key,value in [('id','replaced-page'),('webContentsId',12),('navigationEpoch',2),('url','about:blank'),('width',899),('height',599),('scrollX',11),('scrollY',21),('marker','reloaded-page')]:
   with self.subTest(pin=key),self.assertRaises(ValueError):facts=desktop_transition();facts['transitions'][0]['pageAfter'][0][key]=value;validate(facts)
  for key,value in [('domTag','IMG'),('pixelX',451),('pixelY',301),('viewportWidth',0),('rgba',[100,100,100,255]),('rgba',[240,240,240,0])]:
   with self.subTest(sample=key,value=value),self.assertRaises(ValueError):facts=desktop_transition();facts['transitions'][0]['captures'][0]['rows'][0]['sample'][key]=value;validate(facts)

 def test_fixed_viewport_controls_retain_tab_lifecycle_and_agent_acceptance(self):
  validate=P['verify_623_retained'];validate(retained623())
  for mutate in [lambda f:f.update(seamFree=True),lambda f:f.update(geometryVersion='6.0.23'),lambda f:f.update(fixedViewport=False),lambda f:f['frames'].pop(),lambda f:f['agentEntry'].update(color='unverified')]:
   with self.assertRaises(ValueError):facts=retained623();mutate(facts);validate(facts)
  for group,keys in [('tabLifecycle',P['LIFECYCLE_FACTS_623']),('agentEntry',P['AGENT_ENTRY_FACTS_623'])]:
   for key in keys:
    with self.subTest(group=group,key=key),self.assertRaises(ValueError):facts=retained623();facts[group][key]=False;validate(facts)

 def test_documented_schema_matches_current_native_bundle_contract(self):
  schema=json.loads((ROOT/'staging/mouse/6.0.27-arm64/evidence.schema.json').read_text())
  self.assertEqual(set(schema['required']),set(P['JSON_FILES_627']+P['RETAINED_JSON_FILES']+['mouse-626-verification.json',P['TRACE_FILE_627']]))
  self.assertEqual(set(schema['x-requiredPngFiles']),set(P['PNG_FILES_627']+['mouse-626-palette.png']))
  self.assertEqual(set(schema['x-requiredNativeMarkers']),set(P['NATIVE_MARKERS_627']+P['NATIVE_MARKERS_626']))
  self.assertEqual(set(schema['x-supersededFeatureTokens']),P['SUPERSEDED_FEATURE_TOKENS'])
  for name,fields in [('mouse-627-motion.json',P['MOTION_FACTS']),('mouse-627-desktop-transition.json',P['DESKTOP_TRANSITION_FACTS'])]:
   proof=schema['properties'][name]
   for field in fields:self.assertIn(field,proof['required']);self.assertEqual(proof['properties'][field],{'const':True})
  self.assertIn('allSnapshots',schema['$defs']['desktopTransition']['required']);self.assertIn('ids',schema['$defs']['desktopCapture']['required'])
  self.assertIn('sample',schema['$defs']['desktopCapture']['properties']['rows']['items']['required']);self.assertEqual(schema['$defs']['desktopPixelSample']['properties']['domTag'],{'const':'BODY'})
  for name in ['noraPresentation','desktopPresentation','pdfPresentation']:
   self.assertEqual(schema['$defs'][name]['properties']['source'],{'const':'beginFrameSubscription'})
   for field in ['source','sequence','elapsedMs','dirtyRect','scaleFactor','pixelSize','metadata']:self.assertIn(field,schema['$defs'][name]['required'])
  self.assertIn('painted',schema['$defs']['movingCaptureState']['required'])
  self.assertEqual(schema['$defs']['desktopTransition']['allOf'],[{'if':{'properties':{'direction':{'const':1}},'required':['direction']},'then':{'required':['paintedFrame']}}])
  self.assertIn('readability',schema['properties']['mouse-627-pdf-text.json']['required']);self.assertEqual(schema['properties']['mouse-627-pdf-text.json']['properties']['editTextVisible'],{'const':True})
  self.assertEqual(schema['$defs']['pdfPresentation']['properties']['metadata']['properties']['samples']['minItems'],12)
  self.assertEqual(schema['$defs']['desktopTransition']['properties']['nativeLayoutCalls'],{'type':'integer','minimum':1,'maximum':8})
  self.assertEqual(schema['properties']['mouse-626-verification.json']['properties']['supersededForNora'],{'const':P['SUPERSEDED_NORA_METADATA']})
  self.assertEqual(schema['properties']['mouse-626-verification.json']['not'],{'required':['nora']})
  self.assertEqual(schema['properties']['mouse-623-verification.json']['not'],{'required':['seamFree']})
  gate=schema['x-motionTraceGate'];self.assertFalse(gate['directIdentityLink']);self.assertFalse(gate['savedReportAcceptedAsInput']);self.assertEqual(gate['attribution'],'temporal-correlation')
  self.assertEqual(gate['inputFiles'],[P['TRACE_FILE_627'],'mouse-627-motion.json']);self.assertEqual(gate['maxTraceBytes'],P['TRACE_MAX_BYTES_627'])

 def test_trace_report_is_recomputed_from_exact_inputs_and_never_reused(self):
  validate=P['verify_627_motion_trace'];trace_name=P['TRACE_FILE_627'];motion_name='mouse-627-motion.json'
  files={trace_name:b'{"newTrace":1}',motion_name:b'{"newMotion":2}',P['TRACE_REPORT_627']:b'{"passed":true}'};reads=[]
  def read(name):reads.append(name);return files[name]
  accepted={'status':'pass','algorithm':'mouse627-motion-trace-evidence-v1','directIdentityLink':False,'attribution':'temporal-correlation'}
  verifier=Mock(return_value=accepted)
  with patch.object(P['runpy'],'run_path',return_value={'verify_trace_data':verifier}):
   result=validate(read,{'stage':'synthetic-test','publisherRun':'17'})
   verifier.assert_called_once_with({'newTrace':1},{'newMotion':2})
   self.assertEqual(reads,[trace_name,motion_name]);self.assertEqual(result['provenance']['publisherRun'],'17')
   self.assertEqual(result['inputs'][trace_name],{'size':len(files[trace_name]),'sha256':hashlib.sha256(files[trace_name]).hexdigest()})
   files[trace_name]=b'{"newTrace":3}';verifier.side_effect=ValueError('fresh trace rejected')
   with self.assertRaisesRegex(ValueError,'fresh trace rejected'):validate(read,{'stage':'synthetic-test','publisherRun':'18'})
   self.assertEqual(verifier.call_count,2);self.assertNotIn(P['TRACE_REPORT_627'],reads)
  for mutate in [lambda f:f.pop(trace_name),lambda f:f.update({trace_name:b''}),lambda f:f.update({trace_name:b'not JSON'})]:
   changed=dict(files);mutate(changed)
   with self.assertRaises((KeyError,ValueError)):validate(changed.__getitem__,{})
  for report in [{}, {**accepted,'status':'fail'}, {**accepted,'directIdentityLink':True},{**accepted,'attribution':'direct-identity'}]:
   with patch.object(P['runpy'],'run_path',return_value={'verify_trace_data':Mock(return_value=report)}),self.assertRaisesRegex(ValueError,'invalid acceptance report'):
    validate(files.__getitem__,{})

 def test_actual_trace_helper_interface_accepts_only_complete_fixture(self):
  fixture=runpy.run_path(str(ROOT/'tools/test-mouse627-motion-trace.py'))
  trace,motion=fixture['observed_schema_fixture']()
  files={P['TRACE_FILE_627']:json.dumps(trace).encode(),'mouse-627-motion.json':json.dumps(motion).encode()}
  result=P['verify_627_motion_trace'](files.__getitem__,{'stage':'explicitly-synthetic-contract'})
  self.assertEqual(result['evidence']['status'],'pass');self.assertFalse(result['evidence']['directIdentityLink'])
  trace['mouseMotionTrace']['complete']=False;files[P['TRACE_FILE_627']]=json.dumps(trace).encode()
  with self.assertRaisesRegex(ValueError,'complete motion scenario'):P['verify_627_motion_trace'](files.__getitem__,{})

 def test_source_trace_rejection_stops_before_candidate_import(self):
  # Exercise the real assembled import control flow with a synthetic GitHub
  # response and ZIP. Geometry validators are separately tested above.
  node=next(n for n in ast.parse(P['code']).body if isinstance(n,ast.FunctionDef) and n.name=='import_candidate')
  files={name:b'{}' for name in P['EVIDENCE_FILES_627']+P['EVIDENCE_FILES_626']}
  files['mouse-626-verification.json']=json.dumps(palette()).encode();files['mouse-626-palette.png']=b'\x89PNG\r\n\x1a\n'
  files['mouse-smoke-write.log']='\n'.join(P['NATIVE_MARKERS_627']+P['NATIVE_MARKERS_626']).encode()
  files['mouse-update-roundtrip.log']=b'MOUSE_627_REAL_625_TO_627_REPLACE_RELAUNCH_PROFILE_PASS'
  files[P['TRACE_FILE_627']]=b'{}';files[P['TRACE_REPORT_627']]=b'{"passed":true}'
  for missing in [False,True]:
   buffer=io.BytesIO()
   with zipfile.ZipFile(buffer,'w') as archive:
    for name,blob in files.items():
     if not missing or name!=P['TRACE_FILE_627']:archive.writestr(name,blob)
   archive_bytes=buffer.getvalue();digest=hashlib.sha256(archive_bytes).hexdigest();head='a'*40;merge='b'*40
   responses={'actions/runs/1':{'workflow_id':419668574,'head_sha':head,'status':'completed','conclusion':'success'},'pulls/4':{'merged':True,'head':{'sha':head},'base':{'ref':'main'},'merge_commit_sha':merge},f'compare/{head}...main':{'status':'ahead','behind_by':0},'actions/runs/1/artifacts':{'artifacts':[{'id':3,'name':'mouse-arm64-verification','expired':False,'digest':'sha256:'+digest}]}}
   api=Mock(side_effect=lambda repo,path:responses[path]);download=Mock(return_value=archive_bytes);trace=Mock(side_effect=ValueError('fresh source trace rejected'))
   scope={**P,'api':api,'SOURCE':'synthetic/source','HEAD':head,'RUN':1,'PR':4,'ARTIFACT':2,'PIN':{'sourceMerge':merge,'verificationArtifact':3,'verificationSHA256':digest},'subprocess':types.SimpleNamespace(check_output=download),'sha':lambda b:hashlib.sha256(b).hexdigest(),'io':io,'zipfile':zipfile,'verify_627_evidence':Mock(),'verify_627_motion_trace':trace}
   exec(compile(ast.Module(body=[node],type_ignores=[]),'<synthetic-import>','exec'),scope)
   with self.subTest(missing=missing),self.assertRaisesRegex(ValueError,'source motion trace missing|fresh source trace rejected'):scope['import_candidate']()
   self.assertEqual(api.call_count,4);download.assert_called_once();self.assertEqual(trace.call_count,0 if missing else 1)

 def test_fresh_installed_trace_rejection_precedes_every_release_api(self):
  # The stale report is intentionally present. It must never authorize a
  # release after the new native trace is rejected.
  code=P['code'];facts624={'version':'6.0.24','agent':dict.fromkeys(['layoutExact','pagesPreserved','aiReturn','reloadExact','defaultDisabled'],True),'history':dict.fromkeys(['undo','redo','persisted','pagesPreserved','entryRestore'],True),'progress':dict.fromkeys(['determinate','indeterminate','completionDismissed','stopped','pageScope'],True)}
  facts625={'version':'6.0.25'}
  for group,keys in [('pdf',['opened','annotated','reopened','originalPreserved','rotated','workerOffMainThread']),('docx',['edited','reopened','unmodifiedPartsPreserved','bold','tablePreserved','headerPreserved']),('xlsx',['edited','formulaPreserved','reopened','unmodifiedPartsPreserved','inlineStringPreserved']),('safeguards',['saveAs','originalUnchanged','dirtyCancel','conflictRejected','privateCleared','dirtySave']),('browser',['gridPreserved','pageIdentityPreserved'])]:facts625[group]=dict.fromkeys(keys,True)
  facts622={'fixedDesks':5,'suggestedRequests':7,'hiddenCaptures':0,'localModelFixtureRequests':3,**dict.fromkeys(['realThumbnails','externalWorker','ptyStdout','autonomousActions','stoppedListener','localhostPreview'],True)}
  search={'version':'6.0.25','stateRestored':True,'search':dict.fromkeys(['cleanGoogleDefault','pickerKeyboardSelection','addressAndHomeMatch','normalPersistsReload','privateRAMOnly','noExternalSearchNavigation'],True)}
  files={name:json.dumps(value) for name,value in [('mouse-622-verification.json',facts622),('mouse-623-verification.json',retained623()),('mouse-624-verification.json',facts624),('mouse-625-documents.json',facts625),('mouse-625-search-verification.json',search),('mouse-626-verification.json',palette()),(P['TRACE_REPORT_627'],{'passed':True})]}
  class SyntheticOutput:
   def __init__(self,name=''):self.name=name
   def __truediv__(self,name):return SyntheticOutput(name)
   def is_file(self):return True
   def read_text(self):return files.get(self.name,code+'\n'+'\n'.join(P['NATIVE_MARKERS_627']+P['NATIVE_MARKERS_626']))
   def read_bytes(self):return b'\x89PNG\r\n\x1a\n'
  api=Mock();trace=Mock(side_effect=ValueError('fresh installed trace rejected'))
  scope={**P,'OUT':SyntheticOutput(),'HEAD':'a'*40,'RUN':1,'ARTIFACT':2,'ARCHIVE_HASH':'c'*64,'api':api,'verify_627_evidence':Mock(),'verify_627_motion_trace':trace,'os':os}
  node=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name=='publish')
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<synthetic-publish>','exec'),scope)
  with patch.dict(os.environ,{'GITHUB_RUN_ID':'17','GITHUB_RUN_ATTEMPT':'2','GITHUB_SHA':'b'*40}),self.assertRaisesRegex(ValueError,'fresh installed trace rejected'):scope['publish']()
  trace.assert_called_once();api.assert_not_called();self.assertEqual(trace.call_args.args[1]['stage'],'installed-before-publication')

 def test_workflow_clears_only_temporary_motion_evidence_and_keeps_attempts(self):
  workflow=(ROOT/'.github/workflows/publish-mouse627.yml').read_text()
  reset='rm -f mouse-627-motion-trace.json mouse-627-motion.json mouse-627-motion-trace-report.json'
  self.assertIn(reset,workflow);self.assertLess(workflow.index(reset),workflow.index('env -u GH_TOKEN python3 mouse-verify.py'))
  self.assertIn('python3 tools/test-mouse627-motion-trace.py',workflow)
  self.assertIn('name: mouse627-release-verification-attempt-${{ github.run_attempt }}',workflow)

 def test_previous_and_historical_gates_are_preserved(self):
  code=P['code']
  for needle in ["released=api(REPO,'releases/tags/quadro-macos-v6.0.25-arm64')","Previous625 immutable updater blob mismatch","MOUSE_627_REAL_625_TO_627_REPLACE_RELAUNCH_PROFILE_PASS","MOUSE_625_DOCUMENTS_NATIVE_EDIT_SAVE_PRESERVE_PASS","MOUSE_625_SEARCH_ENGINE_NORMAL_PRIVATE_PASS","MOUSE_624_LAYOUT_UNDO_REDO_PERSIST_PASS","MOUSE_623_TAB_LIFECYCLE_CHIPS_STABILITY_PASS","MOUSE_622_AGENT_CDP_PTY_WORKER_STOP_PASS","MOUSE_PROFILE_COOKIE_RESTART_PASS","Refusing channel downgrade","Same-version channel differs","Refusing to overwrite different existing bytes","verify_626_facts(json.loads(z.read('mouse-626-verification.json')))","verify_627_evidence(z.read)","verify_627_evidence(lambda name:(OUT/name).read_bytes())"]:self.assertIn(needle,code)
  self.assertEqual(P['NATIVE_MARKERS_626'],['MOUSE_626_CAPTURE_ANY_COLOR_PASS'])
  self.assertEqual(P['FEATURE_TOKENS_626'],{'capture-arbitrary-color-hex-rgb','capture-arbitrary-color-export'})
  self.assertEqual(P['EVIDENCE_FILES_626'],['mouse-626-verification.json','mouse-626-palette.png'])
  for obsolete in P['SUPERSEDED_FEATURE_TOKENS']|{'MOUSE_626_BURROW_LIQUID_SYMMETRY_PASS','MOUSE_623_BURROW_GEOMETRY_AND_SEAM_PASS'}:self.assertNotIn(obsolete,code)
  self.assertIn('SUPERSEDED_FEATURE_TOKENS.intersection',code)
  self.assertIn('MOUSE_627_BURROW_FIXED_VIEWPORT_CONTROLS_PASS',code)
  P['verify_626_facts'](palette())
  for key in P['PALETTE_FACTS']:
   for value in [False,'true',1,None]:
    with self.subTest(palette=key,value=value),self.assertRaises(ValueError):facts=palette();facts['palette'][key]=value;P['verify_626_facts'](facts)
  for mutate in [lambda f:f.update(version='6.0.27'),lambda f:f.update(stateRestored=False),lambda f:f.pop('supersededForNora'),lambda f:f.update(nora=dict.fromkeys(P['scope']['FACT_GROUPS']['nora'],True))]:
   with self.assertRaises(ValueError):facts=palette();mutate(facts);P['verify_626_facts'](facts)

 def test_pending_and_unverified_pins_fail_closed(self):
  ready=P['ready_pin'];pin=json.loads((ROOT/'staging/mouse/6.0.27-arm64/pin.json').read_text())
  # Explicit synthetic values exercise validation independently of a real pin
  # that may later be completed by the release owner.
  pin.update(ready=True,source='a'*40,sourceMerge='b'*40,archiveSHA256='c'*64,verificationSHA256='d'*64,run=1,artifact=2,verificationArtifact=3,sourcePR=4)
  for package in pin['packages'].values():package.update(size=1,sha256='e'*64)
  with tempfile.TemporaryDirectory() as directory:
   stage=pathlib.Path(directory)/'staging/mouse/6.0.27-arm64';stage.mkdir(parents=True)
   (stage/'PUBLISH_OWNER').write_text('READY_TO_PUBLISH_MOUSE_627\nSynthetic unit fixture, never a release record.\n')
   (stage/'RELEASE_NOTES.md').write_text('Synthetic offline validation fixture.\n')
   def write(value):(stage/'pin.json').write_text(json.dumps(value))
   with patch.dict(ready.__globals__,{'__file__':str(pathlib.Path(directory)/'tools/mouse627-release.py')}):
    write(pin);self.assertEqual(ready(),pin)
    for key,value in [('ready',False),('ready','true'),('source',''),('sourceMerge','x'*40),('archiveSHA256','UNSET'),('verificationSHA256',''),('run',0),('sourcePR',0)]:
     with self.subTest(key=key),self.assertRaises(ValueError):changed=copy.deepcopy(pin);changed[key]=value;write(changed);ready()
    with self.assertRaisesRegex(ValueError,'previous625'):changed=copy.deepcopy(pin);changed['previous']['package']['size']+=1;write(changed);ready()
    write(pin);(stage/'PUBLISH_OWNER').write_text('PENDING_MOUSE_627\nUNSET native proof\n')
    with self.assertRaisesRegex(ValueError,'not final'):ready()
  text=(ROOT/'tools/mouse627-release.py').read_text();self.assertIn("ready_pin();builtins.exec(builtins.compile(code,__file__,'exec'),globals())",text)

if __name__=='__main__':unittest.main()
