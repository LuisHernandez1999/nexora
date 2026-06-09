---
phase: 02-funda-o-de-dados-3d
plan: 01
subsystem: catalog
tags: [model, migration, admin, mapper, 3d, filefield]
requires:
  - "Product model (apps/catalog/models.py)"
  - "MEDIA_URL/MEDIA_ROOT (já configurados, usados por image)"
provides:
  - "Product.model_3d (FileField GLB/glTF)"
  - "Product.model_stl (FileField STL)"
  - "Product.has_3d_model / Product.has_stl (propriedades)"
  - "ProductMapper.to_detail expõe model_3d_url, stl_url, has_3d_model, has_stl"
  - "Admin fieldset 'Modelos 3D' para upload de GLB/STL"
affects:
  - "Fase 3 (Visualizador 3D & Galeria) consome model_3d_url/stl_url/has_3d_model/has_stl do to_detail"
tech-stack:
  added: []
  patterns:
    - "FileExtensionValidator para validação de extensão de upload"
    - "Propriedades de negócio read-only no Product (padrão has_discount/in_stock)"
    - "to_detail estende to_dict via data.update (não duplica)"
key-files:
  created:
    - "apps/catalog/migrations/0003_product_model_3d_product_model_stl.py"
  modified:
    - "apps/catalog/models.py"
    - "apps/catalog/admin.py"
    - "apps/catalog/mappers.py"
decisions:
  - "Validação por extensão (FileExtensionValidator) é suficiente nesta fase; MIME/tamanho ficou deferido."
  - "Campos 3D expostos apenas em to_detail; to_dict (card/listagem) permanece inalterado."
  - "serializers.py não foi tocado (arquivo quebrado/não-wired; fora de escopo)."
metrics:
  duration_min: 1
  completed: "2026-06-06T12:58:44Z"
  tasks: 2
  files: 4
---

# Phase 2 Plan 01: Fundação de Dados 3D Summary

FileFields GLB e STL no `Product` com validação de extensão, propriedades `has_3d_model`/`has_stl`, migração 0003 aplicada, fieldset admin "Modelos 3D" e exposição de URLs/flags 3D no `ProductMapper.to_detail` para a Fase 3 consumir.

## What Was Built

- **Modelo (`apps/catalog/models.py`):** importado `FileExtensionValidator`; adicionados os FileFields `model_3d` (glb/gltf, `upload_to="products/models/"`) e `model_stl` (stl, `upload_to="products/stl/"`), ambos `blank=True`; adicionadas as propriedades de negócio `has_3d_model` e `has_stl`.
- **Migração (`0003_product_model_3d_product_model_stl.py`):** gerada com os dois `AddField`; aplicada limpa via `migrate`.
- **Admin (`apps/catalog/admin.py`):** novo fieldset `("Modelos 3D", {"fields": ("model_3d", "model_stl")})` inserido logo após "Visual". Ordem final: None → Preço → Visual → **Modelos 3D** → Estoque & métricas → Impressão 3D → Flags.
- **Mapper (`apps/catalog/mappers.py`):** `to_detail` agora expõe `model_3d_url`, `stl_url`, `has_3d_model`, `has_stl` dentro do `data.update({...})` existente. `to_dict` permanece inalterado.

## Tasks Completed

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Campos 3D (GLB/STL) + propriedades + migração 0003 | fc3d91c | apps/catalog/models.py, apps/catalog/migrations/0003_product_model_3d_product_model_stl.py |
| 2 | Admin fieldset "Modelos 3D" + mapper to_detail + aplicar migração | e60cba5 | apps/catalog/admin.py, apps/catalog/mappers.py |

## Verification

- `python manage.py makemigrations --check --dry-run catalog --settings=config.settings.prod` → exit 0 (sem mudanças pendentes), antes e depois do migrate.
- `python manage.py migrate catalog --settings=config.settings.prod` → aplicou 0003 sem erro (OK).
- Confirmado por grep que os 4 campos 3D estão em `to_detail` (linhas 63-66) e ausentes em `to_dict`.

Nota de ambiente: comandos `manage.py` rodados com `--settings=config.settings.prod` por causa do `debug_toolbar` ausente no dev (gotcha documentado). prod faz `from .base import *` (mesma config de DB/MEDIA para esta fase).

## Deviations from Plan

None - plan executed exactly as written.

## Requirements Satisfied

- **MODEL-01:** `Product.model_3d` (GLB/glTF) presente; migração aplica sem erro.
- **MODEL-02:** `Product.model_stl` (STL) presente; migração aplica sem erro.
- **MODEL-03:** Admin pode subir GLB/STL via fieldset "Modelos 3D"; arquivos expostos à camada de leitura (`to_detail`) para a Fase 3.

## Known Stubs

None. Os FileFields são `blank=True` por design (3D opcional por produto); o seed não popula GLB/STL reais (decisão LOCKED no CONTEXT — sem arquivos de exemplo). As URLs no mapper retornam `""` quando ausentes, comportamento esperado consumido pela Fase 3.

## Self-Check: PASSED

All created/modified files exist; both task commits (fc3d91c, e60cba5) found in git history.
