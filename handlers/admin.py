from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import is_admin
from database import Database

router = Router()
_db: Database | None = None


def init(db: Database) -> None:
    global _db
    _db = db


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not message.from_user or not is_admin(message.from_user.id):
        return
    if _db is None:
        return
    s = _db.get_admin_stats()
    await message.answer(
        "<b>Статистика бота</b>\n\n"
        f"👤 Пользователей: {s['users']}\n"
        f"🔔 Активных подписок: {s['active_subscribers']}\n"
        f"⛽ АЗС в базе: {s['stations']}\n"
        f"📊 Статусов: {s['status_rows']}\n"
        f"📨 Push за 24ч: {s['pushes_24h']}\n"
        f"✅ Отзывов за 24ч: {s['feedback_24h']}",
        parse_mode="HTML",
    )