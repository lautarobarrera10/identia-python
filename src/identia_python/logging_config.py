"""
Configuración del logging de la aplicación.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGER_RAIZ = "identia_python"
ARCHIVO_LOG = Path("logs/identia.log")

FORMATO_CONSOLA = "%(levelname)s: %(message)s"
FORMATO_ARCHIVO = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configurar_logging(
    nivel_consola: int = logging.INFO, archivo: Path | None = ARCHIVO_LOG
) -> None:
    """
    Configura el logger del paquete: consola (stderr) con `nivel_consola` y,
    si se indica `archivo`, un archivo rotativo con nivel DEBUG.
    Se puede llamar varias veces: reemplaza los handlers anteriores.
    """
    logger = logging.getLogger(LOGGER_RAIZ)
    logger.setLevel(logging.DEBUG)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    consola = logging.StreamHandler(sys.stderr)
    consola.setLevel(nivel_consola)
    consola.setFormatter(logging.Formatter(FORMATO_CONSOLA))
    logger.addHandler(consola)

    if archivo is not None:
        archivo.parent.mkdir(parents=True, exist_ok=True)
        en_archivo = RotatingFileHandler(
            archivo, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        en_archivo.setLevel(logging.DEBUG)
        en_archivo.setFormatter(logging.Formatter(FORMATO_ARCHIVO))
        logger.addHandler(en_archivo)
