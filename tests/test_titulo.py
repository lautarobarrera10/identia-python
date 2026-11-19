import pytest
from bs4 import BeautifulSoup

from identia_python.titulo import (
    EXTRACTORES_TITULO,
    ExtractorTitulo,
    TituloDesdeH1,
    obtener_titulo,
)


class TituloDesdeTwitter(ExtractorTitulo):
    """Fuente nueva agregada sin modificar titulo.py."""

    def extraer(self, soup: BeautifulSoup) -> str | None:
        meta = soup.find("meta", attrs={"name": "twitter:title"})
        return str(meta["content"]) if meta else None


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


def test_sin_extractores_devuelve_none() -> None:
    assert obtener_titulo(_soup(HTML), []) is None


def test_no_se_puede_instanciar_la_abstraccion() -> None:
    with pytest.raises(TypeError):
        ExtractorTitulo()  # type: ignore[abstract]
