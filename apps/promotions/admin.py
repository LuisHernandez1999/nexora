from django.contrib import admin

from .models import Coupon, Offer, Promotion


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = (
        "product", "category", "original_price", "promo_price",
        "discount_pct", "is_active", "order", "starts_at", "ends_at",
    )
    list_filter = ("is_active", "category")
    list_editable = ("is_active", "order")
    search_fields = ("product__name",)
    autocomplete_fields = ("product", "category")
    readonly_fields = ("discount_pct",)


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "badge", "is_active", "order", "starts_at", "ends_at")
    list_filter = ("kind", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title", "subtitle")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "value", "min_order", "is_active", "used_count", "usage_limit")
    list_filter = ("discount_type", "is_active")
    search_fields = ("code",)
