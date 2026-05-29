import json

import redis

from app.config import settings


redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)


def session_key(call_id: str) -> str:
    return f"session:{call_id}"


def set_state(call_id: str, payload: dict, ttl_sec: int = 60 * 60 * 6) -> None:
    redis_client.set(session_key(call_id), json.dumps(payload), ex=ttl_sec)


def get_state(call_id: str) -> dict:
    data = redis_client.get(session_key(call_id))
    if not data:
        return {}
    return json.loads(data)


def events_key(call_id: str) -> str:
    return f"session_events:{call_id}"


def append_event(call_id: str, event: dict, ttl_sec: int = 60 * 60 * 6) -> int:
    seq = redis_client.rpush(events_key(call_id), json.dumps(event))
    redis_client.expire(events_key(call_id), ttl_sec)
    return int(seq)


def get_events_since(call_id: str, since_seq: int) -> list[dict]:
    start = max(since_seq, 0)
    raw = redis_client.lrange(events_key(call_id), start, -1)
    events = []
    for i, v in enumerate(raw):
        ev = json.loads(v)
        ev["seq"] = start + i + 1
        events.append(ev)
    return events
