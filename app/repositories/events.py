import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.entities import Event, Place
from app.models import Event as EventModel
from app.models import Place as PlaceModel


def _day_start(day: date) -> datetime:
    """Начало суток по UTC: date(2026, 10, 17) -> 2026-10-17 00:00:00+00:00."""
    return datetime.combine(day, time.min, tzinfo=UTC)


def _place_to_entity(model: PlaceModel) -> Place:
    return Place(
        id=model.id,
        name=model.name,
        city=model.city,
        address=model.address,
        seats_pattern=model.seats_pattern,
        changed_at=model.changed_at,
        created_at=model.created_at,
    )


def _to_entity(model: EventModel) -> Event:
    return Event(
        id=model.id,
        event_time=model.event_time,
        name=model.name,
        place=_place_to_entity(model.place),
        status=model.status,
        number_of_visitors=model.number_of_visitors,
        registration_deadline=model.registration_deadline,
        status_changed_at=model.status_changed_at,
        changed_at=model.changed_at,
        created_at=model.created_at,
    )


class EventRepository:
    """Работа с таблицами events и places.

    Принимает и отдаёт сущности из app.entities, ORM-модели наружу не выходят.
    Транзакцию не коммитит: когда фиксировать изменения, решает вызывающий код.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _upsert_place(self, place: Place) -> None:
        """Вставляет площадку или обновляет её, если площадка с таким id уже есть.

        Одна площадка приходит внутри каждого своего события, то есть много раз,
        поэтому обычный INSERT упал бы на повторе первичного ключа.

        SQL: INSERT INTO places ... ON CONFLICT (id) DO UPDATE SET ...
        """
        values = {
            "id": place.id,
            "name": place.name,
            "city": place.city,
            "address": place.address,
            "seats_pattern": place.seats_pattern,
            "changed_at": place.changed_at,
            "created_at": place.created_at,
        }
        stmt = insert(PlaceModel).values(**values)
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=values)
        await self.session.execute(stmt)

    async def upsert(self, event: Event) -> None:
        """Сохраняет событие вместе с его площадкой.

        Если событие с таким id уже есть, обновляет его: так повторная
        синхронизация не падает, а изменения у провайдера доезжают до нас.
        Площадка сохраняется первой, потому что у события внешний ключ на неё.
        """
        await self._upsert_place(event.place)

        values = {
            "id": event.id,
            "place_id": event.place.id,
            "name": event.name,
            "event_time": event.event_time,
            "registration_deadline": event.registration_deadline,
            "status": event.status,
            "number_of_visitors": event.number_of_visitors,
            "status_changed_at": event.status_changed_at,
            "changed_at": event.changed_at,
            "created_at": event.created_at,
        }
        stmt = insert(EventModel).values(**values)
        stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=values)
        await self.session.execute(stmt)

    async def count(self, date_from: date | None) -> int:
        stmt = select(func.count()).select_from(EventModel)
        if date_from is not None:
            stmt = stmt.where(EventModel.event_time >= _day_start(date_from))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_page(
        self, date_from: date | None, page: int, page_size: int
    ) -> list[Event]:
        stmt = select(EventModel).options(selectinload(EventModel.place))
        if date_from is not None:
            stmt = stmt.where(EventModel.event_time >= _day_start(date_from))
        stmt = (
            stmt.order_by(EventModel.event_time, EventModel.id)
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [_to_entity(model) for model in models]

    async def get(self, event_id: uuid.UUID) -> Event | None:
        """Возвращает событие с площадкой по id или None, если его нет"""
        stmt = (
            select(EventModel)
            .options(selectinload(EventModel.place))
            .where(EventModel.id == event_id)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _to_entity(model)
