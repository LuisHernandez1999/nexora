"""Mappers do painel do vendedor — Order -> dict para o template."""
from __future__ import annotations

from typing import Any

from apps.core.formatting import format_brl
from apps.core.layers import BaseMapper
from apps.orders.models import Order

# status do pedido -> tom do badge (classes .status-badge do tema)
STATUS_TONE = {
    Order.Status.PENDING: "warn",
    Order.Status.PAID: "info",
    Order.Status.PROCESSING: "accent",
    Order.Status.SHIPPED: "info",
    Order.Status.DELIVERED: "success",
    Order.Status.CANCELLED: "danger",
}

# etapas para a barra de rastreio
TRACK_STEPS = [
    (Order.Status.PAID, "Pago"),
    (Order.Status.PROCESSING, "Em produção"),
    (Order.Status.SHIPPED, "Enviado"),
    (Order.Status.DELIVERED, "Entregue"),
]
_STEP_ORDER = {s: i for i, (s, _) in enumerate(TRACK_STEPS)}


class OrderRowMapper(BaseMapper[Order]):
    @classmethod
    def to_dict(cls, instance: Order) -> dict[str, Any]:
        current = _STEP_ORDER.get(instance.status, -1)
        steps = [
            {"label": label, "done": i <= current and current >= 0}
            for i, (_, label) in enumerate(TRACK_STEPS)
        ]
        return {
            "number": instance.number,
            "customer": instance.recipient or instance.user.display_name,
            "status": instance.status,
            "status_label": instance.get_status_display(),
            "tone": STATUS_TONE.get(instance.status, "info"),
            "payment_label": instance.get_payment_method_display(),
            "total_display": format_brl(instance.total),
            "item_count": instance.item_count,
            "created_at": instance.created_at,
            "city": instance.city,
            "state": instance.state,
            "url": f"/pedidos/{instance.number}/",
            "steps": steps,
        }
