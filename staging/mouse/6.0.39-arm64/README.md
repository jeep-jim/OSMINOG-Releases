# Mouse Browser 6.0.39 — macOS Apple Silicon

Кандидат закреплён за source `eccadb3a37abd00d039616b321292cba57a49941`, принятым в [PR #215](https://github.com/jeep-jim/OSMINOG/pull/215) через merge `e9d6b9eb288fe2476fe65c48009c6f965eb2f068`. Дерево принятого source и фактического merge совпадает: `73baeff4c8619d97abdc8d9f581572138335d9bf`.

Нативная приёмка выполнена в [source run 45621651720, attempt 1](https://github.com/jeep-jim/OSMINOG/actions/runs/45621651720/attempts/1), job `139231098387`. Независимый reader повторно проверил семь сценариев AdBlock, 41 raw artifact, настройки, инкогнито и сохранение после перезапуска. Retained Nora/profile/update/performance gates прошли; фактические DMG/ZIP проверены по байтам. В одном первом тёмном кадре после включения остался прежний текст статуса при уже включённом переключателе и готовом DOM/controller; последующие light/private/restart кадры корректны. Точная длительность этого расхождения не установлена.

Точные размеры и SHA256 пакетов, IDs и SHA256 candidate/verification архивов записаны в `pin.json`. Привязки к опубликованной 6.0.38 и отдельной legacy 6.0.29 сохранены.

`PUBLISH_OWNER` выбирает существующий workflow, который заново проверяет установленное приложение, профиль, обновление и независимые raw receipts AdBlock перед публикацией. Активация сама по себе не означает публичную доступность. Результат выпуска и проверки публичных пакетов — в [запусках publisher](https://github.com/jeep-jim/OSMINOG-Releases/actions/workflows/publish-mouse639.yml).

Порядок публикации: **macOS → Linux → Windows**. Следующая платформа допускается после проверки публичного канала и фактических package bytes предыдущей.

Apple Silicon, ad-hoc preview без Developer ID и нотариального заверения Apple.
