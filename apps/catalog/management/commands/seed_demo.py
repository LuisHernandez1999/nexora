"""Popula o catálogo, promoções e cupons com dados de demonstração.

Uso:  python manage.py seed_demo
Idempotente: pode rodar várias vezes (usa get_or_create por slug/código).
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.catalog.models import Category, Product
from apps.promotions.models import Coupon, Promotion

CATEGORIES = [
    {"name": "Action Figures", "icon": "cube", "accent": "#6366f1",
     "description": "Bonecos articulados e estatuetas colecionáveis."},
    {"name": "Utensílios", "icon": "box", "accent": "#0ea5e9",
     "description": "Suportes, organizadores e peças úteis para o dia a dia."},
    {"name": "Decoração", "icon": "spark", "accent": "#8b5cf6",
     "description": "Luminárias, vasos e enfeites para sua setup."},
    {"name": "Gadgets", "icon": "bolt", "accent": "#3b82f6",
     "description": "Acessórios tech impressos em 3D."},
    {"name": "Cosplay & Props", "icon": "layers", "accent": "#06b6d4",
     "description": "Réplicas, máscaras e adereços para cosplay."},
    {"name": "Jogos & Tabuleiro", "icon": "tag", "accent": "#22d3ee",
     "description": "Miniaturas, organizadores e tokens para board games."},
    {"name": "Tabacaria", "icon": "leaf", "accent": "#22c55e",
     "description": "Porta-fumo, porta-pods, dichavadores e acessórios impressos em 3D."},
]

# palavras-chave por categoria para buscar fotos reais (loremflickr)
KEYWORDS = {
    "Action Figures": "anime,figure",
    "Utensílios": "headset,controller",
    "Decoração": "lamp,3dprint",
    "Gadgets": "gadget,tech",
    "Cosplay & Props": "cosplay,helmet",
    "Jogos & Tabuleiro": "boardgame,miniature",
    "Tabacaria": "grinder,herb",
}


def product_image(category_name: str, index: int) -> str:
    kw = KEYWORDS.get(category_name, "product")
    return f"https://loremflickr.com/600/600/{kw}?lock={200 + index}"


# (categoria, nome, preço, preço_cheio|None, featured, rating, vendas, material, dimensões, horas)
PRODUCTS = [
    ("Action Figures", "Cavaleiro Espacial 20cm", "129.90", "169.90", True, "4.9", 320, "PLA+", "20×9×7 cm", 14),
    ("Action Figures", "Mecha Titan Articulado", "199.90", None, True, "5.0", 210, "PETG", "25×14×10 cm", 22),
    ("Action Figures", "Guerreira Élfica", "89.90", "109.90", False, "4.7", 140, "PLA", "18×8×6 cm", 11),
    ("Action Figures", "Caçador de Recompensas", "149.90", None, True, "4.8", 175, "PLA+", "21×10×8 cm", 16),
    ("Utensílios", "Suporte de Headset Gamer", "59.90", "79.90", True, "4.8", 410, "PETG", "26×12×10 cm", 8),
    ("Utensílios", "Organizador de Cabos (kit 6)", "29.90", None, False, "4.6", 530, "PLA", "—", 3),
    ("Utensílios", "Porta-controle Duplo", "44.90", "54.90", False, "4.7", 260, "PLA+", "18×10×9 cm", 5),
    ("Utensílios", "Suporte de Celular Ajustável", "34.90", None, True, "4.9", 600, "PETG", "12×8×8 cm", 4),
    ("Decoração", "Luminária Lua 3D", "119.90", "149.90", True, "5.0", 290, "PLA branco", "Ø15 cm", 12),
    ("Decoração", "Vaso Geométrico Voronoi", "69.90", None, False, "4.6", 120, "PLA", "14×14×16 cm", 9),
    ("Decoração", "Quadro Litofania LED", "99.90", "129.90", True, "4.8", 150, "PLA", "20×15 cm", 10),
    ("Gadgets", "Dock Station Minimalista", "79.90", None, True, "4.7", 200, "PETG", "12×8×6 cm", 6),
    ("Gadgets", "Apoio para Notebook", "89.90", "109.90", False, "4.8", 175, "PETG", "28×22×12 cm", 9),
    ("Gadgets", "Hub de Dados Cyberpunk", "54.90", None, False, "4.5", 95, "PLA+", "10×6×4 cm", 5),
    ("Cosplay & Props", "Máscara Samurai Oni", "179.90", "219.90", True, "4.9", 130, "PLA+", "Tam. único", 20),
    ("Cosplay & Props", "Elmo Mandaloriano", "249.90", None, True, "5.0", 88, "PLA+", "Tam. único", 28),
    ("Jogos & Tabuleiro", "Organizador de Cartas Universal", "49.90", "64.90", False, "4.7", 240, "PLA", "—", 6),
    ("Jogos & Tabuleiro", "Pack 10 Miniaturas RPG", "89.90", None, True, "4.9", 310, "Resina", "32 mm", 7),
    ("Tabacaria", "Porta-Fumo Hermético", "39.90", "49.90", True, "4.8", 180, "PLA+", "8×8×5 cm", 4),
    ("Tabacaria", "Suporte de Pod Duplo", "29.90", None, True, "4.7", 220, "PETG", "10×6×4 cm", 3),
    ("Tabacaria", "Case para Pods (kit 3)", "44.90", "54.90", False, "4.6", 140, "PLA", "12×8×4 cm", 5),
    ("Tabacaria", "Dichavador 3 Partes", "34.90", None, False, "4.9", 260, "PLA+", "Ø6 cm", 3),
    ("Tabacaria", "Porta-Sedas & Piteira", "24.90", None, False, "4.5", 95, "PLA", "9×5×2 cm", 2),
]

PROMOTIONS = [
    {"kind": Promotion.Kind.HERO, "title": "Coleção Action Figures com até 25% OFF",
     "subtitle": "Estatuetas e bonecos articulados com preço de lançamento.",
     "badge": "Oferta da semana", "cta_label": "Ver coleção", "cta_url": "/catalogo/?categoria=action-figures",
     "order": 0, "image_url": "https://loremflickr.com/1600/720/anime,figure?lock=11"},
    {"kind": Promotion.Kind.STRIP, "title": "Frete grátis acima de R$ 199",
     "subtitle": "Para todo o Brasil. Junte suas peças favoritas e economize no envio.",
     "badge": "Entrega", "cta_label": "Aproveitar", "cta_url": "/catalogo/",
     "order": 1, "image_url": "https://loremflickr.com/1600/720/delivery,package?lock=12"},
    {"kind": Promotion.Kind.STRIP, "title": "Decoração que ilumina sua setup",
     "subtitle": "Luminárias e litofanias com 20% OFF nesta semana.",
     "badge": "Decoração", "cta_label": "Quero ver", "cta_url": "/catalogo/?categoria=decoracao",
     "order": 2, "image_url": "https://loremflickr.com/1600/720/lamp,light?lock=13"},
]

COUPONS = [
    {"code": "NERD10", "discount_type": Coupon.DiscountType.PERCENT, "value": "10", "min_order": "0"},
    {"code": "CUBO20", "discount_type": Coupon.DiscountType.PERCENT, "value": "20", "min_order": "150"},
    {"code": "MENOS30", "discount_type": Coupon.DiscountType.FIXED, "value": "30", "min_order": "120"},
]


class Command(BaseCommand):
    help = "Popula o banco com dados de demonstração da L3dLabZ."

    def handle(self, *args, **options):
        cats: dict[str, Category] = {}
        for data in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                slug=slugify(data["name"]),
                defaults={
                    "name": data["name"], "icon": data["icon"],
                    "accent": data["accent"], "description": data["description"],
                    "order": CATEGORIES.index(data),
                },
            )
            cats[data["name"]] = cat
        self.stdout.write(self.style.SUCCESS(f"Categorias: {len(cats)}"))

        created = 0
        for index, (cat_name, name, price, compare, featured, rating, sales, material, dims, hours) in enumerate(PRODUCTS):
            img = product_image(cat_name, index)
            obj, was_created = Product.objects.get_or_create(
                slug=slugify(name),
                defaults={
                    "category": cats[cat_name],
                    "name": name,
                    "description": f"{name} impresso em 3D com acabamento premium. "
                                   f"Material {material}, ideal para colecionadores e fãs.",
                    "price": Decimal(price),
                    "compare_at_price": Decimal(compare) if compare else None,
                    "stock": 25,
                    "rating": Decimal(rating),
                    "sales_count": sales,
                    "material": material,
                    "dimensions": "" if dims == "—" else dims,
                    "print_time_hours": hours,
                    "is_featured": featured,
                    "is_active": True,
                    "image_url": img,
                },
            )
            created += was_created
            if obj.image_url != img:  # mantém o seed idempotente e atualiza imagem
                obj.image_url = img
                obj.save(update_fields=["image_url"])
        self.stdout.write(self.style.SUCCESS(f"Produtos novos: {created} (total {Product.objects.count()})"))

        for data in PROMOTIONS:
            promo, _ = Promotion.objects.get_or_create(
                title=data["title"],
                defaults={**data, "is_active": True,
                          "ends_at": timezone.now() + timedelta(days=14)},
            )
            if promo.image_url != data["image_url"]:
                promo.image_url = data["image_url"]
                promo.save(update_fields=["image_url"])
        self.stdout.write(self.style.SUCCESS(f"Promoções: {Promotion.objects.count()}"))

        for data in COUPONS:
            Coupon.objects.get_or_create(
                code=data["code"],
                defaults={
                    "discount_type": data["discount_type"],
                    "value": Decimal(data["value"]),
                    "min_order": Decimal(data["min_order"]),
                    "is_active": True,
                    "valid_until": timezone.now() + timedelta(days=30),
                },
            )
        self.stdout.write(self.style.SUCCESS(f"Cupons: {Coupon.objects.count()}"))
        self.stdout.write(self.style.SUCCESS("\nSeed concluído! Rode o servidor e acesse /"))
