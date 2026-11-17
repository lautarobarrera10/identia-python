"""
Leer las urls desde un archivo .txt
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def leer_urls(ruta: Path) -> list[str]:
    """
    Lee un archivo de texto con una url por línea y devuelve la lista de urls.
    Ignora líneas vacías, comentarios (que empiezan con #) y urls repetidas.
    """
    urls: list[str] = []
    vistas: set[str] = set()
    repetidas = 0

    for linea in ruta.read_text(encoding="utf-8-sig").splitlines():
        url = linea.strip()
        if not url or url.startswith("#"):
            continue
        if url in vistas:
            repetidas += 1
            continue
        vistas.add(url)
        urls.append(url)

    logger.debug("Leídas %d urls de %s (%d repetidas)", len(urls), ruta, repetidas)
    return urls
