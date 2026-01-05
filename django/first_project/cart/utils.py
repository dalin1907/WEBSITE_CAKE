from decimal import Decimal
from products.models import Product, CakeSize
from .models import Cart, CartItem


def get_cart_items(request):
    items = []
    total = Decimal(0)

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if not cart:
            return items, total

        for item in CartItem.objects.filter(cart=cart):
            size_price = item.size.extra_price if item.size else 0
            size_name = item.size.name if item.size else "Mặc định"

            price = item.product.price + size_price
            subtotal = price * item.quantity
            total += subtotal

            items.append({

                "product_id": item.product.id,

                "size_id": item.size.id if item.size else 0,
                "name": item.product.name,
                "size_name": size_name,
                "image": item.product.image.url if item.product.image else "",
                "price": price,
                "quantity": item.quantity,
                "subtotal": subtotal,
            })


    else:
        cart = request.session.get("cart", {})
        for value in cart.values():
            product = Product.objects.get(id=value["product_id"])
            size = CakeSize.objects.filter(id=value["size_id"]).first()

            size_price = size.extra_price if size else 0
            size_name = size.name if size else "Mặc định"

            price = product.price + size_price
            subtotal = price * value["quantity"]
            total += subtotal

            items.append({
                "product_id": product.id,
                "size_id": size.id if size else 0,
                "name": product.name,
                "size_name": size_name,
                "image": product.image.url if product.image else "",
                "price": price,
                "quantity": value["quantity"],
                "subtotal": subtotal,
            })

    return items, total
