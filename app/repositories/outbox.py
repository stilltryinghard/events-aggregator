import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import OutboxEventType, OutboxStatus
from app.models import Outbox


class OutboxRepository:
    """Работа с таблицей outbox."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        event_type: OutboxEventType,
        payload: dict,
    ) -> None:
        event = Outbox(
            event_type=event_type,
            payload=payload,
            status=OutboxStatus.PENDING,
        )

        self.session.add(event)
        await self.session.flush()

    async def get_pending(
        self,
        limit: int | None = None,
    ) -> list[Outbox]:
        stmt = (
            select(Outbox)
            .where(Outbox.status == OutboxStatus.PENDING)
            .order_by(Outbox.created_at)
        )

        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_sent(self, event_id: uuid.UUID) -> None:
        stmt = (
            update(Outbox).where(Outbox.id == event_id).values(status=OutboxStatus.SENT)
        )

        await self.session.execute(stmt)
