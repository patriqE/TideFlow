import hashlib
import hmac
import json
from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.auth import create_access_token
from accounts.models import Profile
from .availability import get_schedule_available_seats
from .bookings import create_pending_booking
from .expiry import expire_unpaid_bookings
from .models import BoatRoute, BoatSchedule, Booking, ScheduleCapacity
from .views import _confirm_booking_payment


@override_settings(REDIS_URL="", PAYSTACK_WEBHOOK_SECRET="expiry-test-secret")
class ReservationExpiryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="expiry-user")
        Profile.objects.create(user=self.user)
        route = BoatRoute.objects.create(name="Expiry route", origin="A", destination="B")
        self.schedule = BoatSchedule.objects.create(
            route=route, departure_time="10:00", arrival_time="11:00", price=Decimal("10.00"),
        )
        ScheduleCapacity.objects.create(schedule=self.schedule, max_passengers=1)
        self.ride_date = date(2026, 12, 1)
        self.booking, _ = create_pending_booking(self.user, self.schedule, self.ride_date, 1)
        Booking.objects.filter(pk=self.booking.pk).update(payment_reference="expiry-reference")
        self.booking.refresh_from_db()
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(self.user)}"}

    def pass_deadline(self):
        Booking.objects.filter(pk=self.booking.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
        self.booking.refresh_from_db()

    def evidence(self):
        return {"status": "success", "reference": "expiry-reference", "amount": 1000,
                "currency": "NGN", "metadata": {"booking_code": str(self.booking.booking_code)}}

    def webhook(self):
        body = json.dumps({"event": "charge.success", "data": self.evidence()}).encode()
        signature = hmac.new(b"expiry-test-secret", body, hashlib.sha512).hexdigest()
        return self.client.post("/fleet/payments/webhook/", body, content_type="application/json",
                                HTTP_X_PAYSTACK_SIGNATURE=signature)

    def test_default_hold_is_fifteen_minutes_and_deadline_is_exposed(self):
        self.assertAlmostEqual((self.booking.expires_at - self.booking.created_at).total_seconds(), 900, delta=1)
        response = self.client.get(f"/fleet/bookings/{self.booking.booking_code}/", **self.headers)
        self.assertEqual(response.json()["expires_at"], self.booking.expires_at.isoformat())

    @override_settings(BOOKING_HOLD_MINUTES=7)
    def test_custom_window_applies_to_new_bookings(self):
        new, _ = create_pending_booking(self.user, self.schedule, self.ride_date + timedelta(days=1), 1)
        self.assertAlmostEqual((new.expires_at - new.created_at).total_seconds(), 420, delta=1)

    def test_expiry_frees_capacity_without_cleanup_job(self):
        self.pass_deadline()
        self.assertEqual(get_schedule_available_seats(self.schedule, self.ride_date), 1)
        new, remaining = create_pending_booking(self.user, self.schedule, self.ride_date, 1)
        self.assertEqual(remaining, 0)
        self.assertNotEqual(new.pk, self.booking.pk)
        self.assertEqual(get_schedule_available_seats(self.schedule, self.ride_date), 0)

    def test_exact_deadline_is_expired(self):
        with patch("django.utils.timezone.now", return_value=self.booking.expires_at):
            self.assertEqual(get_schedule_available_seats(self.schedule, self.ride_date), 1)
            self.assertEqual(expire_unpaid_bookings(), 1)

    def test_cleanup_command_is_repeatable(self):
        self.pass_deadline()
        output = StringIO()
        call_command("expire_bookings", stdout=output)
        call_command("expire_bookings", stdout=output)
        self.assertIn("Expired 1", output.getvalue())
        self.assertIn("Expired 0", output.getvalue())
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CANCELLED)
        self.assertEqual(self.booking.payment_status, "EXPIRED")

    def test_active_and_paid_bookings_are_not_expired(self):
        self.assertEqual(expire_unpaid_bookings(), 0)
        _confirm_booking_payment(self.booking)
        self.pass_deadline()
        self.assertEqual(expire_unpaid_bookings(), 0)
        self.assertEqual(get_schedule_available_seats(self.schedule, self.ride_date), 0)

    def test_inconsistent_paid_pending_booking_is_not_released(self):
        self.pass_deadline()
        for values in ({"payment_status": "SUCCEEDED", "paid_at": None},
                       {"payment_status": "INITIATED", "paid_at": timezone.now()}):
            Booking.objects.filter(pk=self.booking.pk).update(**values)
            self.assertEqual(expire_unpaid_bookings(), 0)
            self.assertEqual(get_schedule_available_seats(self.schedule, self.ride_date), 0)

    def test_expired_checkout_is_rejected_before_provider_call(self):
        self.pass_deadline()
        with patch("fleet.views.create_paystack_session") as initialize:
            response = self.client.post(f"/fleet/bookings/{self.booking.booking_code}/payment/", **self.headers)
        self.assertEqual(response.status_code, 409)
        initialize.assert_not_called()

    def test_hold_expiring_during_initialization_does_not_return_checkout_url(self):
        def initialize(booking):
            self.pass_deadline()
            return SimpleNamespace(reference="new-reference", authorization_url="https://paystack.test/checkout", access_code="code"), None

        with patch("fleet.views.create_paystack_session", side_effect=initialize):
            response = self.client.post(f"/fleet/bookings/{self.booking.booking_code}/payment/", **self.headers)
        self.assertEqual(response.status_code, 409)
        self.assertNotIn("authorization_url", response.json())
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_reference, "new-reference")
        self.assertEqual(self.booking.payment_status, "EXPIRED")

    def test_late_payment_cannot_reclaim_reallocated_seat(self):
        self.pass_deadline()
        replacement, _ = create_pending_booking(self.user, self.schedule, self.ride_date, 1)
        self.assertEqual(self.webhook().status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CANCELLED)
        self.assertEqual(self.booking.payment_status, "REFUND_REQUIRED")
        paid_at = self.booking.paid_at
        self.assertIsNotNone(paid_at)
        self.assertEqual(self.webhook().status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.paid_at, paid_at)
        self.assertEqual(expire_unpaid_bookings(), 0)
        self.assertEqual(get_schedule_available_seats(self.schedule, self.ride_date), 0)
        replacement.refresh_from_db()
        self.assertEqual(replacement.status, Booking.STATUS_PENDING)

    def test_callback_records_late_payment_for_refund_review(self):
        self.pass_deadline()
        with patch("fleet.views.verify_paystack_transaction", return_value=(self.evidence(), None)):
            response = self.client.get("/payment/success/", {"booking_code": str(self.booking.booking_code)})
        self.assertEqual(response.status_code, 409)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status, "REFUND_REQUIRED")

    def test_unverified_late_payment_is_not_recorded(self):
        self.pass_deadline()
        evidence = self.evidence()
        evidence["amount"] = 1
        with patch("fleet.views.verify_paystack_transaction", return_value=(evidence, None)):
            response = self.client.get("/payment/success/", {"booking_code": str(self.booking.booking_code)})
        self.assertEqual(response.status_code, 400)
        self.booking.refresh_from_db()
        self.assertIsNone(self.booking.paid_at)

    def test_deadline_crossed_during_verification_is_not_confirmed(self):
        def verify(reference):
            self.pass_deadline()
            return self.evidence(), None

        with patch("fleet.views.verify_paystack_transaction", side_effect=verify):
            response = self.client.get("/payment/success/", {"booking_code": str(self.booking.booking_code)})
        self.assertEqual(response.status_code, 409)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CANCELLED)
        self.assertEqual(self.booking.payment_status, "REFUND_REQUIRED")
