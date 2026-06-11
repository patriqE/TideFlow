from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from accounts.auth import create_access_token
from accounts.models import Profile

from .models import BoatRoute, BoatSchedule, ScheduleCapacity


class FakeRedisClient:
    def __init__(self):
        self.storage = {}

    def ping(self):
        return True

    def set(self, key, value):
        self.storage[key] = str(value)
        return True

    def get(self, key):
        return self.storage.get(key)

    def delete(self, key):
        self.storage.pop(key, None)
        return 1


class FleetCrudTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin_user = User.objects.create_user(username="admin@example.com", email="admin@example.com", password="pass12345")
        Profile.objects.create(user=self.admin_user, role=Profile.ROLE_ADMIN)
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(self.admin_user)}"}

    def test_route_schedule_and_capacity_crud(self):
        route_response = self.client.post(
            reverse("fleet_route_collection"),
            data={"name": "Harbor Loop", "origin": "Pier A", "destination": "Pier B", "description": "Local route"},
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(route_response.status_code, 201)
        route_id = route_response.json()["id"]

        schedule_response = self.client.post(
            reverse("fleet_schedule_collection"),
            data={
                "route_id": route_id,
                "departure_time": "08:30:00",
                "arrival_time": "09:00:00",
                "price": "12.50",
                "days_of_week": ["Mon", "Wed", "Fri"],
            },
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(schedule_response.status_code, 201)
        self.assertEqual(schedule_response.json()["price"], "12.50")
        schedule_id = schedule_response.json()["id"]

        capacity_response = self.client.post(
            reverse("fleet_capacity_collection"),
            data={"schedule_id": schedule_id, "max_passengers": 80, "max_cargo_kg": 1200},
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(capacity_response.status_code, 201)

        list_response = self.client.get(reverse("fleet_capacity_collection"), **self.headers)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()["results"]), 1)

    def test_non_admin_cannot_manage_routes(self):
        User = get_user_model()
        user = User.objects.create_user(username="passenger@example.com", email="passenger@example.com", password="pass12345")
        Profile.objects.create(user=user, role=Profile.ROLE_PASSENGER)
        headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(user)}"}

        response = self.client.get(reverse("fleet_route_collection"), **headers)
        self.assertEqual(response.status_code, 403)

    def test_available_rides_filters_by_date_and_time(self):
        route = BoatRoute.objects.create(name="Harbor Express", origin="Dock 1", destination="Dock 9")
        BoatSchedule.objects.create(
            route=route,
            departure_time="08:00:00",
            arrival_time="08:45:00",
            price="15.00",
            days_of_week=["thu", "sat"],
        )
        BoatSchedule.objects.create(
            route=route,
            departure_time="10:30:00",
            arrival_time="11:15:00",
            price="18.00",
            days_of_week=["thu", "sat"],
        )
        BoatSchedule.objects.create(
            route=route,
            departure_time="13:00:00",
            arrival_time="13:45:00",
            price="21.00",
            days_of_week=["mon"],
        )

        response = self.client.get(reverse("fleet_available_rides"), data={"date": "2026-06-11", "time": "09:00:00"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["date"], "2026-06-11")
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["departure_time"], "10:30:00")
        self.assertEqual(body["results"][0]["price"], "18.00")

    @patch("fleet.availability.get_redis_client")
    def test_available_rides_uses_redis_seat_availability(self, mock_get_redis_client):
        fake_client = FakeRedisClient()
        mock_get_redis_client.return_value = fake_client

        route = BoatRoute.objects.create(name="Bay Shuttle", origin="Harbor", destination="Island")
        schedule = BoatSchedule.objects.create(
            route=route,
            departure_time="07:15:00",
            arrival_time="07:45:00",
            price="9.50",
            days_of_week=["thu"],
        )
        ScheduleCapacity.objects.create(schedule=schedule, max_passengers=42, max_cargo_kg=500)

        response = self.client.get(reverse("fleet_available_rides"), data={"date": "2026-06-11"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["available_seats"], 42)
        self.assertEqual(fake_client.get("tideflow:seat-availability:schedule:1"), "42")