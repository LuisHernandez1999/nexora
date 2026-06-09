# Architecture

**Analysis Date:** 2026-06-05

## Pattern Overview

**Overall:** Modular Django monolith with a strict **per-app layered architecture**. Each feature lives in its own app under `apps/` and internally splits responsibilities into discrete layer modules. The convention is documented in `apps/core/layers.py` ("cada macaco no seu galho" — each layer stays in its lane).

**Key Characteristics:**
- **Thin views, fat services.** Views only parse the request, call a service, and render. All business logic lives in `services.py`.
- **Single write boundary.** Services are the only place that writes to the database; queries are read-only.
- **Read/write separation.** `queries.py` builds optimized, cached ORM querysets (read). `services.py` orchestrates and mutates (write).
- **Model → dict boundary at mappers.** Templates and serializers never receive raw model instances directly from services in most flows; `mappers.py` converts `Model -> dict`/DTO.
- **Cache-first reads.** Stable listings (featured, categories, new arrivals) are cached via `apps/core/cache.py` and invalidated by signals.
- **Shared base layer.** `apps/core` provides reusable abstractions (`TimeStampedModel`, `BaseMapper`, `BaseService`, `BaseQuery`, cache helpers, formatting, global context processors).

## Layers

The same module set repeats in each app. Not every app has every layer; the canonical full set is visible in `apps/catalog`.

**Queries (`queries.py`):**
- Purpose: ORM-only. Builds optimized querysets (`select_related`/`prefetch_related`) and caches stable reads. Knows nothing about HTTP or business rules.
- Location: `apps/*/queries.py`
- Contains: `*Query` classes with `@staticmethod` read methods; cache namespaces (e.g. `NS_FEATURED`); a module-level `invalidate_*_cache()` for signals.
- Depends on: `models.py`, `apps/core/cache.py`
- Used by: `services.py`
- Example: `apps/catalog/queries.py` (`ProductQuery.featured`, `ProductQuery.search`), `apps/orders/queries.py` (`OrderQuery.for_user`).

**Services (`services.py`):**
- Purpose: Orchestrate business rules. Combine queries + mappers. Only place that writes to the DB (wrapped in `@transaction.atomic` where multi-step).
- Location: `apps/*/services.py`
- Contains: `*Service(BaseService)` classes with `@staticmethod` methods returning template-ready dicts.
- Depends on: `queries.py`, `mappers.py`, and other apps' services (cross-app calls, often via local import to avoid cycles — see `apps/catalog/services.py` importing `PromotionService`).
- Used by: `views.py`, other services.
- Example: `apps/orders/services.py` `OrderService.create_from_cart` (transactional: creates order + items, decrements stock via `F()`, consumes coupon, calls `PaymentService`, clears cart).

**Mappers (`mappers.py`):**
- Purpose: Convert `Model <-> dict/DTO` for templates and serializers. Apply display formatting (e.g. `format_brl`).
- Location: `apps/*/mappers.py`
- Contains: `*Mapper(BaseMapper[Model])` with `to_dict`, optional `to_detail`/`to_line`/`to_summary`; inherited `to_list`.
- Depends on: `models.py`, `apps/core/formatting.py`, `apps/core/layers.BaseMapper`
- Used by: `services.py`
- Example: `apps/catalog/mappers.py` (`ProductMapper.to_dict`, `to_detail`).

**Serializers (`serializers.py`):**
- Purpose: DRF input/output for the API surface (camelCase render/parse configured globally in `REST_FRAMEWORK`).
- Location: `apps/*/serializers.py` (present in accounts, cart, catalog, orders, promotions).
- Depends on: `rest_framework`, `models.py`.

**Views (`views.py`):**
- Purpose: Thin HTTP layer. Parse request → call service → render template (or raise `Http404`).
- Location: `apps/*/views.py`
- Pattern: Function-based views for catalog/cart/orders; class-based views in `apps/accounts` (`NexoraLoginView`) and `apps/core` (`HomeView`, `AboutView`).
- Example: `apps/catalog/views.py` `product_list` is 3 lines: read page, call `CatalogService.browse`, render.

