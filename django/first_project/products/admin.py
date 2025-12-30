from django.contrib import admin
from .models import Category, Product, CakeSize

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(CakeSize)
class CakeSizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'extra_price')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price')
    search_fields = ('name',)
    filter_horizontal = ('categories','sizes')  # tiện chọn nhiều category trong admin
