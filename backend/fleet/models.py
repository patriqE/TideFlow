import uuid

from django.conf import settings
from django.db import models


class BoatRoute(models.Model):
    name = models.CharField(max_length=120, unique=True)
    origin = models.CharField(max_length=120)
    destination = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.origin} -> {self.destination})"


class BoatSchedule(models.Model):
    route = models.ForeignKey(BoatRoute, on_delete=models.CASCADE, related_name="schedules")
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    days_of_week = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.route.name} @ {self.departure_time}"


class ScheduleCapacity(models.Model):
    schedule = models.OneToOneField(BoatSchedule, on_delete=models.CASCADE, related_name="capacity")
    max_passengers = models.PositiveIntegerField()
    max_cargo_kg = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Capacity for schedule {self.schedule_id}: {self.max_passengers} passengers"


class Booking(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    booking_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    schedule = models.ForeignKey(BoatSchedule, on_delete=models.CASCADE, related_name="bookings")
    ride_date = models.DateField()
    seat_count = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Booking {self.booking_code} ({self.status})"