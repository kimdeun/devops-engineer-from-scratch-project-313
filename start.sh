#!/bin/bash
set -e

PORT=${PORT:-80}

echo "Starting application with PORT=$PORT"
echo "Checking nginx configuration..."
cat /etc/nginx/nginx.conf | grep -A 2 "listen" || echo "Warning: Could not find listen directive"

# Заменяем ${PORT} в nginx.conf на реальное значение
sed -i "s/\${PORT}/$PORT/g" /etc/nginx/nginx.conf

echo "Verifying nginx configuration after PORT substitution..."
nginx -t || echo "Warning: nginx configuration test failed"

echo "Checking frontend files..."
ls -la /usr/share/nginx/html/ | head -10 || echo "Warning: Could not list frontend files"
test -f /usr/share/nginx/html/index.html && echo "index.html found" || echo "ERROR: index.html not found!"

# Запускаем бэкенд в фоне на внутреннем порту 8000 (не конфликтует с PORT от Render)
BACKEND_PORT=8000
echo "Starting FastAPI backend on internal port $BACKEND_PORT..."
echo "Checking DATABASE_URL..."
if [ -z "$DATABASE_URL" ]; then
    echo "WARNING: DATABASE_URL is not set!"
else
    echo "DATABASE_URL is set (length: ${#DATABASE_URL})"
fi

# Используем Python из виртуального окружения
if [ -f "/.venv/bin/python" ]; then
    PYTHON_BIN="/.venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
else
    echo "ERROR: Could not find Python in virtual environment"
    exit 1
fi

echo "Starting uvicorn with $PYTHON_BIN"
$PYTHON_BIN -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

echo "Backend process started with PID: $BACKEND_PID"
sleep 3

# Простая проверка, что бэкенд запустился
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "ERROR: Backend process died!"
    cat /tmp/backend.log
    exit 1
fi

# Ждем, пока бэкенд станет доступен
for i in {1..10}; do
    if curl -f http://localhost:$BACKEND_PORT/ping > /dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    sleep 1
done

# Запускаем Nginx в foreground на порту из переменной PORT
echo "Starting Nginx on port $PORT..."
exec nginx -g "daemon off;"
