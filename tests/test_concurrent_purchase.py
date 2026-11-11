import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select

from app.models import Event, Outbox, Place, Ticket
from app.repositories.events import EventRepository
from app.repositories.outbox import OutboxRepository
from app.repositories.tickets import TicketRepository
from app.usecases.tickets import CreateTicketUsecase


@pytest.mark.asyncio
async def test_concurrent_purchase(db_session_maker):
    event_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    now = datetime.now(UTC)

    # Подготавливаем мероприятие в тестовой БД
    async with db_session_maker() as session:
        place = Place(
            id=uuid.uuid4(),
            name="Test Hall",
            city="Moscow",
            address="Test Street",
            seats_pattern="A1-10",
            changed_at=now,
            created_at=now,
        )
        session.add(place)
        await session.flush()

        session.add(
            Event(
                id=event_id,
                name="Test Event",
                place_id=place.id,
                status="published",
                number_of_visitors=0,
                event_time=now + timedelta(days=7),
                registration_deadline=now + timedelta(days=2),
                status_changed_at=now,
                changed_at=now,
                created_at=now,
            )
        )
        await session.commit()

    # Имитируем внешнего провайдера
    provider = AsyncMock()

    async def fake_register(*args):
        await asyncio.sleep(0.1)
        return ticket_id

    provider.register.side_effect = fake_register

    # Каждый запрос получает собственную сессию
    async def buy():
        async with db_session_maker() as session:
            usecase = CreateTicketUsecase(
                events=EventRepository(session),
                tickets=TicketRepository(session),
                client=provider,
                transaction=session,
                outbox=OutboxRepository(session),
            )

            return await usecase.do(
                event_id,
                "Ivan",
                "Petrov",
                "ivan@test.com",
                "A1",
                idempotency_key="purchase-123",
            )

    # Запускаем две покупки одновременно
    first_id, second_id = await asyncio.gather(
        buy(),
        buy(),
    )

    # Оба запроса получили один билет
    assert first_id == second_id == ticket_id

    # Провайдер вызван только один раз
    provider.register.assert_awaited_once()

    # Проверяем данные в PostgreSQL
    async with db_session_maker() as session:
        tickets_count = await session.scalar(select(func.count()).select_from(Ticket))
        outbox_count = await session.scalar(select(func.count()).select_from(Outbox))

    assert tickets_count == 1
    assert outbox_count == 1
