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
            async with async_session_maker() as session:
                repo = OutboxRepository(session)

                # Получаем события, ожидающие отправки
                events = await repo.get_pending()
                events = events[: settings.outbox_batch_size]

                for event in events:
                    try:
                        if event.event_type != "ticket_purchased":
                            logger.warning(
                                "Неизвестный тип события: %s",
                                event.event_type,
                            )
                            continue

                        payload = event.payload

                        # Формируем текст уведомления
                        message = (
                            f"{payload['first_name']}, "
                            f"вы зарегистрированы на "
                            f"{payload['event_name']}. "
                            f"Ваше место: {payload['seat']}."
                        )

                        # Отправляем уведомление
                        await client.send_notification(
                            message=message,
                            ticket_id=payload["ticket_id"],
                            idempotency_key=str(event.id),
                        )

                        # Отмечаем успешную отправку
                        await repo.mark_sent(event.id)
                        await session.commit()

                    except Exception:
                        await session.rollback()
                        logger.exception(
                            "Ошибка отправки Outbox %s",
                            event.id,
                        )

        except Exception:
            logger.exception("Ошибка воркера Outbox")

        # Ждём перед следующей проверкой
        await asyncio.sleep(settings.outbox_interval_seconds)
