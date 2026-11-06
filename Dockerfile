FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Сначала только зависимости: этот слой кэшируется, пока requirements.txt не меняется.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

EXPOSE 8000

# 0.0.0.0 — чтобы API был доступен снаружи контейнера.
# В docker-compose.yml команда переопределена: сначала миграции, потом API.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
