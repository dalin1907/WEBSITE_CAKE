from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, get_object_or_404
import qrcode
from io import BytesIO
import base64
from django.conf import settings
from .models import Order, OrderItem


# Hàm tạo QR code từ payload string
def generate_qr_code_from_payload(payload):
    qr = qrcode.QRCode(version=1, box_size=4, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


# Class để hiển thị các sản phẩm trong đơn hàng
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ("product_id", "product_name", "price", "quantity", "subtotal")
    extra = 0
    can_delete = False


# Giao diện admin cho model Order
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "phone", "total_amount", "payment_method", "created_at", "view_qr", "recipient_address")
    list_filter = ("payment_method", "status", "paid", "created_at", "recipient_address")
    search_fields = ("full_name", "phone", "recipient_address", "id")
    readonly_fields = ("total_amount", "created_at")
    inlines = [OrderItemInline]
    actions = ["mark_paid", "mark_unpaid", "set_status_processing", "set_status_shipped"]
    change_form_template = "admin/order_change_form.html"  # Để thêm nút in phiếu

    # Hiển thị QR code trong danh sách admin
    def view_qr(self, obj):
        site_base = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
        app_label = obj._meta.app_label
        model_name = obj._meta.model_name
        admin_print_path = f"/admin/{app_label}/{model_name}/{obj.id}/print/"

        if site_base:
            payload = f"{site_base}{admin_print_path}"
        else:
            payload = admin_print_path

        img_str = generate_qr_code_from_payload(payload)
        return format_html(f'<img src="data:image/png;base64,{img_str}" width="80" height="80">')

    view_qr.short_description = "QR Code"

    # Tạo custom URL để in phiếu
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("<int:order_id>/print/", self.admin_site.admin_view(self.print_order), name="order-print"),
        ]
        return custom_urls + urls

    # View render template in phiếu trong admin
    def print_order(self, request, order_id):
        order = get_object_or_404(Order, pk=order_id)
        public_url = request.build_absolute_uri(f"/admin/{order._meta.app_label}/{order._meta.model_name}/{order.id}/print/")
        qr_code = generate_qr_code_from_payload(public_url)
        return render(request, "admin/order_print.html", {"order": order, "qr_code": qr_code})

    # Các hành động trong admin
    def mark_paid(self, request, queryset):
        queryset.update(paid=True)
        self.message_user(request, f"{queryset.count()} đơn hàng đã được đánh dấu là ĐÃ THANH TOÁN.")
    mark_paid.short_description = "Đánh dấu ĐÃ THANH TOÁN"

    def mark_unpaid(self, request, queryset):
        queryset.update(paid=False)
        self.message_user(request, f"{queryset.count()} đơn hàng đã được đánh dấu là CHƯA THANH TOÁN.")
    mark_unpaid.short_description = "Đánh dấu CHƯA THANH TOÁN"

    def set_status_processing(self, request, queryset):
        queryset.update(status="processing")
        self.message_user(request, f"Trạng thái của {queryset.count()} đơn hàng được đặt là ĐANG XỬ LÝ.")
    set_status_processing.short_description = "Đặt trạng thái: Đang xử lý"

    def set_status_shipped(self, request, queryset):
        queryset.update(status="shipped")
        self.message_user(request, f"Trạng thái của {queryset.count()} đơn hàng được đặt là ĐÃ VẬN CHUYỂN.")
    set_status_shipped.short_description = "Đặt trạng thái: Đã vận chuyển"