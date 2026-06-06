"""Serviços do catálogo — orquestram queries + mappers para as views."""
from __future__ import annotations

from typing import Any

from django.core.paginator import Paginator

from apps.core.layers import BaseService

from .mappers import CategoryMapper, ProductMapper
from .queries import CategoryQuery, ProductQuery

PAGE_SIZE = 12


class CatalogService(BaseService):
    # ---- home ----
    @staticmethod
    def list_highlighted_categories() -> list[dict]:
        return CategoryMapper.to_list(CategoryQuery.highlighted())

    @staticmethod
    def list_featured_products(limit: int = 8) -> list[dict]:
        return ProductMapper.to_list(ProductQuery.featured(limit))

    @staticmethod
    def list_new_arrivals(limit: int = 4) -> list[dict]:
        return ProductMapper.to_list(ProductQuery.new_arrivals(limit))

    @staticmethod
    def list_on_sale(limit: int = 8) -> list[dict]:
        return ProductMapper.to_list(ProductQuery.on_sale(limit))

    # ---- catálogo (listagem com filtros + paginação) ----
    @staticmethod
    def browse(params, page: int = 1) -> dict[str, Any]:
        category_slug = params.get("categoria") or None
        query = params.get("q") or None
        sort = params.get("sort") or "relevance"
        min_price = _to_decimal(params.get("min"))
        max_price = _to_decimal(params.get("max"))

        qs = ProductQuery.search(
            category_slug=category_slug,
            query=query,
            sort=sort,
            min_price=min_price,
            max_price=max_price,
        )
        paginator = Paginator(qs, PAGE_SIZE)
        page_obj = paginator.get_page(page)

        active_category = None
        if category_slug:
            cat = CategoryQuery.by_slug(category_slug)
            active_category = CategoryMapper.to_dict(cat) if cat else None

        from apps.promotions.services import PromotionService

        return {
            "products": ProductMapper.to_list(page_obj.object_list),
            "page_obj": page_obj,
            "paginator": paginator,
            "total": paginator.count,
            "categories": CategoryMapper.to_list(CategoryQuery.all_with_counts()),
            "active_category": active_category,
            "current_sort": sort,
            "query": query or "",
            "promotions": PromotionService.list_active_promotions(limit=5),
            "flash_sale": ProductMapper.to_list(ProductQuery.on_sale(8)),
            "best_sellers": ProductMapper.to_list(ProductQuery.featured(6)),
        }

    # ---- detalhe ----
    @staticmethod
    def get_detail(slug: str) -> dict[str, Any] | None:
        product = ProductQuery.detail_by_slug(slug)
        if not product:
            return None
        return {
            "product": ProductMapper.to_detail(product),
            "related": ProductMapper.to_list(ProductQuery.related(product)),
        }


def _to_decimal(value):
    if not value:
        return None
    try:
        from decimal import Decimal

        return Decimal(str(value).replace(",", "."))
    except (ValueError, ArithmeticError):
        return None
