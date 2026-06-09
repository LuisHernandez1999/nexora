# Phase 1: Rebrand & UI Minimalista - Context

**Gathered:** 2026-06-05
**Status:** Ready for planning
**Source:** Brainstorming + user decisions (não passou por discuss-phase; decisões abaixo são locked)

<domain>
## Phase Boundary

Esta fase entrega a **nova identidade visual L3D Labz** (cores do Luigi), aplicada via tokens CSS existentes, em tema **claro e escuro**, com a home e páginas-chave num tratamento **minimalista**. NÃO inclui nada de modelo 3D (Fases 2 e 3).

Cobre: BRAND-01, BRAND-02, BRAND-03, THEME-01, THEME-02, THEME-03, UI-01, UI-02.
</domain>

<decisions>
## Implementation Decisions (LOCKED)

### Marca / Naming
- Nome do site: **"L3D Labz"** (substitui "Nexora" em 100% das ocorrências: `config/settings/base.py` dict `SITE.name`, title/meta em `base.html`, copy de home/about/footer/newsletter, seed `apps/catalog/management/commands/seed_demo.py`, qualquer admin/string).
- Tagline sugerida (pt-br, pode refinar): "Impressão 3D com acabamento de laboratório." — atualizar `SITE.tagline`.
- O `SITE.accent` em settings passa de `#3B82F6` para o verde primário (ver paleta).
- Eliminar a palavra "Nexora" — verificação final: `grep -ri nexora` no projeto deve voltar vazio (exceto histórico git).

### Logo / Wordmark
- Trocar o logo `#i-koala` por um **emblema "L"** estilo boné do Luigi: círculo branco com a letra "L" em verde, em SVG inline (definir um novo símbolo no sprite `apps/core/templates/core/partials/icons.html`, ex.: `#i-l3d-mark`, e referenciá-lo no navbar).
- Wordmark no navbar (`apps/core/templates/core/partials/navbar.html`): hoje é `nex<b>ora</b>` (hardcoded e dividido à mão). Trocar por "L3D Labz" — sugerido `<b>L3D</b> Labz` (o "L3D" com peso/cor de destaque). Como o nome tem grafia estilizada, pode ficar hardcoded como markup, mas o `aria-label` e o `<title>` devem usar "L3D Labz".
- Mesmo emblema serve de favicon conceitual (favicon opcional, não bloqueante).

### Paleta Luigi (tokens) — usar estes valores como base, refinar levemente se necessário p/ contraste AA
Cores-fonte do Luigi: verde do boné, branco do emblema, azul dos olhos, vermelho da boca.

