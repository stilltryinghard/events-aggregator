import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.dependencies import EventRepositoryDep
from app.api.schemas import EventDetail, EventListItem, EventsPageResponse

router = APIRouter(prefix="/api")


@router.get("/events", response_model=EventsPageResponse)
async def list_events(
    request: Request,
    repository: EventRepositoryDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: date | None = None,
):
    count = await repository.count(date_from)
    events = await repository.get_page(date_from, page, page_size)

    next_url = None
    if page * page_size < count:
        next_url = str(request.url.include_query_params(page=page + 1))

    previous_url = None
    if page > 1:
        previous_url = str(request.url.include_query_params(page=page - 1))

    return EventsPageResponse(
        count=count,
        next=next_url,
        previous=previous_url,
        results=[EventListItem.model_validate(event) for event in events],
    )


@router.get("/events/{event_id}", response_model=EventDetail)
async def get_event(event_id: uuid.UUID, repository: EventRepositoryDep):
    event = await repository.get(event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return EventDetail.model_validate(event)
