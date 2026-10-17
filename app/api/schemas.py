import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlaceShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    city: str
    address: str


class EventListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    place: PlaceShort
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int


class EventsPageResponse(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[EventListItem]
