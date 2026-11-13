from sqlalchemy.types import String, TypeDecorator

from app.enums import EventStatus


class EventStatusType(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        try:
            return EventStatus(value)
        except ValueError:
            return value
