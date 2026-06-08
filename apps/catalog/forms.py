"""Formularios do catalogo — cadastro de produto (vendedor) e avaliacao."""
from __future__ import annotations

from django import forms

from .models import Product, Review


class ProductForm(forms.ModelForm):
    """Cadastro/edicao de produto pelo vendedor.

    As fotos (ate 4) sao tratadas fora do ModelForm, na view/service, porque
    vem como lista em request.FILES / lista de URLs.
    """

    class Meta:
        model = Product
        fields = (
            "category", "name", "description",
            "price", "compare_at_price",
            "material", "dimensions", "stock",
            "is_active",
        )
        labels = {
            "category": "Categoria",
            "name": "Nome do produto",
            "description": "Descricao",
            "price": "Valor (R$)",
            "compare_at_price": "Valor normal / de (R$)",
            "material": "Material",
            "dimensions": "Dimensoes",
            "stock": "Estoque",
            "is_active": "Publicado",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Conte os detalhes da peca…"}),
            "dimensions": forms.TextInput(attrs={"placeholder": "ex.: 20×9×7 cm"}),
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "compare_at_price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }
        help_texts = {
            "compare_at_price": "Preco cheio riscado. Deixe vazio se nao houver desconto.",
        }

    def clean(self):
        cleaned = super().clean()
        price = cleaned.get("price")
        compare = cleaned.get("compare_at_price")
        if price is not None and price <= 0:
            self.add_error("price", "O valor deve ser maior que zero.")
        if compare and price and compare <= price:
            self.add_error("compare_at_price", "O valor normal deve ser maior que o valor de venda.")
        return cleaned


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        label="Sua nota",
        coerce=int,
        choices=[(5, "5 — Excelente"), (4, "4 — Muito bom"), (3, "3 — Regular"),
                 (2, "2 — Ruim"), (1, "1 — Pessimo")],
        initial=5,
    )

    class Meta:
        model = Review
        fields = ("rating", "title", "comment")
        labels = {"title": "Titulo (opcional)", "comment": "Comentario"}
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3, "placeholder": "O que achou do produto?"}),
            "title": forms.TextInput(attrs={"placeholder": "Resumo em poucas palavras"}),
        }
