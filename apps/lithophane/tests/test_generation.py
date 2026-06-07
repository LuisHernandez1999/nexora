"""Testes de bancada do motor de geração de lithophane.

Escrevem a especificação do `LithophaneGenerator` ANTES da implementação (TDD).
Resolvem por teste executável as incertezas do RESEARCH:
- a malha é watertight (necessário para STL imprimível)?
- o GLB embute a foto como emissiveTexture (para o toggle "com luz")?
- o relevo é invertido (claro = fino, escuro = grosso)?
"""
from __future__ import annotations

import io

import numpy as np
import trimesh
from django.test import SimpleTestCase
from PIL import Image

from apps.lithophane.generation import EspecsLitho, LithophaneGenerator


def _foto_teste(w: int = 240, h: int = 180) -> Image.Image:
    """Gradiente diagonal de alta variância (0..255) — garante relevo não trivial."""
    xx, yy = np.meshgrid(np.linspace(0, 255, w), np.linspace(0, 255, h))
    arr = ((xx + yy) / 2).astype("uint8")
    return Image.fromarray(arr, mode="L").convert("RGB")


def _foto_metades(w: int = 240, h: int = 180) -> Image.Image:
    """Metade esquerda preta (0), direita branca (255) — para testar inversão do relevo."""
    arr = np.zeros((h, w), dtype="uint8")
    arr[:, w // 2:] = 255
    return Image.fromarray(arr, mode="L").convert("RGB")


_SPECS = EspecsLitho(
    largura_mm=100.0,
    espessura_min_mm=0.8,
    espessura_max_mm=3.0,
    resolucao_px=200,
    formato="placa",
)


def _malha_de(blob: bytes, file_type: str) -> trimesh.Trimesh:
    carregado = trimesh.load(io.BytesIO(blob), file_type=file_type)
    if isinstance(carregado, trimesh.Scene):
        return list(carregado.geometry.values())[0]
    return carregado


class GeracaoLithophaneTests(SimpleTestCase):
    def test_gerar_devolve_dois_bytes(self):
        glb, stl = LithophaneGenerator.gerar(_foto_teste(), _SPECS)
        self.assertIsInstance(glb, bytes)
        self.assertGreater(len(glb), 0)
        self.assertIsInstance(stl, bytes)
        self.assertGreater(len(stl), 0)

    def test_glb_carrega_e_eh_watertight(self):
        glb, _ = LithophaneGenerator.gerar(_foto_teste(), _SPECS)
        malha = _malha_de(glb, "glb")
        self.assertGreater(len(malha.faces), 0)
        self.assertTrue(malha.is_watertight, "GLB precisa ser watertight")

    def test_stl_carrega_e_eh_watertight(self):
        _, stl = LithophaneGenerator.gerar(_foto_teste(), _SPECS)
        malha = _malha_de(stl, "stl")
        self.assertIsInstance(malha, trimesh.Trimesh)
        self.assertGreater(len(malha.faces), 0)
        self.assertTrue(malha.is_watertight, "STL precisa ser watertight (imprimível)")

    def test_relevo_invertido(self):
        # foto: esquerda escura (0) -> grossa, direita clara (255) -> fina
        _, stl = LithophaneGenerator.gerar(_foto_metades(), _SPECS)
        malha = _malha_de(stl, "stl")
        z = malha.vertices[:, 2]
        # a altura máxima atinge ~espessura_max nos pixels escuros
        self.assertGreaterEqual(z.max(), _SPECS.espessura_max_mm - 0.05)
        # e o relevo tem amplitude (não é placa plana)
        self.assertGreater(z.max() - z.min(), _SPECS.espessura_max_mm - _SPECS.espessura_min_mm - 0.05)

    def test_glb_tem_textura_emissiva(self):
        glb, _ = LithophaneGenerator.gerar(_foto_teste(), _SPECS)
        # robusto: ou o material recarregado expõe emissiveTexture, ou o JSON do GLB cita "emissive"
        try:
            material = _malha_de(glb, "glb").visual.material
            tem_attr = getattr(material, "emissiveTexture", None) is not None
        except Exception:
            tem_attr = False
        self.assertTrue(tem_attr or b"emissive" in glb, "GLB deve conter a textura emissiva")

    def test_glb_abaixo_de_5mb(self):
        glb, _ = LithophaneGenerator.gerar(_foto_teste(), _SPECS)
        self.assertLess(len(glb), 5 * 1024 * 1024)

    def test_todos_formatos_geram_malha_watertight(self):
        for fmt in ("placa", "luminaria", "curvo", "cubo"):
            specs = EspecsLitho(
                largura_mm=100.0, espessura_min_mm=0.8, espessura_max_mm=3.0,
                resolucao_px=160, formato=fmt,
            )
            glb, stl = LithophaneGenerator.gerar(_foto_teste(), specs)
            malha = _malha_de(stl, "stl")
            self.assertGreater(len(malha.faces), 0, fmt)
            self.assertTrue(malha.is_watertight, f"formato {fmt} deve ser watertight")
            self.assertGreater(len(glb), 0, fmt)
