"""
Descarga noticias y extrae su título y primer párrafo.
"""

import logging

from .descargar import descargar_html
from .exceptions import DescargaHtmlError, ParseoHtmlError
from .leer_urls import leer_urls
from .modelos import Articulo
from .parsear import parsear_articulo

__all__ = [
    "Articulo",
    "DescargaHtmlError",
    "ParseoHtmlError",
    "descargar_html",
    "leer_urls",
    "parsear_articulo",
]

# Una librería no configura logging: si la app no lo hace, no se emite nada.
logging.getLogger(__name__).addHandler(logging.NullHandler())
