install:
	uv sync
build:
	uv build
run:
	uv run fastapi dev ping_pong/main.py --host 0.0.0.0 --port 8080
tests:
	uv run pytest
lint:
	uv run ruff format .
run_prod:
	uv run uvicorn ping_pong.main:app --host 0.0.0.0 --port 8080
