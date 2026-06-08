"""Modelos do catálogo."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.models import TimeStampedModel

NEW_PRODUCT_WINDOW_DAYS = 21
MAX_PRODUCT_IMAGES = 4  # regra de negocio: ate 4 fotos por produto


class Category(TimeStampedModel):
    name = models.CharField("nome", max_length=80, unique=True)
    slug = models.SlugField("slug", max_length=90, unique=True)
    icon = models.CharField(
        "ícone", max_length=20, default="cube",
        help_text="Nome do ícone SVG do sprite (ex.: cube, tag, bolt, box, layers).",
    )
    accent = models.CharField(
        "cor de destaque", max_length=7, default="#3b82f6",
        help_text="Hex usado no card e no placeholder da categoria.",
    )
    description = models.TextField("descrição", blank=True)
    is_highlighted = models.BooleanField("destaque na home", default=True)
    order = models.PositiveIntegerField("ordem", default=0)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("catalog:product_list") + f"?categoria={self.slug}"


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def with_relations(self):
        # prefetch da galeria evita N+1 ao montar a capa nas listagens
        return self.select_related("category").prefetch_related("images")


class Product(TimeStampedModel):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products", verbose_name="categoria"
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="products", verbose_name="vendedor",
    )
    name = models.CharField("nome", max_length=140)
    slug = models.SlugField("slug", max_length=160, unique=True)
    description = models.TextField("descrição", blank=True)

    price = models.DecimalField("preço", max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(
        "preço cheio", max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Preço antigo riscado. Deixe vazio se não houver desconto.",
    )

    image = models.ImageField("imagem", upload_to="products/", blank=True)
    image_url = models.URLField(
        "imagem (URL externa)", max_length=500, blank=True,
        help_text="Usada quando não há upload. Útil para demo/seed.",
    )

    stock = models.PositiveIntegerField("estoque", default=10)
    rating = models.DecimalField(
        "avaliacao", max_digits=3, decimal_places=2, default=Decimal("5.0"),
        help_text="Media das avaliacoes; recalculada a cada review (denormalizada).",
    )
    review_count = models.PositiveIntegerField("numero de avaliacoes", default=0)
    sales_count = models.PositiveIntegerField("vendas", default=0)

    # Promocao: ligada a oferta real (apps.promotions.Offer). Flag denormalizado
    # no produto para filtrar/listar sem JOIN.
    is_on_promotion = models.BooleanField("em promocao", default=False)

    # Específicos de impressão 3D
    material = models.CharField("material", max_length=60, default="PLA")
    dimensions = models.CharField("dimensões", max_length=80, blank=True)
    print_time_hours = models.PositiveIntegerField("tempo de impressão (h)", default=4)

    is_featured = models.BooleanField("destaque", default=False)
    is_active = models.BooleanField("ativo", default=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "produto"
        verbose_name_plural = "produtos"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "is_featured"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["-sales_count"]),
            models.Index(fields=["is_active", "is_on_promotion"]),
            models.Index(fields=["seller", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    # --- propriedades de negócio (sem efeito colateral) ---
    @property
    def has_discount(self) -> bool:
        return bool(self.compare_at_price and self.compare_at_price > self.price)

    @property
    def discount_pct(self) -> int:
        if not self.has_discount:
            return 0
        diff = (self.compare_at_price - self.price) / self.compare_at_price
        return int(round(diff * 100))

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    @property
    def is_new(self) -> bool:
        return self.created_at >= timezone.now() - timedelta(days=NEW_PRODUCT_WINDOW_DAYS)

    @property
    def cover_image_url(self) -> str:
        """Primeira foto da galeria; cai para o upload/URL legado do produto."""
        first = self.images.first() if self.pk else None
        if first:
            return first.url
        if self.image:
            return self.image.url
        return self.image_url or ""


class ProductImage(TimeStampedModel):
    """Foto da galeria do produto (ate 4 por produto; regra no service/form)."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images", verbose_name="produto"
    )
    image = models.ImageField("imagem", upload_to="products/gallery/", blank=True)
    image_url = models.URLField("imagem (URL externa)", max_length=500, blank=True)
    alt = models.CharField("descricao da imagem", max_length=140, blank=True)
    position = models.PositiveSmallIntegerField("posicao", default=0)

    class Meta:
        verbose_name = "foto do produto"
        verbose_name_plural = "fotos do produto"
        ordering = ["position", "id"]
        indexes = [models.Index(fields=["product", "position"])]

    def __str__(self) -> str:
        return f"Foto {self.position + 1} de {self.product_id}"

    @property
    def url(self) -> str:
        return self.image.url if self.image else (self.image_url or "")


class Review(TimeStampedModel):
    """Avaliacao de produto. Regra: so quem comprou o produto pode avaliar."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews", verbose_name="produto"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews", verbose_name="autor"
    )
    rating = models.PositiveSmallIntegerField(
        "nota", default=5, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField("titulo", max_length=120, blank=True)
    comment = models.TextField("comentario", blank=True)

    class Meta:
        verbose_name = "avaliacao"
        verbose_name_plural = "avaliacoes"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["product", "author"], name="uniq_review_per_user_product")
        ]
        indexes = [models.Index(fields=["product", "-created_at"])]

    def __str__(self) -> str:
        return f"{self.rating}/5 — {self.product_id} por {self.author_id}"
