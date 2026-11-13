"""Import only the successful, merged, exact-source Mac full-width candidate."""
import base64, hashlib, io, json, os, pathlib, re, subprocess, zipfile
SOURCE='jeep-jim/OSMINOG'
ROOT=pathlib.Path(__file__).resolve().parents[1]
request=json.loads((ROOT/'staging/macos/5.0.3-arm64/import.json').read_text())
head=request['sourceCommit'];run_id=int(request['runId']);version='5.0.3'
if not re.fullmatch('[0-9a-f]{40}',head): raise ValueError('Invalid source SHA')
if request['version']!=version or request['tag']!='macos-v5.0.3-arm64': raise ValueError('Invalid release identity')
def api(path):return json.loads(subprocess.check_output(['gh','api',f'repos/{SOURCE}/{path}']))
run=api(f'actions/runs/{run_id}')
if (run['workflow_id']!=417071662 or run['head_sha']!=head or run['status']!='completed' or run['conclusion']!='success'):raise ValueError('Exact Mac candidate has not passed')
pr=api('pulls/129')
if not pr.get('merged') or pr['head']['sha']!=head or pr['base']['ref']!='main':raise ValueError('Verified source is not merged')
comparison=api(f'compare/{head}...main')
if comparison['status'] not in ['ahead','identical'] or comparison['behind_by']!=0:raise ValueError('Verified head is not an ancestor of main')
artifacts=api(f'actions/runs/{run_id}/artifacts')['artifacts']
matched=[a for a in artifacts if a['name']=='macos-arm64-candidate' and not a['expired']]
if len(matched)!=1:raise ValueError('Expected candidate missing or duplicated')
artifact=matched[0]
archive=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{artifact["id"]}/zip'])
if len(archive)>1024**3:raise ValueError('Oversized archive')
if not artifact.get('digest') or artifact['digest']!='sha256:'+hashlib.sha256(archive).hexdigest():raise ValueError('Artifact digest mismatch')
out=ROOT/'macos-release';out.mkdir(exist_ok=True)
expected={'Trader-OS-5.0.3-mac-arm64.dmg','Trader-OS-5.0.3-mac-arm64.zip','SHA256SUMS.txt','macos-build.json'}
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    entries=z.infolist()
    if {x.filename for x in entries}!=expected or len(entries)!=len(expected):raise ValueError('Unexpected artifact entries')
    if sum(x.file_size for x in entries)>1024**3:raise ValueError('Expanded archive too large')
    for item in entries:
        if item.is_dir() or (item.external_attr>>16)&0o170000==0o120000:raise ValueError('Unexpected artifact object')
        (out/item.filename).write_bytes(z.read(item))
build=json.loads((out/'macos-build.json').read_text())
if (build['source']!=head or int(build['runId'])!=run_id or build['version']!=version or build['arch']!='arm64' or build['platform']!='darwin' or build['signing']!='ad-hoc' or build['notarized'] is not False):raise ValueError('Wrong packaged build provenance')
if not {'fullwidth-1-2-4-6','no-tab-reload'}.issubset(set(build['tests'])):raise ValueError('Missing full-width verification')
checks={}
for line in (out/'SHA256SUMS.txt').read_text().splitlines():
    value,name=line.split(maxsplit=1)
    if name not in expected or not name.endswith(('.dmg','.zip')) or name in checks:raise ValueError('Unexpected checksum entry')
    if not re.fullmatch('[0-9a-f]{64}',value) or hashlib.sha256((out/name).read_bytes()).hexdigest()!=value:raise ValueError('Package checksum mismatch')
    checks[name]=value
if len(checks)!=2:raise ValueError('Missing package checksums')
verifier=api(f'contents/tools/verify-macos.py?ref={head}')
(out/'verify-macos.py').write_bytes(base64.b64decode(verifier['content']))
notes=f'''# Trader OS 5.0.3 — macOS Apple Silicon preview

Отдельная нативная arm64-сборка для Mac с Apple Silicon, включая M1 Pro. Требуется macOS13 или новее. Trader OS — актуальное продолжение настольного браузера «Осьминог».

**Закрытие ИИ справа теперь освобождает всю ширину:** вкладки растягиваются до правого края без пустой колонки. Работают крестик и кнопка AI; повторное открытие возвращает боковую панель. Сайты при этом не перезагружаются. Проверены раскладки1/2/4/6 при ширине1440/1100/900 с настоящими WebContentsView, а не только CSS-макетом.

Установка: скачайте DMG, откройте его, перетащите Trader OS в Applications / «Программы», запустите оттуда. При предупреждении о непроверенном разработчике после попытки запуска откройте «Системные настройки → Конфиденциальность и безопасность → Всё равно открыть». Не отключайте защиту macOS глобально.

**Preview с ad-hoc подписью: без Developer ID и без Apple notarization.** Обновления устанавливаются вручную через новый DMG. Профиль: `~/Library/Application Support/Trader OS`.

Дополнительно проверены нативная навигация, IPC, буфер обмена, Dock, сохранение локальных данных после повторного запуска и обычный запуск без тестовых флагов. Проверки CI не подтверждают работу на Mac владельца или авторизацию в его личных аккаунтах. Windows, Android, Chrome и АвтоЦена не публиковались и их каналы не менялись.

Source: https://github.com/{SOURCE}/commit/{head}
Source verification: https://github.com/{SOURCE}/actions/runs/{run_id}
DMG installation verification: https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/{os.environ['GITHUB_RUN_ID']}

SHA-256:
```
{(out/'SHA256SUMS.txt').read_text().strip()}
```
'''
(out/'RELEASE_NOTES.md').write_text(notes)
print(json.dumps({'source':head,'sourceRun':run_id,'artifact':artifact['id'],'checksums':checks},indent=2))
