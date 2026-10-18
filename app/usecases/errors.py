class AppError(Exception):
    """Ошибка бизнес-логики, detail уходит в ответ API."""

    detail = "Error"


class EventNotFound(AppError):
    detail = "Event not found"


class EventNotPublished(AppError):
    detail = "Event is not published"


class RegistrationClosed(AppError):
    detail = "Registration deadline has passed"


class SeatNotFound(AppError):
    detail = "Seat does not exist for this event"


class TicketNotFound(AppError):
    detail = "Ticket not found"


class EventAlreadyPassed(AppError):
    detail = "Event has already passed"
