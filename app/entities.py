import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Place:
    id: uuid.UUID
    name: str
    city: str
    address: str
    seats_pattern: str
    changed_at: datetime
    created_at: datetime


@dataclass
class Event:
    id: uuid.UUID
    event_time: datetime
    name: str
    place: Place
    status: str
    number_of_visitors: int
    registration_deadline: datetime
    status_changed_at: datetime
    changed_at: datetime
    created_at: datetime


@dataclass
class Ticket:
    ticket_id: uuid.UUID
    event_id: uuid.UUID
    seat: str
