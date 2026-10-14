import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Place(Base):
    __tablename__ = "places"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    city: Mapped[str]
    address: Mapped[str]
    seats_pattern: Mapped[str]
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    name: Mapped[str]
    place_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("places.id"))
    place: Mapped[Place] = relationship()
    status: Mapped[str]
    number_of_visitors: Mapped[int]
    registration_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Ticket(Base):
    __tablename__ = "tickets"

    __table_args__ = (
        Index(
            "uq_tickets_active_ticket_id",
            "ticket_id",
            unique=True,
            postgresql_where=text("cancelled_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    ticket_id: Mapped[uuid.UUID]
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id"))
    first_name: Mapped[str]
    last_name: Mapped[str]
    email: Mapped[str]
    seat: Mapped[str]
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    status: Mapped[str]
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None]
