from django.urls import include, path

from fleet import views as fleet_views

urlpatterns = [
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("fleet/", include("fleet.urls")),
    path("payment/success/", fleet_views.payment_success, name="payment-success"),
    path("payment/cancel/", fleet_views.payment_cancel, name="payment-cancel"),
]
