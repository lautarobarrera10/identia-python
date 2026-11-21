"""
Nombre del medio al que pertenece una noticia, a partir de su url.
"""

from urllib.parse import urlparse

# Dominio -> nombre con el que se muestra el medio
NOMBRES_POR_SITIO: dict[str, str] = {
    "infobae.com": "Infobae",
    "clarin.com": "Clarín",
    "urgente24.com": "Urgente24",
    "cronista.com": "El Cronista",
    "pagina12.com.ar": "Página/12",
    "lanacion.com.ar": "La Nación",
    "abogados.com.ar": "Abogados.com.ar",
}


def nombre_medio(url: str) -> str:
    """
    Devuelve el nombre del medio de la url. Si el sitio no es conocido, usa
    el dominio sin "www.".
    """
    host = (urlparse(url).hostname or "").lower()
    for sitio, nombre in NOMBRES_POR_SITIO.items():
        if host == sitio or host.endswith("." + sitio):
            return nombre
    return host.removeprefix("www.") or url
