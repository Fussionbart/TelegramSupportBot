from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter
import asyncio
from config import ADMIN_ID
from bot.core.loader import bot

async def safe_send(chat_id: int, text: str, reply_markup=None):
    try:
        return await bot.send_message(chat_id, text, reply_markup=reply_markup)
    except TelegramForbiddenError:
        return None
    except TelegramBadRequest:
        return None
    except TelegramRetryAfter as e:
        await asyncio.sleep(e.retry_after)
        return await safe_send(chat_id, text, reply_markup)
    except Exception:
        return None


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID
