from django.urls import path
from .views import (
    InventoryListView,
    IngredientUpdateView,
    IngredientCreateView,
    InventoryTransactionCreateView,
)
from . import views

urlpatterns = [
    path('order-statistics/', views.order_statistics, name='order_statistics'),

    # Inventory management (class-based)
    path('inventory/', InventoryListView.as_view(), name='inventory_list'),
    path('inventory/add/', IngredientCreateView.as_view(), name='add_ingredient'),
    path('inventory/<int:pk>/', IngredientUpdateView.as_view(), name='ingredient_detail'),
    path('inventory/<int:pk>/transaction/', InventoryTransactionCreateView.as_view(), name='add_transaction'),
]