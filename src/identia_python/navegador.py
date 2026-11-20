"""
Apertura de archivos en el navegador predeterminado.
"""

import logging
import webbrowser
from pathlib import Path

logger = logging.getLogger(__name__)


def abrir_en_navegador(ruta: Path) -> None:
    """Abre el archivo en el navegador predeterminado."""
    if not webbrowser.open(ruta.resolve().as_uri()):
        logger.warning("No se pudo abrir el navegador. Abrí manualmente: %s", ruta)


class NavegadorWeb:
    """Abre archivos en el navegador. Cumple Visor (salidas.py)."""

    def abrir(self, ruta: Path) -> None:
        abrir_en_navegador(ruta)
