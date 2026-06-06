---
phase: 03-visualizador-3d-galeria
plan: 02
subsystem: catalog
tags: [gallery, 3d, navigation, layered-architecture]
requires:
  - "Fase 2: campo Product.model_3d (FileField GLB) e ProductMapper"
  - "catalog:product_list, catalog:product_detail (cards linkam ao detalhe)"
provides:
  - "ProductQuery.with_3d(limit) — produtos com GLB por -sales_count"
  - "CatalogService.gallery() — context {products} mapeado"
  - "views.models_3d + rota catalog:models_3d (/catalogo/modelos-3d/)"
  - "template catalog/models_3d.html (galeria reusando product_card)"
  - "link 'Modelos 3D' na navbar (.main-nav)"
affects:
  - "apps/catalog (queries/services/views/urls/templates)"
  - "apps/core/templates/core/partials/navbar.html"
tech-stack:
  added: []
  patterns:
    - "Camadas query → service → view → url → template (espelha on_sale/browse)"
    - "Galeria reusa partials/product_card.html; sem viewer por card (perf)"
key-files:
  created:
    - apps/catalog/templates/catalog/models_3d.html
  modified:
    - apps/catalog/queries.py
    - apps/catalog/services.py
    - apps/catalog/views.py
    - apps/catalog/urls.py
    - apps/core/templates/core/partials/navbar.html
decisions:
  - "with_3d sem cache (simplicidade; cache era opcional no CONTEXT/RESEARCH); invalidate_catalog_cache não tocado"
  - "Galeria não carrega o script do model-viewer (cards só linkam ao detalhe)"
  - "Empty state usa #i-box (símbolo existente no sprite icons.html)"
metrics:
  duration_min: 1
  completed: "2026-06-06"
  tasks: 2
  files: 5
---

# Phase 3 Plan 2: Galeria "Modelos 3D" Summary

Aba/galeria dedicada (VIEW-04) que lista somente produtos com modelo 3D, via a cadeia em camadas `ProductQuery.with_3d` → `CatalogService.gallery` → `views.models_3d` → rota `catalog:models_3d` → `models_3d.html`, com link na navbar; cards levam ao detalhe (onde fica o viewer), sem viewer embutido por card.

## What Was Built

- **ProductQuery.with_3d(limit=None)** — `Product.objects.active().with_relations().exclude(model_3d="").order_by("-sales_count")`; retorna só produtos com GLB. Sem cache (decisão de simplicidade).
- **CatalogService.gallery()** — retorna `{"products": ProductMapper.to_list(ProductQuery.with_3d())}`, espelhando o shape simples dos siblings.
- **views.models_3d(request)** — view fina: `render(request, "catalog/models_3d.html", CatalogService.gallery())`.
- **urls** — `path("modelos-3d/", views.models_3d, name="models_3d")`; resolve para `/catalogo/modelos-3d/`.
- **catalog/models_3d.html** (novo) — extends base, hero curto "Modelos 3D", `product-grid` reusando `partials/product_card.html`, empty state pt-br com CTA para o catálogo. Reusa classes existentes (`section`, `container`, `search-hero`, `eyebrow-center`, `product-grid`, `empty-state`, `reveal`); zero CSS novo; sem `<model-viewer>`.
- **navbar.html** — link `<a href="{% url 'catalog:models_3d' %}">Modelos 3D</a>` na `.main-nav`, após "Lançamentos".

## Verification

- `python manage.py check --settings=config.settings.prod` → "System check identified no issues", exit 0.
- `reverse('catalog:models_3d')` → `/catalogo/modelos-3d/`.
- Verificação automatizada do plano (Task 2): template tem extends base, reuso de product_card, empty-state e "Modelos 3D"; navbar tem o link; galeria NÃO contém `<model-viewer>` → "OK".

## Deviations from Plan

None — plano executado exatamente como escrito.

## Authentication Gates

None.

## Deferred Issues

- Render end-to-end via `django.test.Client` com `config.settings.prod` não roda neste ambiente: `ModuleNotFoundError: No module named 'whitenoise'` (dependência de prod ausente no ambiente local). Fora do escopo (causa pré-existente do ambiente, não do código). A verificação do plano (`manage.py check`) já cobre e passa; o render visual fica para a phase verification (human_verification do plano).

## Known Stubs

None — a galeria consome dados reais via `ProductQuery.with_3d`; o empty state é comportamento intencional pt-br quando não há produtos com GLB.

## Self-Check: PASSED
