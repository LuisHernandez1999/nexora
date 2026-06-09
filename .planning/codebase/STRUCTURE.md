# Codebase Structure

**Analysis Date:** 2026-06-05

## Directory Layout

```
l3d-labz-site/
├── manage.py                       # Dev entry (defaults to config.settings.dev)
├── requirements.txt                # Python dependencies
├── README.md
├── config/                         # Project config (settings, urls, wsgi/asgi, env)
│   ├── env.py                      # Env var helpers (env, env_bool, env_int, env_list, load_dotenv)
│   ├── urls.py                     # Root URLconf — mounts all apps
│   ├── wsgi.py / asgi.py           # Servers (default config.settings.prod)
│   └── settings/
│       ├── base.py                 # Shared settings + SITE brand dict + CACHE_TTL
│       ├── dev.py                  # DEBUG, debug toolbar, console email, plain static
│       └── prod.py                 # SSL/HSTS/secure cookies, SMTP email
├── apps/                           # All feature apps (layered)
│   ├── core/                       # Shared base: layers, cache, formatting, base templates
│   ├── accounts/                   # Custom user, auth, profile  (conta/)
│   ├── catalog/                    # Products & categories       (catalogo/)
│   ├── promotions/                 # Promotions & coupons        (promocoes/)
│   ├── cart/                       # Session cart                (carrinho/)
│   └── orders/                     # Checkout & order history    (pedidos/)
├── static/                         # Source static assets (STATICFILES_DIRS)
│   ├── css/theme.css               # Single global stylesheet (dark theme + tokens)
│   └── js/app.js                   # Single global script (defer-loaded)
├── media/                          # Uploaded files (MEDIA_ROOT, e.g. products/)
├── staticfiles/                    # collectstatic output (STATIC_ROOT, prod)
└── db.sqlite3                      # Default dev database
```

## Directory Purposes

**`config/`:**
- Purpose: Project-wide wiring, not feature code.
- Contains: split settings, root URL config, WSGI/ASGI, env helpers.
- Key files: `config/settings/base.py` (brand `SITE` dict, `CACHE_TTL`, INSTALLED_APPS, DRF config), `config/urls.py`, `config/env.py`.

