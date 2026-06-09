# Phase 4: Faça meu Lithophane — Research

**Researched:** 2026-06-07
**Domain:** Geração 3D server-side (Python/trimesh), editor canvas vanilla JS, toggle emissivo model-viewer, integração carrinho/pedido sem preço
**Confidence:** MEDIUM-HIGH (trimesh PBR export verificado via docs oficiais; algoritmo heightmap verificado via repositórios públicos; model-viewer API verificada via api.ts e discussões oficiais)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Geração **server-side em Python** (não client-side)
- Stack: `Pillow` + `numpy` + `trimesh` (exporta GLB e STL)
- Pipeline: imagem → escala de cinza → heightmap reduzido (~300px maior lado) → grade de vértices (relevo invertido: claro=fino, escuro=grosso) → malha → GLB + STL
- Motor isolado e swappable em `generation.py` (espelha `apps/orders/payments.py`)
- Toggle "Com luz / Sem luz": GLB carrega `emissiveTexture` = a foto; JS liga/desliga via API model-viewer (`material.emissiveTexture`/`emissiveStrength` + ajuste exposure)
- Editor vanilla JS + `<canvas>`: crop/escala/brilho/inverter; sem Three.js ou framework pesado
- Ao clicar "Gerar 3D": POST (dataURL + specs) → service gera → canvas troca por `<model-viewer>` CDN `@google/model-viewer@4.3.1`
- `LithophaneDraft(TimeStampedModel)` com campos: `image`, `model_glb`, `model_stl`, `format` (TextChoices placa/luminaria/curvo/cubo), `size`, `thickness`, `user`/`session_key`
- Carrinho referencia o draft (`draft_id`); preço = `None`/"a combinar"
- Checkout cria `Order` com novo status `orcamento`, total pendente, **pula `PaymentService`**
- Formatos Fase 1: placa plana + luminária (mesma malha; luminária = +base/flag)
- Rota `/lithophane/`, link no navbar, slogan "Onde memórias preciosas ganham forma na luz", tokens Luigi + tema claro/escuro, copy pt-br

### Claude's Discretion
- Detalhes do algoritmo de heightmap→malha (densidade, base sólida, espessura mín/máx)
- Nomes internos de funções
- Estrutura exata dos endpoints
- Como exatamente o status `orcamento` se integra ao fluxo de checkout (desde que não capture pagamento)

### Deferred Ideas (OUT OF SCOPE)
- Formato **curvo** (lampshade) — curvatura na malha
- Formato **cubo / caixa de luz** — 4 uploads, 4 faces
- Precificação automática por dimensão/volume
- Endurecimento do serving de media 3D em prod (CDN/object storage)
</user_constraints>

---

## Summary

A Fase 4 constrói um pipeline end-to-end novo: o cliente edita uma foto no browser (canvas puro), o servidor gera uma malha 3D lithophane (GLB + STL) via Python, e o model-viewer exibe com toggle de luz emissivo. O fluxo termina em pedido de orçamento sem captura de pagamento.

As três partes mais novas/arriscadas são: (1) a geração da malha em Python com trimesh — algoritmo bem documentado em repositórios públicos, mas a montagem watertight + UV + emissiveTexture no GLB tem nuances; (2) a extensão do carrinho/checkout para tolerar item sem preço — requer cirurgia precisa em `SessionCart`, `CartService`, `OrderService` e `Order.Status`; (3) o toggle emissivo no model-viewer — a API `setEmissiveFactor` / `setEmissiveStrength` existe e foi verificada, mas a interação entre `emissiveStrength` e `exposure` do viewer precisa de ajuste empírico para o efeito "foto acende".

**Recomendação primária:** Começar por `generation.py` com um teste de bancada (foto real → GLB → abrir no Babylon Sandbox para verificar emissivo) antes de plugar na UI. Isso desbloqueia o risco mais alto cedo.

---

## Standard Stack

### Core
| Biblioteca | Versão | Finalidade | Por que padrão |
|------------|--------|-----------|----------------|
| Pillow | 11.2.1 (já em requirements.txt) | Carregamento, resize, conversão grayscale, PIL.Image para texturas | Já dependência; `PBRMaterial` exige PIL.Image para texturas |
| numpy | ~2.x (última estável) | Array de vértices/faces/UVs vectorizado — performance em grid 300×300 | Única hard-dep do trimesh; operações de grade em numpy são 100–1000× mais rápidas que loops Python |
| trimesh | 4.12.2 (atual no PyPI, Mai 2026) | Construção da Trimesh a partir de arrays, export GLB com PBRMaterial, export STL | Biblioteca padrão para manipulação/export de malhas em Python; suporta emissiveTexture nativamente via PBRMaterial |

### Sem novas dependências front-end
O editor usa `<canvas>` nativo + APIs `CanvasRenderingContext2D.filter` (CSS filters para brightness/contrast) e `getImageData`/`putImageData` para inversão de pixel. Nenhuma lib JS nova.

**Installation:**
```bash
pip install numpy trimesh
```

`Pillow` já está em `requirements.txt`. Adicionar ao `requirements.txt`:
```
numpy==2.2.6
trimesh==4.12.2
```

