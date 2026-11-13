import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.db_types import EventStatusType
from app.enums import EventStatus, OutboxEventType, OutboxStatus, SyncRunStatus


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
    status: Mapped[EventStatus | str] = mapped_column(EventStatusType())
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
    idempotency_key: Mapped[str | None] = mapped_column(
        unique=True,
        nullable=True,
    )
    request_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SyncRun(Base):
    __tablename__ = "sync_runs"

    __table_args__ = (
        Index(
            "uq_sync_runs_single_running",
            "status",
            unique=True,
            postgresql_where=text("status = 'running'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    status: Mapped[SyncRunStatus] = mapped_column(
        SQLEnum(
            SyncRunStatus,
            native_enum=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None]


class Outbox(Base):
    __tablename__ = "outbox"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    event_type: Mapped[OutboxEventType] = mapped_column(
        SQLEnum(
            OutboxEventType,
            native_enum=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
    )

    payload: Mapped[dict] = mapped_column(JSON)

    status: Mapped[OutboxStatus] = mapped_column(
        SQLEnum(
            OutboxStatus,
            native_enum=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=OutboxStatus.PENDING,
        server_default=OutboxStatus.PENDING.value,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
