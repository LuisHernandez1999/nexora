# Codebase Concerns

**Analysis Date:** 2026-06-05

> Context: A rebrand (Nexora -> L3D Labz) and a new 3D-model-viewer feature are upcoming. Concerns most relevant to those efforts are flagged inline.

## Tech Debt

**Hardcoded "Nexora" brand strings scattered across the codebase (REBRAND BLOCKER):**
- Issue: The brand name is not fully centralized. While `SITE = {"name": "Nexora", ...}` exists in `config/settings/base.py` (line 218-222) and is exposed via `apps/core/context_processors.py`, many templates and code paths bypass it with literal "Nexora"/"nexora" strings. A rebrand requires touching every one of these by hand.
- Files:
  - `config/settings/base.py` — `SITE["name"]` (line 219), `SITE["tagline"]` (line 220, "Impressão 3D para quem é nerd ao cubo"), `SITE["accent"]` (line 221), cache `KEY_PREFIX="nexora"` (line 139), LocMem `LOCATION="nexora-locmem"` (line 148), Postgres default DB/user/password `"nexora"` (lines 106-108)
  - `apps/core/templates/core/partials/navbar.html` — hardcoded wordmark `<span class="brand-word">nex<b>ora</b></span>` (line 6) and `aria-label="Nexora — início"` (line 4). The wordmark splits the word ("nex" + "ora") so it cannot be driven by `{{ SITE.name }}` without markup changes.
  - `apps/core/templates/core/partials/footer.html` — `© 2026 Nexora — Impressão 3D...` (line 34)
  - `apps/core/templates/core/home.html` — `Comunidade Nexora` (line 139)
  - `apps/promotions/templates/promotions/list.html` — `Ofertas Nexora` (line 34)
  - `apps/core/templates/core/partials/field.html` — comment "estilo Nexora" (line 1)
  - `apps/core/templates/base.html` — `localStorage.getItem('nexora-theme')` (line 5)
  - `static/js/app.js` — `localStorage.setItem("nexora-theme", next)` (line 26) and header comment (line 1)
  - `static/css/theme.css` — header comment (line 2)
  - `apps/accounts/views.py` — class names `NexoraLoginView` / `NexoraLogoutView` (lines 15, 21), referenced in `apps/accounts/urls.py` (lines 8-9)
  - `apps/orders/payments.py` — PIX payload embeds `nexora-{order.number}` and merchant name `NEXORA` (line 35-37)
  - `apps/catalog/management/commands/seed_demo.py` — help text "da Nexora." (line 94)
  - `apps/cart/models.py` — docstring "O carrinho da Nexora" (line 1)
  - `manage.py` (line 2), `config/urls.py` (line 1), `config/settings/base.py` docstring (line 1) — docstrings/comments
  - `README.md` (lines 1, 57-59), `.env.example` (lines 10-12) — docs
- Impact: Incomplete rebrand leaves visible "Nexora" text in the navbar wordmark, footer, home community section, promotions page, and PIX checkout. The `localStorage` key mismatch (see below) is the highest-risk item.
- Fix approach: Drive all user-facing brand text from `SITE["name"]` in the context processor. Restructure the navbar wordmark markup so it renders `{{ SITE.name }}` (or accept a one-time literal change). Rename the `localStorage` theme key carefully (see Known Bugs). Class/cache-prefix/DB-default renames are internal and lower priority but should be aligned for consistency.

**`localStorage` theme key must change in TWO places atomically (REBRAND):**
- Issue: The theme preference is read in `apps/core/templates/core/base.html` (line 5, inline `<head>` script) and written in `static/js/app.js` (line 26), both using the literal key `'nexora-theme'`. If only one is changed during rebrand, the read and write keys diverge and theme persistence silently breaks.
- Files: `apps/core/templates/base.html:5`, `static/js/app.js:26`
- Impact: Users' chosen light/dark theme stops persisting across page loads; flash-of-wrong-theme on load.
- Fix approach: Change both occurrences in the same commit. Consider a one-time migration that reads the old `nexora-theme` value and copies it to the new key so existing visitors keep their preference.

**Reliance on external image hosts with `onerror` fallback chains (REBRAND + RELIABILITY):**
- Issue: Product, promotion, hero, and about imagery is sourced from `loremflickr.com` (seed/demo data) and falls back to `picsum.photos` via inline `onerror` handlers when the primary URL fails. There is no local/owned image asset pipeline for demo content.
- Files:
  - `apps/catalog/management/commands/seed_demo.py` — `product_image()` returns `loremflickr.com` URLs (line 44-46); promotion `image_url` use `loremflickr.com` (lines 75, 79, 83)
  - `apps/catalog/templates/catalog/partials/product_card.html:7`, `apps/catalog/templates/catalog/product_detail.html:17`, `apps/catalog/templates/catalog/product_list.html:14` — `picsum.photos` `onerror` fallbacks
  - `apps/promotions/templates/promotions/list.html:14,55`, `apps/cart/templates/cart/detail.html:20`, `apps/core/templates/core/home.html:11-12,75`, `apps/core/templates/core/about.html:9-10` — `loremflickr`/`picsum` usage and fallbacks
