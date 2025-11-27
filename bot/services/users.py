import time
from config import USERS_PATH, ADMIN_ID
from bot.core.json_storage import JsonStorage

_users = JsonStorage(USERS_PATH)

async def get_user(user_id: int) -> dict:

    user_id = str(user_id)

    data = await _users.load()

    if user_id not in data:
        data[user_id] = {
            "current_ticket_id": None,
            "last_message_at": None,
            "ack_planned": False,
            "admin_notified": False
        }
        await _users.save(data)

    return data[user_id]

async def update_user(user_id: int, **fields):
    user_id = str(user_id)

    # Загружаем текущие данные
    data = await _users.load()

    if user_id not in data:
        data[user_id] = {
            "current_ticket_id": None,
            "last_message_at": None,
            "ack_planned": False,
            "ticket_fresh": False
        }

    for key, value in fields.items():
        data[user_id][key] = value

    await _users.save(data)

async def set_last_message(user_id: int):
    await update_user(user_id, last_message_at=int(time.time()))

async def set_ack_planned(user_id: int, value: bool):
    await update_user(user_id, ack_planned=value)

async def set_current_ticket(user_id: int, ticket_id: int | None):
    await update_user(user_id, current_ticket_id=ticket_id)

async def get_last_message_time(user_id: int) -> int | None:
    user = await get_user(user_id)
    return user.get("last_message_at")

async def get_current_ticket(user_id: int) -> int | None:
    user = await get_user(user_id)
    return user.get("current_ticket_id")

async def is_ack_planned(user_id: int) -> bool:
    user = await get_user(user_id)
    return bool(user.get("ack_planned"))

async def was_admin_notified(user_id: int) -> bool:
    user = await get_user(user_id)
    return user.get("admin_notified", False)

async def set_admin_notified(user_id: int, value: bool):
    await update_user(user_id, admin_notified=value)

async def has_admin_started() -> bool:
    data = await _users.load()
    adm = str(ADMIN_ID)
    return data.get(adm, {}).get("admin_started", False)

async def set_admin_started():
    data = await _users.load()
    adm = str(ADMIN_ID)
    if adm not in data:
        data[adm] = {}
    data[adm]["admin_started"] = True
    await _users.save(data)
