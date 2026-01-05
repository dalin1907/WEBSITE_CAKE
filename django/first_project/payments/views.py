from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
import hmac, hashlib, base64

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Order, OrderItem
from .paypal_api import create_paypal_order, capture_paypal_order
from .vnpay import create_vnpay_url
from cart.utils import get_cart_items
from cart.models import Cart, CartItem  # ✅ Import Cart và CartItem
from .momo import create_momo_payment
from helpers.finance import convert_to_vnd

ALLOWED_DISTRICTS = [
    "Quận 1","Quận 3","Quận 4","Quận 5","Quận 6","Quận 7","Quận 8",
    "Quận 10","Quận 11","Quận 12","Bình Thạnh","Gò Vấp","Phú Nhuận",
    "Tân Bình","Tân Phú","Thủ Đức","Bình Tân","Hóc Môn","Bình Chánh",
    "Nhà Bè","Củ Chi","Cần Giờ"
]

def checkout(request):
    # ✅ Logging chi tiết thông tin giỏ hàng và POST request
    items, total = get_cart_items(request)
    print(f"Items: {items}, Total: {total}")

    # Nếu giỏ hàng trống hoặc số tiền <= 0
    if total <= 0:
        messages.error(request, "Giỏ hàng của bạn trống hoặc số tiền không hợp lệ.")
        return redirect("payments:checkout")

    # Xử lý GET request
    if request.method == "GET":
        return render(request, "payments/checkout.html", {"items": items, "total": total})

    # ✅ Logging dữ liệu POST request nhận được
    print(f"POST Data: {request.POST}")

    # POST: kiểm tra đầy đủ dữ liệu đầu vào
    full_name = request.POST.get("full_name", "").strip()
    email = request.POST.get("email", "").strip()
    phone = request.POST.get("phone", "").strip()
    district = request.POST.get("district", "").strip()
    street = request.POST.get("recipient_address", "").strip()
    note = request.POST.get("note", "").strip()
    payment_method = request.POST.get("payment_method", "paypal").strip()

    # Kiểm tra email valid
    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, "Vui lòng nhập địa chỉ email hợp lệ.")
        return redirect("payments:checkout")

    # Kiểm tra địa chỉ đầy đủ
    if not district or not street:
        messages.error(request, "Vui lòng nhập đầy đủ địa chỉ giao hàng.")
        return redirect("payments:checkout")

    # Kiểm tra quận/huyện có hợp lệ không
    if district not in ALLOWED_DISTRICTS:
        messages.error(request, "Hiện shop chỉ giao hàng trong TP. Hồ Chí Minh.")
        return redirect("payments:checkout")

    # ✅ Tạo Order
    recipient_address = f"{street}, {district}, TP. Hồ Chí Minh"
    order = Order.objects.create(
        user=request.user,
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

    # ✅ Tạo OrderItem cho từng sản phẩm trong giỏ hàng
    for item in items:
        OrderItem.objects.create(
            order=order,
            product_name=item.get("name"),
            price=item.get("price") or Decimal('0.00'),
            quantity=item.get("quantity") or 1,
            subtotal=item.get("subtotal") or Decimal('0.00')
        )

    # ------------------------
    # Xử lý theo phương thức thanh toán
    # ------------------------

    # ✅ PayPal
    if payment_method == "paypal":
        try:
            return_url = request.build_absolute_uri(reverse("payments:paypal_return")) + f"?order_id={order.id}"
            cancel_url = request.build_absolute_uri(reverse("payments:paypal_cancel")) + f"?order_id={order.id}"

            data = create_paypal_order("{:.2f}".format(total), return_url, cancel_url)
            approve_url = next((link["href"] for link in data.get("links", []) if link.get("rel") == "approve"), None)

            if not approve_url:
                raise Exception("Không lấy được link PayPal.")

            # ✅ Cập nhật trạng thái order
            order.paypal_order_id = data.get("id")
            order.status = "paypal_created"
            order.save()

            # Redirect tới giao diện xác nhận PayPal
            return redirect(approve_url)
        except Exception as e:
            print(f"PayPal error: {e}")
            messages.error(request, f"Lỗi PayPal: {str(e)}")
            return redirect("payments:checkout")

    # ✅ VNPay
    elif payment_method == "vnpay":
        try:
            return_url = "https://a1b2c3d4.ngrok-free.app/payments/vnpay-return/"
            payment_url = create_vnpay_url(order.id, order.total_amount, return_url)

            # ✅ Cập nhật trạng thái order
            order.status = "vnpay_created"
            order.save()

            return redirect(payment_url)
        except Exception as e:
            print(f"VNPay error: {e}")
            messages.error(request, f"Lỗi VNPay: {str(e)}")
            return redirect("payments:checkout")

    # ✅ MoMo
    # ✅ MoMo
    elif payment_method == "momo":
        try:
            # Chuyển số tiền sang integer string để đảm bảo gửi đúng format
            total_amount = str(int(total))  # Loại bỏ phần thập phân, đảm bảo số nguyên

            # Xây dựng thông tin cần thiết để tạo request MoMo
            redirect_url = request.build_absolute_uri("/payments/momo-return/")
            ipn_url = request.build_absolute_uri("/payments/momo-ipn/")
            order_info = f"Thanh toán đơn hàng #{order.id}"

            # Gọi hàm API MoMo (file momo.py)
            print(">>> Gửi yêu cầu MoMo:")
            print(f"Tổng tiền: {total_amount}, Info: {order_info}, Redirect: {redirect_url}, IPN: {ipn_url}")

            res = create_momo_payment(amount=total_amount, order_info=order_info, redirect_url=redirect_url,
                                      ipn_url=ipn_url)

            # ✅ Lấy URL thanh toán từ phản hồi
            momo_url = res.get("payUrl")
            if not momo_url:
                raise Exception(f"MoMo không trả về URL thanh toán (payUrl).")

            # ✅ Cập nhật trạng thái order
            order.momo_order_id = res.get("orderId")  # Order ID từ MoMo
            order.status = "momo_created"
            order.save()

            # Debug log để kiểm tra bước redirect
            print(f"URL thanh toán MoMo: {momo_url}")

            # Redirect tới giao diện thanh toán MoMo
            return redirect(momo_url)

        except Exception as e:
            # Xử lý lỗi MoMo
            print(f"Lỗi MoMo: {e}")
            messages.error(request, f"Lỗi khi tạo thanh toán MoMo: {e}")
            return redirect("payments:checkout")

    # ✅ Thanh toán COD
    else:
        order.paid = False
        order.status = "processing"
        order.save()

    # ✅ Dọn giỏ hàng sau khi tạo order
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            pass
    elif "cart" in request.session:
        del request.session["cart"]

    # ✅ Gửi email xác nhận
    send_order_email(order)

    # Redirect tới trang thành công
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

def pay_with_vnpay(request, order_id):
    order = Order.objects.get(id=order_id)
    amount = order.total_amount  # Lấy tổng tiền từ đơn hàng
    # Tạo return_url linh hoạt
    return_url = request.build_absolute_uri("/payments/vnpay-return/")
    payment_url = create_vnpay_url(order.id, int(order.total_amount))

    return redirect(payment_url)

def vnpay_return(request):
    vnp_response = request.GET
    code = vnp_response.get("vnp_ResponseCode")
    txn_ref = vnp_response.get("vnp_TxnRef")

    if code == "00":
        # Update trạng thái đơn hàng
        from orders.models import Order
        order = Order.objects.get(id=txn_ref)
        order.payment_status = "PAID"
        order.save()
        return HttpResponse("Thanh toán VNPay thành công!")
    else:
        return HttpResponse("Thanh toán VNPay thất bại.")


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

@login_required
def customer_order_list(request):
    # Lấy danh sách các đơn hàng của user hiện tại (tự động dựa vào request.user)
    orders = Order.objects.filter(user=request.user)  # Chỉ hiển thị đơn hàng của user đã đăng nhập
    return render(request, 'payments/customer_order_list.html', {'orders': orders})

@login_required
def customer_order_detail(request, order_id):
    # Lấy đơn hàng theo ID và đảm bảo chỉ hiển thị nếu đơn của user
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()  # Lấy danh sách sản phẩm trong đơn hàng (order.items liên kết tới OrderItem)

    return render(request, 'payments/customer_order_detail.html', {
        'order': order,
        'items': items,
    })


@staff_member_required
def process_orders(request):
    orders = Order.objects.all().order_by('-created_at')  # Lấy danh sách đơn hàng theo thời gian mới nhất
    return render(request, 'payments/admin_order_list.html', {'orders': orders})


# Xử lý chi tiết một đơn hàng
@staff_member_required
def process_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')  # Lấy trạng thái mới từ form
        if new_status:
            order.status = new_status  # Cập nhật trạng thái
            order.save()
            messages.success(request, f"Cập nhật trạng thái đơn hàng #{order.id} thành công!")
        else:
            messages.error(request, "Không tìm thấy trạng thái mới để cập nhật.")
        return redirect('payments:process_orders')

    return render(request, 'payments/admin_order_detail.html', {'order': order})

def track_order_by_token(request):
    token = request.GET.get('token', '')
    order = get_object_or_404(Order, invoice_token=token)

    return render(request, 'payments/track_order.html', {'order': order})


def momo_return(request):
    result = request.GET.get("resultCode")

    if result == "0":
        order = Order.objects.filter(momo_order_id=request.GET.get("orderId")).first()
        if order:
            order.paid = True
            order.status = "processing"
            order.save()
            send_order_email(order)
            return redirect("payments:success", order_id=order.id)

    messages.error(request, "Thanh toán MoMo thất bại")
    return redirect("payments:checkout")


def momo_ipn(request):
    return JsonResponse({"status": "ok"})

def sign(raw_signature, secret_key):
    h = hmac.new(secret_key.encode(), raw_signature.encode(), hashlib.sha256)
    return base64.b64encode(h.digest()).decode()