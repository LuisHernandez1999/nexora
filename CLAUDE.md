<!-- GSD:project-start source:PROJECT.md -->
## Project

**L3D Labz**

Site de uma fábrica de impressão 3D chamada **L3D Labz**. É uma loja Django existente (antes "Nexora") — catálogo, carrinho, checkout, pedidos e contas — que será **rebatizada e redesenhada** com identidade visual inspirada nas cores do Luigi (verde, branco, azul) num estilo **minimalista e elegante**, com suporte a tema claro/escuro. O grande diferencial é uma **aba de visualização 3D**: o cliente abre e manipula o modelo 3D do produto (rotacionar, zoom, pan) de forma intuitiva direto no navegador, com download do arquivo STND/STL disponível.

**Core Value:** O cliente consegue **visualizar o modelo 3D do produto de forma intuitiva** num site bonito e minimalista com a marca L3D Labz — se tudo mais falhar, o visualizador 3D e a identidade da marca precisam funcionar.

### Constraints

- **Tech stack**: manter sem framework JS pesado — `<model-viewer>` é web component (1 script, zero build), encaixa no padrão vanilla atual.
- **Compatibility**: preservar a arquitetura em camadas e o padrão de design tokens existentes; rebrand via tokens, não reescrita.
- **Performance**: arquivos 3D (GLB/STL) podem ser grandes — atenção ao carregamento (lazy/poster) e ao serving de media em prod.
- **Localização**: toda copy nova em pt-br.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.13 - All backend application code (`apps/`, `config/`). The local runtime is Python 3.13.5; no explicit `python_requires` floor is pinned. Django 5.2 supports Python 3.10+.
- HTML (Django Templates) - Server-rendered UI in `apps/*/templates/` and `apps/core/templates/base.html`
- CSS - Hand-written, framework-free theme in `static/css/theme.css` (684 lines)
- JavaScript (vanilla ES) - Progressive enhancement in `static/js/app.js` (153 lines, no framework, IIFE-wrapped)
## Runtime
- CPython 3.13
- WSGI app: `config.wsgi.application`; ASGI app: `config.asgi.application` (declared in `config/settings/base.py`)
- pip with `requirements.txt`
- Lockfile: missing (no `requirements.lock`, `poetry.lock`, or `Pipfile.lock`); versions are pinned directly in `requirements.txt` with `==`
## Frameworks
- Django 5.2.12 - Web framework (MVT, server-rendered). Settings split across `config/settings/base.py`, `dev.py`, `prod.py`
- Django REST Framework 3.16.1 - Serialization layer (configured in `base.py` `REST_FRAMEWORK`). Serializers exist per app (`apps/*/serializers.py`); no DRF ViewSets/routers wired into `config/urls.py` (views are classic Django views)
- djangorestframework-camel-case 1.4.2 - camelCase JSON render/parse for DRF output
- Not detected - No test runner config (no `pytest.ini`, `tox.ini`), no `tests/` directories, and no test dependencies in `requirements.txt`. Only Django's built-in `manage.py test` is available.
- django-debug-toolbar 6.3.0 - Dev-only, injected in `config/settings/dev.py` (installed but hidden by default via `SHOW_TOOLBAR_CALLBACK: lambda request: False`)
- Custom management command(s) under `apps/catalog/management/commands/` (e.g. data seeding)
## Key Dependencies
- Django 5.2.12 - Entire application framework
- djangorestframework 3.16.1 + djangorestframework-camel-case 1.4.2 - API serialization with camelCase contract
- django-filter 25.1 - Catalog filtering; registered as DRF default filter backend (`DjangoFilterBackend`) in `base.py`
- Pillow 11.2.1 - Image handling for `ImageField` (product images `products/`, promotion banners `promotions/`)
- psycopg[binary] 3.3.3 - PostgreSQL driver (production database)
- django-redis 6.0.0 + redis 6.4.0 - Redis cache backend (optional, enabled via `REDIS_URL`)
- gunicorn 23.0.0 - Production WSGI server
- whitenoise 6.9.0 - Static file serving in production (middleware + compressed manifest storage)
## Configuration
- Custom minimal `.env` loader in `config/env.py` (no `python-dotenv` dependency). Provides typed helpers: `env`, `env_bool`, `env_int`, `env_list`, `load_dotenv`. Uses `os.environ.setdefault` (does not overwrite existing env vars).
- `.env.example` documents available variables; copy to `.env` for local overrides. Dev defaults work with no `.env` (SQLite + LocMem cache).
- `DJANGO_SETTINGS_MODULE` defaults to `config.settings.dev` (set in `manage.py`); production must set it to `config.settings.prod`.
- Key configs: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_ENGINE` / `POSTGRES_*`, `REDIS_URL`, `CACHE_TTL_SHORT/MEDIUM/LONG`, `CACHE_TIMEOUT`, `DB_CONN_MAX_AGE`.
- Settings package: `config/settings/{base,dev,prod}.py`
- `STORAGES` differs by environment: dev uses plain `StaticFilesStorage` (no collectstatic needed for runserver); prod uses `whitenoise.storage.CompressedManifestStaticFilesStorage`
- No frontend build pipeline (no `package.json`, no bundler) — CSS/JS are static, served as-is
## Database
- **Default (dev):** SQLite at `BASE_DIR/db.sqlite3` (`django.db.backends.sqlite3`)
- **Production:** PostgreSQL (`django.db.backends.postgresql`), activated when `DATABASE_ENGINE=postgres` or any `POSTGRES_DB` is set. Configured with `CONN_MAX_AGE` (default 60s), `CONN_HEALTH_CHECKS=True`, and connection pooling (`OPTIONS: {"pool": True}`).
- `DEFAULT_AUTO_FIELD = BigAutoField`
- Custom user model: `AUTH_USER_MODEL = "accounts.User"` (email login, no username; see `apps/accounts/models.py`)
## Caching
- **Default:** LocMemCache (`nexora-locmem`)
- **Optional:** Redis via `django-redis` when `REDIS_URL` set; `IGNORE_EXCEPTIONS=True`, key prefix `nexora`, and switches sessions to `cached_db`
- Centralized TTL window `CACHE_TTL = {short: 60, medium: 300, long: 3600}` (seconds) consumed by per-app `queries/` layers
## Static / CSS / Fonts / JS Approach
- **Static files:** Project-level `static/` (`STATICFILES_DIRS`), collected to `staticfiles/` (`STATIC_ROOT`). Served by WhiteNoise in production.
- **CSS:** Single hand-authored stylesheet `static/css/theme.css` — no Tailwind/Bootstrap/SASS. Mobile-first, dark theme with CSS custom properties (design tokens: `--bg`, `--accent`, `--radius`, etc.). Supports light/dark via `data-theme` attribute.
- **Fonts:** Google Fonts CDN loaded in `apps/core/templates/base.html` — "Inter" (body, `--font`) and "Sora" (display headings, `--font-display`), with `preconnect` to `fonts.googleapis.com` / `fonts.gstatic.com`. Falls back to `system-ui`.
- **JavaScript:** Single vanilla JS file `static/js/app.js`, loaded with `defer`. Framework-free progressive enhancement (mobile nav toggle, theme toggle persisted to `localStorage` key `nexora-theme`, scroll effects). No bundler, no npm.
## Platform Requirements
- Python 3.13 + virtualenv, `pip install -r requirements.txt`
- No external services required (SQLite + LocMem defaults); run via `python manage.py runserver`
- gunicorn (WSGI) + WhiteNoise for statics
- PostgreSQL database, optional Redis
- HTTPS enforced (`SECURE_SSL_REDIRECT`, HSTS 1yr, secure cookies — see `config/settings/prod.py`)
- SMTP email backend (dev uses console backend)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Layered Architecture Convention (most important)
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
- `BaseMapper[M]` — provides `to_list()`, requires `to_dict()`.
- `BaseService` / `BaseQuery` — intent markers (empty base classes).
## Portuguese (pt-br) Language Convention
## Naming Patterns
- Services: `<Domain>Service` (`CatalogService`, `OrderService`, `PaymentService`).
- Queries: `<Model>Query` (`ProductQuery`, `CategoryQuery`, `OrderQuery`, `AddressQuery`).
- Mappers: `<Model>Mapper` (`ProductMapper`, `CategoryMapper`, `OrderMapper`).
- Custom QuerySets: `<Model>QuerySet` (`ProductQuerySet` in `apps/catalog/models.py:43`).
- Nested enums: `class Status(models.TextChoices)`, `class Payment(...)` inside the Model.
## Code Style
## Import Organization
- Cross-app imports use **absolute** paths (`from apps.core.cache import ...`).
- Intra-app imports use **relative** paths (`from .models import ...`, `from .queries import ProductQuery`).
- **Deferred imports** to break circular dependencies are placed inside functions (e.g. `from apps.promotions.services import PromotionService` inside `CatalogService.browse`, `apps/catalog/services.py:58`).
## Error Handling
## Caching Convention
- `cache_utils.get_or_set(key, producer, bucket=...)` with a closure `producer()` that returns the materialized list.
- Keys built with `cache_utils.build_key(NS_*, *parts)`; namespaces are module-level `NS_*` constants.
- TTL buckets: `"short"` / `"medium"` / `"long"`, resolved from `settings.CACHE_TTL` (`config/settings/base.py:154-158`).
- Invalidation lives in `queries.py` (`invalidate_catalog_cache`) and is triggered by `post_save`/`post_delete` signals (`apps/catalog/signals.py`). Signals are wired in `AppConfig.ready()` (`apps/catalog/apps.py:9-10`).
## Logging
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
- `apps/core/templates/core/partials/` — `navbar.html`, `footer.html`, `icons.html` (SVG sprite), `field.html`.
- `apps/catalog/templates/catalog/partials/product_card.html`.
## CSS Design-Token Convention
- **Surfaces:** `--bg`, `--bg-soft`, `--bg-card`, `--bg-elevated`, `--border`, `--border-soft`.
- **Text:** `--text`, `--text-muted`, `--text-dim`.
- **Accent (blue):** `--accent`, `--accent-2`, `--accent-strong`, `--accent-soft`, `--accent-glow`.
- **Status:** `--success`, `--danger`, `--warning`.
- **Geometry/motion:** `--radius`, `--radius-sm`, `--radius-lg`, `--shadow`, `--shadow-glow`, `--container`, `--header-h`, `--ease`.
- **Fonts:** `--font`, `--font-display`.
## Front-end JS Convention
## Settings Convention
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- **Thin views, fat services.** Views only parse the request, call a service, and render. All business logic lives in `services.py`.
- **Single write boundary.** Services are the only place that writes to the database; queries are read-only.
- **Read/write separation.** `queries.py` builds optimized, cached ORM querysets (read). `services.py` orchestrates and mutates (write).
- **Model → dict boundary at mappers.** Templates and serializers never receive raw model instances directly from services in most flows; `mappers.py` converts `Model -> dict`/DTO.
- **Cache-first reads.** Stable listings (featured, categories, new arrivals) are cached via `apps/core/cache.py` and invalidated by signals.
- **Shared base layer.** `apps/core` provides reusable abstractions (`TimeStampedModel`, `BaseMapper`, `BaseService`, `BaseQuery`, cache helpers, formatting, global context processors).
## Layers
- Purpose: ORM-only. Builds optimized querysets (`select_related`/`prefetch_related`) and caches stable reads. Knows nothing about HTTP or business rules.
- Location: `apps/*/queries.py`
- Contains: `*Query` classes with `@staticmethod` read methods; cache namespaces (e.g. `NS_FEATURED`); a module-level `invalidate_*_cache()` for signals.
- Depends on: `models.py`, `apps/core/cache.py`
- Used by: `services.py`
- Example: `apps/catalog/queries.py` (`ProductQuery.featured`, `ProductQuery.search`), `apps/orders/queries.py` (`OrderQuery.for_user`).
- Purpose: Orchestrate business rules. Combine queries + mappers. Only place that writes to the DB (wrapped in `@transaction.atomic` where multi-step).
- Location: `apps/*/services.py`
- Contains: `*Service(BaseService)` classes with `@staticmethod` methods returning template-ready dicts.
- Depends on: `queries.py`, `mappers.py`, and other apps' services (cross-app calls, often via local import to avoid cycles — see `apps/catalog/services.py` importing `PromotionService`).
- Used by: `views.py`, other services.
- Example: `apps/orders/services.py` `OrderService.create_from_cart` (transactional: creates order + items, decrements stock via `F()`, consumes coupon, calls `PaymentService`, clears cart).
- Purpose: Convert `Model <-> dict/DTO` for templates and serializers. Apply display formatting (e.g. `format_brl`).
- Location: `apps/*/mappers.py`
- Contains: `*Mapper(BaseMapper[Model])` with `to_dict`, optional `to_detail`/`to_line`/`to_summary`; inherited `to_list`.
- Depends on: `models.py`, `apps/core/formatting.py`, `apps/core/layers.BaseMapper`
- Used by: `services.py`
- Example: `apps/catalog/mappers.py` (`ProductMapper.to_dict`, `to_detail`).
- Purpose: DRF input/output for the API surface (camelCase render/parse configured globally in `REST_FRAMEWORK`).
- Location: `apps/*/serializers.py` (present in accounts, cart, catalog, orders, promotions).
- Depends on: `rest_framework`, `models.py`.
- Purpose: Thin HTTP layer. Parse request → call service → render template (or raise `Http404`).
- Location: `apps/*/views.py`
- Pattern: Function-based views for catalog/cart/orders; class-based views in `apps/accounts` (`NexoraLoginView`) and `apps/core` (`HomeView`, `AboutView`).
- Example: `apps/catalog/views.py` `product_list` is 3 lines: read page, call `CatalogService.browse`, render.
- Purpose: Schema + side-effect-free business properties (`Product.has_discount`, `discount_pct`, `in_stock`, `is_new`). Custom querysets/managers live here (`ProductQuerySet.active().with_relations()`).
- Base: `apps/core/models.TimeStampedModel` (abstract `created_at`/`updated_at`).
- `signals.py` — cache invalidation on save/delete (`apps/catalog/signals.py`, `apps/promotions/signals.py`), wired in `AppConfig.ready()`.
- `managers.py` — custom managers (`apps/accounts/managers.py`).
- `forms.py` — Django forms (`apps/accounts/forms.py`, `apps/orders/forms.py`).
- `admin.py` — Django admin registration.
- `context_processors.py` — global template data (`apps/core`, `apps/cart`).
- `middleware.py` — request augmentation (`apps/cart/middleware.py`).
- `payments.py` — isolated, swappable payment gateway (`apps/orders/payments.py`).
- `cart.py` — session-backed cart state (`apps/cart/cart.py`).
## Apps
## Data Flow
- **Cart state:** Server-side session (`request.session["cart"]` + `cart_coupon`), wrapped by `SessionCart`. No DB persistence for the in-progress cart.
- **Read cache:** Per-namespace cache entries via `apps/core/cache.py` with TTL buckets (`short`/`medium`/`long` from `settings.CACHE_TTL`). LocMem by default; Redis when `REDIS_URL` is set.
- **Order state:** Persisted with snapshots (product name, price, address, totals) so orders are immune to later catalog/price changes.
## Key Abstractions
- Purpose: Enforce and document the layer convention; standardize imports.
- Location: `apps/core/layers.py`
- Pattern: `BaseMapper` provides `to_list` over a subclass `to_dict`; `BaseService`/`BaseQuery` are intent markers.
- Purpose: Shared `created_at`/`updated_at` + default ordering.
- Location: `apps/core/models.py`; subclassed by domain models (`Product`, `Category`, `Order`).
- Purpose: Consistent key building + get-or-set + invalidation.
- Location: `apps/core/cache.py` (`build_key`, `get_or_set`, `ttl`, `invalidate`).
- Pattern: `cache_utils.get_or_set(key, producer, bucket=...)`; signals call `invalidate(...)`.
- Purpose: Pure session state container for cart contents/coupon.
- Location: `apps/cart/cart.py`; hydrated by `CartService`.
- Purpose: Isolated, swappable payment boundary (simulated today; designed to drop in Mercado Pago/Stripe by changing `process()`).
- Location: `apps/orders/payments.py`.
## Entry Points
- Location: `config/wsgi.py`, `config/asgi.py` (default `DJANGO_SETTINGS_MODULE = config.settings.prod`).
- `manage.py` defaults to `config.settings.dev`.
- Location: `config/urls.py` — mounts admin plus each app: `core` at `/`, `accounts` at `conta/`, `catalog` at `catalogo/`, `promotions` at `promocoes/`, `cart` at `carrinho/`, `orders` at `pedidos/`. DEBUG adds media serving and optional debug toolbar.
- Location: `apps/*/urls.py`, each namespaced via `app_name` (e.g. `catalog:product_detail`, `accounts:login`).
- `apps/cart/middleware.py` `CartMiddleware` attaches `request.cart` for every request (registered last in `MIDDLEWARE`).
## Error Handling
- Missing resource: services return `None`, views raise `Http404` (e.g. `apps/catalog/views.py` `product_detail`).
- Domain errors: explicit exception classes, e.g. `EmptyCartError` in `apps/orders/services.py`, caught at the checkout view to message the user.
- Cache resilience: Redis configured with `IGNORE_EXCEPTIONS: True` so cache outages degrade gracefully.
- Coupon/stock validation returns structured dicts (`{"valid", "message", "discount", "code"}`) rather than exceptions for user-facing flows.
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
