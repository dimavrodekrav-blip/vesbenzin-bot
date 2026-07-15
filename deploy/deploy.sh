#!/usr/bin/env bash
# Деплой ТОЛЬКО на отдельный VPS (не 45.133.209.193).
set -euo pipefail

SSH_KEY="${SSH_KEY:-$HOME/.ssh/vesbenzin_vps}"
REMOTE="${REMOTE:-root@YOUR_NEW_VPS_IP}"
REMOTE_DIR="/opt/vesbenzin_bot"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE="vesbenzin-bot.service"
BOT_USER="vesbenzin"

rsync -avz --delete \
  --exclude '.venv' --exclude 'vesbenzin_data.db*' --exclude '.env' \
  --exclude '__pycache__' --exclude '.git' \
  -e "ssh -i ${SSH_KEY}" \
  "${LOCAL_DIR}/" "${REMOTE}:${REMOTE_DIR}/"

ssh -i "${SSH_KEY}" "${REMOTE}" bash -s <<EOF
set -euo pipefail
id -u ${BOT_USER} &>/dev/null || useradd -m -s /bin/bash ${BOT_USER}
chown -R ${BOT_USER}:${BOT_USER} ${REMOTE_DIR}
test -f ${REMOTE_DIR}/.env || { echo "Создайте .env на сервере"; exit 1; }
if [ ! -d ${REMOTE_DIR}/.venv ]; then
  python3 -m venv ${REMOTE_DIR}/.venv
  ${REMOTE_DIR}/.venv/bin/pip install -r ${REMOTE_DIR}/requirements.txt
  chown -R ${BOT_USER}:${BOT_USER} ${REMOTE_DIR}/.venv
fi
cp ${REMOTE_DIR}/deploy/vesbenzin-bot.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable ${SERVICE} && systemctl restart ${SERVICE}
systemctl --no-pager status ${SERVICE}
EOF