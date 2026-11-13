"""Import only the successful, merged, exact-source Apple Silicon candidate."""
import base64, hashlib, io, json, pathlib, re, subprocess, zipfile
SOURCE='jeep-jim/OSMINOG'
ROOT=pathlib.Path(__file__).resolve().parents[1]
request=json.loads((ROOT/'staging/macos/5.0.2-arm64/import.json').read_text())
head=request['sourceCommit'];run_id=int(request['runId'])
if not re.fullmatch('[0-9a-f]{40}',head): raise ValueError('Invalid source SHA')
if request['version']!='5.0.2' or request['tag']!='macos-v5.0.2-arm64': raise ValueError('Invalid release identity')
def api(path):return json.loads(subprocess.check_output(['gh','api',f'repos/{SOURCE}/{path}']))
run=api(f'actions/runs/{run_id}')
if (run['workflow_id']!=417071662 or run['head_sha']!=head or run['status']!='completed' or run['conclusion']!='success'):raise ValueError('Exact Mac candidate has not passed')
pr=api('pulls/128')
if not pr.get('merged') or pr['head']['sha']!=head or pr['base']['ref']!='main':raise ValueError('Verified source is not merged')
comparison=api(f'compare/{head}...main')
if comparison['status'] not in ['ahead','identical'] or comparison['behind_by']!=0:raise ValueError('Verified head is not an ancestor of main')
artifacts=api(f'actions/runs/{run_id}/artifacts')['artifacts']
matched=[a for a in artifacts if a['name']=='macos-arm64-candidate' and not a['expired']]
if len(matched)!=1:raise ValueError('Expected candidate missing or duplicated')
artifact=matched[0]
archive=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{artifact["id"]}/zip'])
if len(archive)>1024**3:raise ValueError('Oversized archive')
if artifact.get('digest') and artifact['digest']!='sha256:'+hashlib.sha256(archive).hexdigest():raise ValueError('Artifact digest mismatch')
out=ROOT/'macos-release';out.mkdir(exist_ok=True)
expected={'Trader-OS-5.0.2-mac-arm64.dmg','Trader-OS-5.0.2-mac-arm64.zip','SHA256SUMS.txt','macos-build.json'}
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    entries=z.infolist()
    if {x.filename for x in entries}!=expected or len(entries)!=len(expected):raise ValueError('Unexpected artifact entries')
    if sum(x.file_size for x in entries)>1024**3:raise ValueError('Expanded archive too large')
    for item in entries:
        if item.is_dir() or (item.external_attr>>16)&0o170000==0o120000:raise ValueError('Unexpected artifact object')
        (out/item.filename).write_bytes(z.read(item))
build=json.loads((out/'macos-build.json').read_text())
if (build['source']!=head or int(build['runId'])!=run_id or build['version']!='5.0.2' or build['arch']!='arm64' or build['platform']!='darwin' or build['signing']!='ad-hoc' or build['notarized'] is not False):raise ValueError('Wrong packaged build provenance')
checks={}
for line in (out/'SHA256SUMS.txt').read_text().splitlines():
    value,name=line.split(maxsplit=1)
    if name not in expected or not name.endswith(('.dmg','.zip')) or name in checks:raise ValueError('Unexpected checksum entry')
    if not re.fullmatch('[0-9a-f]{64}',value) or hashlib.sha256((out/name).read_bytes()).hexdigest()!=value:raise ValueError('Package checksum mismatch')
    checks[name]=value
if len(checks)!=2:raise ValueError('Missing package checksums')
# Download the test runner from the exact reviewed source, never from a moving branch.
verifier=api(f'contents/tools/verify-macos.py?ref={head}')
(out/'verify-macos.py').write_bytes(base64.b64decode(verifier['content']))
notes=f'''# Trader OS 5.0.2 — macOS Apple Silicon preview

Первый отдельный выпуск для Mac с Apple Silicon, включая M1 Pro. Нативный arm64; macOS 13 или новее. Название Trader OS — актуальное продолжение проекта «Осьминог».

Установка: скачать DMG, открыть его, перетащить Trader OS в Applications / «Программы», запустить оттуда. При предупреждении о непроверенном разработчике: после попытки запуска открыть «Системные настройки → Конфиденциальность и безопасность → Всё равно открыть». Не отключать Gatekeeper глобально.

**Это preview с ad-hoc подписью, без Developer ID и без Apple notarization.** Автообновление пока выключено; новые DMG устанавливаются вручную. Профиль хранится отдельно в `~/Library/Application Support/Trader OS`.

Сохранены нативные вкладки и раскладки 1/2/4/6 актуальной Windows-версии. Добавлены меню macOS, Cmd-сочетания, отступ для кнопок окна и возврат окна из Dock. Windows, Android и Chrome каналы не изменены.

Проверено в CI на Apple Silicon: unit-тесты, настоящая навигация страницы, packaged smoke, копирование/вставка, Dock, сохранение данных после повторного запуска и обычный запуск без тестовых флагов. Это НЕ подтверждение запуска на Mac владельца или входа в его аккаунты; сайты могут иметь собственные ограничения.

Source: https://github.com/{SOURCE}/commit/{head}
Source verification: https://github.com/{SOURCE}/actions/runs/{run_id}
Release verification: https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/{{RELEASE_RUN}}

SHA-256:
```
{(out/'SHA256SUMS.txt').read_text().strip()}
```
'''
import os
(out/'RELEASE_NOTES.md').write_text(notes.replace('{RELEASE_RUN}',os.environ['GITHUB_RUN_ID']))
print(json.dumps({'source':head,'sourceRun':run_id,'artifact':artifact['id'],'checksums':checks},indent=2))
