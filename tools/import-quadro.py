"""Import a successful exact-head Quadro candidate. No other channel is modified."""
import base64,hashlib,io,json,os,pathlib,re,subprocess,zipfile
SOURCE='jeep-jim/OSMINOG';ROOT=pathlib.Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'staging/quadro/6.0.1-arm64/import.json').read_text())
head=r['sourceCommit'];run_id=int(r['runId'])
if not re.fullmatch('[0-9a-f]{40}',head) or r['version']!='6.0.1' or r['tag']!='quadro-macos-v6.0.1-arm64':raise ValueError('Invalid release request')
def api(p):return json.loads(subprocess.check_output(['gh','api',f'repos/{SOURCE}/{p}']))
run=api(f'actions/runs/{run_id}')
if run['workflow_id']!=417128557 or run['head_sha']!=head or run['status']!='completed' or run['conclusion']!='success':raise ValueError('Exact Quadro candidate has not passed')
pr=api('pulls/131')
if not pr.get('merged') or pr['head']['sha']!=head or pr['base']['ref']!='main':raise ValueError('Verified source PR131 is not merged')
c=api(f'compare/{head}...main')
if c['status'] not in ['ahead','identical'] or c['behind_by']!=0:raise ValueError('Exact source is not an ancestor of main')
items=[a for a in api(f'actions/runs/{run_id}/artifacts')['artifacts'] if a['name']=='quadro-arm64-candidate' and not a['expired']]
if len(items)!=1:raise ValueError('Ambiguous or expired candidate')
a=items[0];archive=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{a["id"]}/zip'])
if len(archive)>1024**3 or a.get('digest')!='sha256:'+hashlib.sha256(archive).hexdigest():raise ValueError('Artifact digest/size mismatch')
out=ROOT/'quadro-release';out.mkdir(exist_ok=True)
names={'Quadro-Browser-6.0.1-mac-arm64.dmg','Quadro-Browser-6.0.1-mac-arm64.zip','SHA256SUMS.txt','quadro-build.json'}
with zipfile.ZipFile(io.BytesIO(archive)) as z:
 entries=z.infolist()
 if len(entries)!=4 or {x.filename for x in entries}!=names or sum(x.file_size for x in entries)>1024**3:raise ValueError('Unexpected package entries')
 for item in entries:
  if item.is_dir() or (item.external_attr>>16)&0o170000==0o120000:raise ValueError('Unexpected package type')
  (out/item.filename).write_bytes(z.read(item))
b=json.loads((out/'quadro-build.json').read_text())
if b['source']!=head or int(b['runId'])!=run_id or b['version']!='6.0.1' or b['platform']!='darwin' or b['arch']!='arm64' or b['signing']!='ad-hoc' or b['notarized'] is not False:raise ValueError('Wrong build provenance')
checks={}
for line in (out/'SHA256SUMS.txt').read_text().splitlines():
 value,name=line.split(maxsplit=1)
 if name not in names or not name.endswith(('.dmg','.zip')) or name in checks or not re.fullmatch('[a-f0-9]{64}',value):raise ValueError('Invalid checksum entry')
 if hashlib.sha256((out/name).read_bytes()).hexdigest()!=value:raise ValueError('Package digest mismatch')
 checks[name]=value
if len(checks)!=2:raise ValueError('Missing checksum')
for remote,local in [('tools/quadro-verify.py','quadro-verify.py'),('desktop/quadro-update.cjs','quadro-update.cjs')]:
 data=api(f'contents/{remote}?ref={head}');(out/local).write_bytes(base64.b64decode(data['content']))
notes=f'''# Quadro Browser 6.0.1 — компактный интерфейс Mac

Для Mac Apple Silicon, включая M1 Pro; macOS 13+. Предварительный выпуск с ad-hoc подписью, без Developer ID/notarization.

## Что изменилось
- Одна верхняя строка: навигация, общий адрес выбранного окна и вкладки. Постоянные адресные полосы над каждой плиткой убраны. Нажмите на страницу, чтобы адресная строка управляла ей.
- Системные кнопки окна показываются в левом верхнем углу при наведении; для них отведено отдельное место, не перекрывающее вкладки. Крестики вкладок появляются слева при hover/focus без сдвига заголовка.
- Тонкая нижняя полоска содержит настройки/тему, число окон, разделение справа/снизу, удаление выбранной плитки, ИИ, кошелёк, обновление, полный экран и завершение.
- Красная кнопка и Cmd+Q сохраняют состояние, выходят из native fullscreen и завершают приложение вместо скрытия окна. Esc выходит из полного экрана, включая фокус на сайте.
- Сохранены изменение размеров окон/чата, произвольная ссылка ИИ, обе темы и прежний локальный профиль. Страницы не перезагружаются при изменении раскладки.

## Обновление с 6.0.0
Нажмите «Обновить» → «Скачать обновление» → «Открыть установщик». Полностью завершите старую версию через Cmd+Q и перенесите Quadro Browser из DMG в «Программы» с заменой приложения. Автоматическая замена приложения пока не включена. Удалять профиль `~/Library/Application Support/Trader OS` нельзя: он сохраняет прежние данные.

Проверены на CI Mac: реальные native-плитки 1/2/4/6, resize обеих осей, ИИ, отсутствие reload, контраст, геометрия одной строки при ширине 1440/1100/900/800, общий адрес после фокуса, сохранение cookies/раскладки/публичных адресов; реальные normal/fullscreen close и Cmd+Q с завершением процесса и сохранением последнего изменения. Это не проверка на компьютере владельца или всех его сторонних сайтов. Hover traffic lights — штатный experimental режим Electron; полная визуальная идентичность Safari не заявляется.

Кошелёк остаётся watch-only для публичных EVM-адресов, без MetaMask и подписания транзакций. Другие платформы и АвтоЦена не изменялись.

Source: https://github.com/{SOURCE}/commit/{head}
Source verification: https://github.com/{SOURCE}/actions/runs/{run_id}
DMG verification: https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/{os.environ['GITHUB_RUN_ID']}

SHA-256:
```
{(out/'SHA256SUMS.txt').read_text().strip()}
```
'''
(out/'RELEASE_NOTES.md').write_text(notes)
print(json.dumps({'source':head,'runId':run_id,'artifactId':a['id'],'sha256':checks},indent=2))
