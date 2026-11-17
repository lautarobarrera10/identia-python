"""
Caché de artículos ya procesados, guardado en un archivo JSON (url -> artículo).
Solo se guardan los artículos procesados correctamente: las urls que fallaron
se vuelven a intentar en la próxima ejecución.
"""

import json
import logging
from dataclasses import asdict
from pathlib import Path

from identia_python.parsear import Articulo

ARCHIVO_CACHE = Path("resultados/cache.json")

logger = logging.getLogger(__name__)


def cargar_cache(archivo: Path | None = None) -> dict[str, Articulo]:
    """Lee el caché. Si no existe o está corrupto, devuelve un caché vacío."""
    ruta = archivo or ARCHIVO_CACHE
    if not ruta.is_file():
        logger.debug("No hay caché en %s", ruta)
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        cache = {
            url: Articulo(titulo=a["titulo"], primer_parrafo=a["primer_parrafo"])
            for url, a in datos.items()
        }
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as e:
        logger.warning("Caché inválido en %s, se ignora: %s", ruta, e)
        return {}
    logger.debug("Caché cargado: %d urls", len(cache))
    return cache


def guardar_cache(cache: dict[str, Articulo], archivo: Path | None = None) -> Path:
    """Escribe el caché en disco y devuelve la ruta."""
    ruta = archivo or ARCHIVO_CACHE
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = {url: asdict(articulo) for url, articulo in cache.items()}
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.debug("Caché guardado: %d urls en %s", len(cache), ruta)
    return ruta
