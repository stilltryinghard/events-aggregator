import uuid
from datetime import UTC, datetime

from app.usecases.errors import (
    EventAlreadyPassed,
    EventNotFound,
    EventNotPublished,
    IdempotencyConflict,
    RegistrationClosed,
    SeatNotFound,
    TicketNotFound,
)
from app.usecases.idempotency import build_request_hash
from app.usecases.protocols import (
    EventReader,
    OutboxStore,
    TicketClient,
    TicketStore,
    Transaction,
)
from app.usecases.seats_pattern import seat_exists


class CreateTicketUsecase:
    """Регистрация на событие и создание билета."""

    def __init__(
        self,
        events: EventReader,
        tickets: TicketStore,
        client: TicketClient,
        transaction: Transaction,
        outbox: OutboxStore,
    ):
        self.events = events
        self.tickets = tickets
        self.client = client
        self.transaction = transaction
        self.outbox = outbox

    async def do(
        self,
        event_id: uuid.UUID,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
        idempotency_key: str | None = None,
    ) -> uuid.UUID:
        request_hash = None

        if idempotency_key is not None:
            # Вычисляем хеш данных покупки
            request_hash = build_request_hash(
                event_id,
                first_name,
                last_name,
                email,
                seat,
            )

            # Блокируем ключ до завершения транзакции
            await self.tickets.lock_idempotency_key(idempotency_key)

            # Проверяем, существует ли такая покупка
            existing = await self.tickets.get_by_idempotency_key(idempotency_key)

            if existing is not None:
                ticket_id, saved_hash = existing

                # Один ключ нельзя использовать с другими данными
                if saved_hash != request_hash:
                    raise IdempotencyConflict

                # Повторная покупка — возвращаем старый билет
                return ticket_id

        # Проверяем существование мероприятия
        event = await self.events.get(event_id)

        if event is None:
            raise EventNotFound

        if event.status != "published":
            raise EventNotPublished

        if datetime.now(UTC) >= event.registration_deadline:
            raise RegistrationClosed

        if not seat_exists(seat, event.place.seats_pattern):
            raise SeatNotFound

        # Регистрируем билет у внешнего провайдера
        ticket_id = await self.client.register(
            event_id,
            first_name,
            last_name,
            email,
            seat,
        )

        # Сохраняем билет и данные идемпотентности
        await self.tickets.create(
            ticket_id,
            event_id,
            first_name,
            last_name,
            email,
            seat,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )

        # Создаём событие для отправки уведомления
        await self.outbox.create(
            event_type="ticket_purchased",
            payload={
                "ticket_id": str(ticket_id),
                "event_id": str(event_id),
                "event_name": event.name,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "seat": seat,
            },
        )

        # Подтверждаем сохранение билета и Outbox
        await self.transaction.commit()

        return ticket_id


class CancelTicketUsecase:
    """Отмена регистрации на мероприятие."""

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

        await self.client.unregister(
            ticket.event_id,
            ticket_id,
        )

        await self.tickets.cancel(ticket_id)
        await self.transaction.commit()
