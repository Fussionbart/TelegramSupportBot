from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter
import asyncio
from config import ADMIN_ID
from bot.core.loader import bot


async def safe_send(chat_id: int, text: str):
    """
    Безопасная отправка сообщения:
    - игнорирует ошибки, если юзер заблокировал бота
    - корректно обрабатывает FloodWait
    """
    try:
        return await bot.send_message(chat_id, text)
    except TelegramForbiddenError:
        # пользователь заблокировал бота
        return None
    except TelegramBadRequest:
        # сообщение нельзя отправить (например, слишком длинное)
        return None
    except TelegramRetryAfter as e:
        # FloodWait — делаем паузу и пробуем снова
        await asyncio.sleep(e.retry_after)
        return await safe_send(chat_id, text)
    except Exception:
        # любые другие ошибки — игнорируем
        return None


def is_admin(user_id: int) -> bool:
    """
    Проверяет, является ли пользователь админом.
    """
    return user_id == ADMIN_ID
