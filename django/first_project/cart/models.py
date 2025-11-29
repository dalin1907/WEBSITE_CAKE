from decimal import Decimal
from django.conf import settings
from django.db import models

# Cart & CartItem live in cart app. Product referenced from products app.
class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Giỏ hàng của {self.user.username}" if self.user else "Giỏ hàng ẩn danh"

    def total_amount(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.subtotal()
        return total

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE, null=True, blank=True)
    # nếu bạn dùng session-based cart, bạn có thể giữ user=None và lưu session_key khác
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

    def subtotal(self):
        return self.product.price * self.quantity