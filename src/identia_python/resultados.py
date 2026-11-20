"""
Obtención de los resultados de una lista de urls, usando el caché.

Es código de alto nivel: decide qué se toma del caché y qué se procesa, pero no
sabe cómo se guarda el caché ni cómo se descargan las noticias. Depende solo de
las abstracciones que define acá (LectorCache, EscritorCache, ProcesadorUrls) y
las implementaciones concretas se las pasa el cli (principio de inversión de
dependencias).
"""

import asyncio
import logging
from collections.abc import Sequence
from typing import Protocol

from identia_python.modelos import Articulo

logger = logging.getLogger(__name__)


class LectorCache(Protocol):
    def cargar(self) -> dict[str, Articulo]:
        """Devuelve los artículos guardados (url -> artículo)."""
        ...


class EscritorCache(Protocol):
    def actualizar(self, nuevos: dict[str, Articulo]) -> None:
        """Agrega (o reemplaza) los artículos, conservando los demás."""
        ...


class ProcesadorUrls(Protocol):
    async def procesar(self, urls: Sequence[str]) -> list[Articulo | None]:
        """Devuelve un resultado por url, en el mismo orden (None si falló)."""
        ...


def obtener_resultados(
    urls: list[str],
    forzar: bool,
    *,
    lector: LectorCache,
    escritor: EscritorCache,
    procesador: ProcesadorUrls,
) -> list[Articulo | None]:
    """
    Devuelve un resultado por url, en orden. Las urls que ya están en el caché
    se toman de ahí sin procesarse; el resto se procesa y se agrega al caché.
    Con forzar no se lee el caché, así que el lector no se usa.
    """
    disponibles = {} if forzar else lector.cargar()
    pendientes = [url for url in urls if url not in disponibles]
    en_cache = len(urls) - len(pendientes)
    if en_cache:
        logger.info("%d/%d urls ya procesadas, se usan del caché", en_cache, len(urls))

    if pendientes:
        procesados = asyncio.run(procesador.procesar(pendientes))
        nuevos = {
            url: articulo
            for url, articulo in zip(pendientes, procesados, strict=True)
            if articulo is not None
        }
        escritor.actualizar(nuevos)
        disponibles.update(nuevos)
    else:
        logger.info("Todas las urls ya estaban procesadas, no se descarga nada")

    return [disponibles.get(url) for url in urls]
