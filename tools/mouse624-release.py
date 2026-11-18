#!/usr/bin/env python3
"""Publish the exact native-tested624 candidate; pending pins cannot execute API actions."""
import builtins,hashlib,json,pathlib,re,sys
base=pathlib.Path(__file__).with_name('mouse623-release.py')
source=base.read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='84dc4260c3540d84486f8730c284fbd31f48f0a6','Reviewed623 publisher changed'
wrapper=source.decode('utf-8')
dispatch="\nif sys.argv[1:]==['validate-template']:"
assert wrapper.count(dispatch)==1
wrapper=wrapper.split(dispatch,1)[0]+'\n_emit(code)\n'
output=[]
scope={'__file__':str(base),'__name__':'reviewed_source_transform','_emit':output.append}
builtins.exec(builtins.compile(wrapper,str(base),'exec'),scope)
assert len(output)==1,'Ambiguous reviewed623 transform'
code=output[0].replace('6.0.23','6.0.24').replace('mouse623-release','mouse624-release').replace('MOUSE623_','MOUSE624_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once('real-622-to-623-profile-preserving-install','real-623-to-624-profile-preserving-install')
once('MOUSE_623_REAL_622_TO_623_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_624_REAL_623_TO_624_REPLACE_RELAUNCH_PROFILE_PASS')
once('a94317ce121de73a9a469b55af8eea900a35921d','f3019ed8efae25aac9bad5e3b006ed6b4a9d3954')
once('legacy622-update.cjs','legacy623-update.cjs')
once('# Actual released6.0.22 updater from its immutable tested source.','# Actual released6.0.23 updater from its immutable tested source.')
once('Mouse Browser 6.0.24 — форма норки и вкладки','Mouse Browser 6.0.24 — сетка, история и прогресс')
# Historical feature evidence keeps its original schema/version; new624 facts are separate.
once("facts623.get('version')!=V", "facts623.get('version')!='6.0.23'")
once("for m in ['MOUSE_623_BURROW_GEOMETRY_AND_SEAM_PASS'", "for m in ['MOUSE_624_AGENT_SERVICE_LAYOUT_PERSIST_PASS','MOUSE_624_LAYOUT_UNDO_REDO_PERSIST_PASS','MOUSE_624_SCOPED_PROGRESS_PILL_PASS','MOUSE_623_BURROW_GEOMETRY_AND_SEAM_PASS'")
once("for n in ['mouse-623-compact-light.png'", "for n in ['mouse-624-verification.json','mouse-624-agent-preserved.png','mouse-624-layout-history.png','mouse-624-progress-known.png','mouse-624-progress-unknown.png','mouse-623-compact-light.png'")
once(" if not required.issubset(set(b['tests']))", " if not {'agent-service-layout-preserved-return-reload','layout-history-native-undo-redo-persist','scoped-progress-determinate-indeterminate-stop','burrow-seam-one-pixel-join'}.issubset(set(b['tests'])):raise ValueError('Mouse624 feature evidence incomplete')\n if not required.issubset(set(b['tests']))")
once(" found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]", """ facts624=json.loads((OUT/'mouse-624-verification.json').read_text())
 if facts624.get('version')!=V:raise ValueError('Mouse624 native evidence version mismatch')
 for group,keys in [('agent',['layoutExact','pagesPreserved','aiReturn','reloadExact','defaultDisabled']),('history',['undo','redo','persisted','pagesPreserved','entryRestore']),('progress',['determinate','indeterminate','completionDismissed','stopped','pageScope'])]:
  if not all(facts624.get(group,{}).get(k) is True for k in keys):raise ValueError('Mouse624 native evidence incomplete: '+group)
 found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]""")
builtins.compile(code,__file__,'exec')
for required in ["V='6.0.24'","PR=int(PIN['sourcePR'])","(419668574,HEAD,'completed','success')","pr.get('merged')","pr['head']['sha']!=HEAD","pr['base']['ref']!='main'","pr['merge_commit_sha']!=PIN['sourceMerge']","Source is not an ancestor of main","Artifact checksum mismatch","Native verification checksum mismatch","Wrong package bytes","Refusing to overwrite different existing bytes","Refusing channel downgrade","Same-version channel differs","legacy623-update.cjs","ref=f3019ed8efae25aac9bad5e3b006ed6b4a9d3954","MOUSE_624_REAL_623_TO_624_REPLACE_RELAUNCH_PROFILE_PASS","MOUSE_624_AGENT_SERVICE_LAYOUT_PERSIST_PASS","MOUSE_624_LAYOUT_UNDO_REDO_PERSIST_PASS","MOUSE_624_SCOPED_PROGRESS_PILL_PASS","MOUSE_623_BURROW_GEOMETRY_AND_SEAM_PASS","MOUSE_623_TAB_LIFECYCLE_CHIPS_STABILITY_PASS","facts623.get('version')!='6.0.23'","mouse-623-verification.json","mouse-622-verification.json","MOUSE_622_AGENT_CDP_PTY_WORKER_STOP_PASS","autonomousActions","MOUSE_PROFILE_COOKIE_RESTART_PASS","mouse-624-verification.json"]:
 assert required in code,required

def ready_pin():
 stage=pathlib.Path(__file__).resolve().parents[1]/'staging/mouse/6.0.24-arm64'
 pin=json.loads((stage/'pin.json').read_text())
 if pin.get('version')!='6.0.24':raise ValueError('Wrong Mouse624 pin version')
 for key in ['source','sourceMerge']:
  if not isinstance(pin.get(key),str) or not re.fullmatch('[a-f0-9]{40}',pin[key]):raise ValueError('Mouse624 pin not final: '+key)
 for key in ['archiveSHA256','verificationSHA256']:
  if not isinstance(pin.get(key),str) or not re.fullmatch('[a-f0-9]{64}',pin[key]):raise ValueError('Mouse624 pin not final: '+key)
 for key in ['run','artifact','verificationArtifact','sourcePR']:
  if type(pin.get(key)) is not int or pin[key]<=0:raise ValueError('Mouse624 pin not final: '+key)
 names={'Mouse-Browser-6.0.24-mac-arm64.dmg','Mouse-Browser-6.0.24-mac-arm64.zip'}
 if set(pin.get('packages',{}))!=names:raise ValueError('Mouse624 package pin incomplete')
 for package in pin['packages'].values():
  if type(package.get('size')) is not int or package['size']<=0 or not isinstance(package.get('sha256'),str) or not re.fullmatch('[a-f0-9]{64}',package['sha256']):raise ValueError('Mouse624 package bytes not pinned')
 owner=(stage/'PUBLISH_OWNER').read_text()
 if 'UNSET' in owner or 'READY_TO_PUBLISH_MOUSE_624' not in owner:raise ValueError('Mouse624 native publication evidence is not final')
 if 'UNSET' in (stage/'RELEASE_NOTES.md').read_text():raise ValueError('Mouse624 release notes still contain a template placeholder')
 return pin

if sys.argv[1:]==['validate-template']:
 print('MOUSE624_REVIEWED_PUBLISHER_TEMPLATE_GATES_PASS')
elif sys.argv[1:]==['validate']:
 ready_pin();print('MOUSE624_REVIEWED_PUBLISHER_GATES_PASS')
elif len(sys.argv)==2 and sys.argv[1] in ['import','publish','channel']:
 ready_pin();builtins.exec(builtins.compile(code,__file__,'exec'),globals())
else:raise SystemExit('Usage: mouse624-release.py validate-template|validate|import|publish|channel')
