#!/usr/bin/env python3
"""Publish exact verified Mouse 6.0.28 bytes, never rebuild or replace old assets."""
import base64,hashlib,io,json,os,pathlib,shutil,subprocess,sys,urllib.parse,urllib.request,zipfile
SOURCE='jeep-jim/OSMINOG';REPO='jeep-jim/OSMINOG-Releases';V='6.0.28';TAG='quadro-macos-v6.0.28-arm64'
ROOT=pathlib.Path(__file__).resolve().parents[1];STAGE=ROOT/'staging/mouse/6.0.28-arm64';OUT=ROOT/'mouse628-release'
DMG='Mouse-Browser-6.0.28-mac-arm64.dmg';ZIP='Mouse-Browser-6.0.28-mac-arm64.zip';ALIAS='Quadro-Browser-6.0.28-mac-arm64.dmg'
NAMES=[DMG,ZIP,ALIAS,'SHA256SUMS.txt','mouse-build.json']
PIN=json.loads((STAGE/'pin.json').read_text());HEAD=PIN['source'];RUN=int(PIN['run']);ARTIFACT=int(PIN['artifact']);ARCHIVE_HASH=PIN['archiveSHA256'];PR=int(PIN['sourcePR']);ATTEMPT=int(PIN['sourceAttempt']);SOURCE_JOB=int(PIN['sourceJob'])
assert PIN['version']==V and PIN.get('ready') is True and len(HEAD)==40 and len(ARCHIVE_HASH)==64 and len(PIN['verificationSHA256'])==64 and PIN['sourceMerge'] and PIN['sourcePR'] and PIN['packages']
import hashlib as _hashlib, importlib.util as _util, runpy as _runpy
_previous=pathlib.Path(__file__).with_name('mouse627-release.py')
assert _hashlib.sha256(_previous.read_bytes()).hexdigest()=='a1b416cba4f2d9824df4df6654a61f5cee97894a70a79c12cd34b01801932053'
_saved=sys.argv
try:
 sys.argv=[str(_previous),'validate-template']
 _reviewed=_runpy.run_path(str(_previous),run_name='reviewed_mouse627')
finally:sys.argv=_saved
EVIDENCE_FILES_626=_reviewed['EVIDENCE_FILES_626']
NATIVE_MARKERS_626=_reviewed['NATIVE_MARKERS_626']
SUPERSEDED_FEATURE_TOKENS=_reviewed['SUPERSEDED_FEATURE_TOKENS']
FEATURE_TOKENS_626=_reviewed['FEATURE_TOKENS_626']
PALETTE_FACTS=_reviewed['PALETTE_FACTS']
def verify_626_facts(facts):
 if not isinstance(facts,dict) or facts.get('version')!='6.0.26' or facts.get('stateRestored') is not True:raise ValueError('Retained 626 palette evidence incomplete')
 if not isinstance(facts.get('palette'),dict) or not all(facts['palette'].get(k) is True for k in PALETTE_FACTS):raise ValueError('Retained arbitrary colour palette evidence incomplete')
 if facts.get('supersededForNora')!={'version':'6.0.28','proof':'mouse-628-motion.json','reason':'Content-fit borderless Nora replaces the former fixed-size scrolling and outline contracts'} or 'nora' in facts:raise ValueError('Former 626 Nora geometry not explicitly superseded')
NATIVE_MARKERS_628=('MOUSE_628_LOCAL_MCP_NATIVE_PASS','MOUSE_628_PER_PANE_PROGRESS_NATIVE_PASS','MOUSE_628_OPEN_NORA_DESKTOP_SLIDE_NATIVE_PASS','MOUSE_628_BORDERLESS_NATIVE_PASS','MOUSE_628_NORA_CONTENT_FIT_NATIVE_PASS','MOUSE_628_BURROW_CONTENT_FIT_CONTROLS_PASS','MOUSE_628_ACTIVE_TAB_FLOW_BORDERLESS_BOTH_THEMES_PASS','MOUSE_628_BORDERLESS_UPDATE_BADGE_BOTH_THEMES_PASS')
FEATURE_TOKENS_628={'per-pane-progress-owned-tab','standard-page-progress-observer','local-mcp-readonly-edit-permission','local-mcp-native-directory-boundary','local-mcp-live-tree-action-journal','managed-local-dev-restart','shell-borderless-no-footer-seam','nora-content-fit-no-inner-scroll','open-nora-desktop-slide-behind','three-finger-swipe-first-use-learning','active-tab-flow-borderless-both-themes','nora-compositor-open-close-content-fit','nora-background-footer-stable','nora-reversible-reduced-motion','desktop-compositor-simultaneous-transition','desktop-transition-constant-native-layout'}
_spec=_util.spec_from_file_location('mouse628_evidence',pathlib.Path(__file__).with_name('mouse628-evidence.py'))
_evidence=_util.module_from_spec(_spec);_spec.loader.exec_module(_evidence)
_trace=_runpy.run_path(str(pathlib.Path(__file__).with_name('mouse628-motion-trace.py')),run_name='mouse628_trace')
def verify_628(read,source=False):
 result=_evidence.verify(read)
 if source:
  update=read('mouse-update-roundtrip.log').decode('utf-8')
  if 'MOUSE_628_REAL_627_TO_628_REPLACE_RELAUNCH_PROFILE_PASS' not in update:raise ValueError('Source real replacement missing')
 return result
