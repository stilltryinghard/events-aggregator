import logging
from datetime import date

from app.clients.paginator import EventsPaginator
from app.usecases.protocols import EventsClient, EventWriter, SyncRunStore, Transaction

logger = logging.getLogger(__name__)


class SyncEventsUsecase:
    """Синхронизирует события провайдера с локальной базой"""

    def __init__(
        self,
        client: EventsClient,
        events: EventWriter,
        sync_runs: SyncRunStore,
        transaction: Transaction,
    ):
        self.client = client
        self.events = events
        self.sync_runs = sync_runs
        self.transaction = transaction

    async def do(self) -> None:
        run_id = await self.sync_runs.start()
        await self.transaction.commit()

        last_changed_at = await self.sync_runs.last_changed_at()
        if last_changed_at is None:
            changed_at = date(2000, 1, 1)
        else:
            changed_at = last_changed_at.date()

        logger.info("Синхронизация %s началась с даты %s", run_id, changed_at)
        max_changed_at = last_changed_at

        try:
            async for event in EventsPaginator(self.client, changed_at):
                await self.events.upsert(event)
                if max_changed_at is None or event.changed_at > max_changed_at:
                    max_changed_at = event.changed_at
            await self.sync_runs.finish_success(run_id, max_changed_at)
            await self.transaction.commit()
        except Exception as exc:
            await self.transaction.rollback()
            await self.sync_runs.finish_failed(run_id, str(exc))
            await self.transaction.commit()
            logger.exception("Синхронизация %s упала", run_id)
            raise

        logger.info(
            "Синхронизация %s завершена, last_changed_at=%s", run_id, max_changed_at
        )
