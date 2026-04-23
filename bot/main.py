import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from config import load_settings
from keyboards import broadcast_topics_keyboard, main_keyboard, topics_keyboard, user_reply_keyboard
from storage import Storage
from topics import TOPICS


router = Router()
settings = load_settings()
storage = Storage(settings.database_path)
pending_broadcasts: dict[int, dict[str, Optional[str]]] = {}


def topic_names(keys: list[str]) -> str:
    if not keys:
        return "пока ничего не выбрано"
    return ", ".join(TOPICS.get(key, key) for key in keys)


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


def extract_media(message: Message) -> tuple[Optional[str], Optional[str]]:
    if message.photo:
        return "photo", message.photo[-1].file_id
    if message.video:
        return "video", message.video.file_id
    if message.document:
        return "document", message.document.file_id
    if message.audio:
        return "audio", message.audio.file_id
    if message.voice:
        return "voice", message.voice.file_id
    if message.animation:
        return "animation", message.animation.file_id
    if message.video_note:
        return "video_note", message.video_note.file_id
    return None, None


async def send_announcement(bot: Bot, chat_id: int, announcement: str, media_type: Optional[str], file_id: Optional[str]) -> None:
    if media_type == "photo" and file_id:
        await bot.send_photo(chat_id, file_id, caption=announcement)
    elif media_type == "video" and file_id:
        await bot.send_video(chat_id, file_id, caption=announcement)
    elif media_type == "document" and file_id:
        await bot.send_document(chat_id, file_id, caption=announcement)
    elif media_type == "audio" and file_id:
        await bot.send_audio(chat_id, file_id, caption=announcement)
    elif media_type == "voice" and file_id:
        await bot.send_voice(chat_id, file_id, caption=announcement)
    elif media_type == "animation" and file_id:
        await bot.send_animation(chat_id, file_id, caption=announcement)
    elif media_type == "video_note" and file_id:
        await bot.send_video_note(chat_id, file_id)
        await bot.send_message(chat_id, announcement)
    else:
        await bot.send_message(chat_id, announcement)


def demo_announcement(selected: list[str]) -> str:
    primary_topic = TOPICS.get(selected[0], "выбранной теме") if selected else "выбранной теме"
    return (
        "✨ Пример персонального анонса\n\n"
        f"Тема: {primary_topic}\n"
        "Практикум: AI-инструменты для рабочих задач\n\n"
        "За 60 минут разберем, как быстрее готовить тексты, искать идеи и собирать черновики рабочих материалов.\n\n"
        "Формат: онлайн\n"
        "Когда: 15 мая, 11:00\n"
        "Регистрация: https://online-university.example/events/ai-tools\n\n"
        "Так будут выглядеть анонсы по твоим интересам."
    )


@router.message(Command("start"))
async def start(message: Message) -> None:
    user = message.from_user
    if not user:
        return

    storage.upsert_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
    )

    await message.answer(
        "Привет! Я бот онлайн-университета 👋\n\n"
        "Помогу получать анонсы обучения по темам, которые тебе действительно интересны.",
        reply_markup=user_reply_keyboard(is_admin(user.id)),
    )
    await message.answer(
        "Выбери направления ниже — и я покажу пример персонального анонса.",
        reply_markup=topics_keyboard(storage.get_subscriptions(user.id)),
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "Что умею:\n"
        "/start — выбрать интересы\n"
        "/subscriptions — посмотреть подписки\n"
        "/topics — изменить интересы\n\n"
        "Для админов:\n"
        "/stats — статистика по темам\n"
        "/send — выбрать тему и отправить текст/медиа\n"
        "/broadcast topic_key текст — быстрая отправка по теме"
        ,
        reply_markup=user_reply_keyboard(is_admin(message.from_user.id) if message.from_user else False),
    )


