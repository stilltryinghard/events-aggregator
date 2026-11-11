import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from app.repositories.tickets import TicketRepository


@pytest.mark.asyncio
async def test_idempotency_lock(postgres_url):
    # Подключаемся к временной тестовой базе
    engine = create_async_engine(postgres_url)
    session_maker = async_sessionmaker(engine)

    key = "purchase-lock-test"

    try:
        # Две независимые сессии PostgreSQL
        async with (
            session_maker() as first,
            session_maker() as second,
        ):
            repo = TicketRepository(first)

            # Первая транзакция получает блокировку
            await repo.lock_idempotency_key(key)

            # Вторая пытается получить ту же блокировку
            stmt = text("SELECT pg_try_advisory_xact_lock(hashtextextended(:key, 0))")

            result = await second.execute(stmt, {"key": key})

            # Блокировка занята первой транзакцией
            assert result.scalar_one() is False

            # Первая транзакция освобождает блокировку
            await first.commit()

            # Теперь вторая может получить блокировку
            result = await second.execute(stmt, {"key": key})

            assert result.scalar_one() is True

            await second.rollback()
    finally:
        # Закрываем подключения к тестовой базе
        await engine.dispose()
