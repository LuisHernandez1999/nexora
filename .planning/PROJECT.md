# L3D Labz

## What This Is

Site de uma fábrica de impressão 3D chamada **L3D Labz**. É uma loja Django existente (antes "Nexora") — catálogo, carrinho, checkout, pedidos e contas — que será **rebatizada e redesenhada** com identidade visual inspirada nas cores do Luigi (verde, branco, azul) num estilo **minimalista e elegante**, com suporte a tema claro/escuro. O grande diferencial é uma **aba de visualização 3D**: o cliente abre e manipula o modelo 3D do produto (rotacionar, zoom, pan) de forma intuitiva direto no navegador, com download do arquivo STND/STL disponível.

## Core Value

O cliente consegue **visualizar o modelo 3D do produto de forma intuitiva** num site bonito e minimalista com a marca L3D Labz — se tudo mais falhar, o visualizador 3D e a identidade da marca precisam funcionar.

## Requirements

### Validated

<!-- Inferido do código existente (ver .planning/codebase/). Já funciona e é confiável. -->

- ✓ Catálogo de produtos com categorias, filtros e busca — existing (`apps/catalog`)
- ✓ Página de detalhe de produto — existing (`apps/catalog/templates/catalog/product_detail.html`)
- ✓ Carrinho de compras (sessão) — existing (`apps/cart`)
- ✓ Checkout e criação de pedidos com pagamento simulado — existing (`apps/orders`)
- ✓ Contas de usuário (login/registro/perfil) com modelo de usuário por e-mail — existing (`apps/accounts`)
- ✓ Promoções/ofertas — existing (`apps/promotions`)
- ✓ Tema claro/escuro com toggle e persistência em localStorage — existing (`static/js/app.js`, `base.html`)
- ✓ Sistema de design tokens em CSS, sem framework, mobile-first — existing (`static/css/theme.css`)

### Active

<!-- Escopo atual desta milestone. -->

- [ ] Rebrand completo de "Nexora" para "L3D Labz" (nome, wordmark, logo, chave de tema, todas as strings)
- [ ] Nova paleta de cores inspirada no Luigi (verde primário, branco, azul de detalhe) aplicada via tokens
- [ ] Identidade calibrada para os DOIS temas (light + dark) com toggle existente
- [ ] Logo "L" (estilo emblema do boné do Luigi) em SVG inline
- [ ] Home redesenhada num estilo minimalista (mais respiro, menos ornamento)
- [ ] Campo de modelo 3D (GLB) e campo de arquivo STL no modelo `Product`
- [ ] Visualizador 3D interativo (rotacionar/zoom/pan) na página do produto via `<model-viewer>`
- [ ] Aba/galeria dedicada de modelos 3D acessível pela navegação
- [ ] Download do arquivo STL disponível em cada produto que tiver modelo

### Out of Scope

<!-- Limites explícitos. -->

- Gateway de pagamento real — segue simulado (`apps/orders/payments.py`); fora desta milestone
- Conversão automática de STL→GLB no servidor — modelos GLB são fornecidos/enviados manualmente; STL é armazenado para download
- Realidade aumentada (AR) — `<model-viewer>` suporta nativamente, mas não é foco agora (pode vir grátis)
- Cobertura de testes ampla — projeto não tem testes; só testaremos o que for crítico para o novo escopo
- Correção de bugs pré-existentes não relacionados (oversell no checkout, cache stale) — registrados em CONCERNS.md, fora do escopo deste rebrand

## Context

- **Brownfield**: base Django bem estruturada e em camadas (models/services/queries/serializers/mappers/views por app). Ver `.planning/codebase/`.
- **Stack**: Django 5.2 / Python 3.13, DRF, SQLite (dev) / PostgreSQL (prod), WhiteNoise + gunicorn, CSS próprio + JS vanilla, Google Fonts (Inter/Sora).
- **Localização**: tudo em pt-br (verbose_name, help_text, UI copy, URLs).
- **Marca centralizada**: `config/settings/base.py` dict `SITE` + tokens em `static/css/theme.css`. Mas há ~20 ocorrências hardcoded de "Nexora" e o wordmark do navbar é dividido à mão (`nex<b>ora</b>`), além da chave `localStorage 'nexora-theme'` em dois arquivos que precisam mudar juntos.
- **Bloqueio da feature 3D**: `Product` só tem `image`/`image_url` hoje — precisa de novos campos para GLB e STL. Viewer monta em `product_detail.html`.
- **Cores Luigi (referência)**: verde do boné (~#3CA93C / #2E9E2E), branco do emblema, azul dos olhos (~#2BA6E0), marrom do bigode, vermelho da boca — verde + branco como base, azul como acento.

## Constraints

- **Tech stack**: manter sem framework JS pesado — `<model-viewer>` é web component (1 script, zero build), encaixa no padrão vanilla atual.
- **Compatibility**: preservar a arquitetura em camadas e o padrão de design tokens existentes; rebrand via tokens, não reescrita.
- **Performance**: arquivos 3D (GLB/STL) podem ser grandes — atenção ao carregamento (lazy/poster) e ao serving de media em prod.
- **Localização**: toda copy nova em pt-br.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Exibir 3D em GLB via `<model-viewer>` | Web component sem build, rotate/zoom/pan + AR grátis, casa com stack vanilla | — Pending |
| Sempre armazenar + oferecer download do STL | É loja de impressão 3D; STL é o arquivo imprimível que o cliente quer | — Pending |
| Tema claro + escuro (toggle existente) | Usuário pediu os dois; site já tem a infra de toggle | — Pending |
| Rebrand via tokens CSS + dict `SITE` | Mudança de cor/ marca de baixo esforço e alto ROE | — Pending |
| Estilo light/clean minimalista como base estética | Pedido do usuário: "minimalista e lindo" | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-05 after initialization*
