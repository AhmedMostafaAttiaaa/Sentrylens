.PHONY: install run test lint docker-up docker-down pull-models

install:
	uv pip install --system -e ".[dev]"

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

lint:
	ruff check app tests

docker-up:
	docker compose -f docker/docker-compose.yml up --build

docker-down:
	docker compose -f docker/docker-compose.yml down

pull-models:
	bash scripts/pull_ollama_models.sh
