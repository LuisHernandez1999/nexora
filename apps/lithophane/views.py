"""Views do lithophane — finas. Editor (GET) + endpoint de geração (POST)."""
from __future__ import annotations

import base64
import binascii
import io

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from PIL import Image, UnidentifiedImageError

from .mappers import LithophaneMapper
from .services import LithophaneService


def editor(request):
    return render(request, "lithophane/editor.html", {})


@require_POST
def gerar(request):
    data_url = request.POST.get("imagem", "")
    formato = request.POST.get("formato", "placa")
    try:
        largura_mm = float(request.POST.get("largura_mm", 100))
        espessura_mm = float(request.POST.get("espessura_max_mm", 3.0))
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "erro": "Specs inválidas."}, status=400)

    # dataURL "data:image/png;base64,...." -> PIL.Image
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    try:
        raw = base64.b64decode(data_url)
        imagem = Image.open(io.BytesIO(raw))
        imagem.load()
    except (binascii.Error, UnidentifiedImageError, OSError, ValueError):
        return JsonResponse({"ok": False, "erro": "Imagem inválida."}, status=400)

    # garante uma sessão para ser dono do rascunho anônimo (consistente com o carrinho)
    if not request.session.session_key:
        request.session.save()
    draft = LithophaneService.gerar(
        imagem,
        formato=formato,
        largura_mm=largura_mm,
        espessura_mm=espessura_mm,
        user=request.user,
        session_key=request.session.session_key or "",
    )
    return JsonResponse({"ok": True, **LithophaneMapper.to_dict(draft)})