**Verificação de versões (executado em 2026-06-07):**
- `trimesh` 4.12.2 publicado Mai 2026 — confirmado via PyPI
- `numpy` 2.2.6 — versão estável atual para Python 3.13
- Pillow 11.2.1 — já fixado em requirements.txt

### Alternativas consideradas e descartadas (por decisão do CONTEXT.md)
| Em vez de | Poderia usar | Por quê descartado |
|-----------|--------------|-------------------|
| trimesh | numpy-stl (só STL) + pygltflib (GLB manual) | Mais trabalho, sem PBRMaterial nativo — trimesh cobre os dois formatos |
| trimesh | open3d | 50 MB+ de dependências; overkill |

---

## Architecture Patterns

### Estrutura do novo app

```
apps/lithophane/
├── __init__.py
├── apps.py               # AppConfig com app_name = 'lithophane'
├── models.py             # LithophaneDraft(TimeStampedModel)
├── queries.py            # LithophaneQuery — leituras ORM/cache
├── services.py           # LithophaneService.generate() — única escrita
├── generation.py         # MOTOR ISOLADO: foto → GLB + STL (como payments.py)
├── mappers.py            # LithophaneMapper.to_dict() / to_detail()
├── views.py              # editor view + endpoint POST /gerar/
├── urls.py               # app_name = 'lithophane'
├── admin.py
└── templates/
    └── lithophane/
        ├── editor.html
        └── partials/
            └── viewer_section.html
static/
└── js/
    └── lithophane-editor.js   # IIFE, canvas editor + fetch
```

### Pattern 1: Motor de geração isolado (espelha payments.py)

`generation.py` é um boundary swappable — nenhuma view ou service importa trimesh diretamente. Isso permite trocar o algoritmo sem tocar nas camadas superiores.

```python
# apps/lithophane/generation.py
"""Motor de geração de lithophane — isolado e swappável.

Segue o padrão de apps/orders/payments.py: camada única de responsabilidade,
sem dependências de HTTP ou ORM. Retorna bytes prontos para FileField.save().
"""
from __future__ import annotations
import io
from dataclasses import dataclass
from typing import Literal

import numpy as np
import trimesh
import trimesh.visual.material
from PIL import Image

FormatoLitho = Literal["placa", "luminaria"]


@dataclass
class EspecsLitho:
    largura_mm: float       # ex: 100.0
    altura_mm: float        # calculado pela proporção da imagem
    espessura_min_mm: float  # ex: 0.8  (partes claras)
    espessura_max_mm: float  # ex: 3.0  (partes escuras)
    resolucao_px: int       # ex: 300  (maior lado do heightmap)
    formato: FormatoLitho


class LithophaneGenerator:
    @staticmethod
    def gerar(imagem_pil: Image.Image, specs: EspecsLitho) -> tuple[bytes, bytes]:
        """Recebe PIL.Image ajustada + specs, devolve (glb_bytes, stl_bytes)."""
        heightmap = LithophaneGenerator._imagem_para_heightmap(imagem_pil, specs)
        mesh = LithophaneGenerator._heightmap_para_mesh(heightmap, specs)
        glb_bytes = LithophaneGenerator._exportar_glb(mesh, imagem_pil)
        stl_bytes = mesh.export(file_type="stl")
        return glb_bytes, stl_bytes
```

### Pattern 2: Algoritmo heightmap → malha watertight

O algoritmo correto para lithophane usa relevo **invertido**: pixel branco (255) = fino = `espessura_min`; pixel preto (0) = grosso = `espessura_max`. Isso faz a luz retroiluminada passar mais pelo branco (fino) e menos pelo preto (grosso).

