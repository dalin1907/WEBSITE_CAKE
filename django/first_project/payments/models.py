import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models

class Order(models.Model):
    PAYMENT_CHOICES = [
        ('cod', 'COD'),
        ('vnpay', 'VNPay'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    full_name = models.CharField("Người đặt", max_length=255)
    email = models.EmailField("Email", max_length=254, blank=True, null=True)
    phone = models.CharField("Số điện thoại", max_length=50)
    sender_address = models.TextField("Địa chỉ người gửi", blank=True)
    recipient_address = models.TextField("Địa chỉ người nhận")
    note = models.TextField("Ghi chú", blank=True)
    payment_method = models.CharField("Phương thức thanh toán", max_length=50, choices=PAYMENT_CHOICES, default='cod')
    total_amount = models.DecimalField("Tổng tiền", max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField("Thời gian tạo", auto_now_add=True)
    paid = models.BooleanField("Đã thanh toán", default=False)
    status = models.CharField("Trạng thái", max_length=50, default='pending')  # pending, processing, shipped, delivered, cancelled
    invoice_token = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    paypal_order_id = models.CharField(max_length=255, blank=True, null=True)
    payment_details = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Đơn #{self.id} — {self.full_name} — {self.total_amount}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_id = models.IntegerField("Product ID", null=True, blank=True)
    product_name = models.CharField("Tên sản phẩm", max_length=255)
    price = models.DecimalField("Đơn giá", max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField("Số lượng", default=1)
    subtotal = models.DecimalField("Thành tiền", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Mặt hàng đơn hàng"
        verbose_name_plural = "Mặt hàng đơn hàng"

    def __str__(self):
        return f"{self.product_name} x{self.quantity} (Đơn #{self.order.id})"