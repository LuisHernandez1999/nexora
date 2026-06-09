from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.detail, name="detail"),
    path("adicionar/<int:product_id>/", views.add, name="add"),
    path("atualizar/<int:product_id>/", views.update, name="update"),
    path("remover/<int:product_id>/", views.remove, name="remove"),
    path("lithophane/adicionar/<int:draft_id>/", views.add_litho, name="add_litho"),
    path("lithophane/remover/<int:draft_id>/", views.remove_litho, name="remove_litho"),
    path("cupom/", views.apply_coupon, name="apply_coupon"),
    path("limpar/", views.clear, name="clear"),
]
