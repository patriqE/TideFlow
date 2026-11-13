"""Create a booking and reserve its seats in one database transaction."""
import time

from django.db import OperationalError, connection, transaction
from django.db.models import F

from .availability import refresh_schedule_availability, reserved_seat_count
from .models import Booking, ScheduleCapacity


class CapacityUnavailable(Exception):
    pass


class NotEnoughSeats(Exception):
    pass


class ReservationBusy(Exception):
    pass


def create_pending_booking(user, schedule, ride_date, seat_count):
    if type(seat_count) is not int or seat_count < 1:
        raise ValueError("seat_count must be a positive integer")
    for attempt in range(5):
        try:
            with transaction.atomic():
                # A write acquires SQLite's writer lock and a row lock on PostgreSQL.
                # Unlike select_for_update(), this also serializes SQLite bookings.
                capacity_rows = ScheduleCapacity.objects.filter(schedule_id=schedule.id)
                if not capacity_rows.update(max_passengers=F("max_passengers")):
                    raise CapacityUnavailable
                capacity = capacity_rows.get()
                remaining = capacity.max_passengers - reserved_seat_count(schedule.id, ride_date)
                if seat_count > remaining:
                    raise NotEnoughSeats
                booking = Booking.objects.create(
                    user=user, schedule=schedule, ride_date=ride_date, seat_count=seat_count,
                    payment_amount=schedule.price * seat_count,
                )
                refresh_schedule_availability(schedule, ride_date)
            return booking, remaining - seat_count
        except OperationalError as error:
            # Retry only a rolled-back SQLite lock failure, never arbitrary errors.
            if connection.vendor != "sqlite" or "locked" not in str(error).lower():
                raise
            if attempt == 4:
                raise ReservationBusy from error
            time.sleep(0.02 * (2 ** attempt))
