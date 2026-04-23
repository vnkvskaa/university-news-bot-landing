from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from topics import TOPICS


def topics_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    selected_set = set(selected)
    for key, title in TOPICS.items():
        marker = "✓" if key in selected_set else "+"
        buttons.append([
            InlineKeyboardButton(text=f"{marker} {title}", callback_data=f"topic:{key}")
        ])

    buttons.append([
        InlineKeyboardButton(text="Готово", callback_data="topics:done")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Мои подписки", callback_data="menu:subscriptions")],
            [InlineKeyboardButton(text="Изменить интересы", callback_data="menu:topics")],
        ]
    )


def user_reply_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Мои подписки"), KeyboardButton(text="Изменить интересы")],
        [KeyboardButton(text="Помощь")],
    ]
    if is_admin:
        rows.append([KeyboardButton(text="Статистика"), KeyboardButton(text="Создать рассылку")])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Выбери действие",
    )


def broadcast_topics_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for key, title in TOPICS.items():
        buttons.append([
            InlineKeyboardButton(text=title, callback_data=f"broadcast:{key}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
