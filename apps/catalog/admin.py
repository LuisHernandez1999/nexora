from django.contrib import admin

from .models import Category, Product, ProductImage, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "accent", "is_highlighted", "order")
    list_editable = ("order", "is_highlighted")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    max_num = 4  # regra de negocio: ate 4 fotos
    fields = ("image", "image_url", "alt", "position")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name", "category", "seller", "price", "compare_at_price",
        "is_on_promotion", "stock", "rating", "review_count", "is_active",
    )
    list_filter = ("category", "is_featured", "is_active", "is_on_promotion", "material")
    list_editable = ("price", "stock", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description")
    autocomplete_fields = ("category", "seller")
    readonly_fields = ("rating", "review_count", "sales_count")
    inlines = [ProductImageInline]
    fieldsets = (
        (None, {"fields": ("category", "seller", "name", "slug", "description")}),
        ("Preço", {"fields": ("price", "compare_at_price", "is_on_promotion")}),
        ("Visual", {"fields": ("image", "image_url")}),
        ("Modelos 3D", {"fields": ("model_3d", "model_stl")}),
        ("Estoque & métricas", {"fields": ("stock", "rating", "review_count", "sales_count")}),
        ("Impressão 3D", {"fields": ("material", "dimensions", "print_time_hours")}),
        ("Flags", {"fields": ("is_featured", "is_active")}),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "author", "rating", "title", "created_at")
    list_filter = ("rating",)
    search_fields = ("product__name", "author__email", "title", "comment")
    autocomplete_fields = ("product", "author")
