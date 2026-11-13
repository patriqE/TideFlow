from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from decimal import Decimal
from threading import Barrier
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, close_old_connections, connections, transaction
from django.test import TestCase, TransactionTestCase

from accounts.auth import create_access_token
from accounts.models import Profile
from .availability import get_schedule_available_seats, schedule_key
from .bookings import CapacityUnavailable, NotEnoughSeats, ReservationBusy, create_pending_booking
from .models import BoatRoute, BoatSchedule, Booking, ScheduleCapacity
from .tests import FakeRedisClient


def make_fixture():
    user = get_user_model().objects.create_user(username="availability-user")
    Profile.objects.create(user=user)
    route = BoatRoute.objects.create(name="Availability route", origin="A", destination="B")
    schedule = BoatSchedule.objects.create(
        route=route, departure_time="10:00", arrival_time="11:00",
        days_of_week=["thu"], price=Decimal("12.50"),
    )
    ScheduleCapacity.objects.create(schedule=schedule, max_passengers=3)
    return user, schedule, date(2026, 12, 3)


class AvailabilityTests(TestCase):
    def setUp(self):
        self.user, self.schedule, self.ride_date = make_fixture()
        self.cache = FakeRedisClient()
        self.enterContext(patch("fleet.availability.get_redis_client", return_value=self.cache))

    def book(self, count=1, ride_date=None):
        return create_pending_booking(self.user, self.schedule, ride_date or self.ride_date, count)

    def available(self):
        return get_schedule_available_seats(self.schedule, self.ride_date)

    def test_pending_and_confirmed_count_but_cancelled_do_not(self):
        first, _ = self.book()
        second, _ = self.book()
        Booking.objects.filter(pk=first.pk).update(status=Booking.STATUS_CONFIRMED)
        self.assertEqual(self.available(), 1)
        Booking.objects.filter(pk=second.pk).update(status=Booking.STATUS_CANCELLED)
        self.assertEqual(self.available(), 2)

    def test_dates_have_independent_capacity(self):
        self.book(3)
        booking, remaining = self.book(3, self.ride_date + timedelta(days=1))
        self.assertEqual(remaining, 0)
        self.assertEqual(self.available(), 0)
        self.assertEqual(Booking.objects.count(), 2)

    def test_sold_out_booking_is_rejected_without_new_record(self):
        self.book(3)
        with self.assertRaises(NotEnoughSeats):
            self.book()
        self.assertEqual(Booking.objects.count(), 1)

    def test_missing_stale_or_corrupt_cache_is_rebuilt_from_bookings(self):
        self.book(2)
        key = schedule_key(self.schedule.pk, self.ride_date)
        for value in (None, "999", "not-an-integer", "0"):
            with self.subTest(value=value):
                if value is None:
                    self.cache.delete(key)
                else:
                    self.cache.set(key, value)
                with self.captureOnCommitCallbacks(execute=True):
                    self.assertEqual(self.available(), 1)
                self.assertEqual(self.cache.get(key), "1")

    def test_api_books_without_redis_and_rejects_overselling(self):
        with patch("fleet.availability.get_redis_client", return_value=None):
            headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(self.user)}"}
            data = {"schedule_id": self.schedule.pk, "ride_date": self.ride_date.isoformat(), "seat_count": 3}
            response = self.client.post("/fleet/bookings/", data, content_type="application/json", **headers)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()["available_seats_after_booking"], 0)
            response = self.client.post("/fleet/bookings/", data, content_type="application/json", **headers)
            self.assertEqual(response.status_code, 409)
            self.assertEqual(self.available(), 0)

    def test_cache_write_failure_does_not_fail_booking_and_recovers(self):
        broken_cache = Mock()
        broken_cache.set.side_effect = ConnectionError("Redis down")
        with patch("fleet.availability.get_redis_client", return_value=broken_cache):
            with self.captureOnCommitCallbacks(execute=True):
                booking, remaining = self.book(2)
        self.assertTrue(Booking.objects.filter(pk=booking.pk).exists())
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.available(), 1)
        self.assertEqual(self.cache.get(schedule_key(self.schedule.pk, self.ride_date)), "1")

    def test_database_insert_failure_does_not_reserve_or_publish_seats(self):
        with patch("fleet.bookings.Booking.objects.create", side_effect=IntegrityError("Insert failed")):
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                with self.assertRaises(IntegrityError):
                    self.book(2)
        self.assertEqual(callbacks, [])
        self.assertEqual(Booking.objects.count(), 0)
        self.assertEqual(self.available(), 3)

    def test_outer_rollback_does_not_publish_or_keep_reservation(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            with self.assertRaises(RuntimeError):
                with transaction.atomic():
                    self.book(2)
                    raise RuntimeError("Abort outer transaction")
        self.assertEqual(callbacks, [])
        self.assertEqual(Booking.objects.count(), 0)

    def test_capacity_changes_use_current_database_value(self):
        self.book(2)
        ScheduleCapacity.objects.filter(schedule=self.schedule).update(max_passengers=4)
        self.assertEqual(self.available(), 2)
        self.book(2)
        ScheduleCapacity.objects.filter(schedule=self.schedule).update(max_passengers=2)
        self.assertEqual(self.available(), 0)
        with self.assertRaises(NotEnoughSeats):
            self.book()

    def test_missing_capacity_fails_closed(self):
        ScheduleCapacity.objects.filter(schedule=self.schedule).delete()
        self.assertIsNone(self.available())
        with self.assertRaises(CapacityUnavailable):
            self.book()

    def test_cancellation_during_redis_outage_recovers_without_double_release(self):
        booking, _ = self.book(2)
        with patch("fleet.availability.get_redis_client", return_value=None):
            for _ in range(2):
                response = self.client.delete(
                    f"/fleet/bookings/{booking.booking_code}/",
                    HTTP_AUTHORIZATION=f"Bearer {create_access_token(self.user)}",
                )
                self.assertEqual(response.status_code, 200)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.available(), 3)
        self.assertEqual(self.cache.get(schedule_key(self.schedule.pk, self.ride_date)), "3")

    def test_database_lock_exhaustion_returns_retryable_response(self):
        with patch("fleet.views.create_pending_booking", side_effect=ReservationBusy):
            response = self.client.post("/fleet/bookings/", {
                "schedule_id": self.schedule.pk, "ride_date": self.ride_date.isoformat(),
            }, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {create_access_token(self.user)}")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(Booking.objects.count(), 0)


class ConcurrentReservationTests(TransactionTestCase):
    def test_competing_connections_cannot_oversell_last_seat(self):
        user, schedule, ride_date = make_fixture()
        ScheduleCapacity.objects.filter(schedule=schedule).update(max_passengers=1)
        barrier = Barrier(4)

        def reserve():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    create_pending_booking(user, schedule, ride_date, 1)
                    return "created"
                except NotEnoughSeats:
                    return "sold-out"
                except ReservationBusy:
                    return "retry"
            finally:
                connections.close_all()

        with patch("fleet.availability.get_redis_client", return_value=None):
            with ThreadPoolExecutor(max_workers=4) as pool:
                outcomes = list(pool.map(lambda _: reserve(), range(4)))
        self.assertEqual(outcomes.count("created"), 1, outcomes)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(Booking.objects.get().seat_count, 1)
        with self.assertRaises(NotEnoughSeats):
            create_pending_booking(user, schedule, ride_date, 1)
