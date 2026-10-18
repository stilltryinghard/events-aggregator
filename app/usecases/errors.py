class EventNotFound(Exception):
    """Событие не найдено в локальной базе."""


class EventNotPublished(Exception):
    """Событие не опубликовано, места и регистрация недоступны."""
