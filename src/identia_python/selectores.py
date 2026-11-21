"""
Selectores específicos por sitio para encontrar la bajada de una noticia.
"""

from urllib.parse import urlparse

# Sitios que no usan el primer <p> como bajada: dominio -> (etiqueta, clase CSS)
SELECTORES_POR_SITIO: dict[str, tuple[str, str]] = {
    "infobae.com": ("h2", "article-subheadline"),
    "clarin.com": ("h2", "storySummary"),
    "urgente24.com": ("div", "article-sub-title-p"),
    "cronista.com": ("h2", "article-head__subtitle"),
    "pagina12.com.ar": ("h3", "p12Header"),
    "lanacion.com.ar": ("h2", "--bajada"),
}


def selector_para_url(url: str) -> tuple[str, str] | None:
    """Devuelve el selector del sitio de la url, o None si no hay uno específico."""
    host = (urlparse(url).hostname or "").lower()
    for sitio, selector in SELECTORES_POR_SITIO.items():
        if host == sitio or host.endswith("." + sitio):
            return selector
    return None
