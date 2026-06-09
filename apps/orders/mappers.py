"""Mappers de pedido — Model -> dict para template."""
from __future__ import annotations

from typing import Any

from apps.core.formatting import format_brl

from .models import Order, OrderItem
from .payments import PaymentService

# status -> classe de badge (ver .status-badge no CSS)
STATUS_TONE = {
    Order.Status.PENDING: "warn",
    Order.Status.PAID: "info",
    Order.Status.PROCESSING: "info",
    Order.Status.SHIPPED: "accent",
    Order.Status.DELIVERED: "success",
    Order.Status.CANCELLED: "danger",
    Order.Status.ORCAMENTO: "warn",
}


class OrderItemMapper:
    @classmethod
    def to_dict(cls, item: OrderItem, *, reviewable: bool = False, reviewed_ids=frozenset()) -> dict[str, Any]:
        url = item.product.get_absolute_url() if item.product else None
        return {
            "name": item.product_name,
            "quantity": item.quantity,
            "unit_price_display": format_brl(item.unit_price),
            "line_total_display": format_brl(item.line_total),
            "url": url,
            "icon": item.product.category.icon if item.product else "box",
            "accent": item.product.category.accent if item.product else "#3b82f6",
            # avaliacao: so faz sentido se o produto ainda existe e o pedido foi pago
            "can_review": bool(reviewable and item.product_id),
            "reviewed": item.product_id in reviewed_ids,
            "review_url": f"{url}#avaliacoes" if url else None,
        }


class OrderMapper:
    @classmethod
    def to_dict(cls, order: Order, *, reviewed_ids=frozenset()) -> dict[str, Any]:
        reviewable = order.payment_status == Order.PaymentStatus.APPROVED
        return {
            "number": order.number,
            "created_at": order.created_at,
            "status": order.status,
            "status_label": order.get_status_display(),
            "status_tone": STATUS_TONE.get(order.status, "info"),
            "payment_label": order.get_payment_method_display(),
            "total_display": format_brl(order.total),
            "item_count": order.item_count,
            "url": f"/pedidos/{order.number}/",
            # itens avaliaveis (pedido pago, produto existente) — usado na lista "Meus pedidos"
            "review_items": [
                OrderItemMapper.to_dict(i, reviewable=reviewable, reviewed_ids=reviewed_ids)
                for i in order.items.all() if i.product_id
            ] if reviewable else [],
        }

    to_list = classmethod(
        lambda cls, qs, *, reviewed_ids=frozenset(): [cls.to_dict(o, reviewed_ids=reviewed_ids) for o in qs]
    )

    @classmethod
    def to_detail(cls, order: Order, *, reviewed_ids=frozenset()) -> dict[str, Any]:
        data = cls.to_dict(order, reviewed_ids=reviewed_ids)
        reviewable = order.payment_status == Order.PaymentStatus.APPROVED
        data.update({
            "items": [
                OrderItemMapper.to_dict(i, reviewable=reviewable, reviewed_ids=reviewed_ids)
                for i in order.items.all()
            ],
            "subtotal_display": format_brl(order.subtotal),
            "discount_display": format_brl(order.discount),
            "has_discount": order.discount > 0,
            "shipping_display": "Grátis" if order.shipping == 0 else format_brl(order.shipping),
            "coupon_code": order.coupon_code,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "payment_status_label": order.get_payment_status_display(),
            "paid_at": order.paid_at,
            "card_last4": order.card_last4,
            "shipping": {
                "recipient": order.recipient,
                "phone": order.phone,
                "line": order.shipping_line,
                "district": order.district,
                "city": order.city,
                "state": order.state,
                "zip_code": order.zip_code,
            },
            # artefatos de pagamento (fake) para a confirmação
            "pix_payload": PaymentService.pix_payload(order) if order.payment_method == Order.Payment.PIX else "",
            "boleto_line": PaymentService.boleto_line(order) if order.payment_method == Order.Payment.BOLETO else "",
        })
        return data
