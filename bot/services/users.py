import time
from config import USERS_PATH
from bot.core.json_storage import JsonStorage


# создаём глобальный стор
_users = JsonStorage(USERS_PATH)


def get_user(user_id: int) -> dict:
    """
    Возвращает словарь с данными пользователя.
    Если пользователя ещё нет — создаёт новую запись.
    """
    user_id = str(user_id)

    data = _users.load()

    if user_id not in data:
        data[user_id] = {
            "current_ticket_id": None,
            "last_message_at": None,
            "ack_planned": False
        }
        _users.save(data)

    return data[user_id]


def update_user(user_id: int, **fields):
    """
    Обновляет указанные поля пользователя.
    Пример: update_user(123, current_ticket_id=5, ack_planned=True)
    """
    user_id = str(user_id)

    def _update(data):
        if user_id not in data:
            data[user_id] = {
                "current_ticket_id": None,
                "last_message_at": None,
                "ack_planned": False
            }

        for key, value in fields.items():
            data[user_id][key] = value

    _users.update(_update)


def set_last_message(user_id: int):
    """ Обновляет отметку времени последнего сообщения пользователя. """
    update_user(user_id, last_message_at=int(time.time()))


def set_ack_planned(user_id: int, value: bool):
    """ Устанавливает флаг, что мы планируем автоответ. """
    update_user(user_id, ack_planned=value)


def set_current_ticket(user_id: int, ticket_id: int | None):
    """ Устанавливает ID текущего тикета. """
    update_user(user_id, current_ticket_id=ticket_id)


def get_last_message_time(user_id: int) -> int | None:
    return get_user(user_id).get("last_message_at")


def get_current_ticket(user_id: int) -> int | None:
    return get_user(user_id).get("current_ticket_id")


def is_ack_planned(user_id: int) -> bool:
    return bool(get_user(user_id).get("ack_planned"))