- Impact: Pages depend on third-party uptime, render slowly or with broken images if those hosts are down/rate-limited, and the seed bakes branded-looking demo URLs (e.g. `picsum.photos/seed/nexorahero/...`) that reference the old brand. Also a privacy/CSP concern (external requests on every page).
- Fix approach: Ship a small set of owned placeholder images under `static/` and reference them via `{% static %}` for the `onerror` fallback. For demo content, the seed should download/store images into `MEDIA_ROOT` or ship bundled fixtures. Rename any seed strings containing `nexora`.

**Product model has no field for a 3D model file (NEW FEATURE BLOCKER):**
- Issue: The `Product` model (`apps/catalog/models.py:51-119`) has only `image` (ImageField, `upload_to="products/"`) and `image_url` (external URL). There is no `FileField` for `.stl`/`.glb`/`.obj`/`.3mf` assets and no field to drive a web 3D viewer.
- Files: `apps/catalog/models.py:65-69`
- Impact: The planned 3D-model-viewer feature cannot store or reference model files. `ProductMapper` (`apps/catalog/mappers.py:28-65`) also exposes no such field to templates/serializers.
- Fix approach: Add a `model_file = models.FileField(upload_to="models/", blank=True)` (or a URL field for externally hosted GLB) plus an optional `model_format` / poster-image field. Create a migration. Surface the field in `ProductMapper.to_detail()`. Validate uploaded extensions/size (see Security). The product detail template (`apps/catalog/templates/catalog/product_detail.html`, `.detail-media` block, lines 13-19) is where the viewer would mount.

**Cache invalidation is incomplete — stale catalog data after edits:**
- Issue: `invalidate_catalog_cache()` in `apps/catalog/queries.py:131-138` only busts `NS_CATEGORIES`, `NS_FEATURED(8)`, and `NS_NEW(4)`/`NS_NEW(8)`. It does NOT invalidate `on_sale` (`catalog:onsale:*`), individual product detail (`NS_PRODUCT:slug`), or related-product caches (`NS_RELATED:*`), all written with `bucket="medium"` (300s TTL).
- Files: `apps/catalog/queries.py:69-106` (cached but not invalidated), `apps/catalog/queries.py:131-138` (invalidation), `apps/catalog/signals.py` (trigger)
- Impact: After an admin edits a product (price, stock, description, or a new 3D model field), the product detail page and on-sale/related lists can serve stale data for up to 5 minutes.
- Fix approach: Extend `invalidate_catalog_cache()` to clear the on-sale keys and the affected product/related keys (pass the saved instance from the signal, or flush a versioned namespace).

## Known Bugs

**Cart quantity can be silently capped below user intent:**
- Symptoms: In `CartService.build()` (`apps/cart/services.py:55`), `qty = min(qty, product.stock) if product.stock else qty`. When `product.stock` is 0 (falsy), the `else` branch keeps the full requested quantity instead of capping to 0 — an out-of-stock product can remain in the cart with a positive quantity and contribute to subtotal.
- Files: `apps/cart/services.py:55`
- Trigger: Add a product to cart, then have its stock drop to 0; revisit cart.
- Workaround: None in code. `OrderService.create_from_cart` does not re-validate stock either (see below).

**No stock re-validation at checkout — possible oversell / negative stock:**
- Symptoms: `OrderService.create_from_cart` (`apps/orders/services.py:24-82`) decrements stock with `F("stock") - quantity` (line 68-71) but never checks that `stock >= quantity` first. `PositiveIntegerField` can raise/underflow, or with the cart-cap bug above an out-of-stock item passes through.
- Files: `apps/orders/services.py:54-71`
- Trigger: Two concurrent checkouts of the last unit, or checkout of an item that sold out after being added to cart.
- Workaround: None. The whole operation is `@transaction.atomic`, but without a `select_for_update`/conditional update the race is unguarded.

## Security Considerations

