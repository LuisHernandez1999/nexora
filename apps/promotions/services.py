"""Serviços de promoções e cupons."""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.core.layers import BaseService

from .mappers import OfferMapper, PromotionMapper
from .models import Offer
from .queries import CouponQuery, OfferQuery, PromotionQuery


class PromotionService(BaseService):
    @staticmethod
    def get_hero_promotion() -> dict | None:
        promo = PromotionQuery.hero()
        return PromotionMapper.to_dict(promo) if promo else None

    @staticmethod
    def list_active_promotions(limit: int = 6) -> list[dict]:
        return PromotionMapper.to_list(PromotionQuery.active(limit))


class OfferService(BaseService):
    """Ofertas reais de produtos. So o vendedor dono do produto cria oferta."""

    @staticmethod
    def list_featured(limit: int = 6) -> list[dict]:
        return OfferMapper.to_list(OfferQuery.featured(limit))

    @staticmethod
    def list_for_seller(seller) -> list[dict]:
        return OfferMapper.to_list(OfferQuery.for_seller(seller))

    @staticmethod
    @transaction.atomic
    def create(seller, *, product, original_price, promo_price, starts_at=None, ends_at=None) -> tuple[Offer | None, str]:
        if product.seller_id != seller.id:
            return None, "Voce so pode criar ofertas para os seus produtos."
        if promo_price >= original_price:
            return None, "O valor promocional deve ser menor que o valor original."
        offer = Offer.objects.create(
            product=product,
            category=product.category,
            original_price=original_price,
            promo_price=promo_price,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        # a sincronizacao do produto (flag/preco) e feita pelo signal de Offer
        return offer, "Oferta publicada!"

    # ---- sincronizacao produto <-> oferta (chamada pelos signals) ----
    @staticmethod
    def sync_product(offer: Offer) -> None:
        from apps.catalog.models import Product

        if offer.is_active:
            Product.objects.filter(pk=offer.product_id).update(
                is_on_promotion=True,
                price=offer.promo_price,
                compare_at_price=offer.original_price,
            )
        else:
            OfferService.unsync_product(offer)

    @staticmethod
    def unsync_product(offer: Offer) -> None:
        from apps.catalog.models import Product

        if OfferQuery.live_count_for_product(offer.product_id, exclude_pk=offer.pk):
            return  # ainda ha outra oferta viva: nao mexe no produto
        Product.objects.filter(pk=offer.product_id).update(
            is_on_promotion=False,
            price=offer.original_price,
            compare_at_price=None,
        )


class CouponService(BaseService):
    @staticmethod
    def validate(code: str, subtotal: Decimal) -> dict:
        """Valida um cupom para um subtotal. Retorna dict pronto para a view."""
        coupon = CouponQuery.by_code(code)
        if not coupon:
            return {"valid": False, "message": "Cupom não encontrado.", "discount": Decimal("0"), "code": code}
        ok, message = coupon.is_valid(subtotal)
        discount = coupon.discount_for(subtotal) if ok else Decimal("0")
        return {
            "valid": ok,
            "message": message,
            "discount": discount,
            "code": coupon.code,
        }