```python
# Dentro de LithophaneGenerator
@staticmethod
def _imagem_para_heightmap(img: Image.Image, specs: EspecsLitho) -> np.ndarray:
    # 1. Converter para grayscale
    gray = img.convert("L")
    # 2. Redimensionar para resolução controlada (performance)
    w, h = gray.size
    if w >= h:
        new_w = specs.resolucao_px
        new_h = int(h * specs.resolucao_px / w)
    else:
        new_h = specs.resolucao_px
        new_w = int(w * specs.resolucao_px / h)
    gray = gray.resize((new_w, new_h), Image.LANCZOS)
    # 3. Normalizar 0-1 e INVERTER (claro=fino, escuro=grosso)
    arr = np.array(gray, dtype=np.float32) / 255.0
    arr = 1.0 - arr  # inversão: 0=fino(claro), 1=grosso(escuro)
    # 4. Mapear para faixa de espessura em mm
    return arr * (specs.espessura_max_mm - specs.espessura_min_mm) + specs.espessura_min_mm

@staticmethod
def _heightmap_para_mesh(hmap: np.ndarray, specs: EspecsLitho) -> trimesh.Trimesh:
    """Monta malha watertight: face frontal (relevo) + base plana + 4 paredes laterais."""
    rows, cols = hmap.shape  # (H, W) em pixels → (Y, X)

    # Escala pixel → mm
    scale_x = specs.largura_mm / (cols - 1)
    scale_y = (specs.largura_mm * rows / cols) / (rows - 1)  # mantém proporção

    # --- FACE FRONTAL (grade de vértices com altura) ---
    # Gera arrays X, Y vectorizados
    xs = np.arange(cols, dtype=np.float32) * scale_x         # (cols,)
    ys = np.arange(rows, dtype=np.float32) * scale_y         # (rows,)
    XX, YY = np.meshgrid(xs, ys)                              # (rows, cols) cada

    # Vértices da face frontal: shape (rows*cols, 3)
    verts_front = np.column_stack([
        XX.ravel(),
        YY.ravel(),
        hmap.ravel(),
    ])

    # Faces da face frontal: 2 triângulos por célula (quad split)
    # Índice do vértice [r, c] = r*cols + c
    r = np.arange(rows - 1)
    c = np.arange(cols - 1)
    RR, CC = np.meshgrid(r, c, indexing="ij")  # (rows-1, cols-1)
    idx = (RR * cols + CC).ravel()
    # Triângulo 1: (i, i+1, i+cols+1) — sentido anti-horário (normal aponta +Z)
    tri1 = np.column_stack([idx, idx + 1, idx + cols + 1])
    # Triângulo 2: (i, i+cols+1, i+cols)
    tri2 = np.column_stack([idx, idx + cols + 1, idx + cols])
    faces_front = np.vstack([tri1, tri2])

    # UVs da face frontal: normalizar posição (cols-1, rows-1) para 0-1
    uv_front = np.column_stack([
        XX.ravel() / (scale_x * (cols - 1)),
        1.0 - YY.ravel() / (scale_y * (rows - 1)),  # Y invertido (OpenGL)
    ]).astype(np.float32)

    # --- BASE PLANA (z=0) ---
    verts_base = verts_front.copy()
    verts_base[:, 2] = 0.0
    base_offset = len(verts_front)
    # Faces base: sentido oposto (normais apontam -Z)
    faces_base = faces_front[:, ::-1] + base_offset

    # --- PAREDES LATERAIS (4 bordas) ---
    # Cada parede conecta uma aresta da face frontal à aresta correspondente da base
    wall_verts = []
    wall_faces = []
    wv_offset = 2 * len(verts_front)

    def _adicionar_parede(borda_front_ids):
        nonlocal wv_offset
        n = len(borda_front_ids)
        for i in range(n - 1):
            a_f = borda_front_ids[i]
            b_f = borda_front_ids[i + 1]
            a_b = a_f + base_offset  # vértice correspondente na base
            b_b = b_f + base_offset
            # Quatro vértices de parede (duplicados para normais corretas)
            local = [
                verts_front[a_f], verts_base[a_f - base_offset + base_offset],
                verts_base[b_f - base_offset + base_offset], verts_front[b_f],
            ]
            # ... simplificado — na implementação real usa os índices diretos
            lo = wv_offset + len(wall_verts) * 4
            wall_faces.extend([[lo, lo+1, lo+2], [lo, lo+2, lo+3]])
            wall_verts.extend(local)
        wv_offset += (n - 1) * 4

    # bordas: topo (r=0), baixo (r=rows-1), esquerda (c=0), direita (c=cols-1)
    _adicionar_parede(np.arange(cols))                          # topo
    _adicionar_parede(np.arange(cols) + (rows-1)*cols)          # baixo
    _adicionar_parede(np.arange(rows) * cols)                   # esquerda
    _adicionar_parede(np.arange(rows) * cols + (cols-1))        # direita

    # Montar mesh combinada
    all_verts = np.vstack([verts_front, verts_base])
    all_faces = np.vstack([faces_front, faces_base])
    all_uvs   = np.vstack([uv_front, uv_front])  # base reutiliza UVs (não importa)

    if wall_verts:
        all_verts = np.vstack([all_verts, np.array(wall_verts)])
        all_faces = np.vstack([all_faces, np.array(wall_faces)])
        # UVs das paredes: zeros (textura irrelevante na lateral)
        all_uvs = np.vstack([all_uvs, np.zeros((len(wall_verts), 2), dtype=np.float32)])

    material = trimesh.visual.material.PBRMaterial(
        baseColorFactor=np.array([1.0, 1.0, 1.0, 1.0]),
        metallicFactor=0.0,
        roughnessFactor=1.0,
        # emissiveTexture é adicionado por _exportar_glb()
    )
    visual = trimesh.visual.TextureVisuals(uv=all_uvs, material=material)
    mesh = trimesh.Trimesh(vertices=all_verts, faces=all_faces, visual=visual, process=False)
    return mesh
```

**Nota sobre watertight:** `trimesh.Trimesh(..., process=False)` desabilita o merge automático de vértices que pode comprometer faces de parede. Após montar, checar `mesh.is_watertight` — se False, usar `trimesh.repair.fix_winding(mesh)` ou `trimesh.repair.fill_holes(mesh)`.

### Pattern 3: Exportar GLB com emissiveTexture

