"""Настройка логирования.

Уровень задаётся переменной окружения LOG_LEVEL (DEBUG, INFO, WARNING, ERROR, CRITICAL).
Сообщения ниже выбранного уровня не выводятся: при LOG_LEVEL=WARNING не будет DEBUG и INFO.

Где какой уровень используется в приложении:
- DEBUG    — подробности: начало каждого запроса, какие поля меняет PATCH;
- INFO     — штатные события: старт/остановка, успешные запросы, создание/удаление записей;
- WARNING  — ошибки клиента: 404, 409, 422;
- ERROR    — сбои сервера: БД недоступна в /health, необработанное исключение (500);
- CRITICAL — приложение не может работать: нет связи с БД при старте.
"""

import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(level: str) -> None:
    logging.basicConfig(level=level, format=LOG_FORMAT, stream=sys.stdout, force=True)
    # SQL-запросы SQLAlchemy показываем только в режиме DEBUG.
    sql_level = logging.INFO if level == "DEBUG" else logging.WARNING
    logging.getLogger("sqlalchemy.engine").setLevel(sql_level)
