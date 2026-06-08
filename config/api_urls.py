"""Rotas da API JSON (cursor-paginada). Montadas em /api/."""
from django.urls import path

from apps.catalog.api import ProductListAPI, ProductReviewListAPI
from apps.promotions.api import OfferListAPI

app_name = "api"

urlpatterns = [
    path("produtos/", ProductListAPI.as_view(), name="products"),
    path("produtos/<slug:slug>/avaliacoes/", ProductReviewListAPI.as_view(), name="product_reviews"),
    path("ofertas/", OfferListAPI.as_view(), name="offers"),
]
