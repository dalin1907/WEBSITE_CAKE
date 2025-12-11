from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, DetailView, View
from django.contrib.auth.decorators import login_required

from .models import SupplierRequest, SupplierProfile
from .forms import SupplierRequestForm, SupplierClaimForm, SupplierProfileForm
from dashboard.models import Ingredient

User = get_user_model()


# ===========================================================
# 1) ADMIN TẠO YÊU CẦU CUNG CẤP
# ===========================================================
class SupplierRequestCreateView(UserPassesTestMixin, CreateView):
    model = SupplierRequest
    form_class = SupplierRequestForm
    template_name = 'suppliers/request_form.html'
    success_url = reverse_lazy('suppliers:supplier_request_list')

    def test_func(self):
        return self.request.user.is_staff

    def get_initial(self):
        initial = super().get_initial()
        ingredient_pk = self.request.GET.get('ingredient')
        if ingredient_pk:
            try:
                ing = Ingredient.objects.get(pk=int(ingredient_pk))
                initial['ingredient'] = ing.pk
            except:
                pass
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ingredient_pk = self.request.GET.get('ingredient')
        ctx['prefill_ingredient'] = None
        if ingredient_pk:
            try:
                ctx['prefill_ingredient'] = Ingredient.objects.get(pk=int(ingredient_pk))
            except:
                pass
        return ctx

    def form_valid(self, form):
        req = form.save(commit=False)
        req.created_by = self.request.user
        req.save()
        messages.success(self.request, 'Đã tạo yêu cầu cung cấp.')
        return super().form_valid(form)


# ===========================================================
# 2) DANH SÁCH YÊU CẦU
# ===========================================================
class SupplierRequestListView(LoginRequiredMixin, ListView):
    model = SupplierRequest
    template_name = 'suppliers/request_list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user

        # SUPPLIER — xem request mở + request mình đã nhận
        profile = getattr(user, 'supplier_profile', None)
        if profile:
            qs_open = SupplierRequest.objects.filter(status=SupplierRequest.STATUS_OPEN)
            qs_mine = SupplierRequest.objects.filter(claimed_by=profile)
            return (qs_open | qs_mine).distinct().order_by('-created_at')

        # ADMIN — xem tất cả
        if user.is_staff:
            return SupplierRequest.objects.all().order_by('-created_at')

        return SupplierRequest.objects.none()


# ===========================================================
# 3) CHI TIẾT YÊU CẦU
# ===========================================================
class SupplierRequestDetailView(LoginRequiredMixin, DetailView):
    model = SupplierRequest
    template_name = 'suppliers/request_detail.html'
    context_object_name = 'request_obj'


# ===========================================================
# 4) SUPPLIER NHẬN YÊU CẦU
# ===========================================================
class SupplierClaimView(LoginRequiredMixin, View):
    def post(self, request, pk):
        profile = getattr(request.user, 'supplier_profile', None)

        if not profile:
            messages.error(request, 'Bạn cần tạo hồ sơ nhà cung cấp trước.')
            return redirect('suppliers:supplier_profile_create')

        if not profile.is_approved:
            messages.error(request, 'Hồ sơ nhà cung cấp của bạn chưa được admin duyệt.')
            return redirect('suppliers:supplier_request_list')

        req = get_object_or_404(SupplierRequest, pk=pk)

        if req.status != SupplierRequest.STATUS_OPEN:
            messages.error(request, 'Yêu cầu này đã được nhận hoặc không còn mở.')
            return redirect('suppliers:supplier_request_list')

        form = SupplierClaimForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Dữ liệu không hợp lệ.')
            return redirect('suppliers:supplier_request_list')

        # cập nhật request
        req.claimed_by = profile
        req.claimed_at = timezone.now()
        req.supplier_message = form.cleaned_data.get('message', '')
        req.status = SupplierRequest.STATUS_CLAIMED
        req.save()

        # gửi email thông báo admin
        admin_emails = list(
            User.objects.filter(is_staff=True, is_active=True)
            .exclude(email='')
            .values_list('email', flat=True)
        )

        if admin_emails:
            subject = f"[Thông báo] Nhà cung cấp đã nhận yêu cầu #{req.pk}"

            text_body = render_to_string(
                'emails/supplier_claimed.txt',
                {'request': req, 'supplier': profile, 'user': request.user}
            )
            html_body = render_to_string(
                'emails/supplier_claimed.html',
                {'request': req, 'supplier': profile, 'user': request.user}
            )

            email = EmailMultiAlternatives(subject, text_body, None, admin_emails)
            email.attach_alternative(html_body, "text/html")
            email.send()

        messages.success(request, 'Bạn đã nhận yêu cầu. Admin sẽ kiểm tra và phản hồi.')
        return redirect('suppliers:supplier_request_list')


