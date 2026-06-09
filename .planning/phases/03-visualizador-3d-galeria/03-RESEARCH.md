# Phase 3: Visualizador 3D & Galeria - Research

**Researched:** 2026-06-06
**Domain:** Google `<model-viewer>` web component (GLB/glTF) in a build-free Django 5.2 template stack
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Viewer tech:** Google `<model-viewer>` web component (no build, vanilla stack).
- **Loading:** via CDN as ES module, ONLY on pages that need it (product detail + gallery), through `{% block extra_js %}`. NOT loaded globally in `base.html`. (Research confirms current major version + exact unpkg/jsdelivr URL + fallback — see below.)
- **Expected attributes:** `camera-controls`, `auto-rotate`, `touch-action="pan-y"`, `shadow-intensity`, `poster` (use product image), `loading="lazy"`, `reveal`. AR (`ar`/`ar-modes`) is nice-to-have (research decides — cheap if included).
- **VIEW-01:** In `.detail-media`, WHEN `product.has_3d_model`, render `<model-viewer src="{{ product.model_3d_url }}" poster="{{ product.image_url }}" ...>` filling the container (aspect-ratio in CSS, rounded corners, theme-coherent background). Must allow rotate, zoom, pan intuitively. Optional subtle hint ("arraste para girar").
- **VIEW-02:** WHEN no GLB (`not product.has_3d_model`): keep current `.detail-media` behavior (`thumb-mono` monogram + `<img>` with onerror). No layout break. Just an `{% if %}/{% else %}`.
- **VIEW-03:** WHEN `product.has_stl`: show "Baixar STL" button near the add-to-cart block, existing classes (`btn btn-ghost`), `href="{{ product.stl_url }}"`, `download` attribute, with icon. pt-br text. No button when no STL.
- **VIEW-04:** Layered architecture (query → service → view → template):
  - `queries.py` `ProductQuery.with_3d(limit)` — `.exclude(model_3d="")`, order by `-sales_count`.
  - `services.py` `CatalogService.gallery()` — returns context with mapped list (`ProductMapper.to_dict`), mirror `browse`.
  - `views.py` `models_3d(request)`.
  - `urls.py` `path("modelos-3d/", views.models_3d, name="models_3d")`.
  - `templates/catalog/models_3d.html` — extends base, short hero ("Modelos 3D"), grid reusing `product_card.html`. Cards link to detail — NO per-card viewer (perf). pt-br empty state.
  - `navbar.html` — add "Modelos 3D" link in `main-nav`.
  - (Optional) "3D" badge on gallery card only if trivial; prefer a gallery wrapper over editing the shared partial.
- **CSS** (`static/css/theme.css`): styles for the viewer container (height/aspect-ratio, radius, theme background, width 100%). Reuse tokens. No framework.
- **Media serving:** dev serves media via `static()` in `config/urls.py` (confirmed). Prod serving of large GLB/STL is OUT OF SCOPE — note only.

### Claude's Discretion
- Whether to include AR now (cheap if yes).
- Exact pan-enabling mechanism (research confirms).
- Optional short-bucket cache on the gallery query.
- Optional "3D" badge on gallery cards.

### Deferred Ideas (OUT OF SCOPE)
- AR on mobile (if research excludes it now) — v2.
- Mini-viewer embedded in each gallery card — perf, avoid.
- Production media serving / CDN for large files — infra.
- Automatic STL→GLB conversion — v2.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VIEW-01 | Interactive 3D viewer on product detail; rotate + zoom + pan intuitively | `<model-viewer>` 4.3.1 with `camera-controls` (pan is ON by default), `touch-action="pan-y"`, `auto-rotate`, `shadow-intensity`, `camera-orbit`/`field-of-view` defaults — Sections "Standard Stack", "Interaction Attributes", "Code Examples". |
| VIEW-02 | Graceful fallback to current image when no GLB | Pure `{% if product.has_3d_model %}` Django template branch — no viewer JS runs. Section "Architecture Patterns". |
| VIEW-03 | STL download from product detail | Plain `<a href download>` — model-viewer does NOT render STL (GLB/glTF only). Section "Don't Hand-Roll" + "Code Examples". |
| VIEW-04 | "Modelos 3D" gallery tab in navigation | Standard query→service→view→url→template→navbar; `ProductQuery.with_3d` via `.exclude(model_3d="")`. Section "Django Side". |
</phase_requirements>

