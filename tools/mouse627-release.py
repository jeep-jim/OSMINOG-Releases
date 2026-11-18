#!/usr/bin/env python3
"""Publish exact627 bytes; supersede requested Nora geometry, retain release safety."""
import builtins,hashlib,json,math,pathlib,re,runpy,struct,sys,zlib

# Extract the reviewed publisher without running its pin dispatch or any API.
# The existing607→626 files remain byte-for-byte unchanged.
base=pathlib.Path(__file__).with_name('mouse626-release.py')
source=base.read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='956084c555e0472df820dd20039d4e59b815cd8e','Reviewed626 publisher changed'
wrapper=source.decode('utf-8');dispatch='\ndef ready_pin():'
assert wrapper.count(dispatch)==1
wrapper=wrapper.split(dispatch,1)[0]+'\n_emit(code)\n'
output=[];scope={'__file__':str(base),'__name__':'reviewed_source_transform','_emit':output.append}
builtins.exec(builtins.compile(wrapper,str(base),'exec'),scope)
assert len(output)==1,'Ambiguous reviewed626 transform'
code=output[0].replace('6.0.26','6.0.27').replace('mouse626-release','mouse627-release').replace('MOUSE626_','MOUSE627_')

def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)

# The owner explicitly rejected626's contour growth. Supersede only that
# acceptance contract in627; do not edit/relabel the historical626 publisher.
# All five colour checks and the existing release/security/update gates remain.
SUPERSEDED_NORA_TOKENS={'burrow-liquid-footer-continuous-morph','burrow-symmetric-layout','burrow-reversible-reduced-motion'}
SUPERSEDED_FEATURE_TOKENS=SUPERSEDED_NORA_TOKENS|{'burrow-fixed-top-curves-three-heights','burrow-footer-seam-free-both-themes','burrow-seam-one-pixel-join'}
assert SUPERSEDED_NORA_TOKENS.issubset(scope['FEATURE_TOKENS'])
assert scope['FACT_GROUPS']['nora']==['symmetric','footerConnected','continuousOpen','continuousClose','interruptedMotion','resizeContinuous','reducedMotion','contentRevealed','controlsWork']
PALETTE_FACTS=['arbitraryHex','arbitraryRGB','fieldSelection','annotationApplied','exportPreserved']
assert scope['FACT_GROUPS']['palette']==PALETTE_FACTS
FEATURE_TOKENS_626=scope['FEATURE_TOKENS']-SUPERSEDED_NORA_TOKENS
assert FEATURE_TOKENS_626=={'capture-arbitrary-color-hex-rgb','capture-arbitrary-color-export'}
NATIVE_MARKERS_626=['MOUSE_626_CAPTURE_ANY_COLOR_PASS']
EVIDENCE_FILES_626=['mouse-626-verification.json','mouse-626-palette.png']
for old,new in [('FEATURE_TOKENS','FEATURE_TOKENS_626'),('NATIVE_MARKERS','NATIVE_MARKERS_626'),('EVIDENCE_FILES','EVIDENCE_FILES_626')]:code=code.replace(old,new)
once('real-625-to-626-profile-preserving-install','real-625-to-627-profile-preserving-install')
old_marker='MOUSE_626_REAL_625_TO_626_REPLACE_RELAUNCH_PROFILE_PASS';new_marker='MOUSE_627_REAL_625_TO_627_REPLACE_RELAUNCH_PROFILE_PASS'
assert code.count(old_marker)==3
code=code.replace(old_marker,new_marker)
once('Mouse Browser 6.0.27 — Нора и полная палитра','Mouse Browser 6.0.27 — Нора, рабочие столы и документы')
once('MOUSE_623_BURROW_GEOMETRY_AND_SEAM_PASS','MOUSE_627_BURROW_FIXED_VIEWPORT_CONTROLS_PASS')
once("'burrow-seam-one-pixel-join'","'nora-fixed-viewport-scroll-controls'")
once("['fixedTopCurves','seamFree','outlineMatchesFooter']", "['fixedTopCurves','outlineMatchesFooter','fixedViewport','scrollableContent','footerStationary','supersededOldGeometry']")


FEATURE_TOKENS_627={
 'native-window-footer-drag-both-sides','native-window-grip-and-controls',
 'documents-ordinary-tabs-multiple-panes','pdf-existing-text-replacement',
 'coalesced-tab-state-events','unchanged-start-preferences-no-disk-write',
 'nora-fixed-size-transform-slide','nora-static-contour-compositor-only',
 'nora-background-footer-stable','nora-fixed-viewport-scroll-controls','nora-reversible-reduced-motion',
 'burrow-outline-matches-footer-border',
 'desktop-compositor-simultaneous-transition','desktop-transition-constant-native-layout',
}
NATIVE_MARKERS_627=[
 'MOUSE_627_NATIVE_WINDOW_FOOTER_DRAG_PASS','MOUSE_627_DOCUMENT_TABS_NATIVE_PASS',
 'MOUSE_627_PDF_EXISTING_TEXT_NATIVE_PASS','MOUSE_627_NATIVE_METADATA_WORKLOAD_PRESERVES_LIVE_PAGES_PASS',
 'MOUSE_627_FIXED_PANEL_SLIDE_NATIVE_PASS','MOUSE_627_BURROW_FIXED_VIEWPORT_CONTROLS_PASS','MOUSE_627_COMPOSITOR_DESKTOP_SLIDE_NATIVE_PASS',
]
JSON_FILES_627=['mouse-627-window-verification.json','mouse-627-document-tabs.json','mouse-627-pdf-text.json','mouse-627-performance.json','mouse-627-motion.json','mouse-627-desktop-transition.json']
PNG_FILES_627=['mouse-627-window-light.png','mouse-627-window-dark.png','mouse-627-document-tabs.png','mouse-627-pdf-existing-text.png','mouse-627-performance.png']+[f'mouse-627-panel-{theme}-{phase}.png' for theme in ['light','dark'] for phase in ['opening','open','closing']]+[f'mouse-627-desktop-transition-{theme}.png' for theme in ['light','dark']]
RETAINED_JSON_FILES=['mouse-623-verification.json']
EVIDENCE_FILES_627=JSON_FILES_627+RETAINED_JSON_FILES+PNG_FILES_627
TRACE_FILE_627='mouse-627-motion-trace.json'
TRACE_REPORT_627='mouse-627-motion-trace-report.json'
SOURCE_TRACE_REPORT_627='mouse-627-source-motion-trace-report.json'
TRACE_MAX_BYTES_627=72*1024**2
DOCUMENT_FACTS=['ordinaryTabs','noDocumentDialog','twoVisibleEditors','paneResize','tabSwitchDraftPreserved','closeCancelPreserved','navigationCancelPreserved','navigationPreservesTabId','desktopMovePreserved','privateCleared']
PDF_FACTS=['originalTextAbsent','replacementPresent','cyrillicPresent','unrelatedContentPreserved','undo','editTextVisible']
MOTION_FACTS=['fixedSize','translationOnly','constantContour','openClosePainted','interruptionPreserved','reducedMotion','contentScrollable','backgroundStable','footerStable','stateRestored']
DESKTOP_TRANSITION_FACTS=['simultaneous','pngSurfaces','compositorOnly','nativeIdentityPreserved','viewportAndScrollPreserved','slowAckBounded','restored']
LIFECYCLE_FACTS_623=['closedPageDestroyed','closedCountRemoved','metadataNodesStable','chipReorder','chipTransfer','faviconsPainted','pageIdentityPreserved']
AGENT_ENTRY_FACTS_623=['startService','aiPreset','aiSelect','disabledUntilEnabled','mascotLoaded']
SUPERSEDED_NORA_METADATA={'version':'6.0.27','proof':'mouse-627-motion.json','reason':'Fixed-size compositor slide replaces the former contour morph'}