def verify_628_trace(read,provenance):
 names=['mouse-628-motion-trace.json','mouse-628-motion.json']
 blobs={n:read(n) for n in names}
 if not all(0<len(v)<=72*1024**2 for v in blobs.values()):raise ValueError('Missing/oversized trace input')
 docs={n:json.loads(v) for n,v in blobs.items()}
 report=_trace['verify_trace_data'](docs[names[0]],docs[names[1]])
 if report.get('status')!='pass' or report.get('algorithm')!='mouse628-motion-trace-evidence-v2' or report.get('directIdentityLink') is not False:raise ValueError('Motion trace rejected')
 return {'version':V,'inputs':{n:{'size':len(blobs[n]),'sha256':sha(blobs[n])} for n in names},'provenance':provenance,'evidence':report}

def validate():
 if PIN.get('version')!=V or PIN.get('ready') is not True or ATTEMPT<1 or SOURCE_JOB<1:raise ValueError('Mouse628 pin not ready')
 if PIN['previous'].get('version')!='6.0.27' or PIN['previous'].get('source')!='acbcf36beff4ec504b018402227e5b553e4f0fdc' or PIN['previous'].get('updaterBlobSHA')!='c4a9564bc5a7c3cf2c6798b5eade9680ee0e57cf':raise ValueError('Previous627 source/updater pin mismatch')
 if set(PIN['packages'])!={DMG,ZIP}:raise ValueError('Expected exactly two release packages')
 for name,package in PIN['packages'].items():
  if not isinstance(package.get('size'),int) or not 100*1024**2<package['size']<350*1024**2 or len(package.get('sha256',''))!=64 or any(c not in '0123456789abcdef' for c in package['sha256']):raise ValueError('Package pin invalid: '+name)
 if not (STAGE/'RELEASE_NOTES.md').read_text().startswith('# Mouse Browser 6.0.28'):raise ValueError('Release notes version mismatch')
 if (STAGE/'PUBLISH_OWNER').read_text().strip()!='Mouse Browser 6.0.28: publish pinned source and verified Mac packages':raise ValueError('Owner publication trigger mismatch')
 schema=json.loads((STAGE/'evidence.schema.json').read_text())
 if set(schema['required'])!=set(_evidence.JSON_NAMES) or schema['x-motionTraceGate']['algorithm']!='mouse628-motion-trace-evidence-v2':raise ValueError('Evidence schema mismatch')
 print('MOUSE628_RELEASE_PIN_CONTRACT_PASS',flush=True)

