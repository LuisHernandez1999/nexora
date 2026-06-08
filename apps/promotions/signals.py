"""Sinais de promoções: invalida cache e sincroniza produto <-> oferta."""
from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Offer, Promotion
from .queries import invalidate_promotion_cache


@receiver([post_save, post_delete], sender=Promotion)
def _bust_promo_cache(sender, **kwargs):
    invalidate_promotion_cache()


@receiver(post_save, sender=Offer)
def _offer_saved(sender, instance, **kwargs):
    from .services import OfferService

    OfferService.sync_product(instance)
    _bust_all_for(instance)


@receiver(post_delete, sender=Offer)
def _offer_deleted(sender, instance, **kwargs):
    from .services import OfferService

    OfferService.unsync_product(instance)
    _bust_all_for(instance)


def _bust_all_for(offer: Offer) -> None:
    """Oferta mexe no produto: limpa cache de promocoes e do catalogo."""
    from apps.catalog.queries import invalidate_catalog_cache, invalidate_product

    invalidate_promotion_cache()
    invalidate_catalog_cache()
    invalidate_product(getattr(offer.product, "slug", ""))
