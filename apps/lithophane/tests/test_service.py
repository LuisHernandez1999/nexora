"""Smoke test end-to-end do LithophaneService — motor + ORM + FileField juntos."""
from __future__ import annotations

import tempfile

import numpy as np
from django.test import TestCase, override_settings
from PIL import Image

from apps.lithophane.mappers import LithophaneMapper
from apps.lithophane.models import LithophaneDraft
from apps.lithophane.queries import LithophaneQuery
from apps.lithophane.services import LithophaneService

_MEDIA = tempfile.mkdtemp(prefix="litho-test-")


def _foto() -> Image.Image:
    xx, yy = np.meshgrid(np.linspace(0, 255, 160), np.linspace(0, 255, 120))
    return Image.fromarray(((xx + yy) / 2).astype("uint8"), mode="L").convert("RGB")


@override_settings(MEDIA_ROOT=_MEDIA)
class LithophaneServiceTests(TestCase):
    def test_gerar_persiste_draft_com_arquivos(self):
        draft = LithophaneService.gerar(
            _foto(), formato="placa", largura_mm=100.0, espessura_mm=3.0, session_key="abc123",
        )
        self.assertIsInstance(draft, LithophaneDraft)
        self.assertTrue(draft.pk)
        # os três arquivos foram salvos
        self.assertTrue(draft.image.name.endswith(".png"))
        self.assertTrue(draft.model_glb.name.endswith(".glb"))
        self.assertTrue(draft.model_stl.name.endswith(".stl"))
        self.assertGreater(draft.model_glb.size, 0)
        self.assertGreater(draft.model_stl.size, 0)
        self.assertEqual(draft.session_key, "abc123")

    def test_query_e_mapper(self):
        draft = LithophaneService.gerar(
            _foto(), formato="luminaria", largura_mm=120.0, espessura_mm=2.5,
        )
        self.assertEqual(LithophaneQuery.by_id(draft.pk).pk, draft.pk)
        self.assertEqual([d.pk for d in LithophaneQuery.drafts_by_ids([draft.pk])], [draft.pk])
        d = LithophaneMapper.to_dict(draft)
        self.assertEqual(d["draft_id"], draft.pk)
        self.assertEqual(d["format"], "luminaria")
        self.assertTrue(d["glb_url"] and d["stl_url"] and d["image_url"])
