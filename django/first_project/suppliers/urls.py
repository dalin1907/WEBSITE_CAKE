from django.urls import path
from .views import (
    SupplierRequestCreateView,
    SupplierRequestListView,
    SupplierRequestDetailView,
    SupplierClaimView,
    SupplierProfileCreateView,
    supplier_register_view,
    supplier_claimed_list,
    AdminAcceptSupplierRequestView,
    AdminRejectSupplierRequestView,
    supplier_complete_request,
)

app_name = "suppliers"

urlpatterns = [
    # Hồ sơ nhà cung cấp
    path('register/', supplier_register_view, name='supplier_register'),
    path('profile/create/', SupplierProfileCreateView.as_view(), name='supplier_profile_create'),

    # Request
    path('requests/', SupplierRequestListView.as_view(), name='supplier_request_list'),
    path('requests/create/', SupplierRequestCreateView.as_view(), name='supplier_request_create'),
    path('requests/<int:pk>/', SupplierRequestDetailView.as_view(), name='supplier_request_detail'),

    # Supplier nhận yêu cầu
    path('requests/<int:pk>/claim/', SupplierClaimView.as_view(), name='supplier_request_claim'),

    # Supplier đánh dấu hoàn thành
    path('requests/<int:pk>/complete/', supplier_complete_request, name='supplier_request_complete'),

    # Admin xem yêu cầu đã được nhận
    path('requests/claimed/', supplier_claimed_list, name='supplier_claimed_list'),

    # Admin duyệt / từ chối
    path('requests/<int:pk>/accept/', AdminAcceptSupplierRequestView.as_view(), name='supplier_request_accept'),
    path('requests/<int:pk>/reject/', AdminRejectSupplierRequestView.as_view(), name='supplier_request_reject'),
]
