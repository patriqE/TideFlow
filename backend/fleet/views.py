import json
from functools import wraps
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_time
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Profile

from .availability import (
    clear_schedule_availability,
    get_schedule_available_seats,
    release_schedule_seats,
    reserve_schedule_seats,
    seed_schedule_availability,
)
from .models import BoatRoute, BoatSchedule, Booking, ScheduleCapacity


def _is_admin_user(user):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    try:
        return getattr(user, "profile").role == Profile.ROLE_ADMIN
    except Exception:
        return False


def admin_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return JsonResponse({"detail": "Authentication required"}, status=401)
        if not _is_admin_user(request.user):
            return JsonResponse({"detail": "Admin privileges required"}, status=403)
        return view_func(request, *args, **kwargs)

    return wrapper


def _read_json(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode())
    except Exception:
        return None


def _parse_days_of_week(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return None


def _parse_time_value(value, field_name):
    if value is None:
        return None, f"Provide {field_name}"
    parsed_value = parse_time(value) if isinstance(value, str) else value
    if parsed_value is None:
        return None, f"{field_name} must be a valid time"
    return parsed_value, None


def _parse_date_value(value):
    if not value:
        return None, "Provide date"
    try:
        return datetime.strptime(value, "%Y-%m-%d").date(), None
    except ValueError:
        return None, "date must be in YYYY-MM-DD format"


def _parse_integer_value(value, field_name, minimum=1):
    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        return None, f"{field_name} must be a whole number"

    if parsed_value < minimum:
        return None, f"{field_name} must be at least {minimum}"
    return parsed_value, None


def _parse_decimal_value(value, field_name, default=None):
    if value is None:
        return default, None
    try:
        return Decimal(str(value)), None
    except (InvalidOperation, ValueError, TypeError):
        return None, f"{field_name} must be a valid number"


def _route_payload(route):
    return {
        "id": route.id,
        "name": route.name,
        "origin": route.origin,
        "destination": route.destination,
        "description": route.description,
        "is_active": route.is_active,
        "created_at": route.created_at.isoformat(),
        "updated_at": route.updated_at.isoformat(),
    }


def _capacity_payload(capacity):
    if not capacity:
        return None
    return {
        "id": capacity.id,
        "schedule_id": capacity.schedule_id,
        "max_passengers": capacity.max_passengers,
        "max_cargo_kg": capacity.max_cargo_kg,
        "notes": capacity.notes,
        "created_at": capacity.created_at.isoformat(),
        "updated_at": capacity.updated_at.isoformat(),
    }


def _schedule_payload(schedule, ride_date=None):
    capacity = getattr(schedule, "capacity", None)
    available_seats = get_schedule_available_seats(schedule, ride_date)
    return {
        "id": schedule.id,
        "route": _route_payload(schedule.route),
        "route_id": schedule.route_id,
        "departure_time": schedule.departure_time.isoformat(),
        "arrival_time": schedule.arrival_time.isoformat(),
        "price": str(schedule.price),
        "days_of_week": schedule.days_of_week,
        "is_active": schedule.is_active,
        "available_seats": available_seats,
        "capacity": _capacity_payload(capacity) if capacity else None,
        "created_at": schedule.created_at.isoformat(),
        "updated_at": schedule.updated_at.isoformat(),
    }


def _booking_payload(booking):
    return {
        "booking_code": str(booking.booking_code),
        "id": booking.id,
        "user_id": booking.user_id,
        "schedule": _schedule_payload(booking.schedule, booking.ride_date),
        "schedule_id": booking.schedule_id,
        "ride_date": booking.ride_date.isoformat(),
        "seat_count": booking.seat_count,
        "status": booking.status,
        "created_at": booking.created_at.isoformat(),
        "updated_at": booking.updated_at.isoformat(),
    }


def _passenger_ride_payload(schedule, ride_date):
    payload = _schedule_payload(schedule, ride_date)
    payload.update(
        {
            "ride_date": ride_date.isoformat(),
            "weekday": ride_date.strftime("%a"),
        }
    )
    return payload


def _schedule_matches_date(schedule, ride_date):
    weekday_short = ride_date.strftime("%a")
    weekday_long = ride_date.strftime("%A")
    normalized_days = {str(day).strip().lower() for day in schedule.days_of_week}
    return weekday_short.lower() in normalized_days or weekday_long.lower() in normalized_days


def _is_passenger_user(user):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return False
    try:
        return getattr(user, "profile").role == Profile.ROLE_PASSENGER
    except Exception:
        return False


def passenger_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
            return JsonResponse({"detail": "Authentication required"}, status=401)
        if not _is_passenger_user(request.user):
            return JsonResponse({"detail": "Passenger privileges required"}, status=403)
        return view_func(request, *args, **kwargs)

    return wrapper


@csrf_exempt
@admin_only
def route_collection(request):
    if request.method == "GET":
        routes = BoatRoute.objects.order_by("name")
        return JsonResponse({"results": [_route_payload(route) for route in routes]}, status=200)

    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    data = _read_json(request)
    if data is None:
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

    name = (data.get("name") or "").strip()
    origin = (data.get("origin") or "").strip()
    destination = (data.get("destination") or "").strip()
    description = (data.get("description") or "").strip()
    is_active = data.get("is_active", True)

    if not name or not origin or not destination:
        return JsonResponse({"detail": "Provide name, origin, and destination"}, status=400)

    try:
        route = BoatRoute.objects.create(
            name=name,
            origin=origin,
            destination=destination,
            description=description,
            is_active=bool(is_active),
        )
    except IntegrityError:
        return JsonResponse({"detail": "A route with that name already exists"}, status=400)
    return JsonResponse(_route_payload(route), status=201)


@csrf_exempt
@admin_only
def route_detail(request, route_id):
    route = get_object_or_404(BoatRoute, id=route_id)

    if request.method == "GET":
        return JsonResponse(_route_payload(route), status=200)

    if request.method in {"PUT", "PATCH"}:
        data = _read_json(request)
        if data is None:
            return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

        if "name" in data:
            name = (data.get("name") or "").strip()
            if not name:
                return JsonResponse({"detail": "Name cannot be blank"}, status=400)
            route.name = name
        if "origin" in data:
            origin = (data.get("origin") or "").strip()
            if not origin:
                return JsonResponse({"detail": "Origin cannot be blank"}, status=400)
            route.origin = origin
        if "destination" in data:
            destination = (data.get("destination") or "").strip()
            if not destination:
                return JsonResponse({"detail": "Destination cannot be blank"}, status=400)
            route.destination = destination
        if "description" in data:
            route.description = (data.get("description") or "").strip()
        if "is_active" in data:
            route.is_active = bool(data.get("is_active"))

        try:
            route.save()
        except IntegrityError:
            return JsonResponse({"detail": "A route with that name already exists"}, status=400)
        return JsonResponse(_route_payload(route), status=200)

    if request.method == "DELETE":
        route.delete()
        return JsonResponse({"detail": "Route deleted"}, status=200)

    return JsonResponse({"detail": "Method not allowed"}, status=405)


@csrf_exempt
@admin_only
def schedule_collection(request):
    if request.method == "GET":
        schedules = BoatSchedule.objects.select_related("route", "capacity").order_by("route__name", "departure_time")
        return JsonResponse({"results": [_schedule_payload(schedule) for schedule in schedules]}, status=200)

    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    data = _read_json(request)
    if data is None:
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

    route_id = data.get("route_id")
    departure_time, departure_error = _parse_time_value(data.get("departure_time"), "departure_time")
    arrival_time, arrival_error = _parse_time_value(data.get("arrival_time"), "arrival_time")
    price, price_error = _parse_decimal_value(data.get("price"), "price", Decimal("0.00"))
    days_of_week = _parse_days_of_week(data.get("days_of_week"))
    is_active = data.get("is_active", True)

    if not route_id or days_of_week is None:
        return JsonResponse({"detail": "Provide route_id, departure_time, arrival_time, days_of_week, and price"}, status=400)
    if departure_error:
        return JsonResponse({"detail": departure_error}, status=400)
    if arrival_error:
        return JsonResponse({"detail": arrival_error}, status=400)
    if price_error:
        return JsonResponse({"detail": price_error}, status=400)

    route = get_object_or_404(BoatRoute, id=route_id)
    schedule = BoatSchedule.objects.create(
        route=route,
        departure_time=departure_time,
        arrival_time=arrival_time,
        price=price,
        days_of_week=days_of_week,
        is_active=bool(is_active),
    )
    return JsonResponse(_schedule_payload(schedule), status=201)


@csrf_exempt
@admin_only
def schedule_detail(request, schedule_id):
    schedule = get_object_or_404(BoatSchedule.objects.select_related("route", "capacity"), id=schedule_id)

    if request.method == "GET":
        return JsonResponse(_schedule_payload(schedule), status=200)

    if request.method in {"PUT", "PATCH"}:
        data = _read_json(request)
        if data is None:
            return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

        if "route_id" in data:
            schedule.route = get_object_or_404(BoatRoute, id=data.get("route_id"))
        if "departure_time" in data:
            parsed_departure_time, error = _parse_time_value(data.get("departure_time"), "departure_time")
            if error:
                return JsonResponse({"detail": error}, status=400)
            schedule.departure_time = parsed_departure_time
        if "arrival_time" in data:
            parsed_arrival_time, error = _parse_time_value(data.get("arrival_time"), "arrival_time")
            if error:
                return JsonResponse({"detail": error}, status=400)
            schedule.arrival_time = parsed_arrival_time
        if "price" in data:
            parsed_price, error = _parse_decimal_value(data.get("price"), "price")
            if error:
                return JsonResponse({"detail": error}, status=400)
            schedule.price = parsed_price
        if "days_of_week" in data:
            parsed_days = _parse_days_of_week(data.get("days_of_week"))
            if parsed_days is None:
                return JsonResponse({"detail": "days_of_week must be a list or comma-separated string"}, status=400)
            schedule.days_of_week = parsed_days
        if "is_active" in data:
            schedule.is_active = bool(data.get("is_active"))

        schedule.save()
        return JsonResponse(_schedule_payload(schedule), status=200)

    if request.method == "DELETE":
        clear_schedule_availability(schedule.id)
        schedule.delete()
        return JsonResponse({"detail": "Schedule deleted"}, status=200)

    return JsonResponse({"detail": "Method not allowed"}, status=405)


@csrf_exempt
def available_rides(request):
    if request.method != "GET":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    ride_date, date_error = _parse_date_value(request.GET.get("date"))
    if date_error:
        return JsonResponse({"detail": date_error}, status=400)

    requested_time = request.GET.get("time")
    parsed_time = None
    if requested_time:
        parsed_time, time_error = _parse_time_value(requested_time, "time")
        if time_error:
            return JsonResponse({"detail": time_error}, status=400)

    rides = (
        BoatSchedule.objects.select_related("route", "capacity")
        .filter(is_active=True, route__is_active=True)
        .order_by("departure_time", "route__name")
    )

    matching_rides = []
    for ride in rides:
        if not _schedule_matches_date(ride, ride_date):
            continue
        if parsed_time and ride.departure_time < parsed_time:
            continue
        matching_rides.append(_passenger_ride_payload(ride, ride_date))

    return JsonResponse({"date": ride_date.isoformat(), "results": matching_rides}, status=200)


@csrf_exempt
@passenger_only
def booking_collection(request):
    if request.method == "GET":
        bookings = Booking.objects.select_related("schedule", "schedule__route").filter(user=request.user).order_by("-created_at")
        return JsonResponse({"results": [_booking_payload(booking) for booking in bookings]}, status=200)

    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    data = _read_json(request)
    if data is None:
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

    schedule_id = data.get("schedule_id")
    ride_date, date_error = _parse_date_value(data.get("ride_date"))
    seat_count, seat_count_error = _parse_integer_value(data.get("seat_count", 1), "seat_count")

    if not schedule_id:
        return JsonResponse({"detail": "Provide schedule_id"}, status=400)
    if date_error:
        return JsonResponse({"detail": date_error}, status=400)
    if seat_count_error:
        return JsonResponse({"detail": seat_count_error}, status=400)

    schedule = get_object_or_404(BoatSchedule.objects.select_related("route", "capacity"), id=schedule_id, is_active=True, route__is_active=True)
    if not _schedule_matches_date(schedule, ride_date):
        return JsonResponse({"detail": "Selected ride does not operate on that date"}, status=400)

    reserved_seats = reserve_schedule_seats(schedule, ride_date, seat_count)
    if reserved_seats is None:
        if getattr(schedule, "capacity", None) is None:
            return JsonResponse({"detail": "Seat availability is unavailable for this ride"}, status=503)
        return JsonResponse({"detail": "Not enough seats available"}, status=409)

    try:
        with transaction.atomic():
            booking = Booking.objects.create(
                user=request.user,
                schedule=schedule,
                ride_date=ride_date,
                seat_count=seat_count,
                status=Booking.STATUS_PENDING,
            )
    except Exception:
        release_schedule_seats(schedule, ride_date, seat_count)
        raise

    payload = _booking_payload(booking)
    payload["available_seats_after_booking"] = reserved_seats
    return JsonResponse(payload, status=201)


@csrf_exempt
@passenger_only
def booking_detail(request, booking_code):
    booking = get_object_or_404(Booking.objects.select_related("schedule", "schedule__route"), booking_code=booking_code, user=request.user)

    if request.method == "GET":
        return JsonResponse(_booking_payload(booking), status=200)

    if request.method == "DELETE":
        if booking.status == Booking.STATUS_CANCELLED:
            return JsonResponse(_booking_payload(booking), status=200)

        release_schedule_seats(booking.schedule, booking.ride_date, booking.seat_count)
        booking.status = Booking.STATUS_CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        return JsonResponse(_booking_payload(booking), status=200)

    return JsonResponse({"detail": "Method not allowed"}, status=405)


@csrf_exempt
@admin_only
def capacity_collection(request):
    if request.method == "GET":
        capacities = ScheduleCapacity.objects.select_related("schedule", "schedule__route").order_by(
            "schedule__route__name",
            "schedule__departure_time",
        )
        return JsonResponse({"results": [_capacity_payload(capacity) for capacity in capacities]}, status=200)

    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    data = _read_json(request)
    if data is None:
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

    schedule_id = data.get("schedule_id")
    max_passengers = data.get("max_passengers")
    max_cargo_kg = data.get("max_cargo_kg", 0)
    notes = (data.get("notes") or "").strip()

    if not schedule_id or max_passengers is None:
        return JsonResponse({"detail": "Provide schedule_id and max_passengers"}, status=400)

    schedule = get_object_or_404(BoatSchedule, id=schedule_id)
    try:
        capacity = ScheduleCapacity.objects.create(
            schedule=schedule,
            max_passengers=max_passengers,
            max_cargo_kg=max_cargo_kg,
            notes=notes,
        )
    except IntegrityError:
        return JsonResponse({"detail": "That schedule already has capacity configured"}, status=400)

    seed_schedule_availability(schedule)
    return JsonResponse(_capacity_payload(capacity), status=201)


@csrf_exempt
@admin_only
def capacity_detail(request, capacity_id):
    capacity = get_object_or_404(ScheduleCapacity.objects.select_related("schedule", "schedule__route"), id=capacity_id)

    if request.method == "GET":
        return JsonResponse(_capacity_payload(capacity), status=200)

    if request.method in {"PUT", "PATCH"}:
        data = _read_json(request)
        if data is None:
            return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

        if "schedule_id" in data:
            capacity.schedule = get_object_or_404(BoatSchedule, id=data.get("schedule_id"))
        if "max_passengers" in data:
            capacity.max_passengers = data.get("max_passengers")
        if "max_cargo_kg" in data:
            capacity.max_cargo_kg = data.get("max_cargo_kg")
        if "notes" in data:
            capacity.notes = (data.get("notes") or "").strip()

        try:
            capacity.save()
        except IntegrityError:
            return JsonResponse({"detail": "That schedule already has capacity configured"}, status=400)

        seed_schedule_availability(capacity.schedule)
        return JsonResponse(_capacity_payload(capacity), status=200)

    if request.method == "DELETE":
        clear_schedule_availability(capacity.schedule_id)
        capacity.delete()
        return JsonResponse({"detail": "Capacity deleted"}, status=200)

    return JsonResponse({"detail": "Method not allowed"}, status=405)