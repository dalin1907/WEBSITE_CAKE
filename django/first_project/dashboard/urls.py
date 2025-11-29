from django.urls import path
from . import views

urlpatterns = [
    path('order-statistics/', views.order_statistics, name='order_statistics'),
]
