---
status: passed
phase: 05-catalogo-makerworld
verified: 2026-06-07
score: 3/3 must-haves
---

# Phase 5 — Catálogo MakerWorld — VERIFICATION

| # | Must-have | Evidência | Status |
|---|-----------|-----------|--------|
| 1 | Pipeline de foto padronizada (identidade L3D Labz) | `branding.gerar_card` → PNG 800×800 testado | ✅ |
| 2 | Comando cria 8 categorias + 24 produtos com foto branded em `Product.image` | `seed_makerworld` testado (categorias/produtos/fotos + idempotência) | ✅ |
| 3 | Produtos aparecem no catálogo e filtram por categoria + material | `/catalogo/` 200 com fotos; `?material=Resina` filtra; select renderiza | ✅ |

**Score 3/3.** 17/17 testes, `check` limpo.

## Deferido
- Scraping real do MakerWorld (403 + licença) — substituído por curadoria + fotos geradas.
- Botão WhatsApp + preço "sob consulta" — bloqueado no número do lojista (item separado).

## UAT manual
- Abrir `/catalogo/`, ver os cards padronizados, filtrar por categoria e por material, conferir a identidade visual nos temas claro/escuro.
