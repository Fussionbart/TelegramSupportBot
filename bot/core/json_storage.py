import json
import os
import asyncio

class JsonStorage:

    def __init__(self, path: str):
        self.path = path
        self.lock = asyncio.Lock()

    def _ensure_exists(self):
        directory = os.path.dirname(self.path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                f.write("{}")

    async def load(self) -> dict:
        self._ensure_exists()
        async with self.lock:
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}

    async def save(self, data: dict):
        self._ensure_exists()
        async with self.lock:
            temp_path = self.path + ".tmp"

            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            os.replace(temp_path, self.path)


    async def update(self, callback):
        self._ensure_exists()
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}

        callback(data)

        async with self.lock:
            temp_path = self.path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            os.replace(temp_path, self.path)

