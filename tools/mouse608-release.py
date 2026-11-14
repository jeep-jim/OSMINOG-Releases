#!/usr/bin/env python3
"""Publish only the exact tested Mouse608 bytes, then its dedicated static channel."""
import base64,hashlib,io,json,os,pathlib,shutil,subprocess,sys,urllib.parse,urllib.request,zipfile
SOURCE='jeep-jim/OSMINOG';REPO='jeep-jim/OSMINOG-Releases';V='6.0.8';TAG='quadro-macos-v6.0.8-arm64'
HEAD='d76c837311c1691fcc4e0e3af311b9905fc7e37e';RUN=43607404904;PR=140
ARTIFACT=14118454820;ARCHIVE_HASH='591ded2604e8821ca4a53c351811cc09fa732182dbe718a93bcba2093a30a357'
ROOT=pathlib.Path(__file__).resolve().parents[1];OUT=ROOT/'mouse608-release'
DMG='Mouse-Browser-6.0.8-mac-arm64.dmg';ZIP='Mouse-Browser-6.0.8-mac-arm64.zip';ALIAS='Quadro-Browser-6.0.8-mac-arm64.dmg'
PIN={DMG:(128800421,'bdf75806471b5f86c3bbf69593edcd1de9640f5627033a20f485003289908f1f'),ZIP:(128819114,'0a4e93a9ae940bae91c1238129b76b733b7daf6c6409b196fb3987e726a12b3e')}
NAMES=[DMG,ZIP,ALIAS,'SHA256SUMS.txt','quadro-build.json']
def api(repo,p,method='GET',payload=None,missing=False):
 cmd=['gh','api',f'repos/{repo}/{p}','--method',method]
 if payload is not None:cmd+=['--input','-']
 r=subprocess.run(cmd,input=json.dumps(payload).encode() if payload is not None else None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
 if r.returncode:
  if missing and b'HTTP 404' in r.stderr:return None
  raise RuntimeError('GitHub request failed: '+p+' '+r.stderr.decode(errors='replace')[:400])
 return json.loads(r.stdout)
def sha(data):return hashlib.sha256(data).hexdigest()
def import_candidate():
 run=api(SOURCE,f'actions/runs/{RUN}')
 if (run['workflow_id'],run['head_sha'],run['status'],run['conclusion'])!=(417128557,HEAD,'completed','success'):raise ValueError('Exact native source has not passed')
 pr=api(SOURCE,f'pulls/{PR}')
 if not pr.get('merged') or pr['head']['sha']!=HEAD or pr['base']['ref']!='main':raise ValueError('Exact source PR not merged')
 c=api(SOURCE,f'compare/{HEAD}...main')
 if c['status'] not in ['ahead','identical'] or c['behind_by']!=0:raise ValueError('Source is not an ancestor of main')
 matches=[a for a in api(SOURCE,f'actions/runs/{RUN}/artifacts')['artifacts'] if a['id']==ARTIFACT and a['name']=='quadro-arm64-candidate' and not a['expired']]
 if len(matches)!=1:raise ValueError('Pinned artifact unavailable')
 a=matches[0];archive=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{ARTIFACT}/zip'])
 if len(archive)>1024**3 or sha(archive)!=ARCHIVE_HASH or a.get('digest')!='sha256:'+ARCHIVE_HASH:raise ValueError('Artifact checksum mismatch')
 OUT.mkdir(exist_ok=True)
 with zipfile.ZipFile(io.BytesIO(archive)) as z:
  entries=z.infolist();expected={DMG,ZIP,'SHA256SUMS.txt','quadro-build.json'}
  if len(entries)!=4 or {x.filename for x in entries}!=expected or sum(x.file_size for x in entries)>1024**3:raise ValueError('Unexpected archive entries')
  for x in entries:
   if x.is_dir() or (x.external_attr>>16)&0o170000==0o120000:raise ValueError('Invalid archive file type')
   (OUT/x.filename).write_bytes(z.read(x))
 b=json.loads((OUT/'quadro-build.json').read_text())
 if b['source']!=HEAD or int(b['runId'])!=RUN or b['version']!=V or b['productName']!='Mouse Browser' or b['arch']!='arm64' or b['platform']!='darwin' or b['signing']!='ad-hoc' or b['notarized'] is not False:raise ValueError('Invalid build provenance')
 required={'square-white-private-mascot','fixed-light-dock','pane-fullscreen-restore','screen-capturekit-module','static-update-channel','verified-update-installer'}
 if not required.issubset(set(b['tests'])) or b['wallet']['network']!='sepolia-only' or b['wallet']['audited'] is not False or b['globalCapture']['systemPicker'] is not True:raise ValueError('Invalid feature boundary')
 checks={}
 for line in (OUT/'SHA256SUMS.txt').read_text().splitlines():
  digest,name=line.split(maxsplit=1)
  if name not in PIN or name in checks or digest!=PIN[name][1]:raise ValueError('Wrong declared checksum')
  data=(OUT/name).read_bytes()
  if len(data)!=PIN[name][0] or sha(data)!=digest:raise ValueError('Wrong package bytes')
  checks[name]=digest
 if len(checks)!=2:raise ValueError('Missing package checksum')
 shutil.copyfile(OUT/DMG,OUT/ALIAS);checks[ALIAS]=checks[DMG]
 (OUT/'SHA256SUMS.txt').write_text(''.join(f'{digest}  {name}\n' for name,digest in sorted(checks.items())))
 for remote,local in [('tools/quadro-verify.py','quadro-verify.py'),('tools/mouse-update-verify.py','mouse-update-verify.py'),('desktop/mouse-install-update.cjs','mouse-install-update.cjs'),('desktop/quadro-update.cjs','quadro-update.cjs')]:
  obj=api(SOURCE,f'contents/{remote}?ref={HEAD}');(OUT/local).write_bytes(base64.b64decode(obj['content']))
 notes=(ROOT/'staging/mouse/6.0.8-arm64/RELEASE_NOTES.md').read_text()
 notes+=f'\n\nSource: https://github.com/{SOURCE}/commit/{HEAD}\nSource tests: https://github.com/{SOURCE}/actions/runs/{RUN}\nInstalled DMG tests: https://github.com/{REPO}/actions/runs/{os.environ["GITHUB_RUN_ID"]}\n\nSHA-256:\n```\n'+(OUT/'SHA256SUMS.txt').read_text()+'```\n'
 (OUT/'RELEASE_NOTES.md').write_text(notes)
 print('MOUSE608_EXACT_SOURCE_BYTES_IMPORTED',flush=True)
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
 smoke=(OUT/'quadro-smoke-write.log').read_text()
 for m in ['MOUSE_608_WHITE_SQUARE_PIXELS_AND_FIXED_DOCK_PASS','MOUSE_608_PANE_FULLSCREEN_RESTORE_NO_RELOAD_PASS','MOUSE_608_NATIVE_SCK_STILL_CAPTURE_PASS','QUADRO_ARM64_SMOKE_PASS']:
  if m not in smoke:raise ValueError('Missing native verification: '+m)
 if 'MOUSE_608_REAL_607_TO_608_REPLACE_RELAUNCH_PROFILE_PASS' not in (OUT/'mouse-update-roundtrip.log').read_text():raise ValueError('Real replacement check missing')
 found=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]
 if len(found)>1:raise ValueError('Ambiguous release')
 r=api(REPO,'releases/'+str(found[0]['id'])) if found else api(REPO,'releases','POST',{'tag_name':TAG,'target_commitish':os.environ['GITHUB_SHA'],'name':'Mouse Browser 6.0.8 — скриншоты, окна и обновление','body':(OUT/'RELEASE_NOTES.md').read_text(),'draft':True,'prerelease':True,'make_latest':'false'})
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
 print('MOUSE608_PUBLIC_RELEASE_HASHES_PASS',flush=True)
