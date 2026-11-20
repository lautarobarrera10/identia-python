"""
Procesamiento concurrente de urls: descarga y parseo de cada noticia.

ProcesadorHttp cumple ProcesadorUrls (definido en resultados.py). No crea el
cliente HTTP por su cuenta: recibe una fábrica, así que se puede usar con
httpx o con cualquier ClienteHttp (principio de inversión de dependencias).
"""

import asyncio
import logging
from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager

from identia_python.descargar import (
    MAX_CONCURRENCIA,
    ClienteHttp,
    crear_cliente,
    descargar_html,
)
from identia_python.exceptions import IdentiaError
from identia_python.modelos import Articulo
from identia_python.parsear import parsear_articulo

logger = logging.getLogger(__name__)

FabricaCliente = Callable[[], AbstractAsyncContextManager[ClienteHttp]]


async def procesar_url(
    url: str,
    i: int,
    total: int,
    cliente: ClienteHttp,
    semaforo: asyncio.Semaphore,
) -> Articulo | None:
    """Descarga y parsea una url. Devuelve None (y loguea) si falla."""
    async with semaforo:
        logger.info("[%d/%d] %s", i, total, url)
        try:
            html = await descargar_html(url, cliente)
            return parsear_articulo(html, url)
        except IdentiaError as e:  # cualquier error propio, actual o futuro
            logger.error("%s", e)
        except Exception as e:  # p. ej. url inválida
            logger.error("Error inesperado: %s: %s", type(e).__name__, e)
            logger.debug("Detalle del error inesperado", exc_info=True)
        return None


class ProcesadorHttp:
    """Descarga y parsea las urls en paralelo, con un límite de concurrencia."""

    def __init__(
        self,
        fabrica_cliente: FabricaCliente = crear_cliente,
        max_concurrencia: int = MAX_CONCURRENCIA,
    ) -> None:
        self.fabrica_cliente = fabrica_cliente
        self.max_concurrencia = max_concurrencia

    async def procesar(self, urls: Sequence[str]) -> list[Articulo | None]:
        """Devuelve un resultado por url, en el mismo orden (gather lo preserva)."""
        semaforo = asyncio.Semaphore(self.max_concurrencia)
        async with self.fabrica_cliente() as cliente:
            return await asyncio.gather(
                *(
                    procesar_url(url, i, len(urls), cliente, semaforo)
                    for i, url in enumerate(urls, start=1)
                )
            )
