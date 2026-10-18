import uuid

from app.usecases.errors import EventNotFound, EventNotPublished
from app.usecases.protocols import EventReader, SeatsClient, SeatsStore


class GetSeatsUsecase:
    """Свободные места события: из кэша или у провайдера."""

    def __init__(self, events: EventReader, client: SeatsClient, cache: SeatsStore):
        self.events = events
        self.client = client
        self.cache = cache

    async def do(self, event_id: uuid.UUID) -> list[str]:
        cached = self.cache.get(event_id)
        if cached is not None:
            return cached

        event = await self.events.get(event_id)
        if event is None:
            raise EventNotFound
        if event.status != "published":
            raise EventNotPublished

        seats = await self.client.seats(event_id)
        self.cache.set(event_id, seats)
        return seats
