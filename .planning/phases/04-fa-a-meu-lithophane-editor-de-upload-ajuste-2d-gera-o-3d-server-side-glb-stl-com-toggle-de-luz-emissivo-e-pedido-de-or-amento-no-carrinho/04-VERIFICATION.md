---
status: passed
phase: 04-faca-meu-lithophane
verified: 2026-06-07
score: 5/5 must-haves
method: automated (12 testes) + code inspection
---

# Phase 4 — Faça meu Lithophane — VERIFICATION

**Goal:** O cliente sobe uma foto, vê o modelo 3D do lithophane gerado, alterna um toggle "com luz", e encomenda como pedido de orçamento no carrinho.

## Goal-backward — must-haves

| # | Must-have | Evidência | Status |
|---|-----------|-----------|--------|
| 1 | Geração 3D server-side da foto (GLB+STL watertight, relevo invertido, emissiveTexture) | `generation.py` + 6 testes (`test_generation`): is_watertight GLB/STL, inversão, emissive, <5MB | ✅ |
| 2 | Camada Django persiste o draft e envolve o motor | `LithophaneService.gerar` + `LithophaneDraft`/migration + smoke test `test_service` (2 OK) | ✅ |
| 3 | Carrinho aceita item "a combinar" e checkout cria pedido de orçamento SEM cobrança | `cart_litho` + `Order.Status.ORCAMENTO` + `OrderItem.draft_id/litho_specs` + `test_order_flow`: status orcamento, payment PENDING, paid_at None | ✅ |
| 4 | Editor: upload→canvas→Gerar 3D→model-viewer→toggle de luz emissivo | `editor.html` + `lithophane-editor.js` (setEmissiveFactor/Strength, toDataURL, X-CSRFToken) + `test_views`: editor renderiza, endpoint devolve glb/stl/draft_id | ✅ |
| 5 | Rota /lithophane/, link no navbar, slogan, tema Luigi claro/escuro, pt-br | rota resolve, link no navbar com active-state, slogan no template, CSS só com tokens | ✅ |

**Score: 5/5.** Suíte: `python manage.py test apps.lithophane` → **12/12 OK**. `manage.py check` limpo, `makemigrations --check` → "No changes detected".

## Requisitos
Sem REQ-IDs formais mapeados (phase_req_ids null). must-haves derivados do goal + CONTEXT.

## Deferidos (fora de escopo, por design)
- Formatos **curvo** e **cubo** (UI e enum `format` já nascem prontos; geração implementada depois).
- Precificação automática (mantido "a combinar").
- Endurecimento de media serving 3D em prod (concern transversal pré-existente).

## Pendências de UAT manual (browser / WebGL)
Cobertas por testes de unidade no nível de dados/contrato, mas o render visual depende de um navegador real:
1. Abrir `/lithophane/`, subir uma foto, ajustar brilho/inverter e clicar **Gerar 3D** → o lithophane rotacionável aparece no model-viewer.
2. Clicar **Com luz** → a foto "acende" (efeito emissivo); clicar de novo volta ao relevo branco.
3. **Encomendar** → item "A combinar" no carrinho → checkout → pedido criado como orçamento sem pedir pagamento.
4. **Baixar STL** → arquivo .stl baixa e abre num fatiador.
5. Conferir a identidade Luigi nos temas claro e escuro.
