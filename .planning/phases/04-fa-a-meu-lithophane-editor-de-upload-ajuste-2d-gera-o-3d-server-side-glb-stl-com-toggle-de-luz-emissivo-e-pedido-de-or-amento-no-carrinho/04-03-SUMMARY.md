---
phase: 04
plan: 03
status: complete
completed: 2026-06-07
tasks_total: 2
tasks_done: 2
---

# Plan 04-03 — Carrinho + pedido de orçamento — SUMMARY

## O que foi construído
**Carrinho:** `SessionCart` ganhou chave de sessão separada `cart_litho` (`add_litho`/`remove_litho`/`litho_draft_ids`, limpa em `clear()`). `CartService.build` expõe `litho_items` "A combinar" (import deferido anti-ciclo de `LithophaneQuery`) **sem afetar o total** dos produtos. Views/URLs `add_litho`/`remove_litho`. Template `cart/detail.html` mostra o item lithophane, permite remover, e aparece mesmo num carrinho só-lithophane.

**Pedido:** `Order.Status.ORCAMENTO`; `OrderItem.draft_id` + `litho_specs` (JSON) nullable; migration `0002_orcamento_lithophane`. `OrderService.create_from_cart` agora: aceita carrinho só-lithophane, cria `Order` com status `orcamento`, grava `OrderItem`(s) snapshot (Decimal 0.00 + specs JSON), e **pula `PaymentService`** quando há orçamento. `checkout` view/template toleram e exibem os litho "A combinar"; badge de status mapeado (`warn`).

## Verificação
- `manage.py check` limpo; `makemigrations --check` → "No changes detected".
- **Teste de integração** (`test_order_flow.py`, OK): carrinho só-lithophane → `Order.status=orcamento`, `payment_status=PENDING`, `paid_at=None` (pagamento não capturado), `OrderItem` com `draft_id`+`litho_specs`, carrinho esvaziado.

## key-files
### created
- `apps/orders/migrations/0002_orcamento_lithophane.py`
- `apps/lithophane/tests/test_order_flow.py`
### modified
- `apps/cart/{cart,services,views,urls}.py`, `apps/cart/templates/cart/detail.html`
- `apps/orders/{models,services,mappers,views}.py`, `apps/orders/templates/orders/checkout.html`

## Contrato pronto para Plan 04
Botão "Encomendar" do editor chama `POST cart:add_litho draft_id` → item entra no carrinho "a combinar" → checkout existente fecha como orçamento.

## Deviations
Nenhuma relevante. Produtos normais (subtotal/frete/cupom/pagamento) permanecem inalterados quando não há litho.
