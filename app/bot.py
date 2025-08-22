# Инициализация aiogram: Bot, Dispatcher и логирование.
import logging, re
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from .config import settings


bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
