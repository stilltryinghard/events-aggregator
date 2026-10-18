from datetime import date
from unittest.mock import AsyncMock, MagicMock, call

from app.clients.events_provider import EventsPage
from app.clients.paginator import EventsPaginator
from app.entities import Event

CHANGED_AT = date(2026, 1, 1)
e1, e2, e3, e4 = (MagicMock(spec=Event) for _ in range(4))


async def collect(paginator: EventsPaginator) -> list:
    return [event async for event in paginator]


async def test_paginator_walks_all_pages_in_order():
    client = AsyncMock()
    client.events.side_effect = [
        EventsPage(results=[e1, e2], next_cursor="abc"),
        EventsPage(results=[e3], next_cursor="def"),
        EventsPage(results=[e4], next_cursor=None),
    ]

    events = await collect(EventsPaginator(client, CHANGED_AT))

    assert events == [e1, e2, e3, e4]
    assert client.events.await_args_list == [
        call(CHANGED_AT, None),
        call(CHANGED_AT, "abc"),
        call(CHANGED_AT, "def"),
    ]


async def test_paginator_single_page():
    client = AsyncMock()
    client.events.side_effect = [EventsPage(results=[e1], next_cursor=None)]

    events = await collect(EventsPaginator(client, CHANGED_AT))

    assert events == [e1]
    client.events.assert_awaited_once_with(CHANGED_AT, None)


async def test_paginator_empty_result():
    client = AsyncMock()
    client.events.side_effect = [EventsPage(results=[], next_cursor=None)]

    events = await collect(EventsPaginator(client, CHANGED_AT))

    assert events == []
