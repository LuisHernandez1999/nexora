from django.urls import path

from . import views

app_name = "seller"

urlpatterns = [
    path("", views.products, name="products"),
    path("pedidos/", views.orders, name="orders"),
    path("rastreio/", views.tracking, name="tracking"),
]
