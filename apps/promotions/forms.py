"""Formularios de promoções — criacao de oferta pelo vendedor."""
from __future__ import annotations

from django import forms

from apps.catalog.models import Product


class OfferForm(forms.Form):
    """Vendedor escolhe um produto seu e define valor original x promocional."""

    product = forms.ModelChoiceField(
        queryset=Product.objects.none(), label="Produto",
        empty_label="Selecione um produto seu",
    )
    original_price = forms.DecimalField(
        label="Valor original (R$)", max_digits=10, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={"step": "0.01"}),
    )
    promo_price = forms.DecimalField(
        label="Valor promocional (R$)", max_digits=10, decimal_places=2, min_value=0,
        widget=forms.NumberInput(attrs={"step": "0.01"}),
    )

    def __init__(self, *args, seller=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Product.objects.none()
        if seller is not None:
            qs = Product.objects.filter(seller=seller).select_related("category").order_by("name")
        self.fields["product"].queryset = qs

    def clean(self):
        cleaned = super().clean()
        original = cleaned.get("original_price")
        promo = cleaned.get("promo_price")
        if original is not None and promo is not None and promo >= original:
            self.add_error("promo_price", "O valor promocional deve ser menor que o original.")
        return cleaned
