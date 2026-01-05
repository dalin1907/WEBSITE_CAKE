from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.products, name="list"),
    path("category/<slug:slug>/", views.products_by_category, name="products_by_category"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
]