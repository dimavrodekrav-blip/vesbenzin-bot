#!/bin/bash
BASE=https://cdn.jsdelivr.net/gh/dimavrodekrav-blip/vesbenzin-bot@main
mkdir -p "deploy"
mkdir -p "handlers"
mkdir -p "parsers"
mkdir -p "research"
mkdir -p "services"
FAILED=0
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "deploy/deploy.sh" "$BASE/deploy/deploy.sh"; then echo "OK  deploy/deploy.sh"; else echo "FAIL deploy/deploy.sh"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "deploy/setup_env.sh" "$BASE/deploy/setup_env.sh"; then echo "OK  deploy/setup_env.sh"; else echo "FAIL deploy/setup_env.sh"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "deploy/vesbenzin-bot.service" "$BASE/deploy/vesbenzin-bot.service"; then echo "OK  deploy/vesbenzin-bot.service"; else echo "FAIL deploy/vesbenzin-bot.service"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "handlers/__init__.py" "$BASE/handlers/__init__.py"; then echo "OK  handlers/__init__.py"; else echo "FAIL handlers/__init__.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "handlers/admin.py" "$BASE/handlers/admin.py"; then echo "OK  handlers/admin.py"; else echo "FAIL handlers/admin.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "handlers/settings.py" "$BASE/handlers/settings.py"; then echo "OK  handlers/settings.py"; else echo "FAIL handlers/settings.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "handlers/user.py" "$BASE/handlers/user.py"; then echo "OK  handlers/user.py"; else echo "FAIL handlers/user.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "parsers/__init__.py" "$BASE/parsers/__init__.py"; then echo "OK  parsers/__init__.py"; else echo "FAIL parsers/__init__.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "parsers/base.py" "$BASE/parsers/base.py"; then echo "OK  parsers/base.py"; else echo "FAIL parsers/base.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "parsers/gdebenz.py" "$BASE/parsers/gdebenz.py"; then echo "OK  parsers/gdebenz.py"; else echo "FAIL parsers/gdebenz.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "parsers/pinggi.py" "$BASE/parsers/pinggi.py"; then echo "OK  parsers/pinggi.py"; else echo "FAIL parsers/pinggi.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "research/requirements.txt" "$BASE/research/requirements.txt"; then echo "OK  research/requirements.txt"; else echo "FAIL research/requirements.txt"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "research/run_audit.sh" "$BASE/research/run_audit.sh"; then echo "OK  research/run_audit.sh"; else echo "FAIL research/run_audit.sh"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "research/setup_tg.sh" "$BASE/research/setup_tg.sh"; then echo "OK  research/setup_tg.sh"; else echo "FAIL research/setup_tg.sh"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "research/telegram_audit.py" "$BASE/research/telegram_audit.py"; then echo "OK  research/telegram_audit.py"; else echo "FAIL research/telegram_audit.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "services/notifier.py" "$BASE/services/notifier.py"; then echo "OK  services/notifier.py"; else echo "FAIL services/notifier.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "services/poller.py" "$BASE/services/poller.py"; then echo "OK  services/poller.py"; else echo "FAIL services/poller.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "services/status_mapper.py" "$BASE/services/status_mapper.py"; then echo "OK  services/status_mapper.py"; else echo "FAIL services/status_mapper.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o ".env.example" "$BASE/.env.example"; then echo "OK  .env.example"; else echo "FAIL .env.example"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o ".gitignore" "$BASE/.gitignore"; then echo "OK  .gitignore"; else echo "FAIL .gitignore"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "bot.py" "$BASE/bot.py"; then echo "OK  bot.py"; else echo "FAIL bot.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "config.py" "$BASE/config.py"; then echo "OK  config.py"; else echo "FAIL config.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "constants.py" "$BASE/constants.py"; then echo "OK  constants.py"; else echo "FAIL constants.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "database.py" "$BASE/database.py"; then echo "OK  database.py"; else echo "FAIL database.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "keyboards.py" "$BASE/keyboards.py"; then echo "OK  keyboards.py"; else echo "FAIL keyboards.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "main.py" "$BASE/main.py"; then echo "OK  main.py"; else echo "FAIL main.py"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "README.md" "$BASE/README.md"; then echo "OK  README.md"; else echo "FAIL README.md"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "requirements.txt" "$BASE/requirements.txt"; then echo "OK  requirements.txt"; else echo "FAIL requirements.txt"; FAILED=1; fi
if curl --retry 8 --retry-delay 2 --retry-all-errors --max-time 15 -sf -o "states.py" "$BASE/states.py"; then echo "OK  states.py"; else echo "FAIL states.py"; FAILED=1; fi
echo "---"
echo "TOTAL: $(find . -type f | wc -l) files, FAILED=$FAILED"
