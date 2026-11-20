"""
obtener_resultados depende solo de los roles del caché que usa
(principio de segregación de interfaces).
"""

import pytest
from dobles import CacheEnMemoria, CacheSoloEscritura

from identia_python import resultados
from identia_python.modelos import Articulo

A = Articulo(titulo="A", primer_parrafo="pa")
B = Articulo(titulo="B", primer_parrafo="pb")


@pytest.fixture
def procesadas(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Reemplaza el procesamiento real: devuelve un artículo por url, sin red."""
    pedidas: list[str] = []
    articulos = {"https://a.com": A, "https://b.com": B}

    async def procesar_falso(urls: list[str]) -> list[Articulo | None]:
        pedidas.extend(urls)
        return [articulos.get(url) for url in urls]

    monkeypatch.setattr(resultados, "procesar_urls", procesar_falso)
    return pedidas


def test_forzar_solo_necesita_un_escritor(procesadas: list[str]) -> None:
    escritor = CacheSoloEscritura()
    urls = ["https://a.com", "https://b.com", "https://falla.com"]

    obtenidos = resultados.obtener_resultados(urls, forzar=True, escritor=escritor)

    assert obtenidos == [A, B, None]
    assert procesadas == urls
    assert escritor.escrito == {"https://a.com": A, "https://b.com": B}


def test_usa_lo_que_ya_esta_en_el_lector(procesadas: list[str]) -> None:
    memoria = CacheEnMemoria({"https://a.com": A})

    obtenidos = resultados.obtener_resultados(
        ["https://a.com", "https://b.com"],
        forzar=False,
        lector=memoria,
        escritor=memoria,
    )

    assert obtenidos == [A, B]
    assert procesadas == ["https://b.com"]
    assert memoria.datos == {"https://a.com": A, "https://b.com": B}