def finite(value):return type(value) in (int,float) and math.isfinite(value)
def nonnegative(value):return finite(value) and value>=0
def whole(value,minimum=0):return type(value) is int and value>=minimum
def facts_version(facts,label):
 if not isinstance(facts,dict) or facts.get('version')!='6.0.27':raise ValueError('Mouse627 native evidence version mismatch: '+label)
def true_fields(facts,keys,label):
 if not isinstance(facts,dict) or not all(facts.get(key) is True for key in keys):raise ValueError('Mouse627 native evidence incomplete: '+label)

def verify_626_facts(facts):
 if not isinstance(facts,dict) or facts.get('version')!='6.0.26':raise ValueError('Mouse626 native palette evidence version mismatch')
 true_fields(facts,['stateRestored'],'626 palette restoration')
 true_fields(facts.get('palette'),PALETTE_FACTS,'626 complete colour palette')
 if facts.get('supersededForNora')!=SUPERSEDED_NORA_METADATA or 'nora' in facts:raise ValueError('Mouse626 obsolete contour evidence must be explicitly superseded by627')

def verify_623_retained(facts):
 if not isinstance(facts,dict) or facts.get('version')!='6.0.23':raise ValueError('Mouse623 retained evidence version mismatch')
 if facts.get('geometryVersion')!='6.0.27' or 'seamFree' in facts:raise ValueError('Mouse623 old seam geometry must be explicitly superseded by627')
 true_fields(facts,['fixedTopCurves','outlineMatchesFooter','fixedViewport','scrollableContent','footerStationary','supersededOldGeometry'],'623 fixed viewport controls')
 if facts.get('themes')!=['light','dark'] or facts.get('states')!=['compact','modes','preview']:raise ValueError('Mouse623 native control states incomplete')
 frames=facts.get('frames')
 if not isinstance(frames,list) or len(frames)!=6 or any(not isinstance(f,dict) for f in frames) or {(f.get('theme'),f.get('state')) for f in frames}!={(theme,state) for theme in ['light','dark'] for state in ['compact','modes','preview']}:raise ValueError('Mouse623 native control frames incomplete')
 true_fields(facts.get('tabLifecycle'),LIFECYCLE_FACTS_623,'623 tab lifecycle')
 true_fields(facts.get('agentEntry'),AGENT_ENTRY_FACTS_623,'623 agent controls')
 if facts['agentEntry'].get('color') not in ['orange','cyan','green','violet','coral']:raise ValueError('Mouse623 native agent colour evidence incomplete')

def verify_627_window(facts):
 facts_version(facts,'window');true_fields(facts,['restored'],'window restoration')
 expected={theme+' '+region for theme in ['light','dark'] for region in ['footer left','footer right','top grip']}
 rows=facts.get('gestures')
 if not isinstance(rows,list) or len(rows)!=6 or any(not isinstance(row,dict) for row in rows) or {row.get('label') for row in rows}!=expected:raise ValueError('Mouse627 native window gestures incomplete')
 for row in rows:
  before=row.get('before');after=row.get('after');requested=row.get('requested');point=row.get('point')
  if not all(isinstance(value,dict) for value in [before,after,requested,point]):raise ValueError('Mouse627 native window geometry missing')
  if not all(finite(value.get(key)) for value in [before,after] for key in ['x','y','width','height']) or not all(finite(requested.get(key)) and requested[key]!=0 for key in ['dx','dy']) or not all(finite(point.get(key)) for key in ['x','y']):raise ValueError('Mouse627 native window geometry invalid')
  if before['width']<=0 or before['height']<=0 or before['width']!=after['width'] or before['height']!=after['height']:raise ValueError('Mouse627 native drag resized the window')
  if abs(after['x']-before['x']-requested['dx'])>2 or abs(after['y']-before['y']-requested['dy'])>2:raise ValueError('Mouse627 native window did not translate as requested')
 controls=facts.get('controls')
 if not isinstance(controls,list) or len(controls)!=4 or set(controls)!={theme+' '+control for theme in ['light','dark'] for control in ['theme','Nora']}:raise ValueError('Mouse627 native window controls incomplete')

def verify_627_documents(facts):
 facts_version(facts,'document tabs');true_fields(facts,DOCUMENT_FACTS,'document tabs')

def verify_627_pdf(facts):
 facts_version(facts,'PDF text');true_fields(facts,PDF_FACTS,'existing PDF text')
 painted=facts.get('readability');metadata=presented_frame(painted,'PDF glyphs')
 if painted.get('filename')!='mouse-627-pdf-existing-text.png' or metadata.get('text')!='Mouse627 исправлен' or metadata.get('mode')!='edit' or metadata.get('minimum')!=12:raise ValueError('Mouse627 PDF edit-mode glyph proof missing')
 style=metadata.get('beforeStyle')
 if not isinstance(style,dict) or style.get('backdropFilter')!='none' or style.get('webkitBackdropFilter') not in ['', 'none'] or style.get('appearance')!='none':raise ValueError('Mouse627 PDF hit regions still blur or paint over the text')
 viewport=positive_size(metadata.get('viewport'),'PDF viewport');size=painted['pixelSize'];sx=size['width']/viewport['width'];sy=size['height']/viewport['height'];radius=math.ceil(max(sx,sy));samples=metadata.get('samples')
 if not isinstance(samples,list) or len(samples)!=12:raise ValueError('Mouse627 PDF requires twelve rendered glyph samples')
 points=[];pixels=set()
 for sample in samples:
  if not isinstance(sample,dict) or not all(finite(sample.get(key)) for key in ['x','y']) or not 0<=sample['x']<viewport['width'] or not 0<=sample['y']<viewport['height']:raise ValueError('Mouse627 PDF source glyph location is invalid')
  if any(math.hypot(sample['x']-x,sample['y']-y)<2.999 for x,y in points):raise ValueError('Mouse627 PDF glyph samples are not separated')
  points.append((sample['x'],sample['y']));source=rgba(sample.get('sourceRGBA'),'PDF source canvas');actual=rgba(sample.get('rgba'),'PDF presentation')
  if source[3]!=255 or max(source[:3])>=60 or actual[3]!=255 or max(actual[:3])>90 or sample.get('dark')!=max(actual[:3]):raise ValueError('Mouse627 PDF text is covered or blurred in the presentation')
  for axis,dimension,scale in [('X','width',sx),('Y','height',sy)]:
   value=sample.get('pixel'+axis)
   if not whole(value) or not 0<=value<size[dimension] or abs(value-math.floor(sample[axis.lower()]*scale))>radius:raise ValueError('Mouse627 PDF glyph proof is mapped to an unrelated pixel')
  point=(sample['pixelX'],sample['pixelY'])
  if point in pixels:raise ValueError('Mouse627 PDF presentation repeats a glyph sample')
  pixels.add(point)

