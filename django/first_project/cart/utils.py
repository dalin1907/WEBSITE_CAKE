from decimal import Decimal
from products.models import Product
from .models import Cart, CartItem

def get_cart_items(request):
    items = []
    total = Decimal('0.00')

    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = CartItem.objects.filter(cart=cart)
            for ci in cart_items:
                item = {
                    'id': ci.id,
                    'product_id': ci.product.id,
                    'name': ci.product.name,
                    'price': ci.product.price,
                    'quantity': ci.quantity,
                    'subtotal': ci.subtotal(),
                    'image': ci.product.image.url if ci.product.image else None,
                }
                items.append(item)
                total += ci.subtotal()
        except Cart.DoesNotExist:
            pass
    else:
        session_cart = request.session.get('cart', {})
        for pid, data in session_cart.items():
            subtotal = Decimal(str(data.get('price', 0))) * int(data.get('quantity', 0))
            item = {
                'id': pid,
                'product_id': int(pid),
                'name': data.get('name', ''),
                'price': Decimal(str(data.get('price', 0))),
                'quantity': int(data.get('quantity', 0)),
                'subtotal': subtotal,
                'image': data.get('image') or None,
            }
            items.append(item)
            total += subtotal

    return items, total
