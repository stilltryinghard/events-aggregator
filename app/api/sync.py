from fastapi import APIRouter

from app.api.dependencies import SyncUsecaseDep

router = APIRouter(prefix="/api")


@router.post("/sync/trigger")
async def trigger_sync(usecase: SyncUsecaseDep):
    started = await usecase.do()
    return {"status": "ok" if started else "already_running"}
