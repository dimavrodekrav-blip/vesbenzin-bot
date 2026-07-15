#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "$DIR/.env" ]; then
  echo ".env уже есть"
  exit 0
fi
cp "$DIR/.env.example" "$DIR/.env"
echo "Создан $DIR/.env — вставьте TELEGRAM_TOKEN от @BotFather (@vesbenzin_msk_bot)"