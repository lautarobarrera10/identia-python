"""
Obtención del título de una noticia.

Cada fuente posible del título es un ExtractorTitulo. Para agregar una fuente
nueva se crea otra subclase y se la registra en EXTRACTORES_TITULO, sin
modificar obtener_titulo (principio Open/Closed).

Toda subclase cumple el contrato de ExtractorTitulo.extraer, así que cualquiera
puede reemplazar a otra sin que obtener_titulo lo note (principio de Liskov).
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence

from bs4 import BeautifulSoup

from identia_python.texto_html import texto_o_none

logger = logging.getLogger(__name__)


class ExtractorTitulo(ABC):
    """Estrategia para obtener el título de una noticia a partir del html."""

    @abstractmethod
    def extraer(self, soup: BeautifulSoup) -> str | None:
        """
        Devuelve el título, o None si esta fuente no lo tiene.

        Contrato que toda subclase debe respetar:
        - Precondición: acepta cualquier soup, aunque esté vacío o no tenga
          las etiquetas que busca.
        - Postcondición: devuelve un texto no vacío, sin espacios al principio
          ni al final y con los espacios internos normalizados, o None.
          Nunca devuelve "".
        - No lanza excepciones si falta la etiqueta o el atributo buscado.
        """


class TituloDesdeH1(ExtractorTitulo):
    """
    Primer <h1> que no esté dentro de un enlace. Algunos sitios (p. ej.
    abogados.com.ar) usan <a><h1>…</h1></a> en listados de otras notas, y ese
    texto no es el título de la página.
    """

    def extraer(self, soup: BeautifulSoup) -> str | None:
        for h1 in soup.find_all("h1"):
            if h1.find_parent("a") is not None:
                continue
            titulo = texto_o_none(h1.get_text(" "))
            if titulo is not None:
                logger.debug("Título obtenido de <h1>")
                return titulo
        return None


class TituloDesdeOgTitle(ExtractorTitulo):
    def extraer(self, soup: BeautifulSoup) -> str | None:
        og = soup.find("meta", property="og:title")
        contenido = og.get("content") if og else None
        titulo = texto_o_none(str(contenido)) if contenido is not None else None
        if titulo is not None:
            logger.debug("Título obtenido de og:title")
        return titulo


class TituloDesdeTitle(ExtractorTitulo):
    def extraer(self, soup: BeautifulSoup) -> str | None:
        titulo = texto_o_none(soup.title.get_text()) if soup.title else None
        if titulo is not None:
            logger.debug("Título obtenido de <title>")
        return titulo


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
        if titulo is not None:  # el contrato garantiza que no es ""
            return titulo
    return None
