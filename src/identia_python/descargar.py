"""
Descargar el html de una url
"""

import httpx

from identia_python.exceptions import DescargaHtmlError

TIMEOUT_SEGUNDOS = 15
HEADERS = {
    # Algunos medios bloquean pedidos sin un User-Agent de navegador
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
}


def descargar_html(url: str) -> str:
    """
    Descarga el html de una url y lo devuelve como un string.
    Sigue redirecciones. Lanza DescargaHtmlError si la respuesta no es exitosa
    o si ocurre un error de red.
    """
    try:
        r = httpx.get(
            url, follow_redirects=True, timeout=TIMEOUT_SEGUNDOS, headers=HEADERS
        )
    except httpx.HTTPError as e:
        raise DescargaHtmlError(
            f"Error de red al descargar la url: {url} ({type(e).__name__}: {e})"
        ) from e

    if r.is_success:
        return r.text

    raise DescargaHtmlError(
        f"Error al descargar la url: {url}, status code: {r.status_code}"
    )
