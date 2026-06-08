"""Consultas de promoções — ORM + cache."""
from __future__ import annotations

from apps.core import cache as cache_utils

from .models import Coupon, Offer, Promotion

NS_HERO = "promo:hero"
NS_ACTIVE = "promo:active"
NS_OFFERS = "promo:offers"


class PromotionQuery:
    @staticmethod
    def hero() -> Promotion | None:
        def producer():
            return Promotion.objects.live().filter(kind=Promotion.Kind.HERO).order_by("order").first()

        return cache_utils.get_or_set(NS_HERO, producer, bucket="long")

    @staticmethod
    def active(limit: int = 6) -> list[Promotion]:
        def producer():
            return list(Promotion.objects.live().order_by("order")[:limit])

        return cache_utils.get_or_set(
            cache_utils.build_key(NS_ACTIVE, limit), producer, bucket="long"
        )


class OfferQuery:
    """Ofertas reais (produto + valores). A API fatia por cursor; a home cacheia."""

    @staticmethod
    def api_queryset(category_slug: str | None = None):
        qs = Offer.objects.live().with_relations().order_by("-created_at")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs

    @staticmethod
    def featured(limit: int = 6) -> list[Offer]:
        def producer():
            return list(
                Offer.objects.live().with_relations().order_by("order", "-created_at")[:limit]
            )

        return cache_utils.get_or_set(
            cache_utils.build_key(NS_OFFERS, limit), producer, bucket="medium"
        )

    @staticmethod
    def for_seller(user):
        return (
            Offer.objects.filter(product__seller=user)
            .with_relations()
            .order_by("-created_at")
        )

    @staticmethod
    def live_count_for_product(product_id, exclude_pk=None) -> int:
        qs = Offer.objects.live().filter(product_id=product_id)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        return qs.count()


class CouponQuery:
    @staticmethod
    def by_code(code: str) -> Coupon | None:
        return Coupon.objects.filter(code__iexact=code.strip()).first()

    @staticmethod
    def active() -> list[Coupon]:
        from django.db.models import Q
        from django.utils import timezone

        now = timezone.now()
        return list(
            Coupon.objects.filter(is_active=True)
            .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=now))
            .order_by("min_order")
        )


def invalidate_promotion_cache() -> None:
    cache_utils.invalidate(
        NS_HERO,
        cache_utils.build_key(NS_ACTIVE, 3),
        cache_utils.build_key(NS_ACTIVE, 6),
        cache_utils.build_key(NS_ACTIVE, 12),
        cache_utils.build_key(NS_OFFERS, 6),
        cache_utils.build_key(NS_OFFERS, 9),
    )
