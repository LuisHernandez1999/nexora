"""Serviços do catálogo — orquestram queries + mappers para as views."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.core.paginator import Paginator
from django.db import transaction
from django.utils.text import slugify

from apps.core.layers import BaseService

from .mappers import CategoryMapper, ProductMapper, ReviewMapper
from .models import MAX_PRODUCT_IMAGES, Product, ProductImage, Review
from .queries import (
    CategoryQuery,
    ProductQuery,
    ReviewQuery,
    invalidate_catalog_cache,
    invalidate_product,
)

PAGE_SIZE = 12
REVIEW_PREVIEW = 6  # avaliacoes mostradas no detalhe (resto via API/cursor)


class CatalogService(BaseService):
    # ---- home ----
    @staticmethod
    def list_highlighted_categories() -> list[dict]:
        return CategoryMapper.to_list(CategoryQuery.highlighted())

    @staticmethod
    def list_featured_products(limit: int = 8) -> list[dict]:
        return ProductMapper.to_list(ProductQuery.featured(limit))

    @staticmethod
    def list_new_arrivals(limit: int = 4) -> list[dict]:
        return ProductMapper.to_list(ProductQuery.new_arrivals(limit))

    @staticmethod
    def list_on_sale(limit: int = 8) -> list[dict]:
        return ProductMapper.to_list(ProductQuery.on_sale(limit))

    # ---- galeria de modelos 3D ----
    @staticmethod
    def gallery() -> dict[str, Any]:
        return {"products": ProductMapper.to_list(ProductQuery.with_3d())}

    # ---- catálogo (listagem com filtros + paginação) ----
    @staticmethod
    def browse(params, page: int = 1) -> dict[str, Any]:
        category_slug = params.get("categoria") or None
        query = params.get("q") or None
        sort = params.get("sort") or "relevance"
        material = params.get("material") or None
        min_price = _to_decimal(params.get("min"))
        max_price = _to_decimal(params.get("max"))

        qs = ProductQuery.search(
            category_slug=category_slug,
            query=query,
            sort=sort,
            min_price=min_price,
            max_price=max_price,
            material=material,
        )
        paginator = Paginator(qs, PAGE_SIZE)
        page_obj = paginator.get_page(page)

        active_category = None
        if category_slug:
            cat = CategoryQuery.by_slug(category_slug)
            active_category = CategoryMapper.to_dict(cat) if cat else None

        from apps.promotions.services import PromotionService

        return {
            "products": ProductMapper.to_list(page_obj.object_list),
            "page_obj": page_obj,
            "paginator": paginator,
            "total": paginator.count,
            "categories": CategoryMapper.to_list(CategoryQuery.all_with_counts()),
            "active_category": active_category,
            "current_sort": sort,
            "materials": ProductQuery.materials(),
            "active_material": material or "",
            "query": query or "",
            "promotions": PromotionService.list_active_promotions(limit=5),
            "flash_sale": ProductMapper.to_list(ProductQuery.on_sale(8)),
            "best_sellers": ProductMapper.to_list(ProductQuery.featured(6)),
        }

    # ---- detalhe ----
    @staticmethod
    def get_detail(slug: str, *, user=None) -> dict[str, Any] | None:
        product = ProductQuery.detail_with_gallery(slug)
        if not product:
            return None
        reviews = ReviewQuery.for_product(product)[:REVIEW_PREVIEW]
        return {
            "product": ProductMapper.to_detail(product),
            "related": ProductMapper.to_list(ProductQuery.related(product)),
            "reviews": ReviewMapper.to_list(reviews),
            "review_summary": ReviewService.summary(product),
            "review_state": ReviewService.eligibility(user, product),
            "product_obj": product,
        }


class ProductWriteService(BaseService):
    """Escrita de produto pelo vendedor (regra: so vendedor cria/edita o seu)."""

    @staticmethod
    @transaction.atomic
    def create(seller, form, files=None, image_urls=None) -> Product:
        product: Product = form.save(commit=False)
        product.seller = seller
        product.slug = _unique_slug(product.name)
        product.save()
        ProductWriteService._save_images(product, files, image_urls, replace=False)
        invalidate_catalog_cache()
        return product

    @staticmethod
    @transaction.atomic
    def update(product: Product, form, files=None, image_urls=None) -> Product:
        product = form.save()
        replace = bool(_clean_files(files) or _clean_urls(image_urls))
        ProductWriteService._save_images(product, files, image_urls, replace=replace)
        invalidate_catalog_cache()
        invalidate_product(product.slug)
        return product

    @staticmethod
    def _save_images(product: Product, files, image_urls, *, replace: bool) -> None:
        files = _clean_files(files)
        urls = _clean_urls(image_urls)
        if not files and not urls:
            return
        if replace:
            product.images.all().delete()
        rows: list[ProductImage] = []
        position = 0
        for f in files[:MAX_PRODUCT_IMAGES]:
            rows.append(ProductImage(product=product, image=f, alt=product.name, position=position))
            position += 1
        for u in urls[: max(0, MAX_PRODUCT_IMAGES - len(rows))]:
            rows.append(ProductImage(product=product, image_url=u, alt=product.name, position=position))
            position += 1
        for row in rows:
            row.save()  # save individual: ImageField precisa persistir o arquivo


class ReviewService(BaseService):
    """Avaliacoes de produto. Regra central: so quem comprou pode avaliar."""

    @staticmethod
    def has_purchased(user, product) -> bool:
        if not getattr(user, "is_authenticated", False):
            return False
        from apps.orders.models import Order, OrderItem  # import tardio (evita ciclo)

        return OrderItem.objects.filter(
            order__user=user,
            product=product,
            order__payment_status=Order.PaymentStatus.APPROVED,
        ).exists()

    @staticmethod
    def eligibility(user, product) -> dict[str, Any]:
        if not getattr(user, "is_authenticated", False):
            return {"can_review": False, "reason": "anon", "existing": None}
        existing = ReviewQuery.by_user_for_product(user, product)
        if existing:
            return {"can_review": False, "reason": "done", "existing": ReviewMapper.to_dict(existing)}
        if not ReviewService.has_purchased(user, product):
            return {"can_review": False, "reason": "not_purchased", "existing": None}
        return {"can_review": True, "reason": "ok", "existing": None}

    @staticmethod
    @transaction.atomic
    def add(user, product, *, rating: int, title: str = "", comment: str = "") -> tuple[bool, str]:
        if not ReviewService.has_purchased(user, product):
            return False, "Voce so pode avaliar produtos que comprou."
        if ReviewQuery.by_user_for_product(user, product):
            return False, "Voce ja avaliou este produto."
        Review.objects.create(
            product=product, author=user,
            rating=max(1, min(5, int(rating))),
            title=title.strip(), comment=comment.strip(),
        )
        # media/contagem + invalidacao de cache: feitos pelo signal de Review
        return True, "Avaliacao publicada. Obrigado!"

    @staticmethod
    def recompute(product_id) -> None:
        agg = ReviewQuery.aggregate_for_product(product_id)
        avg = agg.get("avg")
        Product.objects.filter(pk=product_id).update(
            rating=round(Decimal(str(avg)), 2) if avg is not None else Decimal("5.0"),
            review_count=agg.get("n") or 0,
        )

    @staticmethod
    def summary(product) -> dict[str, Any]:
        return {
            "avg": round(float(product.rating), 1),
            "count": product.review_count,
            "rating_int": int(round(float(product.rating))),
        }


def _unique_slug(name: str) -> str:
    base = slugify(name) or "produto"
    slug = base
    i = 2
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base}-{i}"
        i += 1
    return slug


def _clean_files(files) -> list:
    return [f for f in (files or []) if f]


def _clean_urls(urls) -> list[str]:
    return [u.strip() for u in (urls or []) if u and u.strip()]


def _to_decimal(value):
    if not value:
        return None
    try:
        return Decimal(str(value).replace(",", "."))
    except (ValueError, ArithmeticError):
        return None
