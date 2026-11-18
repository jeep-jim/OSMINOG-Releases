#!/usr/bin/env python3
"""Publish exact native-tested622 bytes; all unset templates fail before any API action."""
import builtins,hashlib,json,pathlib,re,sys
base=pathlib.Path(__file__).with_name('mouse621-release.py')
source=base.read_bytes()
assert hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='bb0a800852ea8ff4403f142fd81ba12d86f82d10','Reviewed621 publisher changed'
wrapper=source.decode('utf-8')
# Run the reviewed621 transform and its assertions, capturing its final source.
# No pin, token, network operation or release mutation is evaluated here.
old="if sys.argv[1:]==['validate']:"
assert wrapper.count(old)==1
wrapper=wrapper.replace(old,'if False:')
old="builtins.exec(builtins.compile(code,__file__,'exec'),globals())"
assert wrapper.count(old)==1
wrapper=wrapper.replace(old,'_emit(code)')
output=[]
scope={'__file__':str(base),'__name__':'reviewed_source_transform','_emit':output.append}
builtins.exec(builtins.compile(wrapper,str(base),'exec'),scope)
assert len(output)==1,'Ambiguous reviewed621 transform'
code=output[0].replace('6.0.21','6.0.22').replace('mouse621-release','mouse622-release').replace('MOUSE621_','MOUSE622_')
def once(old,new):
 global code
 assert code.count(old)==1,(old,code.count(old))
 code=code.replace(old,new)
once('PR=156',"PR=int(PIN['sourcePR'])")
once("if not pr.get('merged') or pr['head']['sha']!=HEAD or pr['base']['ref']!='main':raise ValueError('Exact source PR not merged')", "if not pr.get('merged') or pr['head']['sha']!=HEAD or pr['base']['ref']!='main' or pr['merge_commit_sha']!=PIN['sourceMerge']:raise ValueError('Exact source PR not merged')")
once("required={'five-desktops-live-pages-preserved'", "required={'fixed-five-desktops-lossless-overflow','five-mode-layouts-empty-only-suggestions','desktop-window-previews-last-visible','curved-large-burrow-round-controls','active-desktop-green-indicator','agent-local-scoped-cdp','agent-node-pty-xterm-terminal','agent-external-worker-local-model-fixture','agent-stop-revokes-listener-and-shell','agent-pixel-presence-on-owned-desktop','five-desktops-live-pages-preserved'")
once('real-620-to-621-profile-preserving-install','real-621-to-622-profile-preserving-install')
once('MOUSE_621_REAL_620_TO_621_REPLACE_RELAUNCH_PROFILE_PASS','MOUSE_622_REAL_621_TO_622_REPLACE_RELAUNCH_PROFILE_PASS')
once('aa58a5c412403790b49aa88eb7374c20a27510b6','ecf39b1f4d9de5f1e3eb85fb8f2d86c52bab6848')
once('legacy620-update.cjs','legacy621-update.cjs')
once('# Actual released6.0.20 updater from its immutable tested source.','# Actual released6.0.21 updater from its immutable tested source.')
once('Mouse Browser 6.0.22 — рабочие столы и удобное перетаскивание','Mouse Browser 6.0.22 — пять столов, превью и Agent Mouse')
once("for m in ['MOUSE_621_DESKTOPS_TOASTS_ZOOM_EDITOR_PASS'", "for m in ['MOUSE_622_FIVE_DESKS_MODES_PRESERVE_TABS_PASS','MOUSE_622_BURROW_PREVIEW_BOTH_THEMES_PASS','MOUSE_622_AGENT_CDP_PTY_WORKER_STOP_PASS','MOUSE_621_DESKTOPS_TOASTS_ZOOM_EDITOR_PASS'")
once("for n in ['mouse-621-desktops-light.png'", "for n in ['mouse-622-preview-light.png','mouse-622-preview-dark.png','mouse-622-modes-light.png','mouse-622-modes-dark.png','mouse-622-agent-running.png','mouse-622-verification.json','mouse-621-desktops-light.png'")
# Bind the native verification ZIP to this exact source run as well as packages.
once(" matches=[a for a in api(SOURCE,f'actions/runs/{RUN}/artifacts')['artifacts'] if a['id']==ARTIFACT and a['name']=='mouse-arm64-candidate' and not a['expired']]", """ artifacts=api(SOURCE,f'actions/runs/{RUN}/artifacts')['artifacts']
 verification=[a for a in artifacts if a['id']==PIN['verificationArtifact'] and a['name']=='mouse-arm64-verification' and not a['expired']]
 if len(verification)!=1 or verification[0].get('digest')!='sha256:'+PIN['verificationSHA256']:raise ValueError('Pinned native verification unavailable')
 verification_bytes=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{PIN["verificationArtifact"]}/zip'])
 if len(verification_bytes)>256*1024**2 or sha(verification_bytes)!=PIN['verificationSHA256']:raise ValueError('Native verification checksum mismatch')
 matches=[a for a in artifacts if a['id']==ARTIFACT and a['name']=='mouse-arm64-candidate' and not a['expired']]""")
