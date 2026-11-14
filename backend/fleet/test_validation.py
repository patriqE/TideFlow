import json
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.auth import create_access_token
from accounts.models import Profile
from .models import BoatRoute, BoatSchedule, ScheduleCapacity, Booking


@override_settings(REDIS_URL="")
class FleetValidationTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(username="admin", is_superuser=True)
        self.user = get_user_model().objects.create_user(username="passenger")
        Profile.objects.create(user=self.user)
        self.admin_headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(self.admin)}"}
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(self.user)}"}
        self.route = BoatRoute.objects.create(name="Validation route", origin="A", destination="B")
        self.schedule = BoatSchedule.objects.create(route=self.route, departure_time="10:00", arrival_time="11:00",
                                                   price=Decimal("10.00"), days_of_week=["thu"])
        self.capacity = ScheduleCapacity.objects.create(schedule=self.schedule, max_passengers=10)

    def test_bad_top_level_payloads_return_400(self):
        for endpoint, headers in (("routes", self.admin_headers), ("schedules", self.admin_headers),
                                  ("capacities", self.admin_headers), ("bookings", self.headers)):
            for data in ([], "value", None, True):
                response = self.client.post(f"/fleet/{endpoint}/", json.dumps(data), content_type="application/json", **headers)
                self.assertEqual(response.status_code, 400)

    def test_invalid_schedule_fields_return_400_without_mutation(self):
        cases = [("price", value) for value in (-1, "NaN", "Infinity", "0.001", "100000000.00", None, True)]
        cases += [("departure_time", value) for value in ([], 12, "25:00", "garbage", "10:00+02:00")]
        cases += [("days_of_week", value) for value in ([], [1], ["noday"], None)]
        cases += [("route_id", value) for value in (True, 1.5, [], "no")]
        cases += [("is_active", "false")]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                response = self.client.patch(f"/fleet/schedules/{self.schedule.pk}/", {field: value}, content_type="application/json", **self.admin_headers)
                self.assertEqual(response.status_code, 400)
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.price, Decimal("10.00"))
        self.assertTrue(self.schedule.is_active)

    def test_valid_weekdays_and_zero_price(self):
        response = self.client.patch(f"/fleet/schedules/{self.schedule.pk}/", {"price": "0.00", "days_of_week": ["Thursday", "thu"]}, content_type="application/json", **self.admin_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["days_of_week"], ["thu"])

    def test_capacity_integer_validation_on_create_and_update(self):
        for field in ("max_passengers", "max_cargo_kg"):
            for value in (-1, 1.5, True, "3.2", None, 2147483648):
                with self.subTest(field=field, value=value):
                    data = {"schedule_id": self.schedule.pk, "max_passengers": 10, field: value}
                    self.assertEqual(self.client.post("/fleet/capacities/", data, content_type="application/json", **self.admin_headers).status_code, 400)
                    self.assertEqual(self.client.patch(f"/fleet/capacities/{self.capacity.pk}/", {field: value}, content_type="application/json", **self.admin_headers).status_code, 400)

    def test_capacity_cannot_drop_below_reserved_seats(self):
        Booking.objects.create(user=self.user, schedule=self.schedule, ride_date=date(2099, 1, 1), seat_count=4)
        response = self.client.patch(f"/fleet/capacities/{self.capacity.pk}/", {"max_passengers": 3}, content_type="application/json", **self.admin_headers)
        self.assertEqual(response.status_code, 409)
        self.capacity.refresh_from_db()
        self.assertEqual(self.capacity.max_passengers, 10)

    def test_booking_rejects_fractional_boolean_and_invalid_ids(self):
        for field, value in [("seat_count", 1.5), ("seat_count", True), ("seat_count", "2.5"),
                             ("schedule_id", []), ("schedule_id", False)]:
            data = {"schedule_id": self.schedule.pk, "seat_count": 1, "ride_date": "2099-01-01", field: value}
            self.assertEqual(self.client.post("/fleet/bookings/", data, content_type="application/json", **self.headers).status_code, 400)
        self.assertEqual(Booking.objects.count(), 0)

    def test_invalid_or_past_booking_dates_are_rejected(self):
        for value in ([], 123, "2099-1-1", "2099-02-30", (timezone.localdate() - timedelta(days=1)).isoformat()):
            data = {"schedule_id": self.schedule.pk, "ride_date": value}
            self.assertEqual(self.client.post("/fleet/bookings/", data, content_type="application/json", **self.headers).status_code, 400)

    def test_same_day_departure_in_past_is_rejected(self):
        self.schedule.departure_time = "00:00"
        self.schedule.days_of_week = [timezone.localdate().strftime("%a")]
        self.schedule.save()
        response = self.client.post("/fleet/bookings/", {"schedule_id": self.schedule.pk, "ride_date": timezone.localdate().isoformat()}, content_type="application/json", **self.headers)
        self.assertEqual(response.status_code, 400)

    def test_total_amount_overflow_does_not_create_booking(self):
        self.schedule.price = Decimal("99999999.99")
        self.schedule.save()
        response = self.client.post("/fleet/bookings/", {"schedule_id": self.schedule.pk, "ride_date": "2099-01-01", "seat_count": 2}, content_type="application/json", **self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Booking.objects.count(), 0)
