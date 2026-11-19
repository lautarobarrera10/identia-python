import pytest
from bs4 import BeautifulSoup

from identia_python.primer_parrafo import (
    ExtractorParrafo,
    PrimerParrafoSignificativo,
    extractores_por_defecto,
    obtener_primer_parrafo,
)

HTML = (
    '<html><body><div class="resumen">Resumen propio del sitio.</div>'
    "<p>Un párrafo suficientemente largo para superar el mínimo.</p></body></html>"
)


class ParrafoDesdeResumen(ExtractorParrafo):
    """Estrategia nueva agregada sin modificar primer_parrafo.py."""

    def extraer(self, soup: BeautifulSoup, url: str) -> str | None:
        div = soup.find("div", class_="resumen")
        return div.get_text(strip=True) if div else None


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def test_extractor_nuevo_antepuesto_gana() -> None:
    extractores = [ParrafoDesdeResumen(), *extractores_por_defecto()]

    assert (
        obtener_primer_parrafo(_soup(HTML), "https://x.com", extractores=extractores)
        == "Resumen propio del sitio."
    )


def test_por_defecto_usa_el_primer_parrafo_significativo() -> None:
    assert obtener_primer_parrafo(_soup(HTML), "https://x.com").startswith("Un párrafo")


def test_min_largo_configurable() -> None:
    extractores = [PrimerParrafoSignificativo(min_largo=1000)]

    assert (
        obtener_primer_parrafo(_soup(HTML), "https://x.com", extractores=extractores)
        is None
    )


def test_sin_extractores_devuelve_none() -> None:
    assert obtener_primer_parrafo(_soup(HTML), "https://x.com", extractores=[]) is None


def test_no_se_puede_instanciar_la_abstraccion() -> None:
    with pytest.raises(TypeError):
        ExtractorParrafo()  # type: ignore[abstract]
