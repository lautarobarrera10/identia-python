"""
Obtención del título de una noticia.

Cada fuente posible del título es un ExtractorTitulo. Para agregar una fuente
nueva se crea otra subclase y se la registra en EXTRACTORES_TITULO, sin
modificar obtener_titulo (principio Open/Closed).
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ExtractorTitulo(ABC):
    """Estrategia para obtener el título de una noticia a partir del html."""

    @abstractmethod
    def extraer(self, soup: BeautifulSoup) -> str | None:
        """Devuelve el título, o None si esta fuente no lo tiene."""


class TituloDesdeH1(ExtractorTitulo):
    def extraer(self, soup: BeautifulSoup) -> str | None:
        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            logger.debug("Título obtenido de <h1>")
            return h1.get_text(" ", strip=True)
        return None


class TituloDesdeOgTitle(ExtractorTitulo):
    def extraer(self, soup: BeautifulSoup) -> str | None:
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            logger.debug("Título obtenido de og:title")
            return str(og["content"]).strip()
        return None


class TituloDesdeTitle(ExtractorTitulo):
    def extraer(self, soup: BeautifulSoup) -> str | None:
        if soup.title and soup.title.string:
            logger.debug("Título obtenido de <title>")
            return soup.title.string.strip()
        return None


# En orden de prioridad
EXTRACTORES_TITULO: list[ExtractorTitulo] = [
    TituloDesdeH1(),
    TituloDesdeOgTitle(),
    TituloDesdeTitle(),
]


def obtener_titulo(
    soup: BeautifulSoup, extractores: Sequence[ExtractorTitulo] | None = None
) -> str | None:
    """
    Devuelve el título del primer extractor que lo encuentre. Por defecto busca
    en <h1>, luego en og:title y por último en <title>.
    """
    if extractores is None:
        extractores = EXTRACTORES_TITULO
    for extractor in extractores:
        titulo = extractor.extraer(soup)
        if titulo:
            return titulo
    return None
