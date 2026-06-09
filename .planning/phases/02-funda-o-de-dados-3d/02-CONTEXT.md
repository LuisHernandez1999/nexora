# Phase 2: Fundação de Dados 3D - Context

**Gathered:** 2026-06-06
**Status:** Ready for planning
**Source:** User decisions (locked)

<domain>
## Phase Boundary

Esta fase dá ao `Product` a capacidade de **armazenar** dois arquivos 3D — um **GLB** (exibição no viewer) e um **STL** (download imprimível) — e permite que o admin os suba. Também expõe esses arquivos às camadas de leitura (mapper) para a Fase 3 consumir. NÃO inclui o viewer/galeria/template (Fase 3).

Cobre: MODEL-01, MODEL-02, MODEL-03.
</domain>

<decisions>
## Implementation Decisions (LOCKED)

### Campos no modelo `Product` (`apps/catalog/models.py`)
- **MODEL-01 (GLB):** adicionar
  ```python
  model_3d = models.FileField(
      "modelo 3D (GLB/glTF)", upload_to="products/models/", blank=True,
      validators=[FileExtensionValidator(allowed_extensions=["glb", "gltf"])],
      help_text="Arquivo .glb ou .gltf exibido no visualizador 3D.",
  )
  ```
- **MODEL-02 (STL):** adicionar
  ```python
  model_stl = models.FileField(
      "arquivo STL (impressão)", upload_to="products/stl/", blank=True,
      validators=[FileExtensionValidator(allowed_extensions=["stl"])],
      help_text="Arquivo .stl imprimível, disponibilizado para download.",
  )
  ```
- Importar `from django.core.validators import FileExtensionValidator`.
- Adicionar propriedades de negócio (sem efeito colateral), junto das existentes (`has_discount`, `in_stock`, etc.):
  ```python
  @property
  def has_3d_model(self) -> bool:
      return bool(self.model_3d)

  @property
  def has_stl(self) -> bool:
      return bool(self.model_stl)
  ```

### Migração
- Gerar migração `apps/catalog/migrations/0003_*` com os dois novos `FileField` (ambos `blank=True`, então sem prompt de default). Deve aplicar limpa (`makemigrations` + `migrate`).

### Admin (`apps/catalog/admin.py`) — MODEL-03
- Adicionar um fieldset novo "Modelos 3D" ao `ProductAdmin.fieldsets`, logo após "Visual":
  ```python
  ("Modelos 3D", {"fields": ("model_3d", "model_stl")}),
  ```
- Isso permite o admin subir GLB e STL por produto.

### Exposição às camadas de leitura (para a Fase 3 consumir)
- `apps/catalog/mappers.py` → `ProductMapper.to_detail`: adicionar ao dict:
  ```python
  "model_3d_url": instance.model_3d.url if instance.model_3d else "",
  "stl_url": instance.model_stl.url if instance.model_stl else "",
  "has_3d_model": instance.has_3d_model,
  "has_stl": instance.has_stl,
  ```
  (Apenas em `to_detail` — a listagem/card não precisa dos arquivos.)
- Se houver `apps/catalog/serializers.py` com um ProductSerializer de detalhe, expor os mesmos campos lá também (opcional/se trivial; não bloqueante).

### Media
- Os uploads usam `MEDIA_ROOT`/`MEDIA_URL` já existentes (o `image` FileField já usa media). Garantir que `MEDIA_URL`/`MEDIA_ROOT` estão configurados e, em dev, servidos (em `config/urls.py` via `static()` quando `DEBUG`). Se já estiver para `image`, nada a fazer. NÃO resolver serving de prod aqui (Fase 3 / fora de escopo).

### Seed (opcional, não bloqueante)
- Pode deixar os campos 3D vazios no `seed_demo` (não temos GLB/STL reais de exemplo). Não inventar URLs externas para FileField.
</decisions>

<canonical_refs>
## Canonical References

### Arquivos a tocar
- `apps/catalog/models.py` — modelo `Product` (FileFields + propriedades). Validators import.
- `apps/catalog/admin.py` — `ProductAdmin.fieldsets` (fieldset "Modelos 3D").
- `apps/catalog/mappers.py` — `ProductMapper.to_detail` (expor urls + flags).
- `apps/catalog/migrations/` — nova migração 0003.
- `config/settings/base.py` / `config/urls.py` — confirmar MEDIA config (já usado por `image`).

### Convenções
- `.planning/codebase/CONVENTIONS.md` — camadas (models/mappers/serializers), pt-br verbose_name/help_text.
- Modelo segue `TimeStampedModel`, QuerySet `ProductQuerySet`. Não quebrar `with_relations`/`active`.
</canonical_refs>

<specifics>
## Specific Ideas
- GLB é o formato de exibição (Fase 3 usa `<model-viewer>`); STL é o download imprimível. Ambos opcionais por produto (`blank=True`).
- Validação por extensão via `FileExtensionValidator` é suficiente nesta fase.
</specifics>

<deferred>
## Deferred Ideas
- Validação de conteúdo/tamanho do arquivo (MIME real, limite de MB) — pode vir depois.
- Conversão STL→GLB automática — v2.
- Serving de media em produção para arquivos grandes — Fase 3 / infra.
</deferred>

---

*Phase: 02-funda-o-de-dados-3d*
*Context gathered: 2026-06-06 (locked user decisions)*
