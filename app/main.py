from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.api.health import router as health_router
from app.config import settings


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
