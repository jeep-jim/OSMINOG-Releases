"""Gate the icon-only Mouse 6.0.7 candidate and publish immutable verified bytes."""
import base64,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,urllib.parse,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE='jeep-jim/OSMINOG';REPO='jeep-jim/OSMINOG-Releases';VERSION='6.0.7';TAG='quadro-macos-v6.0.7-arm64'
out=ROOT/'mouse607-release'
request=json.loads((ROOT/'staging/quadro/6.0.7-arm64/import.json').read_text())
head=request['sourceCommit'];run_id=int(request['runId'])
if not re.fullmatch('[0-9a-f]{40}',head) or request['version']!=VERSION or request['tag']!=TAG or request['sourcePR']!=139:raise ValueError('Invalid pinned release request')
def api(repo,p,method='GET',payload=None):
 cmd=['gh','api',f'repos/{repo}/{p}','--method',method]
 if payload is not None:cmd+=['--input','-']
 return json.loads(subprocess.check_output(cmd,input=json.dumps(payload).encode() if payload is not None else None))
def digest(file):return hashlib.sha256(file.read_bytes()).hexdigest()
primary=f'Mouse-Browser-{VERSION}-mac-arm64.dmg';archive_name=f'Mouse-Browser-{VERSION}-mac-arm64.zip';alias=f'Quadro-Browser-{VERSION}-mac-arm64.dmg'
names=[primary,archive_name,alias,'SHA256SUMS.txt','quadro-build.json']
def import_candidate():
 run=api(SOURCE,f'actions/runs/{run_id}')
 if run['workflow_id']!=417128557 or run['head_sha']!=head or run['status']!='completed' or run['conclusion']!='success':raise ValueError('Exact native candidate has not passed')
 pr=api(SOURCE,'pulls/139')
 if not pr.get('merged') or pr['head']['sha']!=head or pr['base']['ref']!='main':raise ValueError('Exact source PR139 is not merged')
 comparison=api(SOURCE,f'compare/{head}...main')
 if comparison['status'] not in ['ahead','identical'] or comparison['behind_by']!=0:raise ValueError('Source is not an ancestor of main')
 items=[a for a in api(SOURCE,f'actions/runs/{run_id}/artifacts')['artifacts'] if a['name']=='quadro-arm64-candidate' and not a['expired']]
 if len(items)!=1:raise ValueError('Candidate missing or ambiguous')
 artifact=items[0];archive=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{artifact["id"]}/zip'])
 if len(archive)>1024**3 or artifact.get('digest')!='sha256:'+hashlib.sha256(archive).hexdigest():raise ValueError('Artifact size/digest mismatch')
 expected={primary,archive_name,'SHA256SUMS.txt','quadro-build.json'};out.mkdir(exist_ok=True)
 with zipfile.ZipFile(io.BytesIO(archive)) as z:
  entries=z.infolist()
  if len(entries)!=4 or {e.filename for e in entries}!=expected or sum(e.file_size for e in entries)>1024**3:raise ValueError('Unexpected package entries')
  for entry in entries:
   if entry.is_dir() or (entry.external_attr>>16)&0o170000==0o120000:raise ValueError('Unexpected object type')
   (out/entry.filename).write_bytes(z.read(entry))
 build=json.loads((out/'quadro-build.json').read_text())
 if build['source']!=head or int(build['runId'])!=run_id or build['version']!=VERSION or build['productName']!='Mouse Browser' or build['platform']!='darwin' or build['arch']!='arm64' or build['signing']!='ad-hoc' or build['notarized'] is not False:raise ValueError('Wrong package provenance')
 required={'installed-icns-dock-ui-private-tail-left','private-memory-isolation','private-cleanup-disk-scan','native-apple-menu-preserved'}
 if not required.issubset(set(build['tests'])):raise ValueError('Missing required test scope')
 if build['wallet']['network']!='sepolia-only' or build['wallet']['audited'] is not False or build['globalCapture']['requiresScreenPermission'] is not True:raise ValueError('Feature boundary changed')
 checks={}
 for line in (out/'SHA256SUMS.txt').read_text().splitlines():
  value,name=line.split(maxsplit=1)
  if name not in {primary,archive_name} or name in checks or not re.fullmatch('[0-9a-f]{64}',value) or digest(out/name)!=value:raise ValueError('Invalid package checksum')
  checks[name]=value
 if len(checks)!=2:raise ValueError('Missing checksum')
 shutil.copyfile(out/primary,out/alias);checks[alias]=checks[primary]
 (out/'SHA256SUMS.txt').write_text(''.join(f'{v}  {n}\n' for n,v in sorted(checks.items())))
 verifier=api(SOURCE,f'contents/tools/quadro-verify.py?ref={head}')
 (out/'quadro-verify.py').write_bytes(base64.b64decode(verifier['content']))
 notes=f'''# Mouse Browser 6.0.7 — исправлено направление мыши

Точечное исправление по эталону владельца: хвост мыши направлен **влево**. Исходный пиксельный рисунок не перерисован: применено однократное горизонтальное отражение без изменения формы, цветов и числа пикселей.

Исправлены настоящая иконка Mac-приложения (.icns для Finder/установщика), светлый и тёмный Dock, логотипы интерфейса и маскот с очками в инкогнито. В сборке проверяется направление каждого пикселя PNG, иконки из готового .app и отрисованного приватного SVG. Новый файл mouse-607-installed-app-icon.png в проверочных артефактах извлечён из реальной иконки .icns.

Другие функции и профиль не менялись относительно 6.0.6. HTTP403 канала обновления, дополнительная системная полоса и favicon во всех списках (issue138) этим патчем не исправляются. Используйте прямой DMG при ошибке кнопки обновления.

Mac Apple Silicon, включая M1 Pro; macOS13+. Предварительная сборка ad-hoc, без Developer ID и нотариализации Apple. Закройте Mouse/Quadro через Cmd+Q, откройте DMG, скопируйте Mouse Browser.app в «Программы» с заменой и запустите оттуда. Не удаляйте ~/Library/Application Support/Trader OS. Старый Quadro с другим именем не заменяется автоматически; обе версии одновременно не запускайте. Файлы Quadro-Browser и Mouse-Browser в этом выпуске побайтово равны, первое имя сохранено только для совместимости старой кнопки обновления.

Инкогнито по-прежнему очищает локальную временную сессию, но не обещает анонимности или стирания RAM/swap; явно сохранённые файлы остаются. Кошелёк — только экспериментальная Sepolia, без аудита и не для настоящих средств. Глобальный скриншот требует запущенного приложения и разрешения macOS. Другие платформы/АвтоЦена не публиковались. CI Mac не является проверкой на компьютере владельца.

Source: https://github.com/{SOURCE}/commit/{head}
Native source verification: https://github.com/{SOURCE}/actions/runs/{run_id}
Installed DMG verification: https://github.com/{REPO}/actions/runs/{os.environ['GITHUB_RUN_ID']}

SHA-256:
```
{(out/'SHA256SUMS.txt').read_text().strip()}
```
'''
 (out/'RELEASE_NOTES.md').write_text(notes)
 print(json.dumps({'source':head,'runId':run_id,'artifactId':artifact['id'],'sha256':checks},indent=2))
