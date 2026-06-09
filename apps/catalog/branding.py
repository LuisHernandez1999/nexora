"""Padronização de imagem de produto com a identidade visual L3D Labz.

Como não temos a foto real do produto, geramos um card consistente: gradiente
radial verde-Luigi, um "tile" central arredondado com o monograma do produto na
cor de acento da categoria, o nome embaixo e o wordmark L3D Labz. Todos os
produtos ganham o mesmo enquadramento → identidade única.

Pipeline isolado (só Pillow/numpy) — reutilizável por qualquer comando/serviço.
"""
from __future__ import annotations

import io
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# tons do verde Luigi (fundo claro e elegante)
_BG_CENTRO = (246, 251, 247)
_BG_BORDA = (210, 232, 216)
_TEXTO = (22, 32, 26)
_MUTED = (92, 107, 96)


def _rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _fonte(tamanho: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidatos = (
        ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"] if bold
        else ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
    )
    for caminho in candidatos:
        try:
            return ImageFont.truetype(caminho, tamanho)
        except OSError:
            continue
    return ImageFont.load_default(size=tamanho)  # Pillow >= 10.1: escalável


def _gradiente_radial(size: int) -> Image.Image:
    yy, xx = np.mgrid[0:size, 0:size]
    c = size / 2.0
    d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (size * 0.72)
    d = np.clip(d, 0.0, 1.0)[..., None]
    centro = np.array(_BG_CENTRO)
    borda = np.array(_BG_BORDA)
    arr = (centro * (1 - d) + borda * d).astype("uint8")
    return Image.fromarray(arr, "RGB")


def _monograma(nome: str) -> str:
    partes = [p for p in nome.split() if p]
    if len(partes) >= 2:
        return (partes[0][:1] + partes[1][:1]).upper()
    return nome[:2].upper()


def _quebrar(draw, texto, fonte, largura_max) -> list[str]:
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if draw.textlength(teste, font=fonte) <= largura_max:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas[:3]


def gerar_card(nome: str, accent: str = "#2FA84F", tamanho: int = 800) -> bytes:
    """Devolve PNG (bytes) com o card padronizado do produto."""
    img = _gradiente_radial(tamanho)
    draw = ImageDraw.Draw(img)
    acc = _rgb(accent)

    # tile central arredondado na cor da categoria
    tile = int(tamanho * 0.42)
    tx = (tamanho - tile) // 2
    ty = int(tamanho * 0.17)
    draw.rounded_rectangle(
        [tx, ty, tx + tile, ty + tile], radius=int(tile * 0.22), fill=acc
    )
    # leve brilho no topo do tile
    draw.rounded_rectangle(
        [tx, ty, tx + tile, ty + int(tile * 0.5)], radius=int(tile * 0.22),
        fill=tuple(min(255, int(v * 1.12)) for v in acc),
    )
    draw.rounded_rectangle(
        [tx, ty + int(tile * 0.34), tx + tile, ty + tile], radius=int(tile * 0.22), fill=acc
    )

    # monograma centralizado no tile
    mono = _monograma(nome)
    f_mono = _fonte(int(tile * 0.46), bold=True)
    bbox = draw.textbbox((0, 0), mono, font=f_mono)
    mw, mh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (tamanho / 2 - mw / 2 - bbox[0], ty + tile / 2 - mh / 2 - bbox[1]),
        mono, font=f_mono, fill=(255, 255, 255),
    )

    # nome do produto (centralizado, até 3 linhas)
    f_nome = _fonte(int(tamanho * 0.058), bold=True)
    linhas = _quebrar(draw, nome, f_nome, tamanho * 0.82)
    y = int(tamanho * 0.66)
    for ln in linhas:
        w = draw.textlength(ln, font=f_nome)
        draw.text((tamanho / 2 - w / 2, y), ln, font=f_nome, fill=_TEXTO)
        y += int(tamanho * 0.07)

    # wordmark L3D Labz
    f_mark = _fonte(int(tamanho * 0.038), bold=True)
    marca = "L3D Labz"
    w = draw.textlength(marca, font=f_mark)
    draw.text((tamanho / 2 - w / 2, int(tamanho * 0.9)), marca, font=f_mark, fill=acc)
    # impresso em 3D — subtítulo
    f_sub = _fonte(int(tamanho * 0.026))
    sub = "impresso em 3D sob demanda"
    ws = draw.textlength(sub, font=f_sub)
    draw.text((tamanho / 2 - ws / 2, int(tamanho * 0.945)), sub, font=f_sub, fill=_MUTED)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Fotos reais padronizadas (busca por palavra-chave + tratamento de marca)
# --------------------------------------------------------------------------- #

