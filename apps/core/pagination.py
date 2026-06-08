"""Paginacao por cursor compartilhada pela API.

Cursor > offset/page para listas grandes e "scroll infinito": o cursor aponta
para a posicao no indice (created_at), entao a profundidade da pagina nao
degrada a query (sem `OFFSET N`) e itens novos no topo nao deslocam a janela.

A resposta sai camelCase pelo renderer global (results, next, previous).
"""
from __future__ import annotations

from rest_framework.pagination import CursorPagination


class NexoraCursorPagination(CursorPagination):
    page_size = 12
    page_size_query_param = "pageSize"
    max_page_size = 48
    cursor_query_param = "cursor"
    ordering = "-created_at"  # precisa de um campo monotonico e indexado


class OfferCursorPagination(NexoraCursorPagination):
    page_size = 9


class ReviewCursorPagination(NexoraCursorPagination):
    page_size = 8
