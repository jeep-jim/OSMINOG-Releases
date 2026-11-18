#!/usr/bin/env python3
"""Publish exact native-tested625 bytes; pending pins fail before API actions."""
import builtins,hashlib,json,pathlib,re,sys

base=pathlib.Path(__file__).with_name('mouse624-release.py')
source=base.read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='6cd3275692d3ee3156fef8a80f71c84c128c8bb5','Reviewed624 publisher changed'
wrapper=source.decode('utf-8')
dispatch="\nif sys.argv[1:]==['validate-template']:"
assert wrapper.count(dispatch)==1
wrapper=wrapper.split(dispatch,1)[0]+'\n_emit(code)\n'
output=[]
scope={'__file__':str(base),'__name__':'reviewed_source_transform','_emit':output.append}
builtins.exec(builtins.compile(wrapper,str(base),'exec'),scope)
assert len(output)==1,'Ambiguous reviewed624 transform'
code=output[0].replace('6.0.24','6.0.25').replace('mouse624-release','mouse625-release').replace('MOUSE624_','MOUSE625_')

def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)

once('real-623-to-624-profile-preserving-install','real-623-to-625-profile-preserving-install')
once('MOUSE_624_REAL_623_TO_624_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_625_REAL_623_TO_625_REPLACE_RELAUNCH_PROFILE_PASS')
once('# Actual released6.0.23 updater from its immutable tested source.','# Actual released6.0.23 updater from its separately pinned immutable tested source.')
once(" old=api(SOURCE,'contents/desktop/mouse-update.cjs?ref=f3019ed8efae25aac9bad5e3b006ed6b4a9d3954')\n (OUT/'legacy623-update.cjs').write_bytes(base64.b64decode(old['content']))", """ previous=PIN['previous'];package=previous['package']
 released=api(REPO,'releases/tags/quadro-macos-v6.0.23-arm64')
 if released.get('draft') or not released.get('published_at'):raise ValueError('Previous623 release is not public')
 old_assets=[a for a in released.get('assets',[]) if a.get('name')==package['name']]
 if len(old_assets)!=1 or old_assets[0].get('state')!='uploaded' or old_assets[0].get('size')!=package['size'] or old_assets[0].get('digest')!='sha256:'+package['sha256']:raise ValueError('Previous623 public package pin mismatch')
 old=api(SOURCE,f"contents/desktop/mouse-update.cjs?ref={previous['source']}")
 old_bytes=base64.b64decode(old['content'])
 old_blob=hashlib.sha1(b'blob '+str(len(old_bytes)).encode()+b'\\0'+old_bytes).hexdigest()
 if old.get('sha')!=previous['updaterBlobSHA'] or old_blob!=previous['updaterBlobSHA']:raise ValueError('Previous623 immutable updater blob mismatch')
 (OUT/'legacy623-update.cjs').write_bytes(old_bytes)
 # The reviewed, exact-source helper performs the one real public623 DMG
 # download and checksum verification before installed replacement testing.
 # Do not substitute a new download, synthetic fixture, or a different old DMG.
 upgrade=(OUT/'mouse-update-verify.py').read_text()
 for expected in [package['name'],str(package['size']),package['sha256'],"version(target)=='6.0.23'",'MOUSE_625_REAL_623_TO_625_REPLACE_RELAUNCH_PROFILE_PASS']:
  if expected not in upgrade:raise ValueError('Previous623 real replacement helper pin mismatch: '+expected)
""")
once('Mouse Browser 6.0.25 — сетка, история и прогресс','Mouse Browser 6.0.25 — документы и выбор поиска')