def verify_627_performance(facts):
 facts_version(facts,'performance');true_fields(facts,['stateRestored','livePagesPreserved'],'performance restoration and page lifetime')
 if facts.get('platform')!='darwin' or facts.get('arch')!='arm64' or facts.get('panes')!=8:raise ValueError('Mouse627 performance is not the installed eight-pane arm64 workload')
 measurements=facts.get('measurements');names=['controlled-immediate','controlled-batched','unchanged-metadata','renderer-immediate','renderer-batched']
 if not isinstance(measurements,dict) or set(measurements)!=set(names):raise ValueError('Mouse627 performance measurements incomplete')
 for name in names:
  row=measurements[name]
  if not isinstance(row,dict) or row.get('label')!=name or not whole(row.get('stateBuilds')) or not whole(row.get('layoutCalls')) or not nonnegative(row.get('stateBuildMs')) or not finite(row.get('elapsedMs')) or row['elapsedMs']<=0:raise ValueError('Mouse627 invalid work-count measurement: '+name)
  frames=row.get('frames')
  if not isinstance(frames,dict) or not whole(frames.get('count'),1) or not nonnegative(frames.get('p95Ms')) or not nonnegative(frames.get('maxMs')) or frames['maxMs']<frames['p95Ms']:raise ValueError('Mouse627 renderer frame evidence missing: '+name)
  for key in ['mainMemoryBefore','mainMemoryAfter']:
   memory=row.get(key)
   if not isinstance(memory,dict) or not all(nonnegative(memory.get(field)) for field in ['rss','heapTotal','heapUsed','external','arrayBuffers']) or memory['rss']<=0:raise ValueError('Mouse627 main-process memory sample missing: '+name)
 immediate=measurements['controlled-immediate'];batched=measurements['controlled-batched'];unchanged=measurements['unchanged-metadata']
 if immediate.get('events')!=64 or batched.get('events')!=64 or immediate.get('synchronousBuilds')!=64 or batched.get('synchronousBuilds')!=0 or immediate['stateBuilds']<64 or not 1<=batched['stateBuilds']<immediate['stateBuilds']:raise ValueError('Mouse627 controlled metadata batching reduction not demonstrated')
 if unchanged.get('events')!=320 or unchanged.get('synchronousBuilds')!=0:raise ValueError('Mouse627 unchanged metadata still rebuilds state')
 for name in ['renderer-immediate','renderer-batched']:
  row=measurements[name]
  if row.get('requestedTitleChanges')!=96 or not whole(row.get('titleEvents'),1) or row['stateBuilds']<1:raise ValueError('Mouse627 actual renderer title events missing: '+name)
 # Timings and memory are retained for inspection, with no invented machine-
 # independent performance threshold. Only deterministic work counts are gated.

def rectangle(value,label):
 if not isinstance(value,dict) or not all(finite(value.get(k)) for k in ['x','y','width','height']) or value['width']<0 or value['height']<0:raise ValueError('Mouse627 invalid rectangle: '+label)

def positive_size(value,label):
 if not isinstance(value,dict) or not all(finite(value.get(key)) and value[key]>0 for key in ['width','height']):raise ValueError('Mouse627 invalid presentation size: '+label)
 return value

def rgba(value,label):
 if not isinstance(value,list) or len(value)!=4 or any(not whole(channel) or channel>255 for channel in value):raise ValueError('Mouse627 invalid RGBA sample: '+label)
 return value

def presented_frame(value,label):
 if not isinstance(value,dict) or value.get('source')!='beginFrameSubscription' or not whole(value.get('sequence'),1) or not nonnegative(value.get('elapsedMs')) or not finite(value.get('scaleFactor')) or value['scaleFactor']<=0:raise ValueError('Mouse627 actual presentation capture missing: '+label)
 rectangle(value.get('dirtyRect'),label+' dirty rectangle');size=positive_size(value.get('pixelSize'),label+' bitmap')
 if not all(whole(size[key],1) and size[key]<=8192 for key in ['width','height']) or size['width']*size['height']*4>64*1024**2:raise ValueError('Mouse627 presentation bitmap exceeds its bounded size: '+label)
 metadata=value.get('metadata')
 if not isinstance(metadata,dict):raise ValueError('Mouse627 actual presentation metadata missing: '+label)
 return metadata

def verify_panel_presentation(painted,theme,phase,first,before):
 metadata=presented_frame(painted,'Nora '+theme+' '+phase);geometry=metadata.get('geometry')
 if metadata.get('theme')!=theme or metadata.get('state')!=phase or not isinstance(geometry,dict) or geometry.get('before')!=before:raise ValueError('Mouse627 Nora presentation state differs from its recorded action')
 viewport=positive_size(geometry.get('viewport'),'Nora viewport');size=painted['pixelSize'];sx=size['width']/viewport['width'];sy=size['height']/viewport['height']
 if not all(finite(geometry.get(key)) and abs(geometry[key]-first[key])<=1 for key in ['width','height','left','baseline']):raise ValueError('Mouse627 Nora pixels do not use the fixed panel geometry')
 for key in ['fill','line']:
  color=geometry.get(key)
  if not isinstance(color,list) or len(color)!=3 or any(not whole(channel) or channel>255 for channel in color):raise ValueError('Mouse627 Nora presentation colour missing')
 if not all(finite(metadata.get(key)) for key in ['top','translateY','progress']):raise ValueError('Mouse627 Nora painted position missing')
 translate=metadata['translateY'];height=geometry['height'];top=geometry['baseline']-height
 if not max(16,height*.08)<=translate<=height*.9 or abs(metadata['top']-top-translate)>1e-6 or abs(metadata['progress']-(1-translate/height))>1e-6:raise ValueError('Mouse627 Nora PNG is an endpoint instead of a moving panel')
 fill=geometry['fill'];delta=[line-channel for line,channel in zip(geometry['line'],fill)];norm=sum(value*value for value in delta)
 if norm==0:raise ValueError('Mouse627 Nora outline cannot be distinguished from its fill')
 def distance(a,b):return max(abs(x-y) for x,y in zip(a,b))
 def solid(pixel):return pixel[3]==255 and distance(pixel[:3],fill)<=2
 probes=metadata.get('probes');expected_y=round(metadata['top']*sy)
 if not isinstance(probes,list) or len(probes)!=3 or abs(expected_y-metadata['top']*sy)>1e-6:raise ValueError('Mouse627 Nora actual edge samples missing')
 for fraction,probe in zip([.2,.5,.8],probes):
  if not isinstance(probe,dict) or probe.get('x')!=math.floor((geometry['left']+geometry['width']*fraction)*sx) or probe.get('y')!=expected_y or not whole(probe.get('x')) or not whole(probe.get('y')):raise ValueError('Mouse627 Nora edge probe uses an unrelated pixel')
  if not 0<=probe['x']<size['width'] or probe['y']-max(2,math.floor(2*sy+.5))<0 or probe['y']+max(6,math.floor(6*sy+.5))>=size['height']:raise ValueError('Mouse627 Nora edge probe is outside the presentation')
  above,edge,inside,lower=[rgba(probe.get(key),'Nora '+key) for key in ['above','edge','inside','lower']];mix=sum((value-channel)*step for value,channel,step in zip(edge[:3],fill,delta))/norm
  if solid(above) or not solid(inside) or not solid(lower) or edge[3]!=255 or not .025<=mix<=1.03 or distance(edge[:3],[channel+step*mix for channel,step in zip(fill,delta)])>8:raise ValueError('Mouse627 Nora PNG does not show its opaque moving top edge')

