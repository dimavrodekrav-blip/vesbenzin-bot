import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
BOT_USERNAME = os.getenv("BOT_USERNAME", "vesbenzin_msk_bot").strip()
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
DB_PATH = os.getenv("DB_PATH", "vesbenzin_data.db")

POLL_INTERVAL_SEC = int(os.getenv("POLL_INTERVAL_SEC", "180"))
NOTIFY_GLOBAL_RATE = int(os.getenv("NOTIFY_GLOBAL_RATE", "25"))
NOTIFY_PER_CHAT_SEC = float(os.getenv("NOTIFY_PER_CHAT_SEC", "1.0"))
NOTIFY_COOLDOWN_HOURS = int(os.getenv("NOTIFY_COOLDOWN_HOURS", "3"))
SNOOZE_HOURS = int(os.getenv("SNOOZE_HOURS", "24"))
STATUS_FRESH_MINUTES = int(os.getenv("STATUS_FRESH_MINUTES", "45"))
STATUS_DEBOUNCE_MINUTES = int(os.getenv("STATUS_DEBOUNCE_MINUTES", "8"))

DONATE_URL = os.getenv("DONATE_URL", "").strip()


def require_token() -> None:
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN не задан в .env")

logger = logging.getLogger("vesbenzin_bot")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        "bot.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(console)
    logger.addHandler(file_handler)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS