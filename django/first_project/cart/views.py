from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from products.models import Product, CakeSize
from .models import Cart, CartItem
from .utils import get_cart_items
from django.contrib import messages




def add_to_cart(request, product_id):
    if request.method != "POST":
        return redirect("products:product_detail", pk=product_id)

    product = get_object_or_404(Product, id=product_id)

    # chống submit trùng
    token = request.POST.get("csrfmiddlewaretoken")
    if request.session.get("last_add_token") == token:
        return redirect("cart:detail")
    request.session["last_add_token"] = token

    size_id = request.POST.get("size_id")
    size = CakeSize.objects.filter(id=size_id).first() if size_id else None

    try:
        quantity = int(request.POST.get("quantity", 1))
    except:
        quantity = 1

    if quantity < 1:
        quantity = 1

    # ================= LOGIN =================
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size,
            defaults={"quantity": quantity},
        )

        if not created:
            item.quantity += quantity
            item.save()

    # ================= SESSION =================
    else:
        cart = request.session.get("cart", {})
        key = f"{product.id}_{size.id if size else 0}"

        if key not in cart:
            cart[key] = {
                "product_id": product.id,
                "size_id": size.id if size else 0,
                "name": product.name,
                "size_name": size.name if size else "",
                "quantity": quantity,
            }
        else:
            cart[key]["quantity"] += quantity

        request.session["cart"] = cart
        request.session.modified = True

    return redirect("cart:detail")


def update_cart(request, product_id, size_id):
    size_id = int(size_id)
    action = request.POST.get("action")

    # ================= LOGIN =================
    if request.user.is_authenticated:
        cart = get_object_or_404(Cart, user=request.user)

        item = get_object_or_404(
            CartItem,
            cart=cart,
            product_id=product_id,
            size_id=size_id if size_id != 0 else None,
        )

        if action == "increase":
            item.quantity += 1
        elif action == "decrease":
            item.quantity -= 1

        if item.quantity <= 0:
            item.delete()
        else:
            item.save()

    # ================= SESSION =================
    else:
        cart = request.session.get("cart", {})
        key = f"{product_id}_{size_id}"

        if key not in cart:
            return redirect("cart:detail")

        if action == "increase":
            cart[key]["quantity"] += 1
        elif action == "decrease":
            cart[key]["quantity"] -= 1

        if cart[key]["quantity"] <= 0:
            del cart[key]

        request.session["cart"] = cart
        request.session.modified = True

    return redirect("cart:detail")


def remove_from_cart(request, product_id, size_id):
    size_id = int(size_id)

    if request.user.is_authenticated:
        cart = get_object_or_404(Cart, user=request.user)
        CartItem.objects.filter(
            cart=cart,
            product_id=product_id,
            size_id=size_id if size_id != 0 else None,
        ).delete()
    else:
        cart = request.session.get("cart", {})
        key = f"{product_id}_{size_id}"
        cart.pop(key, None)
        request.session["cart"] = cart
        request.session.modified = True

    return redirect("cart:detail")


def cart_detail(request):
    items, total = get_cart_items(request)
    return render(request, "cart/cart.html", {"items": items, "total": total})