def verify_desktop_presentation(painted,theme):
 metadata=presented_frame(painted,'desktop '+theme);viewport=positive_size(metadata.get('viewport'),'desktop viewport');size=painted['pixelSize']
 if painted.get('filename')!=f'mouse-627-desktop-transition-{theme}.png' or metadata.get('bothDesktopsPainted') is not True or metadata.get('colors')!=[[199,37,77],[29,125,220]] or metadata.get('pixelSize')!=size or metadata.get('scaleFactor')!=painted['scaleFactor']:raise ValueError('Mouse627 desktop presentation does not identify both actual surfaces')
 css_rows=viewport.get('rows')
 if not isinstance(css_rows,list) or len(css_rows)!=2 or not all(finite(y) for y in css_rows):raise ValueError('Mouse627 desktop source band rows missing')
 expected=list(dict.fromkeys(max(0,min(size['height']-1,math.floor(y*size['height']/viewport['height']))) for y in css_rows));rows=metadata.get('rows');minimum=math.ceil(16*size['width']/viewport['width']);counts=metadata.get('counts')
 if rows!=expected or not whole(metadata.get('minimum'),1) or metadata['minimum']!=minimum or not isinstance(counts,list) or len(counts)!=2 or any(not whole(count) or not minimum<=count<=size['width']*len(rows) for count in counts):raise ValueError('Mouse627 desktop PNG is missing one of the two moving surfaces')

def decode_png(blob,label):
 # Bounded, dependency-free decoding of Electron's RGB8/RGBA8 screenshots.
 # Pixel acceptance must inspect the exact archived PNG, not just JSON claims.
 if not isinstance(blob,bytes) or not blob.startswith(b'\x89PNG\r\n\x1a\n') or len(blob)>16*1024**2:raise ValueError('Mouse627 screenshot is not PNG: '+label)
 offset=8;header=None;compressed=bytearray();ended=False
 while offset<len(blob):
  if offset+12>len(blob):raise ValueError('Mouse627 truncated PNG: '+label)
  length=struct.unpack_from('>I',blob,offset)[0];kind=blob[offset+4:offset+8];end=offset+12+length
  if end>len(blob):raise ValueError('Mouse627 truncated PNG chunk: '+label)
  chunk=blob[offset+8:offset+8+length];crc=struct.unpack_from('>I',blob,offset+8+length)[0]
  if zlib.crc32(kind+chunk)&0xffffffff!=crc:raise ValueError('Mouse627 PNG checksum mismatch: '+label)
  if header is None and kind!=b'IHDR':raise ValueError('Mouse627 PNG has no first header: '+label)
  if kind==b'IHDR':
   if header is not None or length!=13:raise ValueError('Mouse627 ambiguous PNG header: '+label)
   width,height,depth,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',chunk);channels={2:3,6:4}.get(color)
   if not channels or depth!=8 or compression or filtering or interlace or not 0<width<=8192 or not 0<height<=8192 or width*height*4>64*1024**2:raise ValueError('Mouse627 unsupported or oversized PNG: '+label)
   header=(width,height,channels)
  elif kind==b'IDAT':compressed.extend(chunk)
  elif kind==b'IEND':
   if length or end!=len(blob):raise ValueError('Mouse627 invalid PNG end: '+label)
   ended=True;break
  elif kind==b'tRNS' or kind[0]&32==0 and kind!=b'PLTE':raise ValueError('Mouse627 unsupported PNG chunk: '+label)
  offset=end
 if not ended or not header or not compressed:raise ValueError('Mouse627 incomplete PNG: '+label)
 width,height,channels=header;stride=width*channels;expected=(stride+1)*height;decoder=zlib.decompressobj()
 try:raw=decoder.decompress(compressed,expected+1)
 except zlib.error as error:raise ValueError('Mouse627 corrupt PNG pixels: '+label) from error
 if len(raw)!=expected or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:raise ValueError('Mouse627 invalid PNG pixel length: '+label)
 result=bytearray(stride*height);previous=bytearray(stride)
 for y in range(height):
  start=y*(stride+1);method=raw[start];row=bytearray(raw[start+1:start+1+stride])
  if method not in range(5):raise ValueError('Mouse627 invalid PNG row filter: '+label)
  if method:
   for x in range(stride):
    a=row[x-channels] if x>=channels else 0;b=previous[x];c=previous[x-channels] if x>=channels else 0
    if method==1:predictor=a
    elif method==2:predictor=b
    elif method==3:predictor=(a+b)//2
    else:
     p=a+b-c;pa=abs(p-a);pb=abs(p-b);pc=abs(p-c);predictor=a if pa<=pb and pa<=pc else b if pb<=pc else c
    row[x]=(row[x]+predictor)&255
  result[y*stride:(y+1)*stride]=row;previous=row
 return{'width':width,'height':height,'channels':channels,'pixels':result}

def png_pixel(image,x,y):
 if not whole(x) or not whole(y) or x>=image['width'] or y>=image['height']:raise ValueError('Mouse627 PNG sample is outside its image')
 start=(y*image['width']+x)*image['channels'];value=list(image['pixels'][start:start+image['channels']]);return value if image['channels']==4 else value+[255]

def presented_png(read,name,painted):
 image=decode_png(read(name),name)
 if any(image[key]!=painted['pixelSize'][key] for key in ['width','height']):raise ValueError('Mouse627 PNG dimensions differ from its selected presentation: '+name)
 return image

def verify_presented_pixels(facts,read):
 motion=facts['mouse-627-motion.json']
 for theme in ['light','dark']:
  for phase in ['opening','closing']:
   painted=motion['captureStates'][theme][phase]['painted'];metadata=painted['metadata'];image=presented_png(read,motion['captures'][theme][phase],painted);sy=image['height']/metadata['geometry']['viewport']['height'];near=max(2,math.floor(2*sy+.5));far=max(6,math.floor(6*sy+.5))
   for probe in metadata['probes']:
    for key,dy in [('above',-near),('edge',0),('inside',near),('lower',far)]:
     if png_pixel(image,probe['x'],probe['y']+dy)!=probe[key]:raise ValueError('Mouse627 Nora pixel evidence differs from the saved PNG')
 for row in facts['mouse-627-desktop-transition.json']['transitions']:
  if row['direction']!=1:continue
  painted=row['paintedFrame'];metadata=painted['metadata'];image=presented_png(read,painted['filename'],painted);counts=[0,0]
  for y in metadata['rows']:
   for x in range(image['width']):
    pixel=png_pixel(image,x,y)
    if pixel[3]!=255:continue
    for index,color in enumerate(metadata['colors']):
     if all(abs(a-b)<=2 for a,b in zip(pixel[:3],color)):counts[index]+=1
  if counts!=metadata['counts'] or any(count<metadata['minimum'] for count in counts):raise ValueError('Mouse627 desktop PNG does not paint both recorded surfaces')
 painted=facts['mouse-627-pdf-text.json']['readability'];image=presented_png(read,painted['filename'],painted)
 for sample in painted['metadata']['samples']:
  if png_pixel(image,sample['pixelX'],sample['pixelY'])!=sample['rgba']:raise ValueError('Mouse627 PDF glyph pixels differ from the saved PNG')

