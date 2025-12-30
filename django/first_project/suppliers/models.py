from django.db import models
from django.conf import settings
from django.utils import timezone

# settings.AUTH_USER_MODEL is a string like "auth.User" or "accounts.User"
User = settings.AUTH_USER_MODEL


class SupplierProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="supplier_profile")
    company_name = models.CharField(max_length=255, blank=True)
    contact_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.company_name or self.user}"


class OrderRequest(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Đang mở – chờ nhà cung cấp báo giá"
        SELECTED = "SELECTED", "Đã chọn nhà cung cấp"
        IN_DELIVERY = "IN_DELIVERY", "Đang giao hàng"
        COMPLETED = "COMPLETED", "Hoàn tất"
        CANCELLED = "CANCELLED", "Đã hủy"

    ingredient = models.ForeignKey(
        "dashboard.Ingredient",
        on_delete=models.CASCADE,
        related_name="order_requests"
    )

    title = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit = models.CharField(max_length=20)

    note = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)



class SupplierProposal(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    # NOTE: set null=True for smooth migration if this field is added to an existing table.
    # Remove null=True later after backfilling if you want it non-nullable.
    order_request = models.ForeignKey(
        OrderRequest,
        on_delete=models.CASCADE,
        related_name="proposals",
        null=True,
        blank=True,
    )
    supplier = models.ForeignKey(User, on_delete=models.PROTECT, related_name="supplier_proposals")
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    message = models.TextField(blank=True)
    offered_quantity = models.PositiveIntegerField(default=1)
    offered_price = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)

    def __str__(self):
        return f"Proposal #{self.pk} for Request #{self.order_request_id}"


class Delivery(models.Model):
    # different related_name to avoid reverse-accessor clash with SupplierProposal.order_request
    order_request = models.ForeignKey(
        OrderRequest,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    supplier = models.ForeignKey(User, on_delete=models.PROTECT, related_name="deliveries")
    tracking_code = models.CharField(max_length=255, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    receipt = models.FileField(upload_to="deliveries/receipts/", null=True, blank=True)
    photo = models.ImageField(upload_to="deliveries/photos/", null=True, blank=True)

    def __str__(self):
        return f"Delivery #{self.pk} for Request #{self.order_request_id}"


class WarehouseReceipt(models.Model):
    order_request = models.ForeignKey(OrderRequest, on_delete=models.CASCADE, related_name="warehouse_receipts")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"WR #{self.pk} for Request #{self.order_request_id}"


class InventoryItem(models.Model):
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit = models.CharField(max_length=50, default="kg")

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"