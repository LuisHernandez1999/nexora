# Phase 3: Visualizador 3D & Galeria - Context

**Gathered:** 2026-06-06
**Status:** Ready for planning
**Source:** User decisions (locked) + research pending

<domain>
## Phase Boundary

Entrega a **experiência 3D para o cliente**: visualizador interativo na página do produto, fallback gracioso, download do STL, e uma **aba/galeria "Modelos 3D"** na navegação. Consome os campos criados na Fase 2 (`model_3d`, `model_stl`) já expostos no `ProductMapper.to_detail` (`model_3d_url`, `stl_url`, `has_3d_model`, `has_stl`).

Cobre: VIEW-01, VIEW-02, VIEW-03, VIEW-04.
</domain>

<decisions>
## Implementation Decisions (LOCKED — detalhes técnicos finos confirmados pela pesquisa)

### Tecnologia do viewer
- Usar o web component **`<model-viewer>`** do Google (sem build, encaixa no stack vanilla).
- Carregar via **CDN como ES module**, SOMENTE nas páginas que precisam (detalhe do produto + galeria), via `{% block extra_js %}`. NÃO carregar globalmente no base.html. (Pesquisa: confirmar versão major estável atual e URL exata — unpkg/jsdelivr — e se há fallback/`loading`.)
- Atributos esperados: `camera-controls`, `auto-rotate`, `touch-action="pan-y"`, `shadow-intensity`, `poster` (usar a imagem do produto como poster), `loading="lazy"`, `reveal`. AR (`ar`/`ar-modes`) é bom-ter (pesquisa decide se inclui agora — barato se sim).

### VIEW-01 — Viewer no detalhe (`apps/catalog/templates/catalog/product_detail.html`)
- Na área `.detail-media`: QUANDO `product.has_3d_model`, renderizar o `<model-viewer src="{{ product.model_3d_url }}" poster="{{ product.image_url }}" ...>` preenchendo o container (aspect-ratio definido no CSS, cantos arredondados, fundo coerente com o tema).
- O viewer deve permitir **rotacionar, zoom e pan** de forma intuitiva (camera-controls cobre rotate+zoom; pan via configuração apropriada — pesquisa confirma como habilitar pan, ex.: `camera-controls` + `enable-pan`/`touch-action`).
- Adicionar uma dica visual sutil ("arraste para girar") opcional.

### VIEW-02 — Fallback gracioso
- QUANDO NÃO há GLB (`not product.has_3d_model`): manter o comportamento atual da `.detail-media` (o `thumb-mono` monograma + `<img>` com onerror). Sem quebra de layout. É só um `{% if %}/{% else %}`.

### VIEW-03 — Download do STL
- QUANDO `product.has_stl`: exibir um botão/link **"Baixar STL"** perto do bloco de compra (add-to-cart), usando classes existentes (`btn btn-ghost`), `href="{{ product.stl_url }}"`, atributo `download`, com ícone (ex.: `#i-box` ou `#i-layers`). Texto pt-br.
- QUANDO não há STL: não mostrar o botão.

### VIEW-04 — Aba/Galeria "Modelos 3D"
Seguir a arquitetura em camadas existente (query → service → view → template):
- **queries.py** (`ProductQuery`): adicionar
  ```python
  @staticmethod
  def with_3d(limit: int | None = None) -> list[Product]:
      qs = (Product.objects.active().with_relations()
            .exclude(model_3d="").order_by("-sales_count"))
      return list(qs[:limit]) if limit else list(qs)
  ```
  (Excluir `model_3d=""` pega só quem tem GLB. Sem cache obrigatório, ou cache bucket curto — opcional.)
- **services.py** (`CatalogService`): adicionar `gallery()` que retorna o context com a lista mapeada (`ProductMapper.to_dict`) — reaproveitar o padrão de `browse`.
- **views.py**: `def models_3d(request): return render(request, "catalog/models_3d.html", CatalogService.gallery())`.
- **urls.py** (catalog): `path("modelos-3d/", views.models_3d, name="models_3d")`.
- **template** `apps/catalog/templates/catalog/models_3d.html`: extends base, hero/título curto ("Modelos 3D"), grid reusando `catalog/partials/product_card.html`. Cada card **leva ao detalhe** (onde está o viewer) — NÃO embutir um viewer por card (perf). Empty state pt-br se não houver modelos.
- **navbar** (`apps/core/templates/core/partials/navbar.html`): adicionar link "Modelos 3D" → `{% url 'catalog:models_3d' %}` na `main-nav`.
- (Opcional) badge "3D" no card na galeria — só se trivial; o card é compartilhado, então preferir um wrapper na galeria a alterar o partial.

### CSS (`static/css/theme.css`)
- Adicionar estilos para o container do `model-viewer` (altura/aspect-ratio, radius, fundo por tema, width 100%). Reusar tokens. Sem framework.

### Media / serving
- Dev serve media via `static()` em `config/urls.py` (já confirmado). Prod (serving de GLB/STL grandes) fica fora do escopo — registrar como nota, não implementar.
</decisions>

<canonical_refs>
## Canonical References

### Arquivos a tocar
- `apps/catalog/templates/catalog/product_detail.html` — viewer + fallback + botão STL
- `apps/catalog/templates/catalog/models_3d.html` — NOVO (galeria)
- `apps/catalog/queries.py` — `ProductQuery.with_3d`
- `apps/catalog/services.py` — `CatalogService.gallery`
- `apps/catalog/views.py` — `models_3d`
- `apps/catalog/urls.py` — rota `modelos-3d/`
- `apps/core/templates/core/partials/navbar.html` — link na nav
- `static/css/theme.css` — estilo do container do viewer
- `apps/catalog/templates/catalog/partials/product_card.html` — (referência; só alterar se badge trivial)

### Dados disponíveis (Fase 2)
- `ProductMapper.to_detail` já entrega: `model_3d_url`, `stl_url`, `has_3d_model`, `has_stl`.
- `ProductMapper.to_dict` (usado nos cards) NÃO tem os campos 3D — a galeria já sabe que todos têm modelo.

### Convenções
- `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/ARCHITECTURE.md` — camadas, cache, pt-br.
- Env: `manage.py` em dev falha por `debug_toolbar` ausente — usar `--settings=config.settings.prod` p/ checks.
</canonical_refs>

<specifics>
## Specific Ideas
- Core value do projeto: "cliente visualiza o modelo 3D de forma intuitiva". O viewer no detalhe é o coração desta fase.
- Minimalismo: container do viewer limpo, sem poluição; um único controle implícito (arrastar).
</specifics>

<deferred>
## Deferred Ideas
- AR no celular (se a pesquisa não incluir agora) — v2.
- Mini-viewer embutido em cada card da galeria — perf, evitar.
- Serving de media em produção / CDN para arquivos grandes — infra.
- Conversão STL→GLB automática — v2.
</deferred>

---

*Phase: 03-visualizador-3d-galeria*
*Context gathered: 2026-06-06 (locked user decisions; technical specifics pending research)*
