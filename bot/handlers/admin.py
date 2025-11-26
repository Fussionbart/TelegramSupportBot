from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.core.utils import safe_send, is_admin
from bot.services.tickets import (
    get_open_tickets, get_ticket, get_ticket_messages,
    update_ticket_status, add_message
)
from bot.services.users import set_current_ticket
from aiogram.filters import Command

router = Router()


# =============================
#   ФУНКЦИИ ДЛЯ КНОПОК
# =============================

def ticket_buttons(ticket_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📩 Ответить", callback_data=f"reply:{ticket_id}"),
            InlineKeyboardButton(text="❌ Закрыть", callback_data=f"close:{ticket_id}")
        ]
    ])


# =============================
#      /start — только админ
# =============================



@router.message(Command("start"))


async def admin_start(message: Message):
    if not is_admin(message.from_user.id):
        return  # это не админ — выходим

    await safe_send(
        message.chat.id,
        "Привет, админ.\n"
        "Для работы используй команду /panel."
    )


# =============================
#      /panel — список тикетов
# =============================

@router.message(Command("panel"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return

    open_tickets = get_open_tickets()

    if not open_tickets:
        await safe_send(message.chat.id, "Нет открытых тикетов 👌")
        return

    text = "📂 Открытые тикеты:\n\n"

    keyboard = []
    for tid, info in open_tickets.items():
        user_id = info["user_id"]
        text += f"• #{tid} — от {user_id}\n"
        keyboard.append([
            InlineKeyboardButton(
                text=f"Открыть #{tid}",
                callback_data=f"open:{tid}"
            )
        ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await safe_send(message.chat.id, text)
    await safe_send(message.chat.id, "Выбери тикет:", reply_markup=markup)


# =============================
#    Открыть конкретный тикет
# =============================

@router.callback_query(lambda c: c.data.startswith("open:"))
async def open_ticket_cb(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    ticket_id = int(call.data.split(":")[1])
    ticket = get_ticket(ticket_id)

    if not ticket:
        await call.answer("Тикет не найден", show_alert=True)
        return

    user_id = ticket["user_id"]
    msgs = get_ticket_messages(ticket_id)

    text = f"📄 Тикет #{ticket_id}\n"
    text += f"Пользователь: {user_id}\n"
    text += f"Статус: {ticket['status']}\n\n"

    for m in msgs[-10:]:  # показываем последние 10 сообщений
        sender = "👤 Юзер" if m["from"] == "user" else "🛠 Админ"
        text += f"{sender}: {m['text']}\n"

    await safe_send(
        call.message.chat.id,
        text,
        reply_markup=ticket_buttons(ticket_id)
    )

    await call.answer()


# =============================
#         Ответ на тикет
# =============================

# временное хранилище — кто на какой тикет отвечает
_admin_reply_state = {}


@router.callback_query(lambda c: c.data.startswith("reply:"))
async def reply_ticket_cb(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    ticket_id = int(call.data.split(":")[1])
    _admin_reply_state[call.from_user.id] = ticket_id  # админ "в режиме ответа"

    await safe_send(call.message.chat.id,
                    f"Напиши сообщение, которое отправится пользователю в тикете #{ticket_id}")
    await call.answer()


@router.message(lambda m: is_admin(m.from_user.id))
async def admin_reply(message: Message):
    """
    Если админ находится в режиме ответа — это сообщение пойдет пользователю.
    """
    if not is_admin(message.from_user.id):
        return  # это обычный юзер — игнорим (этот хендлер только для админа)

    admin_id = message.from_user.id

    if admin_id not in _admin_reply_state:
        return  # админ не в режиме ответа → это не ответ на тикет

    ticket_id = _admin_reply_state[admin_id]
    ticket = get_ticket(ticket_id)

    if not ticket:
        await safe_send(message.chat.id, "Ошибка: тикет исчез")
        _admin_reply_state.pop(admin_id, None)
        return

    user_id = ticket["user_id"]
    text = message.text

    # сохраняем сообщение
    add_message(ticket_id, "admin", text)

    # отправляем пользователю
    await safe_send(user_id, f"💬 Поддержка:\n{text}")

    # уведомляем админа
    await safe_send(message.chat.id, "Отправлено ✔️")

    # админ перестаёт быть "в режиме ответа"
    _admin_reply_state.pop(admin_id, None)


# =============================
#         Закрыть тикет
# =============================

@router.callback_query(lambda c: c.data.startswith("close:"))
async def close_ticket_cb(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    ticket_id = int(call.data.split(":")[1])
    ticket = get_ticket(ticket_id)

    if not ticket:
        await call.answer("Тикет не найден", show_alert=True)
        return

    update_ticket_status(ticket_id, "closed")

    # сбрасываем пользователя
    set_current_ticket(int(ticket["user_id"]), None)

    await safe_send(
        call.message.chat.id,
        f"❌ Тикет #{ticket_id} закрыт"
    )

    await safe_send(
        int(ticket["user_id"]),
        f"Тикет #{ticket_id} закрыт. Если проблема осталась — просто напиши снова."
    )

    await call.answer()
