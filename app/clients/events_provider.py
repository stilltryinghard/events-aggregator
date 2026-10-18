"""Клиент к Events Provider API.

Единственный модуль в сервисе, который знает, как устроен API провайдера:
какие у него адреса, в каком виде он присылает данные и как листать страницы.
Наружу отдаёт только сущности из app.entities, JSON провайдера дальше
этого модуля не уходит.
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from urllib.parse import parse_qs, urlparse

import httpx

from app.entities import Event, Place


class SeatUnavailable(Exception):
    """Провайдер отказал в регистрации: место уже занято."""


def _extract_cursor(next_url: str | None) -> str | None:
    """Достаёт курсор из ссылки `next`, которую присылает провайдер.

    Хост в этой ссылке может не совпадать с настроенным адресом,
    поэтому берём только курсор, а запрос собираем сами.
    """
    if next_url is None:
        return None
    query = parse_qs(urlparse(next_url).query)
    return query["cursor"][0]


def _parse_place(data: dict) -> Place:
    """Превращает словарь площадки из ответа провайдера в сущность Place.

    Провайдер присылает айди и даты строками, здесь они становятся
    uuid.UUID и datetime.
    """
    return Place(
        id=uuid.UUID(data["id"]),
        name=data["name"],
        city=data["city"],
        address=data["address"],
        seats_pattern=data["seats_pattern"],
        changed_at=datetime.fromisoformat(data["changed_at"]),
        created_at=datetime.fromisoformat(data["created_at"]),
    )


def _parse_event(data: dict) -> Event:
    """Превращает словарь события из ответа провайдера в сущность Event.

    Площадка приходит внутри события целым словарём под ключом "place",
    её разбирает _parse_place.
    """
    return Event(
        id=uuid.UUID(data["id"]),
        event_time=datetime.fromisoformat(data["event_time"]),
        name=data["name"],
        place=_parse_place(data["place"]),
        status=data["status"],
        number_of_visitors=data["number_of_visitors"],
        registration_deadline=datetime.fromisoformat(data["registration_deadline"]),
        status_changed_at=datetime.fromisoformat(data["status_changed_at"]),
        changed_at=datetime.fromisoformat(data["changed_at"]),
        created_at=datetime.fromisoformat(data["created_at"]),
    )


@dataclass
class EventsPage:
    """Одна страница списка событий.

    results: события этой страницы, уже разобранные в сущности.
    next_cursor: закладка для запроса следующей страницы,
        None, если эта страница последняя.
    """

    results: list[Event]
    next_cursor: str | None


class EventsProviderClient:
    """HTTP-клиент для Events Provider API.

    Единственное место в сервисе, которое общается с провайдером.
    Ожидает httpx.AsyncClient, заранее настроенный на адрес провайдера
    и заголовок x-api-key.

    Читающие запросы (events, seats) повторяются при сбоях через _get.
    Изменяющие (register, unregister) не повторяются.
    При ответе провайдера с ошибкой методы бросают httpx.HTTPStatusError.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        max_attempts: int = 3,
        retry_delay: float = 0.5,
    ):
        self.http = http
        self.max_attempts = max_attempts
        self.retry_delay = retry_delay

    async def _get(self, path: str, params: dict | None = None) -> httpx.Response:
        """GET с повторами при обрыве сети и ответах 5xx.

        Повторяем только чтение: оно ничего не меняет у провайдера.
        Регистрацию и отмену не повторяем, повтор мог бы выполнить действие дважды.
        Паузы между попытками растут: retry_delay, затем 2 * retry_delay.
        """
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = await self.http.get(path, params=params)
            except httpx.TransportError:
                if attempt == self.max_attempts:
                    raise
            else:
                if response.status_code < 500 or attempt == self.max_attempts:
                    response.raise_for_status()
                    return response
            await asyncio.sleep(self.retry_delay * attempt)
        raise AssertionError("unreachable")

    async def events(self, changed_at: date, cursor: str | None = None) -> EventsPage:
        """Запрашивает одну страницу событий, изменённых начиная с changed_at.

        Для первой страницы cursor не передаётся. Для каждой следующей
        передаётся next_cursor из предыдущей страницы. Обходить все страницы
        удобнее через EventsPaginator.

        Запрос: GET /api/events/?changed_at=2026-01-01&cursor=...
        """
        params = {"changed_at": changed_at.isoformat()}
        if cursor:
            params["cursor"] = cursor
        response = await self._get("/api/events/", params=params)
        data = response.json()
        return EventsPage(
            results=[_parse_event(item) for item in data["results"]],
            next_cursor=_extract_cursor(data["next"]),
        )

    async def seats(self, event_id: uuid.UUID) -> list[str]:
        """Возвращает свободные места события, например ["A1", "A3", "B15"].

        Работает только для опубликованных событий. Для остальных провайдер
        отвечает 500 с HTML-страницей вместо JSON, поэтому статус события
        стоит проверять до вызова.

        Запрос: GET /api/events/{event_id}/seats/
        """
        response = await self._get(f"/api/events/{event_id}/seats/")
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
        """Регистрирует участника на место и возвращает ticket_id от провайдера.

        Если место уже занято, провайдер отвечает 400, и метод бросает
        SeatUnavailable. ticket_id привязан к месту: после отмены регистрации
        следующий участник на то же место получит тот же ticket_id.
        Не повторяется при сбоях: регистрация неидемпотентна.

        Запрос: POST /api/events/{event_id}/register/
        """
        response = await self.http.post(
            f"/api/events/{event_id}/register/",
            json={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "seat": seat,
            },
        )
        if response.status_code == httpx.codes.BAD_REQUEST:
            raise SeatUnavailable(response.text)
        response.raise_for_status()
        return uuid.UUID(response.json()["ticket_id"])

    async def unregister(self, event_id: uuid.UUID, ticket_id: uuid.UUID) -> None:
        """Отменяет регистрацию по ticket_id.

        Провайдеру нужен и айди события, и айди билета.
        Не повторяется при сбоях, как и регистрация.

        Запрос: DELETE /api/events/{event_id}/unregister/ с ticket_id в теле.
        """
        # httpx.delete() не принимает тело, а провайдер ждёт ticket_id в JSON
        response = await self.http.request(
            "DELETE",
            f"/api/events/{event_id}/unregister/",
            json={"ticket_id": str(ticket_id)},
        )
        response.raise_for_status()
