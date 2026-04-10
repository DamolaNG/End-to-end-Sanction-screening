POETRY ?= poetry
VENV_BIN := $(if $(wildcard .venv/bin/python),.venv/bin,)
PYTHON ?= $(if $(VENV_BIN),$(VENV_BIN)/python,$(POETRY) run python)
ALEMBIC ?= $(if $(VENV_BIN),$(VENV_BIN)/alembic,$(POETRY) run alembic)
DBT = $(if $(VENV_BIN),$(VENV_BIN)/dbt,$(POETRY) run dbt) --project-dir dbt --profiles-dir dbt
PYTEST ?= $(if $(VENV_BIN),$(VENV_BIN)/pytest,$(POETRY) run pytest)
RUFF ?= $(if $(VENV_BIN),$(VENV_BIN)/ruff,$(POETRY) run ruff)
UVICORN ?= $(if $(VENV_BIN),$(VENV_BIN)/uvicorn,$(POETRY) run uvicorn)
STREAMLIT ?= $(if $(VENV_BIN),$(VENV_BIN)/streamlit,$(POETRY) run streamlit)

.PHONY: install up down migrate pipeline api dashboard test lint format dbt-run dbt-test compile check

install:
	$(POETRY) install

up:
	docker compose up -d postgres

down:
	docker compose down

migrate:
	$(ALEMBIC) upgrade head

pipeline:
	$(PYTHON) -m scripts.run_pipeline

api:
	$(UVICORN) api.main:app --host 0.0.0.0 --port 8000 --reload

dashboard:
	$(STREAMLIT) run dashboards/streamlit_app/main.py --server.port 8501

dbt-run:
	$(DBT) run

dbt-test:
	$(DBT) test

test:
	$(PYTEST) -q

lint:
	$(RUFF) check .

compile:
	$(PYTHON) -m compileall app api dashboards orchestration scripts tests

check:
	$(RUFF) check .
	$(PYTHON) -m compileall app api dashboards orchestration scripts tests
	$(PYTEST) -q
