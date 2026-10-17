import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.sync import router as sync_router
from app.config import settings

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
        yield


app = FastAPI(lifespan=lifespan)
app.include_router(health_router)
app.include_router(sync_router)
