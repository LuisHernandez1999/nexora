"""Modelos de pedido.

O pedido guarda *snapshots* (nome, preço, endereço, totais) para ficar imune a
mudanças futuras de catálogo/preço. O pagamento aqui é simulado, mas o desenho
(status + método) já comporta um gateway real plugado no PaymentService.
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Aguardando pagamento"
        PAID = "paid", "Pago"
        PROCESSING = "processing", "Em produção"
        SHIPPED = "shipped", "Enviado"
        DELIVERED = "delivered", "Entregue"
        CANCELLED = "cancelled", "Cancelado"
        ORCAMENTO = "orcamento", "Orçamento pendente"

    class Payment(models.TextChoices):
        PIX = "pix", "PIX"
        CREDIT_CARD = "credit_card", "Cartão de crédito"
        BOLETO = "boleto", "Boleto"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pendente"
        APPROVED = "approved", "Aprovado"
        REFUSED = "refused", "Recusado"

    number = models.CharField("número", max_length=20, unique=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    status = models.CharField("status", max_length=12, choices=Status.choices, default=Status.PENDING)

    # pagamento
    payment_method = models.CharField("método", max_length=12, choices=Payment.choices)
    payment_status = models.CharField(
        "status do pagamento", max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    paid_at = models.DateTimeField("pago em", null=True, blank=True)
    card_last4 = models.CharField("cartão (final)", max_length=4, blank=True)

    # totais (snapshot)
    subtotal = models.DecimalField("subtotal", max_digits=10, decimal_places=2, default=Decimal("0"))
    discount = models.DecimalField("desconto", max_digits=10, decimal_places=2, default=Decimal("0"))
    shipping = models.DecimalField("frete", max_digits=10, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField("total", max_digits=10, decimal_places=2, default=Decimal("0"))
    coupon_code = models.CharField("cupom", max_length=30, blank=True)

    # entrega (snapshot)
    recipient = models.CharField("destinatário", max_length=120)
    phone = models.CharField("telefone", max_length=20, blank=True)
    zip_code = models.CharField("CEP", max_length=9)
    street = models.CharField("logradouro", max_length=160)
    number_addr = models.CharField("número", max_length=20)
    complement = models.CharField("complemento", max_length=80, blank=True)
    district = models.CharField("bairro", max_length=80)
    city = models.CharField("cidade", max_length=80)
    state = models.CharField("UF", max_length=2)

    class Meta:
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"]), models.Index(fields=["number"])]

    def __str__(self) -> str:
        return self.number or f"Pedido #{self.pk}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.number:
            # número estável baseado no PK, ex.: NX-000042
            type(self).objects.filter(pk=self.pk).update(number=f"NX-{self.pk:06d}")
            self.number = f"NX-{self.pk:06d}"

    @property
    def item_count(self) -> int:
        return sum(i.quantity for i in self.items.all())

    @property
    def shipping_line(self) -> str:
        comp = f" — {self.complement}" if self.complement else ""
        return f"{self.street}, {self.number_addr}{comp}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.SET_NULL, null=True, related_name="order_items"
    )
    product_name = models.CharField("produto", max_length=140)
    unit_price = models.DecimalField("preço unitário", max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField("quantidade")
    line_total = models.DecimalField("total da linha", max_digits=10, decimal_places=2)

    # item custom de lithophane (orçamento): snapshot do rascunho + specs
    draft_id = models.PositiveIntegerField("rascunho lithophane", null=True, blank=True)
    litho_specs = models.JSONField("specs do lithophane", null=True, blank=True)

    class Meta:
        verbose_name = "item do pedido"
        verbose_name_plural = "itens do pedido"

    def __str__(self) -> str:
        return f"{self.quantity}× {self.product_name}"
