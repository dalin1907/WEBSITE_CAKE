from datetime import timedelta
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Sum, F, Q
from django.db.models.functions import TruncDate
from django.utils.timezone import now
from django.utils.dateparse import parse_date
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, UpdateView, CreateView, View
from django import forms
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from payments.models import Order
# Lưu ý: đảm bảo bạn đã thêm models Ingredient và InventoryTransaction trong dashboard.models
from .models import Ingredient, InventoryTransaction


@user_passes_test(lambda u: u.is_staff)
def order_statistics(request):
    """
    Dashboard order statistics with optional date range filtering via GET params:
      - start_date (YYYY-MM-DD)
      - end_date   (YYYY-MM-DD)

    If both are missing, defaults to last 7 days (inclusive).
    If start_date > end_date, they will be swapped automatically and a warning flag is set.
    """
    today = now().date()

    # Read date strings from GET params
    start_str = request.GET.get("start_date")
    end_str = request.GET.get("end_date")

    # Defaults
    default_end = today
    default_start = today - timedelta(days=6)

    # Parse provided dates (returns None if invalid)
    parsed_start = parse_date(start_str) if start_str else None
    parsed_end = parse_date(end_str) if end_str else None

    # Fallback to defaults if parsing failed or not provided
    if not parsed_start:
        parsed_start = default_start
    if not parsed_end:
        parsed_end = default_end

    # If start is after end, swap and flag it for the template
    range_swapped = False
    if parsed_start > parsed_end:
        parsed_start, parsed_end = parsed_end, parsed_start
        range_swapped = True

    # Base queryset filtered by selected date range (inclusive)
    base_qs = Order.objects.filter(
        created_at__date__gte=parsed_start, created_at__date__lte=parsed_end
    )

    # Aggregates and counts within the selected range
    total_orders = base_qs.count()
    paypal_orders = base_qs.filter(payment_method__iexact="paypal").count()
    cod_orders = base_qs.filter(payment_method__iexact="cod").count()
    total_revenue = base_qs.aggregate(Sum("total_amount"))["total_amount__sum"] or 0

    # Chart: counts per day in the range
    qs = (
        base_qs.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    counts_by_day = {item["day"]: item["count"] for item in qs}

    # Build labels and counts for each day in the inclusive range
    num_days = (parsed_end - parsed_start).days + 1
    labels = []
    counts = []
    for i in range(num_days):
        d = parsed_start + timedelta(days=i)
        labels.append(d.strftime("%d-%m"))
        counts.append(counts_by_day.get(d, 0))

    chart_data = {"labels": labels, "counts": counts}

    # Latest orders in range (limit 5)
    latest_orders = base_qs.order_by("-created_at")[:5]

    context = {
        "total_orders": total_orders,
        "paypal_orders": paypal_orders,
        "cod_orders": cod_orders,
        "total_revenue": total_revenue,
        "chart_data": chart_data,
        "latest_orders": latest_orders,
        # For template form prefills and messages
        "start_date_str": parsed_start.isoformat(),
        "end_date_str": parsed_end.isoformat(),
        "range_swapped": range_swapped,
    }

    return render(request, "dashboard/order_statistics.html", context)


# -------------------------
# Inventory: forms (gộp vào views.py)
# -------------------------
class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = ['name', 'unit', 'quantity', 'min_quantity', 'description']


class InventoryTransactionForm(forms.ModelForm):
    class Meta:
        model = InventoryTransaction
        fields = ['transaction_type', 'change', 'note']

    def clean_change(self):
        change = self.cleaned_data.get('change')
        if change == 0:
            raise forms.ValidationError("Số lượng thay đổi phải khác 0.")
        return change


# -------------------------
# Inventory: class-based views
# -------------------------
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        # Bạn có thể redirect tới login hoặc trang error tuỳ nhu cầu
        return redirect(reverse_lazy('admin:login'))


class InventoryListView(StaffRequiredMixin, ListView):
    model = Ingredient
    template_name = 'dashboard/inventory_list.html'
    context_object_name = 'ingredients'
    paginate_by = None  # đặt số nếu muốn phân trang

    def get_queryset(self):
        q = self.request.GET.get('q', '').strip()
        qs = Ingredient.objects.all()
        if q:
            qs = qs.filter(Q(name__icontains=q))
        return qs.order_by('name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '').strip()
        ctx['low_stock_count'] = Ingredient.objects.filter(quantity__lte=F('min_quantity')).count()
        return ctx


class IngredientCreateView(StaffRequiredMixin, CreateView):
    model = Ingredient
    form_class = IngredientForm
    template_name = 'dashboard/ingredient_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['creating'] = True
        ctx['tx_form'] = InventoryTransactionForm()
        return ctx

    def form_valid(self, form):
        ingredient = form.save()
        messages.success(self.request, 'Đã thêm nguyên liệu mới.')
        return redirect('ingredient_detail', pk=ingredient.pk)


class IngredientUpdateView(StaffRequiredMixin, UpdateView):
    model = Ingredient
    form_class = IngredientForm
    template_name = 'dashboard/ingredient_detail.html'
    context_object_name = 'ingredient'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tx_form'] = InventoryTransactionForm()
        ctx['transactions'] = self.object.transactions.all()[:20]
        ctx['creating'] = False
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Thông tin nguyên liệu đã được cập nhật.')
        return response

    def get_success_url(self):
        return reverse('ingredient_detail', kwargs={'pk': self.object.pk})


class InventoryTransactionCreateView(StaffRequiredMixin, View):
    """
    Xử lý POST giao dịch nhập/xuất/điều chỉnh cho một nguyên liệu.
    URL: /inventory/<pk>/transaction/ (POST)
    """
    def post(self, request, pk):
        ingredient = get_object_or_404(Ingredient, pk=pk)
        form = InventoryTransactionForm(request.POST)
        if not form.is_valid():
            # Bạn có thể muốn hiển thị lỗi cụ thể trong template; ở đây ta set message và redirect
            messages.error(request, 'Dữ liệu giao dịch không hợp lệ.')
            return redirect('ingredient_detail', pk=pk)

        tx = form.save(commit=False)
        tx.ingredient = ingredient

        with transaction.atomic():
            # Convention: OUT -> subtract; IN/ADJ -> add
            if tx.transaction_type == 'OUT' and tx.change > 0:
                tx.change = -tx.change

            new_quantity = ingredient.quantity + tx.change
            if new_quantity < 0:
                messages.error(request, 'Không thể làm cho tồn kho âm. Kiểm tra lại số lượng.')
                return redirect('ingredient_detail', pk=pk)

            tx.created_at = timezone.now()
            tx.save()
            ingredient.quantity = new_quantity
            ingredient.save()

        messages.success(request, 'Giao dịch kho đã được lưu.')
        return redirect('ingredient_detail', pk=pk)