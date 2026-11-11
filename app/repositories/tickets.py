import uuid

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities import Ticket
from app.models import Ticket as TicketModel


class TicketRepository:
    """Работа с таблицей tickets."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        ticket_id: uuid.UUID,
        event_id: uuid.UUID,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
        idempotency_key: str | None = None,
        request_hash: str | None = None,
    ) -> None:
        # Создаём запись о билете
        ticket = TicketModel(
            ticket_id=ticket_id,
            event_id=event_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )

        # Добавляем объект в сессию SQLAlchemy
        self.session.add(ticket)

        # Отправляем INSERT в PostgreSQL
        await self.session.flush()

    async def get_active(self, ticket_id: uuid.UUID) -> Ticket | None:
        """Активный, то есть не отменённый, билет по ticket_id."""
        stmt = select(TicketModel).where(
            TicketModel.ticket_id == ticket_id,
            TicketModel.cancelled_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return Ticket(
            ticket_id=model.ticket_id, event_id=model.event_id, seat=model.seat
        )

    async def cancel(self, ticket_id: uuid.UUID) -> None:
        """Помечает активный билет отменённым, строка остаётся для истории."""
        stmt = (
            update(TicketModel)
            .where(
                TicketModel.ticket_id == ticket_id,
                TicketModel.cancelled_at.is_(None),
            )
            .values(cancelled_at=func.now())
        )
        await self.session.execute(stmt)

    async def get_by_idempotency_key(
        self,
        key: str,
    ) -> tuple[uuid.UUID, str | None] | None:
        # Ищем билет по ключу запроса
        stmt = select(
            TicketModel.ticket_id,
            TicketModel.request_hash,
        ).where(TicketModel.idempotency_key == key)

        result = await self.session.execute(stmt)
        row = result.one_or_none()

        # Если такого ключа нет - вовращаем None
        if row is None:
            return None

        return row.ticket_id, row.request_hash

    async def lock_idempotency_key(self, key: str) -> None:
        # Блокируем выполнение запросов с одинаковым ключом
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": key},
        )
