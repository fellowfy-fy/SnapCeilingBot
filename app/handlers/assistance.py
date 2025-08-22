# assistance.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, StateFilter, Command

from . import lead_fsm
from ..keyboards import main_kb
from ..llm import make_dialog_context, chat_completion

router = Router()

@router.callback_query(F.data == "lead:book")
async def start_lead_cb(cb: CallbackQuery, state: lead_fsm.FSMContextType):
    await cb.answer()
    await lead_fsm.start_lead(cb.message, state)

@router.message(CommandStart())
async def cmd_start(msg: Message):
    await msg.answer(
        "Здравствуйте! Я помогу с натяжными потолками. "
        "Скажите, какой объект и что планируете? "
        "Если есть вопросы — задайте. Моя задача: бесплатно записать вас на замер.",
        reply_markup=main_kb()
    )


# Важно: общий диалог — только когда НЕТ активного состояния FSM
@router.message(StateFilter(None), F.text.func(lambda t: t and t.strip() != ""))
async def dialog(msg: Message):
    text = msg.text.strip()
    ctx = make_dialog_context(user_text=text)
    try:
        answer = await chat_completion(ctx)
    except Exception as e:
        answer = "Секунду, связь с моделью недоступна. Попробуйте ещё раз."
        print(f"[LLM ERROR] {e!r}")
    await msg.answer(answer, reply_markup=main_kb())
