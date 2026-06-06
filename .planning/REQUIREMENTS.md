# Requirements: L3D Labz

**Defined:** 2026-06-05
**Core Value:** O cliente consegue visualizar o modelo 3D do produto de forma intuitiva num site bonito e minimalista com a marca L3D Labz.

## v1 Requirements

Requisitos para esta milestone (rebrand + visualizador 3D). Cada um mapeia para uma fase do roadmap.

### Marca (Brand)

- [ ] **BRAND-01**: Todas as ocorrências de "Nexora" são substituídas por "L3D Labz" (title, meta description, copy, footer, dict `SITE`, seed/admin) — nenhum "Nexora" visível resta
- [ ] **BRAND-02**: O navbar exibe o wordmark "L3D Labz" + um logo "L" em SVG inline (estilo emblema do boné do Luigi), substituindo o logo `koala`
- [ ] **BRAND-03**: A chave de tema em localStorage migra de `nexora-theme` para uma chave L3D em ambos os arquivos (`base.html`, `app.js`) sem quebrar a persistência do tema

### Tema & Cores (Theme)

- [ ] **THEME-01**: A paleta inspirada no Luigi (verde primário, branco, azul de acento) é aplicada via tokens CSS no tema escuro
- [ ] **THEME-02**: A mesma identidade é calibrada e legível no tema claro (light/clean como estética base)
- [ ] **THEME-03**: O cliente alterna entre tema claro e escuro pelo toggle existente e a escolha persiste entre páginas/recargas

### Interface Minimalista (UI)

- [ ] **UI-01**: A home é redesenhada num estilo minimalista (mais espaço em branco, menos ornamentos/gradientes), mantendo as seções essenciais
- [ ] **UI-02**: O tratamento minimalista é consistente nas páginas-chave (catálogo e detalhe de produto)

### Dados do Modelo 3D (Model)

- [ ] **MODEL-01**: O modelo `Product` ganha um campo para o arquivo de exibição 3D (GLB/glTF)
- [ ] **MODEL-02**: O modelo `Product` ganha um campo para o arquivo imprimível (STL)
- [ ] **MODEL-03**: O administrador consegue subir GLB e STL por produto pelo Django admin

### Visualizador 3D (Viewer)

- [ ] **VIEW-01**: Na página de detalhe do produto, quando há GLB, o cliente vê um visualizador 3D interativo e consegue rotacionar, dar zoom e mover (pan) de forma intuitiva
- [ ] **VIEW-02**: Quando o produto não tem GLB, a área de mídia faz fallback gracioso para a imagem atual (sem quebrar layout)
- [ ] **VIEW-03**: Quando há STL, o cliente consegue baixar o arquivo STL a partir da página do produto
- [ ] **VIEW-04**: Existe uma aba/galeria de "Modelos 3D" acessível pela navegação, listando os produtos que têm modelo 3D para visualização

## v2 Requirements

Reconhecidos mas adiados — fora do roadmap atual.

### Visualizador avançado

- **VIEW-A1**: Modo AR (realidade aumentada) no celular via `<model-viewer>`
- **VIEW-A2**: Conversão automática STL→GLB no servidor (upload só de STL)
- **VIEW-A3**: Configurador de cor/material do modelo no viewer

## Out of Scope

Excluídos explicitamente para evitar scope creep.

| Feature | Reason |
|---------|--------|
| Gateway de pagamento real | Segue simulado (`apps/orders/payments.py`); não é foco do rebrand |
| Cobertura de testes ampla | Projeto sem testes; só validamos o crítico do novo escopo |
| Correção de bugs pré-existentes (oversell, cache stale) | Registrados em `.planning/codebase/CONCERNS.md`; fora deste rebrand |
| Conversão automática STL→GLB | GLB é fornecido manualmente nesta milestone (ver VIEW-A2 em v2) |

## Traceability

Preenchido durante a criação do roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| BRAND-01 | TBD | Pending |
| BRAND-02 | TBD | Pending |
| BRAND-03 | TBD | Pending |
| THEME-01 | TBD | Pending |
| THEME-02 | TBD | Pending |
| THEME-03 | TBD | Pending |
| UI-01 | TBD | Pending |
| UI-02 | TBD | Pending |
| MODEL-01 | TBD | Pending |
| MODEL-02 | TBD | Pending |
| MODEL-03 | TBD | Pending |
| VIEW-01 | TBD | Pending |
| VIEW-02 | TBD | Pending |
| VIEW-03 | TBD | Pending |
| VIEW-04 | TBD | Pending |

**Coverage:**
- v1 requirements: 15 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 15 ⚠️

---
*Requirements defined: 2026-06-05*
*Last updated: 2026-06-05 after initial definition*
