# Landing + Telegram Bot MVP

Проект содержит:

- презентационный лендинг в корне проекта;
- MVP Telegram-бота в папке `bot/`.

## Структура

- `index.html` — главная страница лендинга
- `styles.css` — стили
- `script.js` — интерактивность на странице
- `assets/` — локальные изображения
- `bot/` — Telegram-бот

## Публикация сайта на GitHub Pages

После создания пустого репозитория на GitHub:

```bash
git branch -M main
git remote add origin https://github.com/vnkvskaa/newsletter-bot-landing.git
git add .
git commit -m "Initial landing and bot MVP"
git push -u origin main
```

Затем на GitHub:

1. Открыть `Settings` -> `Pages`
2. В `Source` выбрать `GitHub Actions`
3. Дождаться завершения workflow `Deploy static site to Pages`

Ожидаемый адрес сайта:

```text
https://vnkvskaa.github.io/newsletter-bot-landing/
```

## Локальный запуск лендинга

```bash
python3 -m http.server 8080
```

## Локальный запуск Telegram-бота

```bash
cd bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
