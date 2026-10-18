import time
import uuid


class SeatsCache:
    """Кэш свободных мест в памяти процесса, каждая запись живёт ttl_seconds."""

    def __init__(self, ttl_seconds: float):
        self.ttl_seconds = ttl_seconds
        self._items: dict[uuid.UUID, tuple[float, list[str]]] = {}

    def get(self, event_id: uuid.UUID) -> list[str] | None:
        item = self._items.get(event_id)
        if item is None:
            return None
        expires_at, seats = item
        if time.monotonic() >= expires_at:
            del self._items[event_id]
            return None
        return seats

    def set(self, event_id: uuid.UUID, seats: list[str]) -> None:
        self._items[event_id] = (time.monotonic() + self.ttl_seconds, seats)
