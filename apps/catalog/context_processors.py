"""Expoe os ids de produtos favoritados do usuario em todos os templates.

Usado pelo coracao nos cards/detalhe: `{% if product.id in favorite_ids %}`.
Uma unica query por request (apenas para usuarios autenticados).
"""
from __future__ import annotations

from .queries import FavoriteQuery


def favorites(request):
    return {"favorite_ids": FavoriteQuery.ids_for_user(getattr(request, "user", None))}