def page_pins(rows,label,epoch_key,background=False):
 if not isinstance(rows,list) or not rows:raise ValueError('Mouse627 live page evidence missing: '+label)
 result={}
 required=['id','webContentsId','url',epoch_key,'width','height','scrollX','scrollY']+(['bounds','clip','timeOrigin','resizeEvents','visible','surfaceBounds'] if background else ['marker'])
 for row in rows:
  if not isinstance(row,dict) or any(key not in row for key in required):raise ValueError('Mouse627 incomplete live page pin: '+label)
  if not isinstance(row['id'],str) or not row['id'] or row['id'] in result or not whole(row['webContentsId'],1) or not whole(row[epoch_key]) or not isinstance(row['url'],str):raise ValueError('Mouse627 invalid live page identity: '+label)
  if not all(finite(row[key]) for key in ['width','height','scrollX','scrollY']) or min(row['width'],row['height'])<=0:raise ValueError('Mouse627 invalid live viewport: '+label)
  if background:
   rectangle(row['bounds'],label)
   if row['clip'] is not None:rectangle(row['clip'],label+' clip')
   if type(row['visible']) is not bool:raise ValueError('Mouse627 background page visibility missing: '+label)
   if row['surfaceBounds'] is not None:rectangle(row['surfaceBounds'],label+' surface')
   elif row['visible']:raise ValueError('Mouse627 visible page has no saved surface bounds: '+label)
   if not finite(row['timeOrigin']) or row['timeOrigin']<=0 or row['resizeEvents']!=[]:raise ValueError('Mouse627 background renderer changed: '+label)
  elif row['marker'] is None:raise ValueError('Mouse627 loaded page marker missing: '+label)
  result[row['id']]=row
 return result

def motion_frame(frame,label):
 if not isinstance(frame,dict) or not all(finite(frame.get(k)) for k in ['time','height','targetHeight','width','progress','left','baseline','opacity']) or min(frame['width'],frame['height'])<=0 or not 0<=frame['progress']<=1:raise ValueError('Mouse627 invalid fixed-panel frame: '+label)
 if not whole(frame.get('geometryWrites')) or not whole(frame.get('measurements')) or not isinstance(frame.get('font'),str) or not frame['font'] or any(type(frame.get(key)) is not bool for key in ['open','hidden','inert']):raise ValueError('Mouse627 missing fixed-panel counters: '+label)
 paths=frame.get('paths');matrix=frame.get('matrix')
 if not isinstance(paths,dict) or not all(isinstance(paths.get(key),str) and paths[key] for key in ['outline','fill','viewBox']) or not isinstance(matrix,dict) or not all(finite(matrix.get(key)) for key in ['a','b','c','d','e','f']):raise ValueError('Mouse627 missing actual path or transform: '+label)
 if any(abs(matrix[key]-1)>=.001 for key in ['a','d']) or any(abs(matrix[key])>=.001 for key in ['b','c','e']):raise ValueError('Mouse627 panel frame scales or rotates: '+label)
 if not -.1<=matrix['f']<=frame['height']+.1 or abs(matrix['f']/frame['height']-(1-frame['progress']))>=.02:raise ValueError('Mouse627 panel translation does not match its progress: '+label)

def verify_627_motion(facts):
 facts_version(facts,'Nora motion');true_fields(facts,MOTION_FACTS,'Nora motion')
 if facts.get('themes')!=['light','dark']:raise ValueError('Mouse627 Nora themes incomplete')
 groups=['lightOpening','lightClosing','darkOpening','darkClosing','interrupted','reduced']
 frames=facts.get('frames');geometry=facts.get('geometry');captures=facts.get('captures');capture_states=facts.get('captureStates')
 if not all(isinstance(value,dict) for value in [frames,geometry,captures,capture_states]) or set(frames)!=set(groups):raise ValueError('Mouse627 Nora frame groups incomplete')
 first_by_group={}
 for name in groups:
  rows=frames[name]
  if not isinstance(rows,list) or not rows:raise ValueError('Mouse627 Nora painted frames missing: '+name)
  for frame in rows:motion_frame(frame,name)
  if any(b['time']<a['time'] for a,b in zip(rows,rows[1:])):raise ValueError('Mouse627 Nora frame times are not ordered: '+name)
  visible=[row for row in rows if row['open'] and not row['hidden']]
  if not visible:raise ValueError('Mouse627 Nora has no visible frame: '+name)
  first=visible[0];first_by_group[name]=first
  for frame in visible:
   if any(frame[key]!=first[key] for key in ['width','height','left','baseline','paths','geometryWrites','font']) or frame['targetHeight']!=first['height'] or frame['opacity']!=1:raise ValueError('Mouse627 Nora geometry changes during translation: '+name)
  if max(row['measurements'] for row in visible)-min(row['measurements'] for row in visible)>2:raise ValueError('Mouse627 Nora measures geometry on animation frames: '+name)
  record=geometry.get(name)
  if not isinstance(record,dict) or not isinstance(record.get('initial'),dict) or not isinstance(record.get('sizes'),list) or not isinstance(record.get('mutations'),list):raise ValueError('Mouse627 Nora observer evidence missing: '+name)
  initial=record['initial'];panel=initial.get('panel')
  if not isinstance(panel,dict) or not finite(panel.get('height')) or panel['height']<=100 or abs(panel['height']-first['height'])>1:raise ValueError('Mouse627 Nora fixed viewport missing: '+name)
  for mutation in record['mutations']:
   if not isinstance(mutation,dict) or not finite(mutation.get('time')) or first['time']<mutation['time']<visible[-1]['time']:raise ValueError('Mouse627 Nora writes geometry during painted motion: '+name)
  for target in ['tray','panel','content','button']:
   size=initial.get(target)
   if not isinstance(size,dict) or not all(finite(size.get(key)) and size[key]>0 for key in ['width','height']):raise ValueError('Mouse627 Nora initial box missing: '+name+' '+target)
   observed=[row for row in record['sizes'] if isinstance(row,dict) and row.get('target')==target and finite(row.get('width')) and finite(row.get('height')) and row['width']>0 and row['height']>0]
   if any(abs(row[key]-observed[0][key])>=.05 for row in observed for key in ['width','height']):raise ValueError('Mouse627 Nora resizes an actual content box: '+name)
  if name.endswith(('Opening','Closing')):
   direction='opening' if name.endswith('Opening') else 'closing';moving=[row for row in rows if row.get('phase')==direction and 0<row['progress']<1]
   if len(moving)<3 or max(row['matrix']['f'] for row in moving)-min(row['matrix']['f'] for row in moving)<2:raise ValueError('Mouse627 Nora lacks distinct painted translations: '+name)
   if any(not row['open'] or row['hidden'] or not row['inert'] for row in moving):raise ValueError('Mouse627 Nora exposes controls during motion: '+name)
   if any((b['matrix']['f']-a['matrix']['f']>.75 if direction=='opening' else b['matrix']['f']-a['matrix']['f']<-.75) for a,b in zip(moving,moving[1:])):raise ValueError('Mouse627 Nora reverses unexpectedly: '+name)
  elif name=='reduced' and any(row['progress'] not in [0,1] for row in rows):raise ValueError('Mouse627 reduced motion contains intermediate frames')
  elif name=='interrupted' and not {'opening','closing'}.issubset({row.get('phase') for row in rows}):raise ValueError('Mouse627 Nora interruption was not painted')
 interruption=facts.get('interruption')
 if not isinstance(interruption,dict) or interruption.get('open') is not True or 'error' in interruption:raise ValueError('Mouse627 Nora interruption evidence incomplete')
 before=interruption.get('before');after=interruption.get('after');pair=interruption.get('closingFrames')
 motion_frame(before,'reversal before');motion_frame(after,'reversal after')
 if abs(before['progress']-after['progress'])>=.04 or abs(before['matrix']['f']-after['matrix']['f'])>=2 or before['paths']!=after['paths'] or before['height']!=after['height']:raise ValueError('Mouse627 Nora reversal jumps or changes its shape')
 if not isinstance(pair,list) or len(pair)!=2:raise ValueError('Mouse627 Nora reversal closing samples missing')
 for row in pair:motion_frame(row,'reversal closing')
 if any(row.get('phase')!='closing' or not row['open'] or row['hidden'] for row in pair) or pair[1]['time']<=pair[0]['time'] or not 0<pair[1]['progress']<pair[0]['progress'] or pair[1]['matrix']['f']-pair[0]['matrix']['f']<1:raise ValueError('Mouse627 Nora reversal did not follow actual closing motion')
 for theme in ['light','dark']:
  if captures.get(theme)!={phase:f'mouse-627-panel-{theme}-{phase}.png' for phase in ['opening','open','closing']}:raise ValueError('Mouse627 Nora capture filenames incomplete: '+theme)
  first=first_by_group[theme+'Opening']
  for phase in ['opening','open','closing']:
   state=capture_states.get(theme,{}).get(phase,{});sample=state.get('before')
   if phase=='open' or sample is not None:motion_frame(sample,theme+' '+phase+' capture')
   if phase=='open':
    if sample.get('phase')!='open' or not sample['open'] or sample['hidden'] or sample['progress']!=1:raise ValueError('Mouse627 Nora settled screenshot did not begin open: '+theme)
   else:
    if phase=='closing' and (sample is None or sample.get('phase')!='open' or not sample['open'] or sample['hidden'] or sample['progress']!=1):raise ValueError('Mouse627 Nora close capture does not record its open starting state')
    if phase=='opening' and sample is not None and (sample['open'] or not sample['hidden'] or sample['progress']!=0):raise ValueError('Mouse627 Nora open capture does not record its closed starting state')
    verify_panel_presentation(state.get('painted'),theme,phase,first,sample)
  controls=geometry.get(theme+'Controls')
  if not isinstance(controls,list) or len(controls)!=3 or any(not isinstance(row,dict) for row in controls) or {row.get('name') for row in controls}!={'preview','modes','history'}:raise ValueError('Mouse627 Nora control coverage incomplete: '+theme)
  for row in controls:
   if not all(finite(row.get(key)) for key in ['height','width','visibleHeight','scrollTop','scrollHeight','clientHeight']) or abs(row['height']-first['height'])>1 or abs(row['width']-first['width'])>1 or row['overflow']!='auto' or row.get('accessible') is not True or row['visibleHeight']<=0 or row['paths']!={key:first['paths'][key] for key in ['outline','fill']} or row.get('geometryWrites')!=first['geometryWrites']:raise ValueError('Mouse627 Nora controls do not stay accessible in a fixed viewport: '+theme)
  footer=facts.get('footer',{}).get(theme)
  if not isinstance(footer,dict) or not isinstance(footer.get('before'),dict) or footer.get('before')!=footer.get('after'):raise ValueError('Mouse627 Nora footer changes: '+theme)
  rectangle(footer['before'],'Nora footer '+theme)
  if not isinstance(footer['before'].get('pixels'),list) or len(footer['before']['pixels'])!=4:raise ValueError('Mouse627 Nora footer pixel samples missing: '+theme)
 background=facts.get('background')
 if not isinstance(background,dict) or type(background.get('nativeBoundsCalls')) is not int or background['nativeBoundsCalls']!=0 or type(background.get('resizeEvents')) is not int or background['resizeEvents']!=0:raise ValueError('Mouse627 Nora touches native page geometry')
 before=page_pins(background.get('before'),'Nora before','epoch',True);after=page_pins(background.get('after'),'Nora after','epoch',True)
 if before!=after:raise ValueError('Mouse627 Nora changes live background identity or viewport')
 snapshots=background.get('snapshots')
 if not isinstance(snapshots,list) or len(snapshots)!=2 or any(not isinstance(row,dict) for row in snapshots) or {row.get('theme') for row in snapshots}!={'light','dark'}:raise ValueError('Mouse627 Nora background surfaces incomplete')
 for row in snapshots:
  images=row.get('images')
  if not isinstance(images,list) or not images or any(not isinstance(image,dict) for image in images):raise ValueError('Mouse627 Nora background surface missing')
  ids=[image.get('id') for image in images]
  if any(not isinstance(id,str) or id not in before for id in ids) or len(set(ids))!=len(ids):raise ValueError('Mouse627 Nora background surface identity is invalid')
  if set(ids)!={id for id,page in before.items() if page['visible']}:raise ValueError('Mouse627 Nora does not paint every formerly visible native page')
  for image in images:
   rectangle(image.get('bounds'),'Nora surface')
   if image['bounds']!=before[image['id']]['surfaceBounds'] or image.get('complete') is not True or image.get('png') is not True or image.get('transform')!='none' or not all(finite(image.get('natural'+key.capitalize())) and image['natural'+key.capitalize()]>=image['bounds'][key]>0 for key in ['width','height']):raise ValueError('Mouse627 Nora background is not an unchanged full-resolution PNG')

