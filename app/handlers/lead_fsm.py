# lead_fsm.py
from aiogram import Router, F
from aiogram.types import (
    Message, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from ..keyboards import contact_request_kb  # кнопка "Отправить телефон" (request_contact=True)
from ..config import settings  # settings.LEADS_CHAT_ID из .env

router = Router()

class LeadForm(StatesGroup):
    name          = State()
    addr_street   = State()
    addr_house    = State()
    addr_building = State()
    area          = State()
    phone         = State()
    call_time     = State()
    comment       = State()
    confirm       = State()  # новый шаг подтверждения

# Алиас для подсказок типов
FSMContextType = FSMContext

# ──────────────────────────
# Вспомогательные функции
# ──────────────────────────
def _fmt_address(data: dict) -> str:
    street = (data.get("addr_street") or "").strip()
    house = (data.get("addr_house") or "").strip()
    bld   = (data.get("addr_building") or "").strip()
    base = f"{street}, дом {house}" if house else street
    if bld and bld.lower() not in ("нет", "—", "-", "пропустить"):
        base += f", корп/стр {bld}"
    return base

def _parse_area_to_float(text: str):
    if not text:
        return None
    t = text.lower().replace(",", ".")
    for suf in ("м2", "м^2", "кв.м", "кв м", "м²"):
        t = t.replace(suf, "")
    t = t.replace(" ", "").strip()
    try:
        return float(t)
    except ValueError:
        return None

def _normalize_phone(text: str) -> str:
    if not text:
        return ""
    digits = "".join(ch for ch in text if ch.isdigit() or ch == "+")
    if digits and not digits.startswith("+") and digits.startswith("8"):
        digits = "+7" + digits[1:]
    return digits

def _confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить", callback_data="lead:confirm")],
            [InlineKeyboardButton(text="🔄 Начать заново", callback_data="lead:restart")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="lead:cancel")],
        ]
    )

def _build_lead_summary(data: dict) -> str:
    addr = _fmt_address(data)
    area = data.get("area")
    name = data.get("name")
    phone = data.get("phone") or "не указан"
    call_time = data.get("call_time") or "не указано"
    comment = data.get("comment") or "—"
    return (
        f"— Имя: {name}\n"
        f"— Адрес: {addr}\n"
        f"— Площадь: {area:g} м²\n"
        f"— Телефон: {phone}\n"
        f"— Когда звонить: {call_time}\n"
        f"— Комментарий: {comment}"
    )

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

async def _send_to_admin_chat(bot, text: str) -> bool:
    chat_id = settings.LEADS_CHAT_ID  # может быть int или str (в т.ч. "@username")
    try:
        # 1) Проверим, что бот вообще видит чат
        chat = await bot.get_chat(chat_id)
        # 2) Пошлём сообщение
        await bot.send_message(chat.id, text)
        return True
    except TelegramForbiddenError as e:
        # Бот кикнут/не состоит/нет прав писать
        print(f"[LEADS SEND] Forbidden: {e}. "
              f"Добавь бота в чат (для каналов — админ). chat_id={chat_id}")
    except TelegramBadRequest as e:
        # Неверный chat_id или приватный чат, куда бот не имеет доступа
        print(f"[LEADS SEND] BadRequest: {e}. Проверь chat_id={chat_id} "
              f"и что бот добавлен именно в этот чат.")
    except Exception as e:
        print(f"[LEADS SEND] Unknown error: {e}")
    return False

