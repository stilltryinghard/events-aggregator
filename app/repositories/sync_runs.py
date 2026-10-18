import uuid
from datetime import datetime

from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SyncRun as SyncRunModel


class SyncRunRepository:
    """Работа с журналом синхронизаций, таблицей sync_runs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def start(self) -> uuid.UUID | None:
        """Записывает начало синхронизации со статусом running и возвращает id строки.
        Если другая синхронизация уже идёт, возвращает None: уникальный индекс
        не даёт вставить вторую строку running. Зависшие running старше часа
        сначала помечаются упавшими, чтобы не блокировать синхронизацию навсегда.
        """

        await self.session.execute(
            update(SyncRunModel)
            .where(
                SyncRunModel.status == "running",
                SyncRunModel.started_at < func.now() - text("interval '1 hour'"),
            )
            .values(status="failed", finished_at=func.now(), error="stale run")
        )
        run = SyncRunModel(status="running")
        try:
            async with self.session.begin_nested():
                self.session.add(run)
        except IntegrityError:
            return None
        return run.id

    async def last_changed_at(self) -> datetime | None:
        """Возвращает last_changed_at последней успешной синхронизации или None,
        если их ещё не было"""
        stmt = (
            select(SyncRunModel.last_changed_at)
            .where(SyncRunModel.status == "success")
            .where(SyncRunModel.last_changed_at.is_not(None))
            .order_by(SyncRunModel.started_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def finish_success(
        self, run_id: uuid.UUID, last_changed_at: datetime | None
    ) -> None:
        stmt = (
            update(SyncRunModel)
            .where(SyncRunModel.id == run_id)
            .values(
                status="success",
                finished_at=func.now(),
                last_changed_at=last_changed_at,
            )
        )

        await self.session.execute(stmt)

    async def finish_failed(self, run_id: uuid.UUID, error: str) -> None:
        stmt = (
            update(SyncRunModel)
            .where(SyncRunModel.id == run_id)
            .values(
                status="failed",
                finished_at=func.now(),
                error=error,
            )
        )
        await self.session.execute(stmt)
