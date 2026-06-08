from django.urls import path

from . import views

app_name = "seller"

urlpatterns = [
    path("", views.products, name="products"),
    path("produtos/novo/", views.product_new, name="product_new"),
    path("produtos/<int:pk>/editar/", views.product_edit, name="product_edit"),
    path("ofertas/", views.offers, name="offers"),
    path("pedidos/", views.orders, name="orders"),
    path("rastreio/", views.tracking, name="tracking"),
]
