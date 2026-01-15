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

# Запускаем бэкенд в фоне на внутреннем порту 8080
echo "Starting FastAPI backend on port 8080..."
uv run uvicorn ping_pong.main:app --host 0.0.0.0 --port 8080 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!

# Ждем запуска бэкенда с проверками
echo "Waiting for backend to start..."
MAX_RETRIES=30
RETRY_COUNT=0
BACKEND_READY=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:8080/ping > /dev/null 2>&1; then
        echo "Backend is ready!"
        BACKEND_READY=true
        break
    fi

    # Проверяем, что процесс еще жив
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "ERROR: Backend process died!"
        echo "Backend logs:"
        cat /tmp/backend.log
        exit 1
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for backend... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 1
done

if [ "$BACKEND_READY" = false ]; then
    echo "ERROR: Backend failed to start after $MAX_RETRIES seconds"
    echo "Backend logs:"
    cat /tmp/backend.log
    exit 1
fi

# Запускаем Nginx в foreground на порту из переменной PORT
echo "Starting Nginx on port $PORT..."
exec nginx -g "daemon off;"
