install:
	uv synce
ping-pong:
	uv run fastapi dev --host 0.0.0.0 --port 8080
tests:
	uv run pytest
lint:
	uv run ruff format .
