from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import Product, Category

def products(request):

    qs = Product.objects.all()
    return render(request, 'products/products.html', {'products': qs})


def product_detail(request, pk):
    # Lấy sản phẩm cụ thể
    product = get_object_or_404(Product, pk=pk)

    # Lấy danh sách sản phẩm tương tự (ví dụ: trong cùng category đầu tiên)
    similar_products = Product.objects.exclude(pk=product.pk).filter(
        categories__in=product.categories.all()
    ).distinct()

    # Áp dụng phân trang
    paginator = Paginator(similar_products, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Truyền dữ liệu vào context
    context = {
        'product': product,
        'similar_products': page_obj,  # Trang hiện tại của paginator
    }
    return render(request, 'products/product_detail.html', context)


def products_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(categories=category)
    return render(request, 'products/products_by_category.html', {
        'category': category,
        'products': products
    })