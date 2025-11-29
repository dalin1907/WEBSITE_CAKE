from django.shortcuts import render, get_object_or_404
from .models import Product, Category

def products(request):

    qs = Product.objects.all()
    return render(request, 'products/products.html', {'products': qs})


def product_detail(request, pk):
    product = Product.objects.get(pk=pk)

    # Lấy danh sách sản phẩm cùng category (hoặc nhiều category) nhưng không gồm chính sản phẩm này
    similar_products = Product.objects.filter(
        categories__in=product.categories.all()
    ).exclude(id=product.id).distinct()[:8]  # lấy tối đa 8 sản phẩm tương tự

    return render(request, 'products/product_detail.html', {
        'product': product,
        'similar_products': similar_products
    })


def products_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(categories=category)
    return render(request, 'products/products_by_category.html', {
        'category': category,
        'products': products
    })