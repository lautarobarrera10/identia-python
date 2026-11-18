"""
Obtención de los resultados de una lista de urls, usando el caché.
"""

import asyncio
import logging

from identia_python import cache
from identia_python.modelos import Articulo
from identia_python.procesamiento import procesar_urls

logger = logging.getLogger(__name__)


def obtener_resultados(urls: list[str], forzar: bool) -> list[Articulo | None]:
    """
    Devuelve un resultado por url, en orden. Las urls que ya están en el caché
    se toman de ahí sin descargarse; el resto se procesa y se agrega al caché.
    """
    disponibles = {} if forzar else cache.cargar_cache()
    pendientes = [url for url in urls if url not in disponibles]
    en_cache = len(urls) - len(pendientes)
    if en_cache:
        logger.info("%d/%d urls ya procesadas, se usan del caché", en_cache, len(urls))

    if pendientes:
        procesados = asyncio.run(procesar_urls(pendientes))
        nuevos = {
            url: articulo
            for url, articulo in zip(pendientes, procesados, strict=True)
            if articulo is not None
        }
        cache.actualizar_cache(nuevos)
        disponibles.update(nuevos)
    else:
        logger.info("Todas las urls ya estaban procesadas, no se descarga nada")

    return [disponibles.get(url) for url in urls]
