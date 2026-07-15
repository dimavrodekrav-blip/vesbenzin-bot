#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/.." && pwd)"
VENV="$DIR/.venv"

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Нет $ROOT/.env"
  echo "Запусти: $DIR/setup_tg.sh"
  exit 1
fi

if ! grep -qE '^TG_API_ID=[0-9]+' "$ROOT/.env"; then
  echo "В $ROOT/.env нет TG_API_ID"
  echo "Запусти: $DIR/setup_tg.sh"
  exit 1
fi

if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
fi

"$VENV/bin/pip" install -q -r "$DIR/requirements.txt"
"$VENV/bin/python" "$DIR/telegram_audit.py"