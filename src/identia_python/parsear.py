"""
Parsear el html de una página para obtener el título y el primer párrafo
"""

import logging

from bs4 import BeautifulSoup

from identia_python.exceptions import ParseoHtmlError
from identia_python.modelos import Articulo
from identia_python.primer_parrafo import obtener_primer_parrafo
from identia_python.titulo import obtener_titulo

logger = logging.getLogger(__name__)


def parsear_articulo(html: str, url: str) -> Articulo:
    """Parsea el html y devuelve el título y el primer párrafo."""
    soup = BeautifulSoup(html, "lxml")
    titulo = obtener_titulo(soup)
    parrafo = obtener_primer_parrafo(soup, url)

    if not titulo or not parrafo:
        faltantes = [
            nombre
            for nombre, valor in (("el título", titulo), ("el primer párrafo", parrafo))
            if not valor
        ]
        mensaje = f"No se pudo obtener {' ni '.join(faltantes)}"
        logger.warning("%s en %s", mensaje, url)
        raise ParseoHtmlError(mensaje)

    return Articulo(titulo=titulo, primer_parrafo=parrafo)