**Models (`models.py`):**
- Purpose: Schema + side-effect-free business properties (`Product.has_discount`, `discount_pct`, `in_stock`, `is_new`). Custom querysets/managers live here (`ProductQuerySet.active().with_relations()`).
- Base: `apps/core/models.TimeStampedModel` (abstract `created_at`/`updated_at`).

**Supporting modules (per app, as needed):**
- `signals.py` — cache invalidation on save/delete (`apps/catalog/signals.py`, `apps/promotions/signals.py`), wired in `AppConfig.ready()`.
- `managers.py` — custom managers (`apps/accounts/managers.py`).
- `forms.py` — Django forms (`apps/accounts/forms.py`, `apps/orders/forms.py`).
- `admin.py` — Django admin registration.
- `context_processors.py` — global template data (`apps/core`, `apps/cart`).
- `middleware.py` — request augmentation (`apps/cart/middleware.py`).
- `payments.py` — isolated, swappable payment gateway (`apps/orders/payments.py`).
- `cart.py` — session-backed cart state (`apps/cart/cart.py`).

## Apps

**`apps.core`** — Shared foundation. Provides `layers.py` (base classes), `cache.py` (key builder + get-or-set + invalidate), `formatting.py` (`format_brl`), `models.py` (`TimeStampedModel`), global context processor (`site_settings`), home/about views, and the base templates (`base.html`, partials). Has no domain models of its own.

**`apps.accounts`** — Custom user (`AUTH_USER_MODEL = "accounts.User"`), registration/login/profile. Class-based auth views (`NexoraLoginView`/`NexoraLogoutView`), `AccountService` for register/profile, `managers.py` for the user manager, `forms.py` for register/profile forms. URL prefix `conta/`.

**`apps.catalog`** — Products and categories (the canonical full-layer app). `Product`/`Category` models, `ProductQuerySet`, cached `ProductQuery`/`CategoryQuery`, `CatalogService` (home blocks, filtered+paginated browse, detail), signal-based cache busting, `management/commands/seed_demo.py`. URL prefix `catalogo/`.

**`apps.promotions`** — Hero/active promotions and coupons. `PromotionService` (display) and `CouponService.validate(code, subtotal)` returning a view-ready dict. `Coupon` model owns validity rules (`is_valid`, `discount_for`). URL prefix `promocoes/`.

**`apps.cart`** — Session cart (no DB model for cart state). `SessionCart` (`cart.py`) holds raw `{product_id: qty}` + coupon in the session; `CartMiddleware` attaches it as `request.cart`; `CartService.build` hydrates products, computes subtotal/discount/shipping; `cart_summary` context processor exposes `cart_count`. URL prefix `carrinho/`.

**`apps.orders`** — Checkout and order history. `OrderService.create_from_cart` (atomic), snapshot-based `Order`/`OrderItem` models, `PaymentService` (simulated PIX/card/boleto), `forms.py` for checkout. URL prefix `pedidos/`.

## Data Flow

**Catalog browse (read path):**
1. `GET /catalogo/?...` → `apps/catalog/views.py` `product_list` reads `page`.
2. Calls `CatalogService.browse(request.GET, page)`.
3. Service calls `ProductQuery.search(...)` (returns queryset), paginates with Django `Paginator`, fetches categories + active promotions.
4. `ProductMapper.to_list` / `CategoryMapper.to_list` convert models → dicts.
5. View renders `catalog/product_list.html` with the dict context.

**Checkout (write path):**
1. `POST /pedidos/...` → orders view validates `CheckoutForm`.
2. `OrderService.create_from_cart(request, data)` runs inside `@transaction.atomic`:
   - `CartService.build(request)` → items + summary (subtotal/discount/shipping/total).
   - Creates `Order` + bulk-creates `OrderItem` snapshots.
   - Decrements `Product.stock` and increments `sales_count` atomically via `F()`.
   - Increments `Coupon.used_count` if a coupon applied.
   - `PaymentService.process(order)` sets payment/order status.
   - `request.cart.clear()` empties the session cart.