def verify_627_desktop_transition(facts):
 facts_version(facts,'desktop transition');true_fields(facts,DESKTOP_TRANSITION_FACTS,'desktop transition')
 rows=facts.get('transitions')
 if not isinstance(rows,list) or len(rows)!=4 or any(not isinstance(row,dict) for row in rows) or {(row.get('theme'),row.get('direction')) for row in rows}!={(theme,direction) for theme in ['light','dark'] for direction in [-1,1]}:raise ValueError('Mouse627 desktop transition directions or themes incomplete')
 if sorted(row.get('ackDelayMs',-1) for row in rows)!=[0,0,0,250]:raise ValueError('Mouse627 desktop transition must include one delayed native acknowledgement')
 for row in rows:
  if type(row['direction']) is not int or type(row['ackDelayMs']) is not int or not whole(row.get('nativeLayoutCalls'),1) or row['nativeLayoutCalls']>8:raise ValueError('Mouse627 desktop transition performs unbounded native layouts')
  if not finite(row.get('animationDurationMs')) or not 0<row['animationDurationMs']<=660+row['ackDelayMs'] or not finite(row.get('totalDurationMs')) or row['totalDurationMs']<row['animationDurationMs']:raise ValueError('Mouse627 desktop transition stalls beyond its bounded animation interval')
  before=page_pins(row.get('pageBefore'),'desktop before','navigationEpoch');after=page_pins(row.get('pageAfter'),'desktop after','navigationEpoch')
  if len(before)!=2 or before!=after:raise ValueError('Mouse627 desktop transition changes either retained page identity, viewport or scroll')
  frames=row.get('frames')
  if not isinstance(frames,list) or len(frames)<3 or any(not isinstance(frame,dict) or not all(finite(frame.get(key)) for key in ['at','outgoingX','incomingX','width']) or frame['width']<=0 for frame in frames):raise ValueError('Mouse627 desktop transition lacks actual compositor frames')
  width=frames[0]['width']
  if any(frame['width']!=width or abs((frame['incomingX']-frame['outgoingX'])-row['direction']*width)>1.5 for frame in frames):raise ValueError('Mouse627 desktop surfaces are not adjacent equal-width layers')
  if any(b['at']<a['at'] for a,b in zip(frames,frames[1:])) or any(len({math.floor(frame[key]+.5) for frame in frames})<3 for key in ['outgoingX','incomingX']):raise ValueError('Mouse627 desktop surfaces do not both move')
  if any(abs((b['outgoingX']-a['outgoingX'])-(b['incomingX']-a['incomingX']))>2 for a,b in zip(frames,frames[1:])):raise ValueError('Mouse627 desktop surfaces do not move simultaneously')
  if row['direction']==1:verify_desktop_presentation(row.get('paintedFrame'),row['theme'])
  snapshots=row.get('snapshots');all_snapshots=row.get('allSnapshots');captures=row.get('captures')
  if not isinstance(snapshots,list) or len(snapshots)!=2 or any(not isinstance(image,dict) for image in snapshots) or {image.get('id') for image in snapshots}!=set(before) or {image.get('frame') for image in snapshots}!={'outgoing','incoming'}:raise ValueError('Mouse627 desktop PNG surface identities incomplete')
  if not isinstance(all_snapshots,list) or len(all_snapshots)<2 or any(not isinstance(image,dict) or not isinstance(image.get('id'),str) or not image['id'] or image.get('frame') not in ['outgoing','incoming'] for image in all_snapshots) or len({(image['frame'],image['id']) for image in all_snapshots})!=len(all_snapshots):raise ValueError('Mouse627 complete desktop surface set missing')
  if {(image['frame'],image['id']):image for image in snapshots}!={(image['frame'],image['id']):image for image in all_snapshots if image['id'] in before}:raise ValueError('Mouse627 tracked desktop snapshots differ from actual surfaces')
  for image in all_snapshots:
   if image.get('png') is not True or image.get('decoded') is not True or not all(finite(image.get(key)) and image[key]>0 for key in ['pixelWidth','pixelHeight','width','height']) or image['pixelWidth']<image['width']-1 or image['pixelHeight']<image['height']-1:raise ValueError('Mouse627 desktop PNG surface was not decoded at full size')
  if not isinstance(captures,list) or len(captures)!=2:raise ValueError('Mouse627 native desktop captures missing')
  captured=[]
  for index,capture in enumerate(captures):
   if not isinstance(capture,dict) or capture.get('prepared') is not bool(index) or capture.get('complete') is not True or not isinstance(capture.get('rows'),list) or len(capture['rows'])!=1:raise ValueError('Mouse627 native desktop capture order incomplete')
   ids=capture.get('ids');frame=['outgoing','incoming'][index]
   if not isinstance(ids,list) or not ids or any(not isinstance(id,str) or not id for id in ids) or len(set(ids))!=len(ids) or set(ids)!={image['id'] for image in all_snapshots if image['frame']==frame}:raise ValueError('Mouse627 desktop frame does not paint every actual captured native page')
   image=capture['rows'][0]
   if not isinstance(image,dict) or image.get('id') not in before or image['id'] not in ids:raise ValueError('Mouse627 native desktop capture identity missing')
   pin=before[image['id']];captured.append(image['id'])
   if image.get('epoch')!=pin['navigationEpoch'] or image.get('webContentsId')!=pin['webContentsId'] or any(image.get(key)!=pin[key] for key in ['width','height']) or not all(finite(image.get(key)) and image[key]>0 for key in ['pixelWidth','pixelHeight']) or image['pixelWidth']<pin['width']-1 or image['pixelHeight']<pin['height']-1:raise ValueError('Mouse627 native desktop capture does not match retained page')
   sample=image.get('sample')
   if not isinstance(sample,dict) or sample.get('domTag')!='BODY' or sample.get('background')!='rgb(240, 240, 240)' or not all(finite(sample.get(key)) for key in ['x','y','viewportWidth','viewportHeight']) or not 0<=sample['x']<sample['viewportWidth'] or not 0<=sample['y']<sample['viewportHeight']:raise ValueError('Mouse627 native PNG body probe missing')
   for axis,dimension in [('X','Width'),('Y','Height')]:
    value=sample.get('pixel'+axis);expected=min(image['pixel'+dimension]-1,math.floor(sample[axis.lower()]*image['pixel'+dimension]/sample['viewport'+dimension]))
    if not whole(value) or value!=expected:raise ValueError('Mouse627 native PNG body probe is mapped to the wrong pixel')
   rgba=sample.get('rgba')
   if not isinstance(rgba,list) or len(rgba)!=4 or not all(whole(channel) and 238<=channel<=242 for channel in rgba[:3]) or type(rgba[3]) is not int or rgba[3]!=255:raise ValueError('Mouse627 native PNG does not contain the measured exposed body colour')
  if set(captured)!=set(before):raise ValueError('Mouse627 desktop transition did not capture both retained pages')

