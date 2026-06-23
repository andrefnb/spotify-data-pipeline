.PHONY: install test lint format typecheck run docker-build docker-run clean

install:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

typecheck:
	mypy src/

run:
	python -m spotify_pipeline.orchestration.pipeline

docker-build:
	docker compose build

docker-run:
	docker compose run --rm pipeline

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -f data/warehouse.duckdb
