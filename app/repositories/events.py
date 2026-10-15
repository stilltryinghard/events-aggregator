from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities import Event, Place
from app.models import Event as EventModel
from app.models import Place as PlaceModel


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