```python
@staticmethod
def _exportar_glb(mesh: trimesh.Trimesh, imagem_pil: Image.Image) -> bytes:
    """Exporta GLB com emissiveTexture = a foto original (colorida, RGB)."""
    # PBRMaterial aceita PIL.Image diretamente para texturas
    material = trimesh.visual.material.PBRMaterial(
        baseColorFactor=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
        metallicFactor=0.0,
        roughnessFactor=1.0,
        doubleSided=False,
        # baseColor branco: o relevo aparece sem textura ("sem luz")
        # emissiveTexture = a foto: "acende" quando emissiveStrength > 0
        emissiveTexture=imagem_pil.convert("RGB"),  # PIL.Image obrigatório
        emissiveFactor=np.array([1.0, 1.0, 1.0], dtype=np.float32),
    )
    mesh.visual = trimesh.visual.TextureVisuals(
        uv=mesh.visual.uv,
        material=material,
    )
    scene = trimesh.Scene()
    scene.add_geometry(mesh)
    glb_bytes = scene.export(file_type="glb")
    return glb_bytes
```

**CRÍTICO:** `emissiveTexture` deve ser `PIL.Image` (não caminho de arquivo). Fonte: docs oficiais trimesh — "Parameters with Texture in them must be PIL.Image objects" (trimesh.visual.material — HIGH confidence).

**CRÍTICO:** `emissiveFactor` é `(3,) float` com valores em `[0.0, 1.0]`. O `emissiveStrength` (multiplicador acima de 1.0) é uma extensão glTF `KHR_materials_emissive_strength` que trimesh pode ou não exportar — testar na versão 4.12.2. Se não houver suporte, a solução alternativa é deixar `emissiveFactor=[1.0, 1.0, 1.0]` no GLB e controlar tudo pelo lado JS com `setEmissiveStrength(0)` / `setEmissiveStrength(5)`.

### Pattern 4: Toggle de luz — model-viewer JS API

A API de materiais do model-viewer (verificada em `api.ts` do repositório oficial):

```typescript
// Tipos verificados em api.ts (master, 2026)
interface Material {
  readonly emissiveFactor: Readonly<RGB>;
  setEmissiveFactor(rgb: RGB | string): void;
  readonly emissiveStrength: number;
  setEmissiveStrength(emissiveStrength: number): void;
}
```

**Padrão JS para o toggle:**

```javascript
// static/js/lithophane-editor.js  (IIFE, sem framework)
(function () {
  'use strict';

  // aguarda o model-viewer terminar de carregar o modelo
  const viewer = document.querySelector('#litho-viewer');
  let _emissiveLigado = false;

  function _toggleLuz() {
    if (!viewer.model) return;
    const mat = viewer.model.materials[0];
    _emissiveLigado = !_emissiveLigado;

    if (_emissiveLigado) {
      // "Com luz" — foto acende em tom quente
      mat.setEmissiveFactor([1.0, 0.9, 0.7]);  // warm LED
      mat.setEmissiveStrength(4.0);             // multiplicador (acima de 1.0)
      viewer.setAttribute('exposure', '0.4');   // escurece a iluminação ambiente
      viewer.setAttribute('shadow-intensity', '0');
    } else {
      // "Sem luz" — só o relevo branco
      mat.setEmissiveFactor([0.0, 0.0, 0.0]);
      mat.setEmissiveStrength(0);
      viewer.setAttribute('exposure', '1.0');
      viewer.setAttribute('shadow-intensity', '1');
    }
    document.querySelector('#btn-luz').classList.toggle('luz-ativa', _emissiveLigado);
  }

  document.querySelector('#btn-luz').addEventListener('click', _toggleLuz);
})();
```

**Nota sobre `exposure`:** É atributo HTML do `<model-viewer>` (não do material), controlável via `setAttribute`. Combinado com `setEmissiveStrength` produz o contraste visual mais nítido entre os dois estados.

**Nota sobre `setEmissiveStrength`:** O getter `emissiveStrength` é `readonly number`. O setter `setEmissiveStrength(n: number)` aceita valores > 1.0 (fora do range de `emissiveFactor`) para simular intensidade de luz. Verificado em `api.ts` e em discussões GitHub (HIGH confidence).

### Pattern 5: Editor canvas 2D

```javascript
// Ajustes ao vivo sem lib (CSS filter + getImageData)
function _aplicarFiltros(ctx, canvas, imgOriginal, brilho, contraste, inverter) {
  ctx.filter = `brightness(${brilho}%) contrast(${contraste}%)`;
  ctx.drawImage(imgOriginal, 0, 0, canvas.width, canvas.height);
  ctx.filter = 'none';

  if (inverter) {
    const id = ctx.getImageData(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < id.data.length; i += 4) {
      id.data[i]   = 255 - id.data[i];
      id.data[i+1] = 255 - id.data[i+1];
      id.data[i+2] = 255 - id.data[i+2];
    }
    ctx.putImageData(id, 0, 0);
  }
}

// Envio ao servidor
async function _gerarModelo(canvas, specs) {
  const dataURL = canvas.toDataURL('image/png');
  const csrf    = document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';

  const fd = new FormData();
  fd.append('imagem', dataURL);
  fd.append('formato', specs.formato);
  fd.append('largura_mm', specs.largura_mm);
  fd.append('espessura_max_mm', specs.espessura_max_mm);

  const resp = await fetch('/lithophane/gerar/', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrf },
    body: fd,
  });
  return resp.json();  // { glb_url, stl_url, draft_id }
}
```

