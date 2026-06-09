from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("modelos-3d/", views.models_3d, name="models_3d"),
    path("p/<slug:slug>/", views.product_detail, name="product_detail"),
    path("avaliar/<int:product_id>/", views.review_create, name="review_create"),
]
