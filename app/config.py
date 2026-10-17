from pydantic_settings import BaseSettings
from sqlalchemy import URL


class Settings(BaseSettings):
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


settings = Settings()  # pyright: ignore[reportCallIssue]
