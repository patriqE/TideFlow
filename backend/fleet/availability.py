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


def schedule_key(schedule_id, ride_date=None):
    if ride_date is None:
        return f"{REDIS_KEY_PREFIX}{schedule_id}"
    return f"{REDIS_KEY_PREFIX}{schedule_id}:{ride_date.isoformat()}"


def seed_schedule_availability(schedule, ride_date=None):
    capacity = getattr(schedule, "capacity", None)
    if not capacity:
        return None

    client = get_redis_client()
    if client is None:
        return int(capacity.max_passengers)

    client.set(schedule_key(schedule.id, ride_date), int(capacity.max_passengers))
    return int(capacity.max_passengers)


def get_schedule_available_seats(schedule, ride_date=None):
    capacity = getattr(schedule, "capacity", None)
    if not capacity:
        return None

    client = get_redis_client()
    if client is None:
        return int(capacity.max_passengers)

    current_value = client.get(schedule_key(schedule.id, ride_date))
    if current_value is None:
        current_value = int(capacity.max_passengers)
        client.set(schedule_key(schedule.id, ride_date), current_value)

    try:
        return int(current_value)
    except (TypeError, ValueError):
        client.set(schedule_key(schedule.id, ride_date), int(capacity.max_passengers))
        return int(capacity.max_passengers)


def reserve_schedule_seats(schedule, ride_date, seat_count):
    capacity = getattr(schedule, "capacity", None)
    if not capacity:
        return None

    client = get_redis_client()
    if client is None:
        return None

    key = schedule_key(schedule.id, ride_date)
    current_value = client.get(key)
    if current_value is None:
        current_value = seed_schedule_availability(schedule, ride_date)

    try:
        available_seats = int(current_value)
    except (TypeError, ValueError):
        available_seats = int(capacity.max_passengers)

    if seat_count > available_seats:
        return None

    updated_value = available_seats - seat_count
    client.set(key, updated_value)
    return updated_value


def release_schedule_seats(schedule, ride_date, seat_count):
    capacity = getattr(schedule, "capacity", None)
    if not capacity:
        return None

    client = get_redis_client()
    if client is None:
        return None

    key = schedule_key(schedule.id, ride_date)
    current_value = client.get(key)
    if current_value is None:
        current_value = int(capacity.max_passengers)

    try:
        available_seats = int(current_value)
    except (TypeError, ValueError):
        available_seats = int(capacity.max_passengers)

    updated_value = min(int(capacity.max_passengers), available_seats + seat_count)
    client.set(key, updated_value)
    return updated_value


def clear_schedule_availability(schedule_id, ride_date=None):
    client = get_redis_client()
    if client is None:
        return False

    client.delete(schedule_key(schedule_id, ride_date))
    return True