@router.message(Command("topics"))
async def topics_command(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    storage.upsert_user(user.id, user.username, user.full_name)
    await message.answer(
        "Выбери интересующие темы ✨",
        reply_markup=topics_keyboard(storage.get_subscriptions(user.id)),
    )


@router.message(Command("subscriptions"))
async def subscriptions_command(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    selected = storage.get_subscriptions(user.id)
    await message.answer(
        f"Твои подписки: {topic_names(selected)}.",
        reply_markup=main_keyboard(),
    )


@router.message(F.text == "Помощь")
async def help_button(message: Message) -> None:
    await help_command(message)


@router.message(F.text == "Изменить интересы")
async def topics_button(message: Message) -> None:
    await topics_command(message)


@router.message(F.text == "Мои подписки")
async def subscriptions_button(message: Message) -> None:
    await subscriptions_command(message)


@router.message(F.text == "Статистика")
async def stats_button(message: Message) -> None:
    await stats_command(message)


@router.message(F.text == "Создать рассылку")
async def create_broadcast_button(message: Message) -> None:
    user = message.from_user
    if not user or not is_admin(user.id):
        await message.answer("Команда доступна только администратору.")
        return
    await message.answer(
        "Пришли текст/медиа для рассылки, а потом ответь на него командой /send.\n\n"
        "Например: отправь картинку с анонсом → ответь на нее /send Подпись к анонсу → выбери тему кнопкой."
    )


@router.callback_query(F.data.startswith("topic:"))
async def toggle_topic(callback: CallbackQuery) -> None:
    user = callback.from_user
    topic_key = callback.data.split(":", 1)[1]

    if topic_key not in TOPICS:
        await callback.answer("Неизвестная тема")
        return

    enabled = storage.toggle_subscription(user.id, topic_key)
    selected = storage.get_subscriptions(user.id)
    status = "добавлено" if enabled else "убрано"

    await callback.answer(f"{TOPICS[topic_key]}: {status}")
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=topics_keyboard(selected))


@router.callback_query(F.data == "topics:done")
async def topics_done(callback: CallbackQuery) -> None:
    selected = storage.get_subscriptions(callback.from_user.id)
    await callback.answer("Готово")
    if callback.message:
        if not selected:
            await callback.message.edit_text(
                "Пока не выбрана ни одна тема.\n\n"
                "Выбери хотя бы одно направление — так я смогу присылать релевантные анонсы 🙂",
                reply_markup=topics_keyboard(selected),
            )
            return

        await callback.message.edit_text(
            f"Готово, подписки сохранены ✅\n\n"
            f"Твои темы: {topic_names(selected)}.\n\n"
            "Ниже пример того, как будет выглядеть персональная рассылка.",
            reply_markup=main_keyboard(),
        )
        await callback.message.answer(demo_announcement(selected))


@router.callback_query(F.data == "menu:subscriptions")
async def menu_subscriptions(callback: CallbackQuery) -> None:
    selected = storage.get_subscriptions(callback.from_user.id)
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            f"Твои подписки: {topic_names(selected)}.",
            reply_markup=main_keyboard(),
        )


@router.callback_query(F.data == "menu:topics")
async def menu_topics(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Можно изменить интересы в любой момент 🙂",
            reply_markup=topics_keyboard(storage.get_subscriptions(callback.from_user.id)),
        )


@router.message(Command("stats"))
async def stats_command(message: Message) -> None:
    user = message.from_user
    if not user or not is_admin(user.id):
        await message.answer("Команда доступна только администратору.")
        return

    counts = storage.count_topic_subscribers()
    lines = ["Статистика подписок:"]
    for key, title in TOPICS.items():
        lines.append(f"• {title}: {counts.get(key, 0)}")
    await message.answer("\n".join(lines))


