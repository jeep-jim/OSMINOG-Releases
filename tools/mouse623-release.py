#!/usr/bin/env python3
"""Publish exact native-tested623 bytes; unset templates fail before any API action."""
import builtins,hashlib,json,pathlib,re,sys
base=pathlib.Path(__file__).with_name('mouse622-release.py')
source=base.read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='4dd99f9004e276c70bf1d11c009e419cbf66b1a1','Reviewed622 publisher changed'
wrapper=source.decode('utf-8')
# Capture the reviewed622 program before its command dispatch. Its source
# assertions run, but no pin, token, network operation or release action does.
dispatch="if sys.argv[1:]==['validate-template']:"
assert wrapper.count(dispatch)==1
wrapper=wrapper.split(dispatch,1)[0]+'\n_emit(code)\n'
output=[]
scope={'__file__':str(base),'__name__':'reviewed_source_transform','_emit':output.append}
builtins.exec(builtins.compile(wrapper,str(base),'exec'),scope)
assert len(output)==1,'Ambiguous reviewed622 transform'
code=output[0].replace('6.0.22','6.0.23').replace('mouse622-release','mouse623-release').replace('MOUSE622_','MOUSE623_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once('real-621-to-622-profile-preserving-install','real-622-to-623-profile-preserving-install')
once('MOUSE_622_REAL_621_TO_622_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_623_REAL_622_TO_623_REPLACE_RELAUNCH_PROFILE_PASS')
once('ecf39b1f4d9de5f1e3eb85fb8f2d86c52bab6848','a94317ce121de73a9a469b55af8eea900a35921d')
once('legacy621-update.cjs','legacy622-update.cjs')
once('# Actual released6.0.21 updater from its immutable tested source.','# Actual released6.0.22 updater from its immutable tested source.')
once('Mouse Browser 6.0.23 — пять столов, превью и Agent Mouse','Mouse Browser 6.0.23 — форма норки и вкладки')
once("for m in ['MOUSE_622_FIVE_DESKS_MODES_PRESERVE_TABS_PASS'", "for m in ['MOUSE_623_BURROW_GEOMETRY_AND_SEAM_PASS','MOUSE_623_TAB_LIFECYCLE_CHIPS_STABILITY_PASS','MOUSE_622_FIVE_DESKS_MODES_PRESERVE_TABS_PASS'")
once("for n in ['mouse-622-preview-light.png'", "for n in ['mouse-623-compact-light.png','mouse-623-compact-dark.png','mouse-623-modes-light.png','mouse-623-modes-dark.png','mouse-623-preview-light.png','mouse-623-preview-dark.png','mouse-623-verification.json','mouse-622-preview-light.png'")
once(" found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]", """ facts623=json.loads((OUT/'mouse-623-verification.json').read_text())
 if facts623.get('version')!=V or not all(facts623.get(k) is True for k in ['fixedTopCurves','seamFree','outlineMatchesFooter']):raise ValueError('Mouse623 native geometry evidence incomplete')
 if facts623.get('themes')!=['light','dark'] or facts623.get('states')!=['compact','modes','preview']:raise ValueError('Mouse623 native geometry states incomplete')
 frames=facts623.get('frames',[])
 if not isinstance(frames,list) or len(frames)!=6 or {(f.get('theme'),f.get('state')) for f in frames}!={(theme,state) for theme in ['light','dark'] for state in ['compact','modes','preview']}:raise ValueError('Mouse623 native geometry frames incomplete')
 lifecycle=facts623.get('tabLifecycle',{})
 if not all(lifecycle.get(k) is True for k in ['closedPageDestroyed','closedCountRemoved','metadataNodesStable','chipReorder','chipTransfer','faviconsPainted','pageIdentityPreserved']):raise ValueError('Mouse623 native tab lifecycle evidence incomplete')
 found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]""")
builtins.compile(code,__file__,'exec')
for required623 in ['MOUSE_623_TAB_LIFECYCLE_CHIPS_STABILITY_PASS','mouse-623-verification.json','fixedTopCurves','seamFree','outlineMatchesFooter','tabLifecycle','closedPageDestroyed','closedCountRemoved','metadataNodesStable','chipReorder','chipTransfer','faviconsPainted','pageIdentityPreserved']:
 assert required623 in code,required623
for required in ["V='6.0.23'","PR=int(PIN['sourcePR'])","(419668574,HEAD,'completed','success')","pr.get('merged')","pr['head']['sha']!=HEAD","pr['base']['ref']!='main'","pr['merge_commit_sha']!=PIN['sourceMerge']","Source is not an ancestor of main","Artifact checksum mismatch","Native verification checksum mismatch","Wrong package bytes","Refusing to overwrite different existing bytes","Refusing channel downgrade","Same-version channel differs","legacy622-update.cjs","ref=a94317ce121de73a9a469b55af8eea900a35921d","MOUSE_623_BURROW_GEOMETRY_AND_SEAM_PASS","MOUSE_623_REAL_622_TO_623_REPLACE_RELAUNCH_PROFILE_PASS","MOUSE_622_AGENT_CDP_PTY_WORKER_STOP_PASS","autonomousActions","MOUSE_621_NATIVE_CROSS_PAGE_PNG_DRAG_PASS","MOUSE_619_EMOJI_PRIVATE_FOCUS_AND_INSERTION_PASS","MOUSE_PROFILE_COOKIE_RESTART_PASS","capture-off-private-no-read","twelve-pixel-pane-corners-clean-compositor","mouse-621-bottom-burrow-dark.png","mouse-622-verification.json","mouse-623-compact-light.png","mouse-623-compact-dark.png","mouse-623-modes-light.png","mouse-623-modes-dark.png","mouse-623-preview-light.png","mouse-623-preview-dark.png"]:
 assert required in code,required

def ready_pin():
 stage=pathlib.Path(__file__).resolve().parents[1]/'staging/mouse/6.0.23-arm64'
 pin=json.loads((stage/'pin.json').read_text())
 if pin.get('version')!='6.0.23':raise ValueError('Wrong Mouse623 pin version')
 for key in ['source','sourceMerge']:
  if not isinstance(pin.get(key),str) or not re.fullmatch('[a-f0-9]{40}',pin[key]):raise ValueError('Mouse623 pin not final: '+key)
 for key in ['archiveSHA256','verificationSHA256']:
  if not isinstance(pin.get(key),str) or not re.fullmatch('[a-f0-9]{64}',pin[key]):raise ValueError('Mouse623 pin not final: '+key)
 for key in ['run','artifact','verificationArtifact','sourcePR']:
  if type(pin.get(key)) is not int or pin[key]<=0:raise ValueError('Mouse623 pin not final: '+key)
 names={'Mouse-Browser-6.0.23-mac-arm64.dmg','Mouse-Browser-6.0.23-mac-arm64.zip'}
 if set(pin.get('packages',{}))!=names:raise ValueError('Mouse623 package pin incomplete')
 for package in pin['packages'].values():
  if type(package.get('size')) is not int or package['size']<=0 or not isinstance(package.get('sha256'),str) or not re.fullmatch('[a-f0-9]{64}',package['sha256']):raise ValueError('Mouse623 package bytes not pinned')
 owner=(stage/'PUBLISH_OWNER').read_text()
 if 'UNSET' in owner or 'READY_TO_PUBLISH_MOUSE_623' not in owner:raise ValueError('Mouse623 native publication evidence is not final')
 notes=(stage/'RELEASE_NOTES.md').read_text()
 if 'UNSET' in notes:raise ValueError('Mouse623 release notes still contain a template placeholder')
 return pin

if sys.argv[1:]==['validate-template']:
 print('MOUSE623_REVIEWED_PUBLISHER_TEMPLATE_GATES_PASS')
elif sys.argv[1:]==['validate']:
 ready_pin();print('MOUSE623_REVIEWED_PUBLISHER_GATES_PASS')
elif len(sys.argv)==2 and sys.argv[1] in ['import','publish','channel']:
 ready_pin();builtins.exec(builtins.compile(code,__file__,'exec'),globals())
else:raise SystemExit('Usage: mouse623-release.py validate-template|validate|import|publish|channel')
