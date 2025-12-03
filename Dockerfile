FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    && apt-get clean  \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN uv sync --frozen --no-cache

RUN uv run alembic upgrade head

CMD [ "/app/.venv/bin/python3", "main.py"]