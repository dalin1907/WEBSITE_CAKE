from django.contrib import admin
from .models import Ingredient, InventoryTransaction

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'quantity', 'min_quantity', 'last_updated', 'is_low_stock')
    search_fields = ('name',)
    list_filter = ('unit',)
    readonly_fields = ('last_updated',)

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('ingredient', 'transaction_type', 'change', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('ingredient__name', 'note')