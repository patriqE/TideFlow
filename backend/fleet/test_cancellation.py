import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.auth import create_access_token
from accounts.models import Profile
from .models import BoatRoute, BoatSchedule, Booking
from .views import _confirm_booking_payment, _fail_booking_payment


@override_settings(PAYSTACK_WEBHOOK_SECRET="cancellation-test-secret")
class CancellationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username="owner")
        cls.other = get_user_model().objects.create_user(username="other")
        Profile.objects.create(user=cls.owner)
        Profile.objects.create(user=cls.other)
        route = BoatRoute.objects.create(name="Cancellation route", origin="A", destination="B")
        schedule = BoatSchedule.objects.create(route=route, departure_time="10:00", arrival_time="11:00")
        cls.booking = Booking.objects.create(
            user=cls.owner, schedule=schedule, ride_date="2026-12-01",
            payment_amount=Decimal("10.00"), payment_reference="cancel-test-reference",
            payment_status="INITIATED", seat_count=2,
        )

    def setUp(self):
        self.release = self.enterContext(patch("fleet.views.release_schedule_seats"))
        self.url = reverse("fleet_booking_detail", args=[self.booking.booking_code])

    def cancel(self, user=None):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(user)}"} if user else {}
        return self.client.delete(self.url, **headers)

    def assert_unchanged(self):
        current = Booking.objects.get(pk=self.booking.pk)
        self.assertEqual(current.status, self.booking.status)
        self.assertEqual(current.payment_status, self.booking.payment_status)
        self.assertEqual(current.paid_at, self.booking.paid_at)
        self.release.assert_not_called()

    def mark_paid(self):
        Booking.objects.filter(pk=self.booking.pk).update(
            status=Booking.STATUS_CONFIRMED, payment_status="SUCCEEDED", paid_at=timezone.now(),
        )
        self.booking.refresh_from_db()

    def failure_webhook(self, event_type="charge.failed"):
        body = json.dumps({"event": event_type, "data": {
            "reference": self.booking.payment_reference, "amount": 1000, "currency": "NGN",
            "metadata": {"booking_code": str(self.booking.booking_code)},
        }}).encode()
        signature = hmac.new(b"cancellation-test-secret", body, hashlib.sha512).hexdigest()
        return self.client.post(reverse("fleet_payment_webhook"), body, content_type="application/json",
                                HTTP_X_PAYSTACK_SIGNATURE=signature)

    def test_anonymous_cancellation_is_rejected(self):
        self.assertEqual(self.cancel().status_code, 401)
        self.assert_unchanged()

    def test_other_passenger_cannot_cancel_booking(self):
        self.assertEqual(self.cancel(self.other).status_code, 404)
        self.assert_unchanged()

    def test_cookie_session_alone_cannot_cancel_csrf_exempt_api(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.cancel().status_code, 401)
        self.assert_unchanged()

    def test_owner_can_cancel_unpaid_booking_only_once(self):
        for _ in range(2):
            response = self.cancel(self.owner)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], Booking.STATUS_CANCELLED)
            self.assertEqual(response.json()["payment_status"], "CANCELLED")
        self.release.assert_called_once()

    def test_public_checkout_redirect_does_not_cancel_or_expose_booking(self):
        for paid in (False, True):
            if paid:
                self.mark_paid()
            response = self.client.get(reverse("payment-cancel"), {"booking_code": str(self.booking.booking_code)})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(set(response.json()), {"detail"})
            self.assert_unchanged()

    def test_public_checkout_post_cannot_cancel(self):
        response = self.client.post(reverse("payment-cancel"), {"booking_code": str(self.booking.booking_code)})
        self.assertEqual(response.status_code, 405)
        self.assert_unchanged()

    def test_booking_get_does_not_cancel(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION=f"Bearer {create_access_token(self.owner)}")
        self.assertEqual(response.status_code, 200)
        self.assert_unchanged()

    def test_paid_booking_cannot_be_cancelled_by_owner(self):
        self.mark_paid()
        self.assertEqual(self.cancel(self.owner).status_code, 409)
        self.assert_unchanged()

    def test_each_payment_indicator_blocks_cancellation(self):
        for fields in ({"status": Booking.STATUS_CONFIRMED}, {"payment_status": "SUCCEEDED"},
                       {"paid_at": timezone.now()}):
            with self.subTest(fields=fields):
                Booking.objects.filter(pk=self.booking.pk).update(
                    status=Booking.STATUS_PENDING, payment_status="INITIATED", paid_at=None,
                )
                Booking.objects.filter(pk=self.booking.pk).update(**fields)
                self.booking.refresh_from_db()
                self.assertEqual(self.cancel(self.owner).status_code, 409)
                self.assert_unchanged()

    def test_late_failure_webhooks_cannot_undo_success(self):
        self.mark_paid()
        for event_type in ("charge.failed", "charge.abandoned"):
            self.assertEqual(self.failure_webhook(event_type).status_code, 200)
            self.assert_unchanged()

    def test_repeated_failure_webhooks_release_once(self):
        for event_type in ("charge.failed", "charge.abandoned"):
            self.assertEqual(self.failure_webhook(event_type).status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CANCELLED)
        self.assertEqual(self.booking.payment_status, "FAILED")
        self.release.assert_called_once()

    def test_stale_cancellation_cannot_overwrite_confirmation(self):
        stale = Booking.objects.get(pk=self.booking.pk)
        _confirm_booking_payment(self.booking)
        _fail_booking_payment(stale, "CANCELLED")
        self.assert_unchanged()

    def test_two_stale_cancellations_release_once(self):
        first = Booking.objects.get(pk=self.booking.pk)
        second = Booking.objects.get(pk=self.booking.pk)
        _fail_booking_payment(first, "CANCELLED")
        _fail_booking_payment(second, "FAILED")
        self.assertEqual(second.status, Booking.STATUS_CANCELLED)
        self.assertEqual(second.payment_status, "CANCELLED")
        self.release.assert_called_once()

    def test_stale_failure_does_not_cancel_replaced_checkout(self):
        Booking.objects.filter(pk=self.booking.pk).update(payment_reference="replacement-reference")
        _fail_booking_payment(self.booking, "FAILED")
        self.assertEqual(self.booking.status, Booking.STATUS_PENDING)
        self.assertEqual(self.booking.payment_reference, "replacement-reference")
        self.release.assert_not_called()
