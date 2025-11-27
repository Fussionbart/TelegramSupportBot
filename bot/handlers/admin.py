from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import ADMIN_ID
from bot.core.utils import safe_send
from bot.services.tickets import (
    get_open_tickets, get_ticket, get_ticket_messages,
    update_ticket_status, add_message
)
from bot.services.users import set_current_ticket, set_admin_notified
from bot.services.users import has_admin_started, set_admin_started
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.services.users import has_admin_started, set_admin_started

router = Router()
router.message.filter(F.from_user.id == ADMIN_ID)
router.callback_query.filter(F.from_user.id == ADMIN_ID)

_admin_panels = {}
_admin_open_msgs = {}
_admin_notifications = {}

admin_main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Панель")]
    ],
    resize_keyboard=True
)


def ticket_buttons(ticket_id: str, user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Ответить 📩", callback_data=f"reply:{ticket_id}"),
                InlineKeyboardButton(text="Закрыть ❌", callback_data=f"close:{ticket_id}")
            ],
            [
                InlineKeyboardButton(text="Пользователь 💬", url=f"tg://user?id={user_id}")
            ]
        ]
    )


@router.message(Command("start"))
async def admin_start(message: Message):

    if await has_admin_started():
        try:
            await message.delete()
        except:
            pass
        return

    await set_admin_started()

    try:
        await message.delete()
    except:
        pass

    await safe_send(
        message.chat.id,
        "Привет, босс! ",
        reply_markup=admin_main_keyboard
    )


@router.message(F.text == "Панель")
async def admin_panel(message: Message):
    chat_id = message.chat.id

    open_msg_id = _admin_open_msgs.get(chat_id)
    if open_msg_id:
        try:
            await message.bot.delete_message(chat_id, open_msg_id)
        except:
            pass
        _admin_open_msgs.pop(chat_id, None)

    notif_id = _admin_notifications.get(chat_id)
    if notif_id:
        try:
            await message.bot.delete_message(chat_id, notif_id)
        except:
            pass
        _admin_notifications.pop(chat_id, None)

    pnl_id = _admin_panels.get(chat_id)
    if pnl_id:
        try:
            await message.bot.delete_message(chat_id, pnl_id)
        except:
            pass
        _admin_panels.pop(chat_id, None)

    try:
        await message.delete()
    except:
        pass

    open_tickets = await get_open_tickets()

    if not open_tickets:
        msg = await message.answer("Нет открытых тикетов 👌")
        _admin_panels[chat_id] = msg.message_id
        return

    text = "Открытые тикеты 📂:\n\n"
    keyboard = []

    for tid, info in open_tickets.items():
        user_id = info["user_id"]
        text += f"• {tid} — от {user_id}\n"
        keyboard.append([
            InlineKeyboardButton(
                text=f"Открыть {tid}",
                callback_data=f"open:{tid}"
            )
        ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    pnl_msg = await message.answer(text, reply_markup=markup)
    _admin_panels[chat_id] = pnl_msg.message_id

@router.callback_query(lambda c: c.data.startswith("open:"))
async def open_ticket_cb(call: CallbackQuery):
    chat_id = call.message.chat.id
    ticket_id = call.data.split(":")[1]
    ticket = await get_ticket(ticket_id)

    if not ticket:
        await call.answer("Тикет не найден", show_alert=True)
        return

    user_id = ticket["user_id"]
    msgs = get_ticket_messages(ticket_id)

    pnl_id = _admin_panels.get(chat_id)
    if pnl_id:
        try:
            await call.bot.delete_message(chat_id, pnl_id)
        except:
            pass

    text = f"Тикет {ticket_id}\n\n"
    for m in msgs[-10:]:
        sender = "Юзер" if m["from"] == "user" else "Админ"
        text += f"{sender}: {m['text']}\n"

    open_msg = await call.message.answer(
        text,
        reply_markup=ticket_buttons(ticket_id, user_id)
    )
    _admin_open_msgs[chat_id] = open_msg.message_id

    await call.answer()


_admin_reply_state = {}

@router.callback_query(lambda c: c.data.startswith("reply:"))
async def reply_ticket_cb(call: CallbackQuery):
    chat_id = call.message.chat.id

    msg_id = _admin_open_msgs.get(chat_id)
    if msg_id:
        try:
            await call.bot.delete_message(chat_id, msg_id)
        except:
            pass

    ticket_id = call.data.split(":")[1]
    _admin_reply_state[chat_id] = ticket_id

    await call.message.answer(
        f"Напиши сообщение, которое отправится пользователю в тикете {ticket_id}"
    )
    await call.answer()




@router.message()
async def admin_reply(message: Message):
    chat_id = message.chat.id

    if chat_id not in _admin_reply_state:
        return

    ticket_id = _admin_reply_state[chat_id]
    ticket = await get_ticket(ticket_id)

    if not ticket:
        await message.answer("Ошибка: тикет исчез")
        _admin_reply_state.pop(chat_id, None)
        return

    user_id = ticket["user_id"]
    text = message.text

    await add_message(ticket_id, "admin", text)
    await safe_send(user_id, text)

    await message.answer("Отправлено ✔️")
    _admin_reply_state.pop(chat_id, None)



@router.callback_query(lambda c: c.data.startswith("close:"))
async def close_ticket_cb(call: CallbackQuery):
    chat_id = call.message.chat.id

    msg_id = _admin_open_msgs.get(chat_id)
    if msg_id:
        try:
            await call.bot.delete_message(chat_id, msg_id)
        except:
            pass

    ticket_id = call.data.split(":")[1]
    ticket = await get_ticket(ticket_id)

    if not ticket:
        await call.answer("Тикет не найден", show_alert=True)
        return

    await update_ticket_status(ticket_id, "closed")
    await set_current_ticket(int(ticket["user_id"]), None)
    await set_admin_notified(int(ticket["user_id"]), False)
    await call.message.answer(f"Тикет {ticket_id} закрыт ❌")

    await safe_send(
        int(ticket["user_id"]),
        f"Тикет {ticket_id} закрыт. Если проблема осталась — просто напиши снова."
    )

    await call.answer()

@router.callback_query(lambda c: c.data == "admin_panel")
async def open_panel_from_button(call: CallbackQuery):
    try:
        await call.message.delete()
    except:
        pass

    temp_msg = await call.message.bot.send_message(
        call.from_user.id,
        "Открываю панель..."
    )

    await admin_panel(temp_msg)

    try:
        await temp_msg.delete()
    except:
        pass

    await call.answer()
