from django.contrib import admin
from .models import (
    SupplierProfile,
    OrderRequest,
    SupplierProposal,
    Delivery,
    WarehouseReceipt,
    InventoryItem,
)


@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name", "contact_email", "phone")
    search_fields = ("user__username", "company_name", "contact_email")


@admin.register(OrderRequest)
class OrderRequestAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "created_by", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "description")


@admin.register(SupplierProposal)
class SupplierProposalAdmin(admin.ModelAdmin):
    list_display = ("pk", "order_request", "supplier", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("supplier__username", "order_request__title")


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ("pk", "order_request", "supplier", "created_at")


@admin.register(WarehouseReceipt)
class WarehouseReceiptAdmin(admin.ModelAdmin):
    list_display = ("pk", "order_request", "created_by", "created_at")


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "quantity", "unit")