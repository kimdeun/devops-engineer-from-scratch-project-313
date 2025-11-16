FROM python:3.11-slim
WORKDIR /
RUN apt-get update && \
    apt-get install -y make curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    # Пробуем установить uv и смотрим что происходит
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"
RUN uv --version

COPY . .
RUn make install
RUN make build
RUN make ping-pong
ENV SENTRY_DSN=https://a8c75166e50c7c0f2f844e7e7c4d53ac@o4510374943195136.ingest.de.sentry.io/4510374946078800