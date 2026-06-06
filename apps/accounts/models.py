"""Modelos do app de contas."""
from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import TimeStampedModel

from .managers import UserManager


class User(AbstractUser):
    """Usuário com login por e-mail (sem username).

    O papel define o fluxo: cliente (compra) ou vendedor (painel da loja).
    """

    class Role(models.TextChoices):
        CLIENTE = "cliente", "Cliente"
        VENDEDOR = "vendedor", "Vendedor"

    username = None
    email = models.EmailField("e-mail", unique=True)
    phone = models.CharField("telefone", max_length=20, blank=True)
    newsletter_opt_in = models.BooleanField("recebe novidades", default=True)

    role = models.CharField("papel", max_length=10, choices=Role.choices, default=Role.CLIENTE)
    # dados exclusivos do vendedor
    store_name = models.CharField("nome da loja", max_length=120, blank=True)
    document = models.CharField("CPF/CNPJ", max_length=20, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    def __str__(self) -> str:
        return self.get_full_name() or self.email

    @property
    def display_name(self) -> str:
        return self.store_name or self.first_name or self.email.split("@")[0]

    @property
    def is_seller(self) -> bool:
        return self.role == self.Role.VENDEDOR


class Address(TimeStampedModel):
    """Endereço de entrega do usuário."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField("identificação", max_length=40, default="Casa")
    recipient = models.CharField("destinatário", max_length=120)
    zip_code = models.CharField("CEP", max_length=9)
    street = models.CharField("logradouro", max_length=160)
    number = models.CharField("número", max_length=20)
    complement = models.CharField("complemento", max_length=80, blank=True)
    district = models.CharField("bairro", max_length=80)
    city = models.CharField("cidade", max_length=80)
    state = models.CharField("UF", max_length=2)
    is_default = models.BooleanField("padrão", default=False)

    class Meta:
        verbose_name = "endereço"
        verbose_name_plural = "endereços"
        ordering = ["-is_default", "-created_at"]

    def __str__(self) -> str:
        return f"{self.label} — {self.city}/{self.state}"
