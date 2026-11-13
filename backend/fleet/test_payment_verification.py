import hashlib
import hmac
import json
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import BoatRoute, BoatSchedule, Booking
from .payments import create_paystack_session


@override_settings(PAYSTACK_WEBHOOK_SECRET="test-only-webhook-secret")
class PaymentVerificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model().objects.create_user(username="payment-test", email="payer@example.com")
        route = BoatRoute.objects.create(name="Test route", origin="A", destination="B")
        schedule = BoatSchedule.objects.create(route=route, departure_time="10:00", arrival_time="11:00")
        cls.booking = Booking.objects.create(
            user=user, schedule=schedule, ride_date=date(2026, 12, 1),
            payment_amount=Decimal("25.50"), payment_currency="ngn",
            payment_reference="expected-reference", payment_status="INITIATED",
        )

    def evidence(self):
        return {
            "status": "success", "reference": self.booking.payment_reference,
            "amount": 2550, "currency": "NGN",
            "metadata": {"booking_code": str(self.booking.booking_code)},
        }

    def callback(self, evidence, reference="expected-reference"):
        with patch("fleet.views.verify_paystack_transaction", return_value=(evidence, None)):
            return self.client.get(reverse("payment-success"), {
                "booking_code": str(self.booking.booking_code), "reference": reference,
            })

    def webhook(self, event, signature=None):
        body = json.dumps(event).encode()
        if signature is None:
            signature = hmac.new(b"test-only-webhook-secret", body, hashlib.sha512).hexdigest()
        return self.client.post(
            reverse("fleet_payment_webhook"), body, content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE=signature,
        )

    def assert_pending(self):
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_PENDING)
        self.assertEqual(self.booking.payment_status, "INITIATED")
        self.assertEqual(self.booking.payment_reference, "expected-reference")
        self.assertIsNone(self.booking.paid_at)

    def invalid_evidence(self):
        for field, values in {
            "status": ["failed", None], "reference": ["unrelated-reference", None],
            "amount": [1, 2551, "2550", 2550.0, True, None],
            "currency": ["USD", None, []],
            "metadata": [None, "", [], {}, {"booking_code": str(uuid4())}],
        }.items():
            for value in values:
                data = self.evidence()
                data[field] = value
                yield data
            data = self.evidence()
            del data[field]
            yield data

    def test_callback_rejects_missing_and_mismatched_payment_details(self):
        for data in self.invalid_evidence():
            with self.subTest(data=data):
                self.assertEqual(self.callback(data).status_code, 400)
                self.assert_pending()

    def test_signed_webhook_rejects_missing_and_mismatched_payment_details(self):
        for data in self.invalid_evidence():
            with self.subTest(data=data):
                response = self.webhook({"event": "charge.success", "data": data})
                self.assertIn(response.status_code, (400, 404))
                self.assert_pending()

    def test_callback_rejects_foreign_reference_before_contacting_provider(self):
        with patch("fleet.views.verify_paystack_transaction") as verify:
            response = self.client.get(reverse("payment-success"), {
                "booking_code": str(self.booking.booking_code), "reference": "foreign-reference",
            })
        self.assertEqual(response.status_code, 400)
        verify.assert_not_called()
        self.assert_pending()

    def test_checkout_must_have_a_recorded_reference(self):
        Booking.objects.filter(pk=self.booking.pk).update(payment_reference=None)
        self.assertEqual(self.callback(self.evidence()).status_code, 400)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_PENDING)

    def test_callback_and_webhook_replays_preserve_paid_timestamp(self):
        data = self.evidence()
        self.assertEqual(self.callback(data).status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CONFIRMED)
        self.assertEqual(self.booking.payment_status, "SUCCEEDED")
        paid_at = self.booking.paid_at
        self.assertIsNotNone(paid_at)
        for _ in range(2):
            self.assertEqual(self.webhook({"event": "charge.success", "data": data}).status_code, 200)
            self.assertEqual(self.callback(data).status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.paid_at, paid_at)

    def test_valid_signed_webhook_confirms_pending_booking(self):
        self.assertEqual(self.webhook({"event": "charge.success", "data": self.evidence()}).status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CONFIRMED)
        self.assertEqual(self.booking.payment_status, "SUCCEEDED")

    def test_bad_signature_cannot_confirm_booking(self):
        response = self.webhook({"event": "charge.success", "data": self.evidence()}, signature="invalid")
        self.assertEqual(response.status_code, 400)
        self.assert_pending()

    def test_malformed_signed_payloads_do_not_crash(self):
        for event in ([], None, {"event": "charge.success", "data": None},
                      {"event": "charge.success", "data": []}):
            with self.subTest(event=event):
                self.assertEqual(self.webhook(event).status_code, 400)
                self.assert_pending()

    def test_unrelated_event_is_ignored_without_booking_metadata(self):
        self.assertEqual(self.webhook({"event": "transfer.success", "data": {}}).status_code, 200)
        self.assert_pending()

    def test_provider_verification_failure_does_not_confirm_booking(self):
        with patch("fleet.views.verify_paystack_transaction", return_value=(None, "Provider unavailable")):
            response = self.client.get(reverse("payment-success"), {"booking_code": str(self.booking.booking_code)})
        self.assertEqual(response.status_code, 400)
        self.assert_pending()

    def test_callback_without_reference_verifies_stored_reference(self):
        with patch("fleet.views.verify_paystack_transaction", return_value=(self.evidence(), None)) as verify:
            response = self.client.get(reverse("payment-success"), {"booking_code": str(self.booking.booking_code)})
        self.assertEqual(response.status_code, 200)
        verify.assert_called_once_with("expected-reference")

    def test_changed_checkout_during_verification_is_not_confirmed(self):
        def verify(reference):
            Booking.objects.filter(pk=self.booking.pk).update(payment_reference="new-checkout")
            return self.evidence(), None

        with patch("fleet.views.verify_paystack_transaction", side_effect=verify):
            response = self.client.get(reverse("payment-success"), {"booking_code": str(self.booking.booking_code)})
        self.assertEqual(response.status_code, 409)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_PENDING)
        self.assertEqual(self.booking.payment_reference, "new-checkout")

    def test_cancelled_booking_cannot_be_reconfirmed(self):
        Booking.objects.filter(pk=self.booking.pk).update(status=Booking.STATUS_CANCELLED)
        self.assertEqual(self.callback(self.evidence()).status_code, 409)
        self.assertEqual(self.webhook({"event": "charge.success", "data": self.evidence()}).status_code, 200)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CANCELLED)
        self.assertEqual(self.booking.payment_status, "REFUND_REQUIRED")
        self.assertIsNotNone(self.booking.paid_at)

    def test_cancellation_during_provider_verification_is_not_overwritten(self):
        def verify(reference):
            Booking.objects.filter(pk=self.booking.pk).update(status=Booking.STATUS_CANCELLED)
            return self.evidence(), None

        with patch("fleet.views.verify_paystack_transaction", side_effect=verify):
            response = self.client.get(reverse("payment-success"), {
                "booking_code": str(self.booking.booking_code), "reference": "expected-reference",
            })
        self.assertEqual(response.status_code, 409)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CANCELLED)

    def test_transaction_for_another_booking_cannot_be_reassigned(self):
        other = Booking.objects.create(
            user=self.booking.user, schedule=self.booking.schedule, ride_date="2026-12-01",
            payment_amount=Decimal("25.50"), payment_reference="other-reference",
        )
        data = self.evidence()
        data["reference"] = other.payment_reference
        self.assertEqual(self.callback(data).status_code, 400)
        self.assertEqual(self.webhook({"event": "charge.success", "data": data}).status_code, 400)
        self.assert_pending()
        other.refresh_from_db()
        self.assertEqual(other.status, Booking.STATUS_PENDING)

    @override_settings(PAYSTACK_SECRET_KEY="test-only-provider-secret")
    def test_initialization_sends_booking_currency_amount_and_metadata(self):
        with patch("fleet.payments.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = json.dumps({
                "status": True, "data": {"authorization_url": "https://checkout.paystack.com/test",
                "access_code": "test-access", "reference": "test-reference"},
            }).encode()
            session, error = create_paystack_session(self.booking)
        self.assertIsNone(error)
        payload = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(payload["amount"], 2550)
        self.assertEqual(payload["currency"], "NGN")
        self.assertEqual(payload["metadata"]["booking_code"], str(self.booking.booking_code))
