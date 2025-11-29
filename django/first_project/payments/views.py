from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.conf import settings

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Order, OrderItem
from .paypal_api import create_paypal_order, capture_paypal_order
from cart.utils import get_cart_items
from cart.models import Cart, CartItem  # ✅ Import Cart và CartItem

def checkout(request):
    items, total = get_cart_items(request)

    if request.method == "GET":
        return render(request, "cart/checkout.html", {"items": items, "total": total})

    # POST: tạo order
    full_name = request.POST.get("full_name", "Test User")
    email = request.POST.get("email", "test@example.com")
    phone = request.POST.get("phone", "")
    recipient_address = request.POST.get("recipient_address", "")
    note = request.POST.get("note", "")
    payment_method = request.POST.get("payment_method", "paypal")
    currency = getattr(settings, "PAYPAL_CURRENCY", "USD")
    formatted_total = "{:.2f}".format(total)

    order = Order.objects.create(
        full_name=full_name,
        email=email,
        phone=phone,
        recipient_address=recipient_address,
        payment_method=payment_method,
        total_amount=total,
        paid=False,
        note=note,
        status="pending"
    )

    for it in items:
        OrderItem.objects.create(
            order=order,
            product_name=it.get("name"),
            price=it.get("price") or Decimal('0.00'),
            quantity=it.get("quantity") or 1,
            subtotal=it.get("subtotal") or Decimal('0.00')
        )

    if payment_method == "paypal":
        return_url = request.build_absolute_uri(reverse("payments:paypal_return")) + f"?order_id={order.id}"
        cancel_url = request.build_absolute_uri(reverse("payments:paypal_cancel")) + f"?order_id={order.id}"

        try:
            data = create_paypal_order(formatted_total, return_url, cancel_url, currency=currency)
        except Exception as e:
            messages.error(request, f"Không thể tạo order PayPal: {str(e)}")
            return redirect("payments:checkout")

        approve_url = next((link["href"] for link in data.get("links", []) if link.get("rel") == "approve"), None)
        if not approve_url:
            messages.error(request, "Không lấy được link PayPal.")
            return redirect("payments:checkout")

        order.paypal_order_id = data.get("id")
        order.status = "paypal_created"
        order.save()

        return redirect(approve_url)

    # COD
    order.paid = False
    order.status = "processing"
    order.save()

    # ✅ Xóa giỏ hàng của user sau khi đặt hàng COD
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            pass
    elif "cart" in request.session:
        del request.session["cart"]

    # gửi email
    send_order_email(order)

    return redirect("payments:success", order_id=order.id)


def paypal_return(request):
    order_id = request.GET.get("order_id")
    if not order_id:
        messages.error(request, "Thiếu order_id")
        return redirect("payments:checkout")
    order = get_object_or_404(Order, id=order_id)

    try:
        capture_data = capture_paypal_order(order.paypal_order_id)
    except Exception as e:
        messages.error(request, f"Thanh toán không hoàn tất: {str(e)}")
        return redirect("payments:checkout")

    if capture_data.get("status") == "COMPLETED":
        order.paid = True
        order.status = "processing"
        order.save()

        # ✅ Xóa giỏ hàng của user sau khi thanh toán PayPal thành công
        if request.user.is_authenticated:
            try:
                cart = Cart.objects.get(user=request.user)
                cart.items.all().delete()
            except Cart.DoesNotExist:
                pass
        elif "cart" in request.session:
            del request.session["cart"]
        # gửi email
        send_order_email(order)
        messages.success(request, f"Thanh toán thành công cho đơn #{order.id}")
        return redirect("payments:success", order_id=order.id)
    else:
        messages.error(request, "Thanh toán chưa hoàn tất")
        return redirect("payments:checkout")


def paypal_cancel(request):
    order_id = request.GET.get("order_id")
    if order_id:
        order = get_object_or_404(Order, id=order_id)
        order.status = "paypal_cancelled"
        order.save()
    messages.info(request, "Bạn đã hủy thanh toán PayPal")
    return redirect("payments:checkout")


def checkout_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # ✅ Dọn giỏ hàng lần cuối (phòng trường hợp còn sót)
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            pass
    elif "cart" in request.session:
        del request.session["cart"]

    return render(request, "payments/checkout_success.html", {"order": order})

def send_order_email(order):
    subject = f"Xác nhận đơn hàng #{order.id}"
    html_message = render_to_string("payments/email/order_confirmation.html", {"order": order})
    plain_message = strip_tags(html_message)
    recipient_list = [order.email]

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        html_message=html_message,
        fail_silently=False,
    )