**SECRET_KEY has an insecure default and is not enforced in production:**
- Risk: `config/settings/base.py:24` defaults `SECRET_KEY` to `"dev-insecure-change-me-in-prod"`. `config/settings/prod.py` does not assert that a real key is set, so a misconfigured prod deploy can silently run with the public default key.
- Files: `config/settings/base.py:24`, `config/settings/prod.py`
- Current mitigation: `.env.example` documents the variable; `.gitignore` excludes `.env`.
- Recommendations: In `prod.py`, raise `ImproperlyConfigured` if `SECRET_KEY` equals the default. Same for `ALLOWED_HOSTS` (defaults to localhost only — would 400 in prod, which is fail-safe but easy to miss).

**No upload validation on ImageField / future model FileField:**
- Risk: `Product.image` (`apps/catalog/models.py:65`) accepts any uploaded image with no size or content validation. The planned 3D model `FileField` would inherit the same gap, allowing large/arbitrary file uploads to `MEDIA_ROOT`.
- Files: `apps/catalog/models.py:65-69`, admin upload path `apps/catalog/admin.py`
- Current mitigation: Pillow validates that images are decodable; uploads are admin-only (`PROTECT`/staff access).
- Recommendations: Add file-size limits and extension allow-lists (validators) on image and (new) model fields. Ensure `MEDIA_ROOT` files are served read-only and never executed.

**Media files served by application server, not hardened:**
- Risk: `MEDIA_ROOT`/`MEDIA_URL` are configured (`config/settings/base.py:190-191`) with `FileSystemStorage`. WhiteNoise (`whitenoise.middleware.WhiteNoiseMiddleware`, `config/settings/base.py:62`) serves STATIC files only — it does not serve MEDIA. There is no documented production media-serving strategy (nginx/object storage), so user-uploaded media (and future large 3D models) may be unserved or served inefficiently in prod.
- Files: `config/settings/base.py:62, 184-198`, `config/settings/prod.py`
- Current mitigation: Static files use `CompressedManifestStaticFilesStorage` via WhiteNoise; dev serves static directly.
- Recommendations: Document/configure media serving for prod (nginx `location /media/`, or S3-compatible storage via a `STORAGES["default"]` backend). This is important before adding large `.glb`/`.stl` uploads.

**Custom `.env` parser is naive:**
- Risk: `config/env.py:load_dotenv` (lines 13-23) splits on the first `=` and strips one layer of surrounding quotes; it does not handle multiline values, escapes, or `export` prefixes. Misformatted secrets (e.g. values containing `#`) can be truncated or mis-parsed.
- Files: `config/env.py:13-23`
- Current mitigation: Documented as intentionally minimal; only used for a handful of vars.
- Recommendations: Acceptable for current scope; revisit if secrets grow complex. Note it uses `setdefault` so real environment variables correctly win over `.env`.

## Performance Bottlenecks

**External image requests block perceived page load:**
- Problem: Every catalog/home/promotions page issues requests to `loremflickr.com`/`picsum.photos` (see Tech Debt). These are slow third-party hops outside CDN control.
- Files: templates listed under "Reliance on external image hosts" above.
- Cause: Demo imagery sourced remotely instead of from owned static/media.
- Improvement path: Self-host placeholder and demo images; add `loading="lazy"` consistently (already present on product cards) and width/height to avoid layout shift.

**Future 3D model assets will be large and unoptimized:**
- Problem: `.glb`/`.stl` files are typically multi-MB. Without an asset pipeline, serving them from the app server (no CDN, no compression beyond WhiteNoise for static) will be slow.
- Files: N/A yet — design concern for the new feature touching `apps/catalog/models.py` and `apps/catalog/templates/catalog/product_detail.html`.
- Improvement path: Store models in object storage / behind a CDN; consider Draco-compressed GLB; lazy-load the viewer only on the detail page.

## Fragile Areas

**Navbar brand wordmark markup (REBRAND):**
- Files: `apps/core/templates/core/partials/navbar.html:4-7`
- Why fragile: The wordmark is hand-split into `nex<b>ora</b>` for styling, so it cannot be swapped to `{{ SITE.name }}` without rewriting the markup. Easy to miss during rebrand, leaving the old name in the most visible UI element.
- Safe modification: Replace with `{{ SITE.name }}` and move the two-tone styling to CSS (e.g. split on a known boundary or style via a span), then verify visual parity.
- Test coverage: None.

**PIX/boleto payment payload generation (faked):**
- Files: `apps/orders/payments.py:31-44`
- Why fragile: `pix_payload` and `boleto_line` build hand-constructed strings with hardcoded merchant data ("NEXORA", "SAO PAULO") and fragile slicing (`order.number[-3:]`). These are simulated and not valid for real payment rails.
- Safe modification: When integrating a real gateway, replace the whole `PaymentService` body (it is intentionally isolated). Until then, update the embedded brand strings during rebrand.
- Test coverage: None.

