FROM python:3.14-slim

# Установка системных зависимостей (nginx для проксирования и раздачи статики, nodejs/npm для фронтенда)
RUN apt-get update && \
    apt-get install -y make curl nginx nodejs npm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN rm -rf ~/.cargo/bin/uv ~/.local/bin/uv /usr/local/bin/uv /usr/bin/uv /bin/uv 2>/dev/null || true
RUN curl -LsSf https://astral.sh/uv/install.sh | UV_VERSION=0.9.24 sh
ENV PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

WORKDIR /

# Копируем файлы проекта
COPY . .

# Устанавливаем зависимости Python
RUN which uv && uv --version
RUN uv cache clean || true
RUN uv sync 2>&1 || (echo "Lock file may be incompatible, updating..." && uv lock && uv sync)

# Проверяем, что виртуальное окружение создано
RUN ls -la .venv/bin/python 2>/dev/null || echo "Note: .venv will be created at runtime"

# Устанавливаем зависимости npm для фронтенда
RUN npm install && \
    echo "npm install completed" && \
    echo "Checking installed packages..." && \
    ls -la ./node_modules/@hexlet/ 2>&1 || echo "No @hexlet packages found"

# Копируем статику фронтенда в директорию для nginx
RUN mkdir -p /usr/share/nginx/html && \
    echo "Checking for frontend package..." && \
    if [ -d "./node_modules/@hexlet/project-devops-deploy-crud-frontend/dist" ]; then \
        echo "Found dist directory, listing contents..." && \
        ls -la ./node_modules/@hexlet/project-devops-deploy-crud-frontend/dist/ && \
        echo "Copying files to /usr/share/nginx/html..." && \
        cp -r ./node_modules/@hexlet/project-devops-deploy-crud-frontend/dist/. /usr/share/nginx/html/ && \
        echo "Setting proper permissions..." && \
        chown -R www-data:www-data /usr/share/nginx/html && \
        chmod -R 755 /usr/share/nginx/html && \
        echo "Frontend static files copied successfully" && \
        echo "Verifying files in /usr/share/nginx/html:" && \
        ls -la /usr/share/nginx/html/ && \
        echo "Checking for index.html:" && \
        ls -la /usr/share/nginx/html/index.html || echo "WARNING: index.html not found!"; \
    else \
        echo "ERROR: Frontend dist directory not found!" && \
        echo "Contents of node_modules/@hexlet/project-devops-deploy-crud-frontend:" && \
        ls -la ./node_modules/@hexlet/project-devops-deploy-crud-frontend/ 2>&1 || echo "Package directory does not exist" && \
        exit 1; \
    fi

# Копируем конфигурацию Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Переменные окружения
# PORT=80 для Render (Render будет передавать свой PORT, но по умолчанию используем 80)
ENV PORT=80

# Копируем скрипт запуска
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
