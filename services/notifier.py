import asyncio
import time
from dataclasses import dataclass
from typing import Any

from aiogram import Bot

from config import (
    NOTIFY_COOLDOWN_HOURS,
    NOTIFY_GLOBAL_RATE,
    NOTIFY_PER_CHAT_SEC,
    STATUS_FRESH_MINUTES,
    logger,
)
from constants import FUELS, STATUS_ICONS
from database import Database
from keyboards import Keyboards


@dataclass
class NotifyJob:
    user_id: int
    station_id: str
    fuel_key: str
    status_key: str
    text: str


@dataclass
class StatusChange:
    station_id: str
    fuel_key: str
    old_status: str | None
    new_status: str
    station: dict[str, Any]


class NotificationQueue:
    def __init__(self, bot: Bot, db: Database):
        self.bot = bot
        self.db = db
        self._queue: asyncio.Queue[NotifyJob | None] = asyncio.Queue()
        self._tokens = NOTIFY_GLOBAL_RATE
        self._refill_at = time.monotonic()
        self._last_chat: dict[int, float] = {}
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        if self._task:
            await self._queue.put(None)
            await self._task
            self._task = None

    async def enqueue(self, job: NotifyJob) -> None:
        await self._queue.put(job)

    def _refill(self) -> None:
        now = time.monotonic()
        if now - self._refill_at >= 1:
            self._tokens = min(
                NOTIFY_GLOBAL_RATE,
                self._tokens + int(now - self._refill_at) * NOTIFY_GLOBAL_RATE,
            )
            self._refill_at = now

    async def _worker(self) -> None:
        while True:
            job = await self._queue.get()
            if job is None:
                break
            try:
                await self._send(job)
            except Exception:
                logger.exception("notify failed user=%s", job.user_id)
            self._queue.task_done()

    async def _send(self, job: NotifyJob) -> None:
        while True:
            self._refill()
            now = time.monotonic()
            if self._tokens <= 0 or now - self._last_chat.get(job.user_id, 0) < NOTIFY_PER_CHAT_SEC:
                await asyncio.sleep(0.05)
                continue
            try:
                await self.bot.send_message(
                    job.user_id,
                    job.text,
                    parse_mode="HTML",
                    reply_markup=Keyboards.push_actions(job.station_id, job.fuel_key),
                )
            except Exception as exc:
                logger.warning("skip user %s: %s", job.user_id, exc)
                return
            self._tokens -= 1
            self._last_chat[job.user_id] = time.monotonic()
            self.db.log_notification(job.user_id, job.station_id, job.fuel_key, job.status_key)
            return


def format_push(station: dict, fuel_key: str, status_key: str) -> str:
    fuel = dict(FUELS).get(fuel_key, fuel_key)
    icon = STATUS_ICONS.get(status_key, "⚪")
    title = "🚗 <b>Можно ехать за бензином</b>" if status_key == "free" else "⛽ <b>Обновление по АЗС</b>"
    lines = [
        title,
        f"{icon} <b>{station['name']}</b>",
        f"📍 {station.get('address') or '—'}",
        f"⛽ {fuel}",
    ]
    if station.get("queue_hint"):
        lines.append(f"🚙 Очередь: {station['queue_hint']}")
    if station.get("limit_hint"):
        lines.append(f"📏 Лимит: {station['limit_hint']}")
    if station.get("status_updated"):
        lines.append(f"🕐 Отметка: {station['status_updated']}")
    lines.append("\nПодтвердите, пожалуйста, актуально ли сейчас.")
    return "\n".join(lines)


def _should_notify_user(
    db: Database,
    user_id: int,
    change: StatusChange,
) -> bool:
    areas = set(db.get_filters(user_id, "area"))
    fuels = set(db.get_filters(user_id, "fuel"))
    statuses = set(db.get_filters(user_id, "status"))
    networks = set(db.get_filters(user_id, "network"))

    if not areas or not fuels or not statuses:
        return False
    if change.station.get("area_key") not in areas:
        return False
    if change.fuel_key not in fuels:
        return False
    if change.new_status not in statuses:
        return False
    if networks and change.station.get("network_key") not in networks:
        return False
    if not db.is_status_fresh(change.station_id, change.fuel_key, STATUS_FRESH_MINUTES):
        return False
    if db.was_notified_recently(user_id, change.station_id, change.fuel_key, NOTIFY_COOLDOWN_HOURS):
        return False
    return True


async def dispatch_changes(
    db: Database,
    queue: NotificationQueue,
    changes: list[StatusChange],
) -> int:
    if not changes:
        return 0
    queued = 0
    for user in db.get_subscribed_users():
        uid = user["user_id"]
        if db.is_snoozed(uid):
            continue
        for change in changes:
            if not _should_notify_user(db, uid, change):
                continue
            await queue.enqueue(
                NotifyJob(
                    user_id=uid,
                    station_id=change.station_id,
                    fuel_key=change.fuel_key,
                    status_key=change.new_status,
                    text=format_push(change.station, change.fuel_key, change.new_status),
                )
            )
            queued += 1
    return queued