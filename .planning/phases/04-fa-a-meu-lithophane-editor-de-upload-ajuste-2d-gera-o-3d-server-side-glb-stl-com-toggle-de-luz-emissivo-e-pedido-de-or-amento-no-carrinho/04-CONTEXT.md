# Phase 4: Faça meu Lithophane - Context

**Gathered:** 2026-06-07
**Status:** Ready for planning

> Decisões derivadas do design aprovado em `docs/superpowers/specs/2026-06-07-faca-meu-lithophane-design.md` (brainstorm validado com o usuário). Smart discuss não reabriu grey areas — todas já foram decididas e aceitas.

<domain>
## Phase Boundary

Entrega a feature **"Faça meu Lithophane"**: um editor web onde o cliente sobe uma foto, ajusta em 2D ao vivo, gera no servidor o modelo 3D do lithophane (GLB para visualização + STL imprimível), visualiza no `<model-viewer>` com um toggle **Com luz / Sem luz** (efeito emissivo), e encomenda a peça como **pedido de orçamento "a combinar"** via carrinho/checkout existentes.

**No escopo (Fase 1 — núcleo):**
- App `apps/lithophane/` no padrão de camadas (models/queries/services/mappers/views/templates).
- Motor de geração `generation.py` (Pillow + numpy + trimesh): foto → heightmap → malha → GLB (com emissiveTexture) + STL.
- Editor front-end vanilla JS (canvas 2D: crop/escala/brilho/inverter) + painel de controles.
- Visualizador `model-viewer` com toggle de luz emissivo.
- Formatos **placa plana** e **luminária/abajur** (mesma malha plana; luminária = base/flag).
- Fluxo "Encomendar" → item custom "a combinar" no carrinho → checkout cria pedido com status `orcamento` (sem captura de pagamento).
- Rota `/lithophane/`, link no navbar, identidade Luigi + tema claro/escuro, copy pt-br.

**Fora de escopo (deferido p/ fase futura):**
- Formatos **curvo** e **cubo** (curvatura de malha / 4 uploads) — UI e enum `format` nascem prontos, implementação depois.
- Precificação automática (fica "a combinar").

</domain>

<decisions>
## Implementation Decisions

### Geração do modelo 3D
- Geração **server-side em Python** (não client-side; respeita "sem framework JS pesado").
- Stack: `Pillow` + `numpy` + `trimesh` (trimesh exporta GLB e STL).
- Pipeline: imagem → escala de cinza → heightmap reduzido (~300px no maior lado) → grade de vértices (relevo invertido: claro=fino, escuro=grosso) → malha → exporta GLB + STL.
- Motor isolado e swappable em `generation.py` (espelha o padrão de `apps/orders/payments.py`).
- Controlar tamanho do GLB pela resolução do heightmap (performance mobile).

### Toggle de luz (emissivo)
- "Sem luz" = relevo branco (baseColor claro, mostra a superfície física).
- "Com luz" = a foto "acende": GLB carrega `emissiveTexture` = a foto; o JS liga/desliga via API do model-viewer (`material.emissiveTexture`/`emissiveStrength` + ajuste de exposure/ambiente) num tom quente de LED.
- Botão flutuante 💡 sobre o viewer.

### Editor (front-end)
- Vanilla JS + `<canvas>` (sem Three.js, sem framework).
- Ajuste 2D ao vivo no navegador: crop, escala, brilho/contraste, inverter.
- Painel direito: presets de formato, sliders de tamanho e espessura, botão "Gerar 3D".
- Ao clicar "Gerar 3D": POST (imagem ajustada como dataURL + specs) → service gera → canvas troca pelo `<model-viewer>` (CDN `@google/model-viewer@4.3.1`, mesmo já usado no detalhe do produto).

### Dados & pedido
- `LithophaneDraft(TimeStampedModel)`: `image`, `model_glb`, `model_stl`, `format` (TextChoices placa/luminaria/curvo/cubo), `size`, `thickness`, dono (`user`/`session_key`).
- Carrinho referencia o draft (`draft_id`); preço = `None`/"a combinar".
- Checkout cria `Order` com novo status `orcamento`, total pendente, **pula `PaymentService`**.
- `OrderItem` guarda snapshot (formato, tamanho, link da foto) — coerente com o padrão de snapshot dos pedidos.
- ⚠️ `SessionCart`/checkout precisam tolerar item sem preço (hoje assumem `price`).

### Identidade & integração
- Rota `/lithophane/`, slogan "Onde memórias preciosas ganham forma na luz".
- Tokens Luigi + tema claro/escuro; link "Faça meu Lithophane" no navbar.
- Reusa `model-viewer` e o padrão "Baixar STL".

### Claude's Discretion
- Detalhes do algoritmo de heightmap→malha (densidade, base sólida, espessura mín/máx), nomes internos de funções, estrutura exata dos endpoints, e como exatamente o status `orcamento` se integra ao fluxo de checkout (desde que não capture pagamento) ficam a critério do Claude, seguindo as convenções do projeto.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `<model-viewer>` já integrado em `apps/catalog/templates/catalog/product_detail.html` (CDN @4.3.1, `camera-controls auto-rotate`, poster, AR) — replicar padrão.
- Padrão "Baixar STL" e campos `model_3d`/`model_stl` (FileField + `FileExtensionValidator`) em `apps/catalog/models.py`.
- `apps/orders/payments.py` — padrão de boundary isolado/swappable (modelo para `generation.py`).
- `apps/cart/cart.py` (`SessionCart`) + `apps/cart/middleware.py` — estado de carrinho por sessão.
- `apps/orders/services.py` (`OrderService.create_from_cart`, `@transaction.atomic`) + `Order.Status` TextChoices.
- `apps/core/models.TimeStampedModel`, `BaseMapper`/`BaseService`/`BaseQuery` (`apps/core/layers.py`).
- Tokens CSS Luigi em `static/css/theme.css`; dict `SITE` em `config/settings/base.py`.

### Established Patterns
- Camadas: views finas → services (única escrita) → queries (só ORM/cache) → mappers (Model→dict). Imports cross-app absolutos, intra-app relativos.
- Pillow já é dependência (prod). numpy/trimesh são novos — adicionar a `requirements.txt`.
- model-viewer carregado por página em `extra_js`, gated.
- JS vanilla IIFE em `static/js/app.js`; tema via localStorage `l3d-theme`.

### Integration Points
- `config/urls.py` — montar `path("lithophane/", include("apps.lithophane.urls"))`.
- `apps/core/templates/core/partials/navbar.html` — adicionar link "Faça meu Lithophane".
- `apps/cart/` e `apps/orders/` — estender p/ item custom sem preço + status `orcamento`.
- Media serving: arquivos GLB/STL gerados vão pra MEDIA (ver CONCERNS sobre serving em prod).

</code_context>

<specifics>
## Specific Ideas

- Referência visual: `image.png` na raiz (editor estilo ItsLitho — rail de ferramentas à esquerda, canvas central com moldura de crop, painel direito com forma/tamanho).
- Slogan obrigatório: "Onde memórias preciosas ganham forma na luz."
- Efeito "com luz" deve ser nítido e impactante (a foto acende), priorizando clareza do efeito sobre realismo físico.

</specifics>

<deferred>
## Deferred Ideas

- Formato **curvo** (lampshade) — curvatura na malha.
- Formato **cubo / caixa de luz** — 4 uploads, 4 faces.
- Precificação automática por dimensão/volume (mantido "a combinar" por ora).
- Endurecimento do serving de media 3D em prod (CDN/object storage) — já listado em CONCERNS, transversal.

</deferred>
