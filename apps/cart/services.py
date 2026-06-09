"""Serviços do carrinho — orquestram sessão + catálogo + cupons."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from apps.core.layers import BaseService
from apps.promotions.services import CouponService

from .mappers import CartItemMapper, CartSummaryMapper
from .queries import CartQuery

FREE_SHIPPING_THRESHOLD = Decimal("199.00")
DEFAULT_SHIPPING = Decimal("24.90")


class CartService(BaseService):
    # ---- mutações (delegam ao SessionCart e validam estoque) ----
    @staticmethod
    def add(request, product_id: int, quantity: int = 1) -> None:
        request.cart.add(product_id, quantity)

    @staticmethod
    def update(request, product_id: int, quantity: int) -> None:
        request.cart.set_quantity(product_id, quantity)

    @staticmethod
    def remove(request, product_id: int) -> None:
        request.cart.remove(product_id)

    @staticmethod
    def apply_coupon(request, code: str) -> dict:
        snapshot = CartService.build(request)
        result = CouponService.validate(code, snapshot["summary"]["subtotal"])
        request.cart.set_coupon(result["code"] if result["valid"] else None)
        return result

    @staticmethod
    def clear_coupon(request) -> None:
        request.cart.set_coupon(None)

    # ---- leitura (monta o contexto completo) ----
    @staticmethod
    def build(request) -> dict[str, Any]:
        raw = request.cart.raw_items()
        products = CartQuery.products_by_ids(raw.keys())

        lines: list[dict] = []
        subtotal = Decimal("0")
        # itens órfãos (produto removido/inativo) são descartados silenciosamente
        for pid_str, qty in raw.items():
            product = products.get(int(pid_str))
            if not product:
                continue
            qty = min(qty, product.stock) if product.stock else qty
            line = CartItemMapper.to_line(product, qty)
            subtotal += line["line_total"]
            lines.append(line)

        discount = Decimal("0")
        coupon_code = request.cart.coupon_code
        if coupon_code:
            result = CouponService.validate(coupon_code, subtotal)
            if result["valid"]:
                discount = result["discount"]
            else:
                coupon_code = None  # cupom deixou de valer

        shipping = Decimal("0") if (subtotal - discount) >= FREE_SHIPPING_THRESHOLD or not lines else DEFAULT_SHIPPING

        summary = CartSummaryMapper.to_summary(
            subtotal=subtotal,
            discount=discount,
            shipping=shipping,
            coupon_code=coupon_code,
            count=request.cart.total_quantity,
        )
        summary["free_shipping_threshold"] = FREE_SHIPPING_THRESHOLD
        summary["missing_for_free_shipping"] = max(Decimal("0"), FREE_SHIPPING_THRESHOLD - (subtotal - discount))

        # itens lithophane "a combinar" — chave de sessão separada, NÃO entram no total
        from apps.lithophane.queries import LithophaneQuery  # import local (evita ciclo)
        litho_items = [
            {
                "draft_id": d.pk,
                "name": f"Lithophane {d.get_format_display()} {d.size}mm",
                "format": d.format,
                "image_url": d.image.url if d.image else "",
                "price_display": "A combinar",
            }
            for d in LithophaneQuery.drafts_by_ids(request.cart.litho_draft_ids)
        ]
        return {"items": lines, "litho_items": litho_items, "summary": summary}
