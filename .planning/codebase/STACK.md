# Technology Stack

**Analysis Date:** 2026-06-05

## Languages

**Primary:**
- Python 3.13 - All backend application code (`apps/`, `config/`). The local runtime is Python 3.13.5; no explicit `python_requires` floor is pinned. Django 5.2 supports Python 3.10+.

**Secondary:**
- HTML (Django Templates) - Server-rendered UI in `apps/*/templates/` and `apps/core/templates/base.html`
- CSS - Hand-written, framework-free theme in `static/css/theme.css` (684 lines)
- JavaScript (vanilla ES) - Progressive enhancement in `static/js/app.js` (153 lines, no framework, IIFE-wrapped)

## Runtime

**Environment:**
- CPython 3.13
- WSGI app: `config.wsgi.application`; ASGI app: `config.asgi.application` (declared in `config/settings/base.py`)

**Package Manager:**
- pip with `requirements.txt`
- Lockfile: missing (no `requirements.lock`, `poetry.lock`, or `Pipfile.lock`); versions are pinned directly in `requirements.txt` with `==`

## Frameworks

**Core:**
- Django 5.2.12 - Web framework (MVT, server-rendered). Settings split across `config/settings/base.py`, `dev.py`, `prod.py`
- Django REST Framework 3.16.1 - Serialization layer (configured in `base.py` `REST_FRAMEWORK`). Serializers exist per app (`apps/*/serializers.py`); no DRF ViewSets/routers wired into `config/urls.py` (views are classic Django views)
- djangorestframework-camel-case 1.4.2 - camelCase JSON render/parse for DRF output

**Testing:**
- Not detected - No test runner config (no `pytest.ini`, `tox.ini`), no `tests/` directories, and no test dependencies in `requirements.txt`. Only Django's built-in `manage.py test` is available.

**Build/Dev:**
- django-debug-toolbar 6.3.0 - Dev-only, injected in `config/settings/dev.py` (installed but hidden by default via `SHOW_TOOLBAR_CALLBACK: lambda request: False`)
- Custom management command(s) under `apps/catalog/management/commands/` (e.g. data seeding)

## Key Dependencies

**Critical:**
- Django 5.2.12 - Entire application framework
- djangorestframework 3.16.1 + djangorestframework-camel-case 1.4.2 - API serialization with camelCase contract
- django-filter 25.1 - Catalog filtering; registered as DRF default filter backend (`DjangoFilterBackend`) in `base.py`
- Pillow 11.2.1 - Image handling for `ImageField` (product images `products/`, promotion banners `promotions/`)

**Infrastructure:**
- psycopg[binary] 3.3.3 - PostgreSQL driver (production database)
- django-redis 6.0.0 + redis 6.4.0 - Redis cache backend (optional, enabled via `REDIS_URL`)
- gunicorn 23.0.0 - Production WSGI server
- whitenoise 6.9.0 - Static file serving in production (middleware + compressed manifest storage)

## Configuration

**Environment:**
- Custom minimal `.env` loader in `config/env.py` (no `python-dotenv` dependency). Provides typed helpers: `env`, `env_bool`, `env_int`, `env_list`, `load_dotenv`. Uses `os.environ.setdefault` (does not overwrite existing env vars).
- `.env.example` documents available variables; copy to `.env` for local overrides. Dev defaults work with no `.env` (SQLite + LocMem cache).
- `DJANGO_SETTINGS_MODULE` defaults to `config.settings.dev` (set in `manage.py`); production must set it to `config.settings.prod`.
- Key configs: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_ENGINE` / `POSTGRES_*`, `REDIS_URL`, `CACHE_TTL_SHORT/MEDIUM/LONG`, `CACHE_TIMEOUT`, `DB_CONN_MAX_AGE`.

**Build:**
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

**Development:**
- Python 3.13 + virtualenv, `pip install -r requirements.txt`
- No external services required (SQLite + LocMem defaults); run via `python manage.py runserver`

**Production:**
- gunicorn (WSGI) + WhiteNoise for statics
- PostgreSQL database, optional Redis
- HTTPS enforced (`SECURE_SSL_REDIRECT`, HSTS 1yr, secure cookies — see `config/settings/prod.py`)
- SMTP email backend (dev uses console backend)

---

*Stack analysis: 2026-06-05*
