"""
Resumen de un reporte: cuántas noticias se procesaron correctamente.
"""

from collections.abc import Sequence

from identia_python.modelos import Articulo


def texto_resumen(resultados: Sequence[Articulo | None]) -> str:
    """Devuelve el texto "Procesadas X/Y noticias correctamente."."""
    total = len(resultados)
    exitosos = total - resultados.count(None)
    return f"Procesadas {exitosos}/{total} noticias correctamente."