**`apps/`:**
- Purpose: One Django app per business domain. Every app follows the same layered module convention.
- Contains: `models.py`, `queries.py`, `services.py`, `mappers.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `apps.py`, `migrations/`, `templates/`, plus optional `signals.py`, `forms.py`, `managers.py`, `context_processors.py`, `middleware.py`, `payments.py`, `cart.py`.

**`apps/core/`:**
- Purpose: Shared foundation (no domain models).
- Key files: `apps/core/layers.py` (BaseMapper/BaseService/BaseQuery), `apps/core/cache.py`, `apps/core/formatting.py`, `apps/core/models.py` (TimeStampedModel), `apps/core/context_processors.py`.

**`apps/<app>/templates/`:**
- Purpose: App-local templates, resolved via `APP_DIRS = True` (no global `templates/` dir is used — `BASE_DIR / "templates"` is configured but empty).
- Convention: namespaced subfolder matching the app (`templates/<app>/...`), except the global shell.

**`apps/core/templates/`:**
- Purpose: Global page shell + shared partials.
- Key files: `apps/core/templates/base.html` (the root layout every page extends), `apps/core/templates/core/partials/` (`navbar.html`, `footer.html`, `icons.html` SVG sprite, `field.html` form-field macro).

**`apps/catalog/management/commands/`:**
- Purpose: Custom management commands.
- Key file: `apps/catalog/management/commands/seed_demo.py` (demo data seeding).

**`static/`:**
- Purpose: Source CSS/JS, registered via `STATICFILES_DIRS = [BASE_DIR / "static"]`.
- Key files: `static/css/theme.css`, `static/js/app.js`.

**`media/`:**
- Purpose: User uploads (e.g. product images at `products/`). `MEDIA_ROOT`; served by Django only under DEBUG.

**`staticfiles/`:**
- Purpose: `collectstatic` target (`STATIC_ROOT`); WhiteNoise serves these in production.

## Key File Locations

**Entry Points:**
- `manage.py`: CLI entry, defaults to `config.settings.dev`.
- `config/wsgi.py` / `config/asgi.py`: server entry, default `config.settings.prod`.
- `config/urls.py`: root URL routing to all apps.

**Configuration:**
- `config/settings/base.py`: shared settings; the `SITE` brand dict (`name`, `tagline`, `accent`) lives here at the bottom; `CACHE_TTL` buckets; DRF camelCase config.
- `config/settings/dev.py` / `prod.py`: environment overrides.
- `config/env.py`: `.env` loading and typed env accessors.
- `.env`: present at project root — environment configuration (never read; contains secrets).

**Core Logic (per app):**
- Reads: `apps/<app>/queries.py`
- Business/writes: `apps/<app>/services.py`
- Model↔dict: `apps/<app>/mappers.py`
- HTTP: `apps/<app>/views.py` + `apps/<app>/urls.py`
- Schema: `apps/<app>/models.py`

**Templates:**
- Global shell: `apps/core/templates/base.html`
- Shared partials: `apps/core/templates/core/partials/`
- Catalog partials: `apps/catalog/templates/catalog/partials/product_card.html`

**Static:**
- `static/css/theme.css`, `static/js/app.js` (both referenced in `base.html` via `{% static %}`).

## Naming Conventions

**Files (layer modules):**
- Fixed, lowercase, singular role names: `queries.py`, `services.py`, `mappers.py`, `serializers.py`, `views.py`, `models.py`. Do not invent alternate names — the layer convention is enforced project-wide (`apps/core/layers.py`).

**Classes:**
- Query sets: `<Domain>Query` (e.g. `ProductQuery`, `OrderQuery`).
- Services: `<Domain>Service(BaseService)` (e.g. `CatalogService`, `OrderService`).
- Mappers: `<Domain>Mapper(BaseMapper[Model])` (e.g. `ProductMapper`).
- Models: singular PascalCase (`Product`, `Order`, `OrderItem`).

**URLs:**
- App namespaces via `app_name` (e.g. `catalog`, `accounts`).
- Route names are snake_case (`product_list`, `product_detail`).
- URL paths are Portuguese (`catalogo/`, `carrinho/`, `pedidos/`, `conta/`, `promocoes/`).

**Templates:**
- App-namespaced folder: `templates/<app>/<page>.html`.
- Partials under `partials/` subfolder.
- Verbose field names and comments are in Portuguese.

**Directories:**
- Apps live under `apps/` with the `apps.<name>` dotted path (configured in `INSTALLED_APPS` and each `AppConfig.name`).

## Where to Add New Code

**New feature in an existing app:**
- Read logic → add a method to `apps/<app>/queries.py` (`*Query` class).
- Business/write logic → add a method to `apps/<app>/services.py` (`*Service`).
- Output shaping → add/extend `apps/<app>/mappers.py`.
- HTTP → thin view in `apps/<app>/views.py` + route in `apps/<app>/urls.py`.
- Template → `apps/<app>/templates/<app>/<page>.html` extending `base.html`.

**New app:**
- Create `apps/<name>/` with the full layer module set, add `apps.<name>` to `LOCAL_APPS` in `config/settings/base.py`, and mount its `urls.py` in `config/urls.py`.

**New model:**
- Subclass `apps/core/models.TimeStampedModel`; put custom read methods in a `QuerySet`/manager and cached reads in `queries.py`; never write to the DB outside a service.

**New cached read:**
- Use `apps/core/cache.py` (`build_key` + `get_or_set` with a `bucket`); add invalidation in the app's `signals.py`.

**Shared utility:**
- Generic helpers → `apps/core/` (e.g. formatting in `apps/core/formatting.py`, base classes in `apps/core/layers.py`).

**Global template change / brand tweak:**
- Layout/partials → `apps/core/templates/base.html` and `apps/core/templates/core/partials/`.
- Brand text/accent → `SITE` dict in `config/settings/base.py`.
- Styles → `static/css/theme.css`; behavior → `static/js/app.js`.

## Special Directories

**`media/`:**
- Purpose: uploaded product images. Generated at runtime. Not committed.

**`staticfiles/`:**
- Purpose: `collectstatic` build output. Generated. Not committed.

**`apps/*/migrations/`:**
- Purpose: Django schema migrations. Generated by `makemigrations`. Committed.

**`db.sqlite3`:**
- Purpose: default dev database. Generated. Typically not committed.

**`.planning/`:**
- Purpose: GSD planning + this codebase map. Committed.

---

*Structure analysis: 2026-06-05*
