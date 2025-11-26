import time
import os
import json
from typing import Optional

from config import TICKETS_PATH, MESSAGES_PATH
from bot.core.json_storage import JsonStorage

# глобальный стор для tickets.json
_tickets = JsonStorage(TICKETS_PATH)


def _ticket_messages_path(ticket_id: int) -> str:
    """Путь к файлу с историей сообщений."""
    return os.path.join(MESSAGES_PATH, f"ticket_{ticket_id}.json")


def create_ticket(user_id: int) -> int:
    """
    Создаёт новый тикет, присваивает id, создаёт файл истории.
    Возвращает ID тикета.
    """
    user_id = str(user_id)

    def _update(data):
        # вычисляем новый тикет ID
        new_id = 1
        if data:
            new_id = max(int(k) for k in data.keys()) + 1

        # создаём новую запись
        data[str(new_id)] = {
            "user_id": user_id,
            "status": "open",
            "created_at": int(time.time()),
            "updated_at": int(time.time())
        }

        # создаём пустой файл для сообщений
        os.makedirs(MESSAGES_PATH, exist_ok=True)
        with open(_ticket_messages_path(new_id), "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

        # возвращаем ID тикета наружу
        data["_last_created_id"] = new_id

    _tickets.update(_update)

    # вытаскиваем id, который мы сохранили
    data = _tickets.load()
    ticket_id = data["_last_created_id"]
    del data["_last_created_id"]
    _tickets.save(data)

    return ticket_id


def add_message(ticket_id: int, sender: str, text: str):
    """
    Добавляет сообщение в историю тикета.
    sender: 'user' или 'admin'
    """
    path = _ticket_messages_path(ticket_id)

    # читаем историю
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = []

    # добавляем сообщение
    history.append({
        "from": sender,
        "text": text,
        "time": int(time.time())
    })

    # сохраняем историю
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    # обновляем updated_at в tickets.json
    def _update(data):
        t = str(ticket_id)
        if t in data:
            data[t]["updated_at"] = int(time.time())

    _tickets.update(_update)


def get_ticket(ticket_id: int) -> Optional[dict]:
    """Возвращает тикет по ID или None."""
    data = _tickets.load()
    return data.get(str(ticket_id))


def get_ticket_messages(ticket_id: int) -> list:
    """Возвращает список сообщений тикета."""
    path = _ticket_messages_path(ticket_id)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_ticket_status(ticket_id: int, status: str):
    """
    Ставит тикету новый статус:
    open / in_progress / closed
    """
    def _update(data):
        t = str(ticket_id)
        if t in data:
            data[t]["status"] = status
            data[t]["updated_at"] = int(time.time())

    _tickets.update(_update)


def get_open_tickets() -> dict:
    """Возвращает все тикеты со статусом open."""
    data = _tickets.load()
    return {tid: t for tid, t in data.items() if t.get("status") == "open"}


def get_recent_closed(limit: int = 10) -> list:
    """Возвращает N последних закрытых тикетов."""
    data = _tickets.load()

    closed = [
        (tid, info)
        for tid, info in data.items()
        if info.get("status") == "closed"
    ]

    # сортируем по updated_at
    closed.sort(key=lambda x: x[1]["updated_at"], reverse=True)

    return closed[:limit]
