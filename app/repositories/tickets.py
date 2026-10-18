import uuid

from sqlalchemy import func, select, update
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
    ) -> None:
        self.session.add(
            TicketModel(
                ticket_id=ticket_id,
                event_id=event_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                seat=seat,
            )
        )
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
