"""Mappers de promoções."""
from __future__ import annotations

from typing import Any

from apps.core.formatting import format_brl
from apps.core.layers import BaseMapper

from .models import Offer, Promotion


def _product_cover(product) -> str:
    gallery = list(product.images.all())  # prefetched em Offer.with_relations
    if gallery:
        return gallery[0].url
    if product.image:
        return product.image.url
    return product.image_url or ""


def _short(text: str, limit: int = 130) -> str:
    text = text or ""
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


class OfferMapper(BaseMapper[Offer]):
    """Card de oferta real: imagem, descricao e valores (original x promo)."""

    @classmethod
    def to_dict(cls, instance: Offer) -> dict[str, Any]:
        product = instance.product
        return {
            "id": instance.id,
            "product_name": product.name,
            "product_slug": product.slug,
            "category_name": instance.category.name,
            "category_slug": instance.category.slug,
            "icon": instance.category.icon,
            "accent": instance.category.accent,
            "monogram": product.name[:1].upper(),
            "image_url": _product_cover(product),
            "description": _short(product.description),
            "original_price": instance.original_price,
            "promo_price": instance.promo_price,
            "original_display": format_brl(instance.original_price),
            "promo_display": format_brl(instance.promo_price),
            "discount_pct": instance.discount_pct,
            "savings_display": format_brl(instance.savings),
            "url": product.get_absolute_url(),
        }


class PromotionMapper(BaseMapper[Promotion]):
    @classmethod
    def to_dict(cls, instance: Promotion) -> dict[str, Any]:
        return {
            "kind": instance.kind,
            "title": instance.title,
            "subtitle": instance.subtitle,
            "badge": instance.badge,
            "cta_label": instance.cta_label,
            "cta_url": instance.cta_url,
            "image_url": instance.image.url if instance.image else (instance.image_url or ""),
            "ends_at": instance.ends_at,
        }
