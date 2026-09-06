# OSMINOG 3.20.7 — Animation Studio + Agent Media Recovery

Этот выпуск включает всю функциональность неопубликованной 3.20.6 и исправления внутреннего чата.

- Animation Studio: таймлайн, дорожки, ключевые кадры, easing, loop-preview, WebM/Lottie export и редактируемый объект анимации.
- Команды изменения интерфейса OSMINOG снова выполняются как source-edit.
- «Подними поле ввода», «время под аватаром» и похожие команды больше не ошибаются режимом холста.
- Изображения ChatGPT захватываются из ответа и автоматически создаются как объекты холста.
- Поиск фотографий в интернете выполняет реальную цепочку web_image_search → asset_create.
- Нижняя панель чата закреплена внутри окна; время сообщений находится под аватарами.
- Graphics Studio, прозрачный PNG и документы сохранены и прошли регрессии.

Пакет: `OSMINOG-Chrome-3.20.7-ANIMATION-AGENT-MEDIA.zip`

SHA-256: `7b1e81f1bcb6a539f5083cf32de58c01bf594b0bf93a3841095c649ae6bb0aee`

Размер: 4090859 байт. Минимальный Dev Hub: 2.0.0. Фиксированный ключ расширения сохранён.

Проверки: [финальная сборка](https://github.com/jeep-jim/OSMINOG/actions/runs/34027200566), [Graphics Studio regression](https://github.com/jeep-jim/OSMINOG/actions/runs/34027114392).
