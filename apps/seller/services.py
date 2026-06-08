"""Serviços do painel do vendedor — orquestram queries + mappers."""
from __future__ import annotations

from apps.catalog.mappers import ProductMapper
from apps.core.layers import BaseService

from .mappers import OrderRowMapper
from .queries import SellerQuery


class SellerService(BaseService):
    @staticmethod
    def products(user) -> list[dict]:
        return [ProductMapper.to_seller_row(p) for p in SellerQuery.products_for(user)]

    @staticmethod
    def orders() -> list[dict]:
        return OrderRowMapper.to_list(SellerQuery.all_orders())

    @staticmethod
    def shipments() -> list[dict]:
        return OrderRowMapper.to_list(SellerQuery.shipments())

    @staticmethod
    def metrics(user) -> dict:
        orders = SellerQuery.all_orders()
        return {
            "products": SellerQuery.products_for(user).count(),
            "orders": orders.count(),
            "to_ship": SellerQuery.shipments().count(),
        }
