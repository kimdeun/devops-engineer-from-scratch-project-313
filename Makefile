install:
	uv sync
	npm install
build:
	uv build
run:
	npm start
run_backend:
	uv run fastapi dev ping_pong/main.py --host 0.0.0.0 --port 8080
run_frontend:
	npx start-hexlet-devops-deploy-crud-frontend
tests:
	uv run pytest
lint:
	uv run ruff format .
run_prod:
	uv run uvicorn ping_pong.main:app --host 0.0.0.0 --port 8080
