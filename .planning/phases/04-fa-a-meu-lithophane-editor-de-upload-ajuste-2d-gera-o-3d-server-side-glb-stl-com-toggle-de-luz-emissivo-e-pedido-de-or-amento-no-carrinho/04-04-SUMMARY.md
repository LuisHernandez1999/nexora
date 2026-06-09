---
phase: 04
plan: 04
status: complete
completed: 2026-06-07
tasks_total: 3
tasks_done: 3
---

# Plan 04-04 — Editor + visualizador + rota — SUMMARY

## O que foi construído
A camada de apresentação completa da feature "Faça meu Lithophane":
- **Views/rota**: `editor` (GET `/lithophane/`) + `gerar` (POST `/lithophane/gerar/`, decodifica dataURL→PIL→`LithophaneService.gerar`→JSON via `LithophaneMapper`). Rota incluída em `config/urls.py`; link **"Faça meu Lithophane"** no navbar.
- **Template** (`editor.html`): editor estilo `image.png` — rail de ferramentas (enviar foto, inverter), palco central (canvas → model-viewer), painel direito (formatos placa/luminária + curvo/cubo "em breve", sliders tamanho/espessura/brilho, botão Gerar 3D). Slogan obrigatório presente. Botões Encomendar + Baixar STL pós-geração. CSS apendado em `theme.css` (só tokens Luigi, responsivo).
- **JS** (`lithophane-editor.js`, IIFE vanilla): upload→canvas com filtros (brilho/grayscale/inverter via `getImageData`), Gerar 3D (`fetch` POST com `X-CSRFToken` + `toDataURL`), swap canvas→`<model-viewer>` (CDN @4.3.1), **toggle de luz emissivo** (`setEmissiveFactor`/`setEmissiveStrength` + exposure), Encomendar (form para `cart:add_litho`) e Baixar STL.

## Verificação
- `manage.py check` limpo; rotas resolvem; template carrega.
- **Suíte completa do app: 12/12 OK** — inclui `test_views`: editor renderiza com o slogan, `gerar` devolve glb_url/stl_url/draft_id, rejeita imagem inválida (400).

## key-files
### created
- `apps/lithophane/{views,urls}.py`
- `apps/lithophane/templates/lithophane/editor.html`
- `static/js/lithophane-editor.js`
- `apps/lithophane/tests/test_views.py`
### modified
- `config/urls.py` (rota), `apps/core/templates/core/partials/navbar.html` (link), `static/css/theme.css` (bloco do editor)

## Deviations
Teste de view roda com `SECURE_SSL_REDIRECT=False` + storage de estáticos plano (artefatos de rodar com prod settings sem collectstatic; não afeta produção).

## Pendente para UAT manual (browser)
O toggle emissivo e o render do model-viewer dependem do navegador (WebGL) — cobertos por teste de unidade do GLB, mas o "ver com a luz" precisa de validação visual real.
