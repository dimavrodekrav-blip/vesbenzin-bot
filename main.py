"""Точка входа: Telegram-бот «где есть бензин» с push-уведомлениями."""

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import TELEGRAM_TOKEN, logger, require_token
from constants import BOT_VERSION
from database import Database
from handlers import setup_routers
from handlers import admin as admin_handlers
from handlers import settings as settings_handlers
from handlers import user as user_handlers
from services.notifier import NotificationQueue
from services.poller import SourcePoller


async def run() -> None:
    require_token()
    bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    db = Database()
    user_handlers.init(db)
    settings_handlers.init(db)
    admin_handlers.init(db)
    dp.include_router(setup_routers())

    notifier = NotificationQueue(bot, db)
    notifier.start()
    poller = SourcePoller(db, notifier)
    poller.start()

    logger.info("vesbenzin-bot v%s starting", BOT_VERSION)
    try:
        me = await bot.get_me()
        logger.info("ready as @%s", me.username)
        await dp.start_polling(bot)
    finally:
        await poller.stop()
        await notifier.stop()
        await bot.session.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("stopped")