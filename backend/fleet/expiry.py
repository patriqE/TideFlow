from django.utils import timezone

from .models import Booking


def expire_unpaid_bookings(queryset=None):
    """Idempotently close expired holds without changing recorded payments."""
    if queryset is None:
        queryset = Booking.objects.all()
    now = timezone.now()
    return queryset.filter(
        status=Booking.STATUS_PENDING, expires_at__lte=now, paid_at__isnull=True,
    ).exclude(payment_status="SUCCEEDED").update(
        status=Booking.STATUS_CANCELLED, payment_status="EXPIRED", updated_at=now,
    )


def expire_booking(booking):
    expire_unpaid_bookings(Booking.objects.filter(pk=booking.pk))
    booking.refresh_from_db()
    return booking
