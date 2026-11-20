"""
Interfaz de línea de comandos: interpreta los argumentos y coordina los pasos.

Es la raíz de composición: el único lugar que conoce las implementaciones
concretas (caché JSON, cliente HTTP, archivo, navegador) y se las pasa al
código de alto nivel, que solo depende de abstracciones (principio de
inversión de dependencias).
"""

import argparse
import logging
import sys
from pathlib import Path

from identia_python import guardar_reporte, logging_config
from identia_python.cache import CacheJson
from identia_python.guardar_reporte import ReporteEnArchivo
from identia_python.leer_urls import leer_urls
from identia_python.navegador import NavegadorWeb
from identia_python.procesamiento import ProcesadorHttp
from identia_python.resultados import obtener_resultados
from identia_python.salidas import Salida, SalidaConsola, SalidaHtml

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


def _nivel_de_consola(args: argparse.Namespace) -> int:
    """Traduce las opciones -v / -q al nivel de logging de la consola."""
    if args.verbose:
        return logging.DEBUG
    if args.quiet:
        return logging.WARNING
    return logging.INFO


def _cargar_urls_o_salir(ruta: Path) -> list[str]:
    """Lee las urls del archivo; si no existe o está vacío, termina con error."""
    if not ruta.is_file():
        logger.error("No se encontró el archivo de urls: %s", ruta)
        sys.exit(1)

    urls = leer_urls(ruta)
    if not urls:
        logger.error("El archivo %s no contiene urls.", ruta)
        sys.exit(1)
    return urls


def _crear_salidas(args: argparse.Namespace) -> list[Salida]:
    """Destinos de los resultados. Para agregar uno nuevo, sumarlo a esta lista."""
    return [
        SalidaConsola(),
        SalidaHtml(
            ReporteEnArchivo(guardar_reporte.ARCHIVO_HTML),
            visor=None if args.no_abrir else NavegadorWeb(),
        ),
    ]


def main(argv: list[str] | None = None) -> None:
    args = _crear_parser().parse_args(argv)
    logging_config.configurar_logging(
        _nivel_de_consola(args), archivo=logging_config.ARCHIVO_LOG
    )

    urls = _cargar_urls_o_salir(args.archivo)
    cache = CacheJson()
    resultados = obtener_resultados(
        urls,
        forzar=args.forzar,
        lector=cache,
        escritor=cache,
        procesador=ProcesadorHttp(),
    )

    for salida in _crear_salidas(args):
        salida.emitir(urls, resultados)
