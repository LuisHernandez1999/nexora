"""Serviços de pedido — orquestram carrinho, estoque, cupom e pagamento."""
from __future__ import annotations

from typing import Any

from django.db import transaction
from django.db.models import F

from apps.cart.services import CartService
from apps.catalog.models import Product
from apps.catalog.queries import ReviewQuery
from apps.core.layers import BaseService
from apps.promotions.models import Coupon

from .mappers import OrderMapper
from .models import Order, OrderItem
from .payments import PaymentService
from .queries import OrderQuery


class EmptyCartError(Exception):
    """Tentativa de fechar pedido com carrinho vazio."""


class OrderService(BaseService):
    @staticmethod
    @transaction.atomic
    def create_from_cart(request, data: dict) -> Order:
        cart = CartService.build(request)
        items = cart["items"]
        tem_orcamento = bool(request.cart.litho_draft_ids)
        if not items and not tem_orcamento:
            raise EmptyCartError()
        summary = cart["summary"]

        order = Order.objects.create(
            user=request.user,
            status=Order.Status.ORCAMENTO if tem_orcamento else Order.Status.PENDING,
            payment_method=data["payment_method"],
            card_last4=data.get("card_last4", ""),
            subtotal=summary["subtotal"],
            discount=summary["discount"],
            shipping=summary["shipping"],
            total=summary["total"],
            coupon_code=summary["coupon_code"] or "",
            recipient=data["recipient"],
            phone=data.get("phone", ""),
            zip_code=data["zip_code"],
            street=data["street"],
            number_addr=data["number_addr"],
            complement=data.get("complement", ""),
            district=data["district"],
            city=data["city"],
            state=data["state"].upper(),
        )

        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                product_id=line["id"],
                product_name=line["name"],
                unit_price=line["unit_price"],
                quantity=line["quantity"],
                line_total=line["line_total"],
            )
            for line in items
        ])

        # itens lithophane "a combinar" — snapshot (draft_id + specs), preço 0 (NOT NULL)
        if tem_orcamento:
            from decimal import Decimal
            from apps.lithophane.queries import LithophaneQuery  # import local anti-ciclo
            litho_drafts = LithophaneQuery.drafts_by_ids(request.cart.litho_draft_ids)
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=None,
                    product_name=f"Lithophane {d.get_format_display()} {d.size}mm",
                    unit_price=Decimal("0.00"),   # "a combinar"
                    quantity=1,
                    line_total=Decimal("0.00"),
                    draft_id=d.pk,
                    litho_specs={
                        "formato": d.format,
                        "largura_mm": float(d.size),
                        "espessura_max_mm": float(d.thickness),
                        "foto_url": d.image.url if d.image else "",
                    },
                )
                for d in litho_drafts
            ])

        # baixa de estoque + métrica de vendas (atômico via F)
        for line in items:
            Product.objects.filter(pk=line["id"]).update(
                stock=F("stock") - line["quantity"],
                sales_count=F("sales_count") + line["quantity"],
            )

        # consumo do cupom
        if order.coupon_code:
            Coupon.objects.filter(code=order.coupon_code).update(used_count=F("used_count") + 1)

        # cobrança (simulada) — orçamento não captura pagamento
        if not tem_orcamento:
            PaymentService.process(order)

        # esvazia o carrinho
        request.cart.clear()
        return order

    # ---- leitura ----
    @staticmethod
    def get_history(user) -> list[dict]:
        orders = list(OrderQuery.for_user(user))
        pids = {i.product_id for o in orders for i in o.items.all() if i.product_id}
        reviewed = ReviewQuery.reviewed_product_ids(user, pids)
        return OrderMapper.to_list(orders, reviewed_ids=reviewed)

    @staticmethod
    def get_detail(user, number: str) -> dict[str, Any] | None:
        order = OrderQuery.detail_for_user(user, number)
        if not order:
            return None
        pids = {i.product_id for i in order.items.all() if i.product_id}
        reviewed = ReviewQuery.reviewed_product_ids(user, pids)
        return OrderMapper.to_detail(order, reviewed_ids=reviewed)
