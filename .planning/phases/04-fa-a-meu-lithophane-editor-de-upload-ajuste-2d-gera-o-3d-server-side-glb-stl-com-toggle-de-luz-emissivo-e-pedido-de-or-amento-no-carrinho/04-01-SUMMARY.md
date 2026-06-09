---
phase: 04
plan: 01
status: complete
completed: 2026-06-07
tasks_total: 2
tasks_done: 2
---

# Plan 04-01 — Motor de geração (generation.py) — SUMMARY

## O que foi construído
Motor isolado `apps/lithophane/generation.py` (`LithophaneGenerator.gerar(PIL.Image, EspecsLitho) -> (glb_bytes, stl_bytes)`), via TDD. Sem dependência de Django — boundary swappável no estilo `apps/orders/payments.py`.

Pipeline: foto → grayscale → resize (maior lado = `resolucao_px`, LANCZOS) → normaliza → **inverte** (claro=fino, escuro=grosso) → heightmap em mm → malha sólida watertight (topo + base + 4 paredes, vértices compartilhados) → `fix_normals`/`fill_holes` → GLB com `PBRMaterial(emissiveTexture=foto)` + STL.

## Verificação
- `python manage.py test apps.lithophane.tests.test_generation --settings=config.settings.prod` → **6/6 OK**.
- Resolvidas as Open Questions do RESEARCH: malha **watertight** confirmada (GLB e STL), **emissiveTexture** embutida no GLB, **relevo invertido** confirmado, GLB **< 5 MB**.

## key-files
### created
- `apps/lithophane/generation.py` — motor (LithophaneGenerator, EspecsLitho)
- `apps/lithophane/tests/test_generation.py` — 6 testes de bancada
- `apps/lithophane/__init__.py`, `apps/lithophane/tests/__init__.py`
### modified
- `requirements.txt` — `numpy==2.2.6`, `trimesh==4.12.2`

## Contrato exposto (consumido pelo Plan 02)
`EspecsLitho(largura_mm, espessura_min_mm, espessura_max_mm, resolucao_px, formato: "placa"|"luminaria")`
`LithophaneGenerator.gerar(imagem_pil, specs) -> (glb_bytes, stl_bytes)`

## Deviations
Nenhuma. Specs padrão de teste: largura 100mm, esp. 0.8–3.0mm, resolução 200px.
