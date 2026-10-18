import asyncio
import logging

import httpx

from app.clients.events_provider import EventsProviderClient
from app.db import async_session_maker
from app.repositories.events import EventRepository
from app.repositories.sync_runs import SyncRunRepository
from app.usecases.sync_events import SyncEventsUsecase

logger = logging.getLogger(__name__)

SYNC_INTERVAL_SECONDS = 24 * 60 * 60


async def sync_loop(http: httpx.AsyncClient) -> None:
    """Запускает синхронизацию сразу после старта и затем раз в сутки."""
    while True:
        try:
            async with async_session_maker() as session:
                usecase = SyncEventsUsecase(
                    client=EventsProviderClient(http),
                    events=EventRepository(session),
                    sync_runs=SyncRunRepository(session),
                    transaction=session,
                )
                await usecase.do()
        except Exception:
            logger.exception("Фоновая синхронизация упала")
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)