# Retained fixtures keep their own schema version. The625 document facts are
# additional evidence; they cannot replace any623/624 or earlier evidence.
once("facts624.get('version')!=V", "facts624.get('version')!='6.0.24'")
once("for m in ['MOUSE_624_AGENT_SERVICE_LAYOUT_PERSIST_PASS'", "for m in ['MOUSE_625_SEARCH_ENGINE_NORMAL_PRIVATE_PASS','MOUSE_625_DOCUMENTS_NATIVE_EDIT_SAVE_PRESERVE_PASS','MOUSE_624_AGENT_SERVICE_LAYOUT_PERSIST_PASS'")
once("for n in ['mouse-624-verification.json'", "for n in ['mouse-625-search-verification.json','mouse-625-search-normal.png','mouse-625-search-private.png','mouse-625-documents.json','mouse-625-pdf.png','mouse-625-docx.png','mouse-625-xlsx.png','mouse-624-verification.json'")
once(" if not required.issubset(set(b['tests']))", " if not {'local-pdf-docx-xlsx-edit-save','document-original-parts-preserved','document-unsaved-conflict-private-guards','document-editor-preserves-browser-grid','bounded-document-rendering','search-engine-choice','private-search-preference'}.issubset(set(b['tests'])):raise ValueError('Mouse625 feature evidence incomplete')\n if not required.issubset(set(b['tests']))")
once(" found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]", """ facts625=json.loads((OUT/'mouse-625-documents.json').read_text())
 if facts625.get('version')!=V:raise ValueError('Mouse625 native evidence version mismatch')
 for group,keys in [('pdf',['opened','annotated','reopened','originalPreserved','rotated','workerOffMainThread']),('docx',['edited','reopened','unmodifiedPartsPreserved','bold','tablePreserved','headerPreserved']),('xlsx',['edited','formulaPreserved','reopened','unmodifiedPartsPreserved','inlineStringPreserved']),('safeguards',['saveAs','originalUnchanged','dirtyCancel','conflictRejected','privateCleared','dirtySave']),('browser',['gridPreserved','pageIdentityPreserved'])]:
  if not isinstance(facts625.get(group),dict) or not all(facts625[group].get(k) is True for k in keys):raise ValueError('Mouse625 native evidence incomplete: '+group)
 search625=json.loads((OUT/'mouse-625-search-verification.json').read_text())
 if not isinstance(search625,dict) or search625.get('version')!=V:raise ValueError('Mouse625 native search evidence version mismatch')
 if search625.get('stateRestored') is not True:raise ValueError('Mouse625 native search fixture did not restore state')
 if not isinstance(search625.get('search'),dict) or not all(search625['search'].get(k) is True for k in ['cleanGoogleDefault','pickerKeyboardSelection','addressAndHomeMatch','normalPersistsReload','privateRAMOnly','noExternalSearchNavigation']):raise ValueError('Mouse625 native search evidence incomplete')
 found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]""")

builtins.compile(code,__file__,'exec')
for required in ["V='6.0.25'","PR=int(PIN['sourcePR'])","(419668574,HEAD,'completed','success')","pr.get('merged')","pr['head']['sha']!=HEAD","pr['base']['ref']!='main'","pr['merge_commit_sha']!=PIN['sourceMerge']","Source is not an ancestor of main","Artifact checksum mismatch","Native verification checksum mismatch","Wrong package bytes","Refusing to overwrite different existing bytes","Refusing channel downgrade","Same-version channel differs","legacy623-update.cjs","ref={previous['source']}","Previous623 immutable updater blob mismatch","Previous623 public package pin mismatch","Previous623 real replacement helper pin mismatch","MOUSE_625_REAL_623_TO_625_REPLACE_RELAUNCH_PROFILE_PASS","MOUSE_625_DOCUMENTS_NATIVE_EDIT_SAVE_PRESERVE_PASS","MOUSE_624_AGENT_SERVICE_LAYOUT_PERSIST_PASS","MOUSE_624_LAYOUT_UNDO_REDO_PERSIST_PASS","MOUSE_624_SCOPED_PROGRESS_PILL_PASS","MOUSE_623_BURROW_GEOMETRY_AND_SEAM_PASS","MOUSE_623_TAB_LIFECYCLE_CHIPS_STABILITY_PASS","facts623.get('version')!='6.0.23'","facts624.get('version')!='6.0.24'","mouse-623-verification.json","mouse-624-verification.json","mouse-622-verification.json","MOUSE_622_AGENT_CDP_PTY_WORKER_STOP_PASS","autonomousActions","MOUSE_PROFILE_COOKIE_RESTART_PASS","mouse-625-documents.json","mouse-625-pdf.png","mouse-625-docx.png","mouse-625-xlsx.png","inlineStringPreserved","dirtySave"]:
 assert required in code,required
