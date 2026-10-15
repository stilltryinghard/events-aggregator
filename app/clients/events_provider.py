import uuid
from dataclasses import dataclass
from datetime import date
from urllib.parse import parse_qs, urlparse

import httpx


def _extract_cursor(next_url: str | None) -> str | None:
    """Достаёт курсор из ссылки `next`, которую присылает провайдер.

    Хост в этой ссылке может не совпадать с настроенным адресом,
    поэтому берём только курсор, а запрос собираем сами.
    """
    if next_url is None:
        return None
    query = parse_qs(urlparse(next_url).query)
    return query["cursor"][0]


@dataclass
class EventsPage:
    results: list[dict]
    next_cursor: str | None


class EventsProviderClient:
    """HTTP-клиент для Events Provider API.

    Единственное место в сервисе, которое общается с провайдером.
    Ожидает httpx.AsyncClient, заранее настроенный на адрес провайдера
    и заголовок x-api-key.
    """

    def __init__(self, http: httpx.AsyncClient):
        self.http = http

    async def events(self, changed_at: date, cursor: str | None = None) -> EventsPage:
        params = {"changed_at": changed_at.isoformat()}
        if cursor:
            params["cursor"] = cursor
        response = await self.http.get("/api/events/", params=params)
        response.raise_for_status()
        data = response.json()
        return EventsPage(
            results=data["results"], next_cursor=_extract_cursor(data["next"])
        )

    async def seats(self, event_id: uuid.UUID) -> list[str]:
        response = await self.http.get(f"/api/events/{event_id}/seats/")
        response.raise_for_status()
        data = response.json()
        return data["seats"]

    async def register(
        self,
        event_id: uuid.UUID,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> uuid.UUID:
        response = await self.http.post(
            f"/api/events/{event_id}/register/",
            json={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "seat": seat,
            },
        )
        response.raise_for_status()
        return uuid.UUID(response.json()["ticket_id"])

    async def unregister(self, event_id: uuid.UUID, ticket_id: uuid.UUID) -> None:
        response = await self.http.request(
            "DELETE",
            f"/api/events/{event_id}/unregister/",
            json={"ticket_id": str(ticket_id)},
        )
        response.raise_for_status()
