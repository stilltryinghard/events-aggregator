import uuid
from datetime import UTC, datetime

from app.usecases.errors import (
    EventAlreadyPassed,
    EventNotFound,
    EventNotPublished,
    RegistrationClosed,
    SeatNotFound,
    TicketNotFound,
)
from app.usecases.protocols import EventReader, TicketClient, TicketStore, Transaction
from app.usecases.seats_pattern import seat_exists


class CreateTicketUsecase:
    """Регистрация на событие: проверки у себя, регистрация у провайдера, билет в базу."""

    def __init__(
        self,
        events: EventReader,
        tickets: TicketStore,
        client: TicketClient,
        transaction: Transaction,
    ):
        self.events = events
        self.tickets = tickets
        self.client = client
        self.transaction = transaction

    async def do(
        self,
        event_id: uuid.UUID,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> uuid.UUID:
        event = await self.events.get(event_id)
        if event is None:
            raise EventNotFound
        if event.status != "published":
            raise EventNotPublished
        if datetime.now(UTC) >= event.registration_deadline:
            raise RegistrationClosed
        if not seat_exists(seat, event.place.seats_pattern):
            raise SeatNotFound

        ticket_id = await self.client.register(
            event_id, first_name, last_name, email, seat
        )
        await self.tickets.create(
            ticket_id, event_id, first_name, last_name, email, seat
        )
        await self.transaction.commit()
        return ticket_id


class CancelTicketUsecase:
    """Отмена регистрации: у провайдера и у себя."""

    def __init__(
        self,
        events: EventReader,
        tickets: TicketStore,
        client: TicketClient,
        transaction: Transaction,
    ):
        self.events = events
        self.tickets = tickets
        self.client = client
        self.transaction = transaction

    async def do(self, ticket_id: uuid.UUID) -> None:
        ticket = await self.tickets.get_active(ticket_id)
        if ticket is None:
            raise TicketNotFound
        event = await self.events.get(ticket.event_id)
        if event is None:
            raise EventNotFound
        if datetime.now(UTC) >= event.event_time:
            raise EventAlreadyPassed

        await self.client.unregister(ticket.event_id, ticket_id)
        await self.tickets.cancel(ticket_id)
        await self.transaction.commit()
