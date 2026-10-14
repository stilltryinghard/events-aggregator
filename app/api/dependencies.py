from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.repositories.health import HealthRepository

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_health_repository(session: SessionDep) -> HealthRepository:
    return HealthRepository(session)


HealthRepositoryDep = Annotated[HealthRepository, Depends(get_health_repository)]
