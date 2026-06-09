# Testing Patterns

**Analysis Date:** 2026-06-05

## Honest Status: No Tests Exist

This project currently has **zero automated tests** and **no testing infrastructure**. This is confirmed by exploration and acknowledged in the project's own `README.md:96-99`, which lists "suíte de testes" (test suite) under *"Próximos passos (não incluídos)"* (next steps — not included).

What was searched for and **not found**:
- No `tests.py` in any app (the default Django stub was removed/never added — `apps/*/tests.py` does not exist).
- No `tests/` package in any app or at the repo root.
- No `test_*.py` or `*_test.py` files anywhere.
- No `conftest.py`.
- No test-runner config: no `pytest.ini`, `tox.ini`, `setup.cfg`, `pyproject.toml`, `[tool.pytest]`.
- No test/QA dependencies in `requirements.txt` (no `pytest`, `pytest-django`, `factory_boy`, `coverage`, `model_bakery`, `faker`, `responses`).
- No CI configuration (no `.github/workflows/`, no `.gitlab-ci.yml`).

The only quality-tooling dependency present is `django-debug-toolbar==6.3.0` (a dev debugging aid, installed in `config/settings/dev.py:7`), which is not a testing tool.

## Test Framework

**None configured.** The only test capability available is Django's built-in test runner (`unittest`-based) via `python manage.py test`, since `manage.py` exists and Django is installed (`Django==5.2.12`). No tests would be collected by it today.

If/when tests are added, no framework choice has been made yet. Given the stack, the natural options are:
- Django's built-in `unittest` runner (zero new dependencies), or
- `pytest` + `pytest-django` (would need to be added to `requirements.txt`).

## Run Commands

No working test command exists today. The runner that *would* be used:
```bash
python manage.py test          # Django's built-in runner (collects nothing currently)
```
There is no coverage, watch, or CI command configured.

## Test File Organization

**Not established.** No convention exists. If tests are introduced, they should mirror the project's strict layered architecture (see `CONVENTIONS.md`). Recommended structure aligned to that architecture:
```
apps/<app>/tests/
    __init__.py
    test_queries.py      # ORM + cache behavior (apps/<app>/queries.py)
    test_services.py     # business rules / writes (apps/<app>/services.py)
    test_mappers.py      # Model -> dict shape (apps/<app>/mappers.py)
    test_forms.py        # validation rules (apps/<app>/forms.py)
    test_views.py        # request -> service -> response (apps/<app>/views.py)
```

## What the Code Makes Easy to Test (high-value targets)

The layered design is highly testable. When tests are added, prioritize the pure/orchestration layers:

- **Model business properties (pure, no DB needed beyond instantiation):**
  - `apps/catalog/models.py:102-119` — `Product.has_discount`, `discount_pct`, `in_stock`, `is_new` (note `is_new` depends on `timezone.now()` — mock/freeze time).
- **Formatting helpers (pure functions):**
  - `apps/core/formatting.py:7` — `format_brl` (e.g. `1234.5 -> "R$ 1.234,50"`, `None -> "—"`, negatives, thousands grouping). Ideal first unit tests.
- **Mappers (Model -> dict, deterministic):**
  - `apps/catalog/mappers.py` — `ProductMapper.to_dict` / `to_detail`, `CategoryMapper.to_dict` (assert dict keys/values).
- **Forms (validation logic):**
  - `apps/orders/forms.py:36-64` — `CheckoutForm.clean()` credit-card branch, `clean_card_number` digit-stripping, `to_order_data()` card_last4 extraction.
  - `apps/accounts/forms.py:22-26` — `RegisterForm.clean_email` duplicate-email rule.
- **Services / transactional flows (highest business value):**
  - `apps/orders/services.py:24-82` — `OrderService.create_from_cart`: empty-cart raises `EmptyCartError`, snapshots created, stock decremented (`F` expression), `sales_count` incremented, coupon `used_count` consumed, cart cleared, all atomic.
- **Queries + cache:**
  - `apps/catalog/queries.py` — `ProductQuery.search` filter/sort combinations; cache hit/miss via `apps/core/cache.py` `get_or_set`; invalidation by signals (`apps/catalog/signals.py`).
- **Payment simulation:**
  - `apps/orders/payments.py:14-44` — `PaymentService.process` status transitions per method (PIX/card → APPROVED+PROCESSING; boleto → PENDING).

## Mocking

**No mocking framework or patterns in place.** When added, the standard library `unittest.mock` covers the needs. Things that would need isolation/control in tests:
- **Time:** `is_new` and `paid_at` use `django.utils.timezone.now()` (`apps/catalog/models.py:119`, `apps/orders/payments.py`). Mock/freeze time.
- **Cache:** queries cache via `apps/core/cache.py`. Use Django's `override_settings` with `LocMemCache` and `cache.clear()` between tests rather than mocking.
- **Payment:** `PaymentService.process` is already simulated (no external gateway), so it needs no mocking today — but its isolation point (`apps/orders/payments.py`) is exactly where a real gateway would be patched in future tests.
- No external HTTP/SDK calls exist yet, so no network mocking (`responses`/`httpx-mock`) is needed currently.

## Fixtures and Factories

**None.** No factories, no `fixtures/*.json`. The closest existing tool is a **seed management command**, `apps/catalog/management/commands/seed_demo.py`, which populates demo categories, products, promotions, and coupons (run via `python manage.py seed_demo`). This is for local/demo data, not for tests, but it documents realistic object shapes that test factories could mirror.

## Coverage

**Not measured.** `coverage` is not installed and no coverage target is enforced. Effective automated coverage is **0%**.

## Test Types

- **Unit tests:** None.
- **Integration tests:** None.
- **E2E tests:** None. No Selenium/Playwright/Cypress.

## Recommended First Steps (for a future testing phase)

1. Add `pytest`, `pytest-django` (and optionally `coverage`/`pytest-cov`) to `requirements.txt`; add a `pytest.ini` pointing `DJANGO_SETTINGS_MODULE` at `config.settings.dev`.
2. Start with pure-function units: `apps/core/formatting.py` and Model properties in `apps/catalog/models.py` (fast, no DB).
3. Add service tests for `OrderService.create_from_cart` — the most business-critical, side-effect-heavy path (stock, sales, coupon, atomicity).
4. Use `override_settings(CACHES=...LocMemCache...)` and clear cache between tests for `queries.py` coverage.
5. Wire a CI workflow to run the suite on push.

---

*Testing analysis: 2026-06-05*
