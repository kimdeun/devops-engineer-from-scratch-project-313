FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y make curl nginx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN rm -rf ~/.cargo/bin/uv ~/.local/bin/uv /usr/local/bin/uv /usr/bin/uv /bin/uv 2>/dev/null || true
RUN curl -LsSf https://astral.sh/uv/install.sh | UV_VERSION=0.9.24 sh
ENV PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

WORKDIR /

COPY . .

# Устанавливаем зависимости Python
RUN which uv && uv --version
RUN uv cache clean || true
RUN uv sync 2>&1 || (echo "Lock file may be incompatible, updating..." && uv lock && uv sync)

# Проверяем, что виртуальное окружение создано
RUN ls -la .venv/bin/python 2>/dev/null || echo "Note: .venv will be created at runtime"

# Копируем статику фронтенда в директорию для nginx
# Предполагается, что фронтенд собран локально и находится в frontend-dist/
RUN mkdir -p /usr/share/nginx/html && \
    if [ -d "./frontend-dist" ]; then \
        cp -r ./frontend-dist/. /usr/share/nginx/html/ && \
        chown -R www-data:www-data /usr/share/nginx/html && \
        chmod -R 755 /usr/share/nginx/html; \
    else \
        echo "ERROR: frontend-dist directory not found! Please build frontend locally." && \
        exit 1; \
    fi

COPY config/nginx.conf /etc/nginx/nginx.conf

# Переменные окружения
# PORT=80 для Render (Render будет передавать свой PORT, но по умолчанию используем 80)
ENV PORT=80

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
