"""Descarga, optimiza e incrusta las fotografías de la presentación.

Uso:  python build/fotos.py

Todas las fotos son de dominio público (CC0), encontradas con Openverse.
Se redimensionan con Pillow, se comprimen a JPEG y se incrustan como data URI
en index.html, en cada <img src="..." data-foto="nombre">.
"""
from __future__ import annotations

import base64
import io
import re
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
HTML = RAIZ / "index.html"

# nombre: (url de origen, ancho final en px, fuente)
FOTOS = {
    "portada": ("https://images.rawpixel.com/editor_1024/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDIyLTExL2ZsNDk3OTgwOTA2MjctaW1hZ2UuanBn.jpg", 1400, "rawpixel · CC0"),
    "tarimas": ("https://images.rawpixel.com/image_1300/czNmcy1wcml2YXRlL3Jhd3BpeGVsX2ltYWdlcy93ZWJzaXRlX2NvbnRlbnQvbHIvZmw0NzcyMjQ2MTM0LWltYWdlLWt1N3o5cjJkLmpwZw.jpg", 1000, "rawpixel · CC0"),
    "analisis": ("https://cdn.stocksnap.io/img-thumbs/960w/PHE63L27S6.jpg", 900, "StockSnap · CC0"),
    "cajas-super": ("https://images.rawpixel.com/editor_1024/czNmcy1wcml2YXRlL3Jhd3BpeGVsX2ltYWdlcy93ZWJzaXRlX2NvbnRlbnQvbHIvZmw0MzA5MTk4NDEyNS1pbWFnZS1rdHdtemE0ay5qcGc.jpg", 1000, "rawpixel · CC0"),
    "navidad": ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Inside_the_Milton_Keynes_Shopping_Mall_on_Christmas_Eve.jpg/1280px-Inside_the_Milton_Keynes_Shopping_Mall_on_Christmas_Eve.jpg", 1400, "Wikimedia Commons · CC0"),
    "pasillo": ("https://images.rawpixel.com/editor_1024/czNmcy1wcml2YXRlL3Jhd3BpeGVsX2ltYWdlcy93ZWJzaXRlX2NvbnRlbnQvbHIvcHg5MTc4MDQtaW1hZ2Uta3d5bzF0dmQuanBn.jpg", 1400, "rawpixel · CC0"),
    "carritos": ("https://images.rawpixel.com/editor_1024/czNmcy1wcml2YXRlL3Jhd3BpeGVsX2ltYWdlcy93ZWJzaXRlX2NvbnRlbnQvbHIvLWEwMTAtbWFya3Vzcy0wNTI0LmpwZw.jpg", 1400, "rawpixel · CC0"),
    "calculadora": ("https://images.rawpixel.com/editor_1024/czNmcy1wcml2YXRlL3Jhd3BpeGVsX2ltYWdlcy93ZWJzaXRlX2NvbnRlbnQvbHIvcHgxMTA5OTI4LWltYWdlLWt3dnc5cGM1LmpwZw.jpg", 1400, "rawpixel · CC0"),
    "bodega": ("https://images.rawpixel.com/editor_1024/cHJpdmF0ZS9sci9pbWFnZXMvd2Vic2l0ZS8yMDIyLTExL2ZsNTE3MjI5OTE1ODQtaW1hZ2UuanBn.jpg", 1400, "rawpixel · CC0"),
    "tienda": ("https://cdn.stocksnap.io/img-thumbs/960w/I93PW8NE0F.jpg", 1200, "StockSnap · CC0"),
    "reunion": ("https://cdn.stocksnap.io/img-thumbs/960w/IS1XRUWYW4.jpg", 1200, "StockSnap · CC0"),
    "papeles": ("https://cdn.stocksnap.io/img-thumbs/960w/Y01VDYAX63.jpg", 1200, "StockSnap · CC0"),
    "equipo": ("https://cdn.stocksnap.io/img-thumbs/960w/Q1OSKR7D42.jpg", 1200, "StockSnap · CC0"),
    "ropa": ("https://cdn.stocksnap.io/img-thumbs/960w/KJ9ZK1L8WS.jpg", 1200, "StockSnap · CC0"),
    "acuerdo": ("https://images.rawpixel.com/editor_1024/czNmcy1wcml2YXRlL3Jhd3BpeGVsX2ltYWdlcy93ZWJzaXRlX2NvbnRlbnQvbHIvbnMxODI3Ni1pbWFnZS1rd3Z5YzFvei5qcGc.jpg", 1200, "rawpixel · CC0"),
    "bolsa": ("https://images.rawpixel.com/editor_1024/czNmcy1wcml2YXRlL3Jhd3BpeGVsX2ltYWdlcy93ZWJzaXRlX2NvbnRlbnQvbHIvbnMxODE5LWltYWdlLWt3dnduMWU2LmpwZw.jpg", 1200, "rawpixel · CC0"),
    "mesa": ("https://cdn.stocksnap.io/img-thumbs/960w/VQXYE2ZEHC.jpg", 1200, "StockSnap · CC0"),
    "analista": ("https://cdn.stocksnap.io/img-thumbs/960w/DC7JUJKYTQ.jpg", 1200, "StockSnap · CC0"),
    "boutique": ("https://cdn.stocksnap.io/img-thumbs/960w/ZN97ZIF3ZU.jpg", 1200, "StockSnap · CC0"),
    "decision": ("https://cdn.stocksnap.io/img-thumbs/960w/V8NHXQVQ70.jpg", 1200, "StockSnap · CC0"),
    "libreta": ("https://cdn.stocksnap.io/img-thumbs/960w/JBW2PXDOL6.jpg", 1200, "StockSnap · CC0"),
}


def descargar(url: str) -> Image.Image:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (presentacion-escolar)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return ImageOps.exif_transpose(Image.open(io.BytesIO(r.read()))).convert("RGB")


def gradacion(im: Image.Image) -> Image.Image:
    """Un mismo look para todas: contraste suave, sombras azul marino, luces cálidas."""
    from PIL import ImageEnhance
    im = ImageEnhance.Color(im).enhance(0.82)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    gris = ImageOps.grayscale(im)
    tono = ImageOps.colorize(gris, black="#0A1226", mid="#5E6C8E", white="#FFF1DC")
    return Image.blend(im, tono, 0.38)


def a_data_uri(im: Image.Image, ancho: int) -> str:
    im = gradacion(im)
    if im.width > ancho:
        im = im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=74, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


html = HTML.read_text(encoding="utf-8")
total = 0
for nombre, (url, ancho, fuente) in FOTOS.items():
    uri = a_data_uri(descargar(url), ancho)
    html, n = re.subn(rf'src="[^"]*"( data-foto="{re.escape(nombre)}")', lambda m: f'src="{uri}"{m.group(1)}', html)
    total += len(uri)
    print(f"{nombre:12} {len(uri) // 1024:5} KB  x{n}  ({fuente})")
HTML.write_text(html, encoding="utf-8")
print(f"Total incrustado: {total // 1024} KB")
