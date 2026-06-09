"""Camada de consultas do catálogo — ORM otimizado + cache.

Toda leitura passa por aqui. Listagens "estáveis" (destaques, categorias,
lançamentos) são cacheadas; a busca filtrada usa TTL curto.
"""
from __future__ import annotations

from django.db.models import Avg, Count, F, Q

from apps.core import cache as cache_utils

from .models import Category, Favorite, Product, Review

NS_FEATURED = "catalog:featured"
NS_NEW = "catalog:new"
NS_CATEGORIES = "catalog:categories"
NS_PRODUCT = "catalog:product"
NS_RELATED = "catalog:related"
NS_BOUGHT = "catalog:bought_together"


class CategoryQuery:
    @staticmethod
    def highlighted() -> list[Category]:
        def producer():
            qs = (
                Category.objects.filter(is_highlighted=True)
                .annotate(num_products=Count("products", filter=Q(products__is_active=True)))
                .order_by("order", "name")
            )
            return list(qs)

        return cache_utils.get_or_set(NS_CATEGORIES, producer, bucket="long")

    @staticmethod
    def all_with_counts() -> list[Category]:
        qs = (
            Category.objects.annotate(
                num_products=Count("products", filter=Q(products__is_active=True))
            ).order_by("order", "name")
        )
        return list(qs)

    @staticmethod
    def by_slug(slug: str) -> Category | None:
        return Category.objects.filter(slug=slug).first()


class ProductQuery:
    @staticmethod
    def featured(limit: int = 8) -> list[Product]:
        def producer():
            qs = Product.objects.active().with_relations().filter(is_featured=True)
            return list(qs.order_by("-sales_count")[:limit])

        return cache_utils.get_or_set(
            cache_utils.build_key(NS_FEATURED, limit), producer, bucket="medium"
        )

    @staticmethod
    def new_arrivals(limit: int = 4) -> list[Product]:
        def producer():
            qs = Product.objects.active().with_relations().order_by("-created_at")
            return list(qs[:limit])

        return cache_utils.get_or_set(
            cache_utils.build_key(NS_NEW, limit), producer, bucket="medium"
        )

    @staticmethod
    def on_sale(limit: int = 8) -> list[Product]:
        def producer():
            qs = (
                Product.objects.active().with_relations()
                .filter(compare_at_price__isnull=False, compare_at_price__gt=F("price"))
                .order_by("-sales_count")
            )
            return list(qs[:limit])

        return cache_utils.get_or_set(
            cache_utils.build_key("catalog:onsale", limit), producer, bucket="medium"
        )

    @staticmethod
    def with_3d(limit: int | None = None) -> list[Product]:
        qs = (
            Product.objects.active().with_relations()
            .exclude(model_3d="")
            .order_by("-sales_count")
        )
        return list(qs[:limit]) if limit else list(qs)

    @staticmethod
    def detail_by_slug(slug: str) -> Product | None:
        def producer():
            return Product.objects.active().with_relations().filter(slug=slug).first()

        return cache_utils.get_or_set(
            cache_utils.build_key(NS_PRODUCT, slug), producer, bucket="medium"
        )

    @staticmethod
    def detail_with_gallery(slug: str) -> Product | None:
        """Detalhe com galeria pre-carregada (sem cache: objeto + prefetch)."""
        return (
            Product.objects.active()
            .with_relations()
            .prefetch_related("images")
            .filter(slug=slug)
            .first()
        )

    @staticmethod
    def api_queryset(*, category_slug=None, on_promotion=None):
        """Queryset base da API (a paginacao por cursor fatia). Campos enxutos."""
        qs = (
            Product.objects.active()
            .with_relations()
            .only(
                "id", "name", "slug", "description", "price", "compare_at_price",
                "image", "image_url", "rating", "review_count", "is_on_promotion",
                "stock", "sales_count", "created_at",
                "category__id", "category__name", "category__slug",
                "category__icon", "category__accent",
            )
        )
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if on_promotion is not None:
            qs = qs.filter(is_on_promotion=on_promotion)
        return qs

    @staticmethod
    def owned_by(user, pk) -> Product | None:
        return Product.objects.filter(pk=pk, seller=user).first()

    @staticmethod
    def related(product: Product, limit: int = 4) -> list[Product]:
        def producer():
            qs = (
                Product.objects.active()
                .with_relations()
                .filter(category=product.category)
                .exclude(pk=product.pk)
                .order_by("-sales_count")
            )
            return list(qs[:limit])

        return cache_utils.get_or_set(
            cache_utils.build_key(NS_RELATED, product.pk, limit), producer, bucket="medium"
        )

    @staticmethod
    def bought_together(product: Product, limit: int = 4) -> list[Product]:
        """Quem comprou este produto tambem levou — co-compra via OrderItem.

        Ranqueia por frequencia de co-ocorrencia nos mesmos pedidos. TTL curto
        (muda conforme novas vendas chegam).
        """
        def producer():
            from apps.orders.models import OrderItem  # import tardio (evita ciclo)

            order_ids = OrderItem.objects.filter(product=product).values_list("order_id", flat=True)
            if not order_ids:
                return []
            ranked = list(
                OrderItem.objects.filter(order_id__in=order_ids)
                .exclude(product=product)
                .exclude(product__isnull=True)
                .values("product_id")
                .annotate(n=Count("id"))
                .order_by("-n")
                .values_list("product_id", flat=True)[: limit * 2]
            )
            if not ranked:
                return []
            pos = {pid: i for i, pid in enumerate(ranked)}
            prods = (
                Product.objects.active().with_relations().filter(id__in=ranked)
            )
            return sorted(prods, key=lambda p: pos.get(p.id, 999))[:limit]

        return cache_utils.get_or_set(
            cache_utils.build_key(NS_BOUGHT, product.pk, limit), producer, bucket="short"
        )

    @staticmethod
    def search(*, category_slug=None, query=None, sort="relevance", min_price=None, max_price=None, material=None):
        """Busca filtrada — retorna um QuerySet (a view pagina). TTL curto via service."""
        qs = Product.objects.active().with_relations()
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if material:
            qs = qs.filter(material=material)
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)

        ordering = {
            "new": "-created_at",
            "popular": "-sales_count",
            "price_asc": "price",
            "price_desc": "-price",
            "relevance": "-is_featured",
        }.get(sort, "-is_featured")
        return qs.order_by(ordering, "-sales_count")

    @staticmethod
    def materials() -> list[str]:
        """Materiais distintos dos produtos ativos (para o filtro)."""
        return sorted(
            m for m in Product.objects.active().order_by("material")
            .values_list("material", flat=True).distinct() if m
        )


