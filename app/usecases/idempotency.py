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
    data = [
        str(event_id),
        first_name,
        last_name,
        email,
        seat,
    ]

    raw = json.dumps(data, ensure_ascii=False)

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
