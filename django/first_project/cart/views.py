from decimal import Decimal
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect

from products.models import Product
from .models import Cart, CartItem
from .utils import get_cart_items

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    qty_raw = request.POST.get('quantity', '')
    try:
        quantity = int(qty_raw) if qty_raw != '' else 1
    except (ValueError, TypeError):
        quantity = 1

    if quantity <= 0:
        messages.error(request, "Số lượng phải là số dương")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 0})
        cart_item.quantity += quantity
        cart_item.save()
    else:
        session_cart = request.session.get('cart', {})
        pid = str(product_id)
        if pid in session_cart:
            session_cart[pid]['quantity'] += quantity
        else:
            session_cart[pid] = {
                'name': product.name,
                'price': str(product.price),
                'quantity': quantity,
                'image': product.image.url if product.image else None,
            }
        request.session['cart'] = session_cart
        request.session.modified = True

    return redirect('cart:detail')


def remove_from_cart(request, item_id):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            CartItem.objects.filter(cart=cart, id=item_id).delete()
        except Cart.DoesNotExist:
            pass
    else:
        session_cart = request.session.get('cart', {})
        session_cart.pop(str(item_id), None)
        request.session['cart'] = session_cart
        request.session.modified = True

    return redirect('cart:detail')


def update_cart(request, item_id):
    if request.method != 'POST':
        return redirect('cart:detail')

    action = request.POST.get('action')
    if action not in ('increase', 'decrease', 'set'):
        return HttpResponseBadRequest("Invalid action")

    product = get_object_or_404(Product, pk=item_id)

    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_item, _ = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': 0})
        except Cart.DoesNotExist:
            return HttpResponseBadRequest("Cart not found")

        current_qty = cart_item.quantity
        if action == 'increase':
            new_qty = current_qty + 1
        elif action == 'decrease':
            new_qty = current_qty - 1
        else:
            try:
                new_qty = int(request.POST.get('quantity', 0))
            except:
                return HttpResponseBadRequest("Invalid quantity")

        if new_qty <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = new_qty
            cart_item.save()
    else:
        session_cart = request.session.get('cart', {})
        key = str(item_id)
        current_qty = session_cart.get(key, {}).get('quantity', 0)
        if action == 'increase':
            new_qty = int(current_qty) + 1
        elif action == 'decrease':
            new_qty = int(current_qty) - 1
        else:
            try:
                new_qty = int(request.POST.get('quantity', 0))
            except:
                return HttpResponseBadRequest("Invalid quantity")

        if new_qty <= 0:
            session_cart.pop(key, None)
        else:
            session_cart[key]['quantity'] = new_qty

        request.session['cart'] = session_cart
        request.session.modified = True

    return redirect('cart:detail')


def cart_detail(request):
    items, total = get_cart_items(request)
    return render(request, 'cart/cart.html', {'items': items, 'total': total})


def cart_count(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            total = CartItem.objects.filter(cart=cart).aggregate(total=Sum('quantity'))['total'] or 0
        except Cart.DoesNotExist:
            total = 0
    else:
        session_cart = request.session.get('cart', {})
        total = sum(int(i.get('quantity', 0)) for i in session_cart.values())
    return {'cart_count': total}

def checkout(request):
    # ví dụ cơ bản
    items, total = get_cart_items(request)
    return render(request, 'cart/checkout.html', {'items': items, 'total': total})