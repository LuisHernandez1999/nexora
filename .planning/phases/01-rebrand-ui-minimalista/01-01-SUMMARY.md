---
phase: 01-rebrand-ui-minimalista
plan: 01
subsystem: ui-branding
tags: [rebrand, theme, css-tokens, svg, localStorage]
requires: []
provides:
  - "Dict SITE com a marca L3D Labz (name/tagline/accent verde)"
  - "Tokens de cor verde Luigi em :root (dark) e [data-theme=light]"
  - "Símbolo SVG do emblema da marca #i-l3d-mark"
  - "Chave de tema localStorage migrada para l3d-theme (boot + escrita)"
  - "Wordmark L3D Labz no navbar/footer/login/register"
affects:
  - config/settings/base.py
  - static/css/theme.css
  - apps/core/templates/base.html
  - static/js/app.js
  - apps/core/templates/core/partials/icons.html
  - apps/core/templates/core/partials/navbar.html
  - apps/core/templates/core/partials/footer.html
  - apps/accounts/templates/accounts/login.html
  - apps/accounts/templates/accounts/register.html
tech-stack:
  added: []
  patterns:
    - "Rebrand via tokens CSS + dict SITE (sem reescrita)"
    - "Wordmark hand-split em markup (<b>L3D</b> Labz herda --accent-2)"
    - "Emblema SVG inline no sprite #i-l3d-mark referenciado via <use href>"
key-files:
  created: []
  modified:
    - config/settings/base.py
    - static/css/theme.css
    - apps/core/templates/base.html
    - static/js/app.js
    - apps/core/templates/core/partials/icons.html
    - apps/core/templates/core/partials/navbar.html
    - apps/core/templates/core/partials/footer.html
    - apps/accounts/templates/accounts/login.html
    - apps/accounts/templates/accounts/register.html
    - apps/core/templates/core/home.html
    - apps/promotions/templates/promotions/list.html
    - apps/core/templates/core/partials/field.html
    - apps/catalog/management/commands/seed_demo.py
decisions:
  - "Default de tema mudou para light (data-theme=light) refletindo a estética minimalista; boot script ainda sobrescreve com a preferência salva."
  - "Símbolo #i-koala mantido em icons.html (não referenciado) para não quebrar referências esquecidas."
  - "Verificação de check rodada com --settings=config.settings.prod por ausência de debug_toolbar no venv dev (pré-existente)."
metrics:
  duration: 2
  completed: 2026-06-05
requirements: [BRAND-01, BRAND-02, BRAND-03, THEME-01, THEME-02, THEME-03]
---

# Phase 1 Plan 01: Rebrand L3D Labz (marca, paleta Luigi, emblema, tema) Summary

Identidade visual L3D Labz aplicada via tokens CSS verdes (dark+light), emblema "L" em SVG inline e wordmark "L3D Labz", com a chave de tema localStorage migrada atomicamente para `l3d-theme` e default light.

## What Was Built

**Task 1 — Paleta Luigi + migração de chave de tema** (commit `c57b085`)
- `static/css/theme.css`: tokens de acento azul→verde nos DOIS blocos. `:root` (dark): `--accent #2FA84F`, `--accent-2 #43C266`, `--accent-strong #1E8C3E`, `--accent-soft #13251A`, `--accent-glow rgba(47,168,79,0.26)`, `--danger #E23B3B`, novo `--accent-blue #2BA6E0`; radial-gradients do body recoloridos para verde. `[data-theme="light"]`: superfícies light/clean (`--bg #FFFFFF`, `--bg-soft #F6F8F5`, etc.), texto verde-frio, `--accent #2FA84F`, `--accent-2/--accent-strong #1E8C3E` (verde-escuro p/ contraste AA em texto/links), `--accent-soft #E7F6EC`, `--accent-blue #2BA6E0`; gradientes do body recoloridos. Comentário-cabeçalho atualizado.
- `config/settings/base.py`: dict `SITE` → name "L3D Labz", tagline "Impressão 3D com acabamento de laboratório.", accent "#2FA84F".
- `apps/core/templates/base.html`: boot script lê `l3d-theme`; `<html data-theme="light">`.
- `static/js/app.js`: escreve preferência em `l3d-theme`; comentário-cabeçalho atualizado.

**Task 2 — Emblema "L", wordmark e remoção de "Nexora" visível** (commit `89319cc`)
- `apps/core/templates/core/partials/icons.html`: novo `<symbol id="i-l3d-mark">` (círculo verde #2FA84F + círculo branco + "L" #1E8C3E). `#i-koala` mantido (não referenciado).
- `navbar.html`/`footer.html`/`login.html`/`register.html`: `<use href="#i-l3d-mark">` + `<span class="brand-word"><b>L3D</b> Labz</span>`; navbar `aria-label="L3D Labz — início"`; footer copyright "© 2026 L3D Labz".
- `home.html`: "Comunidade L3D Labz". `promotions/list.html`: "Ofertas L3D Labz". `field.html` e `seed_demo.py`: strings de marca atualizadas.

## Key Implementation Details

- O "L3D" dentro de `<b>` herda `--accent-2` pela regra CSS existente `.brand-word b`, então o destaque de cor do wordmark é automático nos dois temas.
- Migração da chave de tema feita atomicamente nos dois arquivos (boot em base.html + escrita em app.js) — persistência intacta. Default light, com override pela preferência salva.
- Escopo de "Nexora": apenas strings VISÍVEIS ao cliente. Identificadores internos Python (view classes `NexoraLoginView`, `KEY_PREFIX`/LocMem `nexora-locmem`, PIX merchant, seeds picsum, DB names) NÃO foram renomeados — fora do escopo desta fase, conforme plano.

## Deviations from Plan

### Auto-fixed Issues

None - plan executado exatamente como escrito.

### Notes

- `python manage.py check` com settings dev falha por `ModuleNotFoundError: debug_toolbar` (dependência ausente no venv local, declarada em `dev.py`). Pré-existente e não relacionado ao rebrand. Verificação rodada com `--settings=config.settings.prod` (carrega o `base.py` modificado) — `System check identified no issues`. Registrado em `deferred-items.md`.

## Verification

- Verificação automatizada das duas tasks: PASS (tokens verdes presentes, `l3d-theme` em ambos os arquivos, sem `nexora-theme`, `#i-l3d-mark` presente, sem "Nexora"/"i-koala"/"nex<b>ora" em templates cliente-visíveis).
- `python manage.py check --settings=config.settings.prod`: 0 issues.

## Requirements Satisfied

- BRAND-01: nenhuma string "Nexora" visível em navbar/footer/home/promoções/login/register.
- BRAND-02: navbar/login/register exibem wordmark "L3D Labz" + emblema #i-l3d-mark.
- BRAND-03: chave de tema migrada para `l3d-theme` em base.html e app.js; persistência intacta.
- THEME-01/02: paleta verde Luigi em :root (dark) e [data-theme=light] com #2FA84F.
- THEME-03: toggle alterna e persiste (lógica existente preservada, chave migrada).

## Notes for Next Plan

- Plan 02 trata o minimalismo de forma/spacing e o override v3 (`--radius:0px`, botões outline) — deliberadamente NÃO tocado aqui (só cores).
- `#i-koala` e os gradientes do mascote permanecem em icons.html caso o Plan 02 queira removê-los como limpeza.

## Self-Check: PASSED

Todos os arquivos modificados existem e os dois commits (c57b085, 89319cc) estão no histórico.