**Checkout orchestration:**
- Files: `apps/orders/services.py:24-82`
- Why fragile: Single atomic method couples cart building, order creation, stock decrement, coupon consumption, payment, and cart clearing. No stock re-check (see Known Bugs); a failure mid-way relies entirely on the transaction.
- Safe modification: Add explicit stock validation before the decrement loop; keep the operation atomic.
- Test coverage: None.

## Scaling Limits

**Session-backed cart with no persistence guarantees:**
- Current capacity: Cart lives entirely in the session (`apps/cart/cart.py`, `SESSION_KEY="cart"`), default DB-backed sessions (or `cached_db` when Redis is set, `config/settings/base.py:143`).
- Limit: Carts are lost on session expiry and not shareable across devices; no abandoned-cart analytics possible.
- Scaling path: Acceptable for current scope. If persistence is needed, introduce a DB cart model (the design already isolates session logic in `SessionCart`).

**LocMemCache default is per-process:**
- Current capacity: Without `REDIS_URL`, cache is `LocMemCache` (`config/settings/base.py:144-151`), per-process and not shared across Gunicorn workers.
- Limit: Under multiple workers, cache hit rates drop and invalidation in one worker doesn't reach others — compounding the incomplete-invalidation bug above.
- Scaling path: Set `REDIS_URL` in production (already supported, `config/settings/base.py:129-143`).

## Dependencies at Risk

**External image hosts (loremflickr.com, picsum.photos):**
- Risk: Third-party services with no SLA; rate limiting or shutdown breaks imagery site-wide.
- Impact: Broken/slow images across catalog, home, promotions, cart, about.
- Migration plan: Self-host placeholders and demo media (see Tech Debt). Highest-leverage reliability fix.

**Google Fonts (fonts.googleapis.com / fonts.gstatic.com):**
- Risk: External font dependency (`apps/core/templates/base.html:10-12`); privacy/GDPR and render-blocking concerns.
- Impact: FOUT/FOIT or font fallback if blocked.
- Migration plan: Self-host the Inter/Sora woff2 files under `static/` if needed.

## Missing Critical Features

**No 3D model storage or viewer (PLANNED):**
- Problem: No model file field, no viewer integration, no poster/thumbnail for 3D assets (see Tech Debt: Product model).
- Blocks: The entire upcoming 3D-model-viewer feature.

**No automated tests at all:**
- Problem: The repository contains zero test files (no `test_*.py`/`tests/` anywhere under `apps/`), no `pytest.ini`/`tox.ini`/`conftest.py`/`setup.cfg`, and no CI config.
- Blocks: Safe rebrand and feature work — there is no regression net for the cart/checkout/coupon logic, cache invalidation, or template rendering.

**No CI/linting/formatting enforcement:**
- Problem: No `.pre-commit-config.yaml`, no GitHub Actions/CI. `requirements.txt` includes `django-debug-toolbar` but no linter/formatter/test runner.
- Blocks: Consistent code quality during the rebrand churn.

## Test Coverage Gaps

**Everything — there is no test suite.** Highest-risk untested areas:

**Cart and pricing logic:**
- What's not tested: quantity capping, free-shipping threshold (`apps/cart/services.py:69`), coupon application/expiry (`apps/cart/services.py:60-67`), orphan-item discard (`apps/cart/services.py:51-53`).
- Files: `apps/cart/services.py`, `apps/cart/cart.py`, `apps/promotions/services.py`
- Risk: Incorrect totals/discounts charged to customers; the stock-cap bug (Known Bugs) would have been caught by a unit test.
- Priority: High

**Checkout / order creation:**
- What's not tested: stock decrement, coupon consumption, payment status transitions, empty-cart guard (`apps/orders/services.py`, `apps/orders/payments.py`).
- Files: `apps/orders/services.py`, `apps/orders/payments.py`
- Risk: Oversell/negative stock, wrong order totals.
- Priority: High

**Cache invalidation:**
- What's not tested: that editing a product busts the relevant caches.
- Files: `apps/catalog/queries.py`, `apps/catalog/signals.py`
- Risk: Stale catalog/detail pages (the incomplete-invalidation bug above is unguarded).
- Priority: Medium

**Template rendering / brand correctness (REBRAND):**
- What's not tested: that no literal "Nexora" leaks into rendered pages, that theme persistence works.
- Files: all templates under `apps/*/templates/`, `static/js/app.js`
- Risk: Visible old-brand text post-rebrand; broken theme toggle.
- Priority: High (for the rebrand) — add a smoke test asserting `SITE.name` appears and the old literal does not.

---

*Concerns audit: 2026-06-05*
