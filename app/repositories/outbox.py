import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Outbox


class OutboxRepository:
    """Работа с таблицей outbox."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        event_type: str,
        payload: dict,
    ) -> None:
        # Создаём событие в текущей транзакции
        event = Outbox(
            event_type=event_type,
            payload=payload,
            status="pending",
        )

        self.session.add(event)
        await self.session.flush()

    async def get_pending(
        self,
        limit: int | None = None,
    ) -> list[Outbox]:
        # Выбираем неотправленные события
        stmt = (
            select(Outbox).where(Outbox.status == "pending").order_by(Outbox.created_at)
        )

        # Ограничиваем количество записей на уровне БД
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_sent(self, event_id: uuid.UUID) -> None:
        # Меняем статус после успешной отправки
        stmt = update(Outbox).where(Outbox.id == event_id).values(status="sent")

        await self.session.execute(stmt)
