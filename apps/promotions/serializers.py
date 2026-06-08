"""Serializers de promoções."""
from __future__ import annotations

from rest_framework import serializers

from apps.core.formatting import format_brl

from .mappers import _product_cover, _short
from .models import Coupon, Offer, Promotion


class OfferSerializer(serializers.ModelSerializer):
    """Saida da API de ofertas reais (cursor): imagem, descricao e valores."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    accent = serializers.CharField(source="category.accent", read_only=True)
    cover_image = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    original_display = serializers.SerializerMethodField()
    promo_display = serializers.SerializerMethodField()
    discount_pct = serializers.IntegerField(read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = (
            "id", "product_name", "product_slug", "category_name", "category_slug",
            "accent", "cover_image", "description", "original_price", "promo_price",
            "original_display", "promo_display", "discount_pct", "url",
        )

    def get_cover_image(self, obj: Offer) -> str:
        return _product_cover(obj.product)

    def get_description(self, obj: Offer) -> str:
        return _short(obj.product.description)

    def get_original_display(self, obj: Offer) -> str:
        return format_brl(obj.original_price)

    def get_promo_display(self, obj: Offer) -> str:
        return format_brl(obj.promo_price)

    def get_url(self, obj: Offer) -> str:
        return obj.product.get_absolute_url()


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = ("id", "kind", "title", "subtitle", "badge", "cta_label", "cta_url", "image", "ends_at")


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ("code", "discount_type", "value", "min_order", "valid_until")
