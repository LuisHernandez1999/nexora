"""Views do catálogo — finas, delegam ao CatalogService."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReviewForm
from .models import Product
from .services import CatalogService, ReviewService


def product_list(request):
    page = request.GET.get("page", 1)
    context = CatalogService.browse(request.GET, page=page)
    # AJAX (jQuery) -> devolve so o fragmento do grid, sem recarregar a pagina
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "catalog/partials/results.html", context)
    return render(request, "catalog/product_list.html", context)


def product_detail(request, slug):
    context = CatalogService.get_detail(slug, user=request.user)
    if context is None:
        raise Http404("Produto não encontrado.")
    if context["review_state"]["can_review"]:
        context["review_form"] = ReviewForm()
    return render(request, "catalog/product_detail.html", context)


@login_required
def review_create(request, product_id):
    product = get_object_or_404(Product.objects.active(), pk=product_id)
    if request.method != "POST":
        return redirect(product.get_absolute_url())
    form = ReviewForm(request.POST)
    if form.is_valid():
        ok, message = ReviewService.add(
            request.user, product,
            rating=form.cleaned_data["rating"],
            title=form.cleaned_data.get("title", ""),
            comment=form.cleaned_data.get("comment", ""),
        )
        messages.success(request, message) if ok else messages.error(request, message)
    else:
        messages.error(request, "Confira os campos da avaliação.")
    return redirect(product.get_absolute_url())
