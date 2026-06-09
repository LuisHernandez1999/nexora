# Design — Faça meu Lithophane

> "Onde memórias preciosas ganham forma na luz."

**Data:** 2026-06-07
**Status:** Aprovado (brainstorm) → rumo a planejamento GSD
**Referência visual:** `image.png` na raiz (editor estilo ItsLitho)

## Visão geral

Novo app `apps/lithophane/` no padrão de camadas do projeto. O cliente abre um
**editor** (inspirado no `image.png`), sobe uma foto, ajusta em 2D ao vivo,
clica **Gerar 3D**, vê o lithophane rotacionável no `model-viewer` com um
**toggle Com luz / Sem luz**, e clica **Encomendar** → entra como item custom
"a combinar" no carrinho → checkout cria um **pedido de orçamento**.

## Decisões do brainstorm

| Tema | Decisão |
|------|---------|
| Geração do 3D | **Servidor (Python)** — gera GLB (viewer) + STL (impressão) no upload. Reusa model-viewer + "Baixar STL" existentes; respeita "sem framework JS pesado". |
| Fim do fluxo | **Termina em pedido (carrinho)** → checkout existente. |
| UI | **Editor completo**: canvas central + painel de controles (forma/tamanho/espessura), como a referência. |
| Formatos | Oferecer os 4: **placa, luminária, curvo, cubo** (com faseamento — ver abaixo). |
| Toggle de luz | **Brilho da foto (emissivo)** — ao ligar, a foto "acende" nítida na placa em tom quente. |
| Preço | **Orçamento "a combinar"** — sem preço fixo; pedido entra como orçamento, valor confirmado depois. |

## Arquitetura (camadas existentes)

Novo app `apps/lithophane/` espelhando models → queries → services → mappers → views → templates:

- **`services.py`** — `LithophaneService.generate(image, specs)`: única camada que
  processa/escreve. Recebe imagem ajustada + specs, gera os arquivos 3D, persiste o rascunho.
- **`generation.py`** — motor isolado e swappable (como `apps/orders/payments.py`):
  foto → heightmap → malha → **GLB** (com `emissiveTexture` da foto, pro brilho) + **STL**.
  Stack: `Pillow` + `numpy` + **`trimesh`** (exporta glb e stl). Heightmap reduzido
  (~300px) pra manter a malha leve.
- **`views.py`** — thin: página do editor; endpoint `POST` recebe imagem+specs,
  chama o service, devolve URLs do GLB/poster (JSON).

## Modelo de dados

`LithophaneDraft(TimeStampedModel)`:
- `image` (original enviada)
- `model_glb`, `model_stl` (FileField gerados)
- `format` — `TextChoices`: placa / luminaria / curvo / cubo
- `size`, `thickness`
- `user`/`session_key` (dono do rascunho)

O carrinho referencia o draft (`draft_id`). No checkout, o `OrderItem` guarda
snapshot (formato, tamanho, link da foto) — como os pedidos já fazem snapshot.

## Editor (front — vanilla JS, sem framework pesado)

- **Canvas central**: `<canvas>` com a foto em escala de cinza + moldura de crop.
  Crop / escala / brilho / inverter rodam **no navegador** (leve, só canvas/CSS).
- **Painel direito**: presets de **formato** (4), sliders de **tamanho** e
  **espessura**, botão **Gerar 3D**.
- **Gerar 3D**: envia imagem ajustada (dataURL) + specs → servidor gera → o canvas
  troca pelo `<model-viewer>` (mesmo CDN `@google/model-viewer@4.3.1` já usado no detalhe do produto).

## Toggle de luz (emissivo)

GLB sai com `baseColor` branco (relevo) + **`emissiveTexture`** = a foto. O JS do
toggle liga/desliga via API do model-viewer (`material.emissiveTexture` /
`emissiveStrength` + troca de exposure/ambiente). **Sem luz** = relevo branco;
**Com luz** = foto acende em tom quente. Botão flutuante 💡 sobre o viewer.

## Pedido (orçamento "a combinar")

- **Encomendar** adiciona uma **linha custom** ao `SessionCart` (com `draft_id` +
  specs, preço = `None`/"a combinar").
- No checkout, cria `Order` com status **`orcamento`** (novo `TextChoices`), total
  pendente, **sem captura de pagamento** (pula o `PaymentService`).
- Admin mostra foto + specs; equipe confirma o valor depois.
- ⚠️ Carrinho/checkout precisam **tolerar item sem preço** (hoje assumem `price`).

## Formatos — faseamento

- **Fase 1 (núcleo):** Placa plana + Luminária (mesma malha plana; luminária =
  +base/flag). Entrega o valor rápido.
- **Fase 2:** Curvo (curvatura na malha) e Cubo (4 uploads + 4 faces) — mais
  complexos. A UI e o `format` já nascem prontos pros 4; curvo/cubo implementados depois.

## Identidade & rota

- Rota `/lithophane/`, copy pt-br, slogan "Onde memórias preciosas ganham forma na luz".
- Tokens Luigi + tema claro/escuro. Link no navbar ("Faça meu Lithophane").
- Reusa `model-viewer` e o padrão "Baixar STL".

## Pontos de atenção

- **Geração de malha em Python** é a parte mais nova/arriscada → prototipar
  `generation.py` cedo (TDD) com foto real antes de plugar na UI.
- **Carrinho com item sem preço** exige ajuste no `SessionCart`/checkout.
- **Cubo** quebra o padrão "1 foto" → por isso faseado.
- **Tamanho do GLB** vs performance mobile → controlado pela resolução do heightmap.
