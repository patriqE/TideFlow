from django.urls import path

from . import views


urlpatterns = [
    path("rides/", views.available_rides, name="fleet_available_rides"),
    path("bookings/", views.booking_collection, name="fleet_booking_collection"),
    path("bookings/<uuid:booking_code>/", views.booking_detail, name="fleet_booking_detail"),
    path("routes/", views.route_collection, name="fleet_route_collection"),
    path("routes/<int:route_id>/", views.route_detail, name="fleet_route_detail"),
    path("schedules/", views.schedule_collection, name="fleet_schedule_collection"),
    path("schedules/<int:schedule_id>/", views.schedule_detail, name="fleet_schedule_detail"),
    path("capacities/", views.capacity_collection, name="fleet_capacity_collection"),
    path("capacities/<int:capacity_id>/", views.capacity_detail, name="fleet_capacity_detail"),
]