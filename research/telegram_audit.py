#!/usr/bin/env python3
"""Аудит TG-ботов и каналов про бензин через личный аккаунт (Telethon).

Первый запуск: введите код из Telegram (и 2FA, если включена).
Повторные: сессия в research/.tg_session.session
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.custom.message import Message
from telethon.tl.types import (
    KeyboardButton,
    KeyboardButtonCallback,
    KeyboardButtonUrl,
    ReplyInlineMarkup,
    ReplyKeyboardMarkup,
)

ROOT = Path(__file__).resolve().parent.parent
RESEARCH_DIR = Path(__file__).resolve().parent
SESSION_PATH = RESEARCH_DIR / ".tg_session"

BOTS = [
    "benzin_status_bot",
    "gdebenzin_bot",
    "gdezhebenz_bot",
]

CHANNELS = [
    "gdebenzru",
    "gde_benz_rf",
    "benzinmap",
    "gdezapravitsya",
]

START_COMMANDS = ["/start", "/help", "/menu"]


@dataclass
class ButtonInfo:
    text: str
    kind: str
    data: str | None = None


@dataclass
class MessageInfo:
    id: int
    date: str
    out: bool
    text: str
    buttons: list[ButtonInfo] = field(default_factory=list)
    media: str | None = None


@dataclass
class EntityAudit:
    username: str
    kind: str
    title: str | None = None
    about: str | None = None
    participants_count: int | None = None
    history: list[MessageInfo] = field(default_factory=list)
    after_start: list[MessageInfo] = field(default_factory=list)
    error: str | None = None


def _serialize_buttons(message: Message) -> list[ButtonInfo]:
    markup = message.reply_markup
    if not markup:
        return []

    buttons: list[ButtonInfo] = []

    if isinstance(markup, ReplyKeyboardMarkup):
        for row in markup.rows:
            for btn in row.buttons:
                if isinstance(btn, KeyboardButton):
                    buttons.append(ButtonInfo(text=btn.text, kind="reply"))
    elif isinstance(markup, ReplyInlineMarkup):
        for row in markup.rows:
            for btn in row.buttons:
                if isinstance(btn, KeyboardButtonCallback):
                    buttons.append(
                        ButtonInfo(
                            text=btn.text,
                            kind="inline_callback",
                            data=btn.data.decode("utf-8", errors="replace"),
                        )
                    )
                elif isinstance(btn, KeyboardButtonUrl):
                    buttons.append(
                        ButtonInfo(text=btn.text, kind="inline_url", data=btn.url)
                    )
                else:
                    buttons.append(ButtonInfo(text=getattr(btn, "text", "?"), kind="inline_other"))
    return buttons


def _serialize_message(message: Message) -> MessageInfo:
    media = None
    if message.photo:
        media = "photo"
    elif message.document:
        media = "document"
    elif message.video:
        media = "video"
    elif message.sticker:
        media = "sticker"

    return MessageInfo(
        id=message.id,
        date=message.date.replace(tzinfo=timezone.utc).isoformat(),
        out=bool(message.out),
        text=message.message or "",
        buttons=_serialize_buttons(message),
        media=media,
    )


async def _fetch_history(client: TelegramClient, entity: Any, limit: int = 12) -> list[MessageInfo]:
    messages: list[MessageInfo] = []
    async for msg in client.iter_messages(entity, limit=limit):
        messages.append(_serialize_message(msg))
    messages.reverse()
    return messages


async def _audit_bot(client: TelegramClient, username: str) -> EntityAudit:
    audit = EntityAudit(username=username, kind="bot")
    try:
        entity = await client.get_entity(username)
        audit.title = getattr(entity, "first_name", None) or getattr(entity, "title", None)
        audit.about = getattr(entity, "about", None)

        audit.history = await _fetch_history(client, entity, limit=15)

        max_id = max((m.id for m in audit.history), default=0)
        for cmd in START_COMMANDS:
            await client.send_message(entity, cmd)
            await asyncio.sleep(2.0)

        fresh: list[MessageInfo] = []
        async for msg in client.iter_messages(entity, limit=20):
            if msg.id <= max_id:
                continue
            fresh.append(_serialize_message(msg))
        fresh.reverse()
        audit.after_start = fresh[-10:]
    except Exception as exc:
        audit.error = f"{type(exc).__name__}: {exc}"
    return audit


async def _audit_channel(client: TelegramClient, username: str) -> EntityAudit:
    audit = EntityAudit(username=username, kind="channel")
    try:
        entity = await client.get_entity(username)
        full = await client.get_entity(entity)
        audit.title = getattr(full, "title", None)
        audit.about = getattr(full, "about", None)

        try:
            from telethon.tl.functions.channels import GetFullChannelRequest

            full_info = await client(GetFullChannelRequest(channel=entity))
            audit.participants_count = full_info.full_chat.participants_count
            if not audit.about:
                audit.about = full_info.full_chat.about
        except Exception:
            pass

        audit.history = await _fetch_history(client, entity, limit=8)
    except Exception as exc:
        audit.error = f"{type(exc).__name__}: {exc}"
    return audit


def _load_config() -> tuple[int, str, str | None]:
    load_dotenv(ROOT / ".env")
    api_id = os.getenv("TG_API_ID", "").strip()
    api_hash = os.getenv("TG_API_HASH", "").strip()
    phone = os.getenv("TG_PHONE", "").strip() or None

    if not api_id or not api_hash:
        print(
            "\nНужны TG_API_ID и TG_API_HASH в .env\n"
            "Получить: https://my.telegram.org → API development tools\n",
            file=sys.stderr,
        )
        sys.exit(1)

    return int(api_id), api_hash, phone


async def main() -> None:
    api_id, api_hash, phone = _load_config()

    extra_bots = os.getenv("TG_AUDIT_BOTS", "").strip()
    extra_channels = os.getenv("TG_AUDIT_CHANNELS", "").strip()
    bots = BOTS + [b.strip().lstrip("@") for b in extra_bots.split(",") if b.strip()]
    channels = CHANNELS + [c.strip().lstrip("@") for c in extra_channels.split(",") if c.strip()]

    client = TelegramClient(str(SESSION_PATH), api_id, api_hash)
    await client.start(phone=phone)

    me = await client.get_me()
    print(f"Вошли как: {me.first_name} (@{me.username or 'без username'})")

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "account": {"id": me.id, "username": me.username, "phone": me.phone},
        "bots": [],
        "channels": [],
    }

    for username in bots:
        print(f"  бот @{username}...")
        audit = await _audit_bot(client, username)
        report["bots"].append(asdict(audit))

    for username in channels:
        print(f"  канал @{username}...")
        audit = await _audit_channel(client, username)
        report["channels"].append(asdict(audit))

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESEARCH_DIR / f"audit_report_{ts}.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nГотово: {out_path}")
    print("\n--- Краткая сводка ---")
    for item in report["bots"]:
        name = item["username"]
        if item.get("error"):
            print(f"@{name}: ОШИБКА — {item['error']}")
            continue
        msgs = item.get("after_start") or item.get("history") or []
        last = msgs[-1] if msgs else {}
        preview = (last.get("text") or "")[:120].replace("\n", " ")
        btn_count = len(last.get("buttons") or [])
        print(f"@{name}: {len(msgs)} сообщ., кнопок в последнем: {btn_count}")
        if preview:
            print(f"  → {preview}")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())