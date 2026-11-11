from collections.abc import AsyncIterator, Iterator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.community.postgres import PostgresContainer

from app import models


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    # Запускаем временную PostgreSQL
    with PostgresContainer(
        "postgres:16",
        driver="asyncpg",
    ) as postgres:
        yield postgres.get_connection_url()


@pytest.fixture
async def db_session_maker(
    postgres_url: str,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    # Создаём подключение к тестовой PostgreSQL
    engine = create_async_engine(postgres_url)

    # Создаём таблицы перед тестом
    async with engine.begin() as connection:
        await connection.run_sync(models.Base.metadata.create_all)

    try:
        # Передаём тесту фабрику сессий
        yield async_sessionmaker(
            engine,
            expire_on_commit=False,
        )

    finally:
        # Удаляем тестовые таблицы
        async with engine.begin() as connection:
            await connection.run_sync(models.Base.metadata.drop_all)

        # Закрываем подключения
        await engine.dispose()
