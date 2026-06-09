"""Views do carrinho — finas, delegam ao CartService."""
from __future__ import annotations

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .services import CartService


def _is_fetch(request) -> bool:
    return request.headers.get("X-Requested-With") == "fetch"


def detail(request):
    context = CartService.build(request)
    return render(request, "cart/detail.html", context)


@require_POST
def add(request, product_id: int):
    quantity = max(1, int(request.POST.get("quantity", 1) or 1))
    CartService.add(request, product_id, quantity)
    if _is_fetch(request):
        return JsonResponse({"ok": True, "cart_count": request.cart.total_quantity})
    messages.success(request, "Produto adicionado ao carrinho.")
    return redirect(request.META.get("HTTP_REFERER", "cart:detail"))


@require_POST
def update(request, product_id: int):
    quantity = int(request.POST.get("quantity", 1) or 1)
    CartService.update(request, product_id, quantity)
    if _is_fetch(request):
        data = CartService.build(request)
        return JsonResponse({"ok": True, "cart_count": request.cart.total_quantity,
                             "summary": data["summary"]["total_display"]})
    return redirect("cart:detail")


@require_POST
def remove(request, product_id: int):
    CartService.remove(request, product_id)
    if _is_fetch(request):
        return JsonResponse({"ok": True, "cart_count": request.cart.total_quantity})
    messages.info(request, "Item removido.")
    return redirect("cart:detail")


@require_POST
def add_litho(request, draft_id: int):
    request.cart.add_litho(draft_id)
    if _is_fetch(request):
        return JsonResponse({"ok": True})
    messages.success(request, "Lithophane adicionado ao carrinho.")
    return redirect("cart:detail")


@require_POST
def remove_litho(request, draft_id: int):
    request.cart.remove_litho(draft_id)
    messages.info(request, "Lithophane removido.")
    return redirect("cart:detail")


@require_POST
def apply_coupon(request):
    code = (request.POST.get("code") or "").strip()
    result = CartService.apply_coupon(request, code)
    if result["valid"]:
        messages.success(request, result["message"])
    else:
        messages.error(request, result["message"])
    return redirect("cart:detail")


@require_POST
def clear(request):
    request.cart.clear()
    messages.info(request, "Carrinho esvaziado.")
    return redirect("cart:detail")
