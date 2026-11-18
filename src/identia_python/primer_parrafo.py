"""
Obtención del primer párrafo (o la bajada) de una noticia.
"""

import logging

from bs4 import BeautifulSoup, Tag

from identia_python.selectores import selector_para_url
from identia_python.texto_html import texto_de_bajada, texto_normalizado

logger = logging.getLogger(__name__)

MIN_LARGO_PARRAFO = 40


def _parrafo_por_selector(soup: BeautifulSoup, url: str) -> str | None:
    """Texto del elemento indicado por el selector del sitio, si existe."""
    selector = selector_para_url(url)
    if not selector:
        return None
    etiqueta, clase = selector
    elemento = soup.find(etiqueta, class_=clase)
    if isinstance(elemento, Tag):
        texto = texto_de_bajada(elemento)
        if texto:
            logger.debug("Párrafo obtenido con el selector %s.%s", etiqueta, clase)
            return texto
    logger.debug("El selector %s.%s no encontró texto", etiqueta, clase)
    return None


def _primer_parrafo_significativo(soup: BeautifulSoup, min_largo: int) -> str | None:
    """Primer <p> con texto suficiente, dentro de <article> si existe."""
    contenedor = soup.find("article") or soup
    for p in contenedor.find_all("p"):
        texto = texto_normalizado(p)
        if len(texto) >= min_largo:
            logger.debug("Párrafo obtenido del primer <p> significativo")
            return texto
    return None


def obtener_primer_parrafo(
    soup: BeautifulSoup, url: str, min_largo: int = MIN_LARGO_PARRAFO
) -> str | None:
    """
    Si el sitio de la url tiene un selector específico y el elemento existe,
    devuelve su texto. Si no, devuelve el primer <p> con texto significativo,
    buscando dentro de <article> si existe para evitar menús y footers.
    """
    return _parrafo_por_selector(soup, url) or _primer_parrafo_significativo(
        soup, min_largo
    )
