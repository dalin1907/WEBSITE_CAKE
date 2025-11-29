from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("success/<int:order_id>/", views.checkout_success, name="success"),
    path("paypal/return/", views.paypal_return, name="paypal_return"),
    path("paypal/cancel/", views.paypal_cancel, name="paypal_cancel"),
]
