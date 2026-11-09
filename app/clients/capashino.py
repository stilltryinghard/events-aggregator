import logging

logger = logging.getLogger(__name__)

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
        if response.status_code != 201:
            logger.error(
                "Capashino вернул %s: %s",
                response.status_code,
                response.text[:1000],
            )

        response.raise_for_status()
