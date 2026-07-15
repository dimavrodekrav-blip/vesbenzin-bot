from aiogram import Router

from handlers import admin as admin_handlers
from handlers import settings as settings_handlers
from handlers import user as user_handlers


def setup_routers() -> Router:
    root = Router()
    root.include_router(user_handlers.router)
    root.include_router(settings_handlers.router)
    root.include_router(admin_handlers.router)
    return root