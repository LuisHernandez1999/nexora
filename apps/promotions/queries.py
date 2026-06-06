"""Consultas de promoções — ORM + cache."""
from __future__ import annotations

from apps.core import cache as cache_utils

from .models import Coupon, Promotion

NS_HERO = "promo:hero"
NS_ACTIVE = "promo:active"


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
    )
