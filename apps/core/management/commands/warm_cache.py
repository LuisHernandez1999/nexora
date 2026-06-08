"""Pre-aquece o cache das listagens quentes (pre-warm).

Roda as mesmas queries cacheadas que a home/catalogo/ofertas usam, populando
o cache ANTES do primeiro acesso do usuario — assim ninguem paga o "cache miss".

Uso:  python manage.py warm_cache
Bom para rodar pos-deploy ou via cron/celery-beat apos invalidacoes em massa.
"""
from __future__ import annotations

import time

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Pre-aquece o cache de catalogo, promocoes e ofertas."

    def handle(self, *args, **options):
        from apps.catalog.queries import CategoryQuery, ProductQuery
        from apps.promotions.queries import OfferQuery, PromotionQuery

        started = time.monotonic()
        warmers = [
            ("categorias em destaque", lambda: CategoryQuery.highlighted()),
            ("produtos em destaque", lambda: ProductQuery.featured(8)),
            ("lancamentos (4)", lambda: ProductQuery.new_arrivals(4)),
            ("lancamentos (8)", lambda: ProductQuery.new_arrivals(8)),
            ("produtos em oferta", lambda: ProductQuery.on_sale(8)),
            ("hero da home", lambda: PromotionQuery.hero()),
            ("promocoes ativas (3)", lambda: PromotionQuery.active(3)),
            ("promocoes ativas (6)", lambda: PromotionQuery.active(6)),
            ("ofertas reais (6)", lambda: OfferQuery.featured(6)),
        ]

        for label, fn in warmers:
            count = _safe_len(fn())
            self.stdout.write(self.style.SUCCESS(f"  [ok] {label}: {count} item(ns)"))

        elapsed = (time.monotonic() - started) * 1000
        self.stdout.write(self.style.SUCCESS(f"\nCache pre-aquecido em {elapsed:.0f} ms."))


def _safe_len(value) -> int:
    if value is None:
        return 0
    try:
        return len(value)
    except TypeError:
        return 1
