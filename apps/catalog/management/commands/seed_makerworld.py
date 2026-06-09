"""Popula o catálogo com produtos relevantes (estilo MakerWorld) e fotos
padronizadas na identidade L3D Labz.

MakerWorld bloqueia scraping (403), então é uma curadoria dos tipos mais
relevantes de impressão 3D, com a foto de cada item gerada pelo pipeline de
branding (apps/catalog/branding.py). Idempotente.
"""
from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.models import Category, Product

# (nome, icone do sprite, accent)
CATEGORIES = [
    ("Action Figures", "star", "#2BA6E0"),
    ("Articulados", "cube", "#2FA84F"),
    ("Vasos & Plantas", "leaf", "#43C266"),
    ("Organizadores", "box", "#E0A82B"),
    ("Luminárias", "spark", "#E0552B"),
    ("Miniaturas", "pick3d", "#8B5CF6"),
    ("Gadgets", "printer3d", "#2BA6E0"),
    ("Decoração", "layers", "#E02B6B"),
]

# (categoria, nome, preço, compare, material, dimensões, horas, rating, vendas, destaque)
PRODUCTS = [
    ("Action Figures", "Cavaleiro Espacial", "89.90", "119.90", "PLA+", "22×12×10 cm", 9, "4.9", 320, True),
    ("Action Figures", "Robô Sentinela", "74.90", None, "PLA+", "18×10×9 cm", 7, "4.7", 180, False),
    ("Action Figures", "Heroína Alada", "94.90", "129.90", "Resina", "20×14×11 cm", 11, "4.9", 240, True),
    ("Articulados", "Dragão Flexi", "59.90", "79.90", "PLA", "28×6×4 cm", 6, "4.8", 510, True),
    ("Articulados", "Polvo Articulado", "39.90", None, "PLA", "14×14×5 cm", 4, "4.9", 770, True),
    ("Articulados", "Cobra Flexi Arco-íris", "44.90", "54.90", "PLA", "30×4×3 cm", 5, "4.6", 290, False),
    ("Vasos & Plantas", "Vaso Geométrico Hexagonal", "49.90", None, "PETG", "12×12×14 cm", 6, "4.7", 210, False),
    ("Vasos & Plantas", "Cachepô Origami", "54.90", "69.90", "PETG", "13×13×13 cm", 7, "4.8", 160, True),
    ("Vasos & Plantas", "Vaso Auto-irrigável", "64.90", None, "PETG", "15×15×16 cm", 8, "4.6", 120, False),
    ("Organizadores", "Porta-treco Modular", "34.90", None, "PLA", "10×10×6 cm", 3, "4.7", 430, False),
    ("Organizadores", "Organizador de Cabos", "24.90", "32.90", "PLA", "8×4×3 cm", 2, "4.5", 380, False),
    ("Organizadores", "Bandeja de Mesa Hex", "44.90", None, "PLA+", "24×18×3 cm", 5, "4.8", 150, True),
    ("Luminárias", "Luminária Lua 3D", "119.90", "159.90", "PLA", "16×16×18 cm", 12, "4.9", 280, True),
    ("Luminárias", "Abajur Voronoi", "99.90", None, "PETG", "14×14×22 cm", 10, "4.7", 130, False),
    ("Luminárias", "Luminária Cogumelo", "84.90", "104.90", "PLA", "12×12×16 cm", 8, "4.8", 200, True),
    ("Miniaturas", "Miniatura Cavaleiro D&D", "29.90", None, "Resina", "5×3×3 cm", 3, "4.9", 640, True),
    ("Miniaturas", "Dragão Miniatura", "34.90", "44.90", "Resina", "7×6×5 cm", 4, "4.8", 410, False),
    ("Miniaturas", "Goblin Arqueiro", "27.90", None, "Resina", "4×3×3 cm", 3, "4.6", 220, False),
    ("Gadgets", "Suporte de Headset", "54.90", "69.90", "PLA+", "16×12×24 cm", 7, "4.8", 350, True),
    ("Gadgets", "Suporte de Celular Dobrável", "29.90", None, "PLA", "9×7×3 cm", 3, "4.7", 520, False),
    ("Gadgets", "Apoio de Controle Duplo", "44.90", "54.90", "PLA+", "18×10×9 cm", 5, "4.7", 260, False),
    ("Decoração", "Vaso de Parede Lua", "39.90", None, "PETG", "14×14×7 cm", 5, "4.6", 140, False),
    ("Decoração", "Escultura Onda", "59.90", "74.90", "PLA", "20×8×14 cm", 7, "4.8", 110, True),
    ("Decoração", "Mandala Decorativa", "34.90", None, "PLA", "20×20×1 cm", 4, "4.7", 175, False),
]


class Command(BaseCommand):
    help = "Popula o catálogo com produtos relevantes (estilo MakerWorld) + fotos padronizadas L3D Labz."

    def handle(self, *args, **options):
        cats: dict[str, Category] = {}
        for ordem, (nome, icone, accent) in enumerate(CATEGORIES):
            cat, _ = Category.objects.get_or_create(
                slug=slugify(nome),
                defaults={
                    "name": nome, "icon": icone, "accent": accent,
                    "description": f"Modelos de {nome.lower()} impressos em 3D sob demanda.",
                    "order": ordem, "is_highlighted": True,
                },
            )
            cats[nome] = cat
        self.stdout.write(self.style.SUCCESS(f"Categorias: {len(cats)}"))

        novos = 0
        for cat_nome, nome, preco, compare, material, dims, horas, rating, vendas, destaque in PRODUCTS:
            cat = cats[cat_nome]
            obj, criado = Product.objects.get_or_create(
                slug=slugify(nome),
                defaults={
                    "category": cat,
                    "name": nome,
                    "description": (
                        f"{nome} impresso em 3D com acabamento premium em {material}. "
                        f"Produzido sob demanda pela L3D Labz — preço e prazo combinados no WhatsApp."
                    ),
                    "price": Decimal(preco),
                    "compare_at_price": Decimal(compare) if compare else None,
                    "stock": 25,
                    "rating": Decimal(rating),
                    "sales_count": vendas,
                    "material": material,
                    "dimensions": dims,
                    "print_time_hours": horas,
                    "is_featured": destaque,
                    "is_active": True,
                },
            )
            novos += criado

        total = Product.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Produtos novos: {novos} (total {total})"))
        self.stdout.write("Rode `python manage.py padronizar_fotos` para as fotos reais.")
