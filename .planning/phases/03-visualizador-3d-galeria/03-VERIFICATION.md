---
phase: 03-visualizador-3d-galeria
verified: 2026-06-06T00:00:00Z
status: human_needed
score: 9/9 must-haves verified
human_verification:
  - test: "Abrir um produto com GLB e interagir com o viewer."
    expected: "Dá pra rotacionar (arrastar), dar zoom (scroll/pinça) e mover (pan: botão direito / Ctrl+arrastar / dois dedos). O poster aparece enquanto carrega; sem layout shift; fundo acompanha o tema claro/escuro."
    why_human: "Comportamento interativo/visual do <model-viewer> em navegador — não automatizável via grep."
  - test: "Clicar 'Baixar STL' num produto com STL."
    expected: "O navegador baixa o arquivo .stl em vez de navegar até ele."
    why_human: "Comportamento de download depende do navegador/headers — visual."
  - test: "Abrir /catalogo/modelos-3d/ pela navbar."
    expected: "Aparecem só produtos com GLB; clicar num card abre o detalhe com o viewer."
    why_human: "Resultado depende de dados reais (produtos com GLB) e renderização em browser."
  - test: "Tema claro/escuro no viewer e AR no celular."
    expected: "Fundo do viewer acompanha o tema; AR abre no celular (VIEW-A1 é v2, mas atributos ar já presentes)."
    why_human: "AR exige dispositivo físico; aparência exige inspeção visual."
---

# Phase 03: Visualizador 3D & Galeria — Verification Report

**Phase Goal:** Visualizador 3D interativo no detalhe (rotate/zoom/pan), fallback gracioso, download do STL, e galeria "Modelos 3D" na navegação.
**Verified:** 2026-06-06
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Produto com GLB renderiza `<model-viewer>` interativo (camera-controls) | ✓ VERIFIED | product_detail.html:14-19 — `<model-viewer src="{{ product.model_3d_url }}" ... camera-controls auto-rotate touch-action="pan-y">` gated por `{% if product.has_3d_model %}` |
| 2 | Produto sem GLB mantém monograma + `<img>` onerror (fallback) | ✓ VERIFIED | product_detail.html:20-26 — `{% else %}` com `thumb-mono` + `<img ... onerror=...>` intacto |
| 3 | Produto com STL exibe botão "Baixar STL" (download); sem STL, não exibe | ✓ VERIFIED | product_detail.html:68-72 — `{% if product.has_stl %}<a href="{{ product.stl_url }}" download ...>Baixar STL</a>` |
| 4 | Script CDN do model-viewer só carrega no detalhe quando há GLB | ✓ VERIFIED | product_detail.html:93-98 — `{% block extra_js %}` com `model-viewer@4.3.1` gated por `has_3d_model`; base.html intacto |
| 5 | Container do viewer tem aspect-ratio/radius/fundo por token | ✓ VERIFIED | theme.css:324-336 — `.detail-media model-viewer { aspect-ratio:1/1; border-radius:var(--radius-lg); background:var(--bg-soft); ... }` só tokens, sem hex literal |
| 6 | Rota /catalogo/modelos-3d/ (name catalog:models_3d) acessível pela navbar | ✓ VERIFIED | urls.py:9 `path("modelos-3d/", views.models_3d, name="models_3d")`; navbar.html:12 `{% url 'catalog:models_3d' %}` |
| 7 | Galeria lista APENAS produtos com GLB, ordenados por -sales_count | ✓ VERIFIED | queries.py:84-90 `with_3d` faz `.exclude(model_3d="").order_by("-sales_count")` |
| 8 | Cards da galeria levam ao detalhe — sem viewer embutido por card | ✓ VERIFIED | models_3d.html:15 reusa `product_card.html`; nenhum `<model-viewer>` na galeria |
| 9 | Sem produtos com modelo, galeria mostra empty state pt-br | ✓ VERIFIED | models_3d.html:18-25 — `{% else %}` com `.empty-state` "Nenhum modelo 3D ainda" |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `apps/catalog/templates/catalog/product_detail.html` | Viewer + fallback + STL + script gated | ✓ VERIFIED | Contains `<model-viewer`, `camera-controls`, `touch-action="pan-y"`, `model-viewer@4.3.1`, `{% block extra_js %}`; no `nomodule`/`enable-pan` |
| `static/css/theme.css` | `.detail-media model-viewer` por token | ✓ VERIFIED | theme.css:324-336; tokens only |
| `apps/catalog/queries.py` | `ProductQuery.with_3d` | ✓ VERIFIED | queries.py:84-90; `exclude(model_3d="")` |
| `apps/catalog/services.py` | `CatalogService.gallery` | ✓ VERIFIED | services.py:36-37; `ProductMapper.to_list(ProductQuery.with_3d())` |
| `apps/catalog/views.py` | `models_3d(request)` | ✓ VERIFIED | views.py:23-24; renders `CatalogService.gallery()` |
| `apps/catalog/urls.py` | rota modelos-3d/ name=models_3d | ✓ VERIFIED | urls.py:9 |
| `apps/catalog/templates/catalog/models_3d.html` | Galeria reusando product_card + empty state | ✓ VERIFIED | extends base; `product_card.html`; `empty-state`; no `<model-viewer>` |
| `apps/core/templates/core/partials/navbar.html` | Link 'Modelos 3D' | ✓ VERIFIED | navbar.html:12 |
| `apps/catalog/mappers.py` (supporting) | to_detail fornece campos 3D | ✓ VERIFIED | mappers.py:63-66 — `model_3d_url`, `stl_url`, `has_3d_model`, `has_stl` em `to_detail` |
| `apps/catalog/models.py` (supporting) | campos/props model_3d, model_stl, has_3d_model, has_stl | ✓ VERIFIED | models.py:72,77,134-139 |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| product_detail.html (.detail-media) | product.model_3d_url / image_url | `<model-viewer src=... poster=...>` gated | ✓ WIRED | model-viewer src bound to model_3d_url, poster to image_url |
| product_detail.html (extra_js) | model-viewer@4.3.1 CDN | `<script type=module>` gated | ✓ WIRED | Version pinned @4.3.1, gated por has_3d_model |
| product_detail.html (compra) | product.stl_url | `<a href download>` gated | ✓ WIRED | Gated por has_stl |
| navbar.html (.main-nav) | catalog:models_3d | `{% url %}` | ✓ WIRED | Resolves (check passed) |
| views.models_3d | CatalogService.gallery | render(...) | ✓ WIRED | views.py:24 |
| CatalogService.gallery | ProductQuery.with_3d | ProductMapper.to_list(...) | ✓ WIRED | services.py:37 |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| VIEW-01 | 03-01 | Viewer 3D interativo no detalhe quando há GLB | ✓ SATISFIED (markup); ? human for interaction | model-viewer com camera-controls; rotate/zoom/pan needs browser |
| VIEW-02 | 03-01 | Fallback gracioso para imagem sem GLB | ✓ SATISFIED | `{% else %}` thumb-mono + img onerror |
| VIEW-03 | 03-01 | Download do STL a partir da página | ✓ SATISFIED (markup); ? human for download behavior | `<a href download>` gated por has_stl |
| VIEW-04 | 03-02 | Galeria "Modelos 3D" na navegação | ✓ SATISFIED | Cadeia query→service→view→url→template + navbar link |

