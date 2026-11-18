"""
Obtención del título de una noticia.
"""

import logging

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def obtener_titulo(soup: BeautifulSoup) -> str | None:
    """Busca el título en <h1>, luego en og:title y por último en <title>."""
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        logger.debug("Título obtenido de <h1>")
        return h1.get_text(" ", strip=True)

    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        logger.debug("Título obtenido de og:title")
        return str(og["content"]).strip()

    if soup.title and soup.title.string:
        logger.debug("Título obtenido de <title>")
        return soup.title.string.strip()

    return None
