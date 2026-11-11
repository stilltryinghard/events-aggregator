import uuid
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

from app.api.dependencies import get_create_ticket_usecase
from app.api.tickets import router
from app.usecases.errors import IdempotencyConflict
from app.usecases.idempotency import build_request_hash
from app.usecases.tickets import CreateTicketUsecase


@pytest.mark.asyncio
async def test_repeated_purchase_returns_existing_ticket():
    event_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    key = "purchase-123"

    # Хеш данных уже совершённой покупки
    request_hash = build_request_hash(event_id, "Ivan", "Petrov", "ivan@test.com", "A1")

    # Подменяем реальные зависимости
    tickets = AsyncMock()
    client = AsyncMock()
    transaction = AsyncMock()

    # Имитируем найденный билет
    tickets.get_by_idempotency_key.return_value = (
        ticket_id,
        request_hash,
    )

    usecase = CreateTicketUsecase(
        events=AsyncMock(),
        tickets=tickets,
        client=client,
        transaction=transaction,
        outbox=AsyncMock(),
    )

    result = await usecase.do(
        event_id,
        "Ivan",
        "Petrov",
        "ivan@test.com",
        "A1",
        idempotency_key=key,
    )

    # Возвращается идентификатор старого билета
    assert result == ticket_id

    # Повторной регистрации не было
    client.register.assert_not_awaited()

    # Блокировка была запрошена
    tickets.lock_idempotency_key.assert_awaited_once_with(key)


@pytest.mark.asyncio
async def test_same_key_different_data():
    event_id = uuid.uuid4()
    ticket_id = uuid.uuid4()
    key = "purchase-123"

    # Сохранённая покупка была на место A1
    saved_hash = build_request_hash(event_id, "Ivan", "Petrov", "ivan@test.com", "A1")

    tickets = AsyncMock()
    client = AsyncMock()
    transaction = AsyncMock()

    tickets.get_by_idempotency_key.return_value = (
        ticket_id,
        saved_hash,
    )

    usecase = CreateTicketUsecase(
        events=AsyncMock(),
        tickets=tickets,
        client=client,
        transaction=transaction,
        outbox=AsyncMock(),
    )

    # Повторяем ключ, но меняем место на B2
    with pytest.raises(IdempotencyConflict):
        await usecase.do(
            event_id,
            "Ivan",
            "Petrov",
            "ivan@test.com",
            "B2",
            idempotency_key=key,
        )

    # Новый билет не должен создаваться
    client.register.assert_not_awaited()
    tickets.create.assert_not_awaited()
    transaction.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_idempotency_conflict_returns_409():
    # Создаём тестовое FastAPI-приложение
    app = FastAPI()
    app.include_router(router)

    # Имитируем конфликт в бизнес-логике
    usecase = AsyncMock()
    usecase.do.side_effect = IdempotencyConflict()

    # Подменяем настоящую зависимость
    app.dependency_overrides[get_create_ticket_usecase] = lambda: usecase

    # Отправляем HTTP-запрос без запуска сервера
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/tickets",
            json={
                "event_id": str(uuid.uuid4()),
                "first_name": "Ivan",
                "last_name": "Petrov",
                "email": "ivan@test.com",
                "seat": "A1",
                "idempotency_key": "purchase-123",
            },
        )

    # Проверяем HTTP-ответ
    assert response.status_code == 409
    assert response.json()["detail"] == (IdempotencyConflict.detail)
    usecase.do.assert_awaited_once()
