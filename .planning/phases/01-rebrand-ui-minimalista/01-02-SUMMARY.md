---
phase: 01-rebrand-ui-minimalista
plan: 02
subsystem: ui-minimalismo
tags: [minimalismo, css, whitespace, grad-text, cor-literal, verde]
requires:
  - "Tokens de cor verde Luigi em :root (dark) e [data-theme=light] (Plan 01)"
provides:
  - ".grad-text em verde sólido (sem gradiente roxo nem animação)"
  - "Respiro vertical maior nas seções (.section) e na home"
  - "Overlay do hero-banner suavizado para clima minimalista"
  - "Cores literais azuis (rgba(59,130,246,...)) convertidas para verde em todas as superfícies de mídia/estados info"
affects:
  - static/css/theme.css
  - apps/core/templates/core/home.html
tech-stack:
  added: []
  patterns:
    - "Minimalismo via tokens/classes existentes (sem reescrita de CSS nem mudança de estrutura)"
    - "Realce de palavra (.grad-text) em verde sólido var(--accent)"
key-files:
  created:
    - .planning/phases/01-rebrand-ui-minimalista/01-02-SUMMARY.md
  modified:
    - static/css/theme.css
    - apps/core/templates/core/home.html
decisions:
  - "Purple #a78bfa de .status-badge.accent (linha ~427) mantido — não é azul de acento nem está no escopo do plano (só .grad-text e os 5 rgba azuis foram tratados)."
  - "product_list.html e product_detail.html não foram modificados: já herdam o tratamento de cor/spacing via classes e tokens; minimalismo deles vem do CSS (.section, .detail-media verde)."
  - "Checkpoint visual rodado com python manage.py check via --settings=config.settings.prod (debug_toolbar ausente no venv dev — pré-existente, ver 01-01-SUMMARY)."
metrics:
  duration: 2
  completed: 2026-06-05
requirements: [UI-01, UI-02]
---

# Phase 1 Plan 02: UI Minimalista (home + catálogo + detalhe) Summary

Tratamento minimalista aplicado via tokens/classes existentes: `.grad-text` virou verde sólido sem animação, seções ganharam mais whitespace, overlay do hero foi suavizado, e as cinco cores azuis LITERAIS remanescentes (`rgba(59,130,246,...)`) foram convertidas para verde — deixando home, catálogo e detalhe coerentes com a identidade L3D Labz.

## What Was Built

**Task 1 — Minimalismo na home + .grad-text verde** (commit `a683e61`)
- `static/css/theme.css`:
  - `.grad-text` agora é `color: var(--accent)` com `background:none` e `background-clip:initial` — removidos o gradiente azul→roxo (`#a78bfa`) e a `animation: grad-shift`.
  - `.section` com respiro vertical aumentado: `clamp(2.5rem,4vw,4rem)` → `clamp(3rem,5vw,5.5rem)`.
  - `.hero-banner .bg::after`: overlay escuro suavizado (opacidades `.97/.86/.42/.25` → `.85/.6/.32/.18`) para um clima mais arejado sem perder legibilidade do texto branco do hero.
- `apps/core/templates/core/home.html`: o `style="padding-top:0"` das seções coladas (benefícios, categorias, carrossel de promoções, destaques, lançamentos) trocado por `padding-top:1rem` para dar whitespace entre os blocos. Todas as seções essenciais preservadas (hero, benefícios, categorias, promoções, destaques, lançamentos, newsletter).

**Task 2 — Catálogo/detalhe coerentes + remoção de todo azul literal** (commit `274ff35`)
- `static/css/theme.css`: as CINCO ocorrências literais de `rgba(59,130,246,...)` trocadas por `rgba(47,168,79,...)` preservando o alpha:
  1. `.hero-visual` background radial → `.32`
  2. `.alert-info` background → `.1`
  3. `.detail-media` background radial → `.25`
  4. `.status-badge.info` background `.12` + border `.3`
  5. `.toast.info .ti` background → `.14`
- `product_list.html` / `product_detail.html`: sem mudança estrutural — já herdam cor/spacing via classes (`.section`, `.detail-media`, `.product-grid`, `.search-hero`) e tokens verdes do Plan 01.

## Key Implementation Details

- O minimalismo do catálogo e do detalhe é entregue inteiramente via CSS compartilhado (`.section` mais arejado, `.detail-media` com fundo verde, botões primários verdes via tokens) — coerente com a diretriz "refino via tokens/classes existentes, sem redesenho funcional".
- O override v3 (`--radius:0px`, botões outline) foi mantido propositalmente: cantos retos + outline já são minimalistas, e a cor do outline vem dos tokens verdes do Plan 01.

## Deviations from Plan

### Auto-fixed Issues

None - plan executado exatamente como escrito. As partes opcionais (suavizar overlay do hero — item E da Task 1) foram aplicadas por melhorarem o respiro sem prejudicar legibilidade.

### Notes

- `#a78bfa` permanece APENAS em `.status-badge.accent` (linha ~427), que é um badge roxo de status distinto — não é azul de acento e não está no escopo (o plano só exigia remover `#a78bfa` de `.grad-text`). Não tocado.
- `python manage.py check` com settings dev continua falhando por `ModuleNotFoundError: debug_toolbar` (pré-existente; ver 01-01-SUMMARY). Verificação rodada com `--settings=config.settings.prod`: 0 issues.

## Verification

- Task 1 automated verify: PASS (`.grad-text` presente, `color: var(--accent)` presente, home contém `newsletter`/`benefits`/`cat-grid`).
- Task 2 automated verify: PASS (nenhum `rgba(59,130,246`, nenhum `#5b8def`/`#2f68d8`/`#3B82F6`, `rgba(47,168,79` presente).
- `python manage.py check --settings=config.settings.prod`: System check identified no issues (0 silenced).
- grep final em theme.css: zero azul de acento/literal remanescente.

## Requirements Satisfied

- UI-01: home minimalista — `.grad-text` verde sólido sem animação, mais whitespace entre seções, overlay do hero suavizado, todas as seções essenciais preservadas, botões primários verdes (tokens).
- UI-02: catálogo e detalhe com o mesmo tratamento de cor/spacing (sem redesenho funcional); todos os azuis literais convertidos para verde nas superfícies de mídia e estados info.

## Checkpoint Pendente

Task 3 é um checkpoint `human-verify` (gate blocking). O código está completo e commitado; falta a confirmação visual do usuário (ver passos no retorno do executor). `auto_advance` está desligado, então o orquestrador apresenta os passos e aguarda "approved".

## Self-Check: PASSED
