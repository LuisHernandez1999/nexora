"""Serviços do app de contas — regra de negócio e escrita."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.core.layers import BaseService

from .mappers import AddressMapper, UserMapper
from .queries import AddressQuery

User = get_user_model()


class AccountService(BaseService):
    @staticmethod
    @transaction.atomic
    def register(form) -> User:
        """Cria o usuário a partir do RegisterForm já validado."""
        user = form.save(commit=False)
        data = form.cleaned_data
        user.email = data["email"]
        user.phone = data.get("phone", "")
        user.newsletter_opt_in = data.get("newsletter_opt_in", True)
        user.save()
        return user

    @staticmethod
    def update_profile(user, form) -> User:
        form.save()
        return user

    @staticmethod
    def get_profile_context(user) -> dict:
        addresses = AddressQuery.for_user(user)
        return {
            "profile": UserMapper.to_dict(user),
            "addresses": AddressMapper.to_list(addresses),
        }
