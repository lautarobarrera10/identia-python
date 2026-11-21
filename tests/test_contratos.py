"""
Tests de contrato (principio de sustitución de Liskov).

Cada abstracción define un contrato en su docstring. Estos tests lo verifican
para TODAS las implementaciones, así cualquiera puede reemplazar a otra sin
que el código cliente lo note. Una subclase nueva se suma a la lista de
parametrización correspondiente y tiene que pasar los mismos tests.
"""

import asyncio

import pytest
from bs4 import BeautifulSoup
from dobles import (
    ClienteFalso,
    ParrafoDesdeResumen,
    TituloDesdeTwitter,
)

from identia_python import procesamiento
from identia_python.descargar import ClienteHttp
from identia_python.exceptions import DescargaHtmlError, IdentiaError, ParseoHtmlError
from identia_python.modelos import Articulo
from identia_python.primer_parrafo import (
    ExtractorParrafo,
    ParrafoPorSelectorDeSitio,
    PrimerParrafoSignificativo,
)
from identia_python.titulo import (
    ExtractorTitulo,
    TituloDesdeH1,
    TituloDesdeOgTitle,
    TituloDesdeTitle,
)

# --- Extractores --------------------------------------------------------------

EXTRACTORES_TITULO: list[ExtractorTitulo] = [
    TituloDesdeH1(),
    TituloDesdeOgTitle(),
    TituloDesdeTitle(),
    TituloDesdeTwitter(),
]

EXTRACTORES_PARRAFO: list[ExtractorParrafo] = [
    ParrafoPorSelectorDeSitio(),
    PrimerParrafoSignificativo(),
    PrimerParrafoSignificativo(min_largo=0),
    ParrafoDesdeResumen(),
]

# HTML con casos borde: vacío, sin las etiquetas buscadas, etiquetas solo con
# espacios, atributos faltantes y texto con espacios de más.
HTMLS = {
    "vacio": "",
    "sin_etiquetas": "<html><body><div>nada</div></body></html>",
    "solo_espacios": (
        "<html><head><title>  \n </title>"
        '<meta property="og:title" content="   ">'
        '<meta name="twitter:title" content=" "></head>'
        '<body><h1>  </h1><h2 class="article-subheadline"> </h2>'
        '<h2 class="storySummary"><ul><li> </li></ul></h2>'
        '<div class="resumen">  </div><p>   </p></body></html>'
    ),
    "sin_atributos": (
        '<html><head><meta property="og:title"><meta name="twitter:title">'
        "</head></html>"
    ),
    "con_texto": (
        "<html><head><title> Un \n título </title>"
        '<meta property="og:title" content="  Un   título ">'
        '<meta name="twitter:title" content="Un  título"></head>'
        "<body><h1> Un <b>título</b> </h1>"
        '<h2 class="article-subheadline">  Una   bajada </h2>'
        '<h2 class="storySummary"><ul><li> Uno </li><li>  </li><li>Dos</li></ul></h2>'
        '<div class="resumen"> Un   resumen </div>'
        "<article><p> Un párrafo   suficientemente largo para superar el mínimo. </p>"
        "</article></body></html>"
    ),
}

URLS = [
    "https://www.infobae.com/nota",
    "https://www.clarin.com/nota",
    "https://sitio-desconocido.com/nota",
    "no es una url",
    "",
]


def _cumple_contrato_de_texto(resultado: object) -> None:
    """None, o texto no vacío con cada línea no vacía y normalizada."""
    if resultado is None:
        return
    assert isinstance(resultado, str)
    assert resultado != ""
    for linea in resultado.split("\n"):
        assert linea
        assert linea == " ".join(linea.split())


def _id(objeto: object) -> str:
    return type(objeto).__name__


@pytest.mark.parametrize("extractor", EXTRACTORES_TITULO, ids=_id)
@pytest.mark.parametrize("html", HTMLS.values(), ids=HTMLS.keys())
def test_extractor_titulo_cumple_el_contrato(
    extractor: ExtractorTitulo, html: str
) -> None:
    _cumple_contrato_de_texto(extractor.extraer(BeautifulSoup(html, "lxml")))


@pytest.mark.parametrize("extractor", EXTRACTORES_PARRAFO, ids=_id)
@pytest.mark.parametrize("html", HTMLS.values(), ids=HTMLS.keys())
@pytest.mark.parametrize("url", URLS)
def test_extractor_parrafo_cumple_el_contrato(
    extractor: ExtractorParrafo, html: str, url: str
) -> None:
    _cumple_contrato_de_texto(extractor.extraer(BeautifulSoup(html, "lxml"), url))


# --- Excepciones --------------------------------------------------------------


@pytest.mark.parametrize("error", [DescargaHtmlError, ParseoHtmlError])
def test_errores_propios_heredan_de_identia_error(error: type[Exception]) -> None:
    assert issubclass(error, IdentiaError)


class ErrorNuevo(IdentiaError):
    """Error agregado después: se maneja sin modificar procesamiento.py."""


@pytest.mark.parametrize("error", [DescargaHtmlError, ParseoHtmlError, ErrorNuevo])
def test_procesar_url_maneja_cualquier_identia_error(
    error: type[IdentiaError],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def descargar_que_falla(url: str, cliente: ClienteHttp) -> str:
        raise error("falló")

    monkeypatch.setattr(procesamiento, "descargar_html", descargar_que_falla)

    async def correr() -> Articulo | None:
        return await procesamiento.procesar_url(
            "https://a.com", 1, 1, ClienteFalso(), asyncio.Semaphore(1)
        )

    assert asyncio.run(correr()) is None
    # Se trata como error esperable, no como "Error inesperado"
    assert "falló" in caplog.text
    assert "inesperado" not in caplog.text
