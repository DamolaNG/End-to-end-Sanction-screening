POETRY ?= poetry
PYTHON ?= $(POETRY) run python
DBT = $(POETRY) run dbt --project-dir dbt --profiles-dir dbt

.PHONY: install up down migrate pipeline api dashboard test lint format dbt-run dbt-test compile check

install:
	$(POETRY) install

up:
	docker compose up -d postgres

down:
	docker compose down

migrate:
	$(POETRY) run alembic upgrade head

pipeline:
	$(PYTHON) -m scripts.run_pipeline

api:
	$(POETRY) run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

dashboard:
	$(POETRY) run streamlit run dashboards/streamlit_app/main.py --server.port 8501

dbt-run:
	$(DBT) run

dbt-test:
	$(DBT) test

test:
	$(POETRY) run pytest -q

lint:
	$(POETRY) run ruff check .

compile:
	$(PYTHON) -m compileall app api dashboards orchestration scripts tests

check:
	$(POETRY) run ruff check .
	$(PYTHON) -m compileall app api dashboards orchestration scripts tests
	$(POETRY) run pytest -q
