"""
Procesamiento concurrente de urls: descarga y parseo de cada noticia.
"""

import asyncio
import logging

import httpx

from identia_python.descargar import MAX_CONCURRENCIA, crear_cliente, descargar_html
from identia_python.exceptions import DescargaHtmlError, ParseoHtmlError
from identia_python.modelos import Articulo
from identia_python.parsear import parsear_articulo

logger = logging.getLogger(__name__)


async def procesar_url(
    url: str,
    i: int,
    total: int,
    cliente: httpx.AsyncClient,
    semaforo: asyncio.Semaphore,
) -> Articulo | None:
    """Descarga y parsea una url. Devuelve None (y loguea) si falla."""
    async with semaforo:
        logger.info("[%d/%d] %s", i, total, url)
        try:
            html = await descargar_html(url, cliente)
            return parsear_articulo(html, url)
        except (DescargaHtmlError, ParseoHtmlError) as e:
            logger.error("%s", e)
        except Exception as e:  # p. ej. url inválida
            logger.error("Error inesperado: %s: %s", type(e).__name__, e)
            logger.debug("Detalle del error inesperado", exc_info=True)
        return None


async def procesar_urls(urls: list[str]) -> list[Articulo | None]:
    """
    Procesa todas las urls en paralelo, con un límite de concurrencia.
    Devuelve un resultado por url, en el mismo orden (gather lo preserva).
    """
    semaforo = asyncio.Semaphore(MAX_CONCURRENCIA)
    async with crear_cliente() as cliente:
        return await asyncio.gather(
            *(
                procesar_url(url, i, len(urls), cliente, semaforo)
                for i, url in enumerate(urls, start=1)
            )
        )
