#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"

echo "=== Настройка Telethon для аудита ботов ==="
echo ""

if [[ -f "$ENV_FILE" ]] && grep -q "TG_API_ID=." "$ENV_FILE" 2>/dev/null; then
  echo "В $ENV_FILE уже есть TG_API_ID — редактируй файл вручную или удали строки TG_*"
  exit 0
fi

echo "1) Открой: https://my.telegram.org/apps"
echo "2) Войди номером телефона (код придёт в Telegram)"
echo ""
echo "Если видишь api_id и api_hash — приложение УЖЕ создано, Create new не нужен."
echo "Если форма Create new application даёт ERROR — см. подсказки ниже."
echo ""

read -r -p "TG_API_ID (число): " api_id
read -r -p "TG_API_HASH: " api_hash
read -r -p "TG_PHONE (+79...): " phone

if [[ ! -f "$ENV_FILE" ]]; then
  cp "$ROOT/.env.example" "$ENV_FILE"
fi

append_or_replace() {
  local key="$1" val="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    sed -i '' "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
  else
    printf '\n%s=%s\n' "$key" "$val" >> "$ENV_FILE"
  fi
}

append_or_replace "TG_API_ID" "$api_id"
append_or_replace "TG_API_HASH" "$api_hash"
append_or_replace "TG_PHONE" "$phone"

echo ""
echo "Сохранено в $ENV_FILE"
echo "Запуск аудита: cd $(dirname "$0") && ./run_audit.sh"