"""
Descarga noticias y extrae su título y primer párrafo.
"""

from .descargar import descargar_html
from .exceptions import DescargaHtmlError, ParseoHtmlError
from .leer_urls import leer_urls
from .parsear import Articulo, parsear_articulo

__all__ = [
    "Articulo",
    "DescargaHtmlError",
    "ParseoHtmlError",
    "descargar_html",
    "leer_urls",
    "parsear_articulo",
]