def api(repo,p,method='GET',payload=None,missing=False):
 cmd=['gh','api',f'repos/{repo}/{p}','--method',method]
 if payload is not None:cmd+=['--input','-']
 r=subprocess.run(cmd,input=json.dumps(payload).encode() if payload is not None else None,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if r.returncode:
  if missing and b'HTTP 404' in r.stderr:return None
  raise RuntimeError('GitHub request failed: '+p+' '+r.stderr.decode(errors='replace')[:400])
 return json.loads(r.stdout)
def sha(data):return hashlib.sha256(data).hexdigest()
def import_candidate():
 run=api(SOURCE,f'actions/runs/{RUN}')
 if (run['workflow_id'],run['head_sha'])!=(419668574,HEAD):raise ValueError('Exact native source run mismatch')
 # GitHub re-runs change the run's aggregate conclusion. Bind the artifact to
 # the successful, immutable attempt/job instead of trusting a later attempt.
 jobs=api(SOURCE,f'actions/runs/{RUN}/attempts/{ATTEMPT}/jobs?per_page=100')['jobs']
 passed=[job for job in jobs if job['id']==SOURCE_JOB and job['name']=='mouse-arm64' and
         job['status']=='completed' and job['conclusion']=='success']
 if len(passed)!=1 or not all(any(step['number']==number and step['conclusion']=='success'
     for step in passed[0].get('steps',[])) for number in (15,16,17,18)):
  raise ValueError('Pinned exact native source attempt has not passed all package gates')
 pr=api(SOURCE,f'pulls/{PR}')
 if not pr.get('merged') or pr['head']['sha']!=HEAD or pr['base']['ref']!='main' or pr['merge_commit_sha']!=PIN['sourceMerge']:raise ValueError('Exact source PR not merged')
 c=api(SOURCE,f'compare/{HEAD}...main')
 if c['status'] not in ['ahead','identical'] or c['behind_by']!=0:raise ValueError('Source is not an ancestor of main')
 artifacts=api(SOURCE,f'actions/runs/{RUN}/artifacts')['artifacts']
 verification=[a for a in artifacts if a['id']==PIN['verificationArtifact'] and a['name']=='mouse-arm64-verification' and not a['expired']]
 if len(verification)!=1 or verification[0].get('digest')!='sha256:'+PIN['verificationSHA256']:raise ValueError('Pinned native verification unavailable')
 verification_bytes=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{PIN["verificationArtifact"]}/zip'])
 if len(verification_bytes)>256*1024**2 or sha(verification_bytes)!=PIN['verificationSHA256']:raise ValueError('Native verification checksum mismatch')
 # Inspect new evidence in the exact source verification archive as well as
 # the fresh installed rerun below. A matching archive hash alone is not a
 # substitute for the required native interaction facts and rendered frames.
 with zipfile.ZipFile(io.BytesIO(verification_bytes)) as z:
  for name in EVIDENCE_FILES_626+['mouse-smoke-write.log','mouse-update-roundtrip.log']:
   items=[i for i in z.infolist() if i.filename==name]
   if len(items)!=1 or items[0].is_dir() or items[0].file_size>16*1024**2:raise ValueError('Mouse626 source evidence missing or oversized: '+name)
  verify_626_facts(json.loads(z.read('mouse-626-verification.json')))
  source_smoke=z.read('mouse-smoke-write.log').decode('utf-8')
  if not all(m in source_smoke for m in NATIVE_MARKERS_626):raise ValueError('Mouse626 source native markers missing')
  for name in EVIDENCE_FILES_626[1:]:
   if not z.read(name).startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Mouse626 source screenshot is not PNG: '+name)
 with zipfile.ZipFile(io.BytesIO(verification_bytes)) as z:
  source_report=verify_628(z.read,source=True)
  source_trace=verify_628_trace(z.read,{'stage':'source-import','source':HEAD,'sourceRun':RUN,'verificationArtifact':PIN['verificationArtifact'],'verificationSHA256':PIN['verificationSHA256']})
  source_smoke=z.read('mouse-smoke-write.log').decode('utf-8')
  source_read=z.read('mouse-smoke-read.log').decode('utf-8')
  if not all(marker in source_smoke+source_read for marker in NATIVE_MARKERS_628):raise ValueError('Mouse628 source native markers missing')
 matches=[a for a in artifacts if a['id']==ARTIFACT and a['name']=='mouse-arm64-candidate' and not a['expired']]
 if len(matches)!=1:raise ValueError('Pinned artifact unavailable')
 a=matches[0];archive=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{ARTIFACT}/zip'])
 if len(archive)>1024**3 or sha(archive)!=ARCHIVE_HASH or a.get('digest')!='sha256:'+ARCHIVE_HASH:raise ValueError('Artifact checksum mismatch')
 OUT.mkdir(exist_ok=True)
 with zipfile.ZipFile(io.BytesIO(archive)) as z:
  entries=z.infolist();expected={DMG,ZIP,'SHA256SUMS.txt','mouse-build.json'}
  if len(entries)!=4 or {x.filename for x in entries}!=expected or sum(x.file_size for x in entries)>1024**3:raise ValueError('Unexpected archive entries')
  for x in entries:
   if x.is_dir() or (x.external_attr>>16)&0o170000==0o120000:raise ValueError('Invalid archive file type')
   (OUT/x.filename).write_bytes(z.read(x))
 b=json.loads((OUT/'mouse-build.json').read_text())
 if b['source']!=HEAD or int(b['runId'])!=RUN or b['version']!=V or b['productName']!='Mouse Browser' or b['arch']!='arm64' or b['platform']!='darwin' or b['signing']!='ad-hoc' or b['notarized'] is not False:raise ValueError('Invalid build provenance')
 required={'fixed-five-desktops-lossless-overflow','five-mode-layouts-empty-only-suggestions','desktop-window-previews-last-visible','curved-large-burrow-round-controls','active-desktop-green-indicator','agent-local-scoped-cdp','agent-node-pty-xterm-terminal','agent-external-worker-local-model-fixture','agent-stop-revokes-listener-and-shell','agent-pixel-presence-on-owned-desktop','five-desktops-live-pages-preserved','smooth-native-desktop-slide','expiring-central-feedback-no-footer-text','native-image-file-drag-between-pages','global-page-zoom-existing-future','annotation-select-mouse-keyboard-green-palette','section-labels-after-count','history-meaningful-visits-not-actions','update-minimized-live-progress','head-everywhere-native-icons','download-image-previews','local-opt-in-clipboard-and-screenshot-copies','capture-off-private-no-read','aligned-checkboxes-ai-square-controls','library-favicons-file-icons-list-grid-safe-selection','active-tab-flow-borderless-both-themes','native-emoji-picker-macos-visible','emoji-owned-page-ai-shell-focus','emoji-private-workspace-routing','emoji-windows-api-contract','top-plus-bottom-centered-burrow','owner-exact-128-pixel-small-head','address-focus-native-buttons-first-click','twelve-pixel-pane-corners-clean-compositor','fractional-viewport-endpoints-no-rim','footer-preserved-ai-status-only-hidden','grounded-gradient-desktop-burrow','real-627-to-628-profile-preserving-install','ordinary-top-plus-no-glow','unified-controls-loading-fullscreen-corners','wallet-removed-no-provider','separated-footer-library-original-controls','real-update-badge-normal-mode-metadata-only','mouse-burrow-desktop-button','ai-fullscreen-restore-normal-private-no-reload','tabs-fit-swap-expand-address-ai-height-selection','ai-bundled-official-picker','ai-history-buttons','cyan-ai-active-both-themes','adjacent-new-tab','restored-619-private-artwork-and-glasses','destroyed-view-lifetime','bounded-shell-recovery','private-theme-light-dark-live','capture-legacy-recovery-picker-single-frame','large-update-mascot','resize-transient-size-hud','native-tab-click-below-apple-menu','fixed-light-dock','verified-update-installer'}
 if not {'agent-service-layout-preserved-return-reload','layout-history-native-undo-redo-persist','scoped-progress-determinate-indeterminate-stop','per-pane-progress-owned-tab'}.issubset(set(b['tests'])):raise ValueError('Mouse624 feature evidence incomplete')
 if not {'local-pdf-docx-xlsx-edit-save','document-original-parts-preserved','document-unsaved-conflict-private-guards','document-editor-preserves-browser-grid','bounded-document-rendering','search-engine-choice','private-search-preference'}.issubset(set(b['tests'])):raise ValueError('Mouse625 feature evidence incomplete')
 if not FEATURE_TOKENS_626.issubset(set(b['tests'])):raise ValueError('Mouse626 feature evidence incomplete')
 if SUPERSEDED_FEATURE_TOKENS.intersection(b['tests']):raise ValueError('Mouse628 build claims superseded contour morph')
 if not FEATURE_TOKENS_628.issubset(set(b['tests'])):raise ValueError('Mouse628 feature evidence incomplete')
 if not required.issubset(set(b['tests'])) or b['wallet']!={'removed':True,'legacyDataPreserved':True}:raise ValueError('Invalid feature boundary')
 checks={}
 for line in (OUT/'SHA256SUMS.txt').read_text().splitlines():
  digest,name=line.split(maxsplit=1)
  if name not in PIN['packages'] or name in checks or digest!=PIN['packages'][name]['sha256']:raise ValueError('Wrong declared checksum')
  data=(OUT/name).read_bytes()
  if len(data)!=PIN['packages'][name]['size'] or sha(data)!=digest:raise ValueError('Wrong package bytes')
  checks[name]=digest
 if set(checks)!={DMG,ZIP}:raise ValueError('Missing package checksum')
 shutil.copyfile(OUT/DMG,OUT/ALIAS);checks[ALIAS]=checks[DMG]
 (OUT/'SHA256SUMS.txt').write_text(''.join(f'{digest}  {name}\n' for name,digest in sorted(checks.items())))
 for remote,local in [('tools/mouse-verify.py','mouse-verify.py'),('tools/mouse-update-verify.py','mouse-update-verify.py'),('desktop/mouse-install-update.cjs','mouse-install-update.cjs'),('desktop/mouse-update.cjs','mouse-update.cjs')]:
  obj=api(SOURCE,f'contents/{remote}?ref={HEAD}');(OUT/local).write_bytes(base64.b64decode(obj['content']))
 # Actual released6.0.27 updater from its separately pinned immutable tested source.
 previous=PIN['previous'];package=previous['package']
 released=api(REPO,'releases/tags/quadro-macos-v6.0.27-arm64')
 if released.get('draft') or not released.get('published_at'):raise ValueError('Previous627 release is not public')
 old_assets=[a for a in released.get('assets',[]) if a.get('name')==package['name']]
 if len(old_assets)!=1 or old_assets[0].get('state')!='uploaded' or old_assets[0].get('size')!=package['size'] or old_assets[0].get('digest')!='sha256:'+package['sha256']:raise ValueError('Previous627 public package pin mismatch')
 old=api(SOURCE,f"contents/desktop/mouse-update.cjs?ref={previous['source']}")
 old_bytes=base64.b64decode(old['content'])
 old_blob=hashlib.sha1(b'blob '+str(len(old_bytes)).encode()+b'\0'+old_bytes).hexdigest()
 if old.get('sha')!=previous['updaterBlobSHA'] or old_blob!=previous['updaterBlobSHA']:raise ValueError('Previous627 immutable updater blob mismatch')
 (OUT/'legacy627-update.cjs').write_bytes(old_bytes)
 # The reviewed, exact-source helper performs the one real public627 DMG
 # download and checksum verification before installed replacement testing.
 # Do not substitute a new download, synthetic fixture, or a different old DMG.
 upgrade=(OUT/'mouse-update-verify.py').read_text()
 for expected in [package['name'],str(package['size']),package['sha256'],"version(target)=='6.0.28'",'MOUSE_628_REAL_627_TO_628_REPLACE_RELAUNCH_PROFILE_PASS']:
  if expected not in upgrade:raise ValueError('Previous627 real replacement helper pin mismatch: '+expected)

 notes=(STAGE/'RELEASE_NOTES.md').read_text()
 notes+=f'\n\nSource: https://github.com/{SOURCE}/commit/{HEAD}\nSource tests: https://github.com/{SOURCE}/actions/runs/{RUN}\nInstalled DMG tests: https://github.com/{REPO}/actions/runs/{os.environ["GITHUB_RUN_ID"]}\n\nSHA-256:\n```\n'+(OUT/'SHA256SUMS.txt').read_text()+'```\n'
 (OUT/'RELEASE_NOTES.md').write_text(notes)
 (OUT/'mouse-628-source-evidence-report.json').write_text(json.dumps(source_report,indent=2,allow_nan=False)+'\n')
 (OUT/'mouse-628-source-motion-trace-report.json').write_text(json.dumps(source_trace,indent=2,allow_nan=False)+'\n')
 print('MOUSE628_SOURCE_EVIDENCE_AND_TRACE_PASS',flush=True)
 print('MOUSE628_EXACT_SOURCE_BYTES_IMPORTED',flush=True)
def local_assets():return {n:{'size':(OUT/n).stat().st_size,'digest':'sha256:'+sha((OUT/n).read_bytes())} for n in NAMES}
def verify_release(r):
 local=local_assets();assets={a['name']:a for a in r['assets']}
 if set(assets)!=set(NAMES):raise ValueError('Unexpected release assets')
 for n,v in local.items():
  a=assets[n]
  if a['state']!='uploaded' or a['size']!=v['size'] or a.get('digest')!=v['digest']:raise ValueError('Remote digest mismatch: '+n)
 return assets
def published():
 r=api(REPO,'releases/tags/'+TAG);verify_release(r)
 if r['draft'] or not r['published_at']:raise ValueError('Release not public')
 return r
def publish():
 smoke=(OUT/'mouse-smoke-write.log').read_text()
 private=(OUT/'mouse-mouse-private-smoke.log').read_text()
 for marker in ['MOUSE_619_EMOJI_PRIVATE_FOCUS_AND_INSERTION_PASS','MOUSE_611_PRIVATE_THEME_ASSETS_AND_LIVE_SWITCH_PASS','MOUSE_614_AI_FULLSCREEN_RESTORE_PRIVATE_PASS']:
  if marker not in private:raise ValueError('Actual private verification missing: '+marker)
 if 'MOUSE_PROFILE_COOKIE_RESTART_PASS' not in (OUT/'mouse-smoke-read.log').read_text():raise ValueError('Profile preservation check missing')
 for m in list(NATIVE_MARKERS_628)+NATIVE_MARKERS_626+['MOUSE_625_SEARCH_ENGINE_NORMAL_PRIVATE_PASS','MOUSE_625_DOCUMENTS_NATIVE_EDIT_SAVE_PRESERVE_PASS','MOUSE_624_AGENT_SERVICE_LAYOUT_PERSIST_PASS','MOUSE_624_LAYOUT_UNDO_REDO_PERSIST_PASS','MOUSE_624_SCOPED_PROGRESS_PILL_PASS','MOUSE_623_TAB_LIFECYCLE_CHIPS_STABILITY_PASS','MOUSE_622_FIVE_DESKS_MODES_PRESERVE_TABS_PASS','MOUSE_622_BURROW_PREVIEW_BOTH_THEMES_PASS','MOUSE_622_AGENT_CDP_PTY_WORKER_STOP_PASS','MOUSE_621_DESKTOPS_TOASTS_ZOOM_EDITOR_PASS','MOUSE_621_NATIVE_CROSS_PAGE_PNG_DRAG_PASS','MOUSE_621_SMOOTH_DESKTOP_NATIVE_SLIDE_PASS','MOUSE_620_REAL_HISTORY_NO_ACTION_FLOOD_PASS','MOUSE_620_UPDATE_HEAD_PREVIEW_ARCHIVE_CONTROLS_PASS','MOUSE_620_INSTALLED_ICNS_DOCK_UI_HEAD_PASS','MOUSE_619_LIBRARY_ICONS_VIEWS_TOPBAR_SELECTION_SAFE_CLEAR_PASS','MOUSE_619_EMOJI_FOOTER_PAGE_AI_SHELL_FOCUS_PASS','MOUSE_619_NATIVE_CHARACTER_VIEWER_VISIBLE_PASS','MOUSE_621_TOP_PLUS_BOTTOM_BURROW_BOTH_THEMES_PASS','MOUSE_617_NATIVE_ADDRESS_CLICKS_HEAD_10PX_FOOTER_PASS','MOUSE_616_CONTROLS_LOADING_FULLSCREEN_CORNERS_NO_WALLET_PASS','MOUSE_616_ARCH_PLUS_AND_SEPARATE_FOOTER_BOTH_THEMES_PASS','MOUSE_614_AI_FULLSCREEN_RESTORE_NORMAL_PASS','MOUSE_613_TABS_REGROW_AFTER_CLOSE_PASS','MOUSE_613_TABS_SWAP_ADDRESS_AI_CHROME_PASS','MOUSE_612_AI_LOGOS_NAV_ACTIVE_AND_ADJACENT_PLUS_PASS','MOUSE_612_DESTROYED_GUESTS_DISPOSE_AND_SHELL_RECOVERY_PASS','MOUSE_610_PURPLE_GLASSES_AND_ALL_FOOTER_PIXELS_BOTH_THEMES_PASS','MOUSE_609_RESIZE_HUD_BOTH_AXES_CENTERS_RELEASE_PASS','MOUSE_609_LARGE_UPDATE_MASCOT_BOTH_THEMES_PASS','MOUSE_609_REAL_LEGACY_AND_ONE_FRAME_STREAM_STOP_PASS','MOUSE_609_REAL_APPLE_MENU_TAB_CLICK_PASS','MOUSE_608_WHITE_SQUARE_PIXELS_AND_FIXED_DOCK_PASS','MOUSE_ARM64_SMOKE_PASS']:
  if m not in smoke:raise ValueError('Missing native verification: '+m)
 if 'MOUSE_628_REAL_627_TO_628_REPLACE_RELAUNCH_PROFILE_PASS' not in (OUT/'mouse-update-roundtrip.log').read_text():raise ValueError('Real replacement check missing')
 for n in EVIDENCE_FILES_626+['mouse-625-search-verification.json','mouse-625-search-normal.png','mouse-625-search-private.png','mouse-625-documents.json','mouse-625-pdf.png','mouse-625-docx.png','mouse-625-xlsx.png','mouse-624-verification.json','mouse-624-agent-preserved.png','mouse-624-layout-history.png','mouse-624-progress-known.png','mouse-624-progress-unknown.png','mouse-623-compact-light.png','mouse-623-compact-dark.png','mouse-623-modes-light.png','mouse-623-modes-dark.png','mouse-623-preview-light.png','mouse-623-preview-dark.png','mouse-623-verification.json','mouse-622-preview-light.png','mouse-622-preview-dark.png','mouse-622-modes-light.png','mouse-622-modes-dark.png','mouse-622-agent-running.png','mouse-622-verification.json','mouse-621-desktops-light.png','mouse-621-desktops-dark.png','mouse-621-toast-light.png','mouse-621-toast-dark.png','mouse-621-zoom-light.png','mouse-621-zoom-dark.png','mouse-621-annotation-select.png','mouse-620-history.png','mouse-620-download-previews-light.png','mouse-620-download-previews-dark.png','mouse-620-local-archive-light.png','mouse-620-local-archive-dark.png','mouse-620-text-preview-light.png','mouse-620-text-preview-dark.png','mouse-619-tab-flow-light.png','mouse-619-tab-flow-dark.png','mouse-619-library-bookmarks-light.png','mouse-619-library-bookmarks-dark.png','mouse-619-library-history-light.png','mouse-619-library-history-dark.png','mouse-619-library-downloads-list-light.png','mouse-619-library-downloads-list-dark.png','mouse-619-library-downloads-grid-light.png','mouse-619-library-downloads-grid-dark.png','mouse-619-native-picker.png','mouse-619-native-picker.json','mouse-619-emoji-normal-light.png','mouse-619-emoji-normal-dark.png','mouse-619-emoji-private-light.png','mouse-619-emoji-private-dark.png','mouse-621-bottom-burrow-light.png','mouse-621-bottom-burrow-dark.png','mouse-617-chrome-light.png','mouse-617-chrome-dark.png','mouse-616-controls-light.png','mouse-616-controls-dark.png','mouse-616-native-corners-light.png','mouse-616-native-corners-dark.png','mouse-614-burrow-update-light.png','mouse-614-burrow-update-dark.png','mouse-614-ai-fullscreen-normal-light.png','mouse-614-ai-fullscreen-normal-dark.png','mouse-614-ai-fullscreen-private-light.png','mouse-614-ai-fullscreen-private-dark.png','mouse-613-ai-choice-light.png','mouse-613-ai-choice-dark.png','mouse-613-address-light.png','mouse-613-address-dark.png','mouse-612-ai-light.png','mouse-612-ai-dark.png','mouse-611-private-light.png','mouse-611-private-dark.png','mouse-609-real-menu-tab-click.png','mouse-609-update-light.png','mouse-609-update-dark.png','mouse-609-resize-hud.png']:
  if not (OUT/n).is_file():raise ValueError('Missing actual visual verification: '+n)
 facts=json.loads((OUT/'mouse-622-verification.json').read_text())
 if facts.get('fixedDesks')!=5 or facts.get('suggestedRequests')!=7 or facts.get('hiddenCaptures')!=0 or facts.get('localModelFixtureRequests')!=3 or not all(facts.get(k) is True for k in ['realThumbnails','externalWorker','ptyStdout','autonomousActions','stoppedListener','localhostPreview']):raise ValueError('Mouse622 native evidence incomplete')
 facts623=json.loads((OUT/'mouse-623-verification.json').read_text())
 if facts623.get('version')!='6.0.23' or facts623.get('geometryVersion')!='6.0.28' or not all(facts623.get(k) is True for k in ['fixedTopCurves','supersededOldGeometry']):raise ValueError('Mouse623 content-fit geometry evidence incomplete')
 if facts623.get('themes')!=['light','dark'] or facts623.get('states')!=['compact','modes','preview']:raise ValueError('Mouse623 native geometry states incomplete')
 frames=facts623.get('frames',[])
 if not isinstance(frames,list) or len(frames)!=6:raise ValueError('Mouse623 native geometry frames incomplete')
 lifecycle=facts623.get('tabLifecycle',{})
 if not all(lifecycle.get(k) is True for k in ['closedPageDestroyed','closedCountRemoved','metadataNodesStable','chipReorder','chipTransfer','faviconsPainted','pageIdentityPreserved']):raise ValueError('Mouse623 native tab lifecycle evidence incomplete')
 facts624=json.loads((OUT/'mouse-624-verification.json').read_text())
 if facts624.get('version')!='6.0.24':raise ValueError('Mouse624 native evidence version mismatch')
 for group,keys in [('agent',['layoutExact','pagesPreserved','aiReturn','reloadExact','defaultDisabled']),('history',['undo','redo','persisted','pagesPreserved','entryRestore']),('progress',['determinate','indeterminate','completionDismissed','stopped','pageScope'])]:
  if not all(facts624.get(group,{}).get(k) is True for k in keys):raise ValueError('Mouse624 native evidence incomplete: '+group)
 facts625=json.loads((OUT/'mouse-625-documents.json').read_text())
 if facts625.get('version')!='6.0.25':raise ValueError('Mouse625 native evidence version mismatch')
 for group,keys in [('pdf',['opened','annotated','reopened','originalPreserved','rotated','workerOffMainThread']),('docx',['edited','reopened','unmodifiedPartsPreserved','bold','tablePreserved','headerPreserved']),('xlsx',['edited','formulaPreserved','reopened','unmodifiedPartsPreserved','inlineStringPreserved']),('safeguards',['saveAs','originalUnchanged','dirtyCancel','conflictRejected','privateCleared','dirtySave']),('browser',['gridPreserved','pageIdentityPreserved'])]:
  if not isinstance(facts625.get(group),dict) or not all(facts625[group].get(k) is True for k in keys):raise ValueError('Mouse625 native evidence incomplete: '+group)
 search625=json.loads((OUT/'mouse-625-search-verification.json').read_text())
 if not isinstance(search625,dict) or search625.get('version')!='6.0.25':raise ValueError('Mouse625 native search evidence version mismatch')
 if search625.get('stateRestored') is not True:raise ValueError('Mouse625 native search fixture did not restore state')
 if not isinstance(search625.get('search'),dict) or not all(search625['search'].get(k) is True for k in ['cleanGoogleDefault','pickerKeyboardSelection','addressAndHomeMatch','normalPersistsReload','privateRAMOnly','noExternalSearchNavigation']):raise ValueError('Mouse625 native search evidence incomplete')
 verify_626_facts(json.loads((OUT/'mouse-626-verification.json').read_text()))
 for name in EVIDENCE_FILES_626[1:]:
  if not (OUT/name).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Mouse626 installed screenshot is not PNG: '+name)
 installed_report=verify_628(lambda name:(OUT/name).read_bytes(),source=False)
 trace_report=verify_628_trace(lambda name:(OUT/name).read_bytes(),{'stage':'installed-before-publication','source':HEAD,'sourceRun':RUN,'artifact':ARTIFACT,'archiveSHA256':ARCHIVE_HASH,'publisherRun':os.environ['GITHUB_RUN_ID'],'publisherRunAttempt':os.environ['GITHUB_RUN_ATTEMPT'],'publisherSHA':os.environ['GITHUB_SHA']})
 (OUT/'mouse-628-installed-evidence-report.json').write_text(json.dumps(installed_report,indent=2,allow_nan=False)+'\n')
 (OUT/'mouse-628-motion-trace-report.json').write_text(json.dumps(trace_report,indent=2,allow_nan=False)+'\n')
 print('MOUSE628_FRESH_INSTALLED_EVIDENCE_AND_TRACE_PASS',flush=True)
 found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]
 if len(found)>1:raise ValueError('Ambiguous release')
 r=api(REPO,'releases/'+str(found[0]['id'])) if found else api(REPO,'releases','POST',{'tag_name':TAG,'target_commitish':os.environ['GITHUB_SHA'],'name':'Mouse Browser 6.0.28 — Нора, прогресс и Локал','body':(OUT/'RELEASE_NOTES.md').read_text(),'draft':True,'prerelease':True,'make_latest':'false'})
 if r['draft']:
  local=local_assets();remote={a['name']:a for a in r['assets']}
  if set(remote)-set(NAMES):raise ValueError('Unexpected draft assets')
  for n,v in local.items():
   if n in remote:
    if remote[n]['size']!=v['size'] or remote[n].get('digest')!=v['digest']:raise ValueError('Refusing to overwrite different existing bytes')
    continue
   url=f'https://uploads.github.com/repos/{REPO}/releases/{r["id"]}/assets?name='+urllib.parse.quote(n,safe='')
   request=urllib.request.Request(url,data=(OUT/n).read_bytes(),method='POST',headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Content-Type':'application/octet-stream','Accept':'application/vnd.github+json'})
   with urllib.request.urlopen(request,timeout=180) as response:json.load(response)
  r=api(REPO,'releases/'+str(r['id']));verify_release(r)
  api(REPO,'releases/'+str(r['id']),'PATCH',{'draft':False,'prerelease':True,'make_latest':'false','body':(OUT/'RELEASE_NOTES.md').read_text()})
 r=published();(OUT/'RELEASE_RESULT.json').write_text(json.dumps({'id':r['id'],'url':r['html_url'],'publishedAt':r['published_at'],'assets':[{k:a[k] for k in ['name','size','digest','browser_download_url']} for a in r['assets']]},indent=2)+'\n')
 print('MOUSE628_PUBLIC_RELEASE_HASHES_PASS',flush=True)
def channel():
 r=published();a=next(a for a in r['assets'] if a['name']==DMG)
 data={'schema':1,'platform':'darwin','arch':'arm64','version':V,'url':a['browser_download_url'],'size':a['size'],'digest':a['digest'],'publishedAt':r['published_at']}
 p='contents/channels/mouse/macos-arm64.json';old=api(REPO,p+'?ref=main',missing=True)
 if old:
  previous=json.loads(base64.b64decode(old['content']))
  if tuple(map(int,previous['version'].split('.')))>tuple(map(int,V.split('.'))):raise ValueError('Refusing channel downgrade')
  if previous['version']==V:
   if any(previous.get(k)!=v for k,v in data.items()):raise ValueError('Same-version channel differs; refusing overwrite')
   print('MOUSE628_CHANNEL_ALREADY_PUBLISHED',flush=True);return
 payload={'message':'Publish verified Mouse Browser 6.0.28 static macOS update channel','branch':'main','content':base64.b64encode((json.dumps(data,indent=2)+'\n').encode()).decode()}
 if old:payload['sha']=old['sha']
 api(REPO,p,'PUT',payload);(OUT/'CHANNEL_RESULT.json').write_text(json.dumps(data,indent=2)+'\n')
 print('MOUSE628_STATIC_CHANNEL_PUBLISHED',flush=True)
if __name__=='__main__':
 actions={'validate':validate,'import':import_candidate,'publish':publish,'channel':channel}
 if len(sys.argv)!=2 or sys.argv[1] not in actions:raise SystemExit('Usage: mouse628-release.py validate|import|publish|channel')
 actions[sys.argv[1]]()
