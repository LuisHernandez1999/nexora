"""Admin dos rascunhos de lithophane — a equipe vê a foto + specs para fechar o orçamento."""
from django.contrib import admin

from .models import LithophaneDraft


@admin.register(LithophaneDraft)
class LithophaneDraftAdmin(admin.ModelAdmin):
    list_display = ("__str__", "format", "size", "thickness", "user", "created_at")
    list_filter = ("format",)
    readonly_fields = ("created_at", "updated_at")
