from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        str_strip_whitespace=True,
    )

    postgres_host: str
    postgres_port: int
    postgres_username: str
    postgres_password: str
    postgres_database_name: str
    events_provider_url: str
    events_provider_api_key: str

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_username,
            host=self.postgres_host,
            port=self.postgres_port,
            password=self.postgres_password,
            database=self.postgres_database_name,
        )

    # Настройки сервиса уведомлений
    capashino_url: str = (
        "http://student-system-capashino-web.student-system-capashino.svc:8000"
    )
    capashino_api_key: str = ""

    # Настройки фонового воркера
    outbox_interval_seconds: int = 10
    outbox_batch_size: int = 50


settings = Settings()  # pyright: ignore[reportCallIssue]