class ReviewQuery:
    @staticmethod
    def for_product(product: Product):
        """Avaliacoes do produto, autor pre-carregado (cursor pagina na API)."""
        return (
            Review.objects.filter(product=product)
            .select_related("author")
            .order_by("-created_at")
        )

    @staticmethod
    def by_user_for_product(user, product) -> Review | None:
        if not getattr(user, "is_authenticated", False):
            return None
        return Review.objects.filter(product=product, author=user).first()

    @staticmethod
    def reviewed_product_ids(user, product_ids) -> set[int]:
        """Subconjunto de product_ids que `user` ja avaliou (1 query)."""
        if not getattr(user, "is_authenticated", False) or not product_ids:
            return set()
        return set(
            Review.objects.filter(author=user, product_id__in=product_ids)
            .values_list("product_id", flat=True)
        )


class FavoriteQuery:
    @staticmethod
    def ids_for_user(user) -> set[int]:
        """Ids de produtos favoritados por `user` (1 query, p/ context processor)."""
        if not getattr(user, "is_authenticated", False):
            return set()
        return set(
            Favorite.objects.filter(user=user).values_list("product_id", flat=True)
        )

    @staticmethod
    def products_for_user(user) -> list[Product]:
        """Produtos favoritados, com relations p/ render do card (sem cache: por usuario)."""
        if not getattr(user, "is_authenticated", False):
            return []
        return list(
            Product.objects.filter(favorited_by__user=user, is_active=True)
            .select_related("category")
            .order_by("-favorited_by__created_at")
        )

    @staticmethod
    def aggregate_for_product(product_id) -> dict:
        return Review.objects.filter(product_id=product_id).aggregate(
            avg=Avg("rating"), n=Count("id")
        )


def invalidate_catalog_cache() -> None:
    """Limpa as listagens estáveis. Chamado pelos signals em save/delete."""
    cache_utils.invalidate(
        NS_CATEGORIES,
        cache_utils.build_key(NS_FEATURED, 8),
        cache_utils.build_key(NS_FEATURED, 6),
        cache_utils.build_key(NS_NEW, 4),
        cache_utils.build_key(NS_NEW, 8),
        cache_utils.build_key("catalog:onsale", 8),
    )


def invalidate_product(slug: str) -> None:
    """Limpa o cache do detalhe de um produto especifico."""
    if slug:
        cache_utils.invalidate(cache_utils.build_key(NS_PRODUCT, slug))
