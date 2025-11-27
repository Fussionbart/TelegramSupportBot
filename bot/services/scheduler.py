import asyncio
import time
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import ACK_DELAY, ADMIN_ID

from bot.core.utils import safe_send
from bot.services.users import (
    get_last_message_time,
    set_ack_planned,
    was_admin_notified,
    set_admin_notified
)
from bot.services.tickets import get_ticket

_pending_tasks = {}


async def schedule_ack(user_id: int, ticket_id: str):
    old_task = _pending_tasks.get(user_id)
    if old_task and not old_task.done():
        old_task.cancel()

    task = asyncio.create_task(_ack_waiter(user_id, ticket_id))
    _pending_tasks[user_id] = task


async def _ack_waiter(user_id: int, ticket_id: str):
    from bot.handlers.admin import _admin_notifications

    try:
        await asyncio.sleep(ACK_DELAY)

        last_msg_time = await get_last_message_time(user_id)
        if last_msg_time is None:
            return

        silence_time = time.time() - last_msg_time

        if silence_time < ACK_DELAY:
            await schedule_ack(user_id, ticket_id)
            return

        ticket = await get_ticket(ticket_id)
        if not ticket:
            return

        await safe_send(
            user_id,
            f"Спасибо! Ваш запрос {ticket_id} принят, скоро ответим."
        )

        from bot.services.users import get_user, update_user
        user = await get_user(user_id)

        if user.get("ticket_fresh", False):
            admin_text = (
                f"📨 Новый запрос от пользователя {user_id}\n"
                f"Тикет: {ticket_id}"
            )
        else:
            admin_text = (
                f"💬 Пользователь снова написал в тикете {ticket_id}"
            )

        adm_msg = await safe_send(
            ADMIN_ID,
            admin_text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Открыть панель", callback_data="admin_panel")]
                ]
            )
        )

        if adm_msg:
            _admin_notifications[ADMIN_ID] = adm_msg.message_id

        await update_user(user_id, ticket_fresh=False)
        await set_ack_planned(user_id, False)

    except asyncio.CancelledError:
        return
