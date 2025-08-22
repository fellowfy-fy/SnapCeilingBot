# Точка входа: подключаем роутеры и запускаем polling.
import asyncio
from .bot import bot, dp, setup_logging
from .handlers import chat_router, lead_router

async def main():
    setup_logging()
    dp.include_router(chat_router)
    dp.include_router(lead_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
