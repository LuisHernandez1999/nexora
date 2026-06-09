"""Integração: carrinho só-lithophane -> pedido de orçamento sem captura de pagamento."""
from __future__ import annotations

import tempfile

import numpy as np
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings
from PIL import Image

from apps.cart.cart import SessionCart
from apps.lithophane.services import LithophaneService
from apps.orders.models import Order, OrderItem
from apps.orders.services import OrderService

_MEDIA = tempfile.mkdtemp(prefix="litho-order-")


def _foto() -> Image.Image:
    xx, yy = np.meshgrid(np.linspace(0, 255, 140), np.linspace(0, 255, 100))
    return Image.fromarray(((xx + yy) / 2).astype("uint8"), mode="L").convert("RGB")


def _req_com_sessao(user):
    rf = RequestFactory()
    req = rf.post("/pedidos/checkout/")
    SessionMiddleware(lambda r: None).process_request(req)
    req.session.save()
    req.user = user
    req.cart = SessionCart(req)
    return req


_DADOS_ENTREGA = {
    "payment_method": "pix",
    "recipient": "Fulano de Tal",
    "zip_code": "01001-000",
    "street": "Rua Teste",
    "number_addr": "100",
    "district": "Centro",
    "city": "São Paulo",
    "state": "sp",
}


@override_settings(MEDIA_ROOT=_MEDIA)
class PedidoOrcamentoLithophaneTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="cliente@example.com", password="senha12345"
        )

    def test_checkout_so_lithophane_gera_orcamento_sem_pagamento(self):
        draft = LithophaneService.gerar(
            _foto(), formato="placa", largura_mm=100.0, espessura_mm=3.0,
        )
        req = _req_com_sessao(self.user)
        req.cart.add_litho(draft.pk)

        order = OrderService.create_from_cart(req, _DADOS_ENTREGA)

        # status de orçamento, pagamento NÃO capturado
        self.assertEqual(order.status, Order.Status.ORCAMENTO)
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertIsNone(order.paid_at)

        # um OrderItem de lithophane com snapshot
        item = OrderItem.objects.get(order=order)
        self.assertEqual(item.draft_id, draft.pk)
        self.assertIsNone(item.product)
        self.assertEqual(item.litho_specs["formato"], "placa")
        self.assertEqual(item.litho_specs["largura_mm"], 100.0)

        # carrinho esvaziado (cart_litho limpo)
        self.assertEqual(req.cart.litho_draft_ids, [])
