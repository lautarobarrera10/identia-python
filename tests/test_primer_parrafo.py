import pytest
from bs4 import BeautifulSoup
from dobles import ParrafoDesdeResumen

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


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def test_extractor_nuevo_antepuesto_gana() -> None:
    extractores = [ParrafoDesdeResumen(), *extractores_por_defecto()]

    assert (
        obtener_primer_parrafo(_soup(HTML), "https://x.com", extractores=extractores)
        == "Resumen propio del sitio."
    )


def test_por_defecto_usa_el_primer_parrafo_significativo() -> None:
    parrafo = obtener_primer_parrafo(_soup(HTML), "https://x.com")

    assert parrafo is not None
    assert parrafo.startswith("Un párrafo")


def test_min_largo_configurable() -> None:
    extractores = [PrimerParrafoSignificativo(min_largo=1000)]

    assert (
        obtener_primer_parrafo(_soup(HTML), "https://x.com", extractores=extractores)
        is None
    )


def test_min_largo_cero_no_devuelve_parrafo_vacio() -> None:
    html = "<p>   </p><p>Texto</p>"
    extractores = [PrimerParrafoSignificativo(min_largo=0)]

    assert (
        obtener_primer_parrafo(_soup(html), "https://x.com", extractores=extractores)
        == "Texto"
    )


def test_sin_extractores_devuelve_none() -> None:
    assert obtener_primer_parrafo(_soup(HTML), "https://x.com", extractores=[]) is None


def test_no_se_puede_instanciar_la_abstraccion() -> None:
    with pytest.raises(TypeError):
        ExtractorParrafo()  # type: ignore[abstract]
