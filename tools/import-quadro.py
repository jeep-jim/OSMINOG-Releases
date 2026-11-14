"""Import a successful exact-head Quadro candidate. No other channel is modified."""
import base64,hashlib,io,json,os,pathlib,re,subprocess,zipfile
SOURCE='jeep-jim/OSMINOG';ROOT=pathlib.Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'staging/quadro/6.0.5-arm64/import.json').read_text())
head=r['sourceCommit'];run_id=int(r['runId'])
if not re.fullmatch('[0-9a-f]{40}',head) or r['version']!='6.0.5' or r['tag']!='quadro-macos-v6.0.5-arm64':raise ValueError('Invalid release request')
def api(p):return json.loads(subprocess.check_output(['gh','api',f'repos/{SOURCE}/{p}']))
run=api(f'actions/runs/{run_id}')
if run['workflow_id']!=417128557 or run['head_sha']!=head or run['status']!='completed' or run['conclusion']!='success':raise ValueError('Exact Quadro candidate has not passed')
pr=api('pulls/136')
if not pr.get('merged') or pr['head']['sha']!=head or pr['base']['ref']!='main':raise ValueError('Verified source PR136 is not merged')
c=api(f'compare/{head}...main')
if c['status'] not in ['ahead','identical'] or c['behind_by']!=0:raise ValueError('Exact source is not an ancestor of main')
items=[a for a in api(f'actions/runs/{run_id}/artifacts')['artifacts'] if a['name']=='quadro-arm64-candidate' and not a['expired']]
if len(items)!=1:raise ValueError('Ambiguous or expired candidate')
a=items[0];archive=subprocess.check_output(['gh','api',f'repos/{SOURCE}/actions/artifacts/{a["id"]}/zip'])
if len(archive)>1024**3 or a.get('digest')!='sha256:'+hashlib.sha256(archive).hexdigest():raise ValueError('Artifact digest/size mismatch')
out=ROOT/'quadro-release';out.mkdir(exist_ok=True)
names={'Quadro-Browser-6.0.5-mac-arm64.dmg','Quadro-Browser-6.0.5-mac-arm64.zip','SHA256SUMS.txt','quadro-build.json'}
with zipfile.ZipFile(io.BytesIO(archive)) as z:
 entries=z.infolist()
 if len(entries)!=4 or {x.filename for x in entries}!=names or sum(x.file_size for x in entries)>1024**3:raise ValueError('Unexpected package entries')
 for item in entries:
  if item.is_dir() or (item.external_attr>>16)&0o170000==0o120000:raise ValueError('Unexpected package type')
  (out/item.filename).write_bytes(z.read(item))
b=json.loads((out/'quadro-build.json').read_text())
if b['source']!=head or int(b['runId'])!=run_id or b['version']!='6.0.5' or b['platform']!='darwin' or b['arch']!='arm64' or b['signing']!='ad-hoc' or b['notarized'] is not False:raise ValueError('Wrong build provenance')
if b['wallet']['network']!='sepolia-only' or b['wallet']['audited'] is not False or b['globalCapture']['requiresScreenPermission'] is not True:raise ValueError('Wrong feature safety boundary')
checks={}
for line in (out/'SHA256SUMS.txt').read_text().splitlines():
 value,name=line.split(maxsplit=1)
 if name not in names or not name.endswith(('.dmg','.zip')) or name in checks or not re.fullmatch('[a-f0-9]{64}',value):raise ValueError('Invalid checksum entry')
 if hashlib.sha256((out/name).read_bytes()).hexdigest()!=value:raise ValueError('Package digest mismatch')
 checks[name]=value
if len(checks)!=2:raise ValueError('Missing checksum')
for remote,local in [('tools/quadro-verify.py','quadro-verify.py'),('desktop/quadro-update.cjs','quadro-update.cjs')]:
 data=api(f'contents/{remote}?ref={head}');(out/local).write_bytes(base64.b64decode(data['content']))
