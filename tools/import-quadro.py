"""Import a successful exact-head Quadro candidate. No other channel is modified."""
import base64,hashlib,io,json,os,pathlib,re,subprocess,zipfile
SOURCE='jeep-jim/OSMINOG';ROOT=pathlib.Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'staging/quadro/6.0.2-arm64/import.json').read_text())
head=r['sourceCommit'];run_id=int(r['runId'])
if not re.fullmatch('[0-9a-f]{40}',head) or r['version']!='6.0.2' or r['tag']!='quadro-macos-v6.0.2-arm64':raise ValueError('Invalid release request')
def api(p):return json.loads(subprocess.check_output(['gh','api',f'repos/{SOURCE}/{p}']))
run=api(f'actions/runs/{run_id}')
if run['workflow_id']!=417128557 or run['head_sha']!=head or run['status']!='completed' or run['conclusion']!='success':raise ValueError('Exact Quadro candidate has not passed')
pr=api('pulls/132')
if not pr.get('merged') or pr['head']['sha']!=head or pr['base']['ref']!='main':raise ValueError('Verified source PR132 is not merged')
c=api(f'compare/{head}...main')
if c['status'] not in ['ahead','identical'] or c['behind_by']!=0:raise ValueError('Exact source is not an ancestor of main')
items=[a for a in api(f'actions/runs/{run_id}/artifacts')['artifacts'] if a['name']=='quadro-arm64-candidate' and not a['expired']]
if len(items)!=1:raise ValueError('Ambiguous or expired candidate')
a=items[0];archive=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{a["id"]}/zip'])
if len(archive)>1024**3 or a.get('digest')!='sha256:'+hashlib.sha256(archive).hexdigest():raise ValueError('Artifact digest/size mismatch')
out=ROOT/'quadro-release';out.mkdir(exist_ok=True)
names={'Quadro-Browser-6.0.2-mac-arm64.dmg','Quadro-Browser-6.0.2-mac-arm64.zip','SHA256SUMS.txt','quadro-build.json'}
with zipfile.ZipFile(io.BytesIO(archive)) as z:
 entries=z.infolist()
 if len(entries)!=4 or {x.filename for x in entries}!=names or sum(x.file_size for x in entries)>1024**3:raise ValueError('Unexpected package entries')
 for item in entries:
  if item.is_dir() or (item.external_attr>>16)&0o170000==0o120000:raise ValueError('Unexpected package type')
  (out/item.filename).write_bytes(z.read(item))
b=json.loads((out/'quadro-build.json').read_text())
if b['source']!=head or int(b['runId'])!=run_id or b['version']!='6.0.2' or b['platform']!='darwin' or b['arch']!='arm64' or b['signing']!='ad-hoc' or b['notarized'] is not False:raise ValueError('Wrong build provenance')
checks={}
for line in (out/'SHA256SUMS.txt').read_text().splitlines():
 value,name=line.split(maxsplit=1)
 if name not in names or not name.endswith(('.dmg','.zip')) or name in checks or not re.fullmatch('[a-f0-9]{64}',value):raise ValueError('Invalid checksum entry')
 if hashlib.sha256((out/name).read_bytes()).hexdigest()!=value:raise ValueError('Package digest mismatch')
 checks[name]=value
if len(checks)!=2:raise ValueError('Missing checksum')
for remote,local in [('tools/quadro-verify.py','quadro-verify.py'),('desktop/quadro-update.cjs','quadro-update.cjs')]:
 data=api(f'contents/{remote}?ref={head}');(out/local).write_bytes(base64.b64decode(data['content']))
notes=f'''# Quadro Browser 6.0.2 — управление и скриншоты

Mac Apple Silicon, включая M1 Pro; macOS 13+. Preview, подпись ad-hoc, без Developer ID/notarization.

## Интерфейс
- Возвращена прежняя зелёно-розовая иконка: использован исходный генератор без изменения геометрии и цветов. Название Quadro Browser сохранено.
- Три точки управления постоянно видны слева; становятся цветными при наведении. Зелёная максимизирует обычное окно без системной полноэкранной шторки. Для отдельного native fullscreen оставлен безопасный верхний отступ. Сохранено корректное завершение с сохранением данных.
- Синяя рамка активной плитки убрана. В каждом окне своя компактная панель28px: навигация, favicon, название, адрес и управление разделением. Favicon также показаны у вкладок.
- Название, язык RU/EN, тема, настройки и скриншот собраны рядом в нижней панели. Умеренные стеклянные поверхности; масштабирование плиток и ИИ сохранено.

## Скриншот
Нажмите иконку камеры или **Control+A** при активном браузере/его странице. Выделите область; затем доступны стрелка, линия, текст, круг, прямоугольник, карандаш, маркер, цвет и толщина. Есть отмена/повтор, копирование изображения и сохранение PNG. Cmd+A по-прежнему выделяет текст. Сочетание не перехватывается глобально в других приложениях.

Обычный снимок включает реальные пиксели страниц браузера, включая native webviews. Кнопка «Экран Mac» отдельно запрашивает снимок дисплея текущего окна; macOS может потребовать разрешение записи экрана. Разрешение не обходится. Снимки обрабатываются локально, не передаются в ИИ/облако; файл сохраняется только по явному выбору пользователя.

## Обновление
«Обновить» → «Скачать обновление» → «Открыть установщик». Завершите старую версию через Cmd+Q и перетащите Quadro Browser в «Программы» с заменой. Автоматическая замена пока не включена. Не удаляйте `~/Library/Application Support/Trader OS`: это прежний профиль.

Проверки CI выполняются на тестовых Mac с локальными сайтами: панели/перетаскивание/ИИ/контраст/сохранение профиля, favicon, RU/EN, фактический Control+A, выделение и все инструменты, равенство пикселей clipboard/PNG, fullscreen inset и закрытие. Эти проверки не подтверждают личные аккаунты, все сайты, экранное TCC-разрешение или запуск на Mac владельца. Кошелёк остаётся только для публичных адресов; MetaMask signing не заявляется. Другие платформы и АвтоЦена не публиковались.

Source: https://github.com/{SOURCE}/commit/{head}
Source tests: https://github.com/{SOURCE}/actions/runs/{run_id}
DMG verification: https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/{os.environ['GITHUB_RUN_ID']}

SHA-256:
```
{(out/'SHA256SUMS.txt').read_text().strip()}
```
'''
(out/'RELEASE_NOTES.md').write_text(notes)
print(json.dumps({'source':head,'runId':run_id,'artifactId':a['id'],'sha256':checks},indent=2))
