"""
Presentación de los resultados por consola (stdout).
"""

from collections.abc import Sequence

from identia_python.modelos import Articulo
from identia_python.resumen import texto_resumen


def imprimir_resultados(
    urls: Sequence[str], resultados: Sequence[Articulo | None]
) -> None:
    """Imprime los artículos obtenidos, en orden, y un resumen final."""
    for url, articulo in zip(urls, resultados, strict=True):
        if articulo is None:
            continue
        print(url)
        print("  Título:", articulo.titulo)
        print("  Primer párrafo:", articulo.primer_parrafo, "\n")

    print(texto_resumen(resultados))
