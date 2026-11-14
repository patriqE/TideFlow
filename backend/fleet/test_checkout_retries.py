from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.auth import create_access_token
from accounts.models import Profile
from .models import BoatRoute, BoatSchedule, Booking
from .views import _confirm_booking_payment, _fail_booking_payment


@override_settings(REDIS_URL="")
class CheckoutRetryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="retry-user")
        Profile.objects.create(user=self.user)
        route = BoatRoute.objects.create(name="Retry route", origin="A", destination="B")
        schedule = BoatSchedule.objects.create(route=route, departure_time="10:00", arrival_time="11:00")
        self.booking = Booking.objects.create(user=self.user, schedule=schedule, ride_date=date(2026, 12, 1), payment_amount=Decimal("10.00"))
        self.url = f"/fleet/bookings/{self.booking.booking_code}/payment/"
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(self.user)}"}
        self.initialize = self.enterContext(patch("fleet.views.create_paystack_session", side_effect=self.session))
        self.verify = self.enterContext(patch("fleet.views.verify_paystack_transaction", return_value=(None, "Not verified")))

    def session(self, booking):
        return SimpleNamespace(reference=booking.payment_reference, authorization_url="https://checkout.paystack.com/test",
                               access_code="test-access"), None

    def post(self):
        return self.client.post(self.url, **self.headers)

    def test_repeated_posts_return_same_checkout_without_provider_call(self):
        first = self.post()
        second = self.post()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        for key in ("reference", "authorization_url", "access_code"):
            self.assertEqual(first.json()[key], second.json()[key])
        self.initialize.assert_called_once()
        self.assertEqual(first.json()["reference"], f"tf-{self.booking.booking_code.hex}")

    def test_reference_is_persisted_before_provider_request(self):
        def initialize(booking):
            saved = Booking.objects.get(pk=booking.pk)
            self.assertEqual(saved.payment_reference, booking.payment_reference)
            self.assertIsNotNone(saved.checkout_started_at)
            return self.session(booking)
        self.initialize.side_effect = initialize
        self.assertEqual(self.post().status_code, 200)

    def test_overlapping_request_does_not_initialize_again(self):
        def initialize(booking):
            overlapping = self.post()
            self.assertEqual(overlapping.status_code, 409)
            self.assertEqual(overlapping["Retry-After"], "2")
            return self.session(booking)
        self.initialize.side_effect = initialize
        self.assertEqual(self.post().status_code, 200)
        self.initialize.assert_called_once()

    def test_timeout_retry_reuses_reference(self):
        self.initialize.side_effect = None
        self.initialize.return_value = (None, "Provider timeout")
        first = self.post()
        self.assertEqual(first.status_code, 503)
        reference = first.json()["reference"]
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_reference, reference)
        self.assertIsNone(self.booking.checkout_started_at)
        self.initialize.side_effect = self.session
        second = self.post()
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["reference"], reference)

    def test_crash_lease_can_be_reclaimed_without_new_reference(self):
        Booking.objects.filter(pk=self.booking.pk).update(
            payment_reference="previous-reference", checkout_started_at=timezone.now() - timedelta(seconds=61),
        )
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reference"], "previous-reference")

    def test_stale_worker_cannot_overwrite_reclaimed_lease(self):
        def initialize(booking):
            Booking.objects.filter(pk=booking.pk).update(checkout_started_at=timezone.now() + timedelta(seconds=1))
            return self.session(booking)
        self.initialize.side_effect = initialize
        self.assertEqual(self.post().status_code, 409)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_url, "")

    def test_webhook_confirmation_during_initialization_is_not_downgraded(self):
        def initialize(booking):
            _confirm_booking_payment(booking)
            return self.session(booking)
        self.initialize.side_effect = initialize
        self.assertEqual(self.post().status_code, 409)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status, "SUCCEEDED")
        self.assertEqual(self.post().status_code, 200)
        self.initialize.assert_called_once()

    def test_cancellation_during_initialization_preserves_reference_for_late_payment(self):
        def initialize(booking):
            _fail_booking_payment(booking, "CANCELLED")
            return self.session(booking)
        self.initialize.side_effect = initialize
        self.assertEqual(self.post().status_code, 409)
        self.booking.refresh_from_db()
        self.assertTrue(self.booking.payment_reference)
        _confirm_booking_payment(self.booking)
        self.assertEqual(self.booking.status, Booking.STATUS_CANCELLED)
        self.assertEqual(self.booking.payment_status, "REFUND_REQUIRED")

    def test_wrong_provider_reference_cannot_replace_saved_reference(self):
        self.initialize.side_effect = lambda booking: (SimpleNamespace(reference="wrong-reference"), None)
        self.assertEqual(self.post().status_code, 503)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_reference, f"tf-{self.booking.booking_code.hex}")
        self.assertEqual(self.booking.payment_url, "")

    def test_unknown_provider_outcome_does_not_issue_new_reference(self):
        self.initialize.side_effect = None
        self.initialize.return_value = (None, "Reference already exists")
        references = [self.post().json()["reference"] for _ in range(3)]
        self.assertEqual(len(set(references)), 1)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_PENDING)

    def test_retry_reconciles_already_successful_payment(self):
        self.initialize.side_effect = None
        self.initialize.return_value = (None, "Reference already exists")
        self.verify.return_value = ({
            "status": "success", "reference": f"tf-{self.booking.booking_code.hex}", "amount": 1000,
            "currency": "NGN", "metadata": {"booking_code": str(self.booking.booking_code)},
        }, None)
        self.assertEqual(self.post().status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CONFIRMED)

    def test_out_of_order_failure_success_failure_preserves_refund_review(self):
        self.assertEqual(self.post().status_code, 200)
        self.booking.refresh_from_db()
        _fail_booking_payment(self.booking, "FAILED")
        _confirm_booking_payment(self.booking)
        paid_at = self.booking.paid_at
        _fail_booking_payment(self.booking, "ABANDONED")
        _confirm_booking_payment(self.booking)
        self.assertEqual(self.booking.status, Booking.STATUS_CANCELLED)
        self.assertEqual(self.booking.payment_status, "REFUND_REQUIRED")
        self.assertEqual(self.booking.paid_at, paid_at)
