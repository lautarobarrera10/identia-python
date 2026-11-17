from pathlib import Path

import pytest

from identia_python import cache
from identia_python.parsear import Articulo


def test_cargar_sin_archivo_devuelve_vacio() -> None:
    assert cache.cargar_cache() == {}


def test_guardar_y_cargar_ida_y_vuelta() -> None:
    datos = {
        "https://a.com": Articulo(titulo="Título á", primer_parrafo="línea 1\nlínea 2"),
    }

    ruta = cache.guardar_cache(datos)

    assert ruta == cache.ARCHIVO_CACHE
    assert "Título á" in ruta.read_text(encoding="utf-8")
    assert cache.cargar_cache() == datos


@pytest.mark.parametrize(
    "contenido",
    ["no es json", "[1, 2]", '{"https://a.com": {"titulo": "x"}}'],
)
def test_cache_invalido_se_ignora(
    contenido: str, caplog: pytest.LogCaptureFixture
) -> None:
    ruta: Path = cache.ARCHIVO_CACHE
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")

    assert cache.cargar_cache() == {}
    assert "Caché inválido" in caplog.text
