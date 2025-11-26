from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import TOKEN


# Инициализируем бота
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")  # включим HTML разметку
)

# Создаём диспетчер
dp = Dispatcher()
