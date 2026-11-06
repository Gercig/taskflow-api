from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Настройки приложения. Значения берутся из переменных окружения (или файла .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Строка подключения: postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DATABASE
    database_url: str

    # Уровень логирования: DEBUG, INFO, WARNING, ERROR, CRITICAL (переменная LOG_LEVEL)
    log_level: LogLevel = "INFO"

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        """Разрешаем писать уровень в любом регистре: debug, Info, WARNING..."""
        return value.upper() if isinstance(value, str) else value


settings = Settings()
