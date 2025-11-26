import asyncio
import time

from config import ACK_DELAY
from bot.services.users import (
    get_last_message_time,
    set_ack_planned,
)
from bot.services.tickets import get_ticket
from bot.core.utils import safe_send
from config import ADMIN_ID


# Храним активные задачи по user_id
_pending_tasks = {}


async def schedule_ack(user_id: int, ticket_id: int):
    """
    Запускает задачу, которая через ACK_DELAY проверит,
    нужно ли отправлять автоответ.
    Если задача для этого user_id уже висит — мы её отменяем и создаём заново.
    """

    # Если задача уже существует — отменяем
    old_task = _pending_tasks.get(user_id)
    if old_task and not old_task.done():
        old_task.cancel()

    # Создаём новую задачу
    task = asyncio.create_task(_ack_waiter(user_id, ticket_id))
    _pending_tasks[user_id] = task


async def _ack_waiter(user_id: int, ticket_id: int):
    """
    Ждёт ACK_DELAY секунд и смотрит, писал ли ещё юзер.
    Если писал — задача перезапускается.
    Если замолчал — отправляет автоответ.
    """
    try:
        await asyncio.sleep(ACK_DELAY)

        last_msg_time = get_last_message_time(user_id)

        # если вдруг данных нет — выходим
        if last_msg_time is None:
            return

        silence_time = time.time() - last_msg_time

        # Юзер писал в течение последних ACK_DELAY секунд → ждём дальше
        if silence_time < ACK_DELAY:
            await schedule_ack(user_id, ticket_id)  # перезапуск
            return

        # Юзер замолчал → отправляем автоответ
        ticket = get_ticket(ticket_id)
        if not ticket:
            return

        await safe_send(
            user_id,
            f"Спасибо! Ваш запрос №{ticket_id} принят, скоро ответим."
        )

        # сбрасываем флаг ack_planned
        set_ack_planned(user_id, False)

    except asyncio.CancelledError:
        # задача отменена → ничего не делаем
        return