# ===========================================================
# 5) SUPPLIER TẠO HỒ SƠ
# ===========================================================
class SupplierProfileCreateView(LoginRequiredMixin, CreateView):
    model = SupplierProfile
    form_class = SupplierProfileForm
    template_name = 'suppliers/profile_form.html'
    success_url = reverse_lazy('suppliers:supplier_request_list')

    def dispatch(self, request, *args, **kwargs):
        if getattr(request.user, 'supplier_profile', None):
            messages.info(request, 'Bạn đã có hồ sơ nhà cung cấp.')
            return redirect('suppliers:supplier_request_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        profile = form.save(commit=False)
        profile.user = self.request.user
        profile.save()
        messages.success(self.request, 'Hồ sơ đã tạo thành công. Chờ admin duyệt.')
        return super().form_valid(form)


# ===========================================================
# 6) ĐĂNG KÝ NHÀ CUNG CẤP
# ===========================================================
def supplier_register_view(request):
    if not request.user.is_authenticated:
        messages.info(request, "Vui lòng đăng nhập trước khi đăng ký.")
        return redirect('home:login')

    if hasattr(request.user, 'supplier_profile'):
        messages.info(request, "Bạn đã có hồ sơ nhà cung cấp.")
        return redirect('suppliers:supplier_request_list')

    if request.method == 'POST':
        form = SupplierProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Hồ sơ tạo thành công. Chờ admin duyệt.")
            return redirect('suppliers:supplier_request_list')
    else:
        form = SupplierProfileForm()

    return render(request, 'suppliers/supplier_register.html', {'form': form})


# ===========================================================
# 7) ADMIN — XEM REQUEST ĐÃ ĐƯỢC NHẬN
# ===========================================================
@staff_member_required
def supplier_claimed_list(request):
    requests = SupplierRequest.objects.filter(status=SupplierRequest.STATUS_CLAIMED)
    return render(request, 'suppliers/claimed_list.html', {'requests': requests})


# ===========================================================
# 8) ADMIN DUYỆT / TỪ CHỐI
# ===========================================================
class AdminAcceptSupplierRequestView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, pk):
        req = get_object_or_404(SupplierRequest, pk=pk)

        if req.status != SupplierRequest.STATUS_CLAIMED:
            messages.error(request, "Yêu cầu này chưa được supplier nhận.")
            return redirect("suppliers:supplier_request_detail", pk=pk)

        req.status = SupplierRequest.STATUS_ACCEPTED
        req.admin_decided_by = request.user
        req.admin_decision_at = timezone.now()
        req.admin_note = "Đã duyệt."
        req.save()

        # gửi email cho supplier
        supplier_email = req.claimed_by.user.email
        if supplier_email:
            subject = f"Yêu cầu #{req.pk} đã được duyệt"

            text_body = render_to_string('emails/admin_accept.txt', {'req': req})
            html_body = render_to_string('emails/admin_accept.html', {'req': req})

            email = EmailMultiAlternatives(subject, text_body, None, [supplier_email])
            email.attach_alternative(html_body, "text/html")
            email.send()

        messages.success(request, "Đã chấp nhận yêu cầu.")
        return redirect("suppliers:supplier_request_detail", pk=pk)


class AdminRejectSupplierRequestView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, pk):
        req = get_object_or_404(SupplierRequest, pk=pk)

        if req.status != SupplierRequest.STATUS_CLAIMED:
            messages.error(request, "Yêu cầu chưa được supplier nhận.")
            return redirect("suppliers:supplier_request_detail", pk=pk)

        req.status = SupplierRequest.STATUS_REJECTED
        req.admin_decided_by = request.user
        req.admin_decision_at = timezone.now()
        req.admin_note = "Từ chối yêu cầu."
        req.save()

        supplier_email = req.claimed_by.user.email
        if supplier_email:
            subject = f"Yêu cầu #{req.pk} bị từ chối"

            text_body = render_to_string('emails/admin_reject.txt', {'req': req})
            html_body = render_to_string('emails/admin_reject.html', {'req': req})

            email = EmailMultiAlternatives(subject, text_body, None, [supplier_email])
            email.attach_alternative(html_body, "text/html")
            email.send()

        messages.warning(request, "Đã từ chối yêu cầu.")
        return redirect("suppliers:supplier_request_detail", pk=pk)


# ===========================================================
# 9) SUPPLIER HOÀN THÀNH YÊU CẦU
# ===========================================================
@login_required
def supplier_complete_request(request, pk):
    profile = getattr(request.user, 'supplier_profile', None)

    if not profile:
        messages.error(request, "Bạn phải là nhà cung cấp mới thao tác được.")
        return redirect("suppliers:supplier_request_list")

    req = get_object_or_404(SupplierRequest, pk=pk)

    if req.claimed_by != profile:
        messages.error(request, "Bạn không có quyền hoàn thành yêu cầu này.")
        return redirect("suppliers:supplier_request_list")

    if req.status != SupplierRequest.STATUS_ACCEPTED:
        messages.error(request, "Yêu cầu chưa được admin duyệt.")
        return redirect("suppliers:supplier_request_list")

    req.status = SupplierRequest.STATUS_COMPLETED
    req.completed_at = timezone.now()
    req.save()

    messages.success(request, "Bạn đã đánh dấu hoàn thành yêu cầu!")
    return redirect("suppliers:supplier_request_list")
