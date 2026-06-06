"""Views do núcleo — finas, delegam ao service."""
from __future__ import annotations

from django.views.generic import TemplateView


class AboutView(TemplateView):
    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        from apps.promotions.queries import CouponQuery

        context = super().get_context_data(**kwargs)

        coupons = []
        for c in CouponQuery.active():
            if c.discount_type == c.DiscountType.PERCENT:
                off = f"{c.value:.0f}% OFF"
            else:
                off = f"R$ {c.value:.0f} OFF"
            minv = f"mín. R$ {c.min_order:.0f}" if c.min_order and c.min_order > 0 else "sem valor mínimo"
            coupons.append({"code": c.code, "off": off, "min": minv})
        context["coupons"] = coupons
        return context