## Summary

`<model-viewer>` is the correct, build-free choice. Current stable is **4.3.1** (published 2026-06-04, two days before this research — extremely fresh). It is a single ES-module script loaded from a CDN; no bundler, no npm install in this project. It is loaded per-page through `{% block extra_js %}`, exactly as the locked decision requires.

The most important interaction finding: **pan is enabled by default the moment you add `camera-controls`.** There is no `enable-pan` attribute — the opposite, `disable-pan`, exists to turn it off. With `camera-controls` you get: rotate (left-drag / one-finger), zoom (wheel / pinch), and pan (right-drag or modifier+drag on desktop, two-finger drag on touch). So `camera-controls` alone satisfies "rotate, zoom e pan" in VIEW-01. The `touch-action="pan-y"` attribute from the locked decision is still recommended — it lets the user scroll the page vertically through the viewer instead of getting trapped.

A key compatibility note: model-viewer fetches the GLB as an ArrayBuffer via `fetch()` and parses bytes directly — it does NOT depend on the server sending `model/gltf-binary`. Django's dev `static()` serves `.glb` as `application/octet-stream` (Python `mimetypes` returns `None` for `.glb`), and that is fine; the viewer still loads. STL is download-only (model-viewer renders GLB/glTF, never STL), so a plain `<a download>` is the right and only approach for VIEW-03.

**Primary recommendation:** Pin `<model-viewer>` to 4.3.1 via jsDelivr ES module in `{% block extra_js %}` on the detail page only; use `camera-controls auto-rotate touch-action="pan-y" shadow-intensity="1" poster reveal="auto" loading="lazy"` with an `alt`; size the container with CSS `aspect-ratio` + token background; gallery cards link to detail (no embedded viewers); ship AR as a cheap two-attribute add-on (graceful no-op on desktop).

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@google/model-viewer` | **4.3.1** | Web component that renders GLB/glTF in `<canvas>` (Three.js under the hood) + built-in AR | Google-maintained, zero-build, single `<script type="module">`, native custom element — the canonical drop-in for vanilla stacks |

**Version verification (done):**
```
npm view @google/model-viewer version   -> 4.3.1
npm view @google/model-viewer time.modified -> 2026-06-04T20:57:04Z
dist-tags -> { canary: '2.0.0-rc3', latest: '4.3.1' }   # 4.3.1 IS latest; canary tag is stale/legacy, ignore it
```
Both pinned CDN URLs verified live (HTTP 200, correct JS MIME, `Access-Control-Allow-Origin: *`) on 2026-06-06.

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none) | — | No supporting libs needed | model-viewer bundles Three.js + draco + AR. No npm, no build, no extra JS file. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `<model-viewer>` | raw Three.js | Needs a build/bundler and hand-written loaders/controls — violates the no-build constraint. Reject. |
| jsDelivr CDN | unpkg CDN | Both verified working. jsDelivr serves `application/javascript` with `immutable` cache and a dedicated `cdn.jsdelivr.net` host; unpkg also fine (`text/javascript`). Either is acceptable; prefer jsDelivr as primary, unpkg as documented fallback. |
| Pinned `@4.3.1` | floating `@google/model-viewer` (no version) | Floating gives auto-updates but risks a future major silently breaking the page. **Pin the version** for reproducibility (no lockfile in this project). |

**Installation:** None. CDN only. Exact tag (jsDelivr, primary):
```html
<script type="module"
        src="https://cdn.jsdelivr.net/npm/@google/model-viewer@4.3.1/dist/model-viewer.min.js"></script>
```
unpkg fallback (interchangeable):
```html
<script type="module"
        src="https://unpkg.com/@google/model-viewer@4.3.1/dist/model-viewer.min.js"></script>
