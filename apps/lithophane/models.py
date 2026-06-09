"""Modelo do rascunho de lithophane.

Guarda a foto original e os arquivos 3D gerados (GLB para o viewer, STL para
impressão) + as specs e o dono do rascunho (cliente logado ou sessão anônima).
"""
from __future__ import annotations

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.core.models import TimeStampedModel


class LithophaneDraft(TimeStampedModel):
    class Format(models.TextChoices):
        PLACA = "placa", "Placa plana"
        LUMINARIA = "luminaria", "Luminária"
        CURVO = "curvo", "Curvo"      # deferido — enum nasce pronto
        CUBO = "cubo", "Cubo"          # deferido — enum nasce pronto

    # dono do rascunho (cliente logado OU sessão anônima)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="lithophane_drafts", verbose_name="cliente",
    )
    session_key = models.CharField("sessão", max_length=40, blank=True)

    image = models.ImageField("foto enviada", upload_to="lithophane/fotos/")
    model_glb = models.FileField(
        "modelo GLB", upload_to="lithophane/glb/", blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["glb"])],
    )
    model_stl = models.FileField(
        "arquivo STL", upload_to="lithophane/stl/", blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["stl"])],
    )

    format = models.CharField(
        "formato", max_length=12, choices=Format.choices, default=Format.PLACA
    )
    size = models.DecimalField("tamanho (mm)", max_digits=6, decimal_places=1, default=100.0)
    thickness = models.DecimalField("espessura máx (mm)", max_digits=4, decimal_places=1, default=3.0)

    class Meta:
        verbose_name = "rascunho de lithophane"
        verbose_name_plural = "rascunhos de lithophane"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Lithophane #{self.pk} ({self.get_format_display()})"
