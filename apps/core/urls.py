from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    # Home removida — a raiz abre a página "Sobre" (landing).
    path("", views.AboutView.as_view(), name="home"),
    path("sobre/", views.AboutView.as_view(), name="about"),
]