def publish():
 local={n:{'size':(out/n).stat().st_size,'digest':'sha256:'+digest(out/n)} for n in names}
 if local[primary]!=local[alias]:raise ValueError('Alias is not identical')
 def verify(release):
  assets={a['name']:a for a in release['assets']}
  if set(assets)!=set(names):raise ValueError('Unexpected remote assets')
  for n,v in local.items():
   if assets[n]['state']!='uploaded' or assets[n]['size']!=v['size'] or assets[n].get('digest')!=v['digest']:raise ValueError('Remote digest mismatch: '+n)
  return assets
 existing=[r for r in api(REPO,'releases?per_page=100') if r['tag_name']==TAG]
 if len(existing)>1:raise ValueError('Ambiguous release')
 release=api(REPO,'releases/'+str(existing[0]['id'])) if existing else api(REPO,'releases','POST',{'tag_name':TAG,'target_commitish':os.environ['GITHUB_SHA'],'name':'Mouse Browser 6.0.7 — исправлено направление мыши','body':(out/'RELEASE_NOTES.md').read_text(),'draft':True,'prerelease':True,'make_latest':'false'})
 rid=release['id']
 if release['draft']:
  assets={a['name']:a for a in release['assets']}
  for n in names:
   if n in assets:
    if assets[n]['size']!=local[n]['size'] or assets[n].get('digest')!=local[n]['digest']:raise ValueError('Refusing existing byte overwrite')
    continue
   url=f'https://uploads.github.com/repos/{REPO}/releases/{rid}/assets?name='+urllib.parse.quote(n,safe='')
   req=urllib.request.Request(url,data=(out/n).read_bytes(),method='POST',headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Content-Type':'application/octet-stream','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
   with urllib.request.urlopen(req,timeout=180) as response:json.load(response)
  verify(api(REPO,'releases/'+str(rid)));print('MOUSE_607_REMOTE_ASSETS_VERIFIED',flush=True)
  api(REPO,'releases/'+str(rid),'PATCH',{'draft':False,'prerelease':True,'make_latest':'false','body':(out/'RELEASE_NOTES.md').read_text()})
 release=api(REPO,'releases/'+str(rid));assets=verify(release)
 if release['draft'] or not release['published_at']:raise ValueError('Not published')
 result={'id':rid,'publishedAt':release['published_at'],'url':release['html_url'],'assets':[{k:a[k] for k in ['name','size','digest','browser_download_url']} for a in assets.values()]}
 (out/'RELEASE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));print('MOUSE_607_PUBLISHED_PASS',flush=True)
if sys.argv[1:] == ['import']:import_candidate()
elif sys.argv[1:] == ['publish']:publish()
else:raise SystemExit('Use import or publish')
