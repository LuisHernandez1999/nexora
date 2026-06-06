"""Views do painel do vendedor — finas, gated por papel, delegam ao service."""
from __future__ import annotations

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .services import SellerService


def seller_required(view):
    """Exige login E papel de vendedor; senão manda pra landing."""

    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not getattr(request.user, "is_seller", False):
            return redirect("core:home")
        return view(request, *args, **kwargs)

    return wrapper


@seller_required
def products(request):
    return render(request, "seller/products.html", {
        "products": SellerService.products(request.user),
        "metrics": SellerService.metrics(request.user),
    })


@seller_required
def orders(request):
    return render(request, "seller/orders.html", {
        "orders": SellerService.orders(),
        "metrics": SellerService.metrics(request.user),
    })


@seller_required
def tracking(request):
    return render(request, "seller/tracking.html", {
        "orders": SellerService.shipments(),
        "metrics": SellerService.metrics(request.user),
    })