**CSRF:** lido do cookie `csrftoken` — o padrão Django oficial para AJAX (HIGH confidence, docs Django). O projeto não usa SameSite=Strict explícito; o padrão `Lax` do Django 5.x permite fetch same-origin sem problema.

### Pattern 6: Extensão do carrinho para item sem preço

O `SessionCart` atual (`apps/cart/cart.py`) armazena `{str(product_id): int(qty)}` — só IDs de produtos reais. Um item lithophane não tem `product_id` real. A extensão mais limpa é uma **sessão separada** para rascunhos lithophane no carrinho, paralela à estrutura atual.

**Estratégia: chave de sessão separada `cart_litho`**

```python
# apps/cart/cart.py — adições ao SessionCart
LITHO_KEY = "cart_litho"

class SessionCart:
    # ... código existente inalterado ...

    def add_litho(self, draft_id: int) -> None:
        """Adiciona (ou substitui) um item lithophane ao carrinho."""
        drafts = self.session.get(LITHO_KEY, [])
        if draft_id not in drafts:
            drafts.append(draft_id)
        self.session[LITHO_KEY] = drafts
        self.session.modified = True

    def remove_litho(self, draft_id: int) -> None:
        drafts = [d for d in self.session.get(LITHO_KEY, []) if d != draft_id]
        self.session[LITHO_KEY] = drafts
        self.session.modified = True

    @property
    def litho_draft_ids(self) -> list[int]:
        return list(self.session.get(LITHO_KEY, []))

    def clear(self) -> None:
        self._items = {}
        self.session.pop(COUPON_KEY, None)
        self.session.pop(LITHO_KEY, None)  # <-- adicionado
        self._save()
```

### Pattern 7: Novo status ORCAMENTO e checkout sem pagamento

**`apps/orders/models.py` — adicionar ao TextChoices:**

```python
class Status(models.TextChoices):
    PENDING     = "pending",    "Aguardando pagamento"
    PAID        = "paid",       "Pago"
    PROCESSING  = "processing", "Em produção"
    SHIPPED     = "shipped",    "Enviado"
    DELIVERED   = "delivered",  "Entregue"
    CANCELLED   = "cancelled",  "Cancelado"
    ORCAMENTO   = "orcamento",  "Orçamento pendente"  # NOVO
```

**`apps/orders/models.py` — `Order.status` max_length precisa suportar "orcamento" (9 chars). Atual é `max_length=12` — OK.**

**`OrderItem` — campos novos para item lithophane (snapshot):**

```python
# apps/orders/models.py — OrderItem
class OrderItem(models.Model):
    # ... campos existentes ...
    # Novos campos para item de orçamento (nullable — retrocompatível)
    draft_id    = models.PositiveIntegerField("draft lithophane", null=True, blank=True)
    litho_specs = models.JSONField("specs do lithophane", null=True, blank=True)
    # ex: {"formato": "placa", "largura_mm": 100, "espessura_max_mm": 3.0, "foto_url": "..."}
```

**Necessária migration para o novo campo em `Order.Status` e `OrderItem`.**

**`apps/orders/services.py` — `OrderService.create_from_cart` — extensão para pular pagamento:**

```python
@staticmethod
@transaction.atomic
def create_from_cart(request, data: dict) -> Order:
    cart = CartService.build(request)
    # ... (código existente para itens de produto) ...

    tem_orcamento = bool(request.cart.litho_draft_ids)

    # Status inicial baseado no tipo de pedido
    status_inicial = Order.Status.ORCAMENTO if tem_orcamento else Order.Status.PENDING

    order = Order.objects.create(
        # ... campos existentes ...
        status=status_inicial,
    )

    # Criação de OrderItems normais (código existente)
    ...

    # Criação de OrderItems lithophane (sem product_id, sem unit_price real)
    litho_items = LithophaneQuery.drafts_by_ids(request.cart.litho_draft_ids)
    OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            product=None,
            product_name=f"Lithophane {draft.get_formato_display()} {draft.size}mm",
            unit_price=Decimal("0.00"),  # "a combinar"
            quantity=1,
            line_total=Decimal("0.00"),
            draft_id=draft.pk,
            litho_specs={
                "formato": draft.format,
                "largura_mm": draft.size,
                "espessura_max_mm": draft.thickness,
                "foto_url": draft.image.url if draft.image else "",
            },
        )
        for draft in litho_items
    ])

    # Estoque/cupom: só para itens de produto normais (código existente)
    ...

    # Pagamento: só se NÃO for orçamento
    if not tem_orcamento:
        PaymentService.process(order)

    request.cart.clear()
    return order
```

**Implicação:** `CartService.build` atualmente retorna `subtotal` baseado apenas em itens de produto. Para pedidos mistos (produtos + lithophane), o total de exibição deve incluir "a combinar". O template do checkout precisa de branch para este caso.

---

## Don't Hand-Roll

