from datetime import timedelta
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils.timezone import now

from payments.models import Order


@user_passes_test(lambda u: u.is_staff)
def order_statistics(request):

    total_orders = Order.objects.count()


    paypal_orders = Order.objects.filter(payment_method__iexact="paypal").count()
    cod_orders = Order.objects.filter(payment_method__iexact="cod").count()


    total_revenue = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0


    today = now().date()
    start_date = today - timedelta(days=6)

    qs = (
        Order.objects
        .filter(created_at__date__gte=start_date)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )


    counts_by_day = {item["day"]: item["count"] for item in qs}

    labels = []
    counts = []
    for i in range(7):
        d = start_date + timedelta(days=i)
        labels.append(d.strftime("%d-%m"))
        counts.append(counts_by_day.get(d, 0))

    chart_data = {"labels": labels, "counts": counts}


    latest_orders = Order.objects.order_by("-created_at")[:5]

    context = {
        "total_orders": total_orders,
        "paypal_orders": paypal_orders,
        "cod_orders": cod_orders,
        "total_revenue": total_revenue,
        "chart_data": chart_data,
        "latest_orders": latest_orders,
    }

    return render(request, "dashboard/order_statistics.html", context)