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

# Запускаем бэкенд с подробным логированием
# Убеждаемся, что виртуальное окружение существует
if [ ! -f "/.venv/bin/python" ] && [ ! -f ".venv/bin/python" ]; then
    echo "Creating virtual environment..."
    uv venv .venv || uv venv
fi

# Используем Python из виртуального окружения
if [ -f "/.venv/bin/python" ]; then
    PYTHON_BIN="/.venv/bin/python"
    echo "Using Python from /.venv: $PYTHON_BIN"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
    echo "Using Python from .venv: $PYTHON_BIN"
else
    echo "ERROR: Could not find Python in virtual environment"
    exit 1
fi

# Убеждаемся, что зависимости установлены
echo "Syncing dependencies..."
uv sync --quiet || uv sync

echo "Starting uvicorn with $PYTHON_BIN"
$PYTHON_BIN -m uvicorn ping_pong.main:app --host 0.0.0.0 --port $BACKEND_PORT > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

echo "Backend process started with PID: $BACKEND_PID"
sleep 2

# Проверяем, что процесс еще жив
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "ERROR: Backend process died immediately!"
    echo "Backend logs:"
    cat /tmp/backend.log
    exit 1
fi

echo "Backend process is running, checking logs..."
tail -20 /tmp/backend.log || echo "No logs yet"

# Ждем запуска бэкенда с проверками
echo "Waiting for backend to start..."
MAX_RETRIES=30
RETRY_COUNT=0
BACKEND_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Проверяем, что процесс еще жив
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "ERROR: Backend process died!"
        echo "Backend logs:"
        cat /tmp/backend.log
        exit 1
    fi

    # Проверяем, отвечает ли бэкенд
    if curl -f http://localhost:$BACKEND_PORT/ping > /dev/null 2>&1; then
        echo "Backend is ready!"
        BACKEND_READY=true
        break
    fi

    # Показываем последние строки логов каждые 5 попыток
    if [ $((RETRY_COUNT % 5)) -eq 0 ]; then
        echo "Recent backend logs:"
        tail -10 /tmp/backend.log || echo "No new logs"
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for backend... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 1
done

if [ "$BACKEND_READY" = false ]; then
    echo "ERROR: Backend failed to start after $MAX_RETRIES seconds"
    echo "Backend process status:"
    ps aux | grep uvicorn || echo "No uvicorn process found"
    echo "Port $BACKEND_PORT status:"
    netstat -tlnp 2>/dev/null | grep $BACKEND_PORT || ss -tlnp 2>/dev/null | grep $BACKEND_PORT || echo "Port $BACKEND_PORT not listening"
    echo "Full backend logs:"
    cat /tmp/backend.log
    exit 1
fi

# Запускаем Nginx в foreground на порту из переменной PORT
echo "Starting Nginx on port $PORT..."
exec nginx -g "daemon off;"