**Acento (compartilhado entre temas):**
- `--accent` (verde primário): **#2FA84F**
- `--accent-strong` (verde escuro p/ hover/gradiente): **#1E8C3E**
- `--accent-2` (verde claro p/ eyebrows/realces): **#43C266**
- `--accent-soft` (fundo suave do acento): tint do verde (light: `#E7F6EC`; dark: `#13251A`)
- `--accent-glow`: `rgba(47, 168, 79, 0.26)`
- Azul "olho do Luigi" como acento secundário pontual: `--accent-blue: #2BA6E0` (usar com parcimônia: links de detalhe, foco, um realce no hero).
- `--danger` (vermelho boca, p/ erros/sale): **#E23B3B**
- `--success`: pode reaproveitar o verde (#2FA84F) ou um verde levemente distinto.

**Tema CLARO (estética base — light/clean minimalista):**
- `--bg`: **#FFFFFF**
- `--bg-soft`: **#F6F8F5** (leve toque esverdeado)
- `--bg-card`: **#FFFFFF**
- `--bg-elevated`: **#F1F4EF**
- `--border`: **#E3E8E0**
- `--border-soft`: **#EEF1EB**
- `--text`: **#16201A** (quase preto, leve toque verde-frio)
- `--text-muted`: **#5C6B60**
- `--text-dim`: **#9AA89E**
- Remover/atenuar os radial-gradients pesados do `body`; no light, fundo praticamente liso (talvez um glow verde sutilíssimo no topo).

**Tema ESCURO (recolorir o atual de azul→verde):**
- Manter as superfícies escuras frias atuais (`--bg #0a0d15` etc.) OU deslocar levemente p/ verde-petróleo. Decisão: manter os escuros atuais e só trocar o acento azul pelo verde acima + ajustar `--accent-soft`/glow para versões verdes. Garantir contraste do verde sobre o escuro (AA).

### Tipografia
- Manter as fontes atuais (Inter + Sora) — combinam com minimalismo. Sem mudança de fonte obrigatória.
- Minimalismo: aumentar respiro — line-height confortável, headings com `letter-spacing` negativo discreto (já existe).

### Tema claro/escuro (toggle)
- O toggle já existe (`#themeToggle` em navbar + `static/js/app.js`). Deve continuar funcionando alternando os dois temas calibrados.
- **Migrar a chave de localStorage** de `'nexora-theme'` para **`'l3d-theme'`** em AMBOS os arquivos onde aparece: `apps/core/templates/base.html` (script de boot, linha ~5, leitura) e `static/js/app.js` (escrita). Mudar nos dois juntos para não quebrar a persistência. (Opcional: migração suave lendo a chave antiga uma vez — não obrigatório.)
- Default do tema pode permanecer dark (`data-theme="dark"` no `<html>`), mas como a estética base agora é light/clean, considerar default light. Decisão: **default light** para refletir o minimalismo pedido (ajustar `data-theme` no `<html>` e o boot script de acordo). Manter o toggle para dark.

### Minimalismo (UI-01 home, UI-02 catálogo + detalhe)
- Home (`apps/core/templates/core/home.html`): reduzir densidade visual. Diretrizes:
  - Hero mais enxuto: menos overlay/gradiente, foco em headline + subhead + 1 CTA primário (verde) + 1 secundário ghost. Stats podem ficar, mais discretos.
  - Reduzir gradientes animados (`.grad-text` pode virar só verde sólido ou gradiente verde sutil).
  - Mais whitespace entre seções; cards mais limpos (bordas suaves, sombra leve, menos "glow").
  - Manter as seções essenciais (categorias, destaques, lançamentos, newsletter) mas com respiro.
- Catálogo e detalhe (`product_list.html`, `product_detail.html`): aplicar o mesmo tratamento de cor/spacing minimalista, consistente com a home. Sem redesenho funcional, só refino visual via tokens/classes existentes.
- Botões primários usam o verde; hover shimmer pode ficar mais sutil.

### Out of scope desta fase
- Qualquer coisa de modelo 3D (campos, viewer, galeria) — Fases 2/3.
- Mudança de estrutura de páginas/rotas.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Arquitetura & estrutura
- `.planning/codebase/STRUCTURE.md` — onde ficam templates, static, settings
- `.planning/codebase/ARCHITECTURE.md` — padrão em camadas, context processors
- `.planning/codebase/CONCERNS.md` — bloqueios de rebrand (wordmark hand-split, chave localStorage em 2 arquivos, ~20 strings "Nexora")

### Arquivos-chave a tocar
- `config/settings/base.py` — dict `SITE` (linha ~218)
- `static/css/theme.css` — tokens de cor (`:root` ~linha 6; verificar bloco `[data-theme]` para light/dark)
- `apps/core/templates/base.html` — boot script de tema (linha ~5), title/meta
- `apps/core/templates/core/partials/navbar.html` — wordmark + logo
- `apps/core/templates/core/partials/icons.html` — sprite SVG (adicionar `#i-l3d-mark`)
- `apps/core/templates/core/partials/footer.html` — strings de marca
- `apps/core/templates/core/home.html` — minimalismo
- `apps/catalog/templates/catalog/product_list.html`, `product_detail.html` — minimalismo
- `static/js/app.js` — chave de tema (escrita, ~linha 26)
- `apps/catalog/management/commands/seed_demo.py` — strings de marca em dados demo
</canonical_refs>

<specifics>
## Specific Ideas

- Referência de marca: Luigi (verde/branco/azul). Logo = "L" no emblema do boné.
- Verificar contraste AA do verde #2FA84F: sobre branco como texto é fraco — usar verde para fundos de botão (texto branco) e para realces, NÃO como cor de texto de corpo sobre branco. Para "links" em verde, usar o verde-escuro `#1E8C3E` no light.
</specifics>

<deferred>
## Deferred Ideas
- Favicon/PWA icons com o emblema L3D — bom ter, não bloqueante.
- AR e tudo de 3D — Fases 2/3.
</deferred>

---

*Phase: 01-rebrand-ui-minimalista*
*Context gathered: 2026-06-05 (brainstorming + locked user decisions)*
