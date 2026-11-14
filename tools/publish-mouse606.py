"""Publish verified Mouse bytes; reject overwrites or unexpected release assets."""
import hashlib,json,os,pathlib,subprocess,urllib.parse,urllib.request
REPO='jeep-jim/OSMINOG-Releases';TAG='quadro-macos-v6.0.6-arm64';root=pathlib.Path('mouse-release')
names=['Mouse-Browser-6.0.6-mac-arm64.dmg','Mouse-Browser-6.0.6-mac-arm64.zip','Quadro-Browser-6.0.6-mac-arm64.dmg','SHA256SUMS.txt','quadro-build.json']
local={n:{'size':(root/n).stat().st_size,'digest':'sha256:'+hashlib.sha256((root/n).read_bytes()).hexdigest()} for n in names}
assert local[names[0]]==local[names[2]],'Legacy alias must have identical bytes'
notes=(root/'RELEASE_NOTES.md').read_text()
notes=notes.replace('Убрана лишняя собственная полоса/titlebar; место под настоящее меню определяется его видимостью и измеренной геометрией, не фиксированным пустым отступом.','Убран прежний фиксированный отступ; место под настоящее меню определяется его видимостью и измеренной геометрией. Полное устранение дополнительной нативной полосы при раскрытии меню пока не подтверждено: на проверочном кадре она ещё видна над вкладками.')
notes+='\n\n## Незакрытые замечания этого preview\n\n- Задача #138 о favicon во всех строках истории/закладок/загрузок и после перезапуска остаётся открытой. Нынешняя сборка не выдаётся за её полную реализацию.\n- Настоящее меню Apple снова доступно, однако на тестовом снимке mouse-606-system-menu.png видна дополнительная нативная полоса. Проверка menuVisible=true доказывает доступность меню, а не отсутствие любой перекрывающей полосы во время раскрытия. Этот визуальный дефект остаётся на доработке.\n- HTTP 403 при проверке обновлений наблюдался у владельца. Причина на его Mac не установлена; этот выпуск не содержит подтверждённого исправления доступности GitHub API. Прямая ссылка на DMG не использует кнопку обновления.\n'
(root/'RELEASE_NOTES.md').write_text(notes)
def api(p,method='GET',payload=None):
 cmd=['gh','api',f'repos/{REPO}/{p}','--method',method]
 if payload is not None:cmd+=['--input','-']
 return json.loads(subprocess.check_output(cmd,input=json.dumps(payload).encode() if payload is not None else None))
def verify(release):
 assets={x['name']:x for x in release['assets']}
 if set(assets)!=set(names):raise ValueError('Unexpected remote assets')
 for n,v in local.items():
  if assets[n]['state']!='uploaded' or assets[n]['size']!=v['size'] or assets[n].get('digest')!=v['digest']:raise ValueError('Remote digest mismatch: '+n)
 return assets
existing=[x for x in api('releases?per_page=100') if x['tag_name']==TAG]
if len(existing)>1:raise ValueError('Ambiguous release')
release=api('releases/'+str(existing[0]['id'])) if existing else api('releases','POST',{'tag_name':TAG,'target_commitish':os.environ['GITHUB_SHA'],'name':'Mouse Browser 6.0.6 — Mac Apple Silicon','body':notes,'draft':True,'prerelease':True,'make_latest':'false'})
rid=release['id']
if release['draft']:
 assets={x['name']:x for x in release['assets']}
 for n in names:
  if n in assets:
   if assets[n]['size']!=local[n]['size'] or assets[n].get('digest')!=local[n]['digest']:raise ValueError('Existing draft bytes differ; refusing overwrite')
   continue
  url=f'https://uploads.github.com/repos/{REPO}/releases/{rid}/assets?name='+urllib.parse.quote(n,safe='')
  req=urllib.request.Request(url,data=(root/n).read_bytes(),method='POST',headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Content-Type':'application/octet-stream','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
  with urllib.request.urlopen(req,timeout=180) as response:json.load(response)
 release=api('releases/'+str(rid));verify(release);print('MOUSE_REMOTE_DIGESTS_AND_LEGACY_ALIAS_PASS',flush=True)
 release=api('releases/'+str(rid),'PATCH',{'draft':False,'prerelease':True,'make_latest':'false','body':notes})
release=api('releases/'+str(rid));assets=verify(release)
if release['draft'] or not release['published_at']:raise ValueError('Release not public')
result={'id':rid,'url':release['html_url'],'publishedAt':release['published_at'],'assets':[{k:a[k] for k in ['name','size','digest','browser_download_url']} for a in assets.values()]}
(root/'RELEASE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));print('MOUSE_PUBLISHED_PASS',flush=True)