def verify_627_evidence(read):
 validators=[verify_627_window,verify_627_documents,verify_627_pdf,verify_627_performance,verify_627_motion,verify_627_desktop_transition]
 assert len(JSON_FILES_627)==len(validators);facts={}
 for name,validator in zip(JSON_FILES_627,validators):facts[name]=json.loads(read(name));validator(facts[name])
 verify_623_retained(json.loads(read('mouse-623-verification.json')))
 for name in PNG_FILES_627:
  if not read(name).startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Mouse627 screenshot is not PNG: '+name)
 verify_presented_pixels(facts,read)

def verify_627_motion_trace(read,provenance):
 # Always recompute acceptance from the exact trace and motion bytes. A saved
 # report is an output only; it cannot authorize either import or publication.
 names=[TRACE_FILE_627,'mouse-627-motion.json'];documents={};inputs={}
 for name in names:
  blob=read(name);limit=TRACE_MAX_BYTES_627 if name==TRACE_FILE_627 else 16*1024**2
  if not isinstance(blob,bytes) or not 0<len(blob)<=limit:raise ValueError('Mouse627 trace input missing or oversized: '+name)
  documents[name]=json.loads(blob)
  inputs[name]={'size':len(blob),'sha256':hashlib.sha256(blob).hexdigest()}
 validator=runpy.run_path(str(pathlib.Path(__file__).with_name('mouse627-motion-trace.py')))
 report=validator['verify_trace_data'](documents[TRACE_FILE_627],documents['mouse-627-motion.json'])
 if not isinstance(report,dict) or report.get('status')!='pass' or report.get('algorithm')!='mouse627-motion-trace-evidence-v1' or report.get('directIdentityLink') is not False or report.get('attribution')!='temporal-correlation':raise ValueError('Mouse627 trace validator returned an invalid acceptance report')
 # Keep the limitation visible in the derived report. The sanitized trace has
 # no direct DOM-to-KeyframeModel identity link; ambiguous temporal evidence
 # is rejected by the validator, never promoted to an identity claim here.
 result={'version':'6.0.27','inputs':inputs,'provenance':dict(provenance),'evidence':report}
 json.dumps(result,allow_nan=False)
 return result

once(" if not required.issubset(set(b['tests']))", " if SUPERSEDED_FEATURE_TOKENS.intersection(b['tests']):raise ValueError('Mouse627 build still claims superseded Nora morph evidence')\n if not FEATURE_TOKENS_627.issubset(set(b['tests'])):raise ValueError('Mouse627 feature evidence incomplete')\n if not required.issubset(set(b['tests']))")
once(" matches=[a for a in artifacts if a['id']==ARTIFACT", """ with zipfile.ZipFile(io.BytesIO(verification_bytes)) as z:
  for name in EVIDENCE_FILES_627:
   entries=[item for item in z.infolist() if item.filename==name]
   if len(entries)!=1 or entries[0].is_dir() or entries[0].file_size>16*1024**2:raise ValueError('Mouse627 source evidence missing or oversized: '+name)
  verify_627_evidence(z.read)
  traces=[item for item in z.infolist() if item.filename==TRACE_FILE_627]
  if len(traces)!=1 or traces[0].is_dir() or (traces[0].external_attr>>16)&0o170000==0o120000 or not 0<traces[0].file_size<=TRACE_MAX_BYTES_627:raise ValueError('Mouse627 source motion trace missing, duplicated or oversized')
  source_trace_report=verify_627_motion_trace(z.read,{'stage':'source-import','source':HEAD,'sourceRun':RUN,'verificationArtifact':PIN['verificationArtifact'],'verificationSHA256':PIN['verificationSHA256']})
  if not all(marker in z.read('mouse-smoke-write.log').decode('utf-8') for marker in NATIVE_MARKERS_627):raise ValueError('Mouse627 source native markers missing')
 matches=[a for a in artifacts if a['id']==ARTIFACT""")
