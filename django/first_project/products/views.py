from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import Product, Category

def products(request):

    qs = Product.objects.all()
    return render(request, 'products/products.html', {'products': qs})


def product_detail(request, slug):
    # Lấy sản phẩm theo slug (nếu không có, product = None)
    product = Product.objects.filter(slug=slug).first()

    # Nếu không có sản phẩm, render một template với thông báo lỗi
    if not product:
        return render(request, 'products/product_detail.html', {
            'error': 'Sản phẩm này không tồn tại.',
            'product': None,  # Không có sản phẩm
            'similar_products': []  # Không có sản phẩm tương tự
        })

    # Lấy danh sách sản phẩm tương tự (cùng categories)
    similar_products = Product.objects.filter(
        categories__in=product.categories.all()
    ).exclude(pk=product.pk).distinct()

    # Phân trang cho sản phẩm tương tự
    paginator = Paginator(similar_products, 4)  # Mỗi trang 4 sản phẩm
    page_number = request.GET.get('page')  # Trang hiện tại
    page_obj = paginator.get_page(page_number)

    # Render chi tiết sản phẩm
    return render(request, 'products/product_detail.html', {
        'product': product,
        'similar_products': page_obj
    })




def products_by_category(request, slug):
    category = Category.objects.filter(slug=slug).first()

    if not category:
        return render(request, 'products/products_by_category.html', {
            'category': None,
            'products': [],
            'error': 'Danh mục không tồn tại.'
        })

    products = Product.objects.filter(categories=category)

    return render(request, 'products/products_by_category.html', {
        'category': category,
        'products': products
    })