def channel():
 r=published();a=next(a for a in r['assets'] if a['name']==DMG)
 data={'schema':1,'platform':'darwin','arch':'arm64','version':V,'url':a['browser_download_url'],'size':a['size'],'digest':a['digest'],'publishedAt':r['published_at']}
 p='contents/channels/mouse/macos-arm64.json';old=api(REPO,p+'?ref=main',missing=True)
 if old:
  previous=json.loads(base64.b64decode(old['content']))
  if tuple(map(int,previous['version'].split('.')))>tuple(map(int,V.split('.'))):raise ValueError('Refusing channel downgrade')
  if previous['version']==V:
   if any(previous.get(k)!=v for k,v in data.items()):raise ValueError('Same-version channel differs; refusing overwrite')
   print('MOUSE608_CHANNEL_ALREADY_PUBLISHED',flush=True);return
 payload={'message':'Publish verified Mouse Browser 6.0.8 static macOS update channel','branch':'main','content':base64.b64encode((json.dumps(data,indent=2)+'\n').encode()).decode()}
 if old:payload['sha']=old['sha']
 api(REPO,p,'PUT',payload)
 (OUT/'CHANNEL_RESULT.json').write_text(json.dumps(data,indent=2)+'\n')
 print('MOUSE608_STATIC_CHANNEL_PUBLISHED',flush=True)
if __name__=='__main__':
 actions={'import':import_candidate,'publish':publish,'channel':channel}
 if len(sys.argv)!=2 or sys.argv[1] not in actions:raise SystemExit('Usage: mouse608-release.py import|publish|channel')
 actions[sys.argv[1]]()
