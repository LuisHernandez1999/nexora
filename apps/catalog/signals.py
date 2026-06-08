"""Sinais do catalogo: invalida cache de listagens e mantem agregados de review."""
from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Category, Product, ProductImage, Review
from .queries import invalidate_catalog_cache, invalidate_product


@receiver([post_save, post_delete], sender=Product)
@receiver([post_save, post_delete], sender=Category)
def _bust_catalog_cache(sender, **kwargs):
    invalidate_catalog_cache()


@receiver([post_save, post_delete], sender=ProductImage)
def _bust_product_on_image_change(sender, instance, **kwargs):
    invalidate_catalog_cache()
    invalidate_product(getattr(instance.product, "slug", ""))


@receiver([post_save, post_delete], sender=Review)
def _recompute_product_rating(sender, instance, **kwargs):
    # fonte unica de verdade da media: cobre reviews do app e do admin
    from .services import ReviewService

    ReviewService.recompute(instance.product_id)
    invalidate_product(getattr(instance.product, "slug", ""))