No orphaned requirements: REQUIREMENTS.md maps VIEW-01..04 to Phase 3, all claimed by plans 03-01/03-02.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| — | — | None | — | No TODO/FIXME/placeholder; no `nomodule`/`enable-pan`/`disable-pan`; no stub returns; no literal hex in viewer CSS block |

### Build / System Check

`python manage.py check --settings=config.settings.prod` → "System check identified no issues (0 silenced)." Exit 0.

### Human Verification Required

1. **Viewer interaction** — Open a product with GLB; confirm rotate (drag), zoom (scroll/pinch), pan (right-button / Ctrl-drag / two fingers); poster shows while loading; no layout shift; viewer background follows light/dark theme.
2. **STL download** — Click "Baixar STL"; the .stl file downloads rather than navigating.
3. **Gallery via navbar** — Open /catalogo/modelos-3d/; only GLB products appear; clicking a card opens detail with the viewer.
4. **Theme + AR** — Viewer background tracks theme; AR opens on a phone (AR is v2/VIEW-A1, but `ar` attributes are present).

### Gaps Summary

No gaps. All 9 must-have truths are verified against the codebase: the `<model-viewer>` is present, correctly gated, and wired to the mapped data (model_3d_url/image_url/stl_url); the image fallback is intact in the `{% else %}` branch; the STL download button is gated by has_stl; the CDN script is loaded per-page (version pinned @4.3.1) only when GLB exists, with base.html untouched; and the full layered chain for the gallery (with_3d → gallery → models_3d → urls → template + navbar link) is complete with an empty state and no per-card viewer. Django prod check passes (exit 0). Requirements VIEW-01..04 are all accounted for in REQUIREMENTS.md and claimed by the plans.

The remaining items are inherently visual/interactive (in-browser rotate/zoom/pan, STL download behavior, AR on device, theme-aware viewer background) and are listed under human_verification per the phase instructions — they do not constitute gaps and do not fail the phase.

---

_Verified: 2026-06-06_
_Verifier: Claude (gsd-verifier)_
