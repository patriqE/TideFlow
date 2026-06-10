from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.auth import create_access_token
from accounts.models import Profile


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
                "days_of_week": ["Mon", "Wed", "Fri"],
            },
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(schedule_response.status_code, 201)
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