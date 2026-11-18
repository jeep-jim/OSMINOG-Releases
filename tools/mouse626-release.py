#!/usr/bin/env python3
"""Publish exact native-tested626 bytes; retain all reviewed625 release gates."""
import builtins,hashlib,json,pathlib,re,sys

# Extract the reviewed implementation without executing ready_pin or any API.
# The complete607→625 dependency chain remains byte-for-byte unchanged.
base=pathlib.Path(__file__).with_name('mouse625-release.py')
source=base.read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='9c661592ca6bd29ae042da0097f88751d932dbbd','Reviewed625 publisher changed'
wrapper=source.decode('utf-8')
dispatch='\ndef ready_pin():'
assert wrapper.count(dispatch)==1
wrapper=wrapper.split(dispatch,1)[0]+'\n_emit(code)\n'
output=[]
scope={'__file__':str(base),'__name__':'reviewed_source_transform','_emit':output.append}
builtins.exec(builtins.compile(wrapper,str(base),'exec'),scope)
assert len(output)==1,'Ambiguous reviewed625 transform'
code=output[0].replace('6.0.25','6.0.26').replace('mouse625-release','mouse626-release').replace('MOUSE625_','MOUSE626_')

def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)

once('real-623-to-625-profile-preserving-install','real-625-to-626-profile-preserving-install')
old_marker='MOUSE_625_REAL_623_TO_625_REPLACE_RELAUNCH_PROFILE_PASS'
new_marker='MOUSE_626_REAL_625_TO_626_REPLACE_RELAUNCH_PROFILE_PASS'
assert code.count(old_marker)==2
code=code.replace(old_marker,new_marker)
once('legacy623-update.cjs','legacy625-update.cjs')
once("released=api(REPO,'releases/tags/quadro-macos-v6.0.23-arm64')", "released=api(REPO,'releases/tags/quadro-macos-v6.0.25-arm64')")
once("version(target)=='6.0.23'", "version(target)=='6.0.25'")
code=code.replace('Previous623','Previous625').replace('released6.0.23 updater','released6.0.25 updater').replace('real public623 DMG','real public625 DMG')
once('Mouse Browser 6.0.26 — документы и выбор поиска','Mouse Browser 6.0.26 — Нора и полная палитра')

# Historical feature JSONs keep their own schema versions.626 adds evidence;
# it never relabels625/624/623 outcomes or removes their behavioural assertions.
once("facts625.get('version')!=V", "facts625.get('version')!='6.0.25'")
once("search625.get('version')!=V", "search625.get('version')!='6.0.25'")

FEATURE_TOKENS={
 'burrow-liquid-footer-continuous-morph',
 'burrow-symmetric-layout',
 'burrow-reversible-reduced-motion',
 'capture-arbitrary-color-hex-rgb',
 'capture-arbitrary-color-export',
}
NATIVE_MARKERS=['MOUSE_626_BURROW_LIQUID_SYMMETRY_PASS','MOUSE_626_CAPTURE_ANY_COLOR_PASS']
EVIDENCE_FILES=['mouse-626-verification.json','mouse-626-burrow-light.png','mouse-626-burrow-dark.png','mouse-626-palette.png']
FACT_GROUPS={
 'nora':['symmetric','footerConnected','continuousOpen','continuousClose','interruptedMotion','resizeContinuous','reducedMotion','contentRevealed','controlsWork'],
 'palette':['arbitraryHex','arbitraryRGB','fieldSelection','annotationApplied','exportPreserved'],
}

def verify_626_facts(facts):
 if not isinstance(facts,dict) or facts.get('version')!='6.0.26':raise ValueError('Mouse626 native evidence version mismatch')
 if facts.get('themes')!=['light','dark']:raise ValueError('Mouse626 native themes incomplete')
 if facts.get('stateRestored') is not True:raise ValueError('Mouse626 native fixture did not restore state')
 for group,keys in FACT_GROUPS.items():
  if not isinstance(facts.get(group),dict) or not all(facts[group].get(k) is True for k in keys):raise ValueError('Mouse626 native evidence incomplete: '+group)

