"""Gera um modelo 3D (GLB) + STL para cada produto a partir da foto dele.

Reusa o motor do lithophane (relevo da imagem) para popular o `model_3d`/
`model_stl` de todos os produtos com foto — assim o viewer 3D e a galeria
"Modelos 3D" funcionam para o catálogo inteiro. Idempotente.
"""
from __future__ import annotations

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image

from apps.catalog.models import Product
from apps.lithophane.generation import EspecsLitho, LithophaneGenerator

_SPECS = EspecsLitho(
    largura_mm=120.0, espessura_min_mm=0.8, espessura_max_mm=3.0,
    resolucao_px=170, formato="placa",
)


class Command(BaseCommand):
    help = "Gera GLB + STL (relevo da foto) para todos os produtos com imagem."

    def add_arguments(self, parser):
        parser.add_argument("--forcar", action="store_true",
                            help="Regenera mesmo quem já tem modelo 3D.")

    def handle(self, *args, **options):
        forcar = options["forcar"]
        feitos = 0
        for p in Product.objects.all():
            if not p.image:
                continue
            if p.model_3d and not forcar:
                continue
            try:
                with p.image.open("rb") as fh:
                    img = Image.open(fh)
                    img.load()
                glb, stl = LithophaneGenerator.gerar(img, _SPECS)
            except Exception as e:  # foto corrompida etc. — pula
                self.stderr.write(f"  ! {p.name}: {e}")
                continue
            p.model_3d.save(f"{p.slug}.glb", ContentFile(glb), save=False)
            p.model_stl.save(f"{p.slug}.stl", ContentFile(stl), save=False)
            p.save(update_fields=["model_3d", "model_stl"])
            feitos += 1
            self.stdout.write(f"  · {p.name}")
        self.stdout.write(self.style.SUCCESS(f"Modelos 3D gerados: {feitos}"))
