"""Views do painel do vendedor — finas, gated por papel, delegam ao service."""
from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render

from apps.catalog.forms import ProductForm
from apps.catalog.queries import ProductQuery
from apps.catalog.services import ProductWriteService
from apps.promotions.forms import OfferForm
from apps.promotions.services import OfferService

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
def product_new(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = ProductWriteService.create(
                request.user, form,
                files=request.FILES.getlist("photos"),
                image_urls=request.POST.getlist("photo_url"),
            )
            messages.success(request, f"Produto “{product.name}” cadastrado!")
            return redirect("seller:products")
    else:
        form = ProductForm()
    return render(request, "seller/product_form.html", {
        "form": form, "mode": "create",
        "metrics": SellerService.metrics(request.user),
    })


@seller_required
def product_edit(request, pk):
    product = ProductQuery.owned_by(request.user, pk)
    if not product:
        raise Http404("Produto não encontrado.")
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            ProductWriteService.update(
                product, form,
                files=request.FILES.getlist("photos"),
                image_urls=request.POST.getlist("photo_url"),
            )
            messages.success(request, "Produto atualizado.")
            return redirect("seller:products")
    else:
        form = ProductForm(instance=product)
    return render(request, "seller/product_form.html", {
        "form": form, "mode": "edit", "product": product,
        "gallery": list(product.images.all()),
        "metrics": SellerService.metrics(request.user),
    })


@seller_required
def offers(request):
    if request.method == "POST":
        form = OfferForm(request.POST, seller=request.user)
        if form.is_valid():
            offer, message = OfferService.create(
                request.user,
                product=form.cleaned_data["product"],
                original_price=form.cleaned_data["original_price"],
                promo_price=form.cleaned_data["promo_price"],
            )
            messages.success(request, message) if offer else messages.error(request, message)
            return redirect("seller:offers")
    else:
        form = OfferForm(seller=request.user)
    return render(request, "seller/offers.html", {
        "form": form,
        "offers": OfferService.list_for_seller(request.user),
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
