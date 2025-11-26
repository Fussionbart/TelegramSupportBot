from aiogram import Router
from aiogram.types import Message

from bot.services.users import (
    get_user, set_last_message, set_current_ticket,
    is_ack_planned, set_ack_planned
)

from bot.services.tickets import (
    create_ticket, add_message
)

from bot.core.utils import safe_send
from config import ADMIN_ID
from aiogram.filters import Command

router = Router()




@router.message(Command("start"))

async def start_cmd(message: Message):
    if message.from_user.id == ADMIN_ID:
        await safe_send(message.chat.id,
                        "Привет, админ. Используй /panel чтобы работать с тикетами.")
        return

    text = (
        "Привет! Это поддержка NextRoute.\n"
        "Опиши проблему (можно несколькими сообщениями), мы всё соберём в один запрос."
    )
    await safe_send(message.chat.id, text)


@router.message()
async def user_message(message: Message):
    """Обрабатываем обычные сообщения пользователя."""
    user_id = message.from_user.id
    text = message.text

    # Получаем/создаём пользователя
    user = get_user(user_id)

    # Если нет тикета — создаём
    ticket_id = user.get("current_ticket_id")
    if ticket_id is None:
        ticket_id = create_ticket(user_id)
        set_current_ticket(user_id, ticket_id)

    # Добавляем сообщение в файл сообщений тикета
    add_message(ticket_id, sender="user", text=text)

    # фиксируем время сообщения
    set_last_message(user_id)

    # если автоуведомление ещё не планировалось — включаем его
    if not is_ack_planned(user_id):
        set_ack_planned(user_id, True)

        # запускаем задачу отложенной проверки (дебаунс)
        from bot.services.scheduler import schedule_ack
        await schedule_ack(user_id, ticket_id)

    # Пользователю сейчас НИЧЕГО НЕ ОТВЕЧАЕМ
    # Ответ придёт позже, если он замолчит
