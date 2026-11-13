"""Database-derived availability with an optional, best-effort Redis mirror."""
import logging

from django.conf import settings
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from .models import Booking, ScheduleCapacity

try:
    import redis
except ImportError:  # Redis is optional; reservations never depend on it.
    redis = None

logger = logging.getLogger(__name__)
REDIS_KEY_PREFIX = "tideflow:seat-availability:schedule:"


def get_redis_client():
    redis_url = getattr(settings, "REDIS_URL", None)
    if not redis_url or redis is None:
        return None
    try:
        return redis.Redis.from_url(
            redis_url, decode_responses=True, socket_connect_timeout=0.2,
            socket_timeout=0.2,
        )
    except (ValueError, redis.RedisError):
        return None


def schedule_key(schedule_id, ride_date=None):
    suffix = "" if ride_date is None else f":{ride_date.isoformat()}"
    return f"{REDIS_KEY_PREFIX}{schedule_id}{suffix}"


def reserved_seat_count(schedule_id, ride_date):
    return Booking.objects.filter(
        schedule_id=schedule_id, ride_date=ride_date,
    ).filter(
        Q(status=Booking.STATUS_CONFIRMED)
        | (Q(status=Booking.STATUS_PENDING) & (
            Q(expires_at__gt=timezone.now()) | Q(paid_at__isnull=False) | Q(payment_status="SUCCEEDED")
        ))
    ).aggregate(total=Sum("seat_count"))["total"] or 0


def _database_availability(schedule_id, ride_date):
    maximum = ScheduleCapacity.objects.filter(schedule_id=schedule_id).values_list("max_passengers", flat=True).first()
    if maximum is None:
        return None
    reserved = reserved_seat_count(schedule_id, ride_date) if ride_date is not None else 0
    return max(0, maximum - reserved)


def _mirror_availability(schedule_id, ride_date):
    # Recompute after commit; never publish an uncommitted reservation or release.
    available = _database_availability(schedule_id, ride_date)
    try:
        client = get_redis_client()
        if client is not None:
            if available is None:
                client.delete(schedule_key(schedule_id, ride_date))
            else:
                client.set(schedule_key(schedule_id, ride_date), available, ex=300)
    except Exception:
        # An optional cache outage must not turn a committed booking into an error.
        logger.warning("Unable to update seat availability cache for schedule %s", schedule_id)


def refresh_schedule_availability(schedule, ride_date=None):
    transaction.on_commit(lambda: _mirror_availability(schedule.id, ride_date), robust=True)


def get_schedule_available_seats(schedule, ride_date=None):
    available = _database_availability(schedule.id, ride_date)
    refresh_schedule_availability(schedule, ride_date)
    return available


def seed_schedule_availability(schedule, ride_date=None):
    return get_schedule_available_seats(schedule, ride_date)


def release_schedule_seats(schedule, ride_date, seat_count):
    # The cancellation in the database releases seats. Never increment a cache
    # counter: repeated events and recovery after Redis loss must be harmless.
    refresh_schedule_availability(schedule, ride_date)


def clear_schedule_availability(schedule_id, ride_date=None):
    def clear():
        try:
            client = get_redis_client()
            if client is not None:
                client.delete(schedule_key(schedule_id, ride_date))
        except Exception:
            logger.warning("Unable to clear seat availability cache for schedule %s", schedule_id)
    transaction.on_commit(clear, robust=True)
