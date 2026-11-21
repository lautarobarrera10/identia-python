"""
Punto de entrada: interpreta los argumentos y levanta el servidor web local.

Es la raíz de composición: el único lugar que conoce las implementaciones
concretas (caché JSON, cliente HTTP, archivo, navegador) y se las pasa al
código de alto nivel, que solo depende de abstracciones (principio de
inversión de dependencias).
"""

import argparse
import logging

from identia_python import guardar_reporte, logging_config
from identia_python.cache import CacheJson
from identia_python.generador import GeneradorConCache
from identia_python.guardar_reporte import ReporteEnArchivo
from identia_python.navegador import abrir_url
from identia_python.procesamiento import ProcesadorHttp
from identia_python.servidor import crear_servidor

HOST = "127.0.0.1"
PUERTO = 8000

logger = logging.getLogger(__name__)


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="identia-python",
        description=(
            "Levanta una interfaz web local para descargar noticias y extraer "
            "su título y primer párrafo."
        ),
    )
    parser.add_argument(
        "--host", default=HOST, help=f"dirección del servidor (por defecto: {HOST})"
    )
    parser.add_argument(
        "--puerto",
        type=int,
        default=PUERTO,
        help=f"puerto del servidor (por defecto: {PUERTO})",
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
        help="no abrir la interfaz en el navegador al iniciar",
    )
    return parser


def _nivel_de_consola(args: argparse.Namespace) -> int:
    """Traduce las opciones -v / -q al nivel de logging de la consola."""
    if args.verbose:
        return logging.DEBUG
    if args.quiet:
        return logging.WARNING
    return logging.INFO


def crear_generador() -> GeneradorConCache:
    """Arma el generador de reportes con las implementaciones concretas."""
    cache = CacheJson()
    return GeneradorConCache(
        lector=cache,
        escritor=cache,
        procesador=ProcesadorHttp(),
        guardador=ReporteEnArchivo(guardar_reporte.ARCHIVO_HTML),
    )


def main(argv: list[str] | None = None) -> None:
    args = _crear_parser().parse_args(argv)
    logging_config.configurar_logging(
        _nivel_de_consola(args), archivo=logging_config.ARCHIVO_LOG
    )

    servidor = crear_servidor(args.host, args.puerto, crear_generador())
    # server_address[1] da el puerto real (útil si se pidió el 0)
    url = f"http://{args.host}:{servidor.server_address[1]}/"
    logger.info("Servidor en %s (Ctrl+C para salir)", url)
    if not args.no_abrir:
        abrir_url(url)

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        logger.info("Servidor detenido")
    finally:
        servidor.server_close()
