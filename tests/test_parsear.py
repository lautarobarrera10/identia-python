from collections.abc import Callable

import pytest

from identia_python.exceptions import ParseoHtmlError
from identia_python.parsear import parsear_articulo


def test_articulo_generico(leer_fixture: Callable[[str], str]) -> None:
    html = leer_fixture("articulo_generico.html")

    articulo = parsear_articulo(html, "https://www.diario.com/nota")

    assert articulo.titulo == "El título principal de la noticia"
    assert articulo.primer_parrafo == (
        "Este es el primer párrafo significativo del artículo, "
        "con un enlace y saltos de línea."
    )


def test_selector_especifico_de_infobae(leer_fixture: Callable[[str], str]) -> None:
    html = leer_fixture("articulo_infobae.html")

    articulo = parsear_articulo(html, "https://www.infobae.com/economia/nota/")

    assert articulo.titulo == "Título de la noticia en Infobae"
    assert articulo.primer_parrafo == (
        "La bajada de la noticia, que aparece en un h2 en lugar de un párrafo."
    )


def test_selector_de_infobae_no_aplica_a_otros_dominios(
    leer_fixture: Callable[[str], str],
) -> None:
    html = leer_fixture("articulo_infobae.html")

    articulo = parsear_articulo(html, "https://noinfobae.com/nota")

    assert articulo.primer_parrafo.startswith("Primer párrafo del cuerpo")


def test_titulo_desde_og_title_si_no_hay_h1() -> None:
    html = (
        '<html><head><meta property="og:title" content="Título OG"></head>'
        "<body><p>Un párrafo suficientemente largo para superar el mínimo.</p></body>"
        "</html>"
    )

    assert parsear_articulo(html, "https://x.com").titulo == "Título OG"


def test_titulo_desde_title_como_ultimo_recurso() -> None:
    html = (
        "<html><head><title> Título de pestaña </title></head>"
        "<body><p>Un párrafo suficientemente largo para superar el mínimo.</p></body>"
        "</html>"
    )

    assert parsear_articulo(html, "https://x.com").titulo == "Título de pestaña"


def test_error_si_falta_el_parrafo() -> None:
    html = "<html><body><h1>Título</h1><p>Corto.</p></body></html>"

    with pytest.raises(ParseoHtmlError, match="^No se pudo obtener el primer párrafo$"):
        parsear_articulo(html, "https://x.com")


def test_error_si_faltan_ambos() -> None:
    html = "<html><body></body></html>"

    with pytest.raises(
        ParseoHtmlError, match="^No se pudo obtener el título ni el primer párrafo$"
    ):
        parsear_articulo(html, "https://x.com")
