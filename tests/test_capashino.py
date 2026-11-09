import httpx
import pytest

from app.clients.capashino import CapashinoClient


@pytest.mark.asyncio
async def test_send_notification():
    def handle(request):
        # Проверяем отправляемый JSON
        data = __import__("json").loads(request.content)

        assert data["message"] == "Билет куплен"
        assert data["reference_id"] == "ticket-123"
        assert data["idempotency_key"] == "key-123"

        # Имитируем успешный ответ Capashino
        return httpx.Response(201)

    transport = httpx.MockTransport(handle)

    async with httpx.AsyncClient(
        base_url="http://test",
        transport=transport,
    ) as http:
        client = CapashinoClient(http)

        await client.send_notification(
            message="Билет куплен",
            ticket_id="ticket-123",
            idempotency_key="key-123",
        )