once(" if not required.issubset(set(b['tests']))", " if not FEATURE_TOKENS.issubset(set(b['tests'])):raise ValueError('Mouse626 feature evidence incomplete')\n if not required.issubset(set(b['tests']))")
once(" matches=[a for a in artifacts if a['id']==ARTIFACT", """ # Inspect new evidence in the exact source verification archive as well as
 # the fresh installed rerun below. A matching archive hash alone is not a
 # substitute for the required native interaction facts and rendered frames.
 with zipfile.ZipFile(io.BytesIO(verification_bytes)) as z:
  for name in EVIDENCE_FILES+['mouse-smoke-write.log','mouse-update-roundtrip.log']:
   items=[i for i in z.infolist() if i.filename==name]
   if len(items)!=1 or items[0].is_dir() or items[0].file_size>16*1024**2:raise ValueError('Mouse626 source evidence missing or oversized: '+name)
  verify_626_facts(json.loads(z.read('mouse-626-verification.json')))
  source_smoke=z.read('mouse-smoke-write.log').decode('utf-8')
  if not all(m in source_smoke for m in NATIVE_MARKERS):raise ValueError('Mouse626 source native markers missing')
  if 'MOUSE_626_REAL_625_TO_626_REPLACE_RELAUNCH_PROFILE_PASS' not in z.read('mouse-update-roundtrip.log').decode('utf-8'):raise ValueError('Mouse626 source real625 replacement missing')
  for name in EVIDENCE_FILES[1:]:
   if not z.read(name).startswith(b'\\x89PNG\\r\\n\\x1a\\n'):raise ValueError('Mouse626 source screenshot is not PNG: '+name)
 matches=[a for a in artifacts if a['id']==ARTIFACT""")
once(" for m in ['MOUSE_625_SEARCH_ENGINE_NORMAL_PRIVATE_PASS'", " for m in NATIVE_MARKERS+['MOUSE_625_SEARCH_ENGINE_NORMAL_PRIVATE_PASS'")
once(" for n in ['mouse-625-search-verification.json'", " for n in EVIDENCE_FILES+['mouse-625-search-verification.json'")
once(" found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]", """ verify_626_facts(json.loads((OUT/'mouse-626-verification.json').read_text()))
 for name in EVIDENCE_FILES[1:]:
  if not (OUT/name).read_bytes().startswith(b'\\x89PNG\\r\\n\\x1a\\n'):raise ValueError('Mouse626 installed screenshot is not PNG: '+name)
 found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]""")

builtins.compile(code,__file__,'exec')
for required in ["V='6.0.26'","PR=int(PIN['sourcePR'])","(419668574,HEAD,'completed','success')","pr.get('merged')","pr['head']['sha']!=HEAD","pr['base']['ref']!='main'","pr['merge_commit_sha']!=PIN['sourceMerge']","Source is not an ancestor of main","Artifact checksum mismatch","Native verification checksum mismatch","Wrong package bytes","Refusing to overwrite different existing bytes","Refusing channel downgrade","Same-version channel differs","legacy625-update.cjs","ref={previous['source']}","Previous625 immutable updater blob mismatch","Previous625 public package pin mismatch","Previous625 real replacement helper pin mismatch",new_marker,"MOUSE_625_DOCUMENTS_NATIVE_EDIT_SAVE_PRESERVE_PASS","MOUSE_625_SEARCH_ENGINE_NORMAL_PRIVATE_PASS","MOUSE_624_AGENT_SERVICE_LAYOUT_PERSIST_PASS","MOUSE_624_LAYOUT_UNDO_REDO_PERSIST_PASS","MOUSE_624_SCOPED_PROGRESS_PILL_PASS","MOUSE_623_BURROW_GEOMETRY_AND_SEAM_PASS","MOUSE_623_TAB_LIFECYCLE_CHIPS_STABILITY_PASS","facts623.get('version')!='6.0.23'","facts624.get('version')!='6.0.24'","facts625.get('version')!='6.0.25'","search625.get('version')!='6.0.25'","MOUSE_622_AGENT_CDP_PTY_WORKER_STOP_PASS","autonomousActions","MOUSE_PROFILE_COOKIE_RESTART_PASS","workerOffMainThread","FEATURE_TOKENS.issubset","verify_626_facts(json.loads(z.read('mouse-626-verification.json')))","verify_626_facts(json.loads((OUT/'mouse-626-verification.json').read_text()))"]:
 assert required in code,required

