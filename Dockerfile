FROM python:3.12-slim

ENV POETRY_VERSION=1.8.5 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${POETRY_HOME}/bin:${PATH}"

WORKDIR /workspace

COPY pyproject.toml README.md ./
RUN poetry install --no-interaction --no-ansi

COPY . .

CMD ["poetry", "run", "python", "-m", "scripts.run_pipeline"]

