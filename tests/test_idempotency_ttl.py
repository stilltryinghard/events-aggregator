import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models import Event, Place, Ticket
from app.repositories.tickets import TicketRepository


@pytest.mark.parametrize(
    "age, expired",
    [
        (timedelta(days=2), True),
        (timedelta(hours=1), False),
    ],
)
@pytest.mark.asyncio
async def test_expired_key_is_released(
    db_session_maker,
    age,
    expired,
):
    now = datetime.now(UTC)
    event_id = uuid.uuid4()
    ticket_id = uuid.uuid4()

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
        await session.flush()

        session.add(
            Ticket(
                ticket_id=ticket_id,
                event_id=event_id,
                first_name="Ivan",
                last_name="Petrov",
                email="ivan@test.com",
                seat="A1",
                idempotency_key="old-key",
                request_hash="a" * 64,
                created_at=now - age,
            )
        )
        await session.commit()

    async with db_session_maker() as session:
        repo = TicketRepository(session)

        # TTL — 24 часа, билет создан 48 часов назад
        await repo.release_expired_idempotency_key(
            "old-key",
            ttl_seconds=86400,
        )
        await session.commit()

    async with db_session_maker() as session:
        ticket = await session.scalar(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )

        # Сам билет не удалён
        assert ticket is not None

        # Просроченный ключ и хеш очищены
        if expired:
            assert ticket.idempotency_key is None
            assert ticket.request_hash is None
        else:
            assert ticket.idempotency_key == "old-key"
            assert ticket.request_hash == "a" * 64
