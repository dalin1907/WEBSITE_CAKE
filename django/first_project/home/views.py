from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.conf import settings
from products.models import Category, Product
from django.contrib.auth.models import  User


def index(request):
    categories = Category.objects.all()
    category_products = []

    for category in categories:
        # Lọc product theo ManyToManyField
        products = Product.objects.filter(categories=category)
        category_products.append({
            'category': category,
            'products': products
        })

    return render(request, 'home/index.html', {
        'category_products': category_products
    })


def portfolio(request):
    return render(request, "home/portfolio.html")


def resume(request):
    return render(request, "home/resume.html")


def contact(request):
    return render(request, "home/contact.html")


def register_view(request):
    # from django.contrib.auth.models import User

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm', '')

        if password == confirm:
            if User.objects.filter(username=username).exists():
                messages.error(request, "Tên đăng nhập đã tồn tại")
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                messages.success(request, "Đăng ký thành công! Hãy đăng nhập.")
                return redirect('home:login')
        else:
            messages.error(request, "Mật khẩu không khớp")

    return render(request, 'home/register.html')


def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # merge giỏ session (nếu có) vào DB
            try:
                merge_session_cart_to_user(request)
            except Exception:
                # không để merge gây crash trang login
                pass
            return redirect('home:index')  # chuyển đến trang chính
        else:
            messages.error(request, "Sai tên đăng nhập hoặc mật khẩu")

    return render(request, 'home/login.html')


def logout_view(request):
    logout(request)
    return redirect('home:login')




def user(request):
    user = User.objects.all()
    return render(request, 'home/user.html',{'user':user})
