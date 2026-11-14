"""Import only a successful exact-source Mouse candidate; preserve legacy update discovery."""
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
checks={}
for line in (out/'SHA256SUMS.txt').read_text().splitlines():
 value,name=line.split(maxsplit=1)
 if name not in names or not name.endswith(('.dmg','.zip')) or name in checks or not re.fullmatch('[0-9a-f]{64}',value):raise ValueError('Invalid checksum')
 if hashlib.sha256((out/name).read_bytes()).hexdigest()!=value:raise ValueError('Package digest mismatch')
 checks[name]=value
if len(checks)!=2:raise ValueError('Missing checksum')
# A byte-for-byte alias allows the already-installed 6.0.5 updater to find the rebrand.
alias='Quadro-Browser-6.0.6-mac-arm64.dmg';shutil.copyfile(out/'Mouse-Browser-6.0.6-mac-arm64.dmg',out/alias)
checks[alias]=checks['Mouse-Browser-6.0.6-mac-arm64.dmg']
(out/'SHA256SUMS.txt').write_text(''.join(f'{digest}  {name}\n' for name,digest in sorted(checks.items())))
for remote,local,ref in [('tools/quadro-verify.py','quadro-verify.py',head),('desktop/quadro-update.cjs','quadro-update.cjs',head),('desktop/quadro-update.cjs','legacy-update.cjs','4ac132e85a466b3b01d6503c01ed5707875793ee')]:
 data=api(f'contents/{remote}?ref={ref}');(out/local).write_bytes(base64.b64decode(data['content']))
notes=f'''# Mouse Browser 6.0.6 — мышь, меню Apple и компактный ИИ

Реальное приложение для Mac Apple Silicon, включая M1 Pro, macOS 13+. Название выбрано владельцем: **Mouse Browser**. Использован его исходный pixel mouse.png без перерисовки; старый крестик убран из распространяемой Mac-иконки и интерфейса. Чёрная/белая мышь адаптируется к теме браузера, иконка запущенного приложения — к системной теме. Макс также появляется в существующих состояниях загрузки и обновления, без выдуманного прогресса.

## Настоящая строка macOS
Не удаляются Apple menu, время, батарея, Wi-Fi и другие системные значки. Модуль использует публичные Cocoa API для раскрытия настоящего системного меню у верхнего края полноэкранного окна. Убрана прежняя предположительная пустая полоса64–88px. Место под меню учитывается по его фактической видимости/высоте и геометрии окна. Системные настройки, глобальные defaults и состав меню macOS не меняются; фальшивых часов/Wi-Fi нет.

## ИИ
Отдельная строка «ИИ-чат» удалена. Осталась одна компактная строка: иконка перед названием выбранного сервиса, добавление ссылки, обновление и закрытие. Такой же порядок icon+name в выборе провайдера. Иконки берутся из favicon самих выбранных сайтов; при недоступной иконке используется нейтральный globe, а не чужой/выдуманный логотип. Содержимое сайтов и их собственные заголовки не редактируется.

## Переход с Quadro
Полностью завершите Quadro через Cmd+Q. Откройте DMG и скопируйте **Mouse Browser.app** в «Программы». Запустите именно Mouse Browser. Из-за нового имени это не автоматическая замена файла Quadro Browser.app; старое приложение можно удалить отдельно после проверки. **Не удаляйте `~/Library/Application Support/Trader OS`**: тот же профиль, cookie/история/закладки/раскладки продолжают использоваться. Не запускайте старый и новый браузер одновременно.

Технический release tag и дополнительный файл Quadro-Browser-6.0.6-mac-arm64.dmg сохранены только для перехода старого updater. Этот файл побайтово совпадает с Mouse DMG и устанавливает именно Mouse Browser. Основная пользовательская ссылка — Mouse-Browser-6.0.6-mac-arm64.dmg. Замена приложения остаётся ручной. Доступность анонимного GitHub API проверяется отдельным шагом workflow; прошлые HTTP403 не объявляются навсегда устранёнными.

Многооконность, боковая библиотека, глобальный Control+A/локальная камера и профиль сохранены. Системный скриншот требует разрешения macOS и запущенного приложения; после смены приложения разрешение может потребоваться проверить снова. Кошелёк остаётся экспериментальным **Sepolia-only**, без аудита и не для настоящих средств; его возможности не расширялись. Другие платформы и АвтоЦена не публиковались.

Сборка предварительная, ad-hoc подпись, **нет Developer ID и нотариализации Apple**. Нативные тесты на CI Mac и повторная установка из DMG не являются проверкой физического наведения на M1 Pro владельца, всех настроек выреза/экранов, аккаунтов сайтов или всех favicon. В журнале source/release отдельно указаны фактические native menu assertions и снимок системного экрана, когда разрешение доступно.

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
