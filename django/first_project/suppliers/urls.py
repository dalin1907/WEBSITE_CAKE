from django.urls import path
from . import views

app_name = "suppliers"

urlpatterns = [
    # Supplier views
    path("requests/", views.requests_list, name="requests_list"),
    path("requests/<int:pk>/", views.request_detail, name="request_detail"),
    path("requests/<int:pk>/apply/", views.apply_request, name="apply_request"),
    path("requests/<int:pk>/deliver/", views.supplier_create_delivery, name="supplier_create_delivery"),
    path("claimed/", views.supplier_claimed_list, name="supplier_claimed_list"),
    path("admin/requests/create/",views.admin_order_request_create,name="admin_request_create"),
    # Admin views (staff_member_required)
    path("proposals/", views.proposals_admin_list, name="proposals_admin_list"),
    path("proposal/<int:proposal_id>/", views.proposal_detail_admin, name="proposal_detail_admin"),
    path("proposal/<int:proposal_id>/approve/", views.proposal_approve, name="proposal_approve"),
    path("proposal/<int:proposal_id>/reject/", views.proposal_reject, name="proposal_reject"),
    path("delivery/<int:delivery_id>/confirm/", views.admin_confirm_delivery, name="admin_confirm_delivery"),

    # Supplier registration/profile
    path("register/", views.supplier_register, name="supplier_register"),
]