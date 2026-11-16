"""
Parsear el html de una página para obtener el título y el primer párrafo
"""

from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from identia_python.exception import ParseoHtmlError


@dataclass
class Articulo:
    titulo: str
    primer_parrafo: str


def _obtener_titulo(soup: BeautifulSoup) -> str | None:
    """Busca el título en <h1>, luego en og:title y por último en <title>."""
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(" ", strip=True)

    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return str(og["content"]).strip()

    if soup.title and soup.title.string:
        return soup.title.string.strip()

    return None


# Sitios que no usan el primer <p> como bajada: dominio -> qué buscar con soup.find()
SELECTORES_POR_SITIO: dict[str, dict[str, str]] = {
    "infobae.com": {"name": "h2", "class_": "article-subheadline"},
}


def _selector_para_url(url: str) -> dict[str, str] | None:
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
        elemento = soup.find(**selector)
        if elemento:
            texto = " ".join(elemento.get_text().split())
            if texto:
                return texto

    contenedor = soup.find("article") or soup
    for p in contenedor.find_all("p"):
        # Sin separador para no meter espacios antes de la puntuación en <b>, <a>, etc.;
        # luego se normalizan los espacios/saltos de línea.
        texto = " ".join(p.get_text().split())
        if len(texto) >= min_largo:
            return texto
    return None


def parsear_articulo(html: str, url: str) -> Articulo:
    """Parsea el html y devuelve el título y el primer párrafo."""
    soup = BeautifulSoup(html, "lxml")
    titulo = _obtener_titulo(soup)
    parrafo = _obtener_primer_parrafo(soup, url)

    if not titulo or not parrafo:
        raise ParseoHtmlError(
            f"No se pudo obtener {'el título' if not titulo else 'el primer párrafo'}"
        )

    return Articulo(titulo=titulo, primer_parrafo=parrafo)
