---
phase: 03-visualizador-3d-galeria
plan: 01
subsystem: catalog (detalhe do produto)
tags: [model-viewer, 3d, glb, stl, viewer, fallback, css-tokens, cdn]
requires:
  - "ProductMapper.to_detail (Fase 2): model_3d_url, stl_url, has_3d_model, has_stl"
  - "base.html expõe {% block extra_js %} (linha 41)"
  - "tokens CSS: --radius-lg, --bg-soft, --border, --accent"
  - "sprite de ícones: #i-box"
provides:
  - "Viewer 3D interativo no detalhe (VIEW-01) via <model-viewer> 4.3.1"
  - "Fallback gracioso de imagem quando não há GLB (VIEW-02)"
  - "Botão 'Baixar STL' (download) quando há STL (VIEW-03)"
  - "Script CDN do model-viewer gated por has_3d_model (ES module, por página)"
  - "Regra CSS .detail-media model-viewer (aspect-ratio + tokens)"
affects:
  - "apps/catalog/templates/catalog/product_detail.html"
  - "static/css/theme.css"
tech-stack:
  added:
    - "@google/model-viewer 4.3.1 (CDN jsDelivr, ES module, sem build)"
  patterns:
    - "Script de terceiros carregado por página via {% block extra_js %}, gated por condição de template"
    - "Web component declarativo (só atributos, sem JS imperativo)"
    - "Estilo do container do viewer 100% por design tokens (tema claro/escuro automático)"
key-files:
  created: []
  modified:
    - "apps/catalog/templates/catalog/product_detail.html (viewer + fallback + botão STL + extra_js gated)"
    - "static/css/theme.css (.detail-media model-viewer)"
decisions:
  - "AR incluído (ar ar-modes ar-scale): custa 2 atributos, dá AR Android grátis do GLB, no-op gracioso no desktop/iOS"
  - "Versão fixada @4.3.1 (sem lockfile no projeto → reprodutibilidade); sem nomodule (4.x é só ES module)"
  - "Pan via camera-controls (ligado por padrão); NÃO adicionado disable-pan (pan é desejado)"
metrics:
  duration_min: 1
  tasks: 2
  files: 2
  completed: "2026-06-06"
---

# Phase 3 Plan 01: Viewer 3D no detalhe do produto — Summary

Viewer 3D interativo `<model-viewer>` (rotacionar/zoom/pan + AR Android) no detalhe do produto quando há GLB, com fallback gracioso para a imagem atual quando não há, botão "Baixar STL" quando há STL, e o script CDN do model-viewer 4.3.1 carregado por página (gated por `has_3d_model`) — tudo declarativo, sem JS imperativo e sem build.

## What Was Built

- **VIEW-01 — Viewer 3D:** `.detail-media` agora renderiza um `<model-viewer src="{{ product.model_3d_url }}" poster="{{ product.image_url }}" ...>` quando `product.has_3d_model`. Atributos: `camera-controls` (rotate+zoom+pan), `auto-rotate`, `touch-action="pan-y"`, `shadow-intensity="1"`, `loading="lazy"`, `reveal="auto"`, `alt`, e AR (`ar ar-modes="webxr scene-viewer quick-look" ar-scale="auto"`).
- **VIEW-02 — Fallback:** o ramo `{% else %}` preserva exatamente o comportamento anterior (monograma `thumb-mono` + `<img>` com `onerror` → picsum). Quando não há GLB o `<model-viewer>` nunca é emitido e o script CDN nem carrega.
- **VIEW-03 — Botão STL:** dentro do bloco de compra (`.mt-3`), logo após o if/else de `in_stock`, um `<a href="{{ product.stl_url }}" download class="btn btn-ghost">` com ícone `#i-box` e texto "Baixar STL", gated por `product.has_stl`.
- **Script CDN gated:** novo `{% block extra_js %}` no fim do template carrega `model-viewer@4.3.1` (jsDelivr, `type="module"`) só quando há GLB. base.html intacto.
- **CSS do container:** `.detail-media model-viewer` com `display:block`, `width:100%`, `aspect-ratio:1/1` (evita colapso/reflow — pitfall #2 da pesquisa), `border-radius/background/border` por token, e custom props themáveis (`--poster-color`, `--progress-bar-color: var(--accent)`, `--progress-mask`). Sem cores literais — segue o tema claro/escuro automaticamente.

## Verification

- Task 1 automated check: OK (todas as strings exigidas presentes; sem `nomodule`/`enable-pan`; fallback `thumb-mono`+`onerror` intacto).
- Task 2 automated check: OK (botão STL + CSS presentes; sem hex literais no bloco do viewer — só `var(--...)`).
- `python manage.py check --settings=config.settings.prod` → "System check identified no issues (0 silenced)", exit 0.

### Human Verification (pendente — coberto pela phase verification)

- Abrir um produto com GLB: rotacionar (arrastar), zoom (scroll/pinça), pan (botão direito ou Ctrl+arrastar / dois dedos); poster aparece enquanto carrega; sem layout shift; fundo do viewer acompanha tema claro/escuro.
- Produto sem GLB: monograma + imagem, sem quebra de layout.
- Clicar "Baixar STL" baixa o `.stl` (não navega).

## Deviations from Plan

None — plan executado exatamente como escrito. Nenhuma alteração em Python, base.html, ou nos arquivos do outro agente (queries/services/views/urls/navbar/models_3d).

## Notes / Out of Scope (registrado, não implementado)

- Serving de media em prod para GLB/STL grandes (CDN/object storage) continua fora do escopo (já em STATE.md blockers da Fase 3).
- iOS AR (USDZ) deferido para v2 — não há campo USDZ no `Product`; AR Android funciona do GLB.

## Self-Check: PASSED

All modified files and both task commits (d9a0ecb, 083b3be) verified present.
