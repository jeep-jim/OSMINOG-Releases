"""Import successful exact-source Mouse bytes; never release an untested candidate."""
import base64,hashlib,io,json,os,pathlib,re,shutil,subprocess,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1];SOURCE='jeep-jim/OSMINOG';VERSION='6.0.6'
r=json.loads((ROOT/'staging/quadro/6.0.6-arm64/import.json').read_text());head=r['sourceCommit'];run_id=int(r['runId'])
if not re.fullmatch('[0-9a-f]{40}',head) or r['version']!=VERSION or r['tag']!='quadro-macos-v6.0.6-arm64' or r['sourcePR']!=137:raise ValueError('Invalid request')
def api(p):return json.loads(subprocess.check_output(['gh','api',f'repos/{SOURCE}/{p}']))
run=api(f'actions/runs/{run_id}')
if run['workflow_id']!=417128557 or run['head_sha']!=head or run['status']!='completed' or run['conclusion']!='success':raise ValueError('Exact native candidate has not passed')
pr=api('pulls/137')
if not pr.get('merged') or pr['head']['sha']!=head or pr['base']['ref']!='main':raise ValueError('Exact source PR137 is not merged')
c=api(f'compare/{head}...main')
if c['status'] not in ['ahead','identical'] or c['behind_by']!=0:raise ValueError('Source is not an ancestor of main')
items=[a for a in api(f'actions/runs/{run_id}/artifacts')['artifacts'] if a['name']=='quadro-arm64-candidate' and not a['expired']]
if len(items)!=1:raise ValueError('Candidate missing or ambiguous')
a=items[0];archive=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{a["id"]}/zip'])
if len(archive)>1024**3 or a.get('digest')!='sha256:'+hashlib.sha256(archive).hexdigest():raise ValueError('Artifact digest/size mismatch')
out=ROOT/'mouse-release';out.mkdir(exist_ok=True)
names={'Mouse-Browser-6.0.6-mac-arm64.dmg','Mouse-Browser-6.0.6-mac-arm64.zip','SHA256SUMS.txt','quadro-build.json'}
with zipfile.ZipFile(io.BytesIO(archive)) as z:
 entries=z.infolist()
 if len(entries)!=4 or {x.filename for x in entries}!=names or sum(x.file_size for x in entries)>1024**3:raise ValueError('Unexpected candidate entries')
 for item in entries:
  if item.is_dir() or (item.external_attr>>16)&0o170000==0o120000:raise ValueError('Unexpected object type')
  (out/item.filename).write_bytes(z.read(item))
b=json.loads((out/'quadro-build.json').read_text())
if b['source']!=head or int(b['runId'])!=run_id or b['version']!=VERSION or b['productName']!='Mouse Browser' or b['platform']!='darwin' or b['arch']!='arm64' or b['signing']!='ad-hoc' or b['notarized'] is not False:raise ValueError('Wrong package provenance')
required={'private-memory-isolation','private-cleanup-disk-scan','private-mascot-glasses','start-control-contrast','capture-success-feedback','native-apple-menu-preserved'}
if not required.issubset(set(b['tests'])):raise ValueError('Missing final owner test scope')
if b['wallet']['network']!='sepolia-only' or b['wallet']['audited'] is not False or b['globalCapture']['requiresScreenPermission'] is not True:raise ValueError('Wrong feature boundaries')
checks={}
for line in (out/'SHA256SUMS.txt').read_text().splitlines():
 value,name=line.split(maxsplit=1)
 if name not in names or not name.endswith(('.dmg','.zip')) or name in checks or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('Invalid checksum')
 if hashlib.sha256((out/name).read_bytes()).hexdigest()!=value:raise ValueError('Package digest mismatch')
 checks[name]=value
if len(checks)!=2:raise ValueError('Missing checksum')
alias='Quadro-Browser-6.0.6-mac-arm64.dmg';shutil.copyfile(out/'Mouse-Browser-6.0.6-mac-arm64.dmg',out/alias)
checks[alias]=checks['Mouse-Browser-6.0.6-mac-arm64.dmg']
(out/'SHA256SUMS.txt').write_text(''.join(f'{digest}  {name}\n' for name,digest in sorted(checks.items())))
for remote,local,ref in [('tools/quadro-verify.py','quadro-verify.py',head),('desktop/quadro-update.cjs','quadro-update.cjs',head),('desktop/quadro-update.cjs','legacy-update.cjs','4ac132e85a466b3b01d6503c01ed5707875793ee')]:
 data=api(f'contents/{remote}?ref={ref}');(out/local).write_bytes(base64.b64decode(data['content']))
