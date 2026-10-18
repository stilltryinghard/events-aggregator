import uuid
from datetime import date
from unittest.mock import AsyncMock

import httpx
import pytest

from app.clients.events_provider import EventsProviderClient, SeatUnavailable

EVENT_ID = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
TICKET_ID = uuid.UUID("1fed0122-b675-42e2-8ae7-49bfb53e8d7f")

EVENT_DATA = {
    "id": str(EVENT_ID),
    "name": "Конференция по Python",
    "place": {
        "id": "650e8400-e29b-41d4-a716-446655440001",
        "name": "Конференц-зал Технопарк",
        "city": "Москва",
        "address": "ул. Ленина, д. 1",
        "seats_pattern": "A1-1000,B1-2000",
        "changed_at": "2025-01-01T03:00:00+03:00",
        "created_at": "2025-01-01T03:00:00+03:00",
    },
    "event_time": "2026-01-11T17:00:00+03:00",
    "registration_deadline": "2026-01-10T17:00:00+03:00",
    "status": "published",
    "number_of_visitors": 5,
    "changed_at": "2026-01-04T22:28:35.325270+03:00",
    "created_at": "2026-01-04T22:28:35.325302+03:00",
    "status_changed_at": "2026-01-04T22:28:35.325386+03:00",
}


def make_response(status_code: int, json_data, method: str = "GET") -> httpx.Response:
    """Ответ httpx без сети: raise_for_status требует, чтобы был запрос."""
    return httpx.Response(
        status_code,
        json=json_data,
        request=httpx.Request(method, "http://provider.test"),
    )


async def test_events_first_page_parses_events_and_cursor():
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get.return_value = make_response(
        200,
        {
            "next": "http://other-host/api/events/?changed_at=2026-01-01&cursor=abc",
            "previous": None,
            "results": [EVENT_DATA],
        },
    )
    client = EventsProviderClient(http)

    page = await client.events(date(2026, 1, 1))

    http.get.assert_awaited_once_with(
        "/api/events/", params={"changed_at": "2026-01-01"}
    )
    assert page.next_cursor == "abc"
    assert len(page.results) == 1
    event = page.results[0]
    assert event.id == EVENT_ID
    assert event.place.city == "Москва"
    assert event.event_time.year == 2026


async def test_events_passes_cursor_and_last_page_has_no_cursor():
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get.return_value = make_response(
        200, {"next": None, "previous": "http://x", "results": []}
    )
    client = EventsProviderClient(http)

    page = await client.events(date(2026, 1, 1), cursor="abc")

    http.get.assert_awaited_once_with(
        "/api/events/", params={"changed_at": "2026-01-01", "cursor": "abc"}
    )
    assert page.next_cursor is None
    assert page.results == []


async def test_events_raises_on_provider_error():
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get.return_value = make_response(500, {"detail": "boom"})
    client = EventsProviderClient(http)

    with pytest.raises(httpx.HTTPStatusError):
        await client.events(date(2026, 1, 1))


async def test_seats_returns_list():
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get.return_value = make_response(200, {"seats": ["A1", "A3"]})
    client = EventsProviderClient(http)

    seats = await client.seats(EVENT_ID)

    http.get.assert_awaited_once_with(f"/api/events/{EVENT_ID}/seats/")
    assert seats == ["A1", "A3"]


async def test_register_returns_ticket_id():
    http = AsyncMock(spec=httpx.AsyncClient)
    http.post.return_value = make_response(
        201, {"ticket_id": str(TICKET_ID)}, method="POST"
    )
    client = EventsProviderClient(http)

    ticket_id = await client.register(
        EVENT_ID, "Иван", "Иванов", "ivan@example.com", "A15"
    )

    http.post.assert_awaited_once_with(
        f"/api/events/{EVENT_ID}/register/",
        json={
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": "ivan@example.com",
            "seat": "A15",
        },
    )
    assert ticket_id == TICKET_ID


async def test_register_taken_seat_raises_seat_unavailable():
    http = AsyncMock(spec=httpx.AsyncClient)
    http.post.return_value = make_response(
        400, ["This ticket is not available (already sold)."], method="POST"
    )
    client = EventsProviderClient(http)

    with pytest.raises(SeatUnavailable):
        await client.register(EVENT_ID, "Иван", "Иванов", "ivan@example.com", "A15")


async def test_unregister_sends_ticket_id_in_body():
    http = AsyncMock(spec=httpx.AsyncClient)
    http.request.return_value = make_response(200, {"success": True}, method="DELETE")
    client = EventsProviderClient(http)

    await client.unregister(EVENT_ID, TICKET_ID)

    http.request.assert_awaited_once_with(
        "DELETE",
        f"/api/events/{EVENT_ID}/unregister/",
        json={"ticket_id": str(TICKET_ID)},
    )
