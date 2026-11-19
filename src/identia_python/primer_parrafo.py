"""
Obtención del primer párrafo (o la bajada) de una noticia.

Cada forma de encontrar la bajada es un ExtractorParrafo. Para agregar una
nueva se crea otra subclase y se la pasa en la lista de extractores, sin
modificar obtener_primer_parrafo (principio Open/Closed).
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence

from bs4 import BeautifulSoup, Tag

from identia_python.selectores import selector_para_url
from identia_python.texto_html import texto_de_bajada, texto_normalizado

logger = logging.getLogger(__name__)

MIN_LARGO_PARRAFO = 40


class ExtractorParrafo(ABC):
    """Estrategia para obtener la bajada de una noticia a partir del html."""

    @abstractmethod
    def extraer(self, soup: BeautifulSoup, url: str) -> str | None:
        """Devuelve el párrafo, o None si esta estrategia no lo encuentra."""


class ParrafoPorSelectorDeSitio(ExtractorParrafo):
    """Texto del elemento indicado por el selector del sitio, si existe."""

    def extraer(self, soup: BeautifulSoup, url: str) -> str | None:
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


class PrimerParrafoSignificativo(ExtractorParrafo):
    """Primer <p> con texto suficiente, dentro de <article> si existe."""

    def __init__(self, min_largo: int = MIN_LARGO_PARRAFO) -> None:
        self.min_largo = min_largo

    def extraer(self, soup: BeautifulSoup, url: str) -> str | None:
        contenedor = soup.find("article") or soup
        for p in contenedor.find_all("p"):
            texto = texto_normalizado(p)
            if len(texto) >= self.min_largo:
                logger.debug("Párrafo obtenido del primer <p> significativo")
                return texto
        return None


def extractores_por_defecto(
    min_largo: int = MIN_LARGO_PARRAFO,
) -> list[ExtractorParrafo]:
    """Selector específico del sitio y, si no hay, el primer <p> significativo."""
    return [ParrafoPorSelectorDeSitio(), PrimerParrafoSignificativo(min_largo)]


def obtener_primer_parrafo(
    soup: BeautifulSoup,
    url: str,
    min_largo: int = MIN_LARGO_PARRAFO,
    extractores: Sequence[ExtractorParrafo] | None = None,
) -> str | None:
    """
    Devuelve el párrafo del primer extractor que lo encuentre. Por defecto:
    si el sitio de la url tiene un selector específico y el elemento existe,
    su texto; si no, el primer <p> con texto significativo, buscando dentro
    de <article> si existe para evitar menús y footers.
    """
    if extractores is None:
        extractores = extractores_por_defecto(min_largo)
    for extractor in extractores:
        parrafo = extractor.extraer(soup, url)
        if parrafo:
            return parrafo
    return None
