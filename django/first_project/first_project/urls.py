from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("home.urls", namespace="home")),           # index, resume, contact, portfolio, auth
    path("products/", include("products.urls", namespace="products")),  # product listing/detail/category
    path("cart/", include("cart.urls", namespace="cart")),     # cart view, add, remove, update, checkout (review)
    path("payments/", include("payments.urls", namespace="payments")),  # payment process, success, paypal callbacks
    path('dashboard/', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)