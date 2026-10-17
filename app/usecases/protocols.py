import uuid
from datetime import date, datetime
from typing import Protocol

from app.clients.events_provider import EventsPage
from app.entities import Event


class EventsClient(Protocol):
    async def events(
        self, changed_at: date, cursor: str | None = None
    ) -> EventsPage: ...


class EventWriter(Protocol):
    async def upsert(self, event: Event) -> None: ...


class SyncRunStore(Protocol):
    async def start(self) -> uuid.UUID: ...

    async def last_changed_at(self) -> datetime | None: ...

    async def finish_success(
        self, run_id: uuid.UUID, last_changed_at: datetime | None
    ) -> None: ...

    async def finish_failed(self, run_id: uuid.UUID, error: str) -> None: ...


class Transaction(Protocol):
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
