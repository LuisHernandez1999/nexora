from django.urls import path

from . import views

app_name = "lithophane"

urlpatterns = [
    path("", views.editor, name="editor"),
    path("gerar/", views.gerar, name="gerar"),
]
