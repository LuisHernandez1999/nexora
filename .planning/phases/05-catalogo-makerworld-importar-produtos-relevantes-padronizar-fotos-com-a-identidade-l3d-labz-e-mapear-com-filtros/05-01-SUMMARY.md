---
phase: 05
plan: 01
status: complete
completed: 2026-06-07
---

# Plan 05-01 — Catálogo MakerWorld — SUMMARY

## O que foi construído
- **`apps/catalog/branding.py`** — pipeline Pillow `gerar_card(nome, accent)` → PNG 800×800 padronizado na identidade L3D Labz (gradiente radial verde-Luigi, tile com monograma na cor da categoria, nome, wordmark "L3D Labz").
- **`seed_makerworld`** — comando idempotente: 8 categorias (Action Figures, Articulados, Vasos & Plantas, Organizadores, Luminárias, Miniaturas, Gadgets, Decoração) + **24 produtos curados** (estilo MakerWorld) com atributos completos; para cada um gera a foto branded e salva em `Product.image`.
- **Filtro por material** — `ProductQuery.search(material=...)` + `ProductQuery.materials()` + `CatalogService.browse` expõe `materials`/`active_material` + `<select name="material">` no `product_list.html`.

## Decisão-chave
MakerWorld bloqueia scraping (**HTTP 403**), então foi curadoria realista + fotos **geradas** padronizadas (não há foto de autor; a "padronização" vira a geração do card da loja). Usuário ciente.

## Verificação
- `check` limpo; **17/17 testes** (4 novos: branding gera PNG, seed cria categorias+produtos+fotos, idempotência, filtro de material).
- Ao vivo: `/catalogo/` 200 com as fotos branded; `/catalogo/?material=Resina` filtra; select de material renderiza (PETG/PLA/PLA+/Resina).

## key-files
### created
- `apps/catalog/branding.py`, `apps/catalog/management/commands/seed_makerworld.py`, `apps/catalog/tests/test_makerworld.py`
### modified
- `apps/catalog/queries.py`, `apps/catalog/services.py`, `apps/catalog/templates/catalog/product_list.html`

## Pendente (item separado)
Botão "Comprar no WhatsApp" + preço "sob consulta" — aguardando o número do WhatsApp do lojista. As descrições dos produtos já mencionam "preço e prazo combinados no WhatsApp".
