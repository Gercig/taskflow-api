# TaskFlow API

REST API для управления задачами команды.
Стек: Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16, Docker Compose.

## Запуск

Нужен только Docker (Docker Desktop на Windows/macOS). Python и PostgreSQL ставить не нужно.

```bash
git clone https://github.com/Gercig/taskflow-api.git
cd taskflow-api

# необязательно: свои логин/пароль БД (без .env используются значения по умолчанию taskflow/taskflow)
cp .env.example .env

docker compose up --build
```

При старте контейнер `api` ждёт готовности PostgreSQL, применяет миграции (`alembic upgrade head`) и запускает API.

- API: http://localhost:8000
- Документация Swagger: http://localhost:8000/docs
- Проверка: http://localhost:8000/health

Остановка с сохранением данных — `docker compose down`.
Полный сброс базы (удаляет volume с данными) — `docker compose down -v`.

## Ресурсы

Для `users`, `projects`, `labels`, `tasks`, `comments`:

| Метод | URL | Ответ |
|---|---|---|
| GET | `/v1/{resource}` | 200, список |
| GET | `/v1/{resource}/{id}` | 200 или 404 |
| POST | `/v1/{resource}` | 201, созданная запись |
| PATCH | `/v1/{resource}/{id}` | 200, меняются только переданные поля |
| DELETE | `/v1/{resource}/{id}` | 204 без тела |

Фильтры: `GET /v1/tasks?project_id=1&status=open`, `GET /v1/comments?task_id=1`.

Ошибки: `404` — записи нет, `422` — неверные входные данные (в том числе лишние поля вроде `id`),
`409` — дубликат уникального значения или ссылка на несуществующую запись, а также попытка удалить пользователя с комментариями.

## Примеры запросов

```bash
# проверка соединения с БД
curl http://localhost:8000/health

# создать пользователя
curl -X POST http://localhost:8000/v1/users \
  -H "Content-Type: application/json" \
  -d '{"email": "ivan@example.com", "display_name": "Иван"}'

# создать проект
curl -X POST http://localhost:8000/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "TaskFlow", "description": "Учебный проект"}'

# создать задачу в проекте 1 с исполнителем 1
curl -X POST http://localhost:8000/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"project_id": 1, "assignee_id": 1, "title": "Настроить Docker", "priority": "high"}'

# открытые задачи проекта 1
curl "http://localhost:8000/v1/tasks?project_id=1&status=open"

# перевести задачу 1 в done
curl -X PATCH http://localhost:8000/v1/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

> В Windows PowerShell вызывайте `curl.exe` вместо `curl`. Проще всего проверять запросы через http://localhost:8000/docs.

## Миграции

Схема БД создаётся только миграциями Alembic (`alembic/versions/0001_initial_schema.py`), `create_all()` не используется.
Проверка отката и повторного применения внутри контейнера:

```bash
docker compose exec api alembic downgrade base
docker compose exec api alembic upgrade head
docker compose exec api alembic current
```

## Структура

```text
app/
  main.py        — приложение, подключение роутеров, /health
  config.py      — настройки из переменных окружения (DATABASE_URL)
  database.py    — engine, сессии, Base
  models.py      — ORM-модели пяти таблиц
  schemas.py     — Pydantic-схемы запросов и ответов
  crud.py        — общие функции: 404 и обработка конфликтов (409)
  routers/       — users, projects, labels, tasks, comments
alembic/         — настройки и миграции
Dockerfile, docker-compose.yml, .dockerignore, .env.example
```
