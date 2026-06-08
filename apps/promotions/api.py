"""API DRF de promoções — ofertas reais cursor-paginadas."""
from __future__ import annotations

from rest_framework.generics import ListAPIView

from apps.core.pagination import OfferCursorPagination

from .queries import OfferQuery
from .serializers import OfferSerializer


class OfferListAPI(ListAPIView):
    """GET /api/ofertas/?cursor=&category= — ofertas reais ativas, otimizadas."""

    serializer_class = OfferSerializer
    pagination_class = OfferCursorPagination

    def get_queryset(self):
        return OfferQuery.api_queryset(
            category_slug=self.request.query_params.get("category")
        )
