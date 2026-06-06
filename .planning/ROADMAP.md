# Roadmap: L3D Labz

## Overview

Esta milestone transforma a loja Django existente ("Nexora") na **L3D Labz**: uma loja de impressão 3D com identidade visual inspirada no Luigi (verde + branco + azul de acento), estética minimalista nos dois temas (claro/escuro), e um diferencial de **visualização 3D interativa** do produto. O percurso vai da camada de marca/aparência (tokens CSS, wordmark, strings) — que entrega sozinha a identidade L3D Labz — para a fundação de dados 3D no modelo `Product` (campos GLB/STL + upload via admin), e termina no visualizador `<model-viewer>` na página do produto, com download de STL e uma galeria dedicada de modelos 3D. A fase de marca é independente da feature 3D; dentro da feature 3D, os dados (Fase 2) precedem o visualizador (Fase 3).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Rebrand & UI Minimalista** - Marca L3D Labz, paleta Luigi nos dois temas e redesign minimalista das páginas-chave
- [ ] **Phase 2: Fundação de Dados 3D** - Campos GLB/STL no `Product` com upload via Django admin e migração
- [ ] **Phase 3: Visualizador 3D & Galeria** - `<model-viewer>` no detalhe do produto, fallback de imagem, download STL e aba de Modelos 3D

## Phase Details

### Phase 1: Rebrand & UI Minimalista
**Goal**: Todo o site exibe a marca L3D Labz com a paleta inspirada no Luigi, calibrada e legível nos temas claro e escuro, num visual minimalista — sem nenhum vestígio de "Nexora".
**Depends on**: Nothing (first phase, independente da feature 3D)
**Requirements**: BRAND-01, BRAND-02, BRAND-03, THEME-01, THEME-02, THEME-03, UI-01, UI-02
**Success Criteria** (what must be TRUE):
  1. O cliente navega por home, catálogo, detalhe de produto, promoções, carrinho e footer e não encontra nenhum texto "Nexora" visível — só "L3D Labz".
  2. O navbar exibe o wordmark "L3D Labz" ao lado de um logo "L" em SVG inline (emblema estilo Luigi), no lugar do logo `koala`.
  3. A paleta verde/branco/azul está aplicada via tokens CSS e a identidade fica legível e coerente tanto no tema escuro quanto no claro.
  4. O cliente alterna entre tema claro e escuro pelo toggle existente e a escolha persiste entre páginas e recargas (chave localStorage migrada sem quebrar persistência).
  5. A home e as páginas-chave (catálogo e detalhe) têm tratamento minimalista (mais espaço em branco, menos ornamento) mantendo as seções essenciais.
**Plans**: 2 plans
- [x] 01-01-PLAN.md — Marca L3D Labz: paleta Luigi (dark+light), emblema "L", wordmark, migração da chave de tema, strings
- [ ] 01-02-PLAN.md — UI minimalista: home, catálogo e detalhe (respiro + verde, sem reescrever o CSS)

### Phase 2: Fundação de Dados 3D
**Goal**: O modelo `Product` armazena um arquivo de exibição 3D (GLB) e um arquivo imprimível (STL) por produto, e o administrador consegue subir ambos pelo Django admin.
**Depends on**: Nothing técnico de Fase 1 (pode rodar em paralelo); precede a Fase 3.
**Requirements**: MODEL-01, MODEL-02, MODEL-03
**Success Criteria** (what must be TRUE):
  1. O `Product` tem um campo para o arquivo de exibição 3D (GLB/glTF) e a migração correspondente aplica sem erro.
  2. O `Product` tem um campo para o arquivo imprimível (STL) e a migração correspondente aplica sem erro.
  3. O administrador abre um produto no Django admin, sobe um GLB e um STL, salva, e os arquivos ficam associados ao produto e disponíveis para uso pelas camadas de leitura/mapper.
**Plans**: TBD

### Phase 3: Visualizador 3D & Galeria
**Goal**: O cliente visualiza e manipula o modelo 3D do produto direto no navegador, baixa o STL imprimível, e descobre os produtos com modelo por uma galeria dedicada — com fallback gracioso quando não há modelo.
**Depends on**: Phase 2
**Requirements**: VIEW-01, VIEW-02, VIEW-03, VIEW-04
**Success Criteria** (what must be TRUE):
  1. Na página de detalhe de um produto com GLB, o cliente vê um visualizador 3D interativo e consegue rotacionar, dar zoom e mover (pan) de forma intuitiva.
  2. Num produto sem GLB, a área de mídia faz fallback gracioso para a imagem atual, sem quebra de layout.
  3. Quando o produto tem STL, o cliente consegue baixar o arquivo STL a partir da página do produto.
  4. Existe uma aba/galeria "Modelos 3D" acessível pela navegação que lista apenas os produtos que têm modelo 3D para visualizar.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 (Fase 1 e Fase 2 são independentes e podem ser paralelizadas; Fase 3 depende da Fase 2)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Rebrand & UI Minimalista | 0/2 | Planned | - |
| 2. Fundação de Dados 3D | 0/TBD | Not started | - |
| 3. Visualizador 3D & Galeria | 0/TBD | Not started | - |