once(' for m in NATIVE_MARKERS_626+', ' for m in NATIVE_MARKERS_627+NATIVE_MARKERS_626+')
once(' for n in EVIDENCE_FILES_626+', ' for n in EVIDENCE_FILES_627+EVIDENCE_FILES_626+')
once(" print('MOUSE627_EXACT_SOURCE_BYTES_IMPORTED',flush=True)"," (OUT/SOURCE_TRACE_REPORT_627).write_text(json.dumps(source_trace_report,indent=2,allow_nan=False)+'\\n')\n print('MOUSE627_SOURCE_MOTION_TRACE_EVIDENCE_PASS',flush=True)\n print('MOUSE627_EXACT_SOURCE_BYTES_IMPORTED',flush=True)")
once(" found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]", """ verify_627_evidence(lambda name:(OUT/name).read_bytes())
 trace_report=verify_627_motion_trace(lambda name:(OUT/name).read_bytes(),{'stage':'installed-before-publication','source':HEAD,'sourceRun':RUN,'artifact':ARTIFACT,'archiveSHA256':ARCHIVE_HASH,'publisherRun':os.environ['GITHUB_RUN_ID'],'publisherRunAttempt':os.environ['GITHUB_RUN_ATTEMPT'],'publisherSHA':os.environ['GITHUB_SHA']})
 (OUT/TRACE_REPORT_627).write_text(json.dumps(trace_report,indent=2,allow_nan=False)+'\\n')
 print('MOUSE627_FRESH_INSTALLED_MOTION_TRACE_EVIDENCE_PASS',flush=True)
 found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]""")

builtins.compile(code,__file__,'exec')
for required in ["V='6.0.27'","PR=int(PIN['sourcePR'])","(419668574,HEAD,'completed','success')","pr.get('merged')","pr['head']['sha']!=HEAD","pr['base']['ref']!='main'","pr['merge_commit_sha']!=PIN['sourceMerge']","Source is not an ancestor of main","Artifact checksum mismatch","Native verification checksum mismatch","Wrong package bytes","Refusing to overwrite different existing bytes","Refusing channel downgrade","Same-version channel differs","legacy625-update.cjs","ref={previous['source']}","Previous625 immutable updater blob mismatch","Previous625 public package pin mismatch","Previous625 real replacement helper pin mismatch",new_marker,"MOUSE_625_DOCUMENTS_NATIVE_EDIT_SAVE_PRESERVE_PASS","MOUSE_625_SEARCH_ENGINE_NORMAL_PRIVATE_PASS","MOUSE_624_AGENT_SERVICE_LAYOUT_PERSIST_PASS","MOUSE_624_LAYOUT_UNDO_REDO_PERSIST_PASS","MOUSE_624_SCOPED_PROGRESS_PILL_PASS","MOUSE_627_BURROW_FIXED_VIEWPORT_CONTROLS_PASS","MOUSE_623_TAB_LIFECYCLE_CHIPS_STABILITY_PASS","facts623.get('version')!='6.0.23'","facts624.get('version')!='6.0.24'","facts625.get('version')!='6.0.25'","search625.get('version')!='6.0.25'","MOUSE_622_AGENT_CDP_PTY_WORKER_STOP_PASS","autonomousActions","MOUSE_PROFILE_COOKIE_RESTART_PASS","workerOffMainThread","FEATURE_TOKENS_626.issubset","FEATURE_TOKENS_627.issubset","verify_626_facts(json.loads(z.read('mouse-626-verification.json')))","verify_626_facts(json.loads((OUT/'mouse-626-verification.json').read_text()))","verify_627_evidence(z.read)","verify_627_evidence(lambda name:(OUT/name).read_bytes())"]:
 assert required in code,required
for required in ["source_trace_report=verify_627_motion_trace(z.read,", "trace_report=verify_627_motion_trace(lambda name:(OUT/name).read_bytes(),", "(OUT/SOURCE_TRACE_REPORT_627).write_text", "(OUT/TRACE_REPORT_627).write_text", "MOUSE627_SOURCE_MOTION_TRACE_EVIDENCE_PASS", "MOUSE627_FRESH_INSTALLED_MOTION_TRACE_EVIDENCE_PASS"]:
 assert required in code,required

def ready_pin():
 stage=pathlib.Path(__file__).resolve().parents[1]/'staging/mouse/6.0.27-arm64'
 pin=json.loads((stage/'pin.json').read_text())
 if pin.get('version')!='6.0.27':raise ValueError('Wrong Mouse627 pin version')
 if pin.get('ready') is not True:raise ValueError('Mouse627 pin not final: ready')
 for key in ['source','sourceMerge']:
  if not isinstance(pin.get(key),str) or not re.fullmatch('[a-f0-9]{40}',pin[key]):raise ValueError('Mouse627 pin not final: '+key)
 for key in ['archiveSHA256','verificationSHA256']:
  if not isinstance(pin.get(key),str) or not re.fullmatch('[a-f0-9]{64}',pin[key]):raise ValueError('Mouse627 pin not final: '+key)
 for key in ['run','artifact','verificationArtifact','sourcePR']:
  if type(pin.get(key)) is not int or pin[key]<=0:raise ValueError('Mouse627 pin not final: '+key)
 names={'Mouse-Browser-6.0.27-mac-arm64.dmg','Mouse-Browser-6.0.27-mac-arm64.zip'}
 if set(pin.get('packages',{}))!=names:raise ValueError('Mouse627 package pin incomplete')
 for package in pin['packages'].values():
  if not isinstance(package,dict) or type(package.get('size')) is not int or package['size']<=0 or not isinstance(package.get('sha256'),str) or not re.fullmatch('[a-f0-9]{64}',package['sha256']):raise ValueError('Mouse627 package bytes not pinned')
 expected_previous={'version':'6.0.25','source':'d70dd1e1a9255709b4816b616dd7860581e882bd','updaterBlobSHA':'c4a9564bc5a7c3cf2c6798b5eade9680ee0e57cf','package':{'name':'Mouse-Browser-6.0.25-mac-arm64.dmg','size':133809131,'sha256':'0367c7b07d2b2d1f34345b2f8696ae71d5459522db2bfa9a3a045e67b82bf74f'}}
 if pin.get('previous')!=expected_previous:raise ValueError('Mouse627 previous625 immutable release pin mismatch')
 owner=(stage/'PUBLISH_OWNER').read_text()
 if 'UNSET' in owner or 'READY_TO_PUBLISH_MOUSE_627' not in owner:raise ValueError('Mouse627 native publication evidence is not final')
 if 'UNSET' in (stage/'RELEASE_NOTES.md').read_text():raise ValueError('Mouse627 release notes still contain a template placeholder')
 return pin

if sys.argv[1:]==['validate-template']:
 print('MOUSE627_REVIEWED_PUBLISHER_TEMPLATE_GATES_PASS')
elif sys.argv[1:]==['validate']:
 ready_pin();print('MOUSE627_REVIEWED_PUBLISHER_GATES_PASS')
elif len(sys.argv)==2 and sys.argv[1] in ['import','publish','channel']:
 ready_pin();builtins.exec(builtins.compile(code,__file__,'exec'),globals())
else:raise SystemExit('Usage: mouse627-release.py validate-template|validate|import|publish|channel')
