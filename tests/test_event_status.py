from sqlalchemy.dialects import postgresql

from app.db_types import EventStatusType
from app.enums import EventStatus


def test_known_event_status():
    db_type = EventStatusType()
    dialect = postgresql.dialect()

    result = db_type.process_result_value("published", dialect)

    assert result is EventStatus.PUBLISHED


def test_unknown_event_status():
    db_type = EventStatusType()
    dialect = postgresql.dialect()

    result = db_type.process_result_value("cancelled", dialect)

    assert result == "cancelled"
    assert type(result) is str


def test_save_event_status():
    db_type = EventStatusType()
    dialect = postgresql.dialect()

    result = db_type.process_bind_param(EventStatus.PUBLISHED, dialect)

    assert result == "published"
