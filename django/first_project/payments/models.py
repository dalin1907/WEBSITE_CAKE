import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models

class Order(models.Model):
    # Lựa chọn trạng thái thanh toán
    PAYMENT_CHOICES = [
        ('cod', 'COD'),
        ('vnpay', 'VNPay'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('momo', 'MoMo'),
    ]

    # Lựa chọn trạng thái đơn hàng
    STATUS_CHOICES = [
        ('pending', 'Đang xử lý'),
        ('processing', 'Đang chuẩn bị'),
        ('shipping', 'Đang vận chuyển'),
        ('delivered', 'Đã giao hàng'),
        ('cancelled', 'Đã hủy'),
    ]

    # Các trường trong model Order
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    full_name = models.CharField("Người đặt", max_length=255)
    email = models.EmailField("Email", max_length=254, blank=True, null=True)
    phone = models.CharField("Số điện thoại", max_length=50)
    recipient_address = models.CharField("Địa chỉ người nhận", max_length=500)
    note = models.TextField("Ghi chú", blank=True)
    payment_method = models.CharField("Phương thức thanh toán", max_length=50, choices=PAYMENT_CHOICES, default='cod')
    total_amount = models.DecimalField("Tổng tiền", max_digits=12, decimal_places=3, default=Decimal('0'))
    created_at = models.DateTimeField("Thời gian tạo", auto_now_add=True)
    paid = models.BooleanField("Đã thanh toán", default=False)
    status = models.CharField("Trạng thái", max_length=50, choices=STATUS_CHOICES, default='pending')  # Thêm lựa chọn trạng thái
    invoice_token = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    paypal_order_id = models.CharField(max_length=255, blank=True, null=True)
    payment_details = models.JSONField(blank=True, null=True)  # Lưu thông tin chi tiết thanh toán
    momo_order_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']  # Sắp xếp theo thời gian tạo, mới nhất lên đầu
        verbose_name = "Order"  # Tên hiển thị trong admin
        verbose_name_plural = "Orders"

    def __str__(self):
        # Tùy chỉnh chuỗi đại diện cho Order
        return f"Đơn #{self.id} — {self.full_name} — {self.total_amount}"

    # Method để kiểm tra tình trạng thanh toán
    def is_paid(self):
        return self.paid

    # Tính tổng số lượng sản phẩm từ OrderItem
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name='items', on_delete=models.CASCADE
    )  # 1 Order có nhiều OrderItem, liên kết qua khóa ngoại
    product_id = models.IntegerField("Product ID", null=True, blank=True)
    product_name = models.CharField("Tên sản phẩm", max_length=255)
    price = models.DecimalField("Đơn giá", max_digits=12, decimal_places=3)
    quantity = models.PositiveIntegerField("Số lượng", default=1)
    subtotal = models.DecimalField("Thành tiền", max_digits=12, decimal_places=3)

    class Meta:
        verbose_name = "Mặt hàng đơn hàng"
        verbose_name_plural = "Mặt hàng đơn hàng"

    def __str__(self):
        return f"{self.product_name} x{self.quantity} (Đơn #{self.order.id})"

    # Tính tổng số tiền cho mỗi OrderItem
    def calculate_subtotal(self):
        return self.price * self.quantity