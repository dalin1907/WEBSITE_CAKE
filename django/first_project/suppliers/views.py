from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.db import transaction
from django.conf import settings
from dashboard.models import Ingredient
from .models import (
    OrderRequest,
    SupplierProposal,
    Delivery,
    InventoryItem,
    WarehouseReceipt,
    SupplierProfile,
)

from .forms import (
    SupplierProposalForm,
    DeliveryForm,
    SupplierProfileForm,
    AdminOrderRequestForm,
)

# =====================================================
# SUPPLIER VIEWS
# =====================================================

@login_required
def requests_list(request):
    """
    Supplier xem các yêu cầu do ADMIN tạo
    """
    qs = OrderRequest.objects.filter(status=OrderRequest.Status.OPEN)
    return render(request, "suppliers/requests_list.html", {"requests": qs})


@login_required
def request_detail(request, pk):
    order = get_object_or_404(OrderRequest, pk=pk)
    existing_proposal = SupplierProposal.objects.filter(
        order_request=order,
        supplier=request.user
    ).first()

    return render(
        request,
        "suppliers/request_detail.html",
        {
            "order": order,
            "existing_proposal": existing_proposal,
        },
    )


@login_required
def apply_request(request, pk):
    """
    Supplier gửi đề xuất cung cấp
    """
    order = get_object_or_404(
        OrderRequest,
        pk=pk,
        status=OrderRequest.Status.OPEN
    )

    # Không cho apply 2 lần
    if SupplierProposal.objects.filter(order_request=order, supplier=request.user).exists():
        messages.warning(request, "Bạn đã gửi đề xuất cho yêu cầu này.")
        return redirect("suppliers:request_detail", pk=pk)

    if request.method == "POST":
        form = SupplierProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.order_request = order
            proposal.supplier = request.user
            proposal.status = SupplierProposal.Status.PENDING
            proposal.save()

            # Gửi mail admin (nếu có cấu hình)
            try:
                send_mail(
                    subject=f"Supplier apply cho yêu cầu #{order.pk}",
                    message=f"{request.user.username} đã gửi đề xuất.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.EMAIL_HOST_USER],
                    fail_silently=True,
                )
            except Exception:
                pass

            messages.success(request, "Đã gửi đề xuất, vui lòng chờ admin duyệt.")
            return redirect("suppliers:requests_list")
    else:
        form = SupplierProposalForm()

    return render(
        request,
        "suppliers/apply_request.html",
        {"form": form, "order": order},
    )


@login_required
def supplier_create_delivery(request, pk):
    """
    Supplier giao hàng sau khi proposal được duyệt
    """
    order = get_object_or_404(OrderRequest, pk=pk)

    approved = SupplierProposal.objects.filter(
        order_request=order,
        supplier=request.user,
        status=SupplierProposal.Status.APPROVED
    ).exists()

    if not approved:
        messages.error(request, "Bạn chưa được duyệt để giao hàng.")
        return redirect("suppliers:request_detail", pk=pk)

    if request.method == "POST":
        form = DeliveryForm(request.POST, request.FILES)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.order_request = order
            delivery.supplier = request.user
            delivery.save()

            order.status = OrderRequest.Status.IN_DELIVERY
            order.save()

            messages.success(request, "Đã gửi thông tin giao hàng.")
            return redirect("suppliers:request_detail", pk=pk)
    else:
        form = DeliveryForm()

    return render(
        request,
        "suppliers/supplier_delivery.html",
        {"form": form, "order": order},
    )



@login_required
def supplier_claimed_list(request):
    """
    Supplier xem các yêu cầu mình đã apply
    """
    claimed_requests = OrderRequest.objects.filter(
        proposals__supplier=request.user
    ).distinct()

    # Debugging
    print("Claimed Requests Count:", claimed_requests.count())
    for order in claimed_requests:
        print(order.title)  # In tên các OrderRequest

    return render(
        request,
        "suppliers/claimed_list.html",
        {
            "claimed_requests": claimed_requests,
            "is_admin_view": False,
        },
    )


