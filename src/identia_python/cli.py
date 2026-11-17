"""
Interfaz de línea de comandos.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import httpx

from identia_python import cache, logging_config, reporte_html
from identia_python.descargar import MAX_CONCURRENCIA, crear_cliente, descargar_html
from identia_python.exceptions import DescargaHtmlError, ParseoHtmlError
from identia_python.leer_urls import leer_urls
from identia_python.parsear import Articulo, parsear_articulo

ARCHIVO_URLS = "urls.txt"

logger = logging.getLogger(__name__)


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="identia-python",
        description="Descarga noticias y extrae su título y primer párrafo.",
    )
    # Por defecto lee urls.txt en el directorio desde donde se ejecuta
    parser.add_argument(
        "archivo",
        nargs="?",
        type=Path,
        default=Path.cwd() / ARCHIVO_URLS,
        help=f"archivo con una url por línea (por defecto: ./{ARCHIVO_URLS})",
    )
    nivel = parser.add_mutually_exclusive_group()
    nivel.add_argument(
        "-v", "--verbose", action="store_true", help="mostrar mensajes de depuración"
    )
    nivel.add_argument(
        "-q", "--quiet", action="store_true", help="mostrar solo advertencias y errores"
    )
    parser.add_argument(
        "--no-abrir",
        action="store_true",
        help="generar el reporte HTML sin abrirlo en el navegador",
    )
    parser.add_argument(
        "--forzar",
        action="store_true",
        help="ignorar el caché y volver a procesar todas las urls",
    )
    return parser


async def _procesar_url(
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


async def _procesar_urls(urls: list[str]) -> list[Articulo | None]:
    """Procesa todas las urls en paralelo, con un límite de concurrencia."""
    semaforo = asyncio.Semaphore(MAX_CONCURRENCIA)
    async with crear_cliente() as cliente:
        return await asyncio.gather(
            *(
                _procesar_url(url, i, len(urls), cliente, semaforo)
                for i, url in enumerate(urls, start=1)
            )
        )


def _obtener_resultados(urls: list[str], forzar: bool) -> list[Articulo | None]:
    """
    Devuelve un resultado por url, en orden. Las urls que ya están en el caché
    se toman de ahí sin descargarse; el resto se procesa y se agrega al caché.
    """
    datos_cache = {} if forzar else cache.cargar_cache()
    pendientes = [url for url in urls if url not in datos_cache]
    en_cache = len(urls) - len(pendientes)
    if en_cache:
        logger.info("%d/%d urls ya procesadas, se usan del caché", en_cache, len(urls))

    if pendientes:
        nuevos = asyncio.run(_procesar_urls(pendientes))
        for url, articulo in zip(pendientes, nuevos, strict=True):
            if articulo is not None:
                datos_cache[url] = articulo
        # Se recarga para no perder entradas de otras urls si se usó --forzar
        guardar = cache.cargar_cache() if forzar else {}
        guardar.update(datos_cache)
        cache.guardar_cache(guardar)
    else:
        logger.info("Todas las urls ya estaban procesadas, no se descarga nada")

    return [datos_cache.get(url) for url in urls]


def main(argv: list[str] | None = None) -> None:
    args = _crear_parser().parse_args(argv)

    if args.verbose:
        nivel = logging.DEBUG
    elif args.quiet:
        nivel = logging.WARNING
    else:
        nivel = logging.INFO
    logging_config.configurar_logging(nivel, archivo=logging_config.ARCHIVO_LOG)

    ruta: Path = args.archivo
    if not ruta.is_file():
        logger.error("No se encontró el archivo de urls: %s", ruta)
        sys.exit(1)

    urls = leer_urls(ruta)
    if not urls:
        logger.error("El archivo %s no contiene urls.", ruta)
        sys.exit(1)

    resultados = _obtener_resultados(urls, forzar=args.forzar)

    # gather preserva el orden de entrada: la salida sigue el orden del archivo
    for url, articulo in zip(urls, resultados, strict=True):
        if articulo is None:
            continue
        print(url)
        print("  Título:", articulo.titulo)
        print("  Primer párrafo:", articulo.primer_parrafo, "\n")

    errores = resultados.count(None)
    print(f"Procesadas {len(urls) - errores}/{len(urls)} noticias correctamente.")

    contenido = reporte_html.generar_html(urls, resultados)
    ruta_html = reporte_html.guardar_html(contenido, reporte_html.ARCHIVO_HTML)
    logger.info("Resultado guardado en %s", ruta_html)
    if not args.no_abrir:
        reporte_html.abrir_en_navegador(ruta_html)
