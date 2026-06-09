---
phase: 04
plan: 02
status: complete
completed: 2026-06-07
tasks_total: 2
tasks_done: 2
---

# Plan 04-02 — Camada Django do lithophane — SUMMARY

## O que foi construído
App `apps/lithophane/` no padrão de camadas:
- **`models.LithophaneDraft`** (`TimeStampedModel`): `image`, `model_glb`, `model_stl` (FileField + FileExtensionValidator), `format` (4 escolhas placa/luminaria/curvo/cubo), `size`, `thickness`, `user`/`session_key`. Migration `0001_initial` aplicada.
- **`services.LithophaneService.gerar()`** — única escrita: monta `EspecsLitho`, chama `LithophaneGenerator.gerar` (Plan 01), salva foto+GLB+STL via `ContentFile`/`save=False` num único `draft.save()`.
- **`queries.LithophaneQuery`** — `by_id` + `drafts_by_ids` (consumido pelo Plan 03).
- **`mappers.LithophaneMapper.to_dict`** — `draft_id`/`format`/`glb_url`/`stl_url`/`image_url` (JSON do endpoint, Plan 04).
- **`admin`** — equipe vê foto + specs para fechar o orçamento.
- App registrado em `INSTALLED_APPS`.

## Verificação
- `manage.py check` limpo; `makemigrations --check` → "No changes detected".
- **Smoke test end-to-end** (`test_service.py`, 2/2 OK): `LithophaneService.gerar` persiste o draft com os 3 arquivos; `LithophaneQuery`/`LithophaneMapper` corretos.

## key-files
### created
- `apps/lithophane/{apps,models,queries,mappers,services,admin}.py`
- `apps/lithophane/migrations/0001_initial.py`
- `apps/lithophane/tests/test_service.py`
### modified
- `config/settings/base.py` — `apps.lithophane` em LOCAL_APPS

## Deviation
A foto é salva via `io.BytesIO` + `ContentFile(buf.getvalue())` (o snippet do plano usava `ContentFile(b"", ...)` + `.save()` direto, que não é gravável). Mesmos critérios de aceite mantidos (3× ContentFile, 3× save=False).

## Contrato pronto para Plans 03/04
`LithophaneService.gerar(imagem_pil, *, formato, largura_mm, espessura_mm, user=None, session_key="") -> LithophaneDraft`
`LithophaneQuery.drafts_by_ids(ids) -> list[LithophaneDraft]`
`LithophaneMapper.to_dict(draft) -> dict`
