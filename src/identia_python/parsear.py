"""
Parsear el html de una página para obtener el título y el primer párrafo
"""

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from identia_python.exceptions import ParseoHtmlError

logger = logging.getLogger(__name__)


@dataclass
class Articulo:
    titulo: str
    primer_parrafo: str


def _obtener_titulo(soup: BeautifulSoup) -> str | None:
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


# Sitios que no usan el primer <p> como bajada: dominio -> (etiqueta, clase CSS)
SELECTORES_POR_SITIO: dict[str, tuple[str, str]] = {
    "infobae.com": ("h2", "article-subheadline"),
    "clarin.com": ("h2", "storySummary"),
}


def _texto_normalizado(elemento: Tag) -> str:
    """Texto del elemento con los espacios y saltos de línea normalizados."""
    # Sin separador para no meter espacios antes de la puntuación en <b>, <a>, etc.
    return " ".join(elemento.get_text().split())


def _texto_de_bajada(elemento: Tag) -> str:
    """
    Texto de la bajada. Si viene como lista (p. ej. Clarín usa <ul><li>),
    devuelve un ítem por línea para que no queden pegados.
    """
    items = [_texto_normalizado(li) for li in elemento.find_all("li")]
    items = [item for item in items if item]
    if items:
        return "\n".join(items)
    return _texto_normalizado(elemento)


def _selector_para_url(url: str) -> tuple[str, str] | None:
    """Devuelve el selector del sitio de la url, o None si no hay uno específico."""
    host = (urlparse(url).hostname or "").lower()
    for sitio, selector in SELECTORES_POR_SITIO.items():
        if host == sitio or host.endswith("." + sitio):
            return selector
    return None


def _obtener_primer_parrafo(
    soup: BeautifulSoup, url: str, min_largo: int = 40
) -> str | None:
    """
    Si el sitio de la url tiene un selector específico y el elemento existe,
    devuelve su texto. Si no, devuelve el primer <p> con texto significativo,
    buscando dentro de <article> si existe para evitar menús y footers.
    """
    selector = _selector_para_url(url)
    if selector:
        etiqueta, clase = selector
        elemento = soup.find(etiqueta, class_=clase)
        if isinstance(elemento, Tag):
            texto = _texto_de_bajada(elemento)
            if texto:
                logger.debug("Párrafo obtenido con el selector %s.%s", etiqueta, clase)
                return texto
        logger.debug("El selector %s.%s no encontró texto", etiqueta, clase)

    contenedor = soup.find("article") or soup
    for p in contenedor.find_all("p"):
        texto = _texto_normalizado(p)
        if len(texto) >= min_largo:
            logger.debug("Párrafo obtenido del primer <p> significativo")
            return texto
    return None


def parsear_articulo(html: str, url: str) -> Articulo:
    """Parsea el html y devuelve el título y el primer párrafo."""
    soup = BeautifulSoup(html, "lxml")
    titulo = _obtener_titulo(soup)
    parrafo = _obtener_primer_parrafo(soup, url)

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