def ready_pin():
 stage=pathlib.Path(__file__).resolve().parents[1]/'staging/mouse/6.0.26-arm64'
 pin=json.loads((stage/'pin.json').read_text())
 if pin.get('version')!='6.0.26':raise ValueError('Wrong Mouse626 pin version')
 if pin.get('ready') is not True:raise ValueError('Mouse626 pin not final: ready')
 for key in ['source','sourceMerge']:
  if not isinstance(pin.get(key),str) or not re.fullmatch('[a-f0-9]{40}',pin[key]):raise ValueError('Mouse626 pin not final: '+key)
 for key in ['archiveSHA256','verificationSHA256']:
  if not isinstance(pin.get(key),str) or not re.fullmatch('[a-f0-9]{64}',pin[key]):raise ValueError('Mouse626 pin not final: '+key)
 for key in ['run','artifact','verificationArtifact','sourcePR']:
  if type(pin.get(key)) is not int or pin[key]<=0:raise ValueError('Mouse626 pin not final: '+key)
 names={'Mouse-Browser-6.0.26-mac-arm64.dmg','Mouse-Browser-6.0.26-mac-arm64.zip'}
 if set(pin.get('packages',{}))!=names:raise ValueError('Mouse626 package pin incomplete')
 for package in pin['packages'].values():
  if not isinstance(package,dict) or type(package.get('size')) is not int or package['size']<=0 or not isinstance(package.get('sha256'),str) or not re.fullmatch('[a-f0-9]{64}',package['sha256']):raise ValueError('Mouse626 package bytes not pinned')
 previous=pin.get('previous')
 expected_previous={'version':'6.0.25','source':'d70dd1e1a9255709b4816b616dd7860581e882bd','updaterBlobSHA':'c4a9564bc5a7c3cf2c6798b5eade9680ee0e57cf','package':{'name':'Mouse-Browser-6.0.25-mac-arm64.dmg','size':133809131,'sha256':'0367c7b07d2b2d1f34345b2f8696ae71d5459522db2bfa9a3a045e67b82bf74f'}}
 if previous!=expected_previous:raise ValueError('Mouse626 previous625 immutable release pin mismatch')
 owner=(stage/'PUBLISH_OWNER').read_text()
 if 'UNSET' in owner or 'READY_TO_PUBLISH_MOUSE_626' not in owner:raise ValueError('Mouse626 native publication evidence is not final')
 if 'UNSET' in (stage/'RELEASE_NOTES.md').read_text():raise ValueError('Mouse626 release notes still contain a template placeholder')
 return pin

if sys.argv[1:]==['validate-template']:
 print('MOUSE626_REVIEWED_PUBLISHER_TEMPLATE_GATES_PASS')
elif sys.argv[1:]==['validate']:
 ready_pin();print('MOUSE626_REVIEWED_PUBLISHER_GATES_PASS')
elif len(sys.argv)==2 and sys.argv[1] in ['import','publish','channel']:
 ready_pin();builtins.exec(builtins.compile(code,__file__,'exec'),globals())
else:raise SystemExit('Usage: mouse626-release.py validate-template|validate|import|publish|channel')
