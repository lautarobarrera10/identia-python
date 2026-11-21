"""
Apertura de la interfaz web en el navegador predeterminado.
"""

import logging
import webbrowser

logger = logging.getLogger(__name__)


def abrir_url(url: str) -> None:
    """Abre la dirección en el navegador predeterminado."""
    if not webbrowser.open(url):
        logger.warning("No se pudo abrir el navegador. Abrí manualmente: %s", url)