for required in ['MOUSE_625_SEARCH_ENGINE_NORMAL_PRIVATE_PASS','mouse-625-search-verification.json','mouse-625-search-normal.png','mouse-625-search-private.png','search-engine-choice','private-search-preference','cleanGoogleDefault','pickerKeyboardSelection','addressAndHomeMatch','normalPersistsReload','privateRAMOnly','noExternalSearchNavigation',"search625.get('stateRestored') is not True",'workerOffMainThread']:
 assert required in code,required

def ready_pin():
 stage=pathlib.Path(__file__).resolve().parents[1]/'staging/mouse/6.0.25-arm64'
 pin=json.loads((stage/'pin.json').read_text())
 if pin.get('version')!='6.0.25':raise ValueError('Wrong Mouse625 pin version')
 if pin.get('ready') is not True:raise ValueError('Mouse625 pin not final: ready')
 for key in ['source','sourceMerge']:
  if not isinstance(pin.get(key),str) or not re.fullmatch('[a-f0-9]{40}',pin[key]):raise ValueError('Mouse625 pin not final: '+key)
 for key in ['archiveSHA256','verificationSHA256']:
  if not isinstance(pin.get(key),str) or not re.fullmatch('[a-f0-9]{64}',pin[key]):raise ValueError('Mouse625 pin not final: '+key)
 for key in ['run','artifact','verificationArtifact','sourcePR']:
  if type(pin.get(key)) is not int or pin[key]<=0:raise ValueError('Mouse625 pin not final: '+key)
 names={'Mouse-Browser-6.0.25-mac-arm64.dmg','Mouse-Browser-6.0.25-mac-arm64.zip'}
 if set(pin.get('packages',{}))!=names:raise ValueError('Mouse625 package pin incomplete')
 for package in pin['packages'].values():
  if not isinstance(package,dict) or type(package.get('size')) is not int or package['size']<=0 or not isinstance(package.get('sha256'),str) or not re.fullmatch('[a-f0-9]{64}',package['sha256']):raise ValueError('Mouse625 package bytes not pinned')
 previous=pin.get('previous')
 if not isinstance(previous,dict) or previous.get('version')!='6.0.23':raise ValueError('Mouse625 previous release pin incomplete')
 for key in ['source','updaterBlobSHA']:
  if not isinstance(previous.get(key),str) or not re.fullmatch('[a-f0-9]{40}',previous[key]):raise ValueError('Mouse625 previous623 pin not final: '+key)
 package=previous.get('package')
 if not isinstance(package,dict) or package.get('name')!='Mouse-Browser-6.0.23-mac-arm64.dmg' or type(package.get('size')) is not int or package['size']<=0 or not isinstance(package.get('sha256'),str) or not re.fullmatch('[a-f0-9]{64}',package['sha256']):raise ValueError('Mouse625 previous623 package bytes not pinned')
 owner=(stage/'PUBLISH_OWNER').read_text()
 if 'UNSET' in owner or 'READY_TO_PUBLISH_MOUSE_625' not in owner:raise ValueError('Mouse625 native publication evidence is not final')
 if 'UNSET' in (stage/'RELEASE_NOTES.md').read_text():raise ValueError('Mouse625 release notes still contain a template placeholder')
 return pin

if sys.argv[1:]==['validate-template']:
 print('MOUSE625_REVIEWED_PUBLISHER_TEMPLATE_GATES_PASS')
elif sys.argv[1:]==['validate']:
 ready_pin();print('MOUSE625_REVIEWED_PUBLISHER_GATES_PASS')
elif len(sys.argv)==2 and sys.argv[1] in ['import','publish','channel']:
 ready_pin();builtins.exec(builtins.compile(code,__file__,'exec'),globals())
else:raise SystemExit('Usage: mouse625-release.py validate-template|validate|import|publish|channel')
