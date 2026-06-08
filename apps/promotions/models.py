"""Modelos de promoções e cupons."""
from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class PromotionQuerySet(models.QuerySet):
    def live(self):
        now = timezone.now()
        return self.filter(
            is_active=True,
        ).filter(
            models.Q(starts_at__isnull=True) | models.Q(starts_at__lte=now)
        ).filter(
            models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now)
        )


class Promotion(TimeStampedModel):
    class Kind(models.TextChoices):
        HERO = "hero", "Destaque (home)"
        STRIP = "strip", "Faixa"
        BANNER = "banner", "Banner"

    kind = models.CharField("tipo", max_length=10, choices=Kind.choices, default=Kind.STRIP)
    title = models.CharField("título", max_length=140)
    subtitle = models.CharField("subtítulo", max_length=220, blank=True)
    badge = models.CharField("selo", max_length=40, default="Oferta")
    cta_label = models.CharField("texto do botão", max_length=40, default="Conferir")
    cta_url = models.CharField("link do botão", max_length=200, default="/catalogo/")
    image = models.ImageField("imagem", upload_to="promotions/", blank=True)
    image_url = models.URLField("imagem (URL externa)", max_length=500, blank=True)

    is_active = models.BooleanField("ativa", default=True)
    starts_at = models.DateTimeField("início", null=True, blank=True)
    ends_at = models.DateTimeField("fim", null=True, blank=True)
    order = models.PositiveIntegerField("ordem", default=0)

    objects = PromotionQuerySet.as_manager()

    class Meta:
        verbose_name = "promoção"
        verbose_name_plural = "promoções"
        ordering = ["order", "-created_at"]

    def __str__(self) -> str:
        return self.title


class OfferQuerySet(models.QuerySet):
    def live(self):
        now = timezone.now()
        return (
            self.filter(is_active=True)
            .filter(models.Q(starts_at__isnull=True) | models.Q(starts_at__lte=now))
            .filter(models.Q(ends_at__isnull=True) | models.Q(ends_at__gte=now))
        )

    def with_relations(self):
        return (
            self.select_related("product", "product__category", "category")
            .prefetch_related("product__images")
        )


class Offer(TimeStampedModel):
    """Oferta real de um produto: valor original x valor promocional.

    Diferente de Promotion (banner de marketing), a Offer aponta para um
    produto concreto do vendedor e sincroniza o flag/preco do catalogo.
    """

    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="offers", verbose_name="produto"
    )
    category = models.ForeignKey(
        "catalog.Category", on_delete=models.PROTECT, related_name="offers", verbose_name="categoria"
    )
    original_price = models.DecimalField("valor original", max_digits=10, decimal_places=2)
    promo_price = models.DecimalField("valor promocional", max_digits=10, decimal_places=2)

    is_active = models.BooleanField("ativa", default=True)
    starts_at = models.DateTimeField("inicio", null=True, blank=True)
    ends_at = models.DateTimeField("fim", null=True, blank=True)
    order = models.PositiveIntegerField("ordem", default=0)

    objects = OfferQuerySet.as_manager()

    class Meta:
        verbose_name = "oferta"
        verbose_name_plural = "ofertas"
        ordering = ["order", "-created_at"]
        indexes = [
            models.Index(fields=["is_active", "-created_at"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"Oferta — {self.product_id} ({self.promo_price})"

    @property
    def discount_pct(self) -> int:
        if not self.original_price or self.promo_price >= self.original_price:
            return 0
        diff = (self.original_price - self.promo_price) / self.original_price
        return int(round(diff * 100))

    @property
    def savings(self) -> Decimal:
        return max(Decimal("0"), self.original_price - self.promo_price)


class Coupon(TimeStampedModel):
    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Percentual (%)"
        FIXED = "fixed", "Valor fixo (R$)"

    code = models.CharField("código", max_length=30, unique=True)
    discount_type = models.CharField("tipo", max_length=10, choices=DiscountType.choices, default=DiscountType.PERCENT)
    value = models.DecimalField("valor", max_digits=10, decimal_places=2)
    min_order = models.DecimalField("pedido mínimo", max_digits=10, decimal_places=2, default=Decimal("0"))

    is_active = models.BooleanField("ativo", default=True)
    valid_from = models.DateTimeField("válido de", null=True, blank=True)
    valid_until = models.DateTimeField("válido até", null=True, blank=True)
    usage_limit = models.PositiveIntegerField("limite de usos", null=True, blank=True)
    used_count = models.PositiveIntegerField("usos", default=0)

    class Meta:
        verbose_name = "cupom"
        verbose_name_plural = "cupons"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        super().save(*args, **kwargs)

    # --- regras ---
    def is_valid(self, subtotal: Decimal) -> tuple[bool, str]:
        now = timezone.now()
        if not self.is_active:
            return False, "Cupom inativo."
        if self.valid_from and now < self.valid_from:
            return False, "Cupom ainda não está válido."
        if self.valid_until and now > self.valid_until:
            return False, "Cupom expirado."
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return False, "Cupom esgotado."
        if subtotal < self.min_order:
            from apps.core.formatting import format_brl

            return False, f"Pedido mínimo de {format_brl(self.min_order)}."
        return True, "Cupom aplicado!"

    def discount_for(self, subtotal: Decimal) -> Decimal:
        if self.discount_type == self.DiscountType.PERCENT:
            return (subtotal * self.value / Decimal("100")).quantize(Decimal("0.01"))
        return min(self.value, subtotal)