@login_required
def supplier_register(request):
    """
    Tạo hồ sơ nhà cung cấp
    """
    if request.method == "POST":
        form = SupplierProfileForm(request.POST)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Đăng ký nhà cung cấp thành công.")
            return redirect("home:index")
    else:
        form = SupplierProfileForm()

    return render(
        request,
        "suppliers/supplier_register.html",
        {"form": form},
    )

# =====================================================
# ADMIN VIEWS
# =====================================================

@login_required
@staff_member_required
def admin_order_request_create(request):
    ingredient_id = request.GET.get("ingredient")
    ingredient = get_object_or_404(
        Ingredient,
        pk=ingredient_id
    )

    if request.method == "POST":
        form = AdminOrderRequestForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)

            # GÁN NGHIỆP VỤ
            order.created_by = request.user
            order.status = OrderRequest.Status.OPEN

            # LẤY TÊN + ĐƠN VỊ TỪ INGREDIENT
            order.title = ingredient.name
            order.unit = ingredient.unit

            order.save()
            messages.success(request, "Đã tạo yêu cầu cung cấp.")
            return redirect('suppliers:requests_list')
    else:
        form = AdminOrderRequestForm(
            initial={"ingredient": ingredient}
        )

    return render(
        request,
        "suppliers/admin_request_form.html",
        {
            "form": form,
            "ingredient": ingredient,
        },
    )


@staff_member_required
def proposals_admin_list(request):
    qs = SupplierProposal.objects.filter(
        status=SupplierProposal.Status.PENDING
    ).select_related("supplier", "order_request")

    return render(
        request,
        "suppliers/proposals_admin_list.html",
        {"proposals": qs},
    )


@staff_member_required
def proposal_detail_admin(request, proposal_id):
    proposal = get_object_or_404(SupplierProposal, pk=proposal_id)
    return render(
        request,
        "suppliers/proposal_detail_admin.html",
        {"proposal": proposal},
    )


@staff_member_required
def proposal_approve(request, proposal_id):
    proposal = get_object_or_404(SupplierProposal, pk=proposal_id)

    if request.method == "POST":
        with transaction.atomic():
            proposal.status = SupplierProposal.Status.APPROVED
            proposal.save()

            order = proposal.order_request
            order.status = OrderRequest.Status.SELECTED
            order.save()

        messages.success(request, "Đã duyệt đề xuất.")
    return redirect("suppliers:proposals_admin_list")


@staff_member_required
def proposal_reject(request, proposal_id):
    proposal = get_object_or_404(SupplierProposal, pk=proposal_id)

    if request.method == "POST":
        proposal.status = SupplierProposal.Status.REJECTED
        proposal.save()
        messages.info(request, "Đã từ chối đề xuất.")

    return redirect("suppliers:proposals_admin_list")


@staff_member_required
def admin_confirm_delivery(request, delivery_id):
    delivery = get_object_or_404(Delivery, pk=delivery_id)
    order = delivery.order_request

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "confirm":
            with transaction.atomic():
                order.status = OrderRequest.Status.COMPLETED
                order.save()

                item, _ = InventoryItem.objects.get_or_create(
                    name=order.title,
                    defaults={"unit": order.unit},
                )
                item.quantity += order.quantity
                item.save()

                WarehouseReceipt.objects.create(
                    order_request=order,
                    created_by=request.user,
                    note=f"Tạo từ delivery #{delivery.pk}",
                )

            messages.success(request, "Đã xác nhận giao hàng.")
        else:
            order.status = OrderRequest.Status.DELIVERY_REJECTED
            order.save()
            messages.warning(request, "Đã từ chối giao hàng.")

        return redirect("admin:index")

    return render(
        request,
        "suppliers/admin_confirm_delivery.html",
        {
            "delivery": delivery,
            "order": order,
        },
    )
