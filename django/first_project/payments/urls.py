from django.urls import path
from . import views
from .views import momo_return, momo_ipn

app_name = "payments"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("success/<int:order_id>/", views.checkout_success, name="success"),
    path("paypal/return/", views.paypal_return, name="paypal_return"),
    path("paypal/cancel/", views.paypal_cancel, name="paypal_cancel"),
    path("pay-vnpay/<int:order_id>/", views.pay_with_vnpay, name="pay_vnpay"),
    path("vnpay-return/", views.vnpay_return, name="vnpay_return"),
    path('my-orders/', views.customer_order_list, name='customer_order_list'),
    path('my-orders/<int:order_id>/', views.customer_order_detail, name='customer_order_detail'),
    path('track-order/', views.track_order_by_token, name='track_order_by_token'),
    path('process-orders/', views.process_orders, name='process_orders'),  # Danh sách đơn hàng
    path('process-orders/<int:order_id>/', views.process_order_detail, name='process_order_detail'),  # Chi tiết đơn hàng
    path("momo-return/", views.momo_return, name="momo_return"),  # ✅ Sửa đường dẫn
    path("momo-ipn/", views.momo_ipn, name="momo_ipn"),  # ✅ Sửa đường dẫn
]
