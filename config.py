import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

ACK_DELAY = int(os.getenv("ACK_DELAY", 30))

USERS_PATH = os.getenv("USERS_PATH", "bot/data/users.json")
TICKETS_PATH = os.getenv("TICKETS_PATH", "bot/data/tickets.json")
MESSAGES_PATH = os.getenv("MESSAGES_PATH", "bot/data/messages")