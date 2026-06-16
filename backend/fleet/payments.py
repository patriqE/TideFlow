import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


@dataclass
class PaystackSession:
    authorization_url: str
    access_code: str
    reference: str


PAYSTACK_INITIALIZE_URL = "https://api.paystack.co/transaction/initialize"
PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/"


def get_paystack_secret_key():
    return getattr(settings, "PAYSTACK_SECRET_KEY", None) or os.environ.get("PAYSTACK_SECRET_KEY")


def get_paystack_webhook_secret():
    return getattr(settings, "PAYSTACK_WEBHOOK_SECRET", None) or os.environ.get("PAYSTACK_WEBHOOK_SECRET")


def get_public_app_url():
    return getattr(settings, "APP_BASE_URL", None) or os.environ.get("APP_BASE_URL", "http://localhost:8000")


def build_callback_urls(booking):
    base_url = get_public_app_url().rstrip("/")
    success_url = f"{base_url}/payment/success?booking_code={booking.booking_code}"
    cancel_url = f"{base_url}/payment/cancel?booking_code={booking.booking_code}"
    return success_url, cancel_url


def _amount_to_kobo(amount):
    return int((amount or 0) * 100)


def create_paystack_session(booking):
    secret_key = get_paystack_secret_key()
    if not secret_key:
        return None, "Paystack is not configured"

    success_url, cancel_url = build_callback_urls(booking)
    payload = {
        "email": getattr(booking.user, "email", None) or "passenger@tideflow.local",
        "amount": _amount_to_kobo(booking.payment_amount),
        "callback_url": success_url,
        "metadata": {
            "booking_code": str(booking.booking_code),
            "booking_id": str(booking.id),
            "schedule_id": str(booking.schedule_id),
            "ride_date": booking.ride_date.isoformat(),
            "seat_count": str(booking.seat_count),
            "cancel_url": cancel_url,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    request = Request(
        PAYSTACK_INITIALIZE_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return None, "Unable to initialize Paystack payment"

    if not body.get("status"):
        return None, body.get("message") or "Paystack payment failed to initialize"

    response_data = body.get("data") or {}
    return PaystackSession(
        authorization_url=response_data.get("authorization_url", ""),
        access_code=response_data.get("access_code", ""),
        reference=response_data.get("reference", ""),
    ), None


def verify_paystack_transaction(reference):
    secret_key = get_paystack_secret_key()
    if not secret_key:
        return None, "Paystack is not configured"

    request = Request(
        f"{PAYSTACK_VERIFY_URL}{reference}",
        headers={
            "Authorization": f"Bearer {secret_key}",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return None, "Unable to verify Paystack payment"

    if not body.get("status"):
        return None, body.get("message") or "Paystack payment verification failed"

    return body.get("data") or {}, None


def verify_paystack_signature(payload, signature):
    webhook_secret = get_paystack_webhook_secret()
    if not webhook_secret:
        return False

    computed = hmac.new(webhook_secret.encode("utf-8"), payload, hashlib.sha512).hexdigest()
    return hmac.compare_digest(computed, signature or "")


def parse_paystack_event(payload, signature):
    if not verify_paystack_signature(payload, signature):
        return None, "Invalid Paystack webhook signature"

    try:
        event = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "Invalid Paystack webhook payload"

    return event, None
