#!/bin/bash
set -e
# Запускаем бэкенд в фоне
uv run uvicorn ping_pong.main:app --host 0.0.0.0 --port 8080 &
# Ждем запуска бэкенда
sleep 2
# Запускаем Nginx в foreground
exec nginx -g "daemon off;"
