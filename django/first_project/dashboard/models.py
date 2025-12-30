from django.db import models
from django.utils import timezone

class Ingredient(models.Model):
    UNIT_CHOICES = [
        ('kg', 'kg'),
        ('g', 'g'),
        ('l', 'l'),
        ('ml', 'ml'),
        ('pcs', 'cái'),
        ('box', 'hộp'),
    ]

    name = models.CharField(max_length=200, unique=True)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    quantity = models.PositiveIntegerField(default=1)
    min_quantity = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"

    def is_low_stock(self):
        try:
            return self.quantity <= self.min_quantity
        except Exception:
            return False

class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'Nhập kho'),
        ('OUT', 'Xuất kho'),
        ('ADJ', 'Điều chỉnh'),
    ]

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    change = models.PositiveIntegerField(default=1)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} {self.change} {self.ingredient.unit} — {self.ingredient.name}"