from fastapi import APIRouter

from app.api.dependencies import HealthRepositoryDep

router = APIRouter(prefix="/api")


@router.get("/health")
async def health(repository: HealthRepositoryDep):
    await repository.ping()
    return {"status": "ok"}
