"""Serviço do lithophane — única camada de escrita.

Faz a ponte entre o motor isolado `generation.py` (que só conhece PIL/numpy/
trimesh) e o Django (FileField/ORM): recebe a imagem ajustada + specs, chama
`LithophaneGenerator.gerar`, e persiste o `LithophaneDraft` com os arquivos GLB/STL.
"""
from __future__ import annotations

import io

from django.core.files.base import ContentFile

from apps.core.layers import BaseService

from .generation import EspecsLitho, LithophaneGenerator
from .models import LithophaneDraft

# espessura mínima fixa do lithophane (parte clara/fina) — discricionário
ESPESSURA_MIN_MM = 0.8
# resolução do heightmap (maior lado) — equilíbrio qualidade/tamanho do GLB (RESEARCH Pitfall 3)
RESOLUCAO_PX = 200


class LithophaneService(BaseService):
    @staticmethod
    def gerar(
        imagem_pil,
        *,
        formato: str,
        largura_mm: float,
        espessura_mm: float,
        user=None,
        session_key: str = "",
    ) -> LithophaneDraft:
        """Gera GLB+STL via LithophaneGenerator, persiste e devolve o draft."""
        # formato do motor: os 4 são suportados (placa/luminaria/curvo/cubo)
        formato_motor = formato if formato in ("placa", "luminaria", "curvo", "cubo") else "placa"
        specs = EspecsLitho(
            largura_mm=float(largura_mm),
            espessura_min_mm=ESPESSURA_MIN_MM,
            espessura_max_mm=float(espessura_mm),
            resolucao_px=RESOLUCAO_PX,
            formato=formato_motor,
        )
        glb_bytes, stl_bytes = LithophaneGenerator.gerar(imagem_pil, specs)

        draft = LithophaneDraft(
            user=user if (user and user.is_authenticated) else None,
            session_key=session_key or "",
            format=formato,
            size=largura_mm,
            thickness=espessura_mm,
        )
        # salva a foto original (a imagem ajustada que veio do canvas)
        buf = io.BytesIO()
        imagem_pil.convert("RGB").save(buf, format="PNG")
        draft.image.save("foto.png", ContentFile(buf.getvalue()), save=False)
        # save=False: escreve os FileFields em memória e persiste tudo num único draft.save()
        draft.model_glb.save("modelo.glb", ContentFile(glb_bytes), save=False)
        draft.model_stl.save("modelo.stl", ContentFile(stl_bytes), save=False)
        draft.save()
        return draft