**State Management:**
- **Cart state:** Server-side session (`request.session["cart"]` + `cart_coupon`), wrapped by `SessionCart`. No DB persistence for the in-progress cart.
- **Read cache:** Per-namespace cache entries via `apps/core/cache.py` with TTL buckets (`short`/`medium`/`long` from `settings.CACHE_TTL`). LocMem by default; Redis when `REDIS_URL` is set.
- **Order state:** Persisted with snapshots (product name, price, address, totals) so orders are immune to later catalog/price changes.

## Key Abstractions

**`BaseMapper[M]` / `BaseService` / `BaseQuery`:**
- Purpose: Enforce and document the layer convention; standardize imports.
- Location: `apps/core/layers.py`
- Pattern: `BaseMapper` provides `to_list` over a subclass `to_dict`; `BaseService`/`BaseQuery` are intent markers.

**`TimeStampedModel`:**
- Purpose: Shared `created_at`/`updated_at` + default ordering.
- Location: `apps/core/models.py`; subclassed by domain models (`Product`, `Category`, `Order`).

**Cache helpers:**
- Purpose: Consistent key building + get-or-set + invalidation.
- Location: `apps/core/cache.py` (`build_key`, `get_or_set`, `ttl`, `invalidate`).
- Pattern: `cache_utils.get_or_set(key, producer, bucket=...)`; signals call `invalidate(...)`.

**`SessionCart`:**
- Purpose: Pure session state container for cart contents/coupon.
- Location: `apps/cart/cart.py`; hydrated by `CartService`.

**`PaymentService`:**
- Purpose: Isolated, swappable payment boundary (simulated today; designed to drop in Mercado Pago/Stripe by changing `process()`).
- Location: `apps/orders/payments.py`.

## Entry Points

**WSGI/ASGI:**
- Location: `config/wsgi.py`, `config/asgi.py` (default `DJANGO_SETTINGS_MODULE = config.settings.prod`).
- `manage.py` defaults to `config.settings.dev`.

**Root URL config:**
- Location: `config/urls.py` — mounts admin plus each app: `core` at `/`, `accounts` at `conta/`, `catalog` at `catalogo/`, `promotions` at `promocoes/`, `cart` at `carrinho/`, `orders` at `pedidos/`. DEBUG adds media serving and optional debug toolbar.

**Per-app URLs:**
- Location: `apps/*/urls.py`, each namespaced via `app_name` (e.g. `catalog:product_detail`, `accounts:login`).

**Middleware-injected request state:**
- `apps/cart/middleware.py` `CartMiddleware` attaches `request.cart` for every request (registered last in `MIDDLEWARE`).

## Error Handling

**Strategy:** Conventional Django — views raise `Http404` for missing resources; services raise domain exceptions caught by views.

**Patterns:**
- Missing resource: services return `None`, views raise `Http404` (e.g. `apps/catalog/views.py` `product_detail`).
- Domain errors: explicit exception classes, e.g. `EmptyCartError` in `apps/orders/services.py`, caught at the checkout view to message the user.
- Cache resilience: Redis configured with `IGNORE_EXCEPTIONS: True` so cache outages degrade gracefully.
- Coupon/stock validation returns structured dicts (`{"valid", "message", "discount", "code"}`) rather than exceptions for user-facing flows.

## Cross-Cutting Concerns

**Logging:** No custom logging configuration detected; relies on Django defaults.

**Validation:** Django forms (`apps/accounts/forms.py`, `apps/orders/forms.py`) for HTML flows; DRF serializers for API; business validity on models (`Coupon.is_valid`, `Product` properties).

**Authentication:** Custom user model `accounts.User`; `LOGIN_URL = accounts:login`; standard Django auth middleware. Order/profile views are user-scoped (queries filter by `user`).

**Caching:** Centralized via `apps/core/cache.py`; invalidated by `post_save`/`post_delete` signals (`apps/catalog/signals.py`, `apps/promotions/signals.py`) wired in `AppConfig.ready()`.

**Branding/config:** `settings.SITE` dict surfaced to all templates by `apps/core/context_processors.site_settings`.

**Cart summary:** `apps/cart/context_processors.cart_summary` exposes `cart_count` globally.

---

*Architecture analysis: 2026-06-05*
