# Coding Conventions

**Analysis Date:** 2026-06-05

This is a Django 5.2 + DRF e-commerce project ("Nexora", impressão 3D). It follows a strict per-app layered architecture ("cada macaco no seu galho") and a Portuguese (pt-br) user-facing convention. The conventions below are observed consistently across every app in `apps/` and are documented in `README.md` and `apps/core/layers.py`.

## Layered Architecture Convention (most important)

Every app under `apps/` repeats the same file layout, each file with a single responsibility. This is the dominant convention in the codebase and new code MUST follow it.

| File | Responsibility | Rules |
|------|----------------|-------|
| `models.py` | Schema + business **properties without side effects** | No HTTP, no queries-with-cache logic. See `Product.has_discount`, `Product.discount_pct` in `apps/catalog/models.py:102-119`. |
| `queries.py` | **Only ORM.** Optimized querysets (`select_related`/`prefetch`) + caching | No business rules, no HTTP. All reads go through here. See `apps/catalog/queries.py`. |
| `services.py` | Business-rule orchestration. **The only layer that writes to the DB.** | Uses `queries` + `mappers`. Wrap multi-write flows in `@transaction.atomic`. See `apps/orders/services.py:24-82`. |
| `mappers.py` | `Model -> dict/DTO` for templates and serializers | Subclass `BaseMapper[Model]`, implement `to_dict`. See `apps/catalog/mappers.py`. |
| `serializers.py` | DRF input/output for the API | `ModelSerializer` with explicit `fields` tuple. See `apps/catalog/serializers.py`. |
| `views.py` | **Thin.** request → service → response | No ORM, no business logic. See `apps/catalog/views.py` (entire file is 21 lines). |
| `forms.py` | Form definitions + validation + `to_*_data()` conversion helpers | See `apps/orders/forms.py`. |
| `templates/<app>/` | Presentation only | See template conventions below. |

Base classes live in `apps/core/layers.py`:
- `BaseMapper[M]` — provides `to_list()`, requires `to_dict()`.
- `BaseService` / `BaseQuery` — intent markers (empty base classes).

**When adding a feature:** put reads in `queries.py`, writes/orchestration in `services.py`, Model→dict conversion in `mappers.py`, and keep the view a 3-line delegation to a service method.

## Portuguese (pt-br) Language Convention

The project is fully localized to Brazilian Portuguese. This is mandatory for all user-facing strings and model metadata.

**Model fields** — first positional arg is always a pt-br `verbose_name`, lowercase:
```python
name = models.CharField("nome", max_length=80, unique=True)        # apps/catalog/models.py:17
price = models.DecimalField("preço", max_digits=10, decimal_places=2)
```
**Model Meta** — `verbose_name` / `verbose_name_plural` in pt-br, lowercase:
```python
class Meta:
    verbose_name = "categoria"
    verbose_name_plural = "categorias"
```
**`help_text`** — pt-br, full sentences (e.g. `apps/catalog/models.py:21`, `:62`, `:68`).

**`TextChoices` labels** — pt-br human labels (e.g. `apps/orders/models.py:18-34`: `"Aguardando pagamento"`, `"Em produção"`).

**Form `label=` / error messages** — pt-br (`apps/orders/forms.py`, `apps/accounts/forms.py`: `"Já existe uma conta com este e-mail."`).

**Docstrings, comments, UI copy** — pt-br throughout (e.g. `messages.success(request, f"Pedido {order.number} criado com sucesso!")`).

**Settings:** `LANGUAGE_CODE = "pt-br"`, `TIME_ZONE = "America/Sao_Paulo"`, `USE_I18N = True`, `USE_TZ = True` (`config/settings/base.py:178-181`).

**URL paths** are also pt-br (`config/urls.py`: `conta/`, `catalogo/`, `promocoes/`, `carrinho/`, `pedidos/`).

## Naming Patterns

**Files:** lowercase, matching the layer role (`queries.py`, `services.py`, `mappers.py`). No deviation.

**Classes:**
- Services: `<Domain>Service` (`CatalogService`, `OrderService`, `PaymentService`).
- Queries: `<Model>Query` (`ProductQuery`, `CategoryQuery`, `OrderQuery`, `AddressQuery`).
- Mappers: `<Model>Mapper` (`ProductMapper`, `CategoryMapper`, `OrderMapper`).
- Custom QuerySets: `<Model>QuerySet` (`ProductQuerySet` in `apps/catalog/models.py:43`).
- Nested enums: `class Status(models.TextChoices)`, `class Payment(...)` inside the Model.

**Functions/methods:** `snake_case`. Service read methods use `list_*` / `get_*` / `browse` (`list_featured_products`, `get_detail`). Query methods are concise verbs/nouns (`highlighted`, `by_slug`, `search`, `related`).

**Module-private helpers:** leading underscore (`_to_decimal` in `apps/catalog/services.py:84`, `_initial_from_address` in `apps/orders/views.py:60`, `_bust_catalog_cache` in `apps/catalog/signals.py:13`).

