from enum import StrEnum


class EventStatus(StrEnum):
    PUBLISHED = "published"
    REGISTRATION_CLOSED = "registration_closed"
    FINISHED = "finished"


class OutboxStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"


class SyncRunStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class OutboxEventType(StrEnum):
    TICKET_PURCHASED = "ticket_purchased"
