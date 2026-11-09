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
from app.outbox_worker import outbox_loop
from app.worker import sync_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with (
        httpx.AsyncClient(
            base_url=settings.events_provider_url,
            headers={"x-api-key": settings.events_provider_api_key},
            timeout=10.0,
        ) as events_http,
        httpx.AsyncClient(
            base_url=settings.capashino_url,
            headers={"X-API-Key": settings.capashino_api_key},
            timeout=10.0,
        ) as capashino_http,
    ):
        app.state.http = events_http
        app.state.seats_cache = SeatsCache(ttl_seconds=30)

        # Синхронизация мероприятий
        sync_task = asyncio.create_task(sync_loop(events_http))

        # Отправка уведомлений
        outbox_task = None
        if settings.capashino_api_key:
            outbox_task = asyncio.create_task(outbox_loop(capashino_http))

        try:
            yield
        finally:
            # Останавливаем фоновые задачи
            tasks = [sync_task]

            if outbox_task is not None:
                tasks.append(outbox_task)

            for task in tasks:
                task.cancel()

            for task in tasks:
                with suppress(asyncio.CancelledError):
                    await task


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


@app.exception_handler(httpx.HTTPError)
async def provider_error_handler(
    request: Request, exc: httpx.HTTPError
) -> JSONResponse:
    """Сбой Events Provider API: отвечаем 502, а не 500 с трейсбеком."""
    logging.getLogger(__name__).exception("Ошибка Events Provider API")
    return JSONResponse(
        status_code=502, content={"detail": "Events provider unavailable"}
    )