notes=f'''# Mouse Browser 6.0.6 — настоящий Mac-выпуск

Mac Apple Silicon, включая M1 Pro; macOS 13+. Точное имя владельца — **Mouse Browser**. Иконка — его исходная пиксельная мышь, без перерисовки. Старый крестик больше не используется в Mac-приложении. Мышь — маскот, отдельного имени у неё нет. Чёрный/белый вариант интерфейса следует теме браузера, иконка запущенного приложения следует системной теме.

## Системное меню и ИИ
Настоящая строка Apple с часами, батареей и Wi-Fi остаётся доступной у верхнего края в полном экране. Исправлено превращение приложения в accessory-процесс после системного скриншота. Убрана лишняя собственная полоса/titlebar; место под настоящее меню определяется его видимостью и измеренной геометрией, не фиксированным пустым отступом. Глобальные настройки macOS не меняются.

У ИИ одна компактная строка: favicon перед названием, ссылка, обновление и закрытие. Отдельной строки «ИИ-чат» нет. Логотипы берутся с выбранных сервисов; при недоступности — нейтральный значок, не выдуманный логотип. Сами сайты не перерисовываются.

## Контраст и скриншот
Стрелка поиска и меню плиток на новой вкладке имеют явно заданные контрастные цвета в обеих темах. После успешного получения снимка появляется короткая вспышка и надпись «Снимок готов». Эффект не рисуется в итоговом PNG; при ошибке захвата успех не показывается. Учитывается режим уменьшения движения.

Control+A вызывает системный скриншот, пока браузер запущен, в том числе из другой программы. Нужны разрешение записи экрана macOS и свободное сочетание. Cmd+Q освобождает сочетание; скрытый агент/автозапуск не добавлены. Камера браузера сохраняет отдельный режим снимка его окон. После переименования приложения проверьте разрешение снова. Все раскладки и сторонние приложения на Mac владельца не проверялись.

## Инкогнито с маскотом в пиксельных очках
Кнопка очков внизу или Cmd+Shift+N переключает текущее окно в отдельную временную сессию. Обычные страницы остаются отдельно и возвращаются при выходе. Новая приватная вкладка показывает исходный маскот в чёрных мемных очках. История посещений, запросы и закрытые вкладки не записываются в обычный профиль. Cookie и хранилища сайтов изолированы в непостоянной Chromium session с выключенным дисковым cache; при выходе приватные страницы закрываются, данные сессии очищаются. Настройки и временные закладки этого режима остаются только в MemoryStore. Обычные cookie, закладки и раскладка не очищаются.

Это приватность локального браузера, **не анонимность в интернете и не гарантия обнуления RAM/swap/системных журналов**. Сайты, провайдер и администратор сети могут видеть активность. Файлы, которые пользователь явно скачал или сохранил, скриншоты и буфер обмена остаются. В инкогнито кошелёк и обновление отключены; нельзя сохранять собственный фон в обычный профиль. Выйти из режима можно той же кнопкой/сочетанием или завершить приложение.

## Установка с Quadro
Полностью завершите Quadro через Cmd+Q. Откройте DMG и скопируйте **Mouse Browser.app** в «Программы». Запустите именно Mouse Browser. Из-за нового имени это не автоматическая замена Quadro Browser.app; старое приложение можно убрать отдельно после проверки. **Не удаляйте `~/Library/Application Support/Trader OS`**. Не запускайте обе версии одновременно.

Технический quadro release tag и Quadro-Browser-6.0.6-mac-arm64.dmg оставлены только для совместимости старой кнопки обновления. Alias побайтово равен Mouse DMG. Замена приложения остаётся ручной, доступность GitHub API проверяется отдельно.

Предварительная сборка: ad-hoc, **без Developer ID и нотариализации Apple**. Кошелёк остаётся экспериментальным Sepolia-only, без независимого аудита и не для настоящих средств. Другие платформы и АвтоЦена не публикуются.

Проверки выполняются на CI Mac Apple Silicon и повторяются после копирования из настоящего DMG: системное меню, мышь/ИИ, старые функции, контраст, скриншот, изоляция приватных cookie/localStorage/IndexedDB, повторный вход с пустой сессией, обычные вкладки без перезагрузки, выход процесса и отсутствие тестового приватного маркера в workspace.json. Это не forensic-аудит всего диска и не проверка физического наведения/выреза/всех экранов на M1 Pro владельца.

Source: https://github.com/{SOURCE}/commit/{head}
Source native tests: https://github.com/{SOURCE}/actions/runs/{run_id}
Installed DMG tests: https://github.com/jeep-jim/OSMINOG-Releases/actions/runs/{os.environ['GITHUB_RUN_ID']}

SHA-256:
```
{(out/'SHA256SUMS.txt').read_text().strip()}
```
'''
(out/'RELEASE_NOTES.md').write_text(notes)
print(json.dumps({'source':head,'runId':run_id,'artifactId':a['id'],'sha256':checks},indent=2))