notes=f'''# Quadro Browser 6.0.5 — скриншот всего Mac и боковая библиотека

Mac Apple Silicon, включая M1 Pro; macOS 13+. Предварительный выпуск, ad-hoc подпись без Developer ID и нотариализации Apple. Прежняя зелёно-розовая иконка, имя и профиль сохранены.

## Глобальный скриншот
Control+A зарегистрировано как системное сочетание: команда доступна, пока Quadro запущен, в том числе когда его окно свёрнуто или активно другое приложение. Полный выход Cmd+Q отключает сочетание; скрытый агент и автозапуск не добавлены. Сочетание займёт Control+A в других приложениях. Cmd+A не меняется.

Снимок дисплея под указателем получается до открытия отдельного редактора. Затем доступны выбор области, стрелка, линия, текст, круг, прямоугольник, карандаш, маркер, цвет/толщина, отмена/повтор, копирование и PNG. Крестик и Esc закрывают только редактор. Снимок обрабатывается локально, без облачной отправки, фоновой записи, аудио или видеопотока. Камера в браузере сохраняет прежний отдельный режим снимка окон браузера.

Разрешите Quadro Browser запись экрана в «Системные настройки → Конфиденциальность и безопасность → Запись экрана и системного звука» (название зависит от macOS), затем при необходимости перезапустите приложение. Настройки Quadro показывают состояние разрешения и регистрации сочетания, позволяют отключить его и открыть системные настройки. При занятом сочетании есть сообщение и пункт «Файл → Скриншот экрана Mac». Физическое нажатие в стороннем приложении на устройстве владельца и все раскладки клавиатуры не заявляются проверенными. Для не-QWERTY раскладок у Electron есть известное ограничение globalShortcut; при проблеме переключитесь на английскую раскладку или используйте пункт меню.

## Интерфейс
- История, закладки, поиск и загрузки открываются справа в регулируемой боковой панели, а не центральным окном. Страницы остаются интерактивными. Панель временно занимает место ИИ; закрытие возвращает ИИ и прежние размеры страниц без их перезагрузки.
- Тёмные монохромные favicon инвертируются в тёмной теме, светлые — в светлой; цветные логотипы сохраняют цвета.
- Добавлены промежутки между кнопками настроек и обновления, умеренные стеклянные поверхности и читаемый текст в обеих темах.
- При обращении к верхней кромке полноэкранного окна вкладки временно сдвигаются ниже системного меню. Постоянная пустая полоса не добавлена. Это не отключение меню macOS; поведение выреза и личных настроек экрана на M1 Pro требует проверки владельцем.

## Quadro Wallet — только тестовая Sepolia
Это настоящий экспериментальный модуль локального ключа и подписания, но НЕ готовая замена MetaMask для настоящих средств. Только сеть Sepolia. Не переводите сюда реальные средства и не импортируйте основной кошелёк. Независимого аудита нет.

Создание кошелька с паролем, зашифрованный JSON v3, импорт зашифрованной резервной копии, обязательный backup перед подписанием, автоблокировка. Ключ не передаётся сайтам или ИИ. Подключение сайта и каждое подписание требуют отдельного подтверждения. EIP-1193/EIP-6963 поддерживаются в ограниченном объёме; основная сеть, произвольная сырая подпись eth_sign и прочие сети отключены. HTTPS RPC Sepolia указывает пользователь. Подписи и транзакционные данные проверялись локально на тестовых данных; отправка в публичную сеть и все сторонние DApp не подтверждены. Старые публичные адреса сохранены отдельно.

## Установка и границы проверки
Завершите Quadro через Cmd+Q. Откройте DMG и замените Quadro Browser в «Программах». Не удаляйте `~/Library/Application Support/Trader OS`. Замена приложения пока ручная. Анонимное обнаружение обновлений ранее получало HTTP403 от GitHub; результат этой проверки публикуется отдельно, прямой DMG от неё не зависит.

Нативные проверки запускаются на тестовых Mac Apple Silicon и повторяются после установки из DMG. Проверяются боковая геометрия/resize, иконки/glass, старые меню/плитки/ИИ/история/загрузки/закрытие, криптография/зашифрованное хранилище и тестовое подключение сайта, регистрация globalShortcut, отдельный редактор при скрытом браузере, crop/clipboard/PNG/X. Основной тест глобального редактора использует явно синтетический кадр; фактический захват дисплея проверяется только при уже выданном TCC-разрешении, иначе журнал явно отмечает NOT_TESTED_TCC. Это не независимый аудит и не проверка на Mac владельца. Windows/Chrome/Android/АвтоЦена не публиковались.

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
