from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения. Значения берутся из переменных окружения (или файла .env)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Строка подключения: postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DATABASE
    database_url: str


settings = Settings()
