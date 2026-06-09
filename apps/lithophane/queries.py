"""Consultas de rascunhos de lithophane — só ORM, sem cache (dados por usuário/sessão)."""
from __future__ import annotations

from apps.core.layers import BaseQuery

from .models import LithophaneDraft


class LithophaneQuery(BaseQuery):
    @staticmethod
    def by_id(draft_id: int) -> LithophaneDraft | None:
        return LithophaneDraft.objects.filter(pk=draft_id).first()

    @staticmethod
    def drafts_by_ids(ids) -> list[LithophaneDraft]:
        """Consumido pelo OrderService no checkout (Plan 03)."""
        return list(LithophaneDraft.objects.filter(pk__in=list(ids)))
