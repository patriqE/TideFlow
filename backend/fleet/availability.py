import os

from django.conf import settings

try:
    import redis
except Exception:  # pragma: no cover - dependency is optional for local tests
    redis = None


REDIS_KEY_PREFIX = "tideflow:seat-availability:schedule:"


def get_redis_client():
    redis_url = getattr(settings, "REDIS_URL", None) or os.environ.get("REDIS_URL")
    if not redis_url or redis is None:
        return None

    try:
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


def schedule_key(schedule_id):
    return f"{REDIS_KEY_PREFIX}{schedule_id}"


def seed_schedule_availability(schedule):
    capacity = getattr(schedule, "capacity", None)
    if not capacity:
        return None

    client = get_redis_client()
    if client is None:
        return int(capacity.max_passengers)

    client.set(schedule_key(schedule.id), int(capacity.max_passengers))
    return int(capacity.max_passengers)


def get_schedule_available_seats(schedule):
    capacity = getattr(schedule, "capacity", None)
    if not capacity:
        return None

    client = get_redis_client()
    if client is None:
        return int(capacity.max_passengers)

    current_value = client.get(schedule_key(schedule.id))
    if current_value is None:
        current_value = int(capacity.max_passengers)
        client.set(schedule_key(schedule.id), current_value)

    try:
        return int(current_value)
    except (TypeError, ValueError):
        client.set(schedule_key(schedule.id), int(capacity.max_passengers))
        return int(capacity.max_passengers)


def clear_schedule_availability(schedule_id):
    client = get_redis_client()
    if client is None:
        return False

    client.delete(schedule_key(schedule_id))
    return True