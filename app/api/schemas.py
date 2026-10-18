import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class PlaceDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    city: str
    address: str
    seats_pattern: str


class EventDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    place: PlaceDetail
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int


class SeatsResponse(BaseModel):
    event_id: uuid.UUID
    available_seats: list[str]


class TicketCreate(BaseModel):
    event_id: uuid.UUID
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: EmailStr
    seat: str = Field(min_length=2)


class TicketCreated(BaseModel):
    ticket_id: uuid.UUID


class TicketCancelled(BaseModel):
    success: bool