**Constants:** `UPPER_SNAKE` module-level (`PAGE_SIZE = 12`, `NEW_PRODUCT_WINDOW_DAYS = 21`, cache namespaces `NS_FEATURED`, `NS_CATEGORIES`).

**Variables:** `snake_case`. Note: a few locals inside pt-br domain helpers are pt-br (`inteiro`, `decimal`, `grupos`, `sinal`, `valor`, `cents` in `apps/core/formatting.py` / `apps/orders/payments.py`).

## Code Style

**Type hints:** Every module starts with `from __future__ import annotations` and uses modern hints (`list[dict]`, `str | None`, `dict[str, Any]`). Methods annotate params and return types. Generics used in base classes (`BaseMapper(Generic[M])`).

**Module docstrings:** Every `.py` file opens with a one-line (or short paragraph) pt-br docstring describing its role, e.g. `"""Serviços do catálogo — orquestram queries + mappers para as views."""`.

**Static methods:** Service/query/mapper methods are almost always `@staticmethod` (or `@classmethod` for mappers). These classes are namespaces, not stateful objects.

**Formatting:** No formatter/linter config present (no `.ruff.toml`, `.flake8`, `setup.cfg`, `pyproject.toml`, `.pre-commit-config`). Style is hand-maintained but consistent: 4-space indent, ~100-char lines, double quotes, trailing commas in multi-line literals. `# noqa: F401` used for intentional unused imports (signals registration). Match the surrounding style; there is no automated enforcement.

## Import Organization

Observed 3-group order (stdlib → Django/third-party → local), blank-line separated:
```python
from __future__ import annotations          # always first

from decimal import Decimal                 # stdlib

from django.db import models                # Django / third-party
from rest_framework import serializers

from apps.core.models import TimeStampedModel  # cross-app local (absolute)

from .models import Category, Product       # intra-app relative
```
- Cross-app imports use **absolute** paths (`from apps.core.cache import ...`).
- Intra-app imports use **relative** paths (`from .models import ...`, `from .queries import ProductQuery`).
- **Deferred imports** to break circular dependencies are placed inside functions (e.g. `from apps.promotions.services import PromotionService` inside `CatalogService.browse`, `apps/catalog/services.py:58`).

## Error Handling

**Domain exceptions:** Custom exceptions defined in the service module and caught in the view.
```python
# apps/orders/services.py:20
class EmptyCartError(Exception):
    """Tentativa de fechar pedido com carrinho vazio."""
```
The view catches it and converts to a user message (`apps/orders/views.py:28-30`).

**Not-found:** Queries/services return `None` on miss; the view raises `Http404` with a pt-br message:
```python
context = CatalogService.get_detail(slug)
if context is None:
    raise Http404("Produto não encontrado.")   # apps/catalog/views.py:18-19
```

**Form validation:** `clean_<field>()` and `clean()` raise `forms.ValidationError` / `add_error()` with pt-br messages (`apps/orders/forms.py:36-51`, `apps/accounts/forms.py:22-26`).

**User feedback:** `django.contrib.messages` (`messages.success/error/info`) drives the toast UI rendered in `apps/core/templates/base.html:21-33`.

**Defensive parsing:** Helpers swallow conversion errors and return safe defaults (`_to_decimal` returns `None` on `ValueError/ArithmeticError`; `format_brl(None)` returns `"—"`).

**Transactions:** DB-writing flows are decorated `@transaction.atomic` and use `F()` expressions for race-safe counters (`apps/orders/services.py:26,67-75`).

## Caching Convention

Reads of "stable" listings are cached through the shared helper `apps/core/cache.py`, never via direct `cache.set` in app code.
- `cache_utils.get_or_set(key, producer, bucket=...)` with a closure `producer()` that returns the materialized list.
- Keys built with `cache_utils.build_key(NS_*, *parts)`; namespaces are module-level `NS_*` constants.
- TTL buckets: `"short"` / `"medium"` / `"long"`, resolved from `settings.CACHE_TTL` (`config/settings/base.py:154-158`).
- Invalidation lives in `queries.py` (`invalidate_catalog_cache`) and is triggered by `post_save`/`post_delete` signals (`apps/catalog/signals.py`). Signals are wired in `AppConfig.ready()` (`apps/catalog/apps.py:9-10`).

## Logging

No logging framework configured and no `logging.getLogger` usage. User-facing feedback goes through `django.contrib.messages`. Dev email is routed to console (`config/settings/dev.py:24`). If logging is needed, add a `LOGGING` config to `config/settings/base.py`.

## Comments

- Module docstrings on every file (pt-br).
- Inline section markers in pt-br, e.g. `# ---- home ----`, `# --- entrega ---`, `# baixa de estoque + métrica de vendas (atômico via F)`.
- `# pragma: no cover` marks abstract methods (`apps/core/layers.py:26`).
- Comments explain *why* (e.g. snapshot rationale in `apps/orders/models.py:1-6`), not *what*.

## Function / Module Design

