from django.db.models import Sum

from .models import CartItem

def cart_count(request):
    """
    Context processor trả về tổng số lượng trong giỏ hàng để dùng trong template.
    Sửa để lọc theo cart__user thay vì user (CartItem không có field user).
    """
    if getattr(request, 'user', None) and request.user.is_authenticated:
        total = CartItem.objects.filter(cart__user=request.user).aggregate(total=Sum('quantity'))['total'] or 0
    else:
        cart = request.session.get('cart', {})
        try:
            total = sum(int(item.get('quantity', 0) or 0) for item in cart.values())
        except Exception:
            total = 0
    return {'cart_count': int(total)}