| Problema | Não construir | Usar | Por quê |
|----------|---------------|------|---------|
| Exportar GLB com material PBR | Serialização JSON glTF manual + buffers binários | `trimesh.Scene.export(file_type="glb")` | glTF é binário, tem chunks, padding e CRC — complexo demais à mão |
| Exportar STL binário | Struct packing manual | `trimesh.Trimesh.export(file_type="stl")` | STL binário tem header + normal + vértices por face |
| Watertight check/repair | Detecção manual de buracos | `mesh.is_watertight`, `trimesh.repair.fill_holes()` | Geometria computacional não trivial |
| UV map grid normalizado | Cálculo ad hoc | numpy `meshgrid` + normalização vetorizada | Veja Pattern 2 acima — puro numpy, sem loop |
| CSRF em fetch | Cookie manual | Leitura padrão do cookie `csrftoken` (docs Django) | Ver Pattern 5 — uma linha |

---

## Common Pitfalls

### Pitfall 1: `process=True` destrói a estrutura watertight
**O que vai errado:** Por padrão, `trimesh.Trimesh(..., process=True)` faz merge de vértices duplicados e remoção de faces degeneradas. Isso pode fundir os vértices das paredes laterais com os da face frontal e comprometer a malha fechada.
**Por que acontece:** O `process=True` é o padrão do trimesh; vértices com posição idêntica (ex: corner vértices compartilhados entre face frontal e parede) são colapsados.
**Como evitar:** Sempre construir a malha lithophane com `process=False`. Após montagem, verificar `mesh.is_watertight` manualmente.
**Sinais de alerta:** `mesh.is_watertight == False`; slicer reporta "non-manifold edges" no STL.

### Pitfall 2: `emissiveTexture` aceita apenas PIL.Image, não path/URL
**O que vai errado:** Passar o path do arquivo salvo ou URL do MEDIA em vez de PIL.Image levanta `TypeError` ou resulta em GLB sem textura emissiva.
**Por que acontece:** O `PBRMaterial.__init__` valida o tipo internamente.
**Como evitar:** Manter o `Image.Image` em memória durante todo o pipeline `gerar()` e passar ao `_exportar_glb()`. Não fechar/salvar antes do export.

### Pitfall 3: Tamanho do GLB × resolução do heightmap
**O que vai errado:** 300×300 px = 90 000 vértices na face frontal + base + 4 paredes ≈ ~185 000 vértices totais. Um GLB com emissiveTexture PNG embutida pode chegar a 3–8 MB, lento em mobile.
**Por que acontece:** glTF embute texturas em base64 dentro do JSON do chunk (GLB) ou como buffer separado.
**Como evitar:**
- Redimensionar a `emissiveTexture` para máx 512×512 antes de embutir (independente da resolução do heightmap).
- Para o heightmap, 200px é suficiente para a qualidade visual do viewer; 300px para impressão.
- Checar tamanho do GLB gerado nos testes; se > 5 MB, reduzir resolução.

### Pitfall 4: `CartService.build` quebra com `draft_id` na sessão
**O que vai errado:** O `CartQuery.products_by_ids(raw.keys())` itera sobre todos os IDs da sessão `cart`. Se adicionar `draft_id` no dicionário `cart` (em vez de `cart_litho`), o query tenta buscar um produto com aquele ID e retorna None (item órfão silencioso — pior, poderia colidir com PK real de produto).
**Como evitar:** A chave de sessão separada `cart_litho` (Pattern 6) garante que `cart` continue sendo `{product_id: qty}` apenas.

### Pitfall 5: `OrderItem.unit_price` e `line_total` são `DecimalField` NOT NULL
**O que vai errado:** Tentar salvar `unit_price=None` levanta `IntegrityError`.
**Como evitar:** Usar `Decimal("0.00")` como placeholder para itens "a combinar". O status `orcamento` na `Order` sinaliza para o admin que o valor real será confirmado por fora.

### Pitfall 6: Serving de media em dev vs prod
**O que vai errado:** Em prod, `WhiteNoise` serve apenas `STATIC_ROOT` — arquivos GLB/STL gerados em `MEDIA_ROOT` não são servidos. Em dev, `config/urls.py` já tem `static(MEDIA_URL, document_root=MEDIA_ROOT)` quando `DEBUG=True` — funciona.
**Como evitar:** Em prod, adicionar um web server (nginx) ou storage externo para `MEDIA_ROOT`. Isso é um concern existente (registrado em STATE.md) e está fora do escopo desta fase. Para dev, sem mudança necessária.

### Pitfall 7: `emissiveStrength` > 1.0 requer extensão glTF `KHR_materials_emissive_strength`
**O que vai errado:** Se trimesh 4.12.2 não emitir a extensão `KHR_materials_emissive_strength` no GLB, o `emissiveStrength` embutido no arquivo é ignorado pelo model-viewer (valor default = 1.0).
**Solução:** Controlar o `emissiveStrength` exclusivamente via JS (`mat.setEmissiveStrength(4.0)`) ao invés de embutir no GLB. O GLB carrega com `emissiveFactor=[1,1,1]` e strength=1.0; o JS eleva para o efeito "com luz".

---

## Code Examples

### Construir mesh grid vectorizado (núcleo do heightmap→malha)
```python
# Fonte: adaptado de colbrydi/Lithophane + loady.one/blog/terrain_mesh (verificado)
# Sem loops Python — completamente vectorizado com numpy

rows, cols = hmap.shape
xs = np.arange(cols, dtype=np.float32) * scale_x
ys = np.arange(rows, dtype=np.float32) * scale_y
XX, YY = np.meshgrid(xs, ys)                    # (rows, cols)

verts = np.column_stack([XX.ravel(), YY.ravel(), hmap.ravel()])  # (N, 3)

r = np.arange(rows - 1)
c = np.arange(cols - 1)
RR, CC = np.meshgrid(r, c, indexing="ij")       # (rows-1, cols-1)
idx = (RR * cols + CC).ravel()
faces = np.vstack([
    np.column_stack([idx, idx + 1, idx + cols + 1]),    # tri1
    np.column_stack([idx, idx + cols + 1, idx + cols]), # tri2
])  # (2*(rows-1)*(cols-1), 3)

uv = np.column_stack([
    XX.ravel() / (scale_x * (cols - 1)),
    1.0 - YY.ravel() / (scale_y * (rows - 1)),
]).astype(np.float32)  # (N, 2)
```

### Construir e exportar Trimesh com PBRMaterial + emissiveTexture
```python
# Fonte: trimesh docs (trimesh.org/trimesh.visual.material.html) — HIGH confidence
import trimesh
import trimesh.visual.material
import numpy as np
from PIL import Image

material = trimesh.visual.material.PBRMaterial(
    baseColorFactor=np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
    emissiveFactor=np.array([1.0, 1.0, 1.0], dtype=np.float32),
    emissiveTexture=pil_image,   # PIL.Image.Image obrigatório
    metallicFactor=0.0,
    roughnessFactor=1.0,
    doubleSided=False,
)
visual  = trimesh.visual.TextureVisuals(uv=uv_array, material=material)
mesh    = trimesh.Trimesh(vertices=verts, faces=faces, visual=visual, process=False)
scene   = trimesh.Scene()
scene.add_geometry(mesh)
glb_bytes = scene.export(file_type="glb")   # bytes prontos para FileField
stl_bytes = mesh.export(file_type="stl")    # bytes STL binário
```

### Toggle emissivo model-viewer
```javascript
// Fonte: model-viewer api.ts (github.com/google/model-viewer) — HIGH confidence
// Fonte: github.com/google/model-viewer/discussions/3050 — confirmado
const mv  = document.querySelector('#litho-viewer');
const mat = mv.model.materials[0];

// Ligar
mat.setEmissiveFactor([1.0, 0.9, 0.7]);   // warm LED
mat.setEmissiveStrength(4.0);
mv.setAttribute('exposure', '0.4');

// Desligar
mat.setEmissiveFactor([0.0, 0.0, 0.0]);
mat.setEmissiveStrength(0);
mv.setAttribute('exposure', '1.0');
```

### Fetch com CSRF para endpoint de geração
```javascript
// Fonte: docs.djangoproject.com/howto/csrf — HIGH confidence
const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';
const fd   = new FormData();
fd.append('imagem', canvas.toDataURL('image/png'));
fd.append('formato', 'placa');
fd.append('largura_mm', '100');

const resp = await fetch('/lithophane/gerar/', {
  method: 'POST',
  headers: { 'X-CSRFToken': csrf },
  body: fd,
});
const { glb_url, stl_url, draft_id } = await resp.json();
```

---

## Integration Points — Mapa de arquivos que mudam

### Arquivos novos (app `apps/lithophane/`)
| Arquivo | O que cria |
|---------|-----------|
| `apps/lithophane/__init__.py` | — |
| `apps/lithophane/apps.py` | `LithophaneConfig` |
| `apps/lithophane/models.py` | `LithophaneDraft` |
| `apps/lithophane/queries.py` | `LithophaneQuery` |
| `apps/lithophane/services.py` | `LithophaneService.generate()` |
| `apps/lithophane/generation.py` | `LithophaneGenerator` (motor isolado) |
| `apps/lithophane/mappers.py` | `LithophaneMapper` |
| `apps/lithophane/views.py` | `editor` view + `gerar` endpoint |
| `apps/lithophane/urls.py` | rotas do app |
| `apps/lithophane/admin.py` | registro admin |
| `apps/lithophane/templates/lithophane/editor.html` | página do editor |
| `apps/lithophane/migrations/0001_initial.py` | migration `LithophaneDraft` |
| `static/js/lithophane-editor.js` | editor canvas + toggle JS |

### Arquivos existentes que mudam
| Arquivo | Mudança |
|---------|---------|
| `config/settings/base.py` | Adicionar `"apps.lithophane"` em `LOCAL_APPS` |
| `config/urls.py` | `path("lithophane/", include("apps.lithophane.urls"))` |
| `apps/core/templates/core/partials/navbar.html` | Link "Faça meu Lithophane" |
| `apps/cart/cart.py` | `add_litho()`, `remove_litho()`, `litho_draft_ids`, `clear()` atualizado |
| `apps/cart/services.py` | `CartService.build()` — incluir itens litho no contexto de exibição |
| `apps/orders/models.py` | `Order.Status.ORCAMENTO` + campos `draft_id`/`litho_specs` em `OrderItem` |
| `apps/orders/services.py` | `OrderService.create_from_cart` — branch para pular `PaymentService` |
| `apps/orders/migrations/` | Nova migration para campos adicionados |
| `requirements.txt` | Adicionar `numpy` e `trimesh` |

---

## State of the Art

| Abordagem antiga | Abordagem atual | Quando mudou | Impacto |
|------------------|-----------------|--------------|---------|
| `numpy-stl` para STL apenas | `trimesh` cobre STL + GLB + PBR | 2018+ | trimesh é o padrão de fato para export 3D em Python |
| `emissiveFactor` max 1.0 | `KHR_materials_emissive_strength` permite >1.0 | glTF 2.0 extensão 2022 | `setEmissiveStrength()` no model-viewer js API |
| model-viewer material API experimental | API estável em @4.x: `setEmissiveFactor`, `setEmissiveStrength` | @4.0 (2024) | Seguro usar nos @4.3.1 já carregado |

---

## Open Questions

1. **trimesh 4.12.2 emite `KHR_materials_emissive_strength`?**
   - O que sabemos: a extensão existe na spec glTF 2.0; trimesh suporta PBRMaterial com `emissiveFactor`
   - O que não está claro: se o export GLB do trimesh 4.12.2 inclui automaticamente a extensão quando `emissiveFactor` é [1,1,1] + `emissiveStrength` > 1
   - Recomendação: Testar no Wave 0 — gerar GLB, abrir no Babylon Sandbox (sandbox.babylonjs.com) e inspecionar o JSON do chunk 0. Se a extensão não aparecer, controlar tudo pelo JS `setEmissiveStrength()`.

2. **`mesh.is_watertight` após montagem das paredes**
   - O que sabemos: a estratégia de duplicar vértices para paredes (Pattern 2) é necessária; trimesh tem `repair.fill_holes()`
   - O que não está claro: quantos casos corner (espessura min = 0 mm) geram faces degeneradas
   - Recomendação: Adicionar `assert mesh.is_watertight` no teste de bancada de `generation.py` com foto de alta variância.

3. **`CartService.build()` com itens lithophane**
   - O que sabemos: `CartSummaryMapper.to_summary()` calcula `total` baseado em subtotal+shipping-discount
   - O que não está claro: se o template de checkout precisa de branch para exibir "subtotal + itens a combinar" corretamente sem quebrar a UI de pedidos normais
   - Recomendação: O checkout pode ter um bloco `{% if has_litho_items %}` que exibe os itens litho separadamente com "A combinar"; manter o total dos produtos normais calculado normalmente.

---

## Sources

### Primary (HIGH confidence)
- [trimesh.visual.material — PBRMaterial docs](https://trimesh.org/trimesh.visual.material.html) — assinatura do construtor, tipos de parâmetros, emissiveTexture = PIL.Image
- [trimesh.creation docs](https://trimesh.org/trimesh.creation.html) — funções disponíveis, `extrude_triangulation`
- [trimesh PyPI](https://pypi.org/project/trimesh/) — versão atual 4.12.2, dependências
- [model-viewer api.ts](https://github.com/google/model-viewer/blob/master/packages/model-viewer/src/features/scene-graph/api.ts) — interface Material: `setEmissiveFactor`, `setEmissiveStrength`, `emissiveStrength: number`
- [Django CSRF docs](https://docs.djangoproject.com/en/6.0/howto/csrf/) — `X-CSRFToken` header para fetch

### Secondary (MEDIUM confidence)
- [model-viewer discussions #3050](https://github.com/google/model-viewer/discussions/3050) — `setEmissiveFactor()` confirmado como setter correto; valores > 1 via RGB
- [colbrydi/Lithophane lithophane.py](https://github.com/colbrydi/Lithophane/blob/master/lithophane.py) — algoritmo heightmap invertido verificado
- [trimesh test_texture.py](https://github.com/mikedh/trimesh/blob/main/tests/test_texture.py) — padrão `PBRMaterial + TextureVisuals + scene.export()`
- [KHR_materials_emissive_strength spec](https://github.com/KhronosGroup/glTF/blob/main/extensions/2.0/Khronos/KHR_materials_emissive_strength/README.md) — extensão glTF para strength > 1.0

### Tertiary (LOW confidence — marcado para validação)
- trimesh 4.12.2 emissão da extensão `KHR_materials_emissive_strength` — não confirmado via test case; requer validação no Wave 0

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versões verificadas no PyPI; trimesh docs oficiais consultados
- Algoritmo heightmap: HIGH — múltiplos repositórios públicos confirmam o padrão; vectorização numpy confirmada
- trimesh PBRMaterial + emissiveTexture export GLB: MEDIUM — API verificada nos docs; comportamento exato do export (extensão KHR_emissive_strength) não testado
- model-viewer emissive API: HIGH — verificado em `api.ts` do repositório oficial
- Cart/order integration: HIGH — código-fonte completo lido; padrões mapeados explicitamente
- Editor canvas 2D: HIGH — APIs nativas `CanvasRenderingContext2D.filter` + `getImageData` bem documentadas

**Research date:** 2026-06-07
**Valid until:** 2026-09-07 (stack estável; model-viewer e trimesh têm changelogs frequentes — reverificar se phase execução atrasar > 3 meses)

---

## RESEARCH COMPLETE
