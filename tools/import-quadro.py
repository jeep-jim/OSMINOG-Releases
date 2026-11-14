"""Import a successful exact-head Quadro candidate. No other channel is modified."""
import base64,hashlib,io,json,os,pathlib,re,subprocess,zipfile
SOURCE='jeep-jim/OSMINOG';ROOT=pathlib.Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'staging/quadro/6.0.4-arm64/import.json').read_text())
head=r['sourceCommit'];run_id=int(r['runId'])
if not re.fullmatch('[0-9a-f]{40}',head) or r['version']!='6.0.4' or r['tag']!='quadro-macos-v6.0.4-arm64':raise ValueError('Invalid release request')
def api(p):return json.loads(subprocess.check_output(['gh','api',f'repos/{SOURCE}/{p}']))
run=api(f'actions/runs/{run_id}')
if run['workflow_id']!=417128557 or run['head_sha']!=head or run['status']!='completed' or run['conclusion']!='success':raise ValueError('Exact Quadro candidate has not passed')
pr=api('pulls/135')
if not pr.get('merged') or pr['head']['sha']!=head or pr['base']['ref']!='main':raise ValueError('Verified source PR135 is not merged')
c=api(f'compare/{head}...main')
if c['status'] not in ['ahead','identical'] or c['behind_by']!=0:raise ValueError('Exact source is not an ancestor of main')
items=[a for a in api(f'actions/runs/{run_id}/artifacts')['artifacts'] if a['name']=='quadro-arm64-candidate' and not a['expired']]
if len(items)!=1:raise ValueError('Ambiguous or expired candidate')
a=items[0];archive=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{a["id"]}/zip'])
if len(archive)>1024**3 or a.get('digest')!='sha256:'+hashlib.sha256(archive).hexdigest():raise ValueError('Artifact digest/size mismatch')
out=ROOT/'quadro-release';out.mkdir(exist_ok=True)
names={'Quadro-Browser-6.0.4-mac-arm64.dmg','Quadro-Browser-6.0.4-mac-arm64.zip','SHA256SUMS.txt','quadro-build.json'}
with zipfile.ZipFile(io.BytesIO(archive)) as z:
 entries=z.infolist()
 if len(entries)!=4 or {x.filename for x in entries}!=names or sum(x.file_size for x in entries)>1024**3:raise ValueError('Unexpected package entries')
 for item in entries:
  if item.is_dir() or (item.external_attr>>16)&0o170000==0o120000:raise ValueError('Unexpected package type')
  (out/item.filename).write_bytes(z.read(item))
b=json.loads((out/'quadro-build.json').read_text())
if b['source']!=head or int(b['runId'])!=run_id or b['version']!='6.0.4' or b['platform']!='darwin' or b['arch']!='arm64' or b['signing']!='ad-hoc' or b['notarized'] is not False:raise ValueError('Wrong build provenance')
checks={}
for line in (out/'SHA256SUMS.txt').read_text().splitlines():
 value,name=line.split(maxsplit=1)
 if name not in names or not name.endswith(('.dmg','.zip')) or name in checks or not re.fullmatch('[a-f0-9]{64}',value):raise ValueError('Invalid checksum entry')
 if hashlib.sha256((out/name).read_bytes()).hexdigest()!=value:raise ValueError('Package digest mismatch')
 checks[name]=value
if len(checks)!=2:raise ValueError('Missing checksum')
for remote,local in [('tools/quadro-verify.py','quadro-verify.py'),('desktop/quadro-update.cjs','quadro-update.cjs')]:
 data=api(f'contents/{remote}?ref={head}');(out/local).write_bytes(base64.b64decode(data['content']))
notes=f'''# Quadro Browser 6.0.4 — меню и новая вкладка

Mac Apple Silicon, включая M1 Pro; macOS13+. Предварительный выпуск с ad-hoc подписью, без Developer ID и нотариализации Apple. Прежняя зелёно-розовая иконка, название и локальный профиль сохранены.

## Исправление нижнего меню
Меню, настройки, история, закладки, загрузки, кошелёк, обновление и скриншот больше не полагаются на разовое скрытие страниц. Пока открыт диалог, отдельные нативные поверхности страниц временно отсоединяются от окна и не могут перекрыть его при позднем обновлении раскладки. После закрытия возвращаются те же страницы без перезагрузки. Язык, число окон и выбор ИИ раскрываются через компактное меню с тем же механизмом. Это исправление проверено реальными кликами и проверкой порядка нативных поверхностей, а не только DOM click().

## Новая вкладка
- Кнопка + и Cmd+T открывают локальную стартовую страницу с визуальными плитками: иконка, название и переход на сайт в выбранном окне. Свободные окна также показывают эту страницу.
- «Добавить сайт» создаёт закладку; кнопка ⋯ у плитки позволяет изменить название/адрес или удалить её. Прежние закладки сохранены. Искусственный лимит1000 снят: коллекция не обрезается, большие списки выводятся порциями через «Показать ещё». Ёмкость устройства не бесконечна.
- «Недавно посещённые» заполняется из реальной локальной истории. Выдуманных или предустановленных посещений нет.
- «Настроить страницу» справа внизу самой новой вкладки: градиентные фоны, вариант без фона и собственное изображение PNG/JPEG/WebP. Копия изображения хранится только в прежнем локальном профиле. Можно скрыть недавние сайты. Закладки, фон и внутренние вкладки сохраняются после перезапуска.
- Системный шрифт, округлые плитки и умеренное стекло ориентированы на предоставленный пример Mac. Полная идентичность Safari не заявляется; встроенные фоны — градиенты, а не фотография из примера.

## Установка
Завершите текущий Quadro через Cmd+Q. Скачайте DMG этого выпуска и перетащите Quadro Browser в «Программы» с заменой. Полное удаление не требуется; не удаляйте `~/Library/Application Support/Trader OS`. Замена приложения остаётся ручной. У старой версии обнаружение новых выпусков через анонимный GitHub API ранее получало HTTP403; прямой DMG — независимый способ установки. Новое состояние проверки кнопки обновления отражается отдельным шагом release workflow и не подменяет тесты приложения.

Проверки:22 unit-теста, включая сохранение1305 закладок без обрезки; на CI Apple Silicon — все нижние диалоги и выпадающие списки, искусственно запоздавшие layout/resize, настоящие mouse clicks, отсутствие нативных страниц поверх меню, визуальная закладка и реальная навигация, реальные недавние сайты, собственный фон и сохранение после restart. Повторены прежние проверки окон/ИИ/скриншота/clipboard/PNG/истории/загрузок/закрытия и оригинальной иконки. Выбор файла в диалоге на Mac владельца, его сайты/авторизации и запуск новой версии на его устройстве не наблюдались; тестовые страницы не доказывают совместимость всех сайтов.

Windows, Chrome, Android и АвтоЦена не публиковались. Кошелёк остаётся только для публичных адресов, не MetaMask signing.

Source: https://github.com/{SOURCE}/commit/{head}
Source tests: https://github.com/{SOURCE}/actions/runs/{run_id}
Installed DMG tests: https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/{os.environ['GITHUB_RUN_ID']}

SHA-256:
```
{(out/'SHA256SUMS.txt').read_text().strip()}
```
'''
(out/'RELEASE_NOTES.md').write_text(notes)
print(json.dumps({'source':head,'runId':run_id,'artifactId':a['id'],'sha256':checks},indent=2))
