import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot.core.loader import bot, dp
from bot.core.dispatcher import register_all_handlers

async def main():
    register_all_handlers(dp)

    print("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
