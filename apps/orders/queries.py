"""Consultas de pedidos — só ORM, com prefetch dos itens."""
from __future__ import annotations

from .models import Order


class OrderQuery:
    @staticmethod
    def for_user(user):
        return (
            Order.objects.filter(user=user)
            .prefetch_related("items__product__category")
            .order_by("-created_at")
        )

    @staticmethod
    def detail_for_user(user, number: str) -> Order | None:
        return (
            Order.objects.filter(user=user, number=number)
            .prefetch_related("items__product__category")
            .first()
        )
