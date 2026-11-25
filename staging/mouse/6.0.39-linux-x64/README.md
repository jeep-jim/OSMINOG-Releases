# Mouse Browser 6.0.39 — Linux x64

Кандидат закреплён за source `eccadb3a37abd00d039616b321292cba57a49941`, принятым в [PR #215](https://github.com/jeep-jim/OSMINOG/pull/215) через merge `e9d6b9eb288fe2476fe65c48009c6f965eb2f068`. Дерево принятого source и merge: `73baeff4c8619d97abdc8d9f581572138335d9bf`.

Нативная приёмка выполнена в [source run 45621652166, attempt 1](https://github.com/jeep-jim/OSMINOG/actions/runs/45621652166/attempts/1). main и Ubuntu 24.04 Noble; семь сценариев AdBlock, 41 raw artifact и восемь settings frames в каждом окружении; точные AppImage/deb и installation binding проверены.

Точные package sizes и SHA256, а также IDs и SHA256 исходных candidate/verification архивов записаны в `pin.json`. Сохранены привязки к опубликованной 6.0.38 и отдельные legacy gates там, где они требуются.

`PUBLISH_OWNER` выбирает существующий workflow, который повторно проверяет установленное приложение, сохранение профиля, обновление и независимые raw receipts AdBlock перед публикацией. Активация сама по себе не означает публичную доступность. Результат публикации и проверки публичных пакетов фиксируется в [запусках publisher](https://github.com/jeep-jim/OSMINOG-Releases/actions/workflows/publish-mouse639-linux.yml).

Порядок публикации: **macOS → Linux → Windows**. Следующая платформа допускается после проверки публичного канала и фактических package bytes предыдущей.

Сборка x64. Проверены штатные sandbox и зависимости deb на Ubuntu; устройство владельца с Linux Mint этим не проверено.
