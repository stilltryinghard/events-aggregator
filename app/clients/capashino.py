import asyncio

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
        for attempt in range(5):
            try:
                response = await self.http.post(
                    "/api/notifications",
                    json={
                        "message": message,
                        "reference_id": ticket_id,
                        "idempotency_key": idempotency_key,
                    },
                )

                response.raise_for_status()
                return

            except httpx.HTTPStatusError as exc:
                # Ошибки 4xx не повторяем
                if exc.response.status_code < 500:
                    raise

                # Последняя попытка — отдаём ошибку воркеру
                if attempt == 4:
                    raise

            except httpx.TransportError:
                # Ошибка сети — тоже пробуем повторить
                if attempt == 4:
                    raise

            # Пауза перед следующей попыткой
            await asyncio.sleep(1)
