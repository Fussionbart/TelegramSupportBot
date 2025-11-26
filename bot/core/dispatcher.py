from aiogram import Dispatcher

# импортируем роутеры
from bot.handlers.user import router as user_router
from bot.handlers.admin import router as admin_router


def register_all_handlers(dp: Dispatcher):
    """
    Здесь подключаем все хендлеры проекта.
    """

    # порядок важен:
    # 1) админские — чтобы раньше ловили админа
    # 2) пользовательские — чтобы ловили всех остальных

    dp.include_router(admin_router)
    dp.include_router(user_router)
