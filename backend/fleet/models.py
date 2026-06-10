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