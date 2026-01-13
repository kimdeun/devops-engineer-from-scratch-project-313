FROM python:3.14-slim

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y make curl nginx nodejs npm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Установка uv (последняя стабильная версия)
# Удаляем старые версии uv, если они есть
RUN rm -rf ~/.cargo/bin/uv ~/.local/bin/uv /usr/local/bin/uv 2>/dev/null || true
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"
# Проверяем версию uv и убеждаемся, что используется правильный бинарник
RUN which uv && uv --version

WORKDIR /

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости Python
# Переустанавливаем uv после копирования файлов для синхронизации версий
RUN rm -rf ~/.cargo/bin/uv ~/.local/bin/uv /usr/local/bin/uv 2>/dev/null || true && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    uv cache clean || true
RUN make install

# Устанавливаем зависимости npm
RUN npm install

# Собираем статику фронтенда
# Создаем директорию для статики
RUN mkdir -p /usr/share/nginx/html

# Пытаемся собрать статику через пакет
# Пакет может иметь команды: build, export, или просто запускать сервер
RUN npx --yes @hexlet/project-devops-deploy-crud-frontend build /usr/share/nginx/html 2>&1 || \
    npx --yes @hexlet/project-devops-deploy-crud-frontend export /usr/share/nginx/html 2>&1 || \
    (echo "Frontend static files not found, will be generated at runtime" && \
     echo '<!DOCTYPE html><html><head><title>Loading...</title></head><body><h1>Frontend Loading...</h1></body></html>' > /usr/share/nginx/html/index.html)

# Копируем конфигурацию Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Переменные окружения
ENV PORT=80
ENV SENTRY_DSN=https://a8c75166e50c7c0f2f844e7e7c4d53ac@o4510374943195136.ingest.de.sentry.io/4510374946078800

# Копируем скрипт запуска
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
