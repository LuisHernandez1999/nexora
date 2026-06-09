# External Integrations

**Analysis Date:** 2026-06-05

## APIs & External Services

This project is largely self-contained. There are **no live third-party API integrations** (no Stripe/Mercado Pago/AWS/Supabase SDKs in `requirements.txt`). External dependencies are limited to fonts and optional infrastructure.

**Fonts (CDN):**
- Google Fonts - Inter + Sora typefaces
  - Loaded in `apps/core/templates/base.html` via `https://fonts.googleapis.com/css2?...` with `preconnect` to `fonts.googleapis.com` and `fonts.gstatic.com`
  - Auth: none (public CDN)

## Data Storage

**Databases:**
- SQLite (development default)
  - Location: `BASE_DIR/db.sqlite3`
  - Client: Django ORM (`django.db.backends.sqlite3`)
- PostgreSQL (production)
  - Connection: env vars `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`; activated by `DATABASE_ENGINE=postgres` or presence of `POSTGRES_DB`
  - Client: Django ORM via `psycopg[binary]` 3.3.3, with connection pooling (`OPTIONS: {"pool": True}`) and health checks
  - Config: `config/settings/base.py` (`DATABASES`)

**File Storage:**
- Local filesystem only - `django.core.files.storage.FileSystemStorage`
  - Media root: `BASE_DIR/media` (`MEDIA_URL = media/`)
  - Uploaded images: product images → `media/products/` (`apps/catalog/models.py:65`), promotion banners → `media/promotions/` (`apps/promotions/models.py:36`)
  - Images processed with Pillow; no external CDN or object storage (no S3/Cloudinary)
  - In production, static assets (not media) are served via WhiteNoise compressed manifest storage

**Caching:**
- LocMemCache (default) or Redis (optional)
  - Redis enabled when `REDIS_URL` is set (e.g. `redis://127.0.0.1:6379/1`)
  - Client: `django-redis` (`RedisCache`, `DefaultClient`), `IGNORE_EXCEPTIONS=True`, key prefix `nexora`
  - When Redis active, sessions switch to `cached_db` backend
  - Config: `config/settings/base.py` (`CACHES`)

## Authentication & Identity

**Auth Provider:**
- Custom (Django built-in auth) - no external identity provider
  - Custom user model `apps.accounts.User` (`apps/accounts/models.py`): email-based login (`USERNAME_FIELD = "email"`, no username), custom `UserManager`
  - `AUTH_USER_MODEL = "accounts.User"`, `LOGIN_URL = accounts:login`
  - Standard Django password validators (similarity, min length, common, numeric)
  - Routes under `conta/` (`apps/accounts/urls.py`)
  - No OAuth, no social login, no JWT/token packages installed

## Monitoring & Observability

**Error Tracking:**
- None - no Sentry or equivalent in `requirements.txt`

**Logs:**
- Default Django logging (no custom `LOGGING` config detected). django-debug-toolbar available in dev only (hidden by default).

## CI/CD & Deployment

**Hosting:**
- Not pinned in repo. Production stack implies a generic WSGI host: gunicorn 23.0.0 + WhiteNoise for static serving + PostgreSQL.

**CI Pipeline:**
- None detected - no `.github/workflows/`, `.gitlab-ci.yml`, or similar

## Environment Configuration

**Required env vars (production):**
- `SECRET_KEY` - Django secret (must override the insecure default)
- `DEBUG` - set to `False` in prod (`config/settings/prod.py` forces `False`)
- `ALLOWED_HOSTS` - comma-separated host list
- `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_HOST` / `POSTGRES_PORT` (or `DATABASE_ENGINE=postgres`)
- `REDIS_URL` - optional, enables Redis cache + cached sessions
- `CACHE_TTL_SHORT` / `CACHE_TTL_MEDIUM` / `CACHE_TTL_LONG`, `CACHE_TIMEOUT`, `DB_CONN_MAX_AGE` - optional tuning
- SMTP settings for email (prod uses `smtp.EmailBackend`; specific host/credentials vars not yet defined in code)

**Secrets location:**
- `.env` file at project root (git-ignored), loaded by `config/env.py`. Template in `.env.example` (contains only non-secret dev defaults). No secrets manager integration.

## Payments

**Payment processing is SIMULATED — no real gateway is integrated.**

- Implementation: `apps/orders/payments.py` → `PaymentService`
  - `PaymentService.process(order)` - fakes charge: PIX and credit card are auto-approved (`PaymentStatus.APPROVED`, status → `PROCESSING`, sets `paid_at`); boleto stays `PENDING`. No network call.
  - `PaymentService.pix_payload(order)` - generates a fake PIX BR Code / copia-e-cola string for the confirmation screen
  - `PaymentService.boleto_line(order)` - generates a fake boleto digitable line
- Supported methods (`apps/orders/models.py` `Order.Payment`): `pix`, `credit_card`, `boleto`. Order stores `card_last4`, `payment_status`, `paid_at` as snapshots.
- Designed as a swap point: the module docstring notes that replacing the body of `process()` with a real gateway call (Mercado Pago, Stripe, etc.) requires no changes elsewhere.
- No payment SDK, no API keys, no PCI handling present.

## Webhooks & Callbacks

**Incoming:**
- None - no webhook endpoints. Routes (`config/urls.py`): `admin/`, `/`, `conta/`, `catalogo/`, `promocoes/`, `carrinho/`, `pedidos/`. Since payments are simulated, there is no payment-confirmation callback.

**Outgoing:**
- None - no outbound HTTP calls to external services in application code

## Email

- Dev: `console.EmailBackend` (emails printed to console — `config/settings/dev.py`)
- Prod: `smtp.EmailBackend` (`config/settings/prod.py`); SMTP host/credentials must be supplied via environment/settings (not yet wired)

---

*Integration audit: 2026-06-05*
