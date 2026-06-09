# Phase 5: Catálogo MakerWorld - Context

**Gathered:** 2026-06-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Encher a loja com um catálogo realista e relevante (estilo MakerWorld), com as **fotos padronizadas na identidade visual L3D Labz** e navegável pelos **filtros já existentes** (categoria, busca, ordenação) — opcionalmente enriquecido com filtro por material.

Entrega: pipeline de padronização de imagem (Pillow) + comando `seed_makerworld` que cria categorias + ~24 produtos curados com atributos e imagens padronizadas; produtos aparecem no catálogo com a foto branded e filtram por categoria/material.
</domain>

<decisions>
## Implementation Decisions

### Origem dos produtos
- **Scraping ao vivo do MakerWorld foi descartado**: o site retorna **403** a bots (anti-scraping). Em vez disso, curadoria realista dos *tipos* mais relevantes de impressão 3D (articulados, vasos, organizadores, luminárias, miniaturas, decoração, gadgets, cosplay), com nomes descritivos genéricos (sem copiar títulos autorais específicos).
- Usuário ciente e de acordo (tratado como catálogo de demonstração).

### Padronização de foto (identidade L3D Labz)
- Como não há fotos reais (MakerWorld bloqueado), a padronização **gera** o card do produto: fundo em gradiente radial verde-Luigi, "tile" central arredondado com o monograma do produto na cor de acento da categoria, nome embaixo, wordmark **L3D Labz**. Layout idêntico para todos → identidade única.
- Salvo no `Product.image` (ImageField `products/`) via `ContentFile`. O `ProductMapper.to_dict` já prefere `image.url` sobre `image_url`, então as fotos aparecem.
- Pipeline isolado em `apps/catalog/branding.py` (Pillow), reutilizável (aceita um nome + accent).

### Catálogo & filtros
- Filtros já existem: categoria (pills), busca (`q`), ordenação (`sort`: relevance/new/popular/price). Reusar.
- Enriquecer com **filtro por material** (PLA/PETG/Resina) no `ProductQuery.search` + select no `product_list.html`.
- Categorias ricas (8) com ícones do sprite existente + accents.

### Comando
- `python manage.py seed_makerworld` — idempotente (`get_or_create` por slug), regenera a imagem branded. Não apaga o seed_demo; complementa.
</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Product` (catalog/models.py): category FK, name, slug, description, price, compare_at_price, **image (ImageField)**, image_url (fallback), stock, rating, sales_count, material, dimensions, print_time_hours, is_featured, is_active.
- `Category`: name, slug, icon (sprite id), accent (hex), description, is_highlighted, order.
- `ProductMapper.to_dict`: `image_url = instance.image.url if instance.image else instance.image_url` — foto enviada tem prioridade.
- `ProductQuery.search(category_slug, query, sort, min_price, max_price)` (catalog/queries.py:118) — ponto de extensão p/ filtro de material.
- `CatalogService.browse(params, page)` (catalog/services.py:41) — lê `categoria`/`q`/`sort` dos params.
- `product_list.html`: pill bar de categorias + select de sort (linhas 16-37) — ponto p/ select de material.
- Padrão do comando de seed: `apps/catalog/management/commands/seed_demo.py` (CATEGORIES/PRODUCTS + get_or_create + slugify).
- Ícones do sprite disponíveis: cube, box, layers, leaf, printer3d, pick3d, ruler, star, spark, tag, etc.

### Established Patterns
- Camadas: services (escrita) → queries (ORM) → mappers. Pillow já é dependência.
- Comandos de management em catalog/management/commands/.
- `slugify` para slugs; Decimal para preços.

### Integration Points
- `apps/catalog/queries.py` (search) + `services.py` (browse) + `templates/catalog/product_list.html` — filtro de material.
- Media servida em dev via `if DEBUG` em config/urls.py — imagens branded aparecem.
</code_context>

<specifics>
## Specific Ideas
- "Padronizar a foto do que está sendo vendido com a identidade visual da loja" — gerar cards consistentes (verde Luigi + wordmark) é a interpretação robusta dado o bloqueio do MakerWorld.
- "Tudo mapeado e com filtros" — categoria (existe) + material (novo).
</specifics>

<deferred>
## Deferred Ideas
- Scraping real do MakerWorld com fotos dos autores (bloqueado por 403 + questão de licença já sinalizada).
- Filtro por faixa de preço na UI (a query já suporta min/max).
</deferred>
