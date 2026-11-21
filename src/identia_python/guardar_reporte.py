"""
Escritura del reporte HTML en disco.
"""

from pathlib import Path

ARCHIVO_HTML = Path("resultados/resultado.html")


def guardar_html(contenido: str, archivo: Path | None = None) -> Path:
    """Escribe el HTML (por defecto en ARCHIVO_HTML) y devuelve la ruta absoluta."""
    destino = (archivo or ARCHIVO_HTML).resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")
    return destino


class ReporteEnArchivo:
    """Guarda el reporte en un archivo. Cumple GuardadorReporte (generador.py)."""

    def __init__(self, archivo: Path | None = None) -> None:
        # None: se usa ARCHIVO_HTML en el momento de guardar
        self.archivo = archivo

    def guardar(self, contenido: str) -> Path:
        return guardar_html(contenido, self.archivo)
