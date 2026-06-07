"""Padroniza a foto de TODOS os produtos com a identidade L3D Labz.

Gera o card branded (apps/catalog/branding.py) para cada produto que ainda não
tem imagem própria — deixando o catálogo visualmente consistente (sem misturar
fotos aleatórias com os cards da loja). Idempotente; não sobrescreve uploads.
"""
from __future__ import annotations

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.catalog.branding import gerar_card
from apps.catalog.models import Product


class Command(BaseCommand):
    help = "Gera a foto padronizada (identidade L3D Labz) para todos os produtos sem imagem."

    def add_arguments(self, parser):
        parser.add_argument(
            "--forcar", action="store_true",
            help="Regenera mesmo quem já tem imagem (sobrescreve).",
        )

    def handle(self, *args, **options):
        forcar = options["forcar"]
        feitos = 0
        for p in Product.objects.select_related("category").all():
            if p.image and not forcar:
                continue
            png = gerar_card(p.name, p.category.accent if p.category else "#2FA84F")
            p.image.save(f"{p.slug}.png", ContentFile(png), save=True)
            feitos += 1
        self.stdout.write(self.style.SUCCESS(f"Fotos padronizadas: {feitos}/{Product.objects.count()}"))
