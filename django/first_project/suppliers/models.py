from django.conf import settings
from django.db import models
from django.utils import timezone

class SupplierProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='supplier_profile')
    company_name = models.CharField(max_length=255, blank=True)
    contact_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False, help_text='Admin bật khi supplier đã được kiểm duyệt')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.company_name or self.user.get_username()

class SupplierRequest(models.Model):
    STATUS_OPEN = 'OPEN'
    STATUS_CLAIMED = 'CLAIMED'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Mở'),
        (STATUS_CLAIMED, 'Đã nhận (đang xử lý)'),
        (STATUS_ACCEPTED, 'Đã chấp nhận'),
        (STATUS_REJECTED, 'Bị từ chối'),
        (STATUS_CANCELLED, 'Hủy'),
    ]

    # reference dashboard.Ingredient (ingredient model remains in dashboard app)
    ingredient = models.ForeignKey('dashboard.Ingredient', on_delete=models.CASCADE, related_name='supplier_requests')
    requested_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.TextField(blank=True, help_text='Ghi chú / yêu cầu đặc biệt')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_supplier_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(default=timezone.now)

    # Claim info
    claimed_by = models.ForeignKey(SupplierProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='claimed_requests')
    claimed_at = models.DateTimeField(null=True, blank=True)
    supplier_message = models.TextField(blank=True, help_text='Message supplier gửi khi nhận yêu cầu')

    # Admin decision
    admin_decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='decided_supplier_requests')
    admin_decision_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Request #{self.pk} - {self.ingredient.name} ({self.requested_quantity} {self.ingredient.unit})"