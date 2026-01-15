#!/bin/bash
set -e

# Получаем PORT из переменной окружения (Render передает его)
# Если не установлен, используем 8080 по умолчанию
PORT=${PORT:-8080}

# Запускаем FastAPI напрямую на порту из переменной PORT
# Render сам управляет проксированием и балансировкой
exec uv run uvicorn ping_pong.main:app --host 0.0.0.0 --port "$PORT"
