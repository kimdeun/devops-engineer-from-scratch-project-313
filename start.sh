#!/bin/bash
set -e

# Получаем PORT из переменной окружения (Render передает его, по умолчанию 80)
PORT=${PORT:-80}

# Заменяем ${PORT} в nginx.conf на реальное значение
sed -i "s/\${PORT}/$PORT/g" /etc/nginx/nginx.conf

# Запускаем бэкенд в фоне на внутреннем порту 8080
uv run uvicorn ping_pong.main:app --host 0.0.0.0 --port 8080 &

# Ждем запуска бэкенда
sleep 2

# Запускаем Nginx в foreground на порту из переменной PORT
exec nginx -g "daemon off;"
