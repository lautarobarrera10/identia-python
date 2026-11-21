"""
Limpieza de la lista de urls escrita en el formulario.
"""

import logging

logger = logging.getLogger(__name__)

BOM = "﻿"  # marca que algunos editores agregan al inicio del texto


def limpiar_urls(texto: str) -> list[str]:
    """
    Recibe un texto con una url por línea y devuelve la lista de urls.
    Ignora líneas vacías, comentarios (que empiezan con #) y urls repetidas.
    """
    urls: list[str] = []
    vistas: set[str] = set()
    repetidas = 0

    for linea in texto.lstrip(BOM).splitlines():
        url = linea.strip()
        if not url or url.startswith("#"):
            continue
        if url in vistas:
            repetidas += 1
            continue
        vistas.add(url)
        urls.append(url)

    logger.debug("Leídas %d urls (%d repetidas)", len(urls), repetidas)
    return urls
