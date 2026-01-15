FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y make curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN rm -rf ~/.cargo/bin/uv ~/.local/bin/uv /usr/local/bin/uv /usr/bin/uv /bin/uv 2>/dev/null || true
RUN curl -LsSf https://astral.sh/uv/install.sh | UV_VERSION=0.9.24 sh
ENV PATH="/root/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

WORKDIR /

COPY . .

RUN which uv && uv --version
RUN uv cache clean || true
RUN uv sync 2>&1 || (echo "Lock file may be incompatible, updating..." && uv lock && uv sync)

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
