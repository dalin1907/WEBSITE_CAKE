from django.contrib import admin
from django.core.mail import send_mail
from django.utils import timezone
from .models import SupplierProfile, SupplierRequest

@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'contact_email', 'phone', 'is_approved', 'created_at')
    search_fields = ('company_name', 'user__username', 'contact_email')
    list_filter = ('is_approved',)

@admin.register(SupplierRequest)
class SupplierRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'ingredient', 'requested_quantity', 'status', 'claimed_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('ingredient__name', 'claimed_by__company_name', 'created_by__username')
    readonly_fields = ('created_at', 'claimed_at', 'admin_decision_at')
    actions = ('action_accept', 'action_reject')

    def action_accept(self, request, queryset):
        for req in queryset:
            req.status = SupplierRequest.STATUS_ACCEPTED
            req.admin_decided_by = request.user
            req.admin_decision_at = timezone.now()
            req.save()
            # send email to supplier (if claimed)
            if req.claimed_by and req.claimed_by.contact_email:
                send_mail(
                    subject=f"[Đã chấp nhận] Yêu cầu cung cấp #{req.pk}",
                    message=f"Yêu cầu #{req.pk} đã được chấp nhận bởi admin.",
                    from_email=None,
                    recipient_list=[req.claimed_by.contact_email],
                    fail_silently=True,
                )
        self.message_user(request, f"Đã chấp nhận {queryset.count()} yêu cầu.")
    action_accept.short_description = "Chấp nhận các yêu cầu đã chọn"

    def action_reject(self, request, queryset):
        for req in queryset:
            req.status = SupplierRequest.STATUS_REJECTED
            req.admin_decided_by = request.user
            req.admin_decision_at = timezone.now()
            req.save()
            if req.claimed_by and req.claimed_by.contact_email:
                send_mail(
                    subject=f"[Bị từ chối] Yêu cầu cung cấp #{req.pk}",
                    message=f"Yêu cầu #{req.pk} đã bị từ chối bởi admin.",
                    from_email=None,
                    recipient_list=[req.claimed_by.contact_email],
                    fail_silently=True,
                )
        self.message_user(request, f"Đã từ chối {queryset.count()} yêu cầu.")
    action_reject.short_description = "Từ chối các yêu cầu đã chọn"