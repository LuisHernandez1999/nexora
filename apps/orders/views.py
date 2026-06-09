"""Views de pedido — checkout, confirmação, histórico e detalhe."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render

from apps.accounts.queries import AddressQuery
from apps.cart.services import CartService

from .forms import CheckoutForm
from .services import EmptyCartError, OrderService


@login_required
def checkout(request):
    cart = CartService.build(request)
    if not cart["items"] and not cart.get("litho_items"):
        messages.info(request, "Seu carrinho está vazio.")
        return redirect("cart:detail")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = OrderService.create_from_cart(request, form.to_order_data())
            except EmptyCartError:
                messages.error(request, "Seu carrinho está vazio.")
                return redirect("cart:detail")
            messages.success(request, f"Pedido {order.number} criado com sucesso!")
            return redirect("orders:confirmation", number=order.number)
    else:
        form = CheckoutForm(initial=_initial_from_address(request.user))

    return render(request, "orders/checkout.html", {
        "form": form, "summary": cart["summary"], "items": cart["items"],
        "litho_items": cart.get("litho_items", []),
    })


@login_required
def confirmation(request, number):
    detail = OrderService.get_detail(request.user, number)
    if not detail:
        raise Http404("Pedido não encontrado.")
    return render(request, "orders/confirmation.html", {"order": detail})


@login_required
def order_list(request):
    return render(request, "orders/list.html", {"orders": OrderService.get_history(request.user)})


@login_required
def order_detail(request, number):
    detail = OrderService.get_detail(request.user, number)
    if not detail:
        raise Http404("Pedido não encontrado.")
    return render(request, "orders/detail.html", {"order": detail})


def _initial_from_address(user) -> dict:
    addr = AddressQuery.default_for_user(user)
    base = {"recipient": user.get_full_name() or user.display_name, "phone": user.phone}
    if addr:
        base.update({
            "recipient": addr.recipient, "zip_code": addr.zip_code, "street": addr.street,
            "number_addr": addr.number, "complement": addr.complement, "district": addr.district,
            "city": addr.city, "state": addr.state,
        })
    return base
