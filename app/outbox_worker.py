import asyncio
import logging

import httpx

from app.clients.capashino import CapashinoClient
from app.config import settings
from app.db import async_session_maker
from app.repositories.outbox import OutboxRepository

logger = logging.getLogger(__name__)


async def outbox_loop(http: httpx.AsyncClient) -> None:
    client = CapashinoClient(http)

    while True:
        try:
            # Получаем ожидающие события
            async with async_session_maker() as session:
                repo = OutboxRepository(session)
                events = await repo.get_pending(
                    limit=settings.outbox_batch_size,
                )

                # Копируем данные из ORM-объектов
                pending = [
                    (event.id, event.event_type, dict(event.payload))
                    for event in events
                ]

            # Обрабатываем события независимо
            for event_id, event_type, payload in pending:
                try:
                    if event_type != "ticket_purchased":
                        logger.warning(
                            "Неизвестное событие: %s",
                            event_type,
                        )
                        continue

                    message = (
                        f"{payload['first_name']}, "
                        f"вы зарегистрированы на "
                        f"{payload['event_name']}. "
                        f"Ваше место: {payload['seat']}."
                    )

                    await client.send_notification(
                        message=message,
                        ticket_id=payload["ticket_id"],
                        idempotency_key=str(event_id),
                    )

                    # Отмечаем успешную отправку
                    async with async_session_maker() as session:
                        repo = OutboxRepository(session)
                        await repo.mark_sent(event_id)
                        await session.commit()

                except Exception:
                    logger.exception(
                        "Ошибка отправки Outbox %s",
                        event_id,
                    )

        except Exception:
            logger.exception("Ошибка воркера Outbox")

        await asyncio.sleep(settings.outbox_interval_seconds)
