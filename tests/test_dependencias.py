"""
Inversión de dependencias (principio D de SOLID).

El código de alto nivel no importa detalles concretos (disco, red, navegador):
depende de abstracciones propias y recibe las implementaciones desde el cli.
"""

import ast
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from dobles import ClienteFalso, RespuestaFalsa

from identia_python import generador, resultados, servidor
from identia_python.modelos import Articulo
from identia_python.procesamiento import ProcesadorHttp

DETALLES = {
    "httpx",
    "webbrowser",
    "identia_python.cache",
    "identia_python.descargar",
    "identia_python.guardar_reporte",
    "identia_python.navegador",
    "identia_python.procesamiento",
}


def _modulos_importados(ruta: Path) -> set[str]:
    importados: set[str] = set()
    for nodo in ast.walk(ast.parse(ruta.read_text(encoding="utf-8"))):
        if isinstance(nodo, ast.Import):
            importados.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            importados.add(nodo.module)
            # from identia_python import cache
            importados.update(f"{nodo.module}.{alias.name}" for alias in nodo.names)
    return importados


@pytest.mark.parametrize(
    "modulo", [resultados, servidor, generador], ids=lambda m: m.__name__
)
def test_alto_nivel_no_importa_detalles(modulo: object) -> None:
    ruta = Path(str(getattr(modulo, "__file__", "")))

    assert _modulos_importados(ruta) & DETALLES == set()


HTML = (
    "<html><body><h1>Título</h1>"
    "<p>Un primer párrafo lo bastante largo como para ser válido.</p>"
    "</body></html>"
)


def test_procesador_http_usa_el_cliente_que_recibe() -> None:
    """Sin httpx: la fábrica inyectada entrega un cliente falso."""
    cliente = ClienteFalso(RespuestaFalsa(text=HTML))

    @asynccontextmanager
    async def fabrica() -> AsyncIterator[ClienteFalso]:
        yield cliente

    urls = ["https://a.com", "https://b.com"]
    procesador = ProcesadorHttp(fabrica, max_concurrencia=1)

    obtenidos = asyncio.run(procesador.procesar(urls))

    assert sorted(cliente.pedidas) == urls
    esperado = Articulo(
        titulo="Título",
        primer_parrafo="Un primer párrafo lo bastante largo como para ser válido.",
    )
    assert obtenidos == [esperado, esperado]
