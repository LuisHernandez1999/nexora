"""Dá a TODOS os produtos uma FOTO REAL padronizada na identidade L3D Labz.

Para cada produto: busca uma foto real relevante por palavra-chave da categoria
(loremflickr) e aplica o tratamento da loja (recorte quadrado + moldura accent +
selo L3D Labz). Se a rede falhar, cai no card gerado. Idempotente (`lock` = pk).
"""
from __future__ import annotations

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.catalog.branding import baixar, gerar_card, padronizar_foto, url_curada
from apps.catalog.models import Product


class Command(BaseCommand):
    help = "Gera a FOTO REAL padronizada (identidade L3D Labz) para os produtos."

    def add_arguments(self, parser):
        parser.add_argument("--forcar", action="store_true",
                            help="Regenera mesmo quem já tem imagem (sobrescreve).")

    def handle(self, *args, **options):
        forcar = options["forcar"]
        feitos, fallback = 0, 0
        indice: dict[str, int] = {}
        for p in Product.objects.select_related("category").order_by("category__name", "pk"):
            if p.image and not forcar:
                continue
            accent = p.category.accent if p.category else "#2FA84F"
            cat = p.category.name if p.category else ""
            i = indice.get(cat, 0)
            indice[cat] = i + 1
            try:
                raw = baixar(url_curada(cat, i))
                conteudo = padronizar_foto(raw, accent)
                ext = "jpg"
            except Exception:
                conteudo = gerar_card(p.name, accent)  # rede falhou -> card
                ext = "png"
                fallback += 1
            p.image.save(f"{p.slug}.{ext}", ContentFile(conteudo), save=True)
            feitos += 1
            self.stdout.write(f"  · {p.name}")
        self.stdout.write(self.style.SUCCESS(
            f"Fotos padronizadas: {feitos}/{Product.objects.count()} (fallback card: {fallback})"
        ))
