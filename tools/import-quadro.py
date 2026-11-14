"""Import a successful exact-head Quadro candidate. No other channel is modified."""
import base64,hashlib,io,json,os,pathlib,re,subprocess,zipfile
SOURCE='jeep-jim/OSMINOG';ROOT=pathlib.Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'staging/quadro/6.0.3-arm64/import.json').read_text())
head=r['sourceCommit'];run_id=int(r['runId'])
if not re.fullmatch('[0-9a-f]{40}',head) or r['version']!='6.0.3' or r['tag']!='quadro-macos-v6.0.3-arm64':raise ValueError('Invalid release request')
def api(p):return json.loads(subprocess.check_output(['gh','api',f'repos/{SOURCE}/{p}']))
run=api(f'actions/runs/{run_id}')
if run['workflow_id']!=417128557 or run['head_sha']!=head or run['status']!='completed' or run['conclusion']!='success':raise ValueError('Exact Quadro candidate has not passed')
pr=api('pulls/133')
if not pr.get('merged') or pr['head']['sha']!=head or pr['base']['ref']!='main':raise ValueError('Verified source PR133 is not merged')
c=api(f'compare/{head}...main')
if c['status'] not in ['ahead','identical'] or c['behind_by']!=0:raise ValueError('Exact source is not an ancestor of main')
items=[a for a in api(f'actions/runs/{run_id}/artifacts')['artifacts'] if a['name']=='quadro-arm64-candidate' and not a['expired']]
if len(items)!=1:raise ValueError('Ambiguous or expired candidate')
a=items[0];archive=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{a["id"]}/zip'])
if len(archive)>1024**3 or a.get('digest')!='sha256:'+hashlib.sha256(archive).hexdigest():raise ValueError('Artifact digest/size mismatch')
out=ROOT/'quadro-release';out.mkdir(exist_ok=True)
names={'Quadro-Browser-6.0.3-mac-arm64.dmg','Quadro-Browser-6.0.3-mac-arm64.zip','SHA256SUMS.txt','quadro-build.json'}
with zipfile.ZipFile(io.BytesIO(archive)) as z:
 entries=z.infolist()
 if len(entries)!=4 or {x.filename for x in entries}!=names or sum(x.file_size for x in entries)>1024**3:raise ValueError('Unexpected package entries')
 for item in entries:
  if item.is_dir() or (item.external_attr>>16)&0o170000==0o120000:raise ValueError('Unexpected package type')
  (out/item.filename).write_bytes(z.read(item))
b=json.loads((out/'quadro-build.json').read_text())
if b['source']!=head or int(b['runId'])!=run_id or b['version']!='6.0.3' or b['platform']!='darwin' or b['arch']!='arm64' or b['signing']!='ad-hoc' or b['notarized'] is not False:raise ValueError('Wrong build provenance')
checks={}
for line in (out/'SHA256SUMS.txt').read_text().splitlines():
 value,name=line.split(maxsplit=1)
 if name not in names or not name.endswith(('.dmg','.zip')) or name in checks or not re.fullmatch('[a-f0-9]{64}',value):raise ValueError('Invalid checksum entry')
 if hashlib.sha256((out/name).read_bytes()).hexdigest()!=value:raise ValueError('Package digest mismatch')
 checks[name]=value
if len(checks)!=2:raise ValueError('Missing checksum')
for remote,local in [('tools/quadro-verify.py','quadro-verify.py'),('desktop/quadro-update.cjs','quadro-update.cjs')]:
 data=api(f'contents/{remote}?ref={head}');(out/local).write_bytes(base64.b64decode(data['content']))
notes=f'''# Quadro Browser 6.0.3 — история, подсказки и загрузки

Mac Apple Silicon, включая M1 Pro; macOS13+. Предварительный выпуск, подпись ad-hoc, без Developer ID и нотариализации Apple. Прежняя зелёно-розовая иконка не изменена.

## Интерфейс
Нижняя панель разделена: слева название/язык/тема/настройки/камера/раскладка и история/закладки/загрузки; справа ИИ, кошелёк, обновление и выход. Зелёная точка включает/выключает настоящий полноэкранный режим. Постоянная пустая полоса над вкладками убрана. Точки всегда видимы, окрашиваются при наведении. Компактные строки окон, favicon и регулируемые разделители сохранены.

Крестик редактора скриншота закрывает редактор и возвращает страницы; отключена область перетаскивания окна под модальным крестиком. Esc сначала закрывает диалог. Ошибающаяся кнопка «Экран Mac» удалена из редактора; снимки области браузера, Control+A, разметка, копирование и PNG сохранены. Системный захват рабочего стола не выдается за работающую функцию этого интерфейса.

## Обычные функции браузера
- Подсказки при вводе адреса: из локальной истории, сохранённых запросов и закладок, выбор мышью или стрелками/Enter. Вводимые символы не отправляются внешнему сервису подсказок.
- История с датами, поиском, удалением записей и подтверждаемой очисткой; отдельный список поисковых запросов. Новая история начинается с этой версии, прежняя не восстанавливается из несуществующих записей.
- Закладки: звезда в строке окна / Cmd+D; закрытую вкладку можно вернуть Cmd+Shift+T. История Cmd+Y; загрузки Cmd+Shift+J.
- Загрузки: выбор места сохранения, прогресс, пауза/продолжение, отмена/повтор, открытие файла с подтверждением, показ в Finder. Удаление записи не удаляет файл. Продолжение зависит от сервера; после перезапуска незавершённое отмечается прерванным и доступен повтор.

Данные хранятся только в существующем локальном профиле. Это базовые функции, не заявление полной совместимости с Safari/Chrome: парольный менеджер, облачная синхронизация и любые расширения не добавлены. Кошелёк по-прежнему только для публичных адресов.

## Обновление
«Обновить» → «Скачать обновление» → «Открыть установщик». Завершите старую версию через Cmd+Q и замените Quadro Browser в «Программах». Замена приложения пока ручная. Не удаляйте `~/Library/Application Support/Trader OS`.

Проверено на CI Apple Silicon и повторно после установки из настоящего DMG: старые регрессии окон/ИИ/скриншотов/тем/сохранения, новые подсказки/история/закладки, фактический файл загрузки и pause/resume, mouse-click крестика редактора в обычном/fullscreen, fullscreen без искусственного отступа, закрытие и перезапуск с профилем. Локальные fixtures не доказывают работу всех сайтов и всех вариантов системного меню/выреза на Mac владельца. Пользовательское разрешение экрана не обходится. Другие проекты/платформы не публиковались.

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
