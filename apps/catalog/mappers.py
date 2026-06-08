"""Mappers do catálogo — Model -> dict para template/serializer."""
from __future__ import annotations

from typing import Any

from apps.core.formatting import format_brl
from apps.core.layers import BaseMapper

from .models import Category, Product, ProductImage, Review


class CategoryMapper(BaseMapper[Category]):
    @classmethod
    def to_dict(cls, instance: Category) -> dict[str, Any]:
        count = getattr(instance, "num_products", None)
        if count is None:
            count = instance.products.filter(is_active=True).count()
        return {
            "name": instance.name,
            "slug": instance.slug,
            "icon": instance.icon,
            "accent": instance.accent,
            "product_count": count,
            "url": instance.get_absolute_url(),
        }


class ProductImageMapper(BaseMapper[ProductImage]):
    @classmethod
    def to_dict(cls, instance: ProductImage) -> dict[str, Any]:
        return {
            "id": instance.id,
            "url": instance.url,
            "alt": instance.alt,
            "position": instance.position,
        }


class ReviewMapper(BaseMapper[Review]):
    @classmethod
    def to_dict(cls, instance: Review) -> dict[str, Any]:
        author = instance.author
        name = author.display_name if author else "Cliente"
        return {
            "id": instance.id,
            "author_name": name,
            "monogram": (name[:1] or "?").upper(),
            "rating": instance.rating,
            "stars_full": range(instance.rating),
            "stars_empty": range(5 - instance.rating),
            "title": instance.title,
            "comment": instance.comment,
            "created_at": instance.created_at,
        }


class ProductMapper(BaseMapper[Product]):
    @staticmethod
    def _cover(instance: Product) -> str:
        # images vem prefetched (with_relations) -> sem query extra por item
        gallery = list(instance.images.all())
        if gallery:
            return gallery[0].url
        if instance.image:
            return instance.image.url
        return instance.image_url or ""

    @classmethod
    def to_dict(cls, instance: Product) -> dict[str, Any]:
        return {
            "id": instance.id,
            "name": instance.name,
            "slug": instance.slug,
            "category_name": instance.category.name,
            "category_slug": instance.category.slug,
            "icon": instance.category.icon,
            "accent": instance.category.accent,
            "monogram": instance.name[:1].upper(),
            "image_url": cls._cover(instance),
            "price": instance.price,
            "price_display": format_brl(instance.price),
            "old_price_display": format_brl(instance.compare_at_price) if instance.has_discount else "",
            "has_discount": instance.has_discount,
            "discount_pct": instance.discount_pct,
            "is_on_promotion": instance.is_on_promotion,
            "is_new": instance.is_new,
            "in_stock": instance.in_stock,
            "rating": float(instance.rating),
            "review_count": instance.review_count,
            "url": instance.get_absolute_url(),
        }

    @classmethod
    def to_detail(cls, instance: Product) -> dict[str, Any]:
        data = cls.to_dict(instance)
        gallery = ProductImageMapper.to_list(instance.images.all())
        if not gallery and data["image_url"]:
            gallery = [{"id": 0, "url": data["image_url"], "alt": instance.name, "position": 0}]
        data.update(
            {
                "description": instance.description,
                "material": instance.material,
                "dimensions": instance.dimensions,
                "print_time_hours": instance.print_time_hours,
                "stock": instance.stock,
                "sales_count": instance.sales_count,
                "gallery": gallery,
                "rating_int": int(round(float(instance.rating))),
            }
        )
        return data

    @classmethod
    def to_seller_row(cls, instance: Product) -> dict[str, Any]:
        """Linha do produto no painel do vendedor (campos operacionais)."""
        from django.urls import reverse

        data = cls.to_dict(instance)
        data.update(
            {
                "stock": instance.stock,
                "sales_count": instance.sales_count,
                "is_active": instance.is_active,
                "image_count": len(instance.images.all()),
                "edit_url": reverse("seller:product_edit", args=[instance.id]),
            }
        )
        return data
