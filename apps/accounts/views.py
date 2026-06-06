"""Views do app de contas — finas, delegam ao AccountService."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import EmailLoginForm, ProfileForm, RegisterForm
from .services import AccountService


def _post_auth_redirect(user) -> str:
    """Vendedor cai no painel da loja; cliente vai pra landing."""
    return "seller:products" if getattr(user, "is_seller", False) else "core:home"


class NexoraLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        # respeita ?next= se houver; senão roteia pelo papel do usuário
        return self.get_redirect_url() or reverse_lazy(_post_auth_redirect(self.request.user))


class NexoraLogoutView(LogoutView):
    next_page = reverse_lazy("core:home")


def register(request):
    if request.user.is_authenticated:
        return redirect(_post_auth_redirect(request.user))
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = AccountService.register(form)
            login(request, user)
            messages.success(request, f"Bem-vindo(a), {user.display_name}! Sua conta foi criada.")
            return redirect(_post_auth_redirect(user))
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            AccountService.update_profile(request.user, form)
            messages.success(request, "Dados atualizados com sucesso.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    context = AccountService.get_profile_context(request.user)
    context["form"] = form
    return render(request, "accounts/profile.html", context)
