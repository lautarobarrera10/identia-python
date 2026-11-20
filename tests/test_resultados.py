"""
obtener_resultados depende solo de los roles del caché que usa (segregación de
interfaces) y recibe todas sus dependencias, así que se prueba con dobles sin
monkeypatch (inversión de dependencias).
"""

from dobles import CacheEnMemoria, CacheSoloEscritura, ProcesadorFalso

from identia_python.modelos import Articulo
from identia_python.resultados import obtener_resultados

A = Articulo(titulo="A", primer_parrafo="pa")
B = Articulo(titulo="B", primer_parrafo="pb")


def _procesador() -> ProcesadorFalso:
    return ProcesadorFalso({"https://a.com": A, "https://b.com": B})


class LectorQueNoSeUsa:
    def cargar(self) -> dict[str, Articulo]:
        raise AssertionError("con forzar no se debería leer el caché")


def test_forzar_no_lee_el_cache() -> None:
    escritor = CacheSoloEscritura()
    procesador = _procesador()
    urls = ["https://a.com", "https://b.com", "https://falla.com"]

    obtenidos = obtener_resultados(
        urls,
        forzar=True,
        lector=LectorQueNoSeUsa(),
        escritor=escritor,
        procesador=procesador,
    )

    assert obtenidos == [A, B, None]
    assert procesador.pedidas == urls
    assert escritor.escrito == {"https://a.com": A, "https://b.com": B}


def test_usa_lo_que_ya_esta_en_el_lector() -> None:
    memoria = CacheEnMemoria({"https://a.com": A})
    procesador = _procesador()

    obtenidos = obtener_resultados(
        ["https://a.com", "https://b.com"],
        forzar=False,
        lector=memoria,
        escritor=memoria,
        procesador=procesador,
    )

    assert obtenidos == [A, B]
    assert procesador.pedidas == ["https://b.com"]
    assert memoria.datos == {"https://a.com": A, "https://b.com": B}


def test_todo_en_cache_no_usa_el_procesador() -> None:
    memoria = CacheEnMemoria({"https://a.com": A})
    procesador = _procesador()

    obtenidos = obtener_resultados(
        ["https://a.com"],
        forzar=False,
        lector=memoria,
        escritor=memoria,
        procesador=procesador,
    )

    assert obtenidos == [A]
    assert procesador.pedidas == []
