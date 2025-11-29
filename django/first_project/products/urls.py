from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.products, name="list"),
    path("category/<int:category_id>/", views.products_by_category, name="products_by_category"),
    path("<int:pk>/", views.product_detail, name="product_detail"),
]