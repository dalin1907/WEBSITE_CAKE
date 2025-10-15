from django.shortcuts import render, get_object_or_404

from .models import Product, Category

def index(request):

    try:
        new_category = Category.objects.get(id=2)
        favorite_category = Category.objects.get(id=3)
        sale_category = Category.objects.get(id=4)
    except Category.DoesNotExist:
        new_category = favorite_category = sale_category = None

    new_products = Product.objects.filter(category=new_category) if new_category else []
    favorite_products = Product.objects.filter(category=favorite_category) if favorite_category else []
    sale_products = Product.objects.filter(category=sale_category) if sale_category else []

    return render(request, 'index.html', {
        'new_products': new_products,
        'favorite_products': favorite_products,
        'sale_products': sale_products,
    })
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})
def portfolio(request):
     return render(request, "portfolio.html")
def resume(request):
     return render(request, "resume.html")
def contact(request):
    return render(request, "contact.html")
def products(request):
    products = Product.objects.all()
    return render(request, "products.html", {"products": products})
# Create your views here.
