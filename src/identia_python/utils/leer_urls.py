"""
Leer las urls desde un archivo .txt
"""

from pathlib import Path


def leer_urls(ruta: Path) -> list[str]:
    """
    Lee un archivo de texto con una url por línea y devuelve la lista de urls.
    Ignora líneas vacías, comentarios (que empiezan con #) y urls repetidas.
    """
    urls: list[str] = []
    vistas: set[str] = set()

    for linea in ruta.read_text(encoding="utf-8-sig").splitlines():
        url = linea.strip()
        if not url or url.startswith("#") or url in vistas:
            continue
        vistas.add(url)
        urls.append(url)

    return urls
