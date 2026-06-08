"""Serializers DRF do catálogo (saida da API, camelCase pelo renderer global)."""
from __future__ import annotations

from rest_framework import serializers

from apps.core.formatting import format_brl

from .models import Category, Product, Review


class CategoryCompactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "icon", "accent")


class ProductListSerializer(serializers.ModelSerializer):
    """Card de produto para listas cursor-paginadas: imagem, descricao e valor."""

    category = CategoryCompactSerializer(read_only=True)
    cover_image = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    old_price_display = serializers.SerializerMethodField()
    discount_pct = serializers.IntegerField(read_only=True)
    has_discount = serializers.BooleanField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    url = serializers.CharField(source="get_absolute_url", read_only=True)
    short_description = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "name", "slug", "short_description", "price", "price_display",
            "compare_at_price", "old_price_display", "cover_image", "rating",
            "review_count", "is_on_promotion", "discount_pct", "has_discount",
            "in_stock", "category", "url",
        )

    def get_cover_image(self, obj: Product) -> str:
        gallery = list(obj.images.all())
        if gallery:
            return gallery[0].url
        if obj.image:
            return obj.image.url
        return obj.image_url or ""

    def get_short_description(self, obj: Product) -> str:
        text = obj.description or ""
        return text if len(text) <= 140 else text[:137].rstrip() + "…"

    def get_price_display(self, obj: Product) -> str:
        return format_brl(obj.price)

    def get_old_price_display(self, obj: Product) -> str:
        return format_brl(obj.compare_at_price) if obj.has_discount else ""


class ReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ("id", "author_name", "rating", "title", "comment", "created_at")

    def get_author_name(self, obj: Review) -> str:
        return obj.author.display_name if obj.author_id else "Cliente"
