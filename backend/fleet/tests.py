import json
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from types import SimpleNamespace

from accounts.auth import create_access_token
from accounts.models import Profile

from .models import BoatRoute, BoatSchedule, Booking, ScheduleCapacity


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


class FakePaystackClient:
    pass


class FakePaystackSession(SimpleNamespace):
    pass


def fake_paystack_session():
    return FakePaystackSession(
        authorization_url="https://paystack.test/authorize",
        access_code="ac_test_123",
        reference="ref_test_123",
    )


def make_completed_event(booking_code):
    return {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "client_reference_id": str(booking_code),
                "metadata": {"booking_code": str(booking_code)},
            }
        },
    }


def make_failed_event(booking_code):
    return {
        "type": "checkout.session.expired",
        "data": {
            "object": {
                "id": "cs_test_123",
                "client_reference_id": str(booking_code),
                "metadata": {"booking_code": str(booking_code)},
            }
        },
    }


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
        self.assertEqual(fake_client.get(f"tideflow:seat-availability:schedule:{schedule.id}:2026-06-11"), "42")

    @patch("fleet.availability.get_redis_client")
    def test_passenger_can_create_pending_booking_and_release_seats_on_cancel(self, mock_get_redis_client):
        fake_client = FakeRedisClient()
        mock_get_redis_client.return_value = fake_client

        passenger = get_user_model().objects.create_user(
            username="passenger-1@example.com",
            email="passenger-1@example.com",
            password="pass12345",
        )
        Profile.objects.create(user=passenger, role=Profile.ROLE_PASSENGER)
        passenger_headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(passenger)}"}

        route = BoatRoute.objects.create(name="Sunset Ferry", origin="Dock A", destination="Dock B")
        schedule = BoatSchedule.objects.create(
            route=route,
            departure_time="18:00:00",
            arrival_time="18:45:00",
            price="25.00",
            days_of_week=["thu"],
        )
        ScheduleCapacity.objects.create(schedule=schedule, max_passengers=10, max_cargo_kg=100)

        booking_response = self.client.post(
            reverse("fleet_booking_collection"),
            data={"schedule_id": schedule.id, "ride_date": "2026-06-11", "seat_count": 3},
            content_type="application/json",
            **passenger_headers,
        )
        self.assertEqual(booking_response.status_code, 201)
        booking_body = booking_response.json()
        self.assertEqual(booking_body["status"], Booking.STATUS_PENDING)
        self.assertEqual(booking_body["available_seats_after_booking"], 7)

        booking_code = booking_body["booking_code"]
        detail_response = self.client.get(reverse("fleet_booking_detail", args=[booking_code]), **passenger_headers)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["status"], Booking.STATUS_PENDING)

        cancel_response = self.client.delete(reverse("fleet_booking_detail", args=[booking_code]), **passenger_headers)
        self.assertEqual(cancel_response.status_code, 200)
        self.assertEqual(cancel_response.json()["status"], Booking.STATUS_CANCELLED)

        rides_response = self.client.get(reverse("fleet_available_rides"), data={"date": "2026-06-11"})
        self.assertEqual(rides_response.status_code, 200)
        self.assertEqual(rides_response.json()["results"][0]["available_seats"], 10)

    @patch("fleet.availability.get_redis_client")
    def test_booking_requires_available_seats(self, mock_get_redis_client):
        fake_client = FakeRedisClient()
        mock_get_redis_client.return_value = fake_client

        passenger = get_user_model().objects.create_user(
            username="passenger-2@example.com",
            email="passenger-2@example.com",
            password="pass12345",
        )
        Profile.objects.create(user=passenger, role=Profile.ROLE_PASSENGER)
        passenger_headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(passenger)}"}

        route = BoatRoute.objects.create(name="Night Ferry", origin="Dock C", destination="Dock D")
        schedule = BoatSchedule.objects.create(
            route=route,
            departure_time="20:00:00",
            arrival_time="20:45:00",
            price="25.00",
            days_of_week=["thu"],
        )
        ScheduleCapacity.objects.create(schedule=schedule, max_passengers=2, max_cargo_kg=100)

        booking_response = self.client.post(
            reverse("fleet_booking_collection"),
            data={"schedule_id": schedule.id, "ride_date": "2026-06-11", "seat_count": 3},
            content_type="application/json",
            **passenger_headers,
        )
        self.assertEqual(booking_response.status_code, 409)

    @patch("fleet.views.create_paystack_session")
    @patch("fleet.availability.get_redis_client")
    def test_passenger_can_initiate_paystack_payment_for_pending_booking(self, mock_get_redis_client, mock_create_paystack_session):
        fake_client = FakeRedisClient()
        mock_get_redis_client.return_value = fake_client
        mock_create_paystack_session.return_value = (fake_paystack_session(), None)

        passenger = get_user_model().objects.create_user(
            username="passenger-3@example.com",
            email="passenger-3@example.com",
            password="pass12345",
        )
        Profile.objects.create(user=passenger, role=Profile.ROLE_PASSENGER)
        passenger_headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(passenger)}"}

        route = BoatRoute.objects.create(name="Harbor Link", origin="Pier West", destination="Pier East")
        schedule = BoatSchedule.objects.create(
            route=route,
            departure_time="09:00:00",
            arrival_time="09:40:00",
            price="30.00",
            days_of_week=["thu"],
        )
        ScheduleCapacity.objects.create(schedule=schedule, max_passengers=5, max_cargo_kg=200)

        booking_response = self.client.post(
            reverse("fleet_booking_collection"),
            data={"schedule_id": schedule.id, "ride_date": "2026-06-11", "seat_count": 2},
            content_type="application/json",
            **passenger_headers,
        )
        booking_code = booking_response.json()["booking_code"]

        payment_response = self.client.post(reverse("fleet_booking_payment", args=[booking_code]), **passenger_headers)
        self.assertEqual(payment_response.status_code, 200)
        body = payment_response.json()
        self.assertEqual(body["payment_status"], "INITIATED")
        self.assertEqual(body["authorization_url"], "https://paystack.test/authorize")
        self.assertEqual(body["access_code"], "ac_test_123")
        self.assertEqual(body["reference"], "ref_test_123")

    @patch("fleet.views.parse_paystack_event")
    @patch("fleet.availability.get_redis_client")
    def test_paystack_webhook_confirms_booking_and_keeps_seats_reserved(self, mock_get_redis_client, mock_parse_webhook_event):
        fake_client = FakeRedisClient()
        mock_get_redis_client.return_value = fake_client

        passenger = get_user_model().objects.create_user(
            username="passenger-4@example.com",
            email="passenger-4@example.com",
            password="pass12345",
        )
        Profile.objects.create(user=passenger, role=Profile.ROLE_PASSENGER)
        passenger_headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(passenger)}"}

        route = BoatRoute.objects.create(name="Sunrise Ferry", origin="Dock X", destination="Dock Y")
        schedule = BoatSchedule.objects.create(
            route=route,
            departure_time="06:00:00",
            arrival_time="06:45:00",
            price="12.00",
            days_of_week=["thu"],
        )
        ScheduleCapacity.objects.create(schedule=schedule, max_passengers=6, max_cargo_kg=100)

        booking_response = self.client.post(
            reverse("fleet_booking_collection"),
            data={"schedule_id": schedule.id, "ride_date": "2026-06-11", "seat_count": 2},
            content_type="application/json",
            **passenger_headers,
        )
        booking_code = booking_response.json()["booking_code"]
        mock_parse_webhook_event.return_value = (
            {
                "event": "charge.success",
                "data": {
                    "object": {
                        "reference": booking_code,
                        "metadata": {"booking_code": booking_code},
                    }
                },
                "type": "charge.success",
                "data": {
                    "object": {
                        "reference": booking_code,
                        "metadata": {"booking_code": booking_code},
                    }
                },
            },
            None,
        )

        webhook_response = self.client.post(
            reverse("fleet_payment_webhook"),
            data=json.dumps({"event": "charge.success"}),
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE="sig_test",
        )
        self.assertEqual(webhook_response.status_code, 200)

        booking = Booking.objects.get(booking_code=booking_code)
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)
        self.assertEqual(booking.payment_status, "SUCCEEDED")

        rides_response = self.client.get(reverse("fleet_available_rides"), data={"date": "2026-06-11"})
        self.assertEqual(rides_response.status_code, 200)
        self.assertEqual(rides_response.json()["results"][0]["available_seats"], 4)

    @patch("fleet.views.parse_paystack_event")
    @patch("fleet.availability.get_redis_client")
    def test_paystack_webhook_failure_releases_seats(self, mock_get_redis_client, mock_parse_webhook_event):
        fake_client = FakeRedisClient()
        mock_get_redis_client.return_value = fake_client

        passenger = get_user_model().objects.create_user(
            username="passenger-5@example.com",
            email="passenger-5@example.com",
            password="pass12345",
        )
        Profile.objects.create(user=passenger, role=Profile.ROLE_PASSENGER)
        passenger_headers = {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(passenger)}"}

        route = BoatRoute.objects.create(name="Evening Ferry", origin="Dock M", destination="Dock N")
        schedule = BoatSchedule.objects.create(
            route=route,
            departure_time="19:00:00",
            arrival_time="19:40:00",
            price="18.00",
            days_of_week=["thu"],
        )
        ScheduleCapacity.objects.create(schedule=schedule, max_passengers=4, max_cargo_kg=100)

        booking_response = self.client.post(
            reverse("fleet_booking_collection"),
            data={"schedule_id": schedule.id, "ride_date": "2026-06-11", "seat_count": 2},
            content_type="application/json",
            **passenger_headers,
        )
        booking_code = booking_response.json()["booking_code"]
        mock_parse_webhook_event.return_value = (
            {
                "event": "charge.abandoned",
                "type": "charge.abandoned",
                "data": {
                    "object": {
                        "reference": booking_code,
                        "metadata": {"booking_code": booking_code},
                    }
                },
            },
            None,
        )

        webhook_response = self.client.post(
            reverse("fleet_payment_webhook"),
            data=json.dumps({"event": "charge.abandoned"}),
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE="sig_test",
        )
        self.assertEqual(webhook_response.status_code, 200)

        booking = Booking.objects.get(booking_code=booking_code)
        self.assertEqual(booking.status, Booking.STATUS_CANCELLED)
        self.assertEqual(booking.payment_status, "ABANDONED")

        rides_response = self.client.get(reverse("fleet_available_rides"), data={"date": "2026-06-11"})
        self.assertEqual(rides_response.status_code, 200)
        self.assertEqual(rides_response.json()["results"][0]["available_seats"], 4)