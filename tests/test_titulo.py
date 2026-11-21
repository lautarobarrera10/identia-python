import pytest
from bs4 import BeautifulSoup
from dobles import TituloDesdeTwitter

from identia_python.titulo import (
    EXTRACTORES_TITULO,
    ExtractorTitulo,
    TituloDesdeH1,
    TituloDesdeTitle,
    obtener_titulo,
)

HTML = (
    '<html><head><meta name="twitter:title" content="Desde Twitter">'
    "<title>Desde title</title></head><body><h1>Desde h1</h1></body></html>"
)


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def test_extractor_nuevo_se_usa_sin_modificar_el_modulo() -> None:
    extractores = [TituloDesdeTwitter(), *EXTRACTORES_TITULO]

    assert obtener_titulo(_soup(HTML), extractores) == "Desde Twitter"


def test_respeta_el_orden_de_prioridad() -> None:
    extractores = [TituloDesdeH1(), TituloDesdeTwitter()]

    assert obtener_titulo(_soup(HTML), extractores) == "Desde h1"


def test_sigue_con_el_siguiente_si_uno_no_encuentra() -> None:
    html = '<html><head><meta name="twitter:title" content="T"></head></html>'

    assert obtener_titulo(_soup(html), [TituloDesdeH1(), TituloDesdeTwitter()]) == "T"


def test_h1_dentro_de_un_enlace_se_ignora() -> None:
    html = '<body><a href="/otra"><h1>Otra nota</h1></a><h1>La nota</h1></body>'

    assert TituloDesdeH1().extraer(_soup(html)) == "La nota"


def test_si_todos_los_h1_son_enlaces_no_hay_titulo_de_h1() -> None:
    html = '<body><a href="/otra"><h1>Otra nota</h1></a></body>'

    assert TituloDesdeH1().extraer(_soup(html)) is None


def test_title_solo_con_espacios_no_es_un_titulo() -> None:
    html = "<html><head><title>   </title></head><body></body></html>"

    assert obtener_titulo(_soup(html)) is None


def test_og_title_se_normaliza() -> None:
    html = '<html><head><meta property="og:title" content="  Un   título "></head>'

    assert obtener_titulo(_soup(html)) == "Un título"


def test_title_con_saltos_de_linea_se_normaliza() -> None:
    html = "<title>\n  Un\n  título\n</title>"

    assert TituloDesdeTitle().extraer(_soup(html)) == "Un título"


def test_sin_extractores_devuelve_none() -> None:
    assert obtener_titulo(_soup(HTML), []) is None


def test_no_se_puede_instanciar_la_abstraccion() -> None:
    with pytest.raises(TypeError):
        ExtractorTitulo()  # type: ignore[abstract]
