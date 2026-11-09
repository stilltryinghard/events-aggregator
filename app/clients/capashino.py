import httpx


class CapashinoClient:
    def __init__(self, http: httpx.AsyncClient):
        self.http = http

    async def send_notification(
        self,
        message: str,
        ticket_id: str,
        idempotency_key: str,
    ) -> None:
        # Отправляем уведомление в Capashino
        response = await self.http.post(
            "/api/notifications",
            json={
                "mesage": message,
                "reference_id": ticket_id,
                "idempotency_key": idempotency_key,
            },
        )
        # Если capashino вернул ошибку - выбрасываем исключение
        response.raise_for_status()