@router.message(Command("broadcast"))
async def broadcast_command(message: Message, command: CommandObject, bot: Bot) -> None:
    user = message.from_user
    if not user or not is_admin(user.id):
        await message.answer("Команда доступна только администратору.")
        return

    if not command.args:
        await message.answer(
            "Формат: /broadcast topic_key текст анонса\n"
            "Можно ответить этой командой на фото, видео, документ, аудио или голосовое — бот разошлет медиа с подписью.\n"
            f"Доступные topic_key: {', '.join(TOPICS.keys())}"
        )
        return

    topic_key, _, text = command.args.partition(" ")
    replied = message.reply_to_message
    has_media = replied and (
        replied.photo
        or replied.video
        or replied.document
        or replied.audio
        or replied.voice
        or replied.animation
        or replied.video_note
    )

    if topic_key not in TOPICS or (not text.strip() and not has_media):
        await message.answer(
            "Не получилось распознать тему или текст.\n"
            "Пример: /broadcast digital Новый практикум по AI: https://...\n"
            "Или ответь командой на медиафайл: /broadcast digital Подпись к анонсу"
        )
        return

    subscribers = storage.get_topic_subscribers(topic_key)
    if not subscribers:
        await message.answer("У этой темы пока нет подписчиков.")
        return

    sent = 0
    failed = 0
    announcement = f"📌 Новый анонс по теме «{TOPICS[topic_key]}»"
    if text.strip():
        announcement += f"\n\n{text.strip()}"

    media_type, file_id = extract_media(replied) if replied else (None, None)

    for chat_id in subscribers:
        try:
            await send_announcement(bot, chat_id, announcement, media_type, file_id)
            sent += 1
        except Exception:
            logging.exception("Failed to send broadcast to %s", chat_id)
            failed += 1

    await message.answer(f"Рассылка завершена. Отправлено: {sent}. Ошибок: {failed}.")


@router.message(Command("send"))
async def send_command(message: Message, command: CommandObject) -> None:
    user = message.from_user
    if not user or not is_admin(user.id):
        await message.answer("Команда доступна только администратору.")
        return

    source = message.reply_to_message or message
    media_type, file_id = extract_media(source)
    text = (command.args or "").strip()

    if message.reply_to_message:
        text = text or message.reply_to_message.caption or message.reply_to_message.text or ""

    if not text and not file_id:
        await message.answer(
            "Пришли текст/медиа для рассылки или ответь на сообщение командой /send.\n\n"
            "Пример: отправь фото, затем ответь на него /send Подпись к анонсу"
        )
        return

    pending_broadcasts[user.id] = {
        "text": text,
        "media_type": media_type,
        "file_id": file_id,
    }
    await message.answer(
        "Куда отправляем анонс? Выбери тему:",
        reply_markup=broadcast_topics_keyboard(),
    )


@router.callback_query(F.data.startswith("broadcast:"))
async def choose_broadcast_topic(callback: CallbackQuery, bot: Bot) -> None:
    user = callback.from_user
    if not is_admin(user.id):
        await callback.answer("Недоступно", show_alert=True)
        return

    topic_key = callback.data.split(":", 1)[1]
    payload = pending_broadcasts.get(user.id)
    if topic_key not in TOPICS or not payload:
        await callback.answer("Нет подготовленной рассылки", show_alert=True)
        return

    subscribers = storage.get_topic_subscribers(topic_key)
    if not subscribers:
        await callback.answer("У темы нет подписчиков", show_alert=True)
        return

    text = str(payload.get("text") or "").strip()
    announcement = f"📌 Новый анонс по теме «{TOPICS[topic_key]}»"
    if text:
        announcement += f"\n\n{text}"

    sent = 0
    failed = 0
    for chat_id in subscribers:
        try:
            await send_announcement(
                bot,
                chat_id,
                announcement,
                payload.get("media_type"),
                payload.get("file_id"),
            )
            sent += 1
        except Exception:
            logging.exception("Failed to send prepared broadcast to %s", chat_id)
            failed += 1

    pending_broadcasts.pop(user.id, None)
    await callback.answer("Рассылка отправлена")
    if callback.message:
        await callback.message.edit_text(
            f"Рассылка по теме «{TOPICS[topic_key]}» завершена.\n"
            f"Отправлено: {sent}. Ошибок: {failed}."
        )


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    storage.setup()

    bot = Bot(settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