- **Services/queries/mappers** are stateless namespace classes of `@staticmethod`/`@classmethod`.
- **Mappers** return plain `dict`s with display-ready values (e.g. `price_display` via `format_brl`, `monogram`, `url` via `get_absolute_url()`). `to_detail()` extends `to_dict()` rather than duplicating it (`apps/catalog/mappers.py:52-65`).
- **Forms** expose a `to_<x>_data()` method converting validated data into the dict the service expects (`apps/orders/forms.py:53`), keeping the service decoupled from the form.
- **Models** keep computed business logic as read-only `@property` (no side effects).

## DRF / API Convention

- `REST_FRAMEWORK` is configured with **camelCase** render/parse (`djangorestframework_camel_case`), `DjangoFilterBackend`, and `PageNumberPagination` `PAGE_SIZE=12` (`config/settings/base.py:203-213`).
- Serializers are `ModelSerializer` with an explicit `fields` tuple; computed model properties exposed as read-only fields (`apps/catalog/serializers.py:15-28`).
- NOTE: serializers exist in every app but **no API routes/viewsets are wired** in `config/urls.py` or app `urls.py` (all current endpoints are server-rendered HTML). The serializer layer is scaffolding for a future public API (README "Próximos passos"). Also note `apps/catalog/serializers.py` references `emoji` fields that no longer exist on the model (see CONCERNS).

## Template Conventions

Templates live in `apps/<app>/templates/<app>/` (app-namespaced). Shared/layout templates live in `apps/core/templates/`.

**Single base template:** `apps/core/templates/base.html` defines blocks `title`, `extra_head`, `content`, `extra_js`. All pages `{% extends "base.html" %}`.

**Partials convention:** reusable fragments live in a `partials/` subdirectory and are documented with a leading `{# ... #}` comment describing the expected context variable:
- `apps/core/templates/core/partials/` — `navbar.html`, `footer.html`, `icons.html` (SVG sprite), `field.html`.
- `apps/catalog/templates/catalog/partials/product_card.html`.

Partials state their contract in a comment, e.g.:
```django
{# Espera um dict `product` (ver catalog.mappers.ProductMapper). #}
{# Renderiza um campo... Uso: {% include "core/partials/field.html" with field=form.email %} #}
```
Partials consume the **mapper dict** shape, not Model instances directly (e.g. `product.price_display`, `product.monogram`, `product.url`).

**Form rendering:** fields are rendered via the shared `core/partials/field.html` partial (`{% include ... with field=form.x %}`), which handles label, checkbox layout, help text, and errors uniformly.

**Icons:** inline SVG sprite (`icons.html`) referenced with `<svg class="icon"><use href="#i-cart"></use></svg>`. No icon font, no JS framework.

**Loaded tags:** `{% load static humanize %}` in base; CSRF via `{% csrf_token %}` in all POST forms.

## CSS Design-Token Convention

A single hand-written stylesheet `static/css/theme.css` (~50KB, no framework, mobile-first). All theming flows through CSS custom properties ("tokens") declared in `:root` at the top of the file (`static/css/theme.css:6-46`):
- **Surfaces:** `--bg`, `--bg-soft`, `--bg-card`, `--bg-elevated`, `--border`, `--border-soft`.
- **Text:** `--text`, `--text-muted`, `--text-dim`.
- **Accent (blue):** `--accent`, `--accent-2`, `--accent-strong`, `--accent-soft`, `--accent-glow`.
- **Status:** `--success`, `--danger`, `--warning`.
- **Geometry/motion:** `--radius`, `--radius-sm`, `--radius-lg`, `--shadow`, `--shadow-glow`, `--container`, `--header-h`, `--ease`.
- **Fonts:** `--font`, `--font-display`.

Rules **must** reference these tokens (`background: var(--bg)`, `color: var(--text)`) rather than literal colors. Per-instance overrides are passed via inline CSS vars (`style="--acc:{{ product.accent }}"` in `product_card.html`). Theme switching uses `data-theme` on `<html>` with an early inline script in `base.html:5` reading `localStorage('nexora-theme')`; toggled in `static/js/app.js:20-28`.

The stylesheet is organized into clearly commented sections (`/* --- botões */`, `/* --- produtos */`, `/* --- carrinho */`, etc.). Class naming is BEM-ish kebab-case (`.product-card`, `.product-thumb`, `.badge-discount`, `.btn-primary`, `.btn-block`).

## Front-end JS Convention

Single vanilla file `static/js/app.js` — IIFE with `"use strict"`, no framework, no build step. Progressive-enhancement style: every feature guards on element existence (`if (toggle && nav)`) and feature-detects APIs (`"IntersectionObserver" in window`). Loaded with `defer` in `base.html:40`.

## Settings Convention

Split settings under `config/settings/` (`base.py`, `dev.py`, `prod.py`); dev/prod do `from .base import *`. Environment read through a dependency-free helper `config/env.py` (`env`, `env_bool`, `env_int`, `env_list`, `load_dotenv`) — no `django-environ`. Backends switch by env var presence (SQLite↔Postgres, LocMem↔Redis) with **no code changes**. Secrets via `.env` (gitignored; `.env.example` committed).

---

*Convention analysis: 2026-06-05*
