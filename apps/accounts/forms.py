"""Formulários de conta — cadastro, login e perfil."""
from __future__ import annotations

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Nome", max_length=60)
    email = forms.EmailField(label="E-mail")
    phone = forms.CharField(label="Telefone", max_length=20, required=False)
    newsletter_opt_in = forms.BooleanField(
        label="Quero receber novidades e promoções", required=False, initial=True
    )

    class Meta:
        model = User
        fields = ("first_name", "email", "phone", "newsletter_opt_in")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email


class EmailLoginForm(AuthenticationForm):
    """Login por e-mail (o campo continua se chamando 'username' no AuthenticationForm)."""

    username = forms.EmailField(label="E-mail", widget=forms.EmailInput)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "newsletter_opt_in")
        labels = {
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "phone": "Telefone",
            "newsletter_opt_in": "Recebe novidades",
        }
