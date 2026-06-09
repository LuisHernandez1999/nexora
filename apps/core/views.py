"""Views do núcleo — finas, delegam ao service."""
from __future__ import annotations

from django.views.generic import TemplateView


class AboutView(TemplateView):
    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        from apps.catalog.services import CatalogService

        context = super().get_context_data(**kwargs)
        # vitrine de produtos na home (conversão)
        context["featured"] = CatalogService.list_featured_products(8)
        context["new_arrivals"] = CatalogService.list_new_arrivals(4)
        context["home_categories"] = CatalogService.list_highlighted_categories()
        return context
