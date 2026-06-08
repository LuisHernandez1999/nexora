"""Consultas do painel do vendedor — só ORM."""
from __future__ import annotations

from apps.catalog.models import Product
from apps.core.layers import BaseQuery
from apps.orders.models import Order


class SellerQuery(BaseQuery):
    @staticmethod
    def products_for(user):
        return (
            Product.objects.filter(seller=user)
            .select_related("category")
            .prefetch_related("images")
            .order_by("-created_at")
        )

    @staticmethod
    def all_orders():
        return (
            Order.objects.select_related("user")
            .prefetch_related("items")
            .order_by("-created_at")
        )

    @staticmethod
    def shipments():
        """Pedidos relevantes para rastreio (em produção ou já enviados)."""
        return (
            Order.objects.select_related("user")
            .filter(status__in=[
                Order.Status.PROCESSING,
                Order.Status.SHIPPED,
                Order.Status.DELIVERED,
            ])
            .order_by("-created_at")
        )
