"""API DRF do catálogo — listagens cursor-paginadas e otimizadas."""
from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView

from apps.core.pagination import NexoraCursorPagination, ReviewCursorPagination

from .models import Product
from .queries import ProductQuery, ReviewQuery
from .serializers import ProductListSerializer, ReviewSerializer

_BOOL = {"true": True, "1": True, "false": False, "0": False}


class ProductListAPI(ListAPIView):
    """GET /api/produtos/?cursor=&category=&onPromotion=true"""

    serializer_class = ProductListSerializer
    pagination_class = NexoraCursorPagination

    def get_queryset(self):
        params = self.request.query_params
        on_promo = params.get("onPromotion")
        return ProductQuery.api_queryset(
            category_slug=params.get("category"),
            on_promotion=_BOOL.get((on_promo or "").lower()) if on_promo else None,
        )


class ProductReviewListAPI(ListAPIView):
    """GET /api/produtos/<slug>/avaliacoes/?cursor= — avaliacoes paginadas."""

    serializer_class = ReviewSerializer
    pagination_class = ReviewCursorPagination

    def get_queryset(self):
        product = get_object_or_404(Product.objects.active(), slug=self.kwargs["slug"])
        return ReviewQuery.for_product(product)
