"""Import a successful exact-head Quadro candidate. No other channel is modified."""
import base64,hashlib,io,json,os,pathlib,re,subprocess,zipfile
SOURCE='jeep-jim/OSMINOG';ROOT=pathlib.Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'staging/quadro/6.0.0-arm64/import.json').read_text())
head=r['sourceCommit'];run_id=int(r['runId'])
if not re.fullmatch('[0-9a-f]{40}',head) or r['version']!='6.0.0' or r['tag']!='quadro-macos-v6.0.0-arm64':raise ValueError('Invalid release request')
def api(p):return json.loads(subprocess.check_output(['gh','api',f'repos/{SOURCE}/{p}']))
run=api(f'actions/runs/{run_id}')
if run['workflow_id']!=417128557 or run['head_sha']!=head or run['status']!='completed' or run['conclusion']!='success':raise ValueError('Exact Quadro candidate has not passed')
pr=api('pulls/130')
if not pr.get('merged') or pr['head']['sha']!=head or pr['base']['ref']!='main':raise ValueError('Verified source PR130 is not merged')
c=api(f'compare/{head}...main')
if c['status'] not in ['ahead','identical'] or c['behind_by']!=0:raise ValueError('Exact source is not an ancestor of main')
items=[a for a in api(f'actions/runs/{run_id}/artifacts')['artifacts'] if a['name']=='quadro-arm64-candidate' and not a['expired']]
if len(items)!=1:raise ValueError('Ambiguous or expired candidate')
a=items[0];archive=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{a["id"]}/zip'])
if len(archive)>1024**3 or a.get('digest')!='sha256:'+hashlib.sha256(archive).hexdigest():raise ValueError('Artifact digest/size mismatch')
out=ROOT/'quadro-release';out.mkdir(exist_ok=True)
names={'Quadro-Browser-6.0.0-mac-arm64.dmg','Quadro-Browser-6.0.0-mac-arm64.zip','SHA256SUMS.txt','quadro-build.json'}
with zipfile.ZipFile(io.BytesIO(archive)) as z:
 entries=z.infolist()
 if len(entries)!=4 or {x.filename for x in entries}!=names or sum(x.file_size for x in entries)>1024**3:raise ValueError('Unexpected package entries')
 for item in entries:
  if item.is_dir() or (item.external_attr>>16)&0o170000==0o120000:raise ValueError('Unexpected package type')
  (out/item.filename).write_bytes(z.read(item))
b=json.loads((out/'quadro-build.json').read_text())
if b['source']!=head or int(b['runId'])!=run_id or b['version']!='6.0.0' or b['platform']!='darwin' or b['arch']!='arm64' or b['signing']!='ad-hoc' or b['notarized'] is not False:raise ValueError('Wrong build provenance')
checks={}
for line in (out/'SHA256SUMS.txt').read_text().splitlines():
 value,name=line.split(maxsplit=1)
 if name not in names or not name.endswith(('.dmg','.zip')) or name in checks or not re.fullmatch('[a-f0-9]{64}',value):raise ValueError('Invalid checksum entry')
 if hashlib.sha256((out/name).read_bytes()).hexdigest()!=value:raise ValueError('Package digest mismatch')
 checks[name]=value
if len(checks)!=2:raise ValueError('Missing checksum')
verifier=api(f'contents/tools/quadro-verify.py?ref={head}')
(out/'quadro-verify.py').write_bytes(base64.b64decode(verifier['content']))
notes=f'''# Quadro Browser 6.0.0 — Mac Apple Silicon

Новый универсальный многооконный браузер вместо торговой оболочки Trader OS. Для Apple Silicon, включая M1 Pro; macOS 13+. Это предварительный выпуск с ad-hoc подписью, **без Developer ID и нотариализации Apple**.

## Изменения
- Полностью убрана левая колонка, тикеры, watchlist, рынки, скальпинг и торговые подсказки. Рабочие страницы начинаются от левого края. Название приложения, меню, установщик и иконка — Quadro Browser.
- Удалён статусный значок приложения из верхней строки меню macOS; работа через Dock и обычное меню приложения.
- До 12 окон; готовые раскладки и разделение выбранного окна справа/снизу. Вертикальные и горизонтальные разделители перетаскиваются, размеры сохраняются. Двойной щелчок возвращает разделитель в середину.
- Правый ИИ-чат выбирается из списка или по произвольной HTTP(S)-ссылке; его ширина изменяется перетаскиванием. Закрытие чата освобождает всю ширину. Это обычный веб-чат, без автоматической передачи содержимого других окон.
- Светлая и тёмная темы с контрастными кнопками/полями. В CI проверены реальные native bounds, pointer drag обоих направлений, custom AI, отсутствие reload, контраст, повторный запуск с cookies/layout/адресами и обычный запуск.
- Сохранён прежний режим кошелька: публичные EVM-адреса. **Это не MetaMask и не кошелёк для подписи/отправки транзакций.** Seed-фразы и приватные ключи вводить нельзя.

## Установка и обновление
1. Полностью завершите Trader OS через Cmd+Q, чтобы не было двух приложений с одним профилем.
2. Скачайте DMG, перетащите Quadro Browser в Applications / «Программы» и запустите оттуда.
3. Старый профиль используется без удаления: `~/Library/Application Support/Trader OS`. Внутреннее имя оставлено для совместимости, в новом интерфейсе торгового бренда нет. Старую папку профиля не удаляйте.
4. В установленной 5.0.3 автоматическое обновление было отключено; первый переход через её кнопку невозможен. В Quadro кнопка проверяет новые выпуски, скачивает DMG с проверкой размера/SHA-256 и открывает установщик. Перетаскивание приложения остаётся ручным; автоматическая замена не заявляется.
5. Иконку старого установочного диска на рабочем столе можно убрать командой «Извлечь» после копирования приложения. Это не изменение файлов пользователя со стороны CI.

При предупреждении о непроверенном разработчике используйте предусмотренное macOS подтверждение в «Конфиденциальность и безопасность», только убедившись в источнике приложения; не отключайте защиту системы целиком.

Проверки CI используют локальные тестовые страницы. Они не доказывают вход в личные аккаунты, совместимость всех сторонних сервисов или фактический запуск на Mac владельца. Windows, Chrome, Android и АвтоЦена не публиковались и их каналы не менялись.

Source: https://github.com/{SOURCE}/commit/{head}
Source verification: https://github.com/{SOURCE}/actions/runs/{run_id}
Distributed DMG verification: https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/{os.environ['GITHUB_RUN_ID']}

SHA-256:
```
{(out/'SHA256SUMS.txt').read_text().strip()}
```
'''
(out/'RELEASE_NOTES.md').write_text(notes)
print(json.dumps({'source':head,'runId':run_id,'artifactId':a['id'],'sha256':checks},indent=2))
