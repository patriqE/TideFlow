from django.urls import path

from core.views import health_check, index

urlpatterns = [
    path("", index, name="index"),
    path("health/", health_check, name="health-check"),
]
