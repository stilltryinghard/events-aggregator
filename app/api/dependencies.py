from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import SeatsCache
from app.clients.events_provider import EventsProviderClient
from app.db import get_session
from app.repositories.events import EventRepository
from app.repositories.health import HealthRepository
from app.repositories.sync_runs import SyncRunRepository
from app.repositories.tickets import TicketRepository
from app.usecases.get_seats import GetSeatsUsecase
from app.usecases.sync_events import SyncEventsUsecase
from app.usecases.tickets import CancelTicketUsecase, CreateTicketUsecase

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_health_repository(session: SessionDep) -> HealthRepository:
    return HealthRepository(session)


HealthRepositoryDep = Annotated[HealthRepository, Depends(get_health_repository)]


def get_event_repository(session: SessionDep) -> EventRepository:
    return EventRepository(session)


EventRepositoryDep = Annotated[EventRepository, Depends(get_event_repository)]


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


def get_seats_cache(request: Request) -> SeatsCache:
    return request.app.state.seats_cache


SeatsCacheDep = Annotated[SeatsCache, Depends(get_seats_cache)]


def get_seats_usecase(
    session: SessionDep, client: EventsClientDep, cache: SeatsCacheDep
) -> GetSeatsUsecase:
    return GetSeatsUsecase(events=EventRepository(session), client=client, cache=cache)


SeatsUsecaseDep = Annotated[GetSeatsUsecase, Depends(get_seats_usecase)]


def get_create_ticket_usecase(
    session: SessionDep, client: EventsClientDep
) -> CreateTicketUsecase:
    return CreateTicketUsecase(
        events=EventRepository(session),
        tickets=TicketRepository(session),
        client=client,
        transaction=session,
    )


CreateTicketUsecaseDep = Annotated[
    CreateTicketUsecase, Depends(get_create_ticket_usecase)
]


def get_cancel_ticket_usecase(
    session: SessionDep, client: EventsClientDep
) -> CancelTicketUsecase:
    return CancelTicketUsecase(
        events=EventRepository(session),
        tickets=TicketRepository(session),
        client=client,
        transaction=session,
    )


CancelTicketUsecaseDep = Annotated[
    CancelTicketUsecase, Depends(get_cancel_ticket_usecase)
]