# Fotos reais CURADAS (Unsplash) por categoria — relevantes e bonitas, não aleatórias.
_FOTOS = {
    "action figures": ["1606663889134-b1dedb5ed8b7", "1702138129392-364adea0ad00",
                        "1558679908-541bcf1249ff", "1558507334-57300f59f0bd",
                        "1608278047522-58806a6ac85b", "1597422232698-1a27a1289cea"],
    "articulados": ["1642534270237-ae57b321c5bc", "1559592036-0052501e60f4",
                    "1638013412964-d8b72c5d3f5f", "1550747545-c896b5f89ff7",
                    "1676390651124-64e9077daa7a", "1638012107344-3ed0f994d8d7"],
    "vasos & plantas": ["1631125915902-d8abe9225ff2", "1597696929736-6d13bed8e6a8",
                        "1612196808214-b8e1d6145a8c", "1660721671073-e139688fa3cf",
                        "1677761640321-b80251be00ca", "1631125915973-e0d155a14e4e"],
    "organizadores": ["1644463589256-02679b9c0767", "1700451761309-656bd9439443",
                      "1496128858413-b36217c2ce36", "1600658747056-eb00845297a5",
                      "1707413463619-8f4926d225ba"],
    "luminárias": ["1517991104123-1d56a6e81ed9", "1585128719715-46776b56a0d1",
                   "1580130281320-0ef0754f2bf7", "1621177555630-b861919c864f",
                   "1570974802254-4b0ad1a755f5", "1620812067822-899be8a6a9a7"],
    "miniaturas": ["1581273126845-a6892323dfc1", "1659019758082-602807e08519",
                   "1739133978409-ea3edf530979", "1739133978422-b7f72d385865",
                   "1558896153-5186ac7ed53d"],
    "gadgets": ["1595303526913-c7037797ebe7", "1575318634028-6a0cfcb60c59",
                "1702390740712-ce6daf1673be", "1612093991429-acd0fc7b1804",
                "1595161397851-cb282659df5e", "1605436247078-f0ef43ee8d5c"],
    "decoração": ["1691957713140-a9a042252202", "1672343385650-8d5bb804580a",
                  "1746458538063-8afc4d7d8619", "1662661600572-5968e350d394",
                  "1657026947006-a7663dbe4cd4"],
    "jogos & tabuleiro": ["1611891487122-207579d67d98", "1549056572-75914d5d5fd4",
                          "1506954673998-b077f05b13c7", "1642284474435-aba7be889406",
                          "1635921481467-fba710b8e65c", "1659480142156-212863498632"],
}
# aliases p/ categorias do seed antigo
_FOTOS["vasos"] = _FOTOS["vasos & plantas"]
_FOTOS["utensílios"] = _FOTOS["gadgets"]
_FOTOS["utensilios"] = _FOTOS["gadgets"]
_FOTOS["cosplay & props"] = _FOTOS["action figures"]
_FOTOS["_default"] = _FOTOS["articulados"]


def _ids(categoria: str) -> list[str]:
    return _FOTOS.get((categoria or "").strip().lower(), _FOTOS["_default"])


def url_curada(categoria: str, indice: int) -> str:
    """URL de uma foto real Unsplash relevante para a categoria (cicla pela lista)."""
    ids = _ids(categoria)
    pid = ids[indice % len(ids)]
    return f"https://images.unsplash.com/photo-{pid}?w=900&q=80&auto=format&fit=crop"


def baixar(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (Unsplash CDN)
        return r.read()


def padronizar_foto(foto_bytes: bytes, accent: str = "#2FA84F", tamanho: int = 800) -> bytes:
    """Aplica o tratamento padrão da loja a uma foto real: recorte quadrado,
    moldura de acento e selo L3D Labz — deixando todo o catálogo coeso."""
    im = Image.open(io.BytesIO(foto_bytes)).convert("RGB")

    # cover-crop central -> quadrado
    w, h = im.size
    lado = min(w, h)
    esq, topo = (w - lado) // 2, (h - lado) // 2
    im = im.crop((esq, topo, esq + lado, topo + lado)).resize((tamanho, tamanho), Image.LANCZOS)

    acc = _rgb(accent)

    # gradiente sutil no rodapé (legibilidade do selo)
    grad = np.zeros((tamanho, tamanho), dtype="uint8")
    ramp = np.clip((np.arange(tamanho) - tamanho * 0.66) / (tamanho * 0.34), 0, 1)
    grad[:] = (ramp * 165).astype("uint8")[:, None]
    sombra = Image.fromarray(grad, "L")
    base = Image.new("RGBA", (tamanho, tamanho), (10, 18, 13, 0))
    base.putalpha(sombra)
    im = Image.alpha_composite(im.convert("RGBA"), base).convert("RGB")

    draw = ImageDraw.Draw(im)
    # selo L3D Labz (pílula no canto inferior esquerdo)
    f = _fonte(int(tamanho * 0.042), bold=True)
    txt = "L3D Labz"
    tw = draw.textlength(txt, font=f)
    pad = int(tamanho * 0.035)
    bh = int(tamanho * 0.082)
    by1 = tamanho - pad
    draw.rounded_rectangle(
        [pad, by1 - bh, pad + tw + int(tamanho * 0.07), by1],
        radius=int(bh * 0.5), fill=acc,
    )
    draw.text((pad + int(tamanho * 0.035), by1 - bh + int(bh * 0.22)), txt, font=f, fill=(255, 255, 255))

    # moldura fina de acento
    draw.rectangle([0, 0, tamanho - 1, tamanho - 1], outline=acc, width=5)

    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=86)
    return buf.getvalue()
