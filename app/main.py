import asyncio
import logging
from contextlib import asynccontextmanager, suppress

import httpx
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.events import router as events_router
from app.api.health import router as health_router
from app.api.sync import router as sync_router
from app.api.tickets import router as tickets_router
from app.cache import SeatsCache
from app.config import settings
from app.worker import sync_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(
        base_url=settings.events_provider_url,
        headers={"x-api-key": settings.events_provider_api_key},
        timeout=10.0,
    ) as http:
        app.state.http = http
        app.state.seats_cache = SeatsCache(ttl_seconds=30)
        sync_task = asyncio.create_task(sync_loop(http))
        yield
        sync_task.cancel()
        with suppress(asyncio.CancelledError):
            await sync_task


app = FastAPI(lifespan=lifespan)
app.include_router(health_router)
app.include_router(sync_router)
app.include_router(events_router)
app.include_router(tickets_router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Ошибки валидации запроса отдаём как 400, как в контракте ТЗ."""
    return JSONResponse(
        status_code=400,
        content={"detail": jsonable_encoder(exc.errors())},
    )
