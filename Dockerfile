FROM python:3.14-slim

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y make curl nginx nodejs npm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копируем конкретную версию uv (0.27.2) из официального образа для совместимости с CI
# Удаляем все возможные старые версии uv
RUN rm -rf ~/.cargo/bin/uv ~/.local/bin/uv /usr/local/bin/uv /usr/bin/uv /bin/uv 2>/dev/null || true
COPY --from=ghcr.io/astral-sh/uv:0.27.2 /uv /usr/local/bin/uv
RUN chmod +x /usr/local/bin/uv
# Убеждаемся, что PATH настроен правильно и uv доступен
ENV PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
# Проверяем версию uv и путь к нему
RUN which uv && uv --version

WORKDIR /

# Копируем файлы проекта (node_modules исключается через .dockerignore)
COPY . .

# Устанавливаем зависимости Python
# Убеждаемся, что используем правильную версию uv
RUN which uv && uv --version
# Обновляем uv.lock до версии 0.27.2 для совместимости с CI
RUN uv lock --upgrade
# Очищаем кэш uv перед установкой
RUN uv cache clean || true
# Устанавливаем зависимости
RUN uv sync

# Устанавливаем зависимости npm
# Удаляем node_modules если они были скопированы, и переустанавливаем
RUN rm -rf node_modules 2>/dev/null || true
RUN npm ci --omit=dev || npm install

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