```

**No `nomodule` legacy build needed.** model-viewer 4.x targets modern evergreen browsers (it requires WebGL2 + ES2020 + custom elements). Every browser that can render WebGL2 already supports `type="module"`. The old `<script nomodule>` + `dist/model-viewer-legacy.js` pattern from the IE11 era is obsolete in 2026 and would only add weight. Browsers that don't support modules also can't run model-viewer at all — the graceful path there is the `poster` (it shows the product image and simply never reveals a canvas).

## Architecture Patterns

### Where it mounts (current `.detail-media`)
`apps/catalog/templates/catalog/product_detail.html` lines 13-19 currently render a `thumb-mono` span + `<img>` with onerror fallback inside `.detail-media`. The pattern is a single `{% if %}/{% else %}`:

```django
<div class="detail-media reveal">
  {% if product.has_3d_model %}
    <model-viewer ...>...</model-viewer>      {# VIEW-01 #}
  {% else %}
    <span class="thumb-mono" ...>...</span>   {# VIEW-02: unchanged current behavior #}
    {% if product.image_url %}<img ...>{% endif %}
  {% endif %}
</div>
```
VIEW-02 needs zero new JS — when there's no GLB the branch never emits a `<model-viewer>`, so the CDN script (also gated) never even loads.

### Per-page script loading (locked)
Put the CDN script in `{% block extra_js %}` of `product_detail.html` AND `models_3d.html`. base.html already exposes `{% block extra_js %}` at line 41 (after `app.js`). Gate it so it only loads when actually needed:

```django
{% block extra_js %}
  {% if product.has_3d_model %}
  <script type="module"
          src="https://cdn.jsdelivr.net/npm/@google/model-viewer@4.3.1/dist/model-viewer.min.js"></script>
  {% endif %}
{% endblock %}
```
(On the gallery page there's no per-product viewer, so the gallery does NOT need the script at all — cards just link to detail. Only load model-viewer on the detail page.)

### Recommended structure (no new dirs)
```
apps/catalog/
├── queries.py     # + ProductQuery.with_3d
├── services.py    # + CatalogService.gallery
├── views.py       # + models_3d
├── urls.py        # + path("modelos-3d/", ...)
└── templates/catalog/
    ├── product_detail.html   # edit: viewer/fallback/STL button
    └── models_3d.html        # NEW: gallery (reuses partials/product_card.html)
apps/core/templates/core/partials/navbar.html  # + nav link
static/css/theme.css          # + .detail-media model-viewer rules
```

### Anti-Patterns to Avoid
- **Embedding a `<model-viewer>` per gallery card.** Each instance spins up a WebGL context + downloads a GLB. Browsers cap live WebGL contexts (~8-16) and GLBs are heavy. Gallery cards must link to detail (locked decision). Confirmed correct.
- **Loading the CDN script in base.html.** It would download Three.js on every page. Per-page only.
- **Floating (unpinned) CDN version.** Pin to 4.3.1.
- **Relying on a custom JS file to "init" the viewer.** model-viewer is declarative — attributes only. No `app.js` changes needed.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 3D rotate/zoom/pan controls | Custom Three.js OrbitControls | `camera-controls` attribute | Pan/zoom/rotate, inertia, touch, keyboard all built in and tuned |
| Loading spinner / progress | Custom overlay | built-in poster + progress bar (`--poster-color`, `slot="progress-bar"`) | Free, accessible, themeable |
| STL preview in browser | An STL parser/renderer | **Don't render STL at all** — plain `<a href="{{ product.stl_url }}" download>` | model-viewer renders GLB/glTF ONLY. STL is download-only (VIEW-03). |
| AR launch button | Custom WebXR/Scene Viewer/Quick Look glue | `ar ar-modes` attributes (+ built-in AR button slot) | One attribute set; degrades to nothing on unsupported devices |
| "Drag to rotate" hint | Custom tooltip | built-in `interaction-prompt` (default `auto`) | Animated hand prompt shows automatically; set `interaction-prompt="none"` to suppress |

**Key insight:** model-viewer is fully declarative. Everything VIEW-01 asks for is an HTML attribute; there is no imperative JS to write for this phase.

## Interaction Attributes (VIEW-01 — verified against modelviewer.dev docs.json)

| Attribute | Recommended value | Default | Effect |
|-----------|-------------------|---------|--------|
| `camera-controls` | (present, no value) | off | **Enables rotate + zoom + pan together.** Pan is included by default. |
| `touch-action` | `"pan-y"` | `"pan-y"` | Lets vertical page scroll pass through the viewer on touch. Keep as locked. |
| `auto-rotate` | (present) | off | Slow idle spin; stops on interaction, resumes after `auto-rotate-delay` (3000ms). |
| `shadow-intensity` | `"1"` | `0` | Contact shadow under the model. Locked decision wants it; default 0 = no shadow, so set `1`. |
| `poster` | `"{{ product.image_url }}"` | `""` | Product image shown until GLB loads / on failure. |
| `loading` | `"lazy"` | `"auto"` | Defers GLB fetch until near viewport. Note: on a single product page it's usually in view; harmless. |
| `reveal` | `"auto"` | `"auto"` | Model reveals automatically when loaded. (`"manual"` only if you call `dismissPoster()` yourself — not needed.) |
| `alt` | pt-br description | `""` | Accessibility (see Accessibility section). REQUIRED for a11y. |
| `interaction-prompt` | leave default `auto`, OR `"none"` | `"auto"` | Animated "drag" hand. The locked "arraste para girar" hint can be this built-in prompt (keep `auto`) instead of custom HTML. |
| `camera-orbit` | omit (use default) | `"0deg 75deg 105%"` | Default framing is good. Only set if a specific angle is wanted. |
| `field-of-view` | omit (use default) | `"auto"` | Auto-frames the model. Leave default. |

**Pan mechanics (verified):** With `camera-controls`, pan is ON by default —
- **Desktop:** right-click drag, OR hold a modifier key (Ctrl/Shift/Alt/Cmd) + left-drag.
- **Touch:** two-finger drag.
- To disable pan you'd add `disable-pan` (there is NO `enable-pan` attribute). We do NOT add it — pan is wanted.

**Recommended attribute set (desktop + touch):**
```
camera-controls auto-rotate touch-action="pan-y" shadow-intensity="1"
loading="lazy" reveal="auto" poster="..." alt="..."
```

## AR (recommendation: INCLUDE — cheap, graceful)

| Attribute | Value | Notes |
|-----------|-------|-------|
| `ar` | (present) | Enables the AR affordance (an AR button appears on supported devices only). |
| `ar-modes` | `"webxr scene-viewer quick-look"` | Default; covers Android (WebXR/Scene Viewer) + iOS (Quick Look). |
| `ar-scale` | `"auto"` | Default. `"fixed"` to lock real-world size. |
| `ios-src` | USDZ URL (optional) | iOS Quick Look needs USDZ. Without it, AR on iOS won't launch; Android still works from the GLB. |

**Cost:** AR is just attributes — no extra script, no extra download on desktop (the AR button is hidden when AR isn't available). On Android Chrome it uses the existing GLB. On iOS it requires a separate `.usdz` (we don't have one yet — no USDZ field on the model).

**Recommendation:** The locked CONTEXT lists AR as "nice-to-have, cheap if yes" and VIEW-A1 is a v2 requirement. Decision: **add `ar ar-modes="webxr scene-viewer quick-look" ar-scale="auto"` now.** It's two attributes, costs nothing on desktop, and gives Android AR for free from the existing GLB. Do NOT add `ios-src`/USDZ now — that requires a new model field + asset pipeline (defer to v2, matching VIEW-A1). The AR button simply won't appear on iOS until USDZ exists; no breakage. If the planner prefers strict v2-scoping, omitting `ar` entirely is also valid — but including it is lower-effort than wiring it later.

## Sizing / CSS (VIEW-01)

`<model-viewer>` is `display:block` but **has no intrinsic size** — without explicit dimensions it can collapse to a tiny or zero height. Size it via the container with `aspect-ratio`. Pattern using existing theme tokens (`--radius-lg`, `--bg-soft`/`--bg-card`, `--border`):

```css
/* static/css/theme.css */
.detail-media model-viewer {
  display: block;
  width: 100%;
  aspect-ratio: 1 / 1;            /* square, matches the 800x800 image convention */
  border-radius: var(--radius-lg);
  background: var(--bg-soft);     /* token -> auto light/dark via [data-theme] */
  border: 1px solid var(--border);
  overflow: hidden;
  /* model-viewer custom props (theme-aware): */
  --poster-color: var(--bg-soft);          /* poster/letterbox bg */
  --progress-bar-color: var(--accent);     /* themed load bar */
  --progress-mask: transparent;
}
```
Notes:
- The site defaults to `data-theme="light"` (base.html line 3) and migrated theme key is `l3d-theme` (line 5) — using tokens means the viewer background flips automatically with the toggle; no JS.
- `aspect-ratio: 1 / 1` keeps layout stable while the GLB downloads (no reflow). Match whatever the current `.detail-media`/`<img>` ratio is so VIEW-02 fallback and VIEW-01 viewer occupy the same box.
- Set `--poster-color` so the poster image letterboxes against the theme background, not black.

## Poster & Loading UX (VIEW-01)

- **Poster = product image:** `poster="{{ product.image_url }}"`. Shown immediately, before/while the GLB downloads, and remains if the GLB fails — this is also the VIEW-02-adjacent safety net even when a GLB exists.
- **Progress bar:** built in. Theme it with `--progress-bar-color: var(--accent)` (above). A custom one via `slot="progress-bar"` is optional and not needed.
- **Lazy:** `loading="lazy"` defers the (potentially large) GLB fetch until near the viewport.
- **Graceful while downloading:** poster + progress bar; no layout shift because the container has a fixed `aspect-ratio`.
- **Optional hint:** prefer the built-in `interaction-prompt` (default `auto` shows an animated hand) over custom "arraste para girar" markup. If a text hint is still wanted, a small absolutely-positioned caption over the container is fine and costs nothing.

## STL Download (VIEW-03)

**Confirmed:** model-viewer renders **GLB/glTF only** — it has no STL support. STL must be download-only. A plain anchor is correct:
```django
{% if product.has_stl %}
  <a href="{{ product.stl_url }}" download class="btn btn-ghost">
    <svg class="icon"><use href="#i-box"></use></svg> Baixar STL
  </a>
{% endif %}
```
- `download` attribute triggers a save instead of navigation (same-origin media — works in dev `static()` serving).
- Place near the add-to-cart block (lines 46-60 of product_detail.html), reuse existing `btn btn-ghost` and an existing sprite icon (`#i-box` or `#i-layers` both exist in the icon sprite usage).
- No JS. No model-viewer involvement.

## Accessibility (VIEW-01)

- **`alt` is required:** set a pt-br description, e.g. `alt="Modelo 3D de {{ product.name }}"`. model-viewer exposes this to screen readers.
- **Keyboard:** model-viewer is focusable and supports arrow-key orbit when focused (built in). Ensure the container isn't `tabindex="-1"`.
- **ARIA:** the component manages its own roles; the `alt` text drives the accessible name. Provide visible context (the heading `<h1>` already labels the product).
- **Reduced motion:** consider gating `auto-rotate` — model-viewer respects `prefers-reduced-motion` for the interaction prompt; auto-rotate itself does not auto-stop, so if strict, drop `auto-rotate` under reduced-motion. Low priority for this phase.

## Common Pitfalls

### Pitfall 1: `.glb` MIME type in Django dev serving
**What goes wrong:** Worry that `static()` serves `.glb` with the wrong Content-Type.
**Reality (verified):** Python `mimetypes.guess_type('x.glb')` returns `(None, None)` (also for `.gltf`, `.stl`, `.usdz`), so Django's dev media view sends `application/octet-stream`. **model-viewer does NOT care** — it fetches the URL as an ArrayBuffer and parses the bytes; Content-Type is ignored for GLB. So dev works as-is.
**For prod (note only, out of scope):** WhiteNoise / a real server should send `model/gltf-binary` for `.glb` and `model/gltf+json` for `.gltf` for correctness/caching, but it is not required for rendering. Record as a prod note; do not implement (matches locked "prod serving out of scope").
**Optional polish (if desired):** register types once at startup — `mimetypes.add_type("model/gltf-binary", ".glb")`. Not necessary for the phase.

### Pitfall 2: Collapsed/zero-height viewer
**What goes wrong:** `<model-viewer>` shows nothing because it has no intrinsic size.
**How to avoid:** Always give the container/element explicit `width` + `aspect-ratio` (see CSS section). This is the #1 model-viewer beginner issue.

### Pitfall 3: Loading the script globally / per-card
**What goes wrong:** Three.js downloaded on every page, or N WebGL contexts in the gallery.
**How to avoid:** CDN script only in detail page `extra_js`, gated by `has_3d_model`; gallery cards link to detail (no viewer).

### Pitfall 4: Touch users trapped (can't scroll past the viewer)
**What goes wrong:** Without `touch-action`, dragging on the viewer never scrolls the page.
**How to avoid:** Keep `touch-action="pan-y"` (locked) — vertical scroll passes through; rotate still works.

### Pitfall 5: CORS on the GLB
**What goes wrong:** Cross-origin GLB blocked.
**Reality:** Media is served same-origin (Django `static()` / WhiteNoise), so no CORS issue. The CDN *script* itself is cross-origin but served with `Access-Control-Allow-Origin: *` (verified on both unpkg and jsDelivr). No action needed.

### Pitfall 6: File size / performance
**What goes wrong:** Large GLBs stall the page.
**How to avoid:** `loading="lazy"` + poster cover UX. For asset hygiene (not code): GLBs should be Draco/meshopt-compressed and reasonably sized (model-viewer supports Draco out of the box). This is an asset-prep note, not a code task.

## Code Examples

### VIEW-01 viewer (verified attributes; modelviewer.dev)
```django
{# inside .detail-media, when product.has_3d_model #}
<model-viewer
    src="{{ product.model_3d_url }}"
    poster="{{ product.image_url }}"
    alt="Modelo 3D de {{ product.name }}"
    camera-controls
    auto-rotate
    touch-action="pan-y"
    shadow-intensity="1"
    loading="lazy"
    reveal="auto"
    ar ar-modes="webxr scene-viewer quick-look" ar-scale="auto">
</model-viewer>
```

### Full `.detail-media` block (VIEW-01 + VIEW-02)
```django
<div class="detail-media reveal">
  {% if product.has_3d_model %}
    <model-viewer src="{{ product.model_3d_url }}" poster="{{ product.image_url }}"
                  alt="Modelo 3D de {{ product.name }}"
                  camera-controls auto-rotate touch-action="pan-y"
                  shadow-intensity="1" loading="lazy" reveal="auto"
                  ar ar-modes="webxr scene-viewer quick-look" ar-scale="auto"></model-viewer>
  {% else %}
    <span class="thumb-mono" style="--acc:{{ product.accent }}">{{ product.monogram }}</span>
    {% if product.image_url %}
      <img src="{{ product.image_url }}" alt="{{ product.name }}"
           onerror="this.onerror=null;this.src='https://picsum.photos/seed/{{ product.slug }}/800/800'">
    {% endif %}
  {% endif %}
</div>
```

### Per-page CDN script (gated)
```django
{% block extra_js %}
  {% if product.has_3d_model %}
  <script type="module"
          src="https://cdn.jsdelivr.net/npm/@google/model-viewer@4.3.1/dist/model-viewer.min.js"></script>
  {% endif %}
{% endblock %}
```

## Django Side (VIEW-04 — confirmed standard, matches existing patterns)

The query→service→view→url→template→navbar chain is exactly the codebase convention (see `ProductQuery.on_sale` / `CatalogService.browse`). Keep it short:

- **queries.py** — mirror `on_sale`. `.active().with_relations()` is the existing optimized queryset; `.exclude(model_3d="")` selects only products with a GLB. Optional `short`/`medium` cache via `cache_utils.get_or_set` (consistent with siblings); the locked decision says cache is optional.
  ```python
  @staticmethod
  def with_3d(limit: int | None = None) -> list[Product]:
      qs = (Product.objects.active().with_relations()
            .exclude(model_3d="").order_by("-sales_count"))
      return list(qs[:limit]) if limit else list(qs)
  ```
- **services.py** — `gallery()` returns `{"products": ProductMapper.to_list(ProductQuery.with_3d())}` plus anything the template hero needs. Mirror the shape of `browse`'s return (but no pagination needed unless desired). `ProductMapper.to_dict` is correct for cards (it lacks 3D fields, which is fine — the gallery already knows every product has a model).
- **views.py** — thin: `def models_3d(request): return render(request, "catalog/models_3d.html", CatalogService.gallery())`.
- **urls.py** — `path("modelos-3d/", views.models_3d, name="models_3d")` (under the existing `catalogo/` mount → final URL `/catalogo/modelos-3d/`).
- **template** `catalog/models_3d.html` — extends base, short hero ("Modelos 3D"), `product-grid` reusing `partials/product_card.html`, pt-br empty state. Cards link to detail (no viewer). The gallery does NOT need the model-viewer CDN script.
- **navbar.html** — add `<a href="{% url 'catalog:models_3d' %}">Modelos 3D</a>` inside `.main-nav` (after "Lançamentos" or near "Promoções").
- **Optional "3D" badge:** wrap the card include in the gallery template rather than editing the shared partial (the partial is reused by catalog/home).

**Invalidation note (optional):** if the gallery query is cached, mirror the existing pattern — add its key to `invalidate_catalog_cache()` so admin uploads of GLBs surface promptly. If left uncached, nothing to do.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `<script nomodule>` legacy build for IE11 | ES-module-only; no legacy build | model-viewer dropped IE/legacy long ago | Don't ship a nomodule fallback — dead weight in 2026. |
| `enable-pan` (never existed) / custom OrbitControls pan | Pan ON by default with `camera-controls`; `disable-pan` to remove | Built-in for years | Just add `camera-controls`; pan is free. |
| Manual `mimetypes` GLB worries | Irrelevant for rendering (ArrayBuffer fetch) | — | Don't block on MIME type in dev. |

**Deprecated/outdated:**
- The `canary` dist-tag points at `2.0.0-rc3` (an old pre-release). Ignore it — `latest` (4.3.1) is the real current release.

## Open Questions

1. **iOS AR (USDZ)** — We render GLB only; iOS Quick Look needs a `.usdz`. There's no USDZ field on `Product`.
   - What we know: Android AR works from GLB now; iOS AR needs USDZ + a model field + asset.
   - Recommendation: Ship `ar` for Android now; defer USDZ/iOS AR to v2 (VIEW-A1). No code blocker.
2. **Gallery cache** — optional per locked decision.
   - Recommendation: skip caching for simplicity, OR add a `short`-bucket cache mirroring siblings + wire into `invalidate_catalog_cache`. Planner's call; both are convention-compliant.
3. **Reduced-motion + auto-rotate** — minor a11y polish; auto-rotate doesn't auto-disable under `prefers-reduced-motion`.
   - Recommendation: low priority; acceptable to leave `auto-rotate` on for v1.

## Sources

### Primary (HIGH confidence)
- npm registry (`npm view @google/model-viewer`) — version **4.3.1**, modified 2026-06-04, dist-tags. Direct registry, authoritative.
- modelviewer.dev `docs.json` (raw GitHub, google/model-viewer master) — attribute names + defaults (camera-controls, disable-pan, touch-action `pan-y`, auto-rotate, poster, loading `auto`, reveal `auto`, shadow-intensity `0`, camera-orbit `0deg 75deg 105%`, field-of-view `auto`, ar/ar-modes `webxr scene-viewer quick-look`/ar-scale `auto`/ar-placement, ios-src, alt, interaction-prompt `auto`).
- Live CDN HEAD checks (2026-06-06): `https://cdn.jsdelivr.net/npm/@google/model-viewer@4.3.1/dist/model-viewer.min.js` and `https://unpkg.com/...` — both HTTP 200, JS MIME, `Access-Control-Allow-Origin: *`.
- Python `mimetypes.guess_type` for `.glb/.gltf/.stl/.usdz` → all `(None, None)` (local check) — confirms dev Content-Type is `application/octet-stream`.
- Codebase: product_detail.html, base.html (`extra_js` block, `l3d-theme`, `data-theme`), product_card.html, mappers.py (`to_detail` exposes `model_3d_url/stl_url/has_3d_model/has_stl`), queries.py/services.py/views.py/urls.py (layer patterns), config/urls.py (`static()` media serving), CLAUDE.md (stack/conventions).

### Secondary (MEDIUM confidence, verified against docs)
- WebSearch: pan defaults (two-finger / right-click / modifier-drag) — corroborated by modelviewer.dev staging-and-cameras docs and `disable-pan` existing in docs.json.
- WebSearch: CDN script tag convention (unpkg/jsDelivr `dist/model-viewer.min.js`, `type="module"`) — corroborated by live HEAD checks.

### Tertiary (LOW confidence)
- None relied upon for prescriptive claims.

## Metadata

**Confidence breakdown:**
- Standard stack / version: HIGH — pulled live from npm registry + verified CDN URLs.
- Attributes / pan behavior: HIGH — read from official docs.json + corroborated.
- MIME/CORS pitfalls: HIGH — verified locally + via CDN response headers.
- Django side: HIGH — directly mirrors existing in-repo patterns.

**Research date:** 2026-06-06
**Valid until:** ~2026-07-06 (model-viewer ships often — re-verify version before a much-later plan; attribute API is stable across minors).
