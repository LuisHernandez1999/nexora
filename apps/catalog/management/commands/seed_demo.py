"""Popula o catálogo, promoções e cupons com dados de demonstração.

Uso:  python manage.py seed_demo
Idempotente: pode rodar várias vezes (usa get_or_create por slug/código).
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone
from django.utils.text import slugify

from apps.catalog.models import Category, Product, ProductImage, Review
from apps.orders.models import Order, OrderItem
from apps.promotions.models import Coupon, Offer, Promotion

User = get_user_model()


def _ensure_approved_purchase(buyer, product) -> bool:
    """Garante uma compra paga (Order APPROVED + OrderItem) de `buyer` por `product`.

    Idempotente: se ja existe item desse comprador para esse produto num pedido
    aprovado, nao cria nada. Retorna True se criou um pedido novo.
    """
    already = OrderItem.objects.filter(
        order__user=buyer,
        product=product,
        order__payment_status=Order.PaymentStatus.APPROVED,
    ).exists()
    if already:
        return False
    order = Order.objects.create(
        user=buyer,
        status=Order.Status.DELIVERED,
        payment_method=Order.Payment.PIX,
        payment_status=Order.PaymentStatus.APPROVED,
        paid_at=timezone.now(),
        subtotal=product.price,
        total=product.price,
        recipient=buyer.first_name or buyer.email,
        zip_code="01001-000",
        street="Rua Demo",
        number_addr="100",
        district="Centro",
        city="Sao Paulo",
        state="SP",
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        unit_price=product.price,
        quantity=1,
        line_total=product.price,
    )
    return True


def _ensure_basket(buyer, products) -> bool:
    """Pedido pago multi-item (gera co-compra p/ 'quem comprou tambem levou').

    Idempotente: pula se o comprador ja tem algum pedido com mais de um item.
    """
    products = [p for p in products if p]
    if len(products) < 2:
        return False
    has_multi = (
        Order.objects.filter(user=buyer).annotate(n=Count("items")).filter(n__gt=1).exists()
    )
    if has_multi:
        return False
    total = sum((p.price for p in products), Decimal("0"))
    order = Order.objects.create(
        user=buyer, status=Order.Status.DELIVERED, payment_method=Order.Payment.PIX,
        payment_status=Order.PaymentStatus.APPROVED, paid_at=timezone.now(),
        subtotal=total, total=total,
        recipient=buyer.first_name or buyer.email, zip_code="01001-000",
        street="Rua Demo", number_addr="100", district="Centro", city="Sao Paulo", state="SP",
    )
    for p in products:
        OrderItem.objects.create(
            order=order, product=p, product_name=p.name,
            unit_price=p.price, quantity=1, line_total=p.price,
        )
    return True

# Fotos reais (Unsplash CDN), verificadas e mapeadas por categoria.
# A capa do produto sai da galeria; sempre carregam (sem placeholder instavel).
CATEGORY_IMAGES = {
    "Action Figures": ["1608889175123-8ee362201f81", "1558060370-d644479cb6f7",
                       "1518946222227-364f22132616", "1535378917042-10a22c95931a"],
    "Utensílios": ["1550009158-9ebf69173e03", "1572635196237-14b3f281503f", "1610945265064-0e34e5519bbf"],
    "Decoração": ["1593305841991-05c297ba4575", "1612036782180-6f0b6cd846fe", "1580927752452-89d86da3fa0a"],
    "Gadgets": ["1517336714731-489689fd1ca8", "1607462109225-6b64ae2dd3cb", "1526170375885-4d8ecf77b99f",
               "1610945265064-0e34e5519bbf", "1580927752452-89d86da3fa0a"],
    "Cosplay & Props": ["1608889175123-8ee362201f81", "1535378917042-10a22c95931a", "1558060370-d644479cb6f7"],
    "Jogos & Tabuleiro": ["1558060370-d644479cb6f7", "1518946222227-364f22132616", "1612036782180-6f0b6cd846fe"],
    "Tabacaria": ["1526170375885-4d8ecf77b99f", "1558060370-d644479cb6f7", "1610945265064-0e34e5519bbf"],
}
_FALLBACK_IMAGES = CATEGORY_IMAGES["Gadgets"]


def category_image(category_name: str, n: int = 0, w: int = 600, h: int = 600) -> str:
    ids = CATEGORY_IMAGES.get(category_name) or _FALLBACK_IMAGES
    return f"https://images.unsplash.com/photo-{ids[n % len(ids)]}?w={w}&h={h}&fit=crop&q=80"


DEMO_REVIEWS = [
    (5, "Impressao impecavel", "Acabamento perfeito, chegou rapido e bem embalado."),
    (5, "Recomendo demais", "Qualidade acima do esperado pelo preco. Compro de novo."),
    (4, "Muito bom", "Peca linda, so achei um pouco menor do que imaginei."),
    (5, "Sensacional", "Ficou perfeito na minha setup. Caprichado nos detalhes."),
    (4, "Valeu a compra", "Boa qualidade de material, recomendo para presente."),
    (5, "Top demais", "Encaixes precisos e cor igual a da foto."),
]

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
    help = "Popula o banco com dados de demonstração da L3D Labz."

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

        # ---- vendedor demo + posse dos produtos ----
        seller, made_seller = User.objects.get_or_create(
            email="vendedor@l3dlabz.test",
            defaults={"first_name": "Studio", "role": User.Role.VENDEDOR, "store_name": "Studio Maker 3D"},
        )
        if made_seller:
            seller.set_password("l3dlabz123")
            seller.save()
        elif seller.role != User.Role.VENDEDOR:
            seller.role = User.Role.VENDEDOR
            seller.store_name = seller.store_name or "Studio Maker 3D"
            seller.save(update_fields=["role", "store_name"])
        Product.objects.filter(seller__isnull=True).update(seller=seller)
        self.stdout.write(self.style.SUCCESS(f"Vendedor: {seller.email} (loja '{seller.store_name}')"))

        # ---- galeria real (ate 4 fotos) para quem ainda nao tem ----
        gallery = 0
        for product in Product.objects.all():
            if product.images.exists():
                continue
            for pos in range(3):
                ProductImage.objects.create(
                    product=product,
                    image_url=category_image(product.category.name, product.id + pos),
                    alt=product.name, position=pos,
                )
                gallery += 1
        self.stdout.write(self.style.SUCCESS(f"Fotos de produto: {gallery}"))

        # ---- ofertas reais (produto + valor original x promocional) ----
        offers = 0
        for product in Product.objects.filter(compare_at_price__isnull=False):
            _, was = Offer.objects.get_or_create(
                product=product,
                defaults={
                    "category": product.category,
                    "original_price": product.compare_at_price,
                    "promo_price": product.price,
                    "is_active": True,
                },
            )
            offers += was
        self.stdout.write(self.style.SUCCESS(f"Ofertas novas: {offers} (total {Offer.objects.count()})"))

        # ---- compradores demo + avaliacoes (so quem comprou avalia) ----
        buyers = []
        for i in range(1, 4):
            buyer, made = User.objects.get_or_create(
                email=f"cliente{i}@l3dlabz.test",
                defaults={"first_name": f"Cliente {i}", "role": User.Role.CLIENTE},
            )
            if made:
                buyer.set_password("l3dlabz123")
                buyer.save()
            buyers.append(buyer)

        reviewed = 0
        purchases = 0
        for idx, product in enumerate(Product.objects.order_by("id")[:8]):
            for b, buyer in enumerate(buyers[: 1 + idx % 3]):
                # de verdade: a avaliacao so existe porque houve uma compra paga
                purchases += _ensure_approved_purchase(buyer, product)
                rating, title, comment = DEMO_REVIEWS[(idx + b) % len(DEMO_REVIEWS)]
                _, made = Review.objects.get_or_create(
                    product=product, author=buyer,
                    defaults={"rating": rating, "title": title, "comment": comment},
                )
                reviewed += made
        self.stdout.write(self.style.SUCCESS(
            f"Compras demo (pagas): {purchases} | Avaliacoes novas: {reviewed} (total {Review.objects.count()})"
        ))

        # ---- carrinhos multi-item (co-compra -> recomendacoes) ----
        prods = list(Product.objects.order_by("id")[:8])
        baskets = 0
        if len(prods) >= 6:
            combos = [
                [prods[0], prods[1], prods[2]],
                [prods[0], prods[3]],
                [prods[1], prods[4], prods[5]],
            ]
            for buyer, combo in zip(buyers, combos):
                baskets += _ensure_basket(buyer, combo)
        self.stdout.write(self.style.SUCCESS(f"Carrinhos multi-item (co-compra): {baskets}"))

        self.stdout.write(self.style.SUCCESS(
            "\nSeed concluido!\n"
            "  Clientes: cliente1..3@l3dlabz.test / l3dlabz123 (compraram -> podem avaliar)\n"
            "  Ofertas em /promocoes/ofertas/ | API em /api/ofertas/ e /api/produtos/"
        ))
