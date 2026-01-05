from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("home.urls", namespace="home")),
    path("products/", include("products.urls", namespace="products")),
    path("cart/", include("cart.urls", namespace="cart")),
    path("payments/", include("payments.urls", namespace="payments")),
    path("suppliers/", include("suppliers.urls", namespace="suppliers")),
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
    path('social-auth/', include('social_django.urls', namespace='social')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)