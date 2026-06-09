"""Views do editor: a página carrega e o endpoint gera de ponta a ponta."""
from __future__ import annotations

import base64
import io
import tempfile

import numpy as np
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

_MEDIA = tempfile.mkdtemp(prefix="litho-views-")


def _data_url() -> str:
    xx, yy = np.meshgrid(np.linspace(0, 255, 120), np.linspace(0, 255, 90))
    img = Image.fromarray(((xx + yy) / 2).astype("uint8"), mode="L").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


@override_settings(
    MEDIA_ROOT=_MEDIA,
    SECURE_SSL_REDIRECT=False,
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
)
class EditorViewsTests(TestCase):
    def test_editor_renderiza(self):
        resp = self.client.get(reverse("lithophane:editor"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Onde memórias preciosas ganham forma na luz")
        self.assertContains(resp, "litho-canvas")

    def test_gerar_endpoint_devolve_urls(self):
        resp = self.client.post(reverse("lithophane:gerar"), {
            "imagem": _data_url(),
            "formato": "placa",
            "largura_mm": "100",
            "espessura_max_mm": "3",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertTrue(data["glb_url"].endswith(".glb"))
        self.assertTrue(data["stl_url"].endswith(".stl"))
        self.assertTrue(data["draft_id"])

    def test_gerar_rejeita_imagem_invalida(self):
        resp = self.client.post(reverse("lithophane:gerar"), {"imagem": "data:image/png;base64,xxx"})
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()["ok"])
