from aiogram import F, Router
from aiogram.types import CallbackQuery

from constants import AREAS, FUELS, NETWORKS, STATUSES
from database import Database
from handlers.user import render_settings
from keyboards import Keyboards

router = Router()
_db: Database | None = None

PICKERS = {
    "area": ("📍 Выберите районы и города", AREAS, Keyboards.area_picker),
    "fuel": ("⛽ Выберите топливо", FUELS, Keyboards.fuel_picker),
    "status": ("⚠️ При каких статусах присылать push", STATUSES, Keyboards.status_picker),
    "network": ("🏪 Сети АЗС (необязательно)", NETWORKS, Keyboards.network_picker),
}


def init(db: Database) -> None:
    global _db
    _db = db


@router.callback_query(F.data.startswith("set:"))
async def open_set(callback: CallbackQuery) -> None:
    key = callback.data.split(":", 1)[1]
    cfg = PICKERS.get(key)
    if not cfg or _db is None:
        await callback.answer("Ошибка")
        return
    title, _items, picker = cfg
    selected = set(_db.get_filters(callback.from_user.id, key))
    await callback.message.edit_text(
        render_settings(callback.from_user.id) + f"\n\n{title}:",
        reply_markup=picker(selected),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle:"))
async def toggle(callback: CallbackQuery) -> None:
    _, key, value = callback.data.split(":", 2)
    cfg = PICKERS.get(key)
    if not cfg or _db is None:
        await callback.answer("Ошибка")
        return
    _db.toggle_filter(callback.from_user.id, key, value)
    title, _items, picker = cfg
    selected = set(_db.get_filters(callback.from_user.id, key))
    await callback.message.edit_text(
        render_settings(callback.from_user.id) + f"\n\n{title}:",
        reply_markup=picker(selected),
        parse_mode="HTML",
    )
    await callback.answer()