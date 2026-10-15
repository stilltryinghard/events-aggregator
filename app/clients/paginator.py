from collections.abc import AsyncIterator
from datetime import date

from app.clients.events_provider import EventsProviderClient
from app.entities import Event


class EventsPaginator:
    """Обходит все страницы событий провайдера и отдаёт события по одному.

    Использование: async for event in EventsPaginator(client, changed_at).
    """

    def __init__(self, client: EventsProviderClient, changed_at: date):
        self.client = client
        self.changed_at = changed_at

    async def __aiter__(self) -> AsyncIterator[Event]:
        cursor = None
        while True:
            page = await self.client.events(self.changed_at, cursor)
            for event in page.results:
                yield event
            if page.next_cursor is None:
                return
            cursor = page.next_cursor
