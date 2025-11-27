from aiogram import Dispatcher
from bot.handlers.user import router as user_router
from bot.handlers.admin import router as admin_router

def register_all_handlers(dp: Dispatcher):
    dp.include_router(admin_router)
    dp.include_router(user_router)

