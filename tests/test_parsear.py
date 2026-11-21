import logging
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


def test_selector_especifico_de_urgente24(leer_fixture: Callable[[str], str]) -> None:
    html = leer_fixture("articulo_urgente24.html")

    articulo = parsear_articulo(html, "https://urgente24.com/dinero/nota-n1")

    assert articulo.titulo == "Título de la noticia en Urgente24"
    assert articulo.primer_parrafo == (
        "La bajada de la noticia, que aparece en un div antes del cuerpo."
    )


def test_selector_especifico_de_cronista(leer_fixture: Callable[[str], str]) -> None:
    html = leer_fixture("articulo_cronista.html")

    articulo = parsear_articulo(html, "https://www.cronista.com/economia/nota/")

    assert articulo.titulo == "Título de la noticia en El Cronista"
    assert articulo.primer_parrafo == (
        "La bajada de la noticia, que aparece en un h2 debajo del título."
    )


def test_selector_especifico_de_pagina12(leer_fixture: Callable[[str], str]) -> None:
    html = leer_fixture("articulo_pagina12.html")

    articulo = parsear_articulo(html, "https://www.pagina12.com.ar/2026/01/24/nota/")

    assert articulo.titulo == "Título de la noticia en Página/12"
    assert articulo.primer_parrafo == (
        "La bajada de la noticia, que aparece en un h3 debajo del título."
    )


def test_selector_especifico_de_lanacion(leer_fixture: Callable[[str], str]) -> None:
    html = leer_fixture("articulo_lanacion.html")

    articulo = parsear_articulo(html, "https://www.lanacion.com.ar/el-mundo/nota-nid1/")

    assert articulo.titulo == "Título de la noticia en La Nación"
    assert articulo.primer_parrafo == (
        "La bajada de la noticia, que aparece en un h2 debajo del título."
    )


def test_h1_dentro_de_enlaces_no_es_el_titulo(
    leer_fixture: Callable[[str], str],
) -> None:
    html = leer_fixture("articulo_abogados.html")

    articulo = parsear_articulo(html, "https://abogados.com.ar/index.php/nota/1")

    assert articulo.titulo == "Título de la noticia en Abogados"
    assert articulo.primer_parrafo == (
        "El primer párrafo de la noticia, que tiene texto suficiente."
    )


def test_selector_de_infobae_no_aplica_a_otros_dominios(
    leer_fixture: Callable[[str], str],
) -> None:
    html = leer_fixture("articulo_infobae.html")

    articulo = parsear_articulo(html, "https://noinfobae.com/nota")

    assert articulo.primer_parrafo.startswith("Primer párrafo del cuerpo")


def test_selector_especifico_de_clarin_une_items_con_salto_de_linea(
    leer_fixture: Callable[[str], str],
) -> None:
    html = leer_fixture("articulo_clarin.html")

    articulo = parsear_articulo(html, "https://www.clarin.com/politica/nota.html")

    assert articulo.titulo == "Título de la noticia en Clarín"
    assert articulo.primer_parrafo == (
        "Primer ítem de la bajada, con negrita.\nSegundo ítem de la bajada."
    )


def test_bajada_de_clarin_sin_lista() -> None:
    html = (
        "<html><body><h1>Título</h1>"
        '<h2 class="storySummary">Bajada   en texto plano.</h2></body></html>'
    )

    articulo = parsear_articulo(html, "https://www.clarin.com/nota.html")

    assert articulo.primer_parrafo == "Bajada en texto plano."


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


def test_loguea_warning_antes_de_fallar(caplog: pytest.LogCaptureFixture) -> None:
    with pytest.raises(ParseoHtmlError):
        parsear_articulo("<html><body></body></html>", "https://x.com")

    assert [(r.levelno, r.getMessage()) for r in caplog.records] == [
        (
            logging.WARNING,
            "No se pudo obtener el título ni el primer párrafo en https://x.com",
        )
    ]


def test_loguea_fuente_del_titulo_en_debug(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="identia_python")
    html = (
        "<html><head><title>T</title></head>"
        "<body><p>Un párrafo suficientemente largo para superar el mínimo.</p></body>"
        "</html>"
    )

    parsear_articulo(html, "https://x.com")

    assert "Título obtenido de <title>" in caplog.text


def test_selector_sin_resultado_usa_parrafo_generico(
    leer_fixture: Callable[[str], str],
) -> None:
    html = leer_fixture("articulo_generico.html")

    articulo = parsear_articulo(html, "https://www.infobae.com/nota/")

    assert articulo.primer_parrafo.startswith("Este es el primer párrafo")
