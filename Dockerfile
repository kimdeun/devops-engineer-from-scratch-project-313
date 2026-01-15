FROM python:3.14-slim


RUN apt-get update && \
    apt-get install -y make curl nginx nodejs npm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


RUN rm -rf ~/.cargo/bin/uv ~/.local/bin/uv /usr/local/bin/uv /usr/bin/uv /bin/uv 2>/dev/null || true

ENV UV_VERSION=0.9.24
RUN curl -LsSf https://astral.sh/uv/install.sh | UV_VERSION=0.9.24 sh
ENV PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

RUN which uv && uv --version

WORKDIR /


COPY . .


RUN which uv && uv --version

RUN uv cache clean || true

RUN uv sync 2>&1 || (echo "Lock file may be incompatible, updating..." && uv lock && uv sync)


RUN rm -rf node_modules 2>/dev/null || true
RUN npm install


RUN mkdir -p /usr/share/nginx/html

RUN npx --yes @hexlet/project-devops-deploy-crud-frontend build /usr/share/nginx/html 2>&1 || \
    npx --yes @hexlet/project-devops-deploy-crud-frontend export /usr/share/nginx/html 2>&1 || \
    (echo "Frontend static files not found, will be generated at runtime" && \
     echo '<!DOCTYPE html><html><head><title>Loading...</title></head><body><h1>Frontend Loading...</h1></body></html>' > /usr/share/nginx/html/index.html)

COPY nginx.conf /etc/nginx/nginx.conf

ENV PORT=80
ENV SENTRY_DSN=https://a8c75166e50c7c0f2f844e7e7c4d53ac@o4510374943195136.ingest.de.sentry.io/4510374946078800
ENV DATABASE_URL=postgres://postgres:password@db:5432/appdb?sslmode=disable

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
