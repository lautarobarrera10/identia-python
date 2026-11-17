"""
Interfaz de línea de comandos.
"""

import argparse
import logging
import sys
from pathlib import Path

from identia_python import logging_config
from identia_python.descargar import descargar_html
from identia_python.exceptions import DescargaHtmlError, ParseoHtmlError
from identia_python.leer_urls import leer_urls
from identia_python.parsear import parsear_articulo

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
    return parser


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

    errores = 0
    for i, url in enumerate(urls, start=1):
        logger.info("[%d/%d] %s", i, len(urls), url)
        try:
            html = descargar_html(url)
            articulo = parsear_articulo(html, url)
        except (DescargaHtmlError, ParseoHtmlError) as e:
            errores += 1
            logger.error("%s", e)
            continue
        except Exception as e:  # p. ej. url inválida
            errores += 1
            logger.error("Error inesperado: %s: %s", type(e).__name__, e)
            logger.debug("Detalle del error inesperado", exc_info=True)
            continue

        print(url)
        print("  Título:", articulo.titulo)
        print("  Primer párrafo:", articulo.primer_parrafo, "\n")

    print(f"Procesadas {len(urls) - errores}/{len(urls)} noticias correctamente.")