# ──────────────────────────
# Старт сценария — зовём из assistance.py
# ──────────────────────────
async def start_lead(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(LeadForm.name)
    await message.answer(
        "Давайте оформим заявку на замер.\n\nКак вас зовут?",
        reply_markup=ReplyKeyboardRemove()
    )

# 1) Имя
@router.message(LeadForm.name, F.text)
async def lead_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await state.set_state(LeadForm.addr_street)
    await message.answer("Адрес: укажите улицу (например, «Тверская»).")

# 2) Улица
@router.message(LeadForm.addr_street, F.text)
async def lead_addr_street(message: Message, state: FSMContext):
    await state.update_data(addr_street=message.text.strip())
    await state.set_state(LeadForm.addr_house)
    await message.answer("Номер дома (например, «12»).")

# 3) Дом
@router.message(LeadForm.addr_house, F.text)
async def lead_addr_house(message: Message, state: FSMContext):
    await state.update_data(addr_house=message.text.strip())
    await state.set_state(LeadForm.addr_building)
    await message.answer("Корпус/строение (если есть). Если нет — напишите «нет» или «пропустить».")

# 4) Корпус/строение (опционально)
@router.message(LeadForm.addr_building, F.text)
async def lead_addr_building(message: Message, state: FSMContext):
    await state.update_data(addr_building=message.text.strip())
    await state.set_state(LeadForm.area)
    await message.answer("Примерная площадь работ (в м²). Например: 45")

# 5) Площадь (валидация числа)
@router.message(LeadForm.area, F.text)
async def lead_area(message: Message, state: FSMContext):
    area = _parse_area_to_float(message.text)
    if area is None or area <= 0:
        await message.answer("Пожалуйста, укажите площадь числом, например: 45")
        return
    await state.update_data(area=area)
    await state.set_state(LeadForm.phone)
    await message.answer(
        "Контактный номер телефона (можно отправить контакт кнопкой):",
        reply_markup=contact_request_kb()
    )

# 6) Телефон: кнопка-контакт
@router.message(LeadForm.phone, F.contact)
async def lead_phone_contact(message: Message, state: FSMContext):
    phone = (message.contact.phone_number or "").strip()
    await state.update_data(phone=_normalize_phone(phone))
    await state.set_state(LeadForm.call_time)
    await message.answer("Когда удобно вам позвонить? (например, «сегодня после 18:00»)", reply_markup=ReplyKeyboardRemove())

# 6а) Телефон: текстом (разрешим «пропустить»)
@router.message(LeadForm.phone, F.text)
async def lead_phone_text(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text.lower() != "пропустить":
        phone = _normalize_phone(text)
        if not phone or len(phone) < 7:
            await message.answer("Похоже, номер некорректный. Отправьте ещё раз или напишите «пропустить».")
            return
        await state.update_data(phone=phone)
    await state.set_state(LeadForm.call_time)
    await message.answer("Когда удобно вам позвонить? (например, «сегодня после 18:00»)", reply_markup=ReplyKeyboardRemove())

# 7) Удобное время для звонка
@router.message(LeadForm.call_time, F.text)
async def lead_call_time(message: Message, state: FSMContext):
    await state.update_data(call_time=message.text.strip())
    await state.set_state(LeadForm.comment)
    await message.answer("Оставьте дополнительный комментарий (пожелания, особенности объекта). Если нечего добавить — напишите «пропустить».")

# 8) Комментарий → ПРЕДПРОСМОТР и ПОДТВЕРЖДЕНИЕ
@router.message(LeadForm.comment, F.text)
async def lead_comment(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if text.lower() != "пропустить":
        await state.update_data(comment=text)

    data = await state.get_data()
    preview = _build_lead_summary(data)

    await state.set_state(LeadForm.confirm)
    await message.answer(
        "Проверьте, всё ли верно. Если да — отправьте заявку:\n\n" + preview,
        reply_markup=_confirm_kb()
    )

# ──────────────────────────
# КНОПКИ ПОДТВЕРЖДЕНИЯ / ПЕРЕЗАПУСКА / ОТМЕНЫ
# ──────────────────────────

@router.callback_query(LeadForm.confirm, F.data == "lead:confirm")
async def lead_confirm(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    data = await state.get_data()
    summary = _build_lead_summary(data)
    admin_text = "пришел новый лид!\n\n" + summary

    sent = await _send_to_admin_chat(cb.message.bot, admin_text)

    if sent:
        await cb.message.edit_reply_markup(reply_markup=None)
        await cb.message.answer("Готово! Мы получили ваши данные. Менеджер свяжется с вами в ближайшее время 👍")
    else:
        # Фолбэк, если не настроен LEADS_CHAT_ID
        await cb.message.edit_reply_markup(reply_markup=None)
        await cb.message.answer(
            "Данные собраны, но не удалось отправить администратору — проверьте настройку LEADS_CHAT_ID. "
            "Я всё равно сохранил вашу заявку локально (если так реализовано)."
        )
    await state.clear()

@router.callback_query(LeadForm.confirm, F.data == "lead:restart")
async def lead_restart(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.edit_reply_markup(reply_markup=None)
    await start_lead(cb.message, state)

@router.callback_query(LeadForm.confirm, F.data == "lead:cancel")
async def lead_cancel(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer("Анкета отменена. Если захотите начать снова — нажмите «Записаться на замер».")
    await state.clear()