# This artifact describes deterministic local-model fixture coverage honestly.
once(" found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]", """ facts=json.loads((OUT/'mouse-622-verification.json').read_text())
 if facts.get('fixedDesks')!=5 or facts.get('suggestedRequests')!=7 or facts.get('hiddenCaptures')!=0 or facts.get('localModelFixtureRequests')!=3 or not all(facts.get(k) is True for k in ['realThumbnails','externalWorker','ptyStdout','autonomousActions','stoppedListener','localhostPreview']):raise ValueError('Mouse622 native evidence incomplete')
 found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]""")
builtins.compile(code,__file__,'exec')
for required in ["V='6.0.22'","PR=int(PIN['sourcePR'])","(419668574,HEAD,'completed','success')","pr.get('merged')","pr['head']['sha']!=HEAD","pr['merge_commit_sha']!=PIN['sourceMerge']","Source is not an ancestor of main","Artifact checksum mismatch","Native verification checksum mismatch","Wrong package bytes","Refusing to overwrite different existing bytes","Refusing channel downgrade","Same-version channel differs","legacy621-update.cjs","ref=ecf39b1f4d9de5f1e3eb85fb8f2d86c52bab6848","MOUSE_622_AGENT_CDP_PTY_WORKER_STOP_PASS","MOUSE_622_REAL_621_TO_622_REPLACE_RELAUNCH_PROFILE_PASS","MOUSE_621_NATIVE_CROSS_PAGE_PNG_DRAG_PASS","MOUSE_619_EMOJI_PRIVATE_FOCUS_AND_INSERTION_PASS","MOUSE_PROFILE_COOKIE_RESTART_PASS","capture-off-private-no-read","twelve-pixel-pane-corners-clean-compositor","mouse-621-bottom-burrow-dark.png","mouse-622-preview-dark.png"]:
 assert required in code,required

def ready_pin():
 stage=pathlib.Path(__file__).resolve().parents[1]/'staging/mouse/6.0.22-arm64'
 pin=json.loads((stage/'pin.json').read_text())
 if pin.get('version')!='6.0.22':raise ValueError('Wrong Mouse622 pin version')
 for key in ['source','sourceMerge']:
  if not isinstance(pin.get(key),str) or not re.fullmatch('[a-f0-9]{40}',pin[key]):raise ValueError('Mouse622 pin not final: '+key)
 for key in ['archiveSHA256','verificationSHA256']:
  if not isinstance(pin.get(key),str) or not re.fullmatch('[a-f0-9]{64}',pin[key]):raise ValueError('Mouse622 pin not final: '+key)
 for key in ['run','artifact','verificationArtifact','sourcePR']:
  if type(pin.get(key)) is not int or pin[key]<=0:raise ValueError('Mouse622 pin not final: '+key)
 names={'Mouse-Browser-6.0.22-mac-arm64.dmg','Mouse-Browser-6.0.22-mac-arm64.zip'}
 if set(pin.get('packages',{}))!=names:raise ValueError('Mouse622 package pin incomplete')
 for package in pin['packages'].values():
  if type(package.get('size')) is not int or package['size']<=0 or not isinstance(package.get('sha256'),str) or not re.fullmatch('[a-f0-9]{64}',package['sha256']):raise ValueError('Mouse622 package bytes not pinned')
 owner=(stage/'PUBLISH_OWNER').read_text()
 if 'UNSET' in owner or 'READY_TO_PUBLISH_MOUSE_622' not in owner:raise ValueError('Mouse622 native publication evidence is not final')
 notes=(stage/'RELEASE_NOTES.md').read_text()
 if 'UNSET' in notes:raise ValueError('Mouse622 release notes still contain a template placeholder')
 return pin

if sys.argv[1:]==['validate-template']:
 print('MOUSE622_REVIEWED_PUBLISHER_TEMPLATE_GATES_PASS')
elif sys.argv[1:]==['validate']:
 ready_pin();print('MOUSE622_REVIEWED_PUBLISHER_GATES_PASS')
elif len(sys.argv)==2 and sys.argv[1] in ['import','publish','channel']:
 ready_pin();builtins.exec(builtins.compile(code,__file__,'exec'),globals())
else:raise SystemExit('Usage: mouse622-release.py validate-template|validate|import|publish|channel')
