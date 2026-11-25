# Mouse Browser 6.0.39 — macOS Apple Silicon

## Блокировка рекламы

В Mouse появилась встроенная блокировка рекламных запросов. **По умолчанию она выключена.** Включить её можно через шестерёнку в нижней панели: **Настройки → Приватность и библиотека → Блокировать рекламу**. После изменения настройки при необходимости обновите открытую страницу.

Mouse загружает **EasyList и RU AdList**, сохраняет списки локально и проверяет запросы на устройстве. Сохранённые списки работают без подключения; при включённой блокировке Mouse обновляет их автоматически. Если обновление не удалось, сохраняются ранее загруженные списки. Состояние фильтров показано рядом с переключателем.

Выбор сохраняется после перезапуска и применяется также в инкогнито. Менять постоянную настройку можно в обычном режиме.

Используются поддерживаемые сетевые правила списков. Полное удаление рекламы на каждом сайте, включая рекламу внутри самого видеопотока, не гарантируется.

## Установка

DMG и ZIP содержат одно и то же приложение для Mac с Apple Silicon. Это предварительная версия с ad-hoc подписью, без Developer ID и нотариального заверения Apple.

Существующий профиль, вкладки, рабочие столы и каналы обновления сохраняются. Совместимость расширений по-прежнему ограничена API, которые поддерживает Electron.

---

## Ad blocking

Mouse now includes built-in advertising request blocking. **It is off by default.** Open **Settings** using the gear button in the bottom bar and enable **Block ads**. Reload an already open page after changing the setting if needed.

Mouse downloads **EasyList and RU AdList**, caches them locally and checks requests on your device. Cached lists work offline and update automatically while blocking is enabled. A failed update keeps the previously downloaded lists. Filter status appears beside the switch.

Your choice survives a restart and also applies in incognito; change the persistent setting in normal mode. This uses the supported network rules from the lists. Complete ad removal on every site, including ads embedded in the same video stream, is not guaranteed.

## Installation

The DMG and ZIP contain the same Apple Silicon application. This remains an ad-hoc signed preview without Developer ID signing or Apple notarization.

Existing profiles, tabs, workspaces and update channels are retained. Extension compatibility remains limited to the APIs supported by Electron.
