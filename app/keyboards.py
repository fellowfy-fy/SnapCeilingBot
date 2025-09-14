# Инлайн-клавиатуры: сброс сессии и запись на замер.
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
def main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📏 Записаться на замер", callback_data="lead:book"),
    ]])


def contact_request_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        one_time_keyboard=True,
        keyboard=[[KeyboardButton(text="📞 Отправить телефон", request_contact=True)]],
        input_field_placeholder="Отправьте телефон или введите его вручную"
    )