import hashlib
import json
import uuid


def build_request_hash(
    event_id: uuid.UUID,
    first_name: str,
    last_name: str,
    email: str,
    seat: str,
) -> str:
    # Собираем данные покупки в определённом порядке
    data = [
        str(event_id),
        first_name,
        last_name,
        email,
        seat,
    ]

    # Превращаем данные в строку JSON
    raw = json.dumps(data, ensure_ascii=False)

    # Вычисляем SHA-256 и возвращаем строку из 64 символов
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
