"""
Descargar el html de una url
"""

import httpx

from identia_python.exception import DescargaHtmlError


def descargar_html(url: str) -> str:
    """
    Descarga el html de una url y lo devuelve como un string
    """
    r = httpx.get(url)

    if r.status_code == 200:
        return r.text

    raise DescargaHtmlError(
        f"Error al descargar la url: {url}, status code: {r.status_code}"
    )
