# Telegram-бот рассылок онлайн-университета

MVP-бот: сотрудник выбирает интересующие темы, бот сохраняет подписки и позволяет администратору отправлять анонсы по выбранной теме.

## Что умеет

- `/start` — онбординг и выбор интересов.
- `/topics` — изменить интересы.
- `/subscriptions` — посмотреть текущие подписки.
- `/stats` — статистика подписок по темам, только для администраторов.
- `/broadcast topic_key текст` — отправить анонс подписчикам темы, только для администраторов.

## Запуск

1. Создать бота через BotFather и получить токен.
2. Установить зависимости:

```bash
cd bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Создать `.env` рядом с `.env.example`:

```bash
BOT_TOKEN=токен_бота
ADMIN_IDS=ваш_telegram_id
DATABASE_PATH=bot.db
```

4. Запустить:

```bash
python main.py
```

## Пример рассылки

```text
/broadcast digital Практикум: AI-инструменты для рабочих задач. Регистрация: https://example.com
```

`topic_key` можно посмотреть в `topics.py`.
