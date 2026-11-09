import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app import outbox_worker


class StopLoop(Exception):
    pass


@pytest.mark.asyncio
@pytest.mark.parametrize("failed", [False, True])
async def test_outbox_notification(monkeypatch, failed):
    # Подготавливаем событие
    event = SimpleNamespace(
        id=uuid.uuid4(),
        event_type="ticket_purchased",
        payload={
            "ticket_id": str(uuid.uuid4()),
            "first_name": "Иван",
            "event_name": "Конференция",
            "seat": "A1",
        },
    )

    # Подменяем PostgreSQL
    session = AsyncMock()
    session.__aenter__.return_value = session

    repo = MagicMock()
    repo.get_pending = AsyncMock(return_value=[event])
    repo.mark_sent = AsyncMock()

    monkeypatch.setattr(
        outbox_worker,
        "async_session_maker",
        lambda: session,
    )
    monkeypatch.setattr(
        outbox_worker,
        "OutboxRepository",
        lambda session: repo,
    )

    # Подменяем Capashino
    send = AsyncMock()

    if failed:
        send.side_effect = RuntimeError("Capashino unavailable")

    monkeypatch.setattr(
        outbox_worker,
        "CapashinoClient",
        lambda http: SimpleNamespace(send_notification=send),
    )

    # Останавливаем бесконечный цикл после одной итерации
    monkeypatch.setattr(
        outbox_worker.asyncio,
        "sleep",
        AsyncMock(side_effect=StopLoop),
    )

    with pytest.raises(StopLoop):
        await outbox_worker.outbox_loop(MagicMock())

    send.assert_awaited_once()

    if failed:
        repo.mark_sent.assert_not_awaited()
        session.commit.assert_not_awaited()
    else:
        repo.mark_sent.assert_awaited_once_with(event.id)
        session.commit.assert_awaited_once()
