import asyncio

from core.loader import bot, dp
from core.dispatcher import register_all_handlers
from services.scheduler import _pending_tasks


async def main():
    # Регистрируем хендлеры
    register_all_handlers(dp)

    print("Bot is running...")

    # Запускаем polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
