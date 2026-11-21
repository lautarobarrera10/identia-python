from dobles import CacheEnMemoria, GuardadorEnMemoria, ProcesadorFalso

from identia_python.generador import GeneradorConCache
from identia_python.modelos import Articulo

NUEVO = Articulo(titulo="Nuevo", primer_parrafo="Recién descargado")
GUARDADO = Articulo(titulo="Guardado", primer_parrafo="De antes")


def _armar(
    cache: CacheEnMemoria, procesador: ProcesadorFalso, guardador: GuardadorEnMemoria
) -> GeneradorConCache:
    return GeneradorConCache(
        lector=cache, escritor=cache, procesador=procesador, guardador=guardador
    )


def test_usa_cache_procesa_el_resto_y_guarda_el_reporte() -> None:
    cache = CacheEnMemoria({"https://a.com": GUARDADO})
    procesador = ProcesadorFalso({"https://b.com": NUEVO})
    guardador = GuardadorEnMemoria()

    html = _armar(cache, procesador, guardador).generar(
        ["https://a.com", "https://b.com", "https://mal.com"], forzar=False
    )

    assert procesador.pedidas == ["https://b.com", "https://mal.com"]
    assert "Guardado" in html
    assert "Nuevo" in html
    assert "No se pudo procesar esta noticia." in html
    assert '<a class="volver" href="/">' in html
    assert guardador.contenidos == [html]
    assert set(cache.datos) == {"https://a.com", "https://b.com"}


def test_forzar_vuelve_a_procesar() -> None:
    cache = CacheEnMemoria({"https://a.com": GUARDADO})
    procesador = ProcesadorFalso({"https://a.com": NUEVO})

    html = _armar(cache, procesador, GuardadorEnMemoria()).generar(
        ["https://a.com"], forzar=True
    )

    assert procesador.pedidas == ["https://a.com"]
    assert "Nuevo" in html
    assert cache.datos["https://a.com"] == NUEVO
