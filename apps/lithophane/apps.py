"""Configuração do app de lithophane."""
from django.apps import AppConfig


class LithophaneConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.lithophane"
    verbose_name = "Lithophane"
