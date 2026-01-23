install:
	uv sync
	npm install
build:
	uv build
build-frontend:
	npm install && \
	mkdir -p frontend-dist && \
	cp -r node_modules/@hexlet/project-devops-deploy-crud-frontend/dist/. frontend-dist/
run:
	npm start
run_backend:
	uv run fastapi dev app/main.py --host 0.0.0.0 --port 8080
run_frontend:
	npx start-hexlet-devops-deploy-crud-frontend
tests:
	uv run pytest -v
lint:
	uv run ruff format .
run_prod:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
