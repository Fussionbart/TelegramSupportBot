import json
import os
import threading


class JsonStorage:

    def __init__(self, path: str):
        self.path = path
        self.lock = threading.Lock()

        # создаём файл, если его нет
        self._ensure_exists()

    def _ensure_exists(self):
        if not os.path.exists(self.path):
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                f.write("{}")

    def load(self) -> dict:
        with self.lock:
            with open(self.path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}

    def save(self, data: dict):
        with self.lock:
            temp_path = self.path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # заменяем оригинальный файл
            os.replace(temp_path, self.path)

    def update(self, callback):
        with self.lock:
            data = self.load()
            callback(data)
            self.save(data)
