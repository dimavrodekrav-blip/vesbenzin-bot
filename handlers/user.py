import random

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import BOT_USERNAME, DONATE_URL, SNOOZE_HOURS, logger
from constants import (
    AREAS,
    CAPTCHA_EMOJIS,
    CAPTCHA_PROMPT,
    FUELS,
    HELP_TEXT,
    NETWORKS,
    STATUSES,
    WELCOME_TEXT,
)
from database import Database
from keyboards import Keyboards
from states import CaptchaState

router = Router()
_db: Database | None = None

LABELS = {
    "area": dict(AREAS),
    "fuel": dict(FUELS),
    "status": dict(STATUSES),
    "network": dict(NETWORKS),
}


def init(db: Database) -> None:
    global _db
    _db = db


def _dbx() -> Database:
    if _db is None:
        raise RuntimeError("DB not init")
    return _db


def _fmt(keys: list[str], mapping: dict[str, str]) -> str:
    return ", ".join(mapping.get(k, k) for k in keys) if keys else "не выбрано"


def render_settings(user_id: int) -> str:
    s = _dbx().get_settings(user_id)
    notify = "вкл ✅" if s["notifications_enabled"] else "выкл ❌"
    nets = _fmt(s["networks"], LABELS["network"])
    if not s["networks"]:
        nets = "все сети"
    return (
        "<b>Настройки поиска</b>\n\n"
        f"📍 Районы: {_fmt(s['areas'], LABELS['area'])}\n"
        f"⛽ Топливо: {_fmt(s['fuels'], LABELS['fuel'])}\n"
        f"⚠️ Статусы: {_fmt(s['statuses'], LABELS['status'])}\n"
        f"🏪 Сети: {nets}\n"
        f"🔔 Уведомления: {notify}"
    )


def _encode_station_id(station_id: str) -> str:
    return station_id.replace(":", "__", 1)


def _decode_station_id(raw: str) -> str:
    source, ext = raw.split("__", 1)
    return f"{source}:{ext}"


async def _captcha(message: Message, state: FSMContext) -> None:
    correct_emoji = random.choice(CAPTCHA_EMOJIS)
    options = [correct_emoji]
    while len(options) < 3:
        e = random.choice(CAPTCHA_EMOJIS)
        if e not in options:
            options.append(e)
    random.shuffle(options)
    await state.set_state(CaptchaState.waiting)
    await state.update_data(captcha_correct=options.index(correct_emoji))
    await message.answer(
        CAPTCHA_PROMPT.format(emoji=correct_emoji),
        reply_markup=Keyboards.captcha(options),
        parse_mode="HTML",
    )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user:
        return
    ref = None
    if message.text and " " in message.text:
        payload = message.text.split(maxsplit=1)[1]
        if payload.startswith("ref_") and payload[4:].isdigit():
            ref = int(payload[4:])
    _dbx().upsert_user(user.id, user.username, user.first_name, referrer_id=ref)
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=Keyboards.main_menu(), parse_mode="HTML")


@router.callback_query(F.data == "menu:main")
async def menu_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=Keyboards.main_menu(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:settings")
async def menu_settings(callback: CallbackQuery, state: FSMContext) -> None:
    user = _dbx().get_user(callback.from_user.id)
    if not user or not user.get("captcha_passed"):
        await _captcha(callback.message, state)
        await callback.answer()
        return
    await callback.message.edit_text(
        render_settings(callback.from_user.id) + "\n\nЧто настроить?",
        reply_markup=Keyboards.settings_root(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("captcha:"))
async def captcha_ok(callback: CallbackQuery, state: FSMContext) -> None:
    picked = int(callback.data.split(":")[1])
    data = await state.get_data()
    if data.get("captcha_correct") != picked:
        await callback.answer("Неверно", show_alert=True)
        await _captcha(callback.message, state)
        return
    _dbx().set_captcha_passed(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(
        render_settings(callback.from_user.id) + "\n\nЧто настроить?",
        reply_markup=Keyboards.settings_root(),
        parse_mode="HTML",
    )
    await callback.answer("Готово ✅")


@router.callback_query(F.data == "menu:status")
async def menu_status(callback: CallbackQuery) -> None:
    rows = _dbx().get_matching_stations(callback.from_user.id)
    if not rows:
        await callback.message.edit_text(
            "Сначала настройте район, топливо и статусы.",
            reply_markup=Keyboards.back_main(),
        )
        await callback.answer()
        return
    fuel_map = dict(FUELS)
    area_map = dict(AREAS)
    lines = ["<b>Текущий статус по вашим фильтрам</b>\n"]
    for r in rows[:15]:
        icon = {"free": "🟢", "limited": "🟡", "absent": "🔴"}.get(r["status_key"], "⚪")
        lines.append(
            f"{icon} <b>{r['name']}</b> — {fuel_map.get(r['fuel_key'], r['fuel_key'])}\n"
            f"   {area_map.get(r['area_key'], r['area_key'])}, {r.get('address') or ''}"
        )
    await callback.message.edit_text("\n".join(lines), reply_markup=Keyboards.back_main(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:notify")
async def menu_notify(callback: CallbackQuery) -> None:
    user = _dbx().get_user(callback.from_user.id) or {}
    enabled = not bool(user.get("notifications_enabled", 1))
    _dbx().set_notifications(callback.from_user.id, enabled)
    label = "включены ✅" if enabled else "выключены ❌"
    await callback.answer(f"Уведомления {label}", show_alert=True)


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery) -> None:
    await callback.message.edit_text(HELP_TEXT, reply_markup=Keyboards.back_main(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "menu:invite")
async def menu_invite(callback: CallbackQuery) -> None:
    username = BOT_USERNAME or "vesbenzin_msk_bot"
    link = f"https://t.me/{username}?start=ref_{callback.from_user.id}"
    await callback.message.edit_text(
        f"👥 <b>Пригласить друга</b>\n\n<code>{link}</code>",
        reply_markup=Keyboards.back_main(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "menu:donate")
async def menu_donate(callback: CallbackQuery) -> None:
    text = f"☕ <b>Поддержать проект</b>\n\n{DONATE_URL}" if DONATE_URL else "Ссылка доната не настроена."
    await callback.message.edit_text(text, reply_markup=Keyboards.back_main(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("push:"))
async def push_feedback(callback: CallbackQuery) -> None:
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer()
        return
    action, enc_station, fuel_key = parts[1], parts[2], parts[3]
    station_id = _decode_station_id(enc_station)
    uid = callback.from_user.id

    if action == "snooze":
        _dbx().set_snooze(uid, SNOOZE_HOURS)
        await callback.answer(f"Пауза на {SNOOZE_HOURS} ч", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return

    verdict = "confirmed" if action == "ok" else "denied"
    _dbx().log_push_feedback(uid, station_id, fuel_key, verdict)
    if action in ("ok", "no"):
        _dbx().apply_crowd_feedback(station_id, fuel_key, verdict)
    if action == "ok":
        await callback.answer("Спасибо! Это помогает другим водителям.", show_alert=True)
    else:
        await callback.answer("Понял, спасибо за отметку.", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)


@router.message(Command("settings"))
async def cmd_settings(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if not user:
        return
    _dbx().upsert_user(user.id, user.username, user.first_name)
    row = _dbx().get_user(user.id)
    if not row or not row.get("captcha_passed"):
        await _captcha(message, state)
        return
    await message.answer(
        render_settings(user.id) + "\n\nЧто настроить?",
        reply_markup=Keyboards.settings_root(),
        parse_mode="HTML",
    )