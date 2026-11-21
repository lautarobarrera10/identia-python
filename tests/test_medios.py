import pytest

from identia_python.medios import nombre_medio


@pytest.mark.parametrize(
    ("url", "esperado"),
    [
        ("https://www.lanacion.com.ar/politica/nota", "La Nación"),
        ("https://www.clarin.com/nota", "Clarín"),
        ("https://www.infobae.com/nota", "Infobae"),
        ("https://www.pagina12.com.ar/nota", "Página/12"),
        ("https://www.cronista.com/nota", "El Cronista"),
        ("https://urgente24.com/nota", "Urgente24"),
        ("https://abogados.com.ar/nota", "Abogados.com.ar"),
        ("https://WWW.LANACION.COM.AR/nota", "La Nación"),
    ],
)
def test_nombre_medio_conocido(url: str, esperado: str) -> None:
    assert nombre_medio(url) == esperado


def test_nombre_medio_desconocido_usa_el_dominio_sin_www() -> None:
    assert nombre_medio("https://www.ejemplo.com/nota") == "ejemplo.com"


def test_nombre_medio_no_confunde_dominios_parecidos() -> None:
    assert nombre_medio("https://falsolanacion.com.ar/nota") == "falsolanacion.com.ar"
