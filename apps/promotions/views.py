"""Views de promoções."""
from __future__ import annotations

from django.shortcuts import render

from .services import PromotionService


def promotion_list(request):
    from apps.catalog.services import CatalogService

    from .queries import CouponQuery

    coupons = []
    for c in CouponQuery.active():
        if c.discount_type == c.DiscountType.PERCENT:
            off = f"{c.value:.0f}% OFF"
        else:
            off = f"R$ {c.value:.0f} OFF"
        minv = f"mín. R$ {c.min_order:.0f}" if c.min_order and c.min_order > 0 else "sem mínimo"
        coupons.append({"code": c.code, "off": off, "min": minv})

    context = {
        "promotions": PromotionService.list_active_promotions(limit=12),
        "on_sale": CatalogService.list_on_sale(limit=8),
        "categories": CatalogService.list_highlighted_categories(),
        "best_sellers": CatalogService.list_featured_products(limit=6),
        "coupons": coupons,
    }
    return render(request, "promotions/list.html", context)
