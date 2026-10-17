from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.events_provider import EventsProviderClient
from app.db import get_session
from app.repositories.events import EventRepository
from app.repositories.health import HealthRepository
from app.repositories.sync_runs import SyncRunRepository
from app.usecases.sync_events import SyncEventsUsecase

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_health_repository(session: SessionDep) -> HealthRepository:
    return HealthRepository(session)


HealthRepositoryDep = Annotated[HealthRepository, Depends(get_health_repository)]


def get_events_client(request: Request) -> EventsProviderClient:
    return EventsProviderClient(request.app.state.http)


EventsClientDep = Annotated[EventsProviderClient, Depends(get_events_client)]


def get_sync_usecase(session: SessionDep, client: EventsClientDep) -> SyncEventsUsecase:
    return SyncEventsUsecase(
        client=client,
        events=EventRepository(session),
        sync_runs=SyncRunRepository(session),
        transaction=session,
    )


SyncUsecaseDep = Annotated[SyncEventsUsecase, Depends(get_sync_usecase)